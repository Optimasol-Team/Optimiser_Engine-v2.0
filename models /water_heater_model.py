
class WaterHeater :
    def __init__(self, volume, power) :
        self.volume = volume               #EN LITRES 
        self.power = power                 #EN WATTS 
        self._coeff_isolation = 0 
        self._temperature_eau_froide = 10
    @property 
    def volume(self) :
        return self._volume 
    @volume.setter 
    def volume(self,valeur) :
        if valeur < 0 or not isinstance(valeur, (int, float)):
            raise ValueError("Le volume doit être un nombre positif") 
        self._volume = valeur 

    @property 
    def power(self) :
        return self._power
    @power.setter 
    def power(self,valeur) :
        if valeur < 0 or not isinstance(valeur, (int, float)):
            raise ValueError("La puissance nominale doit être un nombre positif") 
        self._power = valeur 

    @property 
    def coefficient_isolation(self) :
        return self._coeff_isolation 
    
    @coefficient_isolation.setter 
    def coefficient_isolation(self, valeur) :
        self._coeff_isolation = valeur # TODO : Règle interne à ajoiuter. 

    @property 
    def temperature_eau_froide(self) :
        return self._temperature_eau_froide 
    
    @temperature_eau_froide.setter 
    def temperature_eau_froide(self, valeur) :
        if valeur < 0 or not isinstance(valeur, (int, float)) :
            raise ValueError("Impossible : Veuillez entrez une valeur de la température physiquement réalisable.") 
        self._temperature_eau_froide = valeur


#Ces trois fonctions à REVOIR ! La physique n'est pas correcte. 
    def calculer_perte_temperature(self, temp_init, temp_amb, delta_Temps) :
        #TODO : Formule physique à ajouter. 
        pass 
    
    def calculer_temperature_chauffe(self, temp_initial, rate_puissance, delta_Temps) :
        #TODO : nouvelle température après injection de la puissance avec un rate. 
        #Ne pas oublier d'intégrer la fonction précédente pour les pertes naturelles. 

        pass 
    def calculer_temperature_tirage(self, temp_initial, volume_tiree) :
        temperature_eau_froide = self.temperature_eau_froide 
        #TODO : A faire la formule physique 
        pass

    def calculer_temperature(self, temp_init, rate_puissance, temp_amb, delta_Temps, volume_tiree) :
        temp_chauff = self.calculer_temperature_chauffe(temp_init, rate_puissance, delta_Temps) 
        temp_apres_tirage = self.calculer_temperature_tirage(temp_chauff, volume_tiree) 
        temp_final = self.calculer_perte_temperature(temp_apres_tirage, temp_amb, delta_Temps) 
        return temp_final 
    

    
        