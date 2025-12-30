"""
optimiser_service/models_optimiser/system_config.py
Fichier implémentant la classe SystemConfig qui représente les configurations statiques du système domestique. 
Avec la classe ExternalContext et Température initiale, ils représentent l'objet OptimisationInputs à optimiser. 

Author : @anaselb 
"""

from ...domain import Client


class SystemConfig :
    """Classe pour les configurations statiques d'un système. """ 
    def __init__(self, power = None, volume = None, C_pertes = None, is_gradation = True, T_cold_water = None, T_min = 5, T_max = 99) :
        self.power = power 
        self.volume = volume
        self.C_pertes = C_pertes 
        self.T_cold_water = T_cold_water 
        self.T_min_safe = T_min 
        self.T_max_safe = T_max 
        self.is_gradation = is_gradation 
    
    @property 
    def power(self) :
        return self._power 
    @power.setter 
    def power(self, valeur) :
        if valeur is None :
            self._power = None 
        else : 
            if not isinstance(valeur, (int, float)) :
                raise TypeError("La puissance doit être un nombre") 
            elif valeur < 0 :
                raise ValueError("La puissance doit être un nombre positif") 
            else :
                self._power = valeur 

    @property 
    def volume(self) :
        return self._volume
    @volume.setter 
    def volume(self, valeur) :
        if valeur is None :
            self._volume = None 
        else : 
            if not isinstance(valeur, (int, float)) :
                raise TypeError("Le volume doit être un nombre") 
            elif valeur < 0 :
                raise ValueError("Le volume doit être un nombre positif") 
            else :
                self._volume = valeur 
    @property 
    def T_cold_water(self) :
        return self._T_cold_water 
    @T_cold_water.setter 
    def T_cold_water(self, valeur) :
        if valeur is None :
            self._T_cold_water = valeur 
        else :
            if not isinstance(valeur, (int, float)) :
                raise TypeError("La température d'eau froide doit être un nombre.") 
            elif valeur < 0 or valeur > 60 :
                raise ValueError("La température d'eau froide doit être un nombre entre 0 et 60") 
            else :
                self._T_cold_water = valeur 

        
    @property 
    def T_min_safe(self) :
        return self._T_min 
    @T_min_safe.setter 
    def T_min_safe(self, valeur) :
        if valeur is None :
            self._T_min = None 
        else : 
            if not isinstance(valeur, (int, float)) :
                raise TypeError("La température minimale doit être un nombre") 
            elif (valeur < 0) or (valeur>50) :
                raise ValueError("La température de safety minimale doit être entre 0 et 50")  
            else :
                self._T_min = valeur  

    @property 
    def T_max_safe(self) :
        return self._T_max
    @T_max_safe.setter 
    def T_max_safe(self, valeur) :
        if valeur is None :
            self._T_max = None 
        else : 
            if not isinstance(valeur, (int, float)) :
                raise TypeError("La température maximale doit être un nombre") 
            elif (valeur < 50) or (valeur>100) :
                raise ValueError("La température de safety maximale doit être entre 50 et 100")  
            else :
                self._T_max = valeur 
    
    @property 
    def C_pertes(self) :
        return self._C_pertes 
    @C_pertes.setter 
    def C_pertes(self, valeur) :
        if valeur is None :
            self._C_pertes = None 
        else : 
            if not isinstance(valeur, (int, float)) :
                raise TypeError("Le coefficient de pertes doit être un nombre") 
            else :
                self._C_pertes = valeur  

    @property
    def is_gradation(self) :
        return self._is_gradation 
    @is_gradation.setter 
    def is_gradation(self, valeur) :
        if valeur is None :
            self._is_gradation = valeur 
        else :
            if not isinstance(valeur, bool) :
                raise TypeError(f"La variable {valeur} doit être un booléen") 
            self._is_gradation = valeur 

    @classmethod 
    def from_client(cls, client : Client):
        if not isinstance(client, Client):
            raise TypeError(f"La variable {client} doit être de type Client") 
        
        water_heater = client.chauffe_eau
        
        # On récupère les vraies valeurs du métier
        power = water_heater.power
        volume = water_heater.volume
        
        # Conversion du coefficient pour le pas de temps (ex: 15 min)
        # Si le métier stocke une perte par minute, le solveur doit l'intégrer
        c_pertes_par_pas = water_heater.coefficient_isolation 
        
        T_cold = water_heater.temperature_eau_froide
        
        # CRUCIAL : On récupère les réglages de l'utilisateur !
        is_gradation = client.features.gradation #
        T_min = client.contraintes.temperature_minimale #
        T_max = 95 # Sécurité haute fixe

        return cls(power, volume, c_pertes_par_pas, is_gradation, T_cold, T_min, T_max)
    def __repr__(self) :
        A = f"Paramètres physiques / statiques du système : " \
        f"Puissance de chauffe-eau : {self.power}" \
        f"Volume du chauffe-eau : {self.volume}" \
        f"Coefficient de pertes : {self.C_pertes}" \
        f"Température d'eau froide : {self.T_cold_water}" \
        f"Températures de safety minimales et maximales, respectivement : {self.T_min_safe} et {self.T_max_safe}" 
        return A 