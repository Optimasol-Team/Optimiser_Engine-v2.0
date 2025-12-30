"""
Fichier contenant la classe OptimizationInputs. 
C'est la classe d'entrée pour le solveur. 
Elle contient un contexte, une configsystem et une température initiale. 

Auteur : @anaselb 
"""


from .system_config import SystemConfig
from .external_context import ExternalContext 
from Exceptions import NotEnoughVariables
import numpy as np 
from ...domain.features_models import OptimizationMode 


class OptimizationInputs :
    def __init__(self, system_config : SystemConfig, 
                 contexte : ExternalContext, 
                 temp_initial : float, 
                 mode : OptimizationMode = None
                 ) : 
        self.system_config = system_config
        self.contexte = contexte
        self.temp_initial = temp_initial 
        self.mode = mode 
    @property 
    def system_config(self) :
        return self._sys_config 
    @system_config.setter 
    def system_config(self,valeur) :
        if not isinstance(valeur, SystemConfig) :
            raise TypeError(f"La variable {valeur} doit être de type SystemConfig.") 
        self._sys_config = valeur 
    @property 
    def contexte(self) :
        return self._contexte 
    @contexte.setter 
    def contexte(self, valeur) :
        if not isinstance(valeur, ExternalContext) :
            raise TypeError(f"La variable {valeur} doit être de type ExternalContext.") 
        self._contexte = valeur 
    @property 
    def temp_initial(self) :
        return self._temp_init 
    @temp_initial.setter 
    def temp_initial(self, valeur) :
        if not isinstance(valeur, (int, float)) :
            raise TypeError(f"La variable {valeur} doit être de type int ou float.") 
        if valeur < 0 or valeur > 100 :
            raise ValueError("Veuillez entrez une valeur de la température valide. (entre 0 et 100)") 
        self._temp_init = valeur 
    @property 
    def mode(self) :
        return self._mode 
    @mode.setter 
    def mode(self, mde) :
        if mde is None :
            self._mode = OptimizationMode.COST
        else :
            if not isinstance(mde, OptimizationMode) :
                raise TypeError("Le mode doit être une variable du format OptimizationMode") 
            self._mode = mde 

    
    # --- PARTIE ÉGALITÉS (A_eq, B_eq) ---

    def A_eq(self):
        # On appelle les méthodes privées
        Ai = self._build_A_init() 
        At = self._build_A_thermo() 
        Ae = self._build_A_elec() 
        # On empile verticalement les matrices
        return np.vstack((Ai, At, Ae))

    def B_eq(self):
        Bi = self._build_B_init() 
        Bt = self._build_B_thermo() 
        Be = self._build_B_elec() 
        # On concatène les vecteurs (à plat)
        return np.concatenate((Bi, Bt, Be))

    # --- PARTIE INÉGALITÉS (A_in, B_in) ---

    def A_in(self):
        return None 

    def B_in(self):
        return None
    
    # --- MÉTHODES PRIVÉS DE CONSTRUCTION ---
    
    def _build_A_init(self):
        """
        Construit la contrainte de condition initiale.
        1 * T_0 = T_init
        """
        if self.contexte is None:
            raise NotEnoughVariables("Le contexte est manquant. Veuillez le remplir.")
        N = self.contexte.N         #Toujours existe pas de None. 
        nb_vars = 4 * N + 1
        
        # 1. On crée une ligne vide (1 ligne, Total Colonnes)
        A_init = np.zeros((1, nb_vars))
        
        # 2. On cible chirurgicalement T_0
        # Les x sont de 0 à N-1. Donc T_0 est à l'index N.
        idx_T0 = N 
        
        A_init[0, idx_T0] = 1 # On met le coefficient 1
        
        return A_init

    def _build_B_init(self):
        """
        Construit le membre de droite pour l'initialisation.
        """
        # C'est simplement la valeur scalaire stockée dans l'input
        # On renvoie un array 1D de taille 1
        if self.temp_initial is None :
            raise NotEnoughVariables("La température initiale est manquante. Veuillez la remplir.") 
        return np.array([self.temp_initial]) 
    # Deux matrices thermodynamiques. 
    def _build_A_thermo(self):
        """
        Construit la matrice de dynamique thermique (A_thermo).
        Equation : T(t+1) - (1-rho)*T(t) - K_gain*x(t) = ...
        """
        if self.contexte is None:
            raise NotEnoughVariables("Le contexte est manquant. Veuillez le remplir.")
        if self.system_config is None:
            raise NotEnoughVariables("La configuration du système est manquante. Veuillez la remplir.")
        if self.contexte.water_draws is None:
            raise NotEnoughVariables("Les tirages d'eau sont manquants. Veuillez les remplir.")
        N = self.contexte.N
        
        # --- 1. Calcul des Constantes Physiques ---
        # On récupère les données
        V_total = self.system_config.volume        # Litres (équivalent kg pour l'eau)
        P_max_watts = self.system_config.power     # Watts (Joules/sec)
        delta_t_min = self.contexte.step_minutes   # Minutes

        delta_t_sec = delta_t_min * 60             # Secondes
        C_p = 4185                                 # Capacité thermique eau (J/kg/K)
        
        # Calcul du Gain (K_gain) : Combien de degrés on gagne si on chauffe à fond pendant 1 pas
        # Formule du doc 
        K_gain = (P_max_watts * delta_t_sec) / (V_total * C_p)
        
        # Calcul du vecteur Rho (Taux de mélange) pour chaque pas t
        # Rho[t] = V_tirage[t] / V_total 
        vec_rho = self.contexte.water_draws / V_total
        
        # --- 2. Construction des Blocs ---
        
        # BLOC X : Diagonale de -K_gain
        # On chauffe à t pour influencer T(t+1)
        bloc_x = -K_gain * np.eye(N)
        
        # BLOC T : Le plus complexe (N lignes, N+1 colonnes)
        # On doit placer '1' en (t, t+1) et '-(1-rho)' en (t, t)
        
        # A. La diagonale principale (t) : Contient -(1 - rho)
        # On crée une matrice NxN d'abord
        diag_main = np.diag(-(1 - vec_rho))
        
        # B. La diagonale décalée (t+1) : Contient 1
        # C'est une matrice identité NxN
        diag_next = np.eye(N)
        
        # C. Assemblage du bloc T : On colle [diag_main] et une colonne de zéros, 
        # puis on additionne avec [zeros] et [diag_next] ? 
        # Plus simple : On crée une matrice vide N x (N+1) et on remplit.
        bloc_T = np.zeros((N, N + 1))
        
        # Remplissage "Chirurgical" via les indices
        idx = np.arange(N)
        bloc_T[idx, idx] = -(1 - vec_rho) # Position T_t (Diagonale k=0)
        bloc_T[idx, idx + 1] = 1          # Position T_t+1 (Diagonale k=1)
        
        # BLOC I et E : Zéros (L'import/export n'est pas dans l'équation thermique)
        bloc_I = np.zeros((N, N))
        bloc_E = np.zeros((N, N))
        
        # --- 3. Assemblage Final ---
        return np.hstack((bloc_x, bloc_T, bloc_I, bloc_E))

    def _build_B_thermo(self):
        """
        Construit le vecteur membre de droite (B_thermo).
        Equation Droite : rho * T_froide - C_pertes
        """
        if self.contexte is None:
            raise NotEnoughVariables("Le contexte est manquant. Veuillez le remplir.")
        if self.system_config is None:
            raise NotEnoughVariables("La configuration du système est manquante. Veuillez la remplir.")
        if self.contexte.water_draws is None:
            raise NotEnoughVariables("Les tirages d'eau sont manquants. Veuillez les remplir.")
        N = self.contexte.N
        V_total = self.system_config.volume
        T_froide = self.system_config.T_cold_water
        C_pertes_totale = self.system_config.C_pertes * self.contexte.step_minutes
        
        
        # Recalcul de rho (pour être sûr d'avoir le même vecteur)
        vec_rho = self.contexte.water_draws / V_total
        B_thermo = (vec_rho * T_froide) - C_pertes_totale
        # Application de la formule 
        # B[t] = rho[t] * T_froide - C_pertes
        
        return B_thermo
    #Les deux matrices électriques : Voir document formalisation
    def _build_A_elec(self):
        """
        Construit la matrice A_elec (Bilan Électrique).
        I - E - Pmax*x = Pnet
        """
        if self.contexte is None:
            raise NotEnoughVariables("Le contexte est manquant. Veuillez le remplir.")
        if self.system_config is None:
            raise NotEnoughVariables("La configuration du système est manquante. Veuillez la remplir.")
        N = self.contexte.N
        P_max = self.system_config.power # On récupère la puissance en Watts

        # 1. Les 4 Blocs
        bloc_x = -P_max * np.eye(N)       # Diagonale de -Pmax
        bloc_T = np.zeros((N, N + 1))     # T n'intervient pas (N lignes, N+1 colonnes)
        bloc_I = np.eye(N)                # Diagonale de 1
        bloc_E = -np.eye(N)               # Diagonale de -1

        # 2. Assemblage Horizontal (On colle les colonnes)
        return np.hstack((bloc_x, bloc_T, bloc_I, bloc_E))

    def _build_B_elec(self):
        """
        Construit le vecteur B_elec.
        B = P_maison - P_solaire
        """
        if self.contexte is None:
            raise NotEnoughVariables("Le contexte est manquant. Veuillez le remplir.")
        if self.contexte.house_consumption is None:
            raise NotEnoughVariables("La consommation domestique est manquante. Veuillez la remplir.")
        if self.contexte.solar_production is None:
            raise NotEnoughVariables("La production solaire est manquante. Veuillez la remplir.")
        return self.contexte.house_consumption - self.contexte.solar_production
    
    def C_cost(self) :
        """
        Fonction qui renvoie un vecteur ligne C de 4N+1 élément correspondant au vecteur du coût. 
        Il s'agit du vecteur, qui si multiplié à X donne le coût de la trajectoire. 
        Le problème linéaire vise à minimiser C*X. 
        Return : 
        - ndarray : Vecteur de 4N+1 éléments. 
        Raises : 
        - NotEnoughVariables : en cas de None empêchant de calculer le vecteur. 
        """ 
        prices = self.contexte.prices_purchases
        if prices is None :
            raise NotEnoughVariables("La partie des prix d'achat est vide. Veuillez la remplir.") 
        prices_sell = self.contexte.prices_sell 
        if prices_sell is None :
            raise NotEnoughVariables("La partie des prix de vente est vide. Veuillez la remplir.")  

        N = self.contexte.N 
        C_0 = np.zeros(N) 
        C_1 = np.zeros(N+1) 
        C_01 = np.concatenate((C_0,C_1)) 
        C_02 = np.concatenate((C_01,prices)) 
        C = np.concatenate((C_02,-prices_sell)) 
        return C 
    
    def C_autocons(self) :
        """
        Fonction qui retourne le vecteur C de 4N+1 éléments correspondant au vecteur d'autoconsommation.
        Ce vecteur, multiplié par X, donne l'objectif du problème linéaire à minimiser. 
        Return : 
        - ndarray : vecteur de taille 4N+1 
        Raises : 
        (Aucun) 
        """ 
        Alpha, beta = 1000, 1
        N = self.contexte.N
        alpha_pen = np.full(N,Alpha)
        beta_pen = np.full(N, beta) 
        C0 = np.zeros(N) 
        C01 = np.zeros(N+1)
        C1 = np.concatenate((C0,C01)) 
        C2 = np.concatenate((C1,alpha_pen))
        C = np.concatenate((C2,beta_pen))  
        return C 
    
    # --- GESTION DES BORNES (Nouvelle version simplifiée) ---

    def _build_lower_bounds(self):
        """
        Génère le vecteur L_B (Minorant) de taille 4N+1.
        L_B <= X
        """
        if self.contexte is None:
            raise NotEnoughVariables("Le contexte est manquant.") 
        if self.contexte.future_consigns is None :
            raise NotEnoughVariables("Les consignes futures sont manquantes, veuillez les remplir.") 
        
        N = self.contexte.N
        
        # 1. x (Pilotage) : Toujours positif ou nul
        lb_x = np.zeros(N)
        
        # 2. T (Température) : T_req (Consigne Confort + Sécurité Basse)
        # Rappel : future_consigns contient déjà le max(consigne_user, T_min_safe)
        consignes_N = self.contexte.future_consigns
        
        # Pour le point final T_N (qui n'est pas dans future_consigns), 
        # on assure au moins la sécurité minimale.
        val_Tmin_safe = self.system_config.T_min_safe
        lb_T = np.concatenate(([0], consignes_N ))        #0 car tout simplement le point initial est déjà connu. 
        
        # 3. I et E (Flux) : Toujours positifs
        lb_IE = np.zeros(N)
        
        # Assemblage : [x | T | I | E]
        return np.concatenate((lb_x, lb_T, lb_IE, lb_IE))

    def _build_upper_bounds(self):
        """
        Génère le vecteur U_B (Majorant) de taille 4N+1.
        X <= U_B
        """
        if self.contexte is None:
            raise NotEnoughVariables("Le contexte est manquant.")
            
        N = self.contexte.N
        if self.contexte.availability_on is None :
            ub_x = np.ones(N) 
        else :
            ub_x = self.contexte.availability_on.astype(float)
        
        # 2. T (Température) : T_max_safe (Sécurité Matérielle)
        val_Tmax = self.system_config.T_max_safe
        ub_T = np.full(N + 1, val_Tmax)
        
        # 3. I et E (Flux) : +Infini (Limité physiquement par le compteur, mais mathématiquement libre)
        ub_IE = np.full(N, np.inf)
        
        # Assemblage : [x | T | I | E]
        return np.concatenate((ub_x, ub_T, ub_IE, ub_IE))

    def get_bounds(self):
        """
        Retourne la liste des bornes formatée pour le solveur (scipy.linprog).
        Format : Liste de tuples [(min, max), ...] pour chaque variable du vecteur X.
        
        Note : Pour scipy, 'None' équivaut à l'infini dans les bornes.
        """
        # On génère les vecteurs bruts
        L_B = self._build_lower_bounds()
        U_B = self._build_upper_bounds()
        
        bounds_list = []
        
        # On zippe les deux vecteurs pour créer les paires
        for l, u in zip(L_B, U_B):
            # Conversion : Numpy inf -> None (standard Scipy)
            lower = l
            upper = None if u == np.inf else u
            
            bounds_list.append((lower, upper))
            
        return bounds_list

    def get_integrality_vector(self):
        """
        Renvoie le vecteur d'intégrité pour le solveur MILP.
        0 = Variable Continue (Continuous)
        1 = Variable Entière (Integer)
        
        Sera utilisé pour forcer le 'Tout-ou-Rien' si is_gradation est False.
        """
        N = self.contexte.N
        
        # Par défaut, tout le monde est continu (0)
        integrality = np.zeros(4 * N + 1)
        
        # Si le système n'a PAS de gradation (On/Off uniquement),
        # alors les variables 'x' (indices 0 à N-1) doivent être entières.
        if not self.system_config.is_gradation:
            integrality[0:N] = 1  # On force x à être 0 ou 1 strictement
            
        return integrality