"""Shared time interval utilities for domain scheduling components.

Author: @anaselb
"""

from datetime import time 

class TimeSlot:  #Créneau
    """
    Represents a half-open interval between two daytime instants for scheduling.

    Attributes
    ----------
    start : datetime.time
        (heure de début) Beginning of the interval, inclusive.
    end : datetime.time
        (heure de fin) End of the interval, exclusive.
    """
    def __init__(self, start: time, end: time):
        """
        Create a time slot defined by a start and end time.

        Parameters
        ----------
        start : datetime.time
            (heure de début) Beginning of the slot, inclusive.
        end : datetime.time
            (heure de fin) End of the slot, exclusive.

        Returns
        -------
        None
            (aucun retour) The constructor sets attributes without returning.

        Raises
        ------
        ValueError
            (intervalle invalide) If the start time is not before the end time.
        """
        if start >= end:
            raise ValueError("Le début doit être avant la fin (pas de passage de minuit géré ici pour simplifier)")
        self.start = start
        self.end = end

    # Cette méthode permet d'utiliser sort() sur une liste de créneaux (pour pouvoir comparer avec un < plus tard.)
    def __lt__(self, other):
        """
        Compare slots by their start time to support sorting.

        Parameters
        ----------
        other : TimeSlot
            (autre créneau) Another slot to compare against.

        Returns
        -------
        bool
            (résultat de comparaison) True when this slot starts earlier than the other.
        """
        return self.start < other.start

    def overlaps(self, other_timeslot) -> bool:
        """
        Check whether two time slots overlap.

        Parameters
        ----------
        other_timeslot : TimeSlot
            (autre créneau) Slot evaluated for overlap with this one.

        Returns
        -------
        bool
            (chevauchement) True if the intervals intersect.
        """
        # Logique : (A commence avant la fin de B) ET (B commence avant la fin de A)
        return self.start < other_timeslot.end and other_timeslot.start < self.end
    
    def contains(self, moment : time) :
        """
        Determine if a given moment falls within the slot.

        Parameters
        ----------
        moment : datetime.time
            (moment testé) Time value to evaluate.

        Returns
        -------
        bool
            (appartenance) True when the moment is inside the interval.
        """
        if self.start <= moment < self.end :
            return True 
        return False 
    
    def duration_minutes(self):
        """
        Calculate the duration of the slot in minutes.

        Returns
        -------
        int
            (durée en minutes) Number of minutes between start and end.
        """
        # Petit calcul pour convertir en minutes
        h1 = self.start.hour * 60 + self.start.minute
        h2 = self.end.hour * 60 + self.end.minute
        return h2 - h1

    def __repr__(self):
        """
        Represent the slot with a human-readable time range.

        Returns
        -------
        str
            (représentation textuelle) Formatted interval string.
        """
        return f"[{self.start.strftime('%H:%M')} - {self.end.strftime('%H:%M')}]"
