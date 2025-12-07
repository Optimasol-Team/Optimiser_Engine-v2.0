import pulp

def solve_optimization(
    # --- 1. Paramètres Temporels ---
    horizon_steps: int,       # N
    pas_minutes: float,       # Delta t
    
    # --- 2. Vecteurs d'Entrée (Taille N) ---
    vec_p_maison: list,       # P_maison [W]
    vec_p_solaire: list,      # P_solaire [W]
    vec_prix_achat: list,     # Pi_achat [€/kWh]
    vec_prix_vente: list,     # Pi_vente [€/kWh]
    vec_v_tirage: list,       # V_tirage [Litres]
    vec_t_req: list,          # T_req [°C] (Consignes + Min sécu)
    vec_mask_dispo: list,     # M_dispo [0 ou 1]
    
    # --- 3. Scalaires Physiques ---
    p_max: float,             # Puissance résistance [W]
    vol_total: float,         # Volume ballon [L]
    t_cold: float,            # Température eau réseau [°C]
    t_init: float,            # Température initiale [°C]
    c_pertes: float,          # Perte statique [°C/pas]
    
    # --- 4. Configuration ---
    mode: str = "COST",       # "COST" ou "AUTOCONS"
    is_gradation: bool = True # True = Continue, False = Tout-ou-Rien
):
    """
    Implémentation du solveur MILP pour le Chauffe-Eau Solaire.
    """
    
    # --- A. CRÉATION DU PROBLÈME ---
    prob = pulp.LpProblem("SmartWaterHeater_Opt", pulp.LpMinimize)
    
    # --- B. CRÉATION DES VARIABLES (Vecteur X) ---
    indices_flux = range(horizon_steps)        # 0 à N-1
    indices_etat = range(horizon_steps + 1)    # 0 à N (pour T)

    # 1. Variable de chauffe x (0 à 1)
    cat_x = pulp.LpContinuous if is_gradation else pulp.LpBinary
    x = pulp.LpVariable.dicts("x", indices_flux, 0, 1, cat=cat_x)

    # 2. Variable d'état T (Température)
    # On met des bornes larges ici, les contraintes fines sont ajoutées plus bas
    T = pulp.LpVariable.dicts("T", indices_etat, 0, 100, cat=pulp.LpContinuous)

    # 3. Variables Réseau I (Import) et E (Export)
    I = pulp.LpVariable.dicts("Import", indices_flux, 0, None, cat=pulp.LpContinuous)
    E = pulp.LpVariable.dicts("Export", indices_flux, 0, None, cat=pulp.LpContinuous)

    # --- C. PRÉ-CALCUL DES COEFFICIENTS PHYSIQUES ---
    # Cp de l'eau ~ 4185 J/kg/°C. 
    # Energie (J) = Puissance (W) * Temps (s)
    # Gain (°C) = Energie / (Masse * Cp)
    joules_per_step = p_max * (pas_minutes * 60)
    k_gain = joules_per_step / (vol_total * 4185)

    # --- D. AJOUT DES CONTRAINTES ---
    
    # Condition Initiale
    prob += T[0] == t_init, "Init_Temp"

    for t in indices_flux:
        # 1. Bilan Électrique (Loi des noeuds)
        # I - E - (x * Pmax) = Maison - Solaire
        net_load = vec_p_maison[t] - vec_p_solaire[t]
        prob += I[t] - E[t] - (x[t] * p_max) == net_load, f"Elec_Balance_{t}"

        # 2. Thermodynamique (Loi d'évolution avec mélange)
        # rho = Volume tiré / Volume total
        rho_t = vec_v_tirage[t] / vol_total
        
        # T(t+1) = T(t)*(1-rho) + T_cold*rho + x*Gain - Pertes
        prob += T[t+1] == (T[t] * (1 - rho_t)) + \
                          (t_cold * rho_t) + \
                          (x[t] * k_gain) - \
                          c_pertes, f"Thermo_Step_{t}"

        # 3. Disponibilité (Plages Interdites)
        # x[t] <= Mask[t]
        prob += x[t] <= vec_mask_dispo[t], f"Availability_{t}"

        # 4. Confort & Sécurité (Bornes Température)
        # Max physique (90°C)
        prob += T[t] <= 90.0, f"Max_Safety_{t}"
        
        # Requis Client (T_req)
        # Si une consigne existe (non None), on l'impose
        if vec_t_req[t] is not None:
            prob += T[t] >= vec_t_req[t], f"Confort_Req_{t}"

    # --- E. FONCTION OBJECTIF ---
    objective_terms = []
    
    if mode == "COST":
        # Mode Financier : Vrais Prix
        # On divise par 1000 et on * (pas/60) pour avoir des kWh si les prix sont en €/kWh
        # Pour simplifier l'exemple, supposons que vec_prix sont des coûts par pas de temps
        factor_h = pas_minutes / 60.0 / 1000.0 # W -> kWh
        
        for t in indices_flux:
            cost_import = I[t] * vec_prix_achat[t] * factor_h
            gain_export = E[t] * vec_prix_vente[t] * factor_h
            objective_terms.append(cost_import - gain_export)
            
    else: # Mode AUTOCONS
        # Mode Écologique : Pénalités
        alpha = 1000.0 # Pénalité Import
        beta = 1.0     # Pénalité Export
        
        for t in indices_flux:
            objective_terms.append(I[t] * alpha + E[t] * beta)

    prob += pulp.lpSum(objective_terms)

    # --- F. RÉSOLUTION ---
    # msg=0 pour ne pas polluer la console
    prob.solve(pulp.PULP_CBC_CMD(msg=0))

    # --- G. EXTRACTION DES RÉSULTATS ---
    results = {
        "status": pulp.LpStatus[prob.status],
        "x": [pulp.value(x[t]) for t in indices_flux],
        "T": [pulp.value(T[t]) for t in indices_etat], # Inclut T_final
        "I": [pulp.value(I[t]) for t in indices_flux],
        "E": [pulp.value(E[t]) for t in indices_flux]
    }
    return results

# ==============================================================================
# EXEMPLE D'UTILISATION
# ==============================================================================

if __name__ == "__main__":

    # 1. Configuration du scénario
    # Horizon de 2 heures (8 pas de 15 minutes)
    N = 8
    pas = 15.0
    
    # Physique
    vol = 200.0   # 200 Litres
    p_res = 2000.0 # 2000 Watts
    
    # Scénario Métier :
    # - t=0 à 1 : Nuit, Heures Creuses, Pas de besoin
    # - t=2 : DOUCHE ! (On tire 50L) -> T doit être > 50°C
    # - t=3 à 5 : Matinée, le soleil se lève
    # - t=6 à 7 : Plein soleil (Surplus)
    
    # Vecteurs
    v_p_maison = [500] * N
    v_p_solaire = [0, 0, 0, 200, 800, 1500, 2500, 2500] # Monte progressivement
    
    # Prix : HC à 0.10€, HP à 0.20€ (HC au début)
    v_prix_achat = [0.10, 0.10, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20]
    v_prix_vente = [0.05] * N # Revente fixe
    
    # Consignes
    v_tirage = [0] * N
    v_tirage[2] = 50 # Douche à t=2
    
    v_t_req = [10.0] * N # Min sécu par défaut
    v_t_req[2] = 50.0    # Besoin confort pour la douche
    
    v_mask = [1] * N # Tout autorisé
    
    # 2. Appel du Solveur
    res = solve_optimization(
        horizon_steps=N,
        pas_minutes=pas,
        vec_p_maison=v_p_maison,
        vec_p_solaire=v_p_solaire,
        vec_prix_achat=v_prix_achat,
        vec_prix_vente=v_prix_vente,
        vec_v_tirage=v_tirage,
        vec_t_req=v_t_req,
        vec_mask_dispo=v_mask,
        p_max=p_res,
        vol_total=vol,
        t_cold=10.0,
        t_init=40.0,      # On part un peu bas (40°C)
        c_pertes=0.1,
        mode="COST",
        is_gradation=True
    )

    # 3. Affichage des résultats
    print(res['x']) 
    print(res['T']) 
    print(res['I']) 
    print(res['E'])
