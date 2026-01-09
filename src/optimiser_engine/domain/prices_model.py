"""Pricing models used to evaluate energy costs across different tariff modes.

Author: @anaselb
"""
from typing import List
from .common import TimeSlot 
from datetime import time 
# 1. On définit une exception levée si appel à un paramètre du mode incompatible. 
class ModeIncompatibleError(Exception):
    """
    Raised when accessing pricing attributes that are not available in the current mode.
    """
    pass

class Prices:
    """
    Encapsulates electricity tariffs for either base or peak/off-peak configurations.

    Attributes
    ----------
    hp : float
        (tarif heures pleines) Price applied during peak hours when in HPHC mode.
    hc : float
        (tarif heures creuses) Price applied during off-peak hours when in HPHC mode.
    base : float
        (tarif base) Flat rate used when operating in BASE mode.
    resale_price : float
        (prix de revente) Amount earned per kWh sold back to the grid.
    mode : str
        (mode tarifaire) Current pricing mode, either 'HPHC' or 'BASE'.
    hp_slots : list
        (créneaux HP) List of TimeSlot instances defining peak hours in HPHC mode.
    """
    def __init__(self, mode = None):
        """
        Initialize pricing with sensible defaults for both tariff modes.

        Returns
        -------
        None
            (aucun retour) Constructor only sets initial tariff values.
        """
        # Valeurs par défaut
        self._hp = 0.22 
        self._hc = 0.18 
        self._base = 0.20
        self._resale_price = 0.10 
        if mode is None :
            self.mode = "BASE"
        else :
            self.mode = mode
        self._hp_slots = [] 

    # Méthode pour vérifier si on est bien dans le mode attendu. 
    def _check_mode(self, expected_mode: str):
        """
        Ensure that the current mode matches the expectation.

        Parameters
        ----------
        expected_mode : str
            (mode attendu) Mode string that must match the current configuration.

        Returns
        -------
        None
            (aucun retour) Raises if the mode is incompatible.

        Raises
        ------
        ModeIncompatibleError
            (mode incompatible) If attempting to access data for a different mode.
        """
        if self._mode != expected_mode:
            # Ici, on lance l'exception unique, mais avec un message précis
            raise ModeIncompatibleError(
                f"Action impossible : Vous êtes en mode '{self._mode}', "
                f"mais cette action requiert le mode '{expected_mode}'."
            )

    # --- Propriétés ---

    @property 
    def hp(self):
        """
        Retrieve the peak-hour price when operating in HPHC mode.

        Returns
        -------
        float
            (tarif heures pleines) Current peak price per kWh.

        Raises
        ------
        ModeIncompatibleError
            (mode incompatible) If accessed while not in HPHC mode.
        """
        self._check_mode("HPHC") 
        return self._hp 

    @hp.setter 
    def hp(self, valeur):
        """
        Set the peak-hour price, restricted to HPHC mode.

        Parameters
        ----------
        valeur : float
            (tarif heures pleines) Desired price for peak periods.

        Returns
        -------
        None
            (aucun retour) Updates the stored peak tariff.

        Raises
        ------
        ModeIncompatibleError
            (mode incompatible) If the current mode is not HPHC.
        ValueError
            (tarif invalide) If the provided price is negative or not numeric.
        """
        self._check_mode("HPHC")
        # Validation du type : 
        if not isinstance(valeur, (int, float)) or valeur < 0:
            raise ValueError("Le prix HP doit être un nombre positif")
        self._hp = valeur 
    
    @property 
    def hc(self):
        """
        Get the off-peak price in HPHC mode.

        Returns
        -------
        float
            (tarif heures creuses) Current off-peak price per kWh.

        Raises
        ------
        ModeIncompatibleError
            (mode incompatible) If accessed while not in HPHC mode.
        """
        self._check_mode("HPHC")
        return self._hc 

    @hc.setter 
    def hc(self, valeur):
        """
        Update the off-peak tariff, available only in HPHC mode.

        Parameters
        ----------
        valeur : float
            (tarif heures creuses) Desired price for off-peak hours.

        Returns
        -------
        None
            (aucun retour) The setter records the new off-peak price.

        Raises
        ------
        ModeIncompatibleError
            (mode incompatible) If the current mode is not HPHC.
        ValueError
            (tarif invalide) If the price is negative or not numeric.
        """
        self._check_mode("HPHC")
        if not isinstance(valeur, (int, float)) or valeur < 0:
            raise ValueError("Le prix HC doit être un nombre positif")
        self._hc = valeur  

    @property 
    def base(self):
        """
        Return the base tariff when operating in BASE mode.

        Returns
        -------
        float
            (tarif base) Flat rate per kWh.

        Raises
        ------
        ModeIncompatibleError
            (mode incompatible) If accessed while not in BASE mode.
        """
        self._check_mode("BASE")
        return self._base
        
    @base.setter 
    def base(self, valeur):
        """
        Set the base tariff, restricted to BASE mode.

        Parameters
        ----------
        valeur : float
            (tarif base) Desired flat rate per kWh.

        Returns
        -------
        None
            (aucun retour) The setter stores the base price.

        Raises
        ------
        ModeIncompatibleError
            (mode incompatible) If the current mode is not BASE.
        ValueError
            (tarif invalide) If the price is negative or not numeric.
        """
        self._check_mode("BASE")
        if not isinstance(valeur, (int, float)) or valeur < 0:
            raise ValueError("Le prix BASE doit être un nombre positif")
        self._base = valeur 


    @property 
    def resale_price(self):
        """
        Access the resale price applied when exporting energy.

        Returns
        -------
        float
            (prix de revente) Current resale tariff per kWh.
        """
        return self._resale_price
    
    @resale_price.setter
    def resale_price(self, valeur):
        """
        Define the resale price for exported energy.

        Parameters
        ----------
        valeur : float
            (prix de revente) Payment received per kWh sold.

        Returns
        -------
        None
            (aucun retour) Updates the stored resale tariff.

        Raises
        ------
        ValueError
            (tarif invalide) If the provided price is negative or not numeric.
        """
        if not isinstance(valeur, (int, float)) or valeur < 0:
            raise ValueError("Le prix de revente doit être un nombre positif")
        self._resale_price = valeur 

    @property 
    def mode(self):
        """
        Current pricing mode selection.

        Returns
        -------
        str
            (mode tarifaire) Either 'HPHC' or 'BASE'.
        """
        return self._mode 
    
    @mode.setter 
    def mode(self, valeur):
        """
        Switch between base and peak/off-peak pricing modes.

        Parameters
        ----------
        valeur : str
            (mode tarifaire) Mode identifier, 'HPHC' or 'BASE'.

        Returns
        -------
        None
            (aucun retour) Stores the new mode.

        Raises
        ------
        ValueError
            (mode invalide) If the provided mode is unsupported.
        """
        if valeur not in ["HPHC", "BASE"]:
            raise ValueError("Le mode doit être 'HPHC' ou 'BASE'")
        self._mode = valeur 

    @property
    def hp_slots(self):
        """
        Time slots defining peak periods in HPHC mode.

        Returns
        -------
        list of TimeSlot
            (créneaux HP) Configured peak-hour intervals.

        Raises
        ------
        ModeIncompatibleError
            (mode incompatible) If accessed while not in HPHC mode.
        """
        self._check_mode("HPHC")
        return self._hp_slots

    @hp_slots.setter
    def hp_slots(self, nouvelle_liste: List[TimeSlot]):
        """
        Configure the list of peak-hour intervals for HPHC mode.

        Parameters
        ----------
        nouvelle_liste : list of TimeSlot
            (créneaux HP) Candidate list of peak intervals.

        Returns
        -------
        None
            (aucun retour) Saves the validated list of slots.

        Raises
        ------
        ModeIncompatibleError
            (mode incompatible) If the current mode is not HPHC.
        TypeError
            (type invalide) If the provided value is not a list of TimeSlot instances.
        ValueError
            (créneaux invalides) If slots overlap or cover the entire day.
        """
        self._check_mode("HPHC") #On peut pas définir une liste de crénaux pour BASE. 
        # 1. Validation du TYPE (Est-ce une liste d'objets TimeSlot ?)
        if not isinstance(nouvelle_liste, list):
            raise TypeError("Il faut fournir une liste.")
        
        #On vérifie chaque élément avec Le all() : 
        if not all(isinstance(c, TimeSlot) for c in nouvelle_liste):
            raise TypeError("La liste ne doit contenir que des objets de type 'TimeSlot'")

        # 2. On trie la liste (indispensable pour vérifier les trous)
        liste_triee = sorted(nouvelle_liste) #Cela est possible avec __lt__ définie dans crenau. 

        # 3. Validation des CHEVAUCHEMENTS
        for i in range(len(liste_triee) - 1):
            actuel = liste_triee[i]
            suivant = liste_triee[i+1]
            
            if actuel.overlaps(suivant):
                raise ValueError(f"Conflit : Les créneaux {actuel} et {suivant} se chevauchent.")
            
            # Vérification stricte : la fin de l'un ne doit pas dépasser le début de l'autre
            if actuel.end > suivant.start:
                raise ValueError(f"Ordre invalide entre {actuel} et {suivant}")

        # 4. Validation de l'existence de HC également. (Pas 24h de HP)
        total_minutes = sum(c.duration_minutes() for c in liste_triee)
        if total_minutes >= 24 * 60:
            raise ValueError("Impossible : Les Heures Pleines ne peuvent pas couvrir 24h (il faut des HC !)")
        if total_minutes == 0 :
            raise ValueError("Impossible : Les Heures Creuses ne peuvent pas couvrir 24h (il faut des HP !)") 
        # Si tout est bon, on sauvegarde
        self._hp_slots = liste_triee
    
    
    #--- Une fonction pour calculer combien on paie à un instant t --- 
    def get_current_purchase_price(self, heure_test: time) -> float:
        """
        Compute the purchase price per kWh at a specific time based on the active mode.

        Parameters
        ----------
        heure_test : datetime.time
            (instant testé) Time to evaluate for pricing.

        Returns
        -------
        float
            (prix courant) Tariff applicable at the given time.
        """
        if self._mode == "BASE":
            return self._base
        
        elif self._mode == "HPHC":
            # On vérifie si l'heure est dans un des créneaux HP
            #self.hp_slots est triée grâce au setter. 
            est_en_hp = any(c.start <= heure_test < c.end for c in self._hp_slots)
            
            if est_en_hp:
                return self._hp
            else:
                return self._hc
            
            #Si on donne exactement l'instant de début d'une creuse elle renvoit le tarif HC. 

    def __repr__(self) :
        """
        Return a human-readable description of the prices.

        Returns
        -------
        str
            (représentation textuelle) Formatted summary.
        """
        if self.mode == "BASE" :
            sum_mode = "-Mode : Basic.\n"
            sum_prices = f"-Purchase price (prix d'achat) : {self.base}\n"
            sum_intervals = "The price is constant because the mode is Basic.\n"
        elif self.mode == "HPHC" :
            sum_mode = "-Mode : HP-HC (Heures pleines / Heures creuses)\n" 
            sum_prices = f"-Purchase price HP : {self.hp} \n-Purchase price HC : {self.hc}\n" 
            sum_intervals = f"-The slots of HP : \n {self.hp_slots}\n" 
        
        sum_resell = f"-Resale price (Prix de revente) : {self.resale_price}"

        return sum_mode + sum_prices + sum_intervals + sum_resell 
    
        