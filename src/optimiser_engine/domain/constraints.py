from typing import List
from datetime import time
from common import Creneau
from ..exceptions import OptimizerError
import numpy as np
from datetime import datetime, timedelta

class DimensionNotRespected(OptimizerError) :
    pass

class ProfilConsommation:
    points_per_day = 24
    def __init__(self, matrice_7x24=None, bruit_de_fond=300.0):
        # Si rien n'est fourni, on met le bruit de fond partout
        if matrice_7x24 is None:
            self.data = np.full((7, 24), float(bruit_de_fond))
        else:
            self.data = np.array(matrice_7x24)
        
        self.bruit_de_fond = bruit_de_fond
    
    @property 
    def data(self) :
        return self._data 
    @data.setter 
    def data(self,tab) :
        if not isinstance(tab,np.ndarray) :
            raise TypeError("Le tableau à mettre dans data doit être un np.ndarray") 
        if tab.shape != (7, ProfilConsommation.points_per_day):
            raise DimensionNotRespected(f"La dimension du tableau doit être {ProfilConsommation.points_per_day}x7") 
        self._data = tab 
    

    def get_vector(self, start_date : datetime, N : int, step_min : float):
        """
        Génère le vecteur de N points en gérant :
        1. Le passage d'un jour à l'autre (modulo 7).
        2. L'interpolation entre les heures pour un flux continu.
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
    


class Constraints:
    def __init__(self, planning_cons: ProfilConsommation = None, 
                 plages_interdites : List[Creneau] = None, 
                 temp_minimale = 10.0, 
                 ) :
        # On stocke les plages INTERDITES
        # Par défaut vide = Aucune interdiction = 24/24 Autorisé
        if plages_interdites is None :
            self.plages_interdites = [] 
        else :
            self.plages_interdites = plages_interdites
        if planning_cons is None :
            self.planning_consommation = ProfilConsommation() 
        else :
            self.planning_consommation = planning_cons
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

    @property
    def planning_consommation(self) -> ProfilConsommation: 
        return self._planning_consommation 

    @planning_consommation.setter
    def planning_consommation(self, valeur):
        if not isinstance(valeur, ProfilConsommation):
            raise TypeError("Le planning de consommation doit être un élément de type ProfilConsommation.")
        self._planning_consommation = valeur
  
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