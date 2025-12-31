"""Planning models defining temperature setpoints over a weekly schedule.

Author: @anaselb
"""

from datetime import time, datetime 
from typing import List, Dict, Tuple

class Setpoint :  #Point Consigne. 
    """
    Represents a single temperature setpoint at a given day and time.

    Attributes
    ----------
    day : int
        (jour de la semaine) Weekday index with 0 for Monday through 6 for Sunday.
    time : datetime.time
        (heure de consigne) Time of day when the setpoint should apply.
    temperature : float
        (température cible) Desired water temperature in Celsius.
    drawn_volume : float
        (volume prévu) Expected drawn volume associated with the setpoint.
    """
    def __init__(self, day : int, time_of_day : time, temperature : float, volume : float = 30) : 
        """
        Initialize a setpoint describing when and how the heater should operate.

        Parameters
        ----------
        day : int
            (jour de la semaine) Weekday index from 0 (Monday) to 6 (Sunday).
        time_of_day : datetime.time
            (heure de consigne) Time of day when the target applies.
        temperature : float
            (température cible) Desired tank temperature in Celsius.
        volume : float, optional
            (volume prévu) Forecasted draw volume in litres, defaults to 30.

        Returns
        -------
        None
            (aucun retour) Constructor sets attributes after validation.
        """
        self.day = day 
        self.time = time_of_day 
        self.temperature = temperature 
        self.drawn_volume = volume 

    @property 
    def day(self) :
        """
        Weekday index for the setpoint.

        Returns
        -------
        int
            (jour de la semaine) Value between 0 and 6.
        """
        return self._day 
    @day.setter 
    def day(self, valeur) :
        """
        Set the weekday while enforcing the expected 0–6 range.

        Parameters
        ----------
        valeur : int
            (jour de la semaine) Proposed weekday index.

        Returns
        -------
        None
            (aucun retour) Updates the stored day.

        Raises
        ------
        ValueError
            (jour invalide) If the value is not an integer between 0 and 6.
        """
        if valeur > 6 or valeur < 0 or not isinstance(valeur, int) :
            raise ValueError("Le jour doit être un int entre 0 et 6 (0 pour Lundi et 6 pour Dimanche)") 
        self._day = valeur 
    
    @property 
    def time(self) :
        """
        Time of day associated with the setpoint.

        Returns
        -------
        datetime.time
            (heure de consigne) Time indicating when the setpoint applies.
        """
        return self._time 
    @time.setter 
    def time(self, valeur) :
        """
        Assign the setpoint time with type validation.

        Parameters
        ----------
        valeur : datetime.time
            (heure de consigne) Time of day for the setpoint.

        Returns
        -------
        None
            (aucun retour) Records the provided time.

        Raises
        ------
        ValueError
            (type invalide) If the value is not a datetime.time instance.
        """
        if not isinstance(valeur, time) :
            raise ValueError("Le moment doit être un moment de la journée du type time") 
        self._time = valeur 
    
    @property 
    def temperature(self) :
        """
        Target temperature for this setpoint.

        Returns
        -------
        float
            (température cible) Desired temperature in Celsius.
        """
        return self._temperature 
    
    @temperature.setter 
    def temperature(self, valeur) :
        """
        Set the target temperature with bounds checking.

        Parameters
        ----------
        valeur : float
            (température cible) Desired temperature between 30 and 99 Celsius.

        Returns
        -------
        None
            (aucun retour) Stores the target temperature.

        Raises
        ------
        ValueError
            (température invalide) If the value is not numeric or outside 30–99.
        """
        if not isinstance(valeur, (int, float)) or (valeur > 99) or (valeur < 30) :
            raise ValueError("La température cible doit être un nombre entre 30 et 99") 
        self._temperature = valeur 
    
    @property 
    def drawn_volume(self) :
        """
        Volume expected to be drawn at this setpoint.

        Returns
        -------
        float
            (volume prévu) Volume in litres.
        """
        return self._drawn_volume 
    @drawn_volume.setter 
    def drawn_volume(self, valeur) :
        """
        Set the expected draw volume, ensuring it is non-negative.

        Parameters
        ----------
        valeur : float
            (volume prévu) Forecasted volume in litres.

        Returns
        -------
        None
            (aucun retour) Updates the draw volume.

        Raises
        ------
        ValueError
            (volume invalide) If the volume is negative or not numeric.
        """
        if not isinstance(valeur, (int, float)) or valeur < 0:
            raise ValueError("Le volume doit être un nombre positif")
        self._drawn_volume = valeur 
    
    def __lt__(self, other) :
        """
        Compare two setpoints by day then time to support sorting.

        Parameters
        ----------
        other : Setpoint
            (autre consigne) Another setpoint to compare.

        Returns
        -------
        bool
            (résultat de comparaison) True if this setpoint occurs earlier than the other.
        """
        if not isinstance(other, Setpoint) :
            return NotImplemented 
        return (self.day, self.time) < (other.day, other.time) 
    
    def __repr__(self) :
        """
        Return a human-readable description of the setpoint.

        Returns
        -------
        str
            (représentation textuelle) Formatted summary including day, time, temperature, and volume.
        """
        Liste = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"] 
        jour = Liste[self.day]
        moment = self.time 
        temperature = self.temperature 
        volume = self.drawn_volume 
        repr = "Set point : " \
        "Day : " + str(jour) + " "\
        "Time : " + str(moment) + " "\
        "Temperature : " + str(temperature) + " " \
        "Drawn volume : " + str(volume)
        return repr 
    
class Planning:
    """
    Manages an ordered collection of setpoints across the planning horizon.

    Attributes
    ----------
    setpoints : list
        (liste de consignes) Sorted list of Setpoint instances representing the schedule.
    """
    def __init__(self):
        """
        Initialize an empty planning container.

        Returns
        -------
        None
            (aucun retour) Creates an empty setpoint list.
        """
        self._setpoints: List[Setpoint] = []

    def _clean_and_sort(self, raw_list: List[Setpoint]) -> List[Setpoint]:
        """
        Deduplicate and sort setpoints, keeping the hottest entry for identical slots.

        Parameters
        ----------
        raw_list : list of Setpoint
            (consignes brutes) Candidate setpoints that may include duplicates.

        Returns
        -------
        list of Setpoint
            (consignes triées) Cleaned and sorted setpoints for storage.
        """
        # Dictionnaire avec Clé = (Jour, Heure) -> Valeur = Objet Setpoint
        unique_consignes: Dict[Tuple[int, time], Setpoint] = {}

        for c in raw_list:
            cle = (c.day, c.time)
            
            # 1. Si le créneau est libre, on l'ajoute
            if cle not in unique_consignes:
                unique_consignes[cle] = c
            
            # 2. Si conflit : on compare les températures
            else:
                consigne_existante = unique_consignes[cle]
                # La règle : On garde celle avec la température la plus élevée
                if c.temperature > consigne_existante.temperature:
                    # On remplace par la nouvelle (plus chaude)
                    unique_consignes[cle] = c
                # Sinon, on ne fait rien (on garde l'existante qui est >=)

        # On transforme le dico en liste et on trie
        liste_propre = list(unique_consignes.values())
        liste_propre.sort() # Utilise le __lt__ défini dans Setpoint
        
        return liste_propre
    @property
    def setpoints(self) -> List[Setpoint]:
        """
        Access the sorted list of setpoints.

        Returns
        -------
        list of Setpoint
            (liste de consignes) Current planning schedule.
        """
        return self._setpoints

    @setpoints.setter
    def setpoints(self, nouvelle_liste: List[Setpoint]):
        """
        Replace the entire schedule after validating contents.

        Parameters
        ----------
        nouvelle_liste : list of Setpoint
            (nouvelles consignes) Replacement setpoints to store.

        Returns
        -------
        None
            (aucun retour) Updates the internal schedule.

        Raises
        ------
        TypeError
            (type invalide) If the collection is not a list of Setpoint instances.
        """
        if not isinstance(nouvelle_liste, list):
            raise TypeError("Le planning doit être une liste.")
        
        # Validation stricte du contenu
        for i, item in enumerate(nouvelle_liste):
            if not isinstance(item, Setpoint):
                raise TypeError(f"L'élément à l'index {i} n'est pas un Setpoint.")
        
        self._setpoints = self._clean_and_sort(nouvelle_liste) #On a bien fait une copie. 

    # --- 2. AJOUT / SUPPRESSION ---
    
    def add_setpoint(self, consigne: Setpoint):
        """
        Append a setpoint and maintain sorted order.

        Parameters
        ----------
        consigne : Setpoint
            (consigne ajoutée) Setpoint to add to the planning.

        Returns
        -------
        None
            (aucun retour) Stores the setpoint after cleaning and sorting.

        Raises
        ------
        TypeError
            (type invalide) If the provided object is not a Setpoint.
        """
        if not isinstance(consigne, Setpoint) :
            raise TypeError("consigne n'est pas un objet de type Setpoint, il ne peut pas être ajouté.") 
        liste_temporaire = self._setpoints + [consigne]
        self._setpoints = self._clean_and_sort(liste_temporaire) 

    def remove_setpoint(self, jour: int, heure: time):
        """
        Remove a setpoint matching the given day and time.

        Parameters
        ----------
        jour : int
            (jour de la semaine) Weekday index targeted for deletion.
        heure : datetime.time
            (heure ciblée) Time of day for the setpoint to remove.

        Returns
        -------
        bool
            (suppression effectuée) True if a matching setpoint was removed.
        """
        # On cherche l'élément (on filtre pour garder ceux qui NE correspondent PAS)
        taille_avant = len(self._setpoints)
        self._setpoints = [
            c for c in self._setpoints 
            if not (c.day == jour and c.time == heure)
        ]
        return len(self._setpoints) < taille_avant

    def clear(self):
        """
        Remove all setpoints from the planning.

        Returns
        -------
        None
            (aucun retour) Empties the internal list.
        """
        self._setpoints.clear()

    # --- 3. LA MÉTHODE "HORIZON" (CRUCIALE POUR L'OPTIMISEUR)---

    def get_future_setpoints(self, jour_actuel: int = None, heure_actuelle: time = None, horizon_heures: int = 24) -> List[Setpoint]:
        """
        Retrieve upcoming setpoints within a moving horizon starting from a reference time.

        Parameters
        ----------
        jour_actuel : int, optional
            (jour actuel) Weekday index of the reference instant; defaults to current day.
        heure_actuelle : datetime.time, optional
            (heure actuelle) Time component of the reference instant; defaults to current time.
        horizon_heures : int, optional
            (horizon en heures) Width of the search window in hours, default is 24.

        Returns
        -------
        list of Setpoint
            (consignes futures) Setpoints occurring within the specified horizon, sorted in temporal order.
        """
        if jour_actuel is None or heure_actuelle is None:
            # On prend l'instant actuel : 
            maintenant = datetime.now()
            
            if jour_actuel is None:
                jour_actuel = maintenant.weekday() # Renvoie bien un int (0=Lundi...6=Dimanche comme dans la convention) 
            
            if heure_actuelle is None:
                heure_actuelle = maintenant.time() #L'heure. 
        
        
        if not self._setpoints:
            return []

        # Convertisseur helper : Tout en minutes depuis le début de la semaine (Lundi 00:00 = 0)
        def _to_minutes(j, h):
            return j * 24 * 60 + h.hour * 60 + h.minute

        # 1. Bornes temporelles
        t_debut = _to_minutes(jour_actuel, heure_actuelle)
        t_fin = t_debut + (horizon_heures * 60)
        
        resultat = []
        minutes_semaine = 7 * 24 * 60  # minutes dans la semaine. 

        # 2. Scan intelligent
        for c in self._setpoints:
            t_consigne = _to_minutes(c.day, c.time)

            # Cas A : La consigne est dans le futur direct de cette semaine
            if t_debut <= t_consigne <= t_fin:
                resultat.append(c)
            
            # Cas B : Gestion du semaine suivante 
            elif (t_consigne + minutes_semaine) <= t_fin:
                resultat.append(c)
        #On fait un triage pour garder l'ordre naturel
        def cle_de_tri_relatif(consigne):
            t_abs = _to_minutes(consigne.day, consigne.time)
            if t_abs < t_debut:
                return t_abs + minutes_semaine # On la projette dans le futur
            return t_abs

        resultat.sort(key=cle_de_tri_relatif)
        return resultat
    


    def __repr__(self) :
        """
        Return a human-readable description of the planning.

        Returns
        -------
        str
            (représentation textuelle) Formatted summary.
        """
        lst = self.setpoints 
        summary = "[" 
        Liste = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
        for k in lst :
            day, time, temperature, volume = Liste[k.day], str(k.time), str(k.temperature), str(k.drawn_volume) 
            summary = summary + "\n" + "-" + day + "-" + time + "   :  " + temperature + " °C - " + volume + " L." 
        summary = summary + "\n ]"
        return summary 
            




