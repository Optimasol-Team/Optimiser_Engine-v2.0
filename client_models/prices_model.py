from typing import List
from common import Creneau 
from datetime import time 
# 1. On définit une exception levée si appel à un paramètre du mode incompatible. 
class ModeIncompatibleError(Exception):
    """Levée quand on essaie d'accéder à une variable qui n'existe pas dans ce mode."""
    pass

class Prices:
    def __init__(self, mode="BASE", hp=0.22, hc=0.18, base=0.20, revente=0.10):
        # Valeurs par défaut
        self._hp = hp
        self._hc = hc
        self._base = base
        self._revente = revente
        self._mode = mode # On initialise un mode par défaut pour éviter les bugs
        self._creneaux_hp = [] 

    # Méthode pour vérifier si on est bien dans le mode attendu. 
    def _verifier_mode(self, mode_attendu: str):
        """Vérifie si on est dans le bon mode, sinon lève une le ModeIncompatibleError."""
        if self._mode != mode_attendu:
            # Ici, on lance l'exception unique, mais avec un message précis
            raise ModeIncompatibleError(
                f"Action impossible : Vous êtes en mode '{self._mode}', "
                f"mais cette action requiert le mode '{mode_attendu}'."
            )

    # --- Propriétés ---

    @property 
    def hp(self):
        self._verifier_mode("HPHC") 
        return self._hp 

    @hp.setter 
    def hp(self, valeur):
        self._verifier_mode("HPHC")
        # Validation du type : 
        if not isinstance(valeur, (int, float)) or valeur < 0:
            raise ValueError("Le prix HP doit être un nombre positif")
        self._hp = valeur 
    
    @property 
    def hc(self):
        self._verifier_mode("HPHC")
        return self._hc 

    @hc.setter 
    def hc(self, valeur):
        self._verifier_mode("HPHC")
        if not isinstance(valeur, (int, float)) or valeur < 0:
            raise ValueError("Le prix HC doit être un nombre positif")
        self._hc = valeur  

    @property 
    def base(self):
        self._verifier_mode("BASE")
        return self._base
        
    @base.setter 
    def base(self, valeur):
        self._verifier_mode("BASE")
        if not isinstance(valeur, (int, float)) or valeur < 0:
            raise ValueError("Le prix BASE doit être un nombre positif")
        self._base = valeur 


    @property 
    def revente(self):
        return self._revente
    
    @revente.setter
    def revente(self, valeur):
        if not isinstance(valeur, (int, float)) or valeur < 0:
            raise ValueError("Le prix de revente doit être un nombre positif")
        self._revente = valeur 

    @property 
    def mode(self):
        return self._mode 
    
    @mode.setter 
    def mode(self, valeur):
        if valeur not in ["HPHC", "BASE"]:
            raise ValueError("Le mode doit être 'HPHC' ou 'BASE'")
        self._mode = valeur 

    @property
    def creneaux_hp(self):
        self._verifier_mode("HPHC")
        return self._creneaux_hp

    @creneaux_hp.setter
    def creneaux_hp(self, nouvelle_liste: List[Creneau]):
        self._verifier_mode("HPHC") #On peut pas définir une liste de crénaux pour BASE. 
        # 1. Validation du TYPE (Est-ce une liste d'objets Creneau ?)
        if not isinstance(nouvelle_liste, list):
            raise TypeError("Il faut fournir une liste.")
        
        #On vérifie chaque élément avec Le all() : 
        if not all(isinstance(c, Creneau) for c in nouvelle_liste):
            raise TypeError("La liste ne doit contenir que des objets de type 'Creneau'")

        # 2. On trie la liste (indispensable pour vérifier les trous)
        liste_triee = sorted(nouvelle_liste) #Cela est possible avec __lt__ définie dans crenau. 

        # 3. Validation des CHEVAUCHEMENTS
        for i in range(len(liste_triee) - 1):
            actuel = liste_triee[i]
            suivant = liste_triee[i+1]
            
            if actuel.chevauche(suivant):
                raise ValueError(f"Conflit : Les créneaux {actuel} et {suivant} se chevauchent.")
            
            # Vérification stricte : la fin de l'un ne doit pas dépasser le début de l'autre
            if actuel.fin > suivant.debut:
                raise ValueError(f"Ordre invalide entre {actuel} et {suivant}")

        # 4. Validation de l'existence de HC également. (Pas 24h de HP)
        total_minutes = sum(c.duree_minutes() for c in liste_triee)
        if total_minutes >= 24 * 60:
            raise ValueError("Impossible : Les Heures Pleines ne peuvent pas couvrir 24h (il faut des HC !)")
        if total_minutes == 0 :
            raise ValueError("Impossible : Les Heures Creuses ne peuvent pas couvrir 24h (il faut des HP !)") 
        # Si tout est bon, on sauvegarde
        self._creneaux_hp = liste_triee
    
    
    #--- Une fonction pour calculer combien on paie à un instant t --- 
    def get_prix_achat_actuel(self, heure_test: time) -> float:
        """
        Retourne le prix du kWh à l'heure donnée selon le mode configuré.
        """
        if self._mode == "BASE":
            return self._base
        
        elif self._mode == "HPHC":
            # On vérifie si l'heure est dans un des créneaux HP
            #self.creneaux_hp est triée grâce au setter. 
            est_en_hp = any(c.debut <= heure_test < c.fin for c in self._creneaux_hp)
            
            if est_en_hp:
                return self._hp
            else:
                return self._hc
            
            #Si on donne exactement l'instant de début d'une creuse elle renvoit le tarif HC. 
