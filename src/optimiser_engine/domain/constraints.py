"""Consumption profiles and operational constraints for optimisation scenarios.

Author: @anaselb
"""
from typing import List
from datetime import time
from .common import TimeSlot
from ..exceptions import OptimizerError
import numpy as np
from datetime import datetime, timedelta

class DimensionNotRespected(OptimizerError) :
    """
    Raised when a consumption profile matrix does not match the expected dimensions.
    """
    pass

class ConsumptionProfile:
    """
    Represents a weekly consumption profile with optional background noise.

    Attributes
    ----------
    data : numpy.ndarray
        (profil 7x24) Matrix storing hourly consumption for each weekday.
    background_noise : float
        (bruit de fond) Default value used when no matrix is provided.
    """
    points_per_day = 24
    def __init__(self, matrix_7x24=None, background_noise=300.0):
        """
        Initialize the consumption profile with optional predefined data.

        Parameters
        ----------
        matrix_7x24 : array-like, optional
            (matrice initiale) Optional 7x24 matrix of hourly consumption values.
        background_noise : float
            (bruit de fond) Default consumption used to populate missing data.

        Returns
        -------
        None
            (aucun retour) The constructor populates the data array in place.
        """
        # Si rien n'est fourni, on met le bruit de fond partout
        if matrix_7x24 is None:
            self.data = np.full((7, 24), float(background_noise))
        else:
            self.data = np.array(matrix_7x24)
        
        self.background_noise = background_noise
    
    @property 
    def data(self) :
        """
        Access the internal 7x24 consumption matrix.

        Returns
        -------
        numpy.ndarray
            (profil 7x24) Hourly consumption values for each weekday.
        """
        return self._data 
    @data.setter 
    def data(self,tab) :
        """
        Set the consumption matrix, enforcing correct shape and type.

        Parameters
        ----------
        tab : numpy.ndarray
            (matrice 7x24) Consumption data arranged per day and hour.

        Returns
        -------
        None
            (aucun retour) Stores the provided matrix after validation.

        Raises
        ------
        TypeError
            (type invalide) If the supplied object is not a numpy array.
        DimensionNotRespected
            (dimension incorrecte) If the matrix does not match the expected 7x24 shape.
        """
        if not isinstance(tab,np.ndarray) :
            raise TypeError("Le tableau à mettre dans data doit être un np.ndarray") 
        if tab.shape != (7, ConsumptionProfile.points_per_day):
            raise DimensionNotRespected(f"La dimension du tableau doit être {ConsumptionProfile.points_per_day}x7") 
        self._data = tab 
    

    def get_vector(self, start_date : datetime, N : int, step_min : float):
        """
        Generate a time-aligned consumption vector with linear interpolation.

        Parameters
        ----------
        start_date : datetime.datetime
            (date de départ) Reference datetime for the first point.
        N : int
            (nombre de points) Number of values to produce.
        step_min : float
            (pas en minutes) Time step between points, expressed in minutes.

        Returns
        -------
        numpy.ndarray
            (vecteur consommation) Sequence of interpolated consumption values.

        Raises
        ------
        TypeError
            (type invalide) If start_date is not a datetime instance.
        ValueError
            (paramètre invalide) If N or step_min are non-positive or if data is missing.
        """
        if not isinstance(start_date, datetime):
            raise TypeError(f"L'argument 'start_date' doit être un objet datetime. Reçu: {type(start_date)}")
        
        if not isinstance(N, int) or N <= 0:
            raise ValueError(f"Le nombre de points 'N' doit être un entier strictement positif. Reçu: {N}")
            
        if not isinstance(step_min, (int, float)) or step_min <= 0:
            raise ValueError(f"Le pas de temps 'step_min' doit être un nombre strictement positif. Reçu: {step_min}")

        if self.data is None:
            raise ValueError("La matrice de données du profil est manquante (None).")
        ###########CODE #######################################################################################
        t_axis = np.array([start_date + timedelta(minutes=i*step_min) for i in range(N)])
        vector = np.zeros(N)

        for i, dt in enumerate(t_axis):
            jour = dt.weekday()
            heure_float = dt.hour + dt.minute / 60.0
            
            # Récupération des deux heures encadrantes pour l'interpolation
            h1 = int(heure_float)
            h2 = (h1 + 1) % 24
            jour2 = jour if h2 > h1 else (jour + 1) % 7
            
            val1 = self.data[jour, h1]
            val2 = self.data[jour2, h2]
            
            # Interpolation linéaire pour un flux continu "pro"
            fraction = heure_float - h1
            vector[i] = val1 + fraction * (val2 - val1)
            
        return vector
    
    def __repr__(self) :
        """
        Return a human-readable description of the consumption profile.

        Returns
        -------
        str
            (représentation textuelle) Formatted summary.
        """
        summary1 = "The consumption profile : \n- Background noise : " + str(self.background_noise) + "\n" 
        summary2 = f"- Table of consumption : \n {self.data}" 
        summary = summary1 + summary2 
        return summary  

class Constraints:
    """
    Aggregates operational constraints such as forbidden heating windows and minimum temperature.

    Attributes
    ----------
    consumption_profile : ConsumptionProfile
        (profil de consommation) Profile used to estimate baseline demand.
    forbidden_slots : list
        (créneaux interdits) TimeSlot objects during which heating is disallowed.
    minimum_temperature : float
        (température minimale) Lower bound for allowed water temperature.
    """
    def __init__(self, consumption_profile: ConsumptionProfile = None, 
                 forbidden_slots : List[TimeSlot] = None, 
                 minimum_temperature = 10.0, 
                 ) :
        """
        Initialize constraints with optional forbidden slots and temperature limits.

        Parameters
        ----------
        consumption_profile : ConsumptionProfile, optional
            (profil de consommation) Baseline demand profile; defaults to a constant background.
        forbidden_slots : list of TimeSlot, optional
            (créneaux interdits) Intervals during which heating is not allowed.
        minimum_temperature : float, optional
            (température minimale) Minimum admissible tank temperature in Celsius.

        Returns
        -------
        None
            (aucun retour) The constructor stores validated constraint settings.
        """
        # On stocke les plages INTERDITES
        # Par défaut vide = Aucune interdiction = 24/24 Autorisé
        if forbidden_slots is None :
            self.forbidden_slots = [] 
        else :
            self.forbidden_slots = forbidden_slots
        if consumption_profile is None :
            self.consumption_profile = ConsumptionProfile() 
        else :
            self.consumption_profile = consumption_profile
        self.minimum_temperature = minimum_temperature 
        
    # --- MÉTHODE PRIVÉE DE VALIDATION  ---
    def _validate_coherence(self, slot_list: List[TimeSlot]):
        """
        Validate a list of time slots against overlap and full-day coverage rules.

        Parameters
        ----------
        slot_list : list of TimeSlot
            (créneaux interdits) Candidate intervals to check.

        Returns
        -------
        None
            (aucun retour) Raises if any rule is violated.

        Raises
        ------
        ValueError
            (créneaux invalides) If slots overlap or span a full day.
        """
        if not slot_list:
            return # Liste vide = OK

        # 1. Tri obligatoire pour vérifier les chevauchements
        liste_triee = sorted(slot_list)

        # 2. Vérification des chevauchements
        for i in range(len(liste_triee) - 1):
            actuel = liste_triee[i]
            suivant = liste_triee[i+1]
            
            if actuel.overlaps(suivant):
                raise ValueError(f"Conflit : Les plages interdites {actuel} et {suivant} se chevauchent.")

        # 3. Vérification de la durée totale (< 24h)
        total_minutes = sum(c.duration_minutes() for c in liste_triee)
        MINUTES_24H = 24 * 60
        
        if total_minutes >= MINUTES_24H:
            raise ValueError("Configuration impossible : Les interdictions couvrent toute la journée (24h).")

    # --- GETTER / SETTER ---

    @property
    def forbidden_slots(self) -> List[TimeSlot]:
        """
        Access the list of forbidden heating intervals.

        Returns
        -------
        list of TimeSlot
            (créneaux interdits) Sorted list of disallowed time ranges.
        """
        return self._forbidden_slots

    @forbidden_slots.setter
    def forbidden_slots(self, new_slots: List[TimeSlot]):
        """
        Replace the forbidden slots list after validation.

        Parameters
        ----------
        new_slots : list of TimeSlot
            (créneaux interdits) New collection of disallowed intervals.

        Returns
        -------
        None
            (aucun retour) Stores the validated and sorted slots.

        Raises
        ------
        TypeError
            (type invalide) If the provided value is not a list of TimeSlot.
        ValueError
            (créneaux invalides) If slots overlap or cover the full day.
        """
        if not isinstance(new_slots, list):
            raise TypeError("Doit être une liste de TimeSlot")
        
        if not all(isinstance(c, TimeSlot) for c in new_slots):
            raise TypeError("La liste ne doit contenir que des objets TimeSlot")
        
        # On valide AVANT d'enregistrer
        self._validate_coherence(new_slots)
        
        # Si validation OK, on enregistre la version triée
        self._forbidden_slots = sorted(new_slots)

    @property 
    def minimum_temperature(self) -> float :
        """
        Minimum allowable temperature constraint.

        Returns
        -------
        float
            (température minimale) Lower bound expressed in Celsius.
        """
        return self._minimum_temperature 
    @minimum_temperature.setter 
    def minimum_temperature(self, valeur) :
        """
        Set the minimum acceptable temperature.

        Parameters
        ----------
        valeur : float
            (température minimale) Threshold temperature in Celsius.

        Returns
        -------
        None
            (aucun retour) Updates the minimum temperature constraint.

        Raises
        ------
        ValueError
            (température invalide) If the temperature is outside the 0–95°C range or not numeric.
        """
        if not isinstance(valeur, (float,int)) or valeur < 0 or valeur > 95 :
            raise ValueError("La température minimale doit être un nombre entre 0 et 95") 
        self._minimum_temperature = valeur 

    @property
    def consumption_profile(self) -> ConsumptionProfile: 
        """
        Consumption profile used by the solver.

        Returns
        -------
        ConsumptionProfile
            (profil de consommation) Current demand profile instance.
        """
        return self._consumption_profile 

    @consumption_profile.setter
    def consumption_profile(self, valeur):
        """
        Assign the consumption profile after validating its type.

        Parameters
        ----------
        valeur : ConsumptionProfile
            (profil de consommation) Profile representing expected demand.

        Returns
        -------
        None
            (aucun retour) Stores the provided profile.

        Raises
        ------
        TypeError
            (type invalide) If the provided value is not a ConsumptionProfile.
        """
        if not isinstance(valeur, ConsumptionProfile):
            raise TypeError("Le planning de consommation doit être un élément de type ConsumptionProfile.")
        self._consumption_profile = valeur
  
    # --- HELPER D'AJOUT ---

    def add_forbidden_slot(self, start: time, end: time):
        """
        Add a new forbidden slot while preserving coherence rules.

        Parameters
        ----------
        start : datetime.time
            (heure de début) Inclusive start time of the forbidden interval.
        end : datetime.time
            (heure de fin) Exclusive end time of the forbidden interval.

        Returns
        -------
        None
            (aucun retour) Inserts the slot if validation succeeds.

        Raises
        ------
        ValueError
            (créneau invalide) If the slot is inconsistent or overlaps existing entries.
        """
        nouveau = TimeSlot(start, end)
        
        # On crée une liste temporaire pour tester
        liste_test = self._forbidden_slots + [nouveau]
        
        # On lance la validation sur l'ensemble
        self._validate_coherence(liste_test)
        
        # Si ça n'a pas planté, on valide l'ajout
        self._forbidden_slots.append(nouveau)
        self._forbidden_slots.sort()

    # --- INTERFACE SOLVER ---

    def is_allowed(self, heure_test: time) -> bool:
        """
        Determine whether heating is allowed at a specific time.

        Parameters
        ----------
        heure_test : datetime.time
            (instant testé) Time to check against forbidden slots.

        Returns
        -------
        bool
            (autorisation) True if heating is permitted at the given time.
        """
        if not self._forbidden_slots:
            return True 

        for plage_interdite in self._forbidden_slots:
            # On utilise la méthode contient() qui existe dans creneau. 
            if plage_interdite.contains(heure_test):
                return False 
        
        return True
        
    def __repr__(self):
        """
        Return a human-readable description of the constraints.

        Returns
        -------
        str
            (représentation textuelle) Formatted summary.
        """
        #Restrictions : 
        if not self._forbidden_slots:
            summary1 =  "<Constraints: No restriction (Autorisé 24h/24)>"
        else :
            summary1 = f"<Constraints: Restriction on {self._forbidden_slots}>"
        
        #Minimal temperature : 
        summary2 = f"\n<Minimal Temperature : {self.minimum_temperature}" 
        
        #Consumption profile : 
        summary3 = "\n -Please type print(self.consumption_profile) to access to the details of profile consumption" 

        return summary1 + summary2 + summary3

