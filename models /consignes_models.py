
from datetime import time, datetime 
from typing import List, Dict, Tuple

class PointConsign :
    def __init__(self, day : int, moment : time, temperature : float, volume : float = 30) : 
        self.day = day 
        self.moment = moment 
        self.temperature = temperature 
        self.volume_tire = volume 

    @property 
    def day(self) :
        return self._day 
    @day.setter 
    def day(self, valeur) :
        if valeur > 6 or valeur < 0 or not isinstance(valeur, int) :
            raise ValueError("Le jour doit être un int entre 0 et 6 (0 pour Lundi et 6 pour Dimanche)") 
        self._day = valeur 
    
    @property 
    def moment(self) :
        return self._moment 
    @moment.setter 
    def moment(self, valeur) :
        if not isinstance(valeur, time) :
            raise ValueError("Le moment doit être un moment de la journée du type time") 
        self._moment = valeur 
    
    @property 
    def temperature(self) :
        return self._temperature 
    
    @temperature.setter 
    def temperature(self, valeur) :
        if not isinstance(valeur, (int, float)) or (valeur > 99) or (valeur < 30) :
            raise ValueError("La température cible doit être un nombre entre 30 et 99") 
        self._temperature = valeur 
    
    @property 
    def volume_tire(self) :
        return self._volume 
    @volume_tire.setter 
    def volume_tire(self, valeur) :
        if not isinstance(valeur, (int, float)) or valeur < 0:
            raise ValueError("Le volume doit être un nombre positif")
        self._volume = valeur 
    
    def __lt__(self, other) :
        """Fonction implémentée pour faciliter le sort ailleurs""" 
        if not isinstance(other, PointConsign) :
            return NotImplemented 
        return (self.day, self.moment) < (other.day, other.moment) 
    
    def __repr__(self) :
        Liste = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"] 
        jour = Liste[self.day]
        moment = self.moment 
        temperature = self.temperature 
        volume = self.volume_tire 
        repr = "Consigne : " + jour + ", " + str(moment) + ", température souhaitée : " + temperature + ", volume prévu : " + volume 
        return repr 
    
class Planning:
    def __init__(self):
        self._consignes: List[PointConsign] = []

    def _nettoyer_et_trier(self, liste_brute: List[PointConsign]) -> List[PointConsign]:
        """
        Prend une liste de consignes, élimine les doublons de temps
        en gardant celle qui a la température la plus élevée,
        puis retourne la liste triée.
        """
        # Dictionnaire avec Clé = (Jour, Heure) -> Valeur = Objet PointConsign
        unique_consignes: Dict[Tuple[int, time], PointConsign] = {}

        for c in liste_brute:
            cle = (c.day, c.moment)
            
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
        liste_propre.sort() # Utilise le __lt__ défini dans PointConsign
        
        return liste_propre
    @property
    def consignes(self) -> List[PointConsign]:
        return self._consignes

    @consignes.setter
    def consignes(self, nouvelle_liste: List[PointConsign]):
        """
        Permet de remplacer tout le planning d'un coup.
        Valide le type de chaque élément et TRIE la liste.
        """
        if not isinstance(nouvelle_liste, list):
            raise TypeError("Le planning doit être une liste.")
        
        # Validation stricte du contenu
        for i, item in enumerate(nouvelle_liste):
            if not isinstance(item, PointConsign):
                raise TypeError(f"L'élément à l'index {i} n'est pas un PointConsign.")
        
        self._consignes = self._nettoyer_et_trier(nouvelle_liste) #On a bien fait une copie. 

    # --- 2. AJOUT / SUPPRESSION ---
    
    def ajouter(self, consigne: PointConsign):
        if not isinstance(consigne, PointConsign) :
            raise TypeError("consigne n'est pas un objet de type PointConsign, il ne peut pas être ajouté.") 
        liste_temporaire = self._consignes + [consigne]
        self._consignes = self._nettoyer_et_trier(liste_temporaire) 

    def supprimer(self, jour: int, heure: time):
        """
        Supprime une consigne spécifique basée sur son jour et son heure.
        Retourne True si trouvé et supprimé, False sinon.
        """
        # On cherche l'élément (on filtre pour garder ceux qui NE correspondent PAS)
        taille_avant = len(self._consignes)
        self._consignes = [
            c for c in self._consignes 
            if not (c.day == jour and c.moment == heure)
        ]
        return len(self._consignes) < taille_avant

    def vider(self):
        self._consignes.clear()

    # --- 3. LA MÉTHODE "HORIZON" (CRUCIALE POUR L'OPTIMISEUR)---

    def recuperer_consignes_futures(self, jour_actuel: int = None, heure_actuelle: time = None, horizon_heures: int = 24) -> List[PointConsign]:
        """
        Renvoie la liste des consignes qui tombent dans l'intervalle [Maintenant, Maintenant + Horizon].
        Gère intelligemment le bouclage de la semaine (Dimanche -> Lundi).
        """
        if jour_actuel is None or heure_actuelle is None:
            # On prend l'instant actuel : 
            maintenant = datetime.now()
            
            if jour_actuel is None:
                jour_actuel = maintenant.weekday() # Renvoie bien un int (0=Lundi...6=Dimanche comme dans la convention) 
            
            if heure_actuelle is None:
                heure_actuelle = maintenant.time() #L'heure. 
        
        
        if not self._consignes:
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
        for c in self._consignes:
            t_consigne = _to_minutes(c.day, c.moment)

            # Cas A : La consigne est dans le futur direct de cette semaine
            if t_debut <= t_consigne <= t_fin:
                resultat.append(c)
            
            # Cas B : Gestion du semaine suivante 
            elif (t_consigne + minutes_semaine) <= t_fin:
                resultat.append(c)
        #On fait un triage pour garder l'ordre naturel
        def cle_de_tri_relatif(consigne):
            t_abs = _to_minutes(consigne.day, consigne.moment)
            if t_abs < t_debut:
                return t_abs + minutes_semaine # On la projette dans le futur
            return t_abs

        resultat.sort(key=cle_de_tri_relatif)
        return resultat