"""Optimization input container combining system configuration, context, and initial conditions.

Author: @anaselb
"""


from .system_config import SystemConfig
from .external_context import ExternalContext 
from .Exceptions import NotEnoughVariables
import numpy as np 
from ...domain.features_models import OptimizationMode 


class OptimizationInputs :
    """
    Collects all variables, bounds, and objective selection required by the solver.

    Attributes
    ----------
    system_config : SystemConfig
        (configuration système) Static configuration of the heater.
    context : ExternalContext
        (contexte externe) Forecast data and constraints aligned to the horizon.
    initial_temperature : float
        (température initiale) Starting tank temperature in Celsius.
    mode : OptimizationMode
        (mode d'optimisation) Objective to optimize, cost by default.
    """
    def __init__(self, system_config : SystemConfig, 
                 context : ExternalContext, 
                 initial_temperature : float, 
                 mode : OptimizationMode = None
                 ) : 
        """
        Initialize optimisation inputs with system, context, and initial conditions.

        Parameters
        ----------
        system_config : SystemConfig
            (configuration système) Physical configuration for the heater model.
        context : ExternalContext
            (contexte externe) Forecast vectors and constraints.
        initial_temperature : float
            (température initiale) Initial water temperature in Celsius.
        mode : OptimizationMode, optional
            (mode d'optimisation) Objective selection, defaults to cost mode when None.

        Returns
        -------
        None
            (aucun retour) Stores provided inputs for solver use.
        """
        self.system_config = system_config
        self.context = context
        self.initial_temperature = initial_temperature 
        self.mode = mode 
    @property 
    def system_config(self) :
        """
        Static configuration used for optimisation.

        Returns
        -------
        SystemConfig
            (configuration système) Stored system configuration.
        """
        return self._sys_config 
    @system_config.setter 
    def system_config(self,valeur) :
        """
        Set the system configuration with strict type validation.

        Parameters
        ----------
        valeur : SystemConfig
            (configuration système) Configuration object describing the heater.

        Returns
        -------
        None
            (aucun retour) Updates the stored configuration.

        Raises
        ------
        TypeError
            (type invalide) If the provided value is not a SystemConfig instance.
        """
        if not isinstance(valeur, SystemConfig) :
            raise TypeError(f"La variable {valeur} doit être de type SystemConfig.") 
        self._sys_config = valeur 
    @property 
    def context(self) :
        """
        External context providing forecast data.

        Returns
        -------
        ExternalContext
            (contexte externe) Context aligned with the optimisation horizon.
        """
        return self._context 
    @context.setter 
    def context(self, valeur) :
        """
        Assign the external context after validating its type.

        Parameters
        ----------
        valeur : ExternalContext
            (contexte externe) Context supplying forecast vectors and constraints.

        Returns
        -------
        None
            (aucun retour) Stores the provided context.

        Raises
        ------
        TypeError
            (type invalide) If the provided value is not an ExternalContext instance.
        """
        if not isinstance(valeur, ExternalContext) :
            raise TypeError(f"La variable {valeur} doit être de type ExternalContext.") 
        self._context = valeur 
    @property 
    def initial_temperature(self) :
        """
        Initial temperature used as the starting condition.

        Returns
        -------
        float
            (température initiale) Initial tank temperature in Celsius.
        """
        return self._initial_temp 
    @initial_temperature.setter 
    def initial_temperature(self, valeur) :
        """
        Set the initial temperature with bounds checking.

        Parameters
        ----------
        valeur : float
            (température initiale) Temperature in Celsius between 0 and 100.

        Returns
        -------
        None
            (aucun retour) Stores the validated temperature.

        Raises
        ------
        TypeError
            (type invalide) If the temperature is not numeric.
        ValueError
            (température invalide) If outside the 0–100°C range.
        """
        if not isinstance(valeur, (int, float)) :
            raise TypeError(f"La variable {valeur} doit être de type int ou float.") 
        if valeur < 0 or valeur > 100 :
            raise ValueError("Veuillez entrez une valeur de la température valide. (entre 0 et 100)") 
        self._initial_temp = valeur 
    @property 
    def mode(self) :
        """
        Objective selection for optimisation.

        Returns
        -------
        OptimizationMode
            (mode d'optimisation) Current optimisation objective.
        """
        return self._mode 
    @mode.setter 
    def mode(self, mde) :
        """
        Set the optimisation mode, defaulting to cost when unspecified.

        Parameters
        ----------
        mde : OptimizationMode or None
            (mode d'optimisation) Desired optimisation objective.

        Returns
        -------
        None
            (aucun retour) Updates the stored mode.

        Raises
        ------
        TypeError
            (type invalide) If the provided value is not an OptimizationMode.
        """
        if mde is None :
            self._mode = OptimizationMode.COST
        else :
            if not isinstance(mde, OptimizationMode) :
                raise TypeError("Le mode doit être une variable du format OptimizationMode") 
            self._mode = mde 

    
    # --- PARTIE ÉGALITÉS (A_eq, B_eq) ---

    def A_eq(self):
        """
        Build the full equality constraint matrix for the optimisation problem.

        Returns
        -------
        numpy.ndarray
            (matrice égalités) Stacked matrix combining initial, thermal, and electrical constraints.

        Raises
        ------
        NotEnoughVariables
            (variables manquantes) If required context or configuration data is missing.
        """
        # On appelle les méthodes privées
        Ai = self._build_A_init() 
        At = self._build_A_thermo() 
        Ae = self._build_A_elec() 
        # On empile verticalement les matrices
        return np.vstack((Ai, At, Ae))

    def B_eq(self):
        """
        Build the right-hand side vector for equality constraints.

        Returns
        -------
        numpy.ndarray
            (vecteur égalités) Concatenated vector matching the equality matrix.

        Raises
        ------
        NotEnoughVariables
            (variables manquantes) If required inputs are missing.
        """
        Bi = self._build_B_init() 
        Bt = self._build_B_thermo() 
        Be = self._build_B_elec() 
        # On concatène les vecteurs (à plat)
        return np.concatenate((Bi, Bt, Be))

    # --- PARTIE INÉGALITÉS (A_in, B_in) ---

    def A_in(self):
        """
        Inequality constraint matrix placeholder (none defined).

        Returns
        -------
        None
            (aucune contrainte) No inequality constraints are provided.
        """
        return None 

    def B_in(self):
        """
        Inequality constraint vector placeholder (none defined).

        Returns
        -------
        None
            (aucune contrainte) No inequality constraints are provided.
        """
        return None
    
    # --- MÉTHODES PRIVÉS DE CONSTRUCTION ---
    
    def _build_A_init(self):
        """
        Construct the initial condition equality ensuring T0 equals the provided initial temperature.

        Returns
        -------
        numpy.ndarray
            (matrice initiale) Single-row matrix targeting the initial temperature variable.

        Raises
        ------
        NotEnoughVariables
            (variables manquantes) If the context is missing.
        """
        if self.context is None:
            raise NotEnoughVariables("Le contexte est manquant. Veuillez le remplir.")
        N = self.context.N         #Toujours existe pas de None. 
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
        Construct the right-hand side vector for the initial condition.

        Returns
        -------
        numpy.ndarray
            (vecteur initial) Single-element array containing the initial temperature.

        Raises
        ------
        NotEnoughVariables
            (variables manquantes) If the initial temperature is missing.
        """
        # C'est simplement la valeur scalaire stockée dans l'input
        # On renvoie un array 1D de taille 1
        if self.initial_temperature is None :
            raise NotEnoughVariables("La température initiale est manquante. Veuillez la remplir.") 
        return np.array([self.initial_temperature]) 
    # Deux matrices thermodynamiques. 
    def _build_A_thermo(self):
        """
        Build the thermal dynamics matrix linking temperatures to decisions.

        Returns
        -------
        numpy.ndarray
            (matrice thermique) Matrix encoding thermal transitions across the horizon.

        Raises
        ------
        NotEnoughVariables
            (variables manquantes) If context, system configuration, or draws are absent.
        """
        if self.context is None:
            raise NotEnoughVariables("Le contexte est manquant. Veuillez le remplir.")
        if self.system_config is None:
            raise NotEnoughVariables("La configuration du système est manquante. Veuillez la remplir.")
        if self.context.water_draws is None:
            raise NotEnoughVariables("Les tirages d'eau sont manquants. Veuillez les remplir.")
        N = self.context.N
        
        # --- 1. Calcul des Constantes Physiques ---
        # On récupère les données
        V_total = self.system_config.volume        # Litres (équivalent kg pour l'eau)
        P_max_watts = self.system_config.power     # Watts (Joules/sec)
        delta_t_min = self.context.step_minutes   # Minutes

        delta_t_sec = delta_t_min * 60             # Secondes
        C_p = 4185                                 # Capacité thermique eau (J/kg/K)
        
        # Calcul du Gain (K_gain) : Combien de degrés on gagne si on chauffe à fond pendant 1 pas
        # Formule du doc 
        K_gain = (P_max_watts * delta_t_sec) / (V_total * C_p)
        
        # Calcul du vecteur Rho (Taux de mélange) pour chaque pas t
        # Rho[t] = V_tirage[t] / V_total 
        vec_rho = self.context.water_draws / V_total
        
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
        Build the thermal right-hand side vector.

        Returns
        -------
        numpy.ndarray
            (vecteur thermique) Vector capturing cold water influence and losses.

        Raises
        ------
        NotEnoughVariables
            (variables manquantes) If required context or configuration values are missing.
        """
        if self.context is None:
            raise NotEnoughVariables("Le contexte est manquant. Veuillez le remplir.")
        if self.system_config is None:
            raise NotEnoughVariables("La configuration du système est manquante. Veuillez la remplir.")
        if self.context.water_draws is None:
            raise NotEnoughVariables("Les tirages d'eau sont manquants. Veuillez les remplir.")
        N = self.context.N
        V_total = self.system_config.volume
        T_froide = self.system_config.T_cold_water
        total_heat_loss = self.system_config.heat_loss_coefficient * self.context.step_minutes
        
        
        # Recalcul de rho (pour être sûr d'avoir le même vecteur)
        vec_rho = self.context.water_draws / V_total
        B_thermo = (vec_rho * T_froide) - total_heat_loss
        # Application de la formule 
        # B[t] = rho[t] * T_froide - heat_loss_coefficient
        
        return B_thermo
    #Les deux matrices électriques : Voir document formalisation
    def _build_A_elec(self):
        """
        Construct the electrical balance matrix relating imports, exports, and decisions.

        Returns
        -------
        numpy.ndarray
            (matrice électrique) Matrix enforcing the electrical net power equation.

        Raises
        ------
        NotEnoughVariables
            (variables manquantes) If context or configuration is absent.
        """
        if self.context is None:
            raise NotEnoughVariables("Le contexte est manquant. Veuillez le remplir.")
        if self.system_config is None:
            raise NotEnoughVariables("La configuration du système est manquante. Veuillez la remplir.")
        N = self.context.N
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
        Build the electrical right-hand side vector representing net demand.

        Returns
        -------
        numpy.ndarray
            (vecteur électrique) Vector of baseline minus solar production.

        Raises
        ------
        NotEnoughVariables
            (variables manquantes) If required consumption or production data is missing.
        """
        if self.context is None:
            raise NotEnoughVariables("Le contexte est manquant. Veuillez le remplir.")
        if self.context.house_consumption is None:
            raise NotEnoughVariables("La consommation domestique est manquante. Veuillez la remplir.")
        if self.context.solar_production is None:
            raise NotEnoughVariables("La production solaire est manquante. Veuillez la remplir.")
        return self.context.house_consumption - self.context.solar_production
    
    def C_cost(self) :
        """
        Build the cost objective vector of length 4N+1.

        Returns
        -------
        numpy.ndarray
            (vecteur de coût) Row vector that yields trajectory cost when dotted with X.

        Raises
        ------
        NotEnoughVariables
            (variables manquantes) If purchase or resale prices are unavailable.
        """ 
        prices = self.context.prices_purchases
        if prices is None :
            raise NotEnoughVariables("La partie des prix d'achat est vide. Veuillez la remplir.") 
        prices_sell = self.context.prices_sell 
        if prices_sell is None :
            raise NotEnoughVariables("La partie des prix de vente est vide. Veuillez la remplir.")  

        N = self.context.N 
        C_0 = np.zeros(N) 
        C_1 = np.zeros(N+1) 
        C_01 = np.concatenate((C_0,C_1)) 
        C_02 = np.concatenate((C_01,prices)) 
        C = np.concatenate((C_02,-prices_sell)) 
        return C 
    
    def C_autocons(self) :
        """
        Build the objective vector promoting self-consumption.

        Returns
        -------
        numpy.ndarray
            (vecteur autoconsommation) Vector of length 4N+1 used for the self-consumption objective.
        """ 
        Alpha, beta = 1000, 1
        N = self.context.N
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
        Generate the lower bounds vector L_B of size 4N+1.

        Returns
        -------
        numpy.ndarray
            (bornes inférieures) Minimum values for each optimisation variable.

        Raises
        ------
        NotEnoughVariables
            (variables manquantes) If context or future setpoints are missing.
        """
        if self.context is None:
            raise NotEnoughVariables("Le contexte est manquant.") 
        if self.context.future_setpoints is None :
            raise NotEnoughVariables("Les consignes futures sont manquantes, veuillez les remplir.") 
        
        N = self.context.N
        
        # 1. x (Pilotage) : Toujours positif ou nul
        lb_x = np.zeros(N)
        
        # 2. T (Température) : T_req (Consigne Confort + Sécurité Basse)
        # Rappel : future_setpoints contient déjà le max(consigne_user, T_min_safe)
        setpoints_vector = self.context.future_setpoints
        
        # Pour le point final T_N (qui n'est pas dans future_setpoints), 
        # on assure au moins la sécurité minimale.
        val_Tmin_safe = self.system_config.T_min_safe
        lb_T = np.concatenate(([0], setpoints_vector ))        #0 car tout simplement le point initial est déjà connu. 
        
        # 3. I et E (Flux) : Toujours positifs
        lb_IE = np.zeros(N)
        
        # Assemblage : [x | T | I | E]
        return np.concatenate((lb_x, lb_T, lb_IE, lb_IE))

    def _build_upper_bounds(self):
        """
        Generate the upper bounds vector U_B of size 4N+1.

        Returns
        -------
        numpy.ndarray
            (bornes supérieures) Maximum values for each optimisation variable.

        Raises
        ------
        NotEnoughVariables
            (variables manquantes) If context data is missing.
        """
        if self.context is None:
            raise NotEnoughVariables("Le contexte est manquant.")
            
        N = self.context.N
        if self.context.availability_on is None :
            ub_x = np.ones(N) 
        else :
            ub_x = self.context.availability_on.astype(float)
        
        # 2. T (Température) : T_max_safe (Sécurité Matérielle)
        val_Tmax = self.system_config.T_max_safe
        ub_T = np.full(N + 1, val_Tmax)
        
        # 3. I et E (Flux) : +Infini (Limité physiquement par le compteur, mais mathématiquement libre)
        ub_IE = np.full(N, np.inf)
        
        # Assemblage : [x | T | I | E]
        return np.concatenate((ub_x, ub_T, ub_IE, ub_IE))

    def get_bounds(self):
        """
        Format lower and upper bounds for consumption by the solver.

        Returns
        -------
        list of tuple
            (bornes) Sequence of (min, max) tuples for each variable, using None for infinity.

        Raises
        ------
        NotEnoughVariables
            (variables manquantes) If bound construction fails due to missing inputs.
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
        Return the integrality vector required for MILP formulations.

        Returns
        -------
        numpy.ndarray
            (intégralité) Vector marking continuous (0) or integer (1) variables.
        """
        N = self.context.N
        
        # Par défaut, tout le monde est continu (0)
        integrality = np.zeros(4 * N + 1)
        
        # Si le système n'a PAS de gradation (On/Off uniquement),
        # alors les variables 'x' (indices 0 à N-1) doivent être entières.
        if not self.system_config.is_gradation:
            integrality[0:N] = 1  # On force x à être 0 ou 1 strictement
            
        return integrality
