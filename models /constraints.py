from typing import List
from datetime import time
from common import Creneau

class Constraints:
    def __init__(self, plages_interdites : List[Creneau] = None, temp_minimale = 10.0):
        # On stocke les plages INTERDITES
        # Par défaut vide = Aucune interdiction = 24/24 Autorisé
        if plages_interdites is None :
            self.plages_interdites = [] 
        else :
            self.plages_interdites = plages_interdites
        self.temperature_minimale = temp_minimale 

    # --- MÉTHODE PRIVÉE DE VALIDATION  ---
    def _valider_coherence(self, liste_plages: List[Creneau]):
        """
        Vérifie les règles métier : pas de chevauchement, pas de 24h total.
        Lève une erreur si c'est invalide.
        """
        if not liste_plages:
            return # Liste vide = OK

        # 1. Tri obligatoire pour vérifier les chevauchements
        liste_triee = sorted(liste_plages)

        # 2. Vérification des chevauchements
        for i in range(len(liste_triee) - 1):
            actuel = liste_triee[i]
            suivant = liste_triee[i+1]
            
            if actuel.chevauche(suivant):
                raise ValueError(f"Conflit : Les plages interdites {actuel} et {suivant} se chevauchent.")

        # 3. Vérification de la durée totale (< 24h)
        total_minutes = sum(c.duree_minutes() for c in liste_triee)
        MINUTES_24H = 24 * 60
        
        if total_minutes >= MINUTES_24H:
            raise ValueError("Configuration impossible : Les interdictions couvrent toute la journée (24h).")

    # --- GETTER / SETTER ---

    @property
    def plages_interdites(self) -> List[Creneau]:
        return self._plages_interdites

    @plages_interdites.setter
    def plages_interdites(self, nouvelles_plages: List[Creneau]):
        if not isinstance(nouvelles_plages, list):
            raise TypeError("Doit être une liste de Creneau")
        
        if not all(isinstance(c, Creneau) for c in nouvelles_plages):
            raise TypeError("La liste ne doit contenir que des objets Creneau")
        
        # On valide AVANT d'enregistrer
        self._valider_coherence(nouvelles_plages)
        
        # Si validation OK, on enregistre la version triée
        self._plages_interdites = sorted(nouvelles_plages)

    @property 
    def temperature_minimale(self) -> float :
        return self._temperature_minimale 
    @temperature_minimale.setter 
    def temperature_minimale(self, valeur) :
        if not isinstance(valeur, (float,int)) or valeur < 0 or valeur > 95 :
            raise ValueError("La température minimale doit être un nombre entre 0 et 95") 
        self._temperature_minimale = valeur 

    # --- HELPER D'AJOUT ---

    def ajouter_interdit(self, debut: time, fin: time):
        """Ajoute une plage interdite en vérifiant la cohérence globale."""
        nouveau = Creneau(debut, fin)
        
        # On crée une liste temporaire pour tester
        liste_test = self._plages_interdites + [nouveau]
        
        # On lance la validation sur l'ensemble
        self._valider_coherence(liste_test)
        
        # Si ça n'a pas planté, on valide l'ajout
        self._plages_interdites.append(nouveau)
        self._plages_interdites.sort()

    # --- INTERFACE SOLVER ---

    def est_autorise(self, heure_test: time) -> bool:
        """
        Retourne FALSE si l'heure tombe dans un interdit.
        """
        if not self._plages_interdites:
            return True 

        for plage_interdite in self._plages_interdites:
            # On utilise la méthode contient() qui existe dans creneau. 
            if plage_interdite.contient(heure_test):
                return False 
        
        return True
        
    def __repr__(self):
        if not self._plages_interdites:
            return "<Constraints: Pas de restriction (Autorisé 24h/24)>"
        return f"<Constraints: INTERDIT sur {self._plages_interdites}>" 