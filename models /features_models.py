
from enum import Enum


class OptimizationMode(Enum):
    AUTOCONS = "AutoCons"
    COST = "cost"


class Features :
    def __init__(self, gradation : bool, mode: OptimizationMode) :
        self.gradation = gradation #True or False selon si l'utilisateur a / veut le mode gradation
        self.mode = mode

    @property 
    def gradation(self) :
        return self._gradation 
    @gradation.setter 
    def gradation(self, valeur) :
        if not isinstance(valeur, bool) :
            raise TypeError("gradation doit être un booléen selon si le mode gradation est souhaité ou non") 
        self._gradation = valeur 
    
    @property
    def mode(self):
        return self._mode
    
    @mode.setter
    def mode(self, valeur):
        # Vérification ultra-robuste : ça DOIT être un membre de l'Enum
        if not isinstance(valeur, OptimizationMode):
            raise TypeError("Le mode doit être un objet OptimizationMode (ex: OptimizationMode.COST)")
        self._mode = valeur