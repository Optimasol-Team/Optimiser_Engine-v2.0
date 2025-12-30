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
    def coefficient_isolation(self, valeur):
        if not isinstance(valeur, (int, float)) or valeur < 0:
            raise ValueError("Le coefficient d'isolation doit être un nombre positif (en °C/min)")
        self._coeff_isolation = valeur

    @property 
    def temperature_eau_froide(self) :
        return self._temperature_eau_froide 
    
    @temperature_eau_froide.setter 
    def temperature_eau_froide(self, valeur) :
        if valeur < 0 or not isinstance(valeur, (int, float)) :
            raise ValueError("Impossible : Veuillez entrez une valeur de la température physiquement réalisable.") 
        self._temperature_eau_froide = valeur


# --- MÉTHODES PHYSIQUES ---

    
    
    def calculer_temperature_chauffe(self, temp_initial, rate_puissance, delta_Temps_minutes) :
        """
        Calcule l'élévation de température due à la résistance.
        Section 5.2.2 du PDF : "Gain Chauffe... DeltaT = E_elec / (M * Cp)"
        """
        # 1. Calcul de l'énergie apportée (Joules = Watts * Secondes)
        # rate_puissance est le x (entre 0 et 1)
        puissance_effective = self.power * rate_puissance
        dt_seconds = delta_Temps_minutes * 60
        energie_joules = puissance_effective * dt_seconds
        
        # 2. Constantes physiques
        C_p = 4185 # Capacité thermique de l'eau (J / kg / K)
        Masse = self.volume # 1 Litre d'eau ~= 1 kg
        
        # 3. Élévation de température
        if Masse > 0:
            delta_T = energie_joules / (Masse * C_p)
        else:
            delta_T = 0 # Évite la division par zéro si volume vide (cas théorique)
            
        return temp_initial + delta_T

    def calculer_temperature_tirage(self, temp_initial, volume_tiree) :
        """
        Calcule la température après mélange avec l'eau froide entrante.
        Section 5.2.2 du PDF : "T_mix = (1-rho)*T + rho*T_froide"
        """
        if self.volume == 0:
            return temp_initial

        # rho est le taux de renouvellement (entre 0 et 1)
        # On sature à 1 si on tire plus que le volume du ballon (ballon vidé)
        rho = min(volume_tiree / self.volume, 1.0)
        
        term_chaud = temp_initial * (1 - rho)
        term_froid = self.temperature_eau_froide * rho
        
        return term_chaud + term_froid

    def calculer_perte_temperature(self, temp_init, delta_Temps_minutes) :
        """
    On simplifie : on perd un nombre fixe de degrés par minute.
    C'est ce que le solveur (modèle linéaire) utilise.
        """
        # Ici, coefficient_isolation représente des °C perdus par minute
        perte_totale = self.coefficient_isolation * delta_Temps_minutes
        return temp_init - perte_totale

    def calculer_temperature(self, temp_init, rate_puissance, delta_Temps_minutes, volume_tiree):
        # 1. Mélange
        temp_apres_tirage = self.calculer_temperature_tirage(temp_init, volume_tiree)
        # 2. Chauffe
        temp_apres_chauffe = self.calculer_temperature_chauffe(temp_apres_tirage, rate_puissance, delta_Temps_minutes)
        # 3. Pertes
        temp_finale = self.calculer_perte_temperature(temp_apres_chauffe, delta_Temps_minutes)
        return temp_finale