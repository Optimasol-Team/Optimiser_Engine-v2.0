"""Trajectory data structures and helpers for optimisation outputs.

Author: @anaselb
""" 

from enum import Enum 
from .external_context import ExternalContext
from .optimisation_inputs import OptimizationInputs 
from .system_config import SystemConfig 
import numpy as np
from .Exceptions import PermissionDeniedError, DimensionNotRespected, ContextNotDefined, NotEnoughVariables
from .warnings import UpdateRequired
import warnings 

class TrajectorySource(Enum) :
    """
    Modes describing how a trajectory was produced or is being modified.
    """

    MANUAL = "Manuel"                     # Mode par défaut. 
    SOLVER = "Solveur (Interne)"          # État solveur, le solveur a plus de droits de modifications. 
    SOLVER_DELIVERED = "Optimisé (Verrouillé)" # Résultat final du solveur. X est bloqué en écriture.
    STANDARD = "Standard (Thermostat)"    # Simulation sans intelligence sans routeur. 
    STANDARD_ROUTER = "Standard + Routeur" # Simulation avec routeur basique. 

class StandardWHType(Enum) :
    """
    Supported thermostat-driven strategies for standard water heater simulations.
    """
    SETPOINT = "Consigne"                 #Une consigne de température à suivre par le thermostat. 
    SETPOINT_OFF_PEAK = "Consigne_hc"           #Même principe mais chauffage autorisé uniquement lors des heures creuses. 


class RouterMode(Enum):
    """
    Operating strategies for the PV router simulations.
    """
    SELF_CONSUMPTION_ONLY = "Autoconsommation Pure" # Utilise uniquement le surplus solaire (Risque d'eau froide).
    COMFORT = "Confort (Solaire + Appoint Nuit)"    # Solaire le jour + Complément réseau en Heures Creuses si nécessaire.


class TrajectorySystem :
    """
    Represents a complete optimisation trajectory, including decisions and resulting flows.

    Attributes
    ----------
    config_system : SystemConfig
        (configuration système) Static configuration of the water heater.
    context : ExternalContext
        (contexte externe) Forecast data and constraints aligned to the horizon.
    initial_temperature : float
        (température initiale) Starting tank temperature in Celsius.
    x : numpy.ndarray
        (pilotage) Control vector of decisions across the horizon.
    X : numpy.ndarray
        (vecteur complet) Combined vector of decisions, temperatures, imports, and exports.
    cost : float
        (coût) Optional cached cost value for the trajectory.
    self_consumption : float
        (taux d'autoconsommation) Cached self-consumption ratio if computed.
    """
    def __init__(self, 
                 config_system : SystemConfig = None,   #La config système. 
                 context : ExternalContext = None,      #Le external context
                 initial_temperature : float = None,           #La température initiale. 
                 x : np.ndarray = None                  #Le vecteur des décisions x. 
                 ) :
        """
        Initialize a trajectory container with optional configuration and decision vector.

        Parameters
        ----------
        config_system : SystemConfig, optional
            (configuration système) Static system configuration.
        context : ExternalContext, optional
            (contexte externe) Forecast data and constraints for the horizon.
        initial_temperature : float, optional
            (température initiale) Starting tank temperature in Celsius.
        x : numpy.ndarray, optional
            (pilotage initial) Decision vector to seed the trajectory.

        Returns
        -------
        None
            (aucun retour) Prepares internal storage for trajectory data.
        """
        self._mode = TrajectorySource.MANUAL  
        self.config_system = config_system 
        self.context = context
        self.initial_temperature = initial_temperature  
        self._X = None 
        self.x = x
        self._cost = None 
        self._self_consumption = None 

    @property 
    def context(self) :
        """
        External context associated with the trajectory.

        Returns
        -------
        ExternalContext or None
            (contexte externe) Context aligned to the decision horizon.
        """
        return self._context 
    @context.setter 
    def context(self, context_value) :
        """
        Set the external context with type enforcement.

        Parameters
        ----------
        context_value : ExternalContext or None
            (contexte externe) Context carrying forecasts and constraints.

        Returns
        -------
        None
            (aucun retour) Updates the stored context.

        Raises
        ------
        TypeError
            (type invalide) If the provided value is not an ExternalContext instance.
        """
        if context_value is None :
            self._context = None 
        else :
            if not isinstance(context_value,ExternalContext) :
                raise TypeError("Le contexte doit être soit vide (None) soit une variable de type ExternalContext") 
            self._context = context_value 
        
    @property
    def X(self) :
        """
        Full trajectory vector concatenating decisions, temperatures, imports, and exports.

        Returns
        -------
        numpy.ndarray or None
            (vecteur complet) Combined optimisation variables.
        """
        return self._X 
   
    @property
    def x(self) :
        """
        Decision vector extracted from the full trajectory.

        Returns
        -------
        numpy.ndarray or None
            (pilotage) Control values over the horizon.
        """
        if self._X is None or self.context is None :
            return None 
        N = self.context.N
        return self._X[0:N] 
    
    @x.setter 
    def x(self, valeur) :
        """
        Set the decision vector while validating permissions, type, and bounds.

        Parameters
        ----------
        valeur : numpy.ndarray or None
            (pilotage) Decision values between 0 and 1 for each step.

        Returns
        -------
        None
            (aucun retour) Updates the trajectory decisions and resets cached metrics.

        Raises
        ------
        PermissionDeniedError
            (modification interdite) If the trajectory is locked.
        ContextNotDefined
            (contexte manquant) If no context is set when assigning decisions.
        NotEnoughVariables
            (configuration manquante) If system configuration is missing.
        TypeError
            (type invalide) If the provided value is not a numpy array.
        DimensionNotRespected
            (dimension incorrecte) If the vector length does not match the horizon.
        ValueError
            (valeur invalide) If decisions fall outside [0, 1] or violate non-gradation mode.
        """
        #Vérification des autorisations : 
        #if self._mode == TrajectorySource.SOLVER_DELIVERED :
           # raise PermissionDeniedError("Vous n'avez pas le droit de modifier une trajectoire livrée par le solveur") 
        if valeur is None :
            self._X = None 
            self._cost = None 
            self._self_consumption = None 
            return 
        #Vérification du contexte : 
        #Rappel : le contexte peut être None, mais s'il est pas None, il est forcément de la classe ExtenralContext
        #Dans ce cas, N est toujours défini. 
        if self.context is None :
            raise ContextNotDefined("Veuillez définir d'abord un contexte non vide") 
        if self.config_system is None :
            raise NotEnoughVariables("Veuillez mettre une config système non vide") 
        #Vérification du type :
        if not isinstance(valeur, np.ndarray) :
            raise TypeError("La valeur à mettre dans x doit être un tableau np.ndarray") 
        
        #Vérification de la dimension : 
        N = self.context.N 
        if len(valeur) != N :
            raise DimensionNotRespected(f"Le vecteur à mettre dans x doit être de taille {N}") 
        
        #Vérification du contenu de valeur : 
        for i in range(N) : 
            if valeur[i] > 1 or valeur[i] <0 :
                raise ValueError("Les élements du tableau de x ne doivent pas sortir de l'intervalle [0,1]") 
        #Vérification du respect du mode non-gradation :
        if self.config_system.is_gradation == False :
            for i in range(N) :
                if valeur[i] != 0 and valeur[i] != 1 :
                    raise ValueError("En cas d'absence du mode gradation, les valeur de x ne doivent pas être différents de 0 ou 1")
        
        a = np.full(3*N+1, np.nan, dtype=float)  
        self._X = np.concatenate((valeur.astype(float), a))
        self._cost = None 
        self._self_consumption = None 
        warnings.warn("La partie décisions (x) du vecteur objectif X a été modifiée avec succès. " \
        "Toutefois, il faut lancer la fonction update_X() afin de mettre à jour les autres éléments de X." \
        "Ceux-ci sont vides en ce moment (np.nan)", UpdateRequired) 
    
    
    @property 
    def config_system(self) :
        """
        Static system configuration used for the trajectory.

        Returns
        -------
        SystemConfig or None
            (configuration système) Configuration applied to calculations.
        """
        return self._sys_config 
    @config_system.setter 
    def config_system(self, cfg) :
        """
        Set the static configuration with type validation.

        Parameters
        ----------
        cfg : SystemConfig or None
            (configuration système) Configuration describing heater capabilities.

        Returns
        -------
        None
            (aucun retour) Stores the provided configuration.

        Raises
        ------
        TypeError
            (type invalide) If the value is not None or a SystemConfig instance.
        """
        if cfg is None :
            self._sys_config = None 
        else : 
            if not isinstance(cfg,SystemConfig) :
                raise TypeError("La configuration système doit être soit vide (None) soit une variable de type SystemConfig") 
            self._sys_config = cfg

    @property 
    def initial_temperature(self) :
        """
        Starting water temperature for the trajectory.

        Returns
        -------
        float or None
            (température initiale) Initial tank temperature in Celsius.
        """
        return self._initial_temp 
    @initial_temperature.setter 
    def initial_temperature(self, valeur) :
        """
        Define the initial temperature with validation.

        Parameters
        ----------
        valeur : float or None
            (température initiale) Starting temperature in Celsius.

        Returns
        -------
        None
            (aucun retour) Updates the initial temperature.

        Raises
        ------
        TypeError
            (type invalide) If the value is not numeric when provided.
        ValueError
            (température invalide) If outside the 0–100°C range.
        """
        if valeur is None :
            self._initial_temp = None 
            return 
        if not isinstance(valeur, (int,float)) :
            raise TypeError("La température doit être un nombre")
        if valeur < 0 or valeur > 100 :
            raise ValueError("Veuillez entrer une température d'eau liquide valide")
        self._initial_temp = valeur 

    def update_X(self):
        """
        Recompute full trajectory variables (temperatures, imports, exports) from decisions.

        Returns
        -------
        None
            (aucun retour) Updates the internal X vector and clears cached metrics.

        Raises
        ------
        NotEnoughVariables
            (variables manquantes) If required configuration, context, or initial temperature is absent.
        """
        # 1. Vérifications de base
        if self._X is None:
            raise NotEnoughVariables("Le vecteur x n'est pas défini.")
        if self.config_system is None or self.context is None or self.initial_temperature is None:
            raise NotEnoughVariables("Variables manquantes (Config, Contexte ou T_init) pour le calcul.")

        N = self.context.N
        step_min = self.context.step_minutes # On récupère le pas (ex: 15)
        
        # On extrait le vecteur de pilotage x (les N premiers éléments de X)
        x_decisions = self._X[0:N]
        
        # --- A. CALCUL ÉLECTRIQUE (Vectorisé - Ne change pas) ---
        puissance_W = x_decisions * self.config_system.power
        p_net = self.context.house_consumption - self.context.solar_production + puissance_W
        I_vec = np.maximum(0, p_net)
        E_vec = np.maximum(0, -p_net)
        
        # --- B. CALCUL THERMIQUE (Boucle de simulation) ---
        T_vec = np.zeros(N + 1)
        T_vec[0] = self.initial_temperature
        
        # Préparation des constantes
        V = self.config_system.volume
        Cp = 4185 
        dt_sec = step_min * 60
        
        # Gain en °C pour 100% de chauffe pendant un pas de temps
        K_gain = (self.config_system.power * dt_sec) / (V * Cp)
        
        # Perte en °C pour UN pas de temps (Coefficient en °C/min * nombre de minutes)
        loss_per_step = self.config_system.heat_loss_coefficient * step_min # CORRECTION ICI
        
        T_cold = self.config_system.T_cold_water
        rho_vec = self.context.water_draws / V
        
        for t in range(N):
            T_prev = T_vec[t]
            rho = rho_vec[t]
            x_val = x_decisions[t]
            
            # Formule linéaire : Mélange + Chauffe - Pertes du pas
            T_next = T_prev * (1 - rho) + (rho * T_cold) + (K_gain * x_val) - loss_per_step
            
            # Sécurité physique (L'eau ne descend pas en dessous de l'eau froide)
            T_vec[t+1] = max(T_next, T_cold)
            
        # --- C. ASSEMBLAGE ET NETTOYAGE ---
        # On concatène pour former le vecteur X complet [x, T, I, E]
        self._X = np.concatenate((x_decisions, T_vec, I_vec, E_vec))
        
        # On invalide les caches de coût et d'autoconsommation pour forcer le recalcul
        self._cost = None
        self._self_consumption = None
   
    def make_solver_traj(self) :
        """
        Switch the trajectory mode to SOLVER to permit solver updates.

        Returns
        -------
        None
            (aucun retour) Grants solver-level modification rights.
        """
        self._mode = TrajectorySource.SOLVER

    def make_solver_delivered_traj(self) :
        """
        Lock the trajectory after solver delivery.

        Returns
        -------
        None
            (aucun retour) Prevents further modifications to the trajectory vector.
        """
        self._mode = TrajectorySource.SOLVER_DELIVERED

    
    def upload_X_vector(self, x : np.ndarray) :
        """
        Inject a fully computed trajectory vector produced externally.

        Parameters
        ----------
        x : numpy.ndarray
            (vecteur complet) Full concatenated vector of size 4N+1.

        Returns
        -------
        None
            (aucun retour) Stores the provided vector and clears cached metrics.

        Raises
        ------
        PermissionDeniedError
            (modification interdite) If the trajectory is not in solver mode.
        TypeError
            (type invalide) If the provided value is not a numpy array.
        DimensionNotRespected
            (dimension incorrecte) If the vector length does not match 4N+1.
        """

        #Vérification de l'autorisation : 
        if self._mode == TrajectorySource.MANUAL or self._mode == TrajectorySource.SOLVER_DELIVERED :
            raise PermissionDeniedError("Vous n'êtes pas autorisés à modifier le vecteur objectif X")
        
        #Vérification du type de x : 
        if not isinstance(x,np.ndarray) :
            raise TypeError("Le type du vecteur doit être un np.ndarray") 
        
        #Vérification du nombre d'éléments : 
        N = self.context.N
        if np.shape(x) != (4*N+1,) :
            raise DimensionNotRespected(f"La dimension de X doit être 4x{N}+1 soit {4*N+1}") 
        
        #Maintenant tout est vérifié : 
        self._X = x 
        self._cost = None
        self._self_consumption = None 

    def upload_cost(self, cost) :
        """
        Allow the solver to set the cost without recomputation.

        Parameters
        ----------
        cost : float
            (coût) Total cost computed by the solver.

        Returns
        -------
        None
            (aucun retour) Caches the provided cost value.

        Raises
        ------
        PermissionDeniedError
            (modification interdite) If the trajectory is not in solver mode.
        TypeError
            (type invalide) If the cost is not numeric.
        """ 
        #Vérifier l'autorisation : 
        if self._mode == TrajectorySource.MANUAL or self._mode == TrajectorySource.SOLVER_DELIVERED :
            raise PermissionDeniedError("Vous n'êtes pas autorisés à modifier le cout de la trajectoire à partir de cette fonction") 
        if not isinstance(cost,(int,float)) :
            raise TypeError("Le type du coût doit être un nombre") 
        self._cost = cost 

    ###Les gets sur les parties du X###############################
    def get_decisions(self) :
        """
        Retrieve the decision vector from the trajectory.

        Returns
        -------
        numpy.ndarray or None
            (pilotage) Control values across the horizon.
        """
        return self.x 
    
    def get_temperatures(self) :
        """
        Extract the temperature segment from the full trajectory vector.

        Returns
        -------
        numpy.ndarray or None
            (températures) Temperatures for each step including the initial point.

        Raises
        ------
        DimensionNotRespected
            (dimension incorrecte) If the stored vector length does not follow 4N+1 format.
        """
        A = self.X 
        if A is None :
            return None 
        B = len(A) 
        if (B-1)%4 != 0 :
            raise DimensionNotRespected(f"Le vecteur X a la taille {B} donc n'a pas la bonne dimension sous la forme de 4*N+1") 
        N = (B-1)//4 
        return self.X[N:2*N+1] 
    
    def get_exports(self) :
        """
        Extract the export vector from the trajectory.

        Returns
        -------
        numpy.ndarray or None
            (exportations) Energy exported at each step.

        Raises
        ------
        DimensionNotRespected
            (dimension incorrecte) If the stored vector length does not follow 4N+1 format.
        """
        A = self.X 
        if A is None :
            return None 
        B = len(A) 
        if (B-1)%4 != 0 :
            raise DimensionNotRespected(f"Le vecteur X a la taille {B} donc n'a pas la bonne dimension sous la forme de 4*N+1") 
        
        N = (B-1)//4 
        return self.X[3*N+1:4*N+1] 
    
    def get_imports(self) :
        """
        Extract the import vector from the trajectory.

        Returns
        -------
        numpy.ndarray or None
            (importations) Energy imported at each step.

        Raises
        ------
        DimensionNotRespected
            (dimension incorrecte) If the stored vector length does not follow 4N+1 format.
        """
        A = self.X 
        if A is None :
            return None 
        B = len(A) 
        if (B-1)%4 != 0 :
            raise DimensionNotRespected(f"Le vecteur X a la taille {B} donc n'a pas la bonne dimension sous la forme de 4*N+1") 
        
        N = (B-1)//4 
        return self.X[2*N+1:3*N+1]  
    ###################################################################

    def compute_cost(self) :
        """
        Calculate the monetary cost of the trajectory using context prices.

        Returns
        -------
        float
            (coût) Total cost in currency units over the horizon.

        Raises
        ------
        ContextNotDefined
            (contexte manquant) If no context is attached to the trajectory.
        NotEnoughVariables
            (variables manquantes) If price vectors or derived flows are unavailable.
        DimensionNotRespected
            (dimension incorrecte) If vector dimensions do not match the horizon length.
        """
        #if self._mode == TrajectorySource.SOLVER_DELIVERED :
            #return self._cost 
        if self._cost is not None :
            return self._cost 
        
        # Vérifications de base du contexte
        if self.context is None:
            raise ContextNotDefined("Veuillez définir d'abord un contexte non vide")

        # Accès aux vecteurs de prix du contexte
        prices_purchase = self.context.prices_purchases
        prices_sell = self.context.prices_sell
        step_minutes = self.context.step_minutes
        #step_minutes = getattr(self.context, 'step_minutes', None)

        # Import local de l'Exception pour respecter la contrainte de modification limitée
        from .Exceptions import NotEnoughVariables

        # Vérifications de complétude des données de prix
        if prices_purchase is None or prices_sell is None:
            raise NotEnoughVariables("Les vecteurs de prix (achat/revente) sont manquants dans le contexte")
        # Vérification du pas de temps
        if step_minutes is None or not isinstance(step_minutes, int) or step_minutes <= 0:
            raise NotEnoughVariables("Le pas de temps (step_minutes) du contexte est manquant ou invalide")

        # Récupération des importations/exportations
        try :
            exports = self.get_exports()
            imports = self.get_imports()
        except DimensionNotRespected :
            raise DimensionNotRespected("Le vecteur X n'est pas correctement dimensionné pour extraire importations/exportations")
        # Vérifications de présence des vecteurs issus de X
        if exports is None or imports is None:
            raise NotEnoughVariables("Les vecteurs d'importations/exportations sont manquants (X non initialisé)")
        
        # Vérification des dimensions
        N = self.context.N
        if len(prices_purchase) != N or len(prices_sell) != N or len(exports) != N or len(imports) != N:
            raise DimensionNotRespected("Les dimensions des vecteurs (prix/import/export) ne correspondent pas à N")

        # Calcul du coût: convertir puissances (kW) en énergies (kWh)
        dt_hours = step_minutes / 60.0
        cost = float(dt_hours * (np.dot(imports, prices_purchase) - np.dot(exports, prices_sell))) / 1000 
        self._cost = cost
        return cost
    

    def compute_self_consumption(self):
        """
        Compute the self-consumption ratio of the trajectory.

        Returns
        -------
        float
            (taux d'autoconsommation) Ratio of solar production consumed locally.

        Raises
        ------
        ContextNotDefined
            (contexte manquant) If no context is attached.
        NotEnoughVariables
            (variables manquantes) If exports or solar production are unavailable.
        UpdateRequired
            (mise à jour requise) If the trajectory needs recomputation before evaluation.
        """
        if self._self_consumption is not None :
            return self._self_consumption 
        # 1. Vérifications (On a besoin de l'Export et de la Prod Solaire)
        if self.context is None:
            raise ContextNotDefined("Contexte manquant")
        
        exports = self.get_exports() # Vecteur E (Watts)
        solar_production_vector = self.context.solar_production # Vecteur P_pv (Watts)
        
        # Vérifier None AVANT np.isnan()
        if exports is None:
            raise NotEnoughVariables("Les exportations ne sont pas calculées (X non initialisé)")
        if solar_production_vector is None:
            raise NotEnoughVariables("La production solaire (solar_production) est manquante dans le contexte")
        if np.isnan(exports).any():
            raise UpdateRequired("Veuillez lancer update_X() avant de calculer l'autoconsommation.")
    
        # 2. Calcul des énergies (Somme des puissances * pas de temps)
        # Astuce : Comme le pas de temps est constant en haut et en bas de la division, 
        # on peut travailler directement en somme de Watts, les unités s'annulent pour le ratio.
        
        total_prod = np.sum(solar_production_vector)
        total_export = np.sum(exports)
        
        # Sécurité division par zéro (si pas de soleil, ex: nuit)
        if total_prod == 0:
            self._self_consumption = 0.0
            return 0.0

        # L'autoconsommation, c'est ce qu'on a produit MOINS ce qu'on a jeté (exporté)
        # Note : On suppose ici que l'export vient uniquement du solaire.
        autoconsom = total_prod - total_export
        
        # Ratio
        ratio = autoconsom / total_prod
        
        # On stocke en interne
        self._self_consumption = ratio
        return ratio


    @classmethod 
    def from_optimization_input(cls,inputs : OptimizationInputs) :
        """
        Instantiate an empty trajectory using optimisation inputs.

        Parameters
        ----------
        inputs : OptimizationInputs
            (données d'optimisation) Input structure containing configuration and context.

        Returns
        -------
        TrajectorySystem
            (trajectoire) Trajectory initialized with configuration and initial temperature.
        """ 
        config = inputs.system_config
        context = inputs.context
        initial_temperature = inputs.initial_temperature 
        return cls(config,context,initial_temperature) 
    
    @classmethod
    def generate_standard_trajectory(cls, 
                                     context : ExternalContext = None, 
                                     config_system : SystemConfig = None, 
                                     initial_temperature : float = None, 
                                     mode_WH : StandardWHType = None, 
                                     setpoint_temperature : float = None
                                     ) :
        """
        Generate a trajectory simulating a standard thermostat-controlled heater.

        Parameters
        ----------
        context : ExternalContext
            (contexte externe) Forecast data required for the simulation.
        config_system : SystemConfig
            (configuration système) Physical parameters of the heater.
        initial_temperature : float
            (température initiale) Starting water temperature in Celsius.
        mode_WH : StandardWHType, optional
            (mode chauffe-eau) Thermostat behaviour to emulate; defaults to SETPOINT.
        setpoint_temperature : float, optional
            (consigne de température) Target temperature for thermostat logic.

        Returns
        -------
        TrajectorySystem
            (trajectoire) Simulated trajectory without optimisation.

        Raises
        ------
        ContextNotDefined
            (contexte manquant) If the context is not provided.
        NotEnoughVariables
            (variables manquantes) If required configuration or temperatures are missing.
        TypeError
            (type invalide) If inputs have incorrect types.
        ValueError
            (valeur invalide) If the provided temperatures are outside acceptable bounds.
        """
        if context is None :
            raise ContextNotDefined("Le contexte est vide, il doit être rempli L'opération ne peut pas aboutir") 
        if config_system is None :
            raise NotEnoughVariables("Les configurations système sont manquantes, l'opération ne peut pas aboutir") 
        if initial_temperature is None :
            raise NotEnoughVariables("La température initiale est manquante, l'opération ne peut pas aboutir.") 
        if not isinstance(initial_temperature, (int, float)) :
            raise TypeError("La température initiale doit être un entier ou un réel.") 
        if initial_temperature < 0 or initial_temperature > 100 :
            raise ValueError("Veuillez entre une température d'eau liquide valide (entre 0 et 100)") 
        
        if mode_WH is None :
            mode_WH = StandardWHType.SETPOINT
        if not isinstance(mode_WH,(StandardWHType)) :
            raise TypeError("Le mode de chauffe-eau est invalide, l'opération ne peut pas aboutir") 
        
        if setpoint_temperature is None :
            #Essayons de la déduire du contexte : 
            A = context.future_setpoints 
            if A is None :
                raise NotEnoughVariables("La température de consigne est manquante, et elle ne peut pas être déduite du contexte. L'opération ne peut pas aboutir.") 
            setpoint_temperature = np.max(A) 

        if not isinstance(setpoint_temperature, (int, float)) :
            raise TypeError("La température de consigne doit être un nombe, l'opération ne peut pas aboutir.") 

        #Maintenant on possède toutes les informations, toutes les erreurs sont gérés, les valeurs vides éventuels sont remplis. 
        N = context.N
        # --- 1. Préparation des Constantes Physiques (Cohérence avec update_X) ---
        V = config_system.volume
        Cp = 4185 # J/kg/K
        dt_sec = context.step_minutes * 60
        
        # K_gain : Combien de degrés on gagne en chauffant à fond pendant 1 pas
        K_gain = (config_system.power * dt_sec) / (V * Cp)
        
        heat_loss_coefficient = config_system.heat_loss_coefficient
        T_cold = config_system.T_cold_water
        
        # On prépare le vecteur des tirages (rho) et le signal réseau
        rho_vec = context.water_draws / V
        
        # Gestion sécurisée du signal HP/HC (si le contexte n'a pas le vecteur, on suppose que ça marche tout le temps)
        grid_signal = getattr(context, 'off_peak_hours', None) 
        if grid_signal is None:
            grid_signal = np.ones(N) # Par défaut : Courant disponible 24/24 (Mode BASE ou Manquant)

        # --- 2. Boucle de Simulation Temporelle (Causalité) ---
        x = np.zeros(N)
        current_temperature = initial_temperature # C'est notre T_i qui va évoluer
        loss_per_step = heat_loss_coefficient * context.step_minutes
        for t in range(N):
            # --- A. PRISE DE DÉCISION (Le Thermostat) ---
            
            # 1. Le besoin : Est-ce que l'eau est trop froide ?
            need_heating = current_temperature < setpoint_temperature
            
            # 2. La contrainte : Est-ce que j'ai du courant ?
            # Par défaut (Mode CONSIGNE simple), on a toujours le droit
            allowed_to_heat = True 
            
            # Si on est en mode HC, on dépend du signal réseau
            if mode_WH == StandardWHType.SETPOINT_OFF_PEAK:
                if grid_signal[t] == 0: # 0 signifie coupure (Heures Pleines)
                    allowed_to_heat = False
            
            # 3. Action : On chauffe si Besoin ET Droit
            if need_heating and allowed_to_heat:
                x[t] = 1
            else:
                x[t] = 0
            
            # --- B. CONSÉQUENCE PHYSIQUE (Calcul de T_i+1) ---
            
            rho = rho_vec[t] # La proportion d'eau tirée à cet instant
            
            # La formule magique (Conservation de l'énergie) :
            # T_next = (Eau restante à T_actuelle) + (Eau froide entrante) + (Chauffe) - (Pertes)
            T_next = current_temperature * (1 - rho) + (rho * T_cold) + (K_gain * x[t]) - loss_per_step
    
            # Sécurité : l'eau ne peut pas être plus froide que l'eau du réseau
            current_temperature = max(T_next, T_cold)

        # --- 3. Finalisation ---
        # On crée l'objet Trajectoire avec le vecteur x qu'on vient de construire
        traj = cls(config_system, context, initial_temperature, x)
        
        # On lance update_X() pour qu'il recalcule tout le reste proprement (Coûts, vecteurs T, I, E...)
        #traj.update_X() 
        
        return traj

    @classmethod 
    def generate_router_only_trajectory(cls, 
                                        context : ExternalContext = None, 
                                        config_system : SystemConfig = None, 
                                        initial_temperature : float = None, 
                                        router_mode : RouterMode = None, # Nouveau paramètre Enum
                                        setpoint_temperature : float = None
                                        ) :
        """
        Simulate a trajectory driven by a solar router strategy.

        Parameters
        ----------
        context : ExternalContext
            (contexte externe) Forecast data for the simulation.
        config_system : SystemConfig
            (configuration système) Physical parameters of the heater.
        initial_temperature : float
            (température initiale) Starting water temperature in Celsius.
        router_mode : RouterMode, optional
            (mode routeur) Router behaviour to apply; defaults to comfort mode.
        setpoint_temperature : float, optional
            (consigne de température) Thermostat setpoint for router decisions.

        Returns
        -------
        TrajectorySystem
            (trajectoire) Simulated trajectory under router control.

        Raises
        ------
        NotEnoughVariables
            (variables manquantes) If required context or configuration is absent.
        TypeError
            (type invalide) If inputs are of incorrect types.
        """
        
        # --- 1. Vérifications & Initialisation ---
        if context is None or config_system is None:
             raise NotEnoughVariables("Contexte ou Configuration manquante pour la simulation routeur.")
        if initial_temperature is None:
             raise NotEnoughVariables("Température initiale manquante.")
        if router_mode is None:
            # Par défaut, on choisit le mode CONFORT (le plus réaliste pour un foyer normal)
            router_mode = RouterMode.COMFORT
        
        # Constantes Physiques
        N = context.N
        V = config_system.volume
        Cp = 4185 
        dt_sec = context.step_minutes * 60
        
        P_nominale = config_system.power # Puissance max de la résistance (en Watts)
        K_gain = (P_nominale * dt_sec) / (V * Cp)
        heat_loss_coefficient = config_system.heat_loss_coefficient
        T_cold = config_system.T_cold_water
        
        rho_vec = context.water_draws / V
        
        # Données vectorielles du Contexte
        solar_production_vector = context.solar_production
        house_consumption_vector = context.house_consumption # Conso basale (hors chauffe-eau)
        
        # Récupération sécurisée du signal HC/HP (pour le mode Confort)
        grid_signal = getattr(context, 'off_peak_hours', None)
        if grid_signal is None:
            # Si pas d'info, on suppose que le réseau est toujours dispo (Comportement Base)
            grid_signal = np.ones(N)

        # Déduction de la consigne (Thermostat mécanique du routeur)
        if setpoint_temperature is None:
            setpoint_temperature = config_system.T_max_safe 

        # --- 2. Boucle de Simulation (Causalité) ---
        x_vec = np.zeros(N)
        T_vec = np.zeros(N + 1)
        
        current_temperature = initial_temperature
        T_vec[0] = current_temperature
        
        for t in range(N):
            # --- A. LOGIQUE DÉCISIONNELLE DU ROUTEUR ---
            
            # 1. Sécurité Thermostat (Priorité Absolue)
            # Si l'eau est déjà assez chaude, le routeur coupe tout (même le solaire).
            if current_temperature >= setpoint_temperature:
                x_decision = 0.0
            else:
                # 2. Stratégie Solaire (Divertissement de surplus)
                # Le routeur mesure le surplus net à l'instant t
                surplus_W = solar_production_vector[t] - house_consumption_vector[t]
                
                x_solaire = 0.0
                if surplus_W > 0:
                    # Gradation : On injecte proportionnellement (Ex: 500W surplus / 2000W résistance = 0.25)
                    # On sature à 1.0 (on ne peut pas injecter plus que la puissance de la résistance)
                    x_solaire = min(surplus_W / P_nominale, 1.0)
                
                # 3. Stratégie Appoint Réseau (Mode Confort uniquement)
                x_backup = 0.0
                if router_mode == RouterMode.COMFORT:
                    # Si on est en Heures Creuses (Signal=1) ET qu'on a besoin de chauffer
                    is_hc = (grid_signal[t] == 1)
                    if is_hc:
                        # Le routeur force la chauffe à fond (Relais ou Triac à 100%)
                        x_backup = 1.0
                
                # 4. Mixage Final
                # Le routeur prend la source la plus forte. 
                # (En HC, si x_backup=1, on chauffe à fond quel que soit le solaire).
                # (En HP, x_backup=0, on ne chauffe qu'au solaire).
                x_decision = max(x_solaire, x_backup)
            
            x_vec[t] = x_decision
            
            # --- B. CALCUL PHYSIQUE (Mise à jour de T pour t+1) ---
            rho = rho_vec[t]
            
            loss_per_step = heat_loss_coefficient * context.step_minutes
            T_next = current_temperature * (1 - rho) + (rho * T_cold) + (K_gain * x_decision) - loss_per_step
    
            current_temperature = max(T_next, T_cold)
            T_vec[t+1] = current_temperature

        # --- 3. Construction Optimisée de l'Objet (Sans Warnings) ---
        
        # Calcul du bilan électrique pour remplir I et E
        puissance_ce_W = x_vec * P_nominale
        
        # Bilan Net au compteur : Conso Maison - Solaire + Conso CE
        # (Si le CE consomme exactement le surplus, p_net sera proche de 0)
        p_net = house_consumption_vector - solar_production_vector + puissance_ce_W
        
        I_vec = np.maximum(0, p_net)  # Importation (Achat réseau)
        E_vec = np.maximum(0, -p_net) # Exportation (Injection réseau)
        
        # Instanciation vide pour éviter le setter public
        traj = cls(config_system, context, initial_temperature)
        
        # Injection directe dans les "tripes" de l'objet
        traj._X = np.concatenate((x_vec, T_vec, I_vec, E_vec))
        
        # Note : On ne lance pas update_X() car on vient de faire tous les calculs nous-mêmes.
        return traj 
