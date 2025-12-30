"""Ce fichier contient la classe OptimiserService qui représente l'objet qui gère les calculs d'optimisation. 

Auteur : @anaselb 
""" 
from client_models import Client 
import pandas as pd
from datetime import datetime, timedelta

from models_optimiser.system_config import SystemConfig
from models_optimiser.external_context import ExternalContext
from models_optimiser.optimisation_inputs import OptimizationInputs
from models_optimiser.trajectory import TrajectorySystem, StandardWHType, RouterMode
from solver import Solver 
import numpy as np 

class WeatherNotValid(Exception) :
    pass

class OptimiserService :
    pas_minimal = 5 #5 minutes. 
    Horizon_max = 48 #48 heures. 
    Horizon_min = 1 #Pas moins d'une heure. 
    Temp_min_chauffe_eau = 5 #En celsius. 
    Temp_max_chauffe_eau = 99  #En celsius. 
    def __init__(self, horizon : float = 24, pas : float = 15) :
        """On initilaise les objets de la classe avec un pas et un horizon. 
        Les décisions de l'optimisation couvriront une durée = Horizon et espacés d'un pas. 
        L'horizon doit être fourni en heures, le pas en minutes. 
        """
        self.horizon = horizon #L'horizon en heures
        self.pas = pas         #LE pas en minutes. 
    
    @property 
    def horizon(self) :
        return self._horizon 
    @horizon.setter 
    def horizon(self, valeur) :
        a = OptimiserService.Horizon_max
        b = OptimiserService.Horizon_min
        if b <= valeur <= a :
            self._horizon = valeur 
        else :
            raise ValueError(f"L'horizon doit être en heures, et doit être entre {a} et {b} heures.") 
         


    @property
    def pas(self) :
        return self._pas 
    @pas.setter 
    def pas(self,valeur) :
        if valeur/60 > self._horizon /2 :
            raise ValueError("Le pas ne doit pas dépasser la moitié de l'horizon") 
        elif valeur < OptimiserService.pas_minimal :
            raise ValueError(f"Le pas ne peut pas être inférieur à {OptimiserService.pas_minimal} minutes") 
        else :
            self._pas = valeur 

    def trajectory_of_client(self, 
                            client : Client, 
                            instant_initial : datetime, 
                            temp_initial : float, 
                            df_productions : pd.DataFrame) :
        """
        Orchestre l'optimisation :
        1. Prépare les données (Normalisation & Extraction vecteurs)
        2. Construit le modèle mathématique (via formalize_data)
        3. Résout le problème (via solvers)
        4. Formate la réponse en DataFrame
        """
        
        
        try :
            df_normalized = self._normalise_df(df_productions, instant_initial)
        except ValueError :
            raise WeatherNotValid("Le dataframe de la productions n'est pas valide.")
        
        production_array = self._to_array(df_normalized)
        #On construit un input à partir de ça : 
        sys_config = SystemConfig.from_client(client = client) 
        ext_context = ExternalContext.from_client(client = client, 
                                                  date_heure=instant_initial, 
                                                  solar_productions= production_array, 
                                                  horizon=self.horizon,
                                                  pas_temps=self.pas) 
        inputs = OptimizationInputs(sys_config, ext_context, temp_initial, client.features.mode) 
        solver = Solver() 

        trajectory = solver.solve(inputs) 

        return trajectory
    
    def trajectory_of_client_standard(self, 
                            client : Client, 
                            instant_initial : datetime, 
                            temp_initial : float, 
                            df_productions : pd.DataFrame, 
                            mode_WH : StandardWHType = None, 
                            Temp_consigne : float = None ) :
        try :
            df_normalized = self._normalise_df(df_productions, instant_initial)
        except ValueError :
            raise WeatherNotValid("Le dataframe de la productions n'est pas valide.")
        
        production_array = self._to_array(df_normalized)
        sys_config = SystemConfig.from_client(client = client) 
        ext_context = ExternalContext.from_client(client = client, 
                                                  date_heure=instant_initial, 
                                                  solar_productions= production_array, 
                                                  horizon=self.horizon,
                                                  pas_temps=self.pas) 
        trajectory = TrajectorySystem.generate_standard_trajectory(ext_context,sys_config,temp_initial,mode_WH, Temp_consigne) 
        return trajectory 
    
    def trajectory_of_client_router(self, 
                            client : Client, 
                            instant_initial : datetime, 
                            temp_initial : float, 
                            df_productions : pd.DataFrame, 
                            router_mode : RouterMode = None, 
                            Temp_consigne : float = None ) :
        try :
            df_normalized = self._normalise_df(df_productions, instant_initial)
        except ValueError :
            raise WeatherNotValid("Le dataframe de la productions n'est pas valide.")
        
        production_array = self._to_array(df_normalized)
        sys_config = SystemConfig.from_client(client = client) 
        ext_context = ExternalContext.from_client(client = client, 
                                                  date_heure=instant_initial, 
                                                  solar_productions= production_array, 
                                                  horizon=self.horizon,
                                                  pas_temps=self.pas) 
        trajectory = TrajectorySystem.generate_router_only_trajectory(ext_context,sys_config,temp_initial, router_mode, Temp_consigne) 

        return trajectory 
        
    
    def _is_df_valid(self, df: pd.DataFrame, start: datetime, end: datetime) -> bool:
        """
        Vérifie si le DataFrame couvre bien l'intervalle absolu [start, end] avec un pas cohérent.

        Args : 
            df (pd.DataFrame): Le DataFrame à évaluer (doit avoir un index datetime).
            start (datetime): Début absolu de l'horizon requis.
            end (datetime): Fin absolue de l'horizon requis.

        Returns : 
            bool : True si le df respecte la couverture et le pas maximum, False sinon.

        Raises : 
            TypeError : Si df n'est pas un DataFrame.
            ValueError : Si le df ne contient pas d'index ou colonne datetime.
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
        limit_gap = 4 * self.pas
        
        if max_gap_minutes > limit_gap:
            # print(f"Gap temporel trop grand détecté : {max_gap_minutes} min (Limite : {limit_gap} min)")
            return False

        return True

    def _normalise_df(self, df: pd.DataFrame, instant_initial: datetime) -> pd.DataFrame:
        """
        Aligne le DataFrame sur l'horizon temporel exact du service.
        
        La fonction crée un index parfait allant de instant_initial à 
        (instant_initial + horizon), avec le pas défini dans self.pas.
        Les données sont interpolées linéairement pour combler les petits trous.

        Args : 
            df (pd.DataFrame): Le dataframe brut à normaliser.
            instant_initial (datetime): Le moment T0 du début de l'optimisation.

        Returns :
            pd.DataFrame: Un nouveau DF nettoyé, ré-échantillonné et sans trous.

        Raises : 
            ValueError : Si le df n'est pas valide (couverture insuffisante).
        """
        # 1. Calcul de la fin absolue de l'horizon
        fin_horizon = instant_initial + timedelta(hours=self.horizon)

        # 2. Validation de la couverture
        # On passe les bornes absolues (datetime) et non un objet Creneau
        if not self._is_df_valid(df, instant_initial, fin_horizon):
            raise ValueError(f"Le DataFrame fourni ne couvre pas la période {instant_initial} -> {fin_horizon} ou contient des trous > {4*self.pas} min.")

        # 3. Création de la grille de temps cible (Target Index)
        target_index = pd.date_range(
            start=instant_initial,
            end=fin_horizon,
            freq=f"{int(self.pas)}T" # 'T' = minutes dans Pandas
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
        """Renvoie une erreur si la température n'est pas réaliste, sinon, elle renvoie true.
        Args : 
        - temperature : Température à évaluer. 
        Returns : 
        - bool : Si la température est correcte (entre self.Temp_min et self.Temp_max) -> True 
        Raises : 
        - ValueError : Si la température n'est pas correcte. 
        """ 
        a = OptimiserService.Temp_min_chauffe_eau
        b = OptimiserService.Temp_max_chauffe_eau
        if  a <= temperature <= b :
            return True 
        else :
            raise ValueError(f"La température doit être un nombre entre {a} et {b}") 
        


    def _to_array(self, df_normalized: pd.DataFrame) -> np.ndarray:
        """
        Convertit le DataFrame normalisé en un numpy array (vecteur ligne).
        
        Args :
            df_normalized (pd.DataFrame): Le DataFrame temporellement aligné.
        
        Returns :
            np.ndarray : Un tableau numpy de dimension (1, N).
            
        Raises :
            ValueError : Si le DataFrame est vide ou contient des données corrompues (NaN/Inf).
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
        # Même si _normalise_df fait des bfill/ffill, on s'assure qu'on n'envoie pas de NaN au Solver
        if not np.isfinite(flat_data).all():
            raise ValueError("Le vecteur de production contient des valeurs NaN ou infinies.")

        # 4. Formatage en vecteur ligne (1, N)
        # flat_data est de forme (N,). reshape(1, -1) le transforme en (1, N).
        row_vector = flat_data.reshape(1, -1)

        return row_vector