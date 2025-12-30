from datetime import time 

class Creneau:
    def __init__(self, debut: time, fin: time):
        if debut >= fin:
            raise ValueError("Le début doit être avant la fin (pas de passage de minuit géré ici pour simplifier)")
        self.debut = debut
        self.fin = fin

    # Cette méthode permet d'utiliser sort() sur une liste de créneaux (pour pouvoir comparer avec un < plus tard.)
    def __lt__(self, other):
        return self.debut < other.debut

    def chevauche(self, autre_creneau) -> bool:
        """Retourne True si les deux créneaux se marchent dessus."""
        # Logique : (A commence avant la fin de B) ET (B commence avant la fin de A)
        return self.debut < autre_creneau.fin and autre_creneau.debut < self.fin
    
    def contient(self, moment : time) :
        if self.debut <= moment < self.fin :
            return True 
        return False 
    
    def duree_minutes(self):
        # Petit calcul pour convertir en minutes
        h1 = self.debut.hour * 60 + self.debut.minute
        h2 = self.fin.hour * 60 + self.fin.minute
        return h2 - h1

    def __repr__(self):
        return f"[{self.debut.strftime('%H:%M')} - {self.fin.strftime('%H:%M')}]"