"""Service orchestrating optimisation steps to produce heater trajectories.

Author: @anaselb
""" 
from ..domain import Client 
import pandas as pd
from datetime import datetime, timedelta

from .models.system_config import SystemConfig
from .models.external_context import ExternalContext
from .models.optimisation_inputs import OptimizationInputs
from .models.trajectory import TrajectorySystem, StandardWHType, RouterMode
from solver import Solver 
import numpy as np 
from .models.Exceptions import WeatherNotValid , SolverFailed



class OptimizerService :
    """
    Coordinates data preparation and solver execution for client trajectories.

    Attributes
    ----------
    horizon : float
        (horizon en heures) Duration of the optimisation window in hours.
    step_minutes : float
        (pas en minutes) Discretisation step used for the optimisation in minutes.
    """
    min_step_minutes = 5 #5 minutes. 
    MAX_HORIZON_HOURS = 48 #48 heures. 
    MIN_HORIZON_HOURS = 1 #Pas moins d'une heure. 
    MIN_WATER_HEATER_TEMP = 5 #En celsius. 
    MAX_WATER_HEATER_TEMP = 99  #En celsius. 
    def __init__(self, horizon_hours : float = 24, step_minutes : float = 15) :
        """
        Initialize the service with horizon and step settings.

        Parameters
        ----------
        horizon_hours : float, optional
            (horizon en heures) Optimisation window length in hours.
        step_minutes : float, optional
            (pas en minutes) Time step used in minutes.

        Returns
        -------
        None
            (aucun retour) Sets the service configuration values.
        """
        self.horizon = horizon_hours #L'horizon en heures
        self.step_minutes = step_minutes         #LE pas en minutes. 
    
    @property 
    def horizon(self) :
        """
        Optimisation horizon length in hours.

        Returns
        -------
        float
            (horizon en heures) Duration of the optimisation window.
        """
        return self._horizon 
    @horizon.setter 
    def horizon(self, valeur) :
        """
        Set the optimisation horizon while enforcing service limits.

        Parameters
        ----------
        valeur : float
            (horizon en heures) Requested horizon length in hours.

        Returns
        -------
        None
            (aucun retour) Updates the stored horizon.

        Raises
        ------
        ValueError
            (horizon invalide) If the value falls outside allowed bounds.
        """
        a = OptimizerService.MAX_HORIZON_HOURS
        b = OptimizerService.MIN_HORIZON_HOURS
        if b <= valeur <= a :
            self._horizon = valeur 
        else :
            raise ValueError(f"L'horizon doit être en heures, et doit être entre {a} et {b} heures.") 
         


    @property
    def step_minutes(self) :
        """
        Duration of each optimisation step in minutes.

        Returns
        -------
        float
            (pas en minutes) Step size for discretisation.
        """
        return self._step_minutes 
    @step_minutes.setter 
    def step_minutes(self,valeur) :
        """
        Set the optimisation step size with boundary checks.

        Parameters
        ----------
        valeur : float
            (pas en minutes) Desired step length in minutes.

        Returns
        -------
        None
            (aucun retour) Updates the stored step size.

        Raises
        ------
        ValueError
            (pas invalide) If the step exceeds half the horizon or falls below the minimum.
        """
        if valeur/60 > self._horizon /2 :
            raise ValueError("Le pas ne doit pas dépasser la moitié de l'horizon") 
        elif valeur < OptimizerService.min_step_minutes :
            raise ValueError(f"Le pas ne peut pas être inférieur à {OptimizerService.min_step_minutes} minutes") 
        else :
            self._step_minutes = valeur 

    def trajectory_of_client(self, 
                            client : Client, 
                            start_datetime : datetime, 
                            initial_temperature : float, 
                            production_df : pd.DataFrame) :
        """
        Run the optimisation workflow for a client using a solver-backed trajectory.

        Parameters
        ----------
        client : Client
            (client) Client definition containing constraints and assets.
        start_datetime : datetime.datetime
            (date de début) Start timestamp for the horizon.
        initial_temperature : float
            (température initiale) Starting water temperature in Celsius.
        production_df : pandas.DataFrame
            (production solaire) DataFrame of solar production indexed by datetime.

        Returns
        -------
        TrajectorySystem
            (trajectoire optimisée) Optimised trajectory returned by the solver.

        Raises
        ------
        WeatherNotValid
            (données invalides) If the production data fails validation.
        SolverFailed
            (échec du solveur) If the solver cannot produce a trajectory.
        """
        
        
        try :
            df_normalized = self._normalize_df(production_df, start_datetime)
        except ValueError :
            raise WeatherNotValid("Le dataframe de la productions n'est pas valide.")
        
        production_array = self._to_array(df_normalized)
        #On construit un input à partir de ça : 
        sys_config = SystemConfig.from_client(client = client) 
        ext_context = ExternalContext.from_client(client = client, 
                                                  reference_datetime=start_datetime, 
                                                  solar_productions= production_array, 
                                                  horizon=self.horizon,
                                                  time_step_minutes=self.step_minutes) 
        inputs = OptimizationInputs(sys_config, ext_context, initial_temperature, client.features.mode) 
        solver = Solver() 
        try :
            trajectory = solver.solve(inputs) 
        except RuntimeError :
            raise SolverFailed("Le solveur a échoué.")

        return trajectory
    
    def trajectory_of_client_standard(self, 
                            client : Client, 
                            start_datetime : datetime, 
                            initial_temperature : float, 
                            production_df : pd.DataFrame, 
                            mode_WH : StandardWHType = None, 
                            setpoint_temperature : float = None ) :
        """
        Generate a standard thermostat-based trajectory without optimisation.

        Parameters
        ----------
        client : Client
            (client) Client definition to simulate.
        start_datetime : datetime.datetime
            (date de début) Reference timestamp for the simulation.
        initial_temperature : float
            (température initiale) Starting water temperature in Celsius.
        production_df : pandas.DataFrame
            (production solaire) Solar production data indexed by datetime.
        mode_WH : StandardWHType, optional
            (mode chauffe-eau) Thermostat strategy to emulate.
        setpoint_temperature : float, optional
            (consigne de température) Target temperature for thermostat logic.

        Returns
        -------
        TrajectorySystem
            (trajectoire simulée) Simulated trajectory under standard control.

        Raises
        ------
        WeatherNotValid
            (données invalides) If production data fails validation.
        """
        try :
            df_normalized = self._normalize_df(production_df, start_datetime)
        except ValueError :
            raise WeatherNotValid("Le dataframe de la productions n'est pas valide.")
        
        production_array = self._to_array(df_normalized)
        sys_config = SystemConfig.from_client(client = client) 
        ext_context = ExternalContext.from_client(client = client, 
                                                  reference_datetime=start_datetime, 
                                                  solar_productions= production_array, 
                                                  horizon=self.horizon,
                                                  time_step_minutes=self.step_minutes) 
        trajectory = TrajectorySystem.generate_standard_trajectory(ext_context,sys_config,initial_temperature,mode_WH, setpoint_temperature) 
        return trajectory 
    
    def trajectory_of_client_router(self, 
                            client : Client, 
                            start_datetime : datetime, 
                            initial_temperature : float, 
                            production_df : pd.DataFrame, 
                            router_mode : RouterMode = None, 
                            setpoint_temperature : float = None ) :
        """
        Generate a trajectory using a router-only simulation strategy.

        Parameters
        ----------
        client : Client
            (client) Client definition to simulate.
        start_datetime : datetime.datetime
            (date de début) Reference timestamp for the simulation.
        initial_temperature : float
            (température initiale) Starting water temperature in Celsius.
        production_df : pandas.DataFrame
            (production solaire) Solar production data indexed by datetime.
        router_mode : RouterMode, optional
            (mode routeur) Router behaviour to apply.
        setpoint_temperature : float, optional
            (consigne de température) Thermostat setpoint for router logic.

        Returns
        -------
        TrajectorySystem
            (trajectoire simulée) Simulated router-based trajectory.

        Raises
        ------
        WeatherNotValid
            (données invalides) If production data fails validation.
        """
        try :
            df_normalized = self._normalize_df(production_df, start_datetime)
        except ValueError :
            raise WeatherNotValid("Le dataframe de la productions n'est pas valide.")
        
        production_array = self._to_array(df_normalized)
        sys_config = SystemConfig.from_client(client = client) 
        ext_context = ExternalContext.from_client(client = client, 
                                                  reference_datetime=start_datetime, 
                                                  solar_productions= production_array, 
                                                  horizon=self.horizon,
                                                  time_step_minutes=self.step_minutes) 
        trajectory = TrajectorySystem.generate_router_only_trajectory(ext_context,sys_config,initial_temperature, router_mode, setpoint_temperature) 

        return trajectory 

    
    def _is_df_valid(self, df: pd.DataFrame, start: datetime, end: datetime) -> bool:
        """
        Validate that a DataFrame covers the required interval with acceptable gaps.

        Parameters
        ----------
        df : pandas.DataFrame
            (données solaires) DataFrame with a datetime index or column.
        start : datetime.datetime
            (début) Start of the required interval.
        end : datetime.datetime
            (fin) End of the required interval.

        Returns
        -------
        bool
            (validité) True if coverage and sampling are acceptable, False otherwise.

        Raises
        ------
        TypeError
            (type invalide) If df is not a DataFrame.
        ValueError
            (données invalides) If no datetime index or column exists.
        """
        # 1. Vérification des types
        if not isinstance(df, pd.DataFrame):
            raise TypeError("L'argument 'df' doit être un pandas DataFrame.")

        if df.empty:
            return False

        # 2. Identification de la série temporelle
        time_series = None
        
        # Cas A : L'index est déjà des dates
        if pd.api.types.is_datetime64_any_dtype(df.index):
            time_series = df.index.to_series()
        else:
            # Cas B : On cherche une colonne de type datetime
            datetime_cols = [col for col in df.columns if pd.api.types.is_datetime64_any_dtype(df[col])]
            if not datetime_cols:
                raise ValueError("Le DataFrame fourni ne contient aucune colonne de type date/datetime.")
            time_series = df[datetime_cols[0]]

        # 3. Vérification de la couverture temporelle
        # Le min du DF doit être <= start ET le max du DF doit être >= end
        if time_series.min() > start or time_series.max() < end:
            # print(f"Couverture insuffisante : [{time_series.min()} à {time_series.max()}] vs attendu [{start} à {end}]")
            return False

        # 4. Vérification du "Max Gap" (Trou dans les données)
        # On calcule l'écart entre chaque point consécutif
        diffs = time_series.sort_values().diff().dropna()
        
        # Conversion des différences en minutes
        max_gap_minutes = diffs.max().total_seconds() / 60
        limit_gap = 4 * self.step_minutes
        
        if max_gap_minutes > limit_gap:
            # print(f"Gap temporel trop grand détecté : {max_gap_minutes} min (Limite : {limit_gap} min)")
            return False

        return True

    def _normalize_df(self, df: pd.DataFrame, start_datetime: datetime) -> pd.DataFrame:
        """
        Align and interpolate production data to the service horizon and step.

        Parameters
        ----------
        df : pandas.DataFrame
            (données solaires) Raw production data to normalise.
        start_datetime : datetime.datetime
            (référence temporelle) Start of the optimisation horizon.

        Returns
        -------
        pandas.DataFrame
            (données normalisées) Cleaned and resampled DataFrame covering the full horizon.

        Raises
        ------
        ValueError
            (données invalides) If the DataFrame lacks sufficient coverage or has large gaps.
        """
        # 1. Calcul de la fin absolue de l'horizon
        fin_horizon = start_datetime + timedelta(hours=self.horizon)

        # 2. Validation de la couverture
        # On passe les bornes absolues (datetime) et non un objet Creneau
        if not self._is_df_valid(df, start_datetime, fin_horizon):
            raise ValueError(f"Le DataFrame fourni ne couvre pas la période {start_datetime} -> {fin_horizon} ou contient des trous > {4*self.step_minutes} min.")

        # 3. Création de la grille de temps cible (Target Index)
        target_index = pd.date_range(
            start=start_datetime,
            end=fin_horizon,
            freq=f"{int(self.step_minutes)}T" # 'T' = minutes dans Pandas
        )

        # 4. Ré-échantillonnage intelligent
        # a. Union des index : On garde les vrais points + les points cibles
        # Cela évite de perdre de l'information locale avant l'interpolation
        combined_index = df.index.union(target_index).sort_values()
        
        # b. Réindexation sur l'union (crée des NaNs sur les points cibles manquants)
        df_reindexed = df.reindex(combined_index)

        # c. Interpolation temporelle (tient compte de la distance entre les points)
        df_interpolated = df_reindexed.interpolate(method='time')

        # d. Filtrage final : On ne garde que les points de notre grille cible
        df_final = df_interpolated.reindex(target_index)

        # 5. Sécurité : Remplissage des bords (bfill/ffill)
        # Utile si le DF commence pile une minute après instant_initial par exemple
        df_final = df_final.bfill().ffill()

        return df_final
    
    def _is_temperature_realistic(self, temperature) :
        """
        Validate that a temperature lies within physical bounds.

        Parameters
        ----------
        temperature : float
            (température testée) Temperature value to evaluate.

        Returns
        -------
        bool
            (validité) True if the value is within configured limits.

        Raises
        ------
        ValueError
            (température invalide) If the temperature is outside allowed limits.
        """ 
        a = OptimizerService.MIN_WATER_HEATER_TEMP
        b = OptimizerService.MAX_WATER_HEATER_TEMP
        if  a <= temperature <= b :
            return True 
        else :
            raise ValueError(f"La température doit être un nombre entre {a} et {b}") 
        


    def _to_array(self, df_normalized: pd.DataFrame) -> np.ndarray:
        """
        Convert a normalised DataFrame into a row vector.

        Parameters
        ----------
        df_normalized : pandas.DataFrame
            (données normalisées) Time-aligned production DataFrame.

        Returns
        -------
        numpy.ndarray
            (vecteur production) Row vector shaped (1, N).

        Raises
        ------
        ValueError
            (données invalides) If the DataFrame is empty or contains invalid values.
        """
        # 1. Check basique : Est-ce que le DF contient des données ?
        if df_normalized is None or df_normalized.empty:
            raise ValueError("Impossible de convertir : Le DataFrame normalisé est vide.")

        # 2. Extraction des valeurs
        # On part du principe que la donnée pertinente est dans la première colonne
        # (indépendamment du nom de la colonne : 'production', 'watts', etc.)
        try:
            # .to_numpy() extrait les données brutes
            flat_data = df_normalized.iloc[:, 0].to_numpy(dtype=float)
        except IndexError:
            raise ValueError("Le DataFrame ne contient aucune colonne de données.")

        # 3. Check d'intégrité mathématique
        # Même si _normalize_df fait des bfill/ffill, on s'assure qu'on n'envoie pas de NaN au Solver
        if not np.isfinite(flat_data).all():
            raise ValueError("Le vecteur de production contient des valeurs NaN ou infinies.")

        # 4. Formatage en vecteur ligne (1, N)
        # flat_data est de forme (N,). reshape(1, -1) le transforme en (1, N).
        row_vector = flat_data.reshape(1, -1)

        return row_vector
