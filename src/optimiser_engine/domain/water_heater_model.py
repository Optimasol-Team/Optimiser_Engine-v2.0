"""Physical water heater model supporting validation and simple thermal calculations used by the optimiser.

Author: @anaselb
"""

class WaterHeater :
    """
    Represents a domestic water heater with basic physical parameters and helper calculations.

    Attributes
    ----------
    volume : float
        (volume en litres) Capacity of the storage tank in litres.
    power : float
        (puissance nominale) Nominal heating power in watts.
    insulation_coefficient : float
        (coefficient d'isolation) Fixed temperature loss per minute.
    cold_water_temperature : float
        (température eau froide) Inlet cold water temperature in degrees Celsius.
    """
    def __init__(self, volume, power) :
        """
        Initialize the water heater with the given volume and power ratings.

        Parameters
        ----------
        volume : float
            (volume en litres) Tank capacity in litres.
        power : float
            (puissance en watts) Nominal heating power in watts.

        Returns
        -------
        None
            (aucun retour) The constructor sets instance attributes without returning a value.
        """
        self.volume = volume               #EN LITRES 
        self.power = power                 #EN WATTS 
        self._insulation_coefficient = 0 
        self._cold_water_temperature = 10
    @property 
    def volume(self) :
        """
        Retrieve the configured tank volume.

        Returns
        -------
        float
            (volume en litres) Current stored volume in litres.
        """
        return self._volume 
    @volume.setter 
    def volume(self,valeur) :
        """
        Update the tank volume after validating the provided value.

        Parameters
        ----------
        valeur : float
            (volume en litres) Proposed capacity value in litres.

        Returns
        -------
        None
            (aucun retour) The setter updates the internal volume.

        Raises
        ------
        ValueError
            (valeur invalide) If the value is negative or not numeric.
        """
        if valeur < 0 or not isinstance(valeur, (int, float)):
            raise ValueError("Le volume doit être un nombre positif") 
        self._volume = valeur 

    @property 
    def power(self) :
        """
        Access the nominal heating power.

        Returns
        -------
        float
            (puissance nominale) Configured power rating in watts.
        """
        return self._power
    @power.setter 
    def power(self,valeur) :
        """
        Set the nominal heating power while enforcing a positive numeric value.

        Parameters
        ----------
        valeur : float
            (puissance en watts) Desired power rating in watts.

        Returns
        -------
        None
            (aucun retour) The setter stores the validated power.

        Raises
        ------
        ValueError
            (puissance invalide) If the provided power is not a positive number.
        """
        if valeur < 0 or not isinstance(valeur, (int, float)):
            raise ValueError("La puissance nominale doit être un nombre positif") 
        self._power = valeur 

    @property 
    def insulation_coefficient(self) :
        """
        Get the fixed heat loss coefficient.

        Returns
        -------
        float
            (coefficient d'isolation) Degrees lost per minute due to insulation.
        """
        return self._insulation_coefficient 
    
    @insulation_coefficient.setter 
    def insulation_coefficient(self, valeur):
        """
        Set the heat loss coefficient, ensuring it is a non-negative number.

        Parameters
        ----------
        valeur : float
            (coefficient d'isolation) Temperature drop per minute.

        Returns
        -------
        None
            (aucun retour) The setter updates the insulation coefficient.

        Raises
        ------
        ValueError
            (coefficient invalide) If the coefficient is negative or not numeric.
        """
        if not isinstance(valeur, (int, float)) or valeur < 0:
            raise ValueError("Le coefficient d'isolation doit être un nombre positif (en °C/min)")
        self._insulation_coefficient = valeur

    @property 
    def cold_water_temperature(self) :
        """
        Access the configured inlet cold water temperature.

        Returns
        -------
        float
            (température eau froide) Current assumed cold water temperature in Celsius.
        """
        return self._cold_water_temperature 
    
    @cold_water_temperature.setter 
    def cold_water_temperature(self, valeur) :
        """
        Define the inlet cold water temperature with validation.

        Parameters
        ----------
        valeur : float
            (température eau froide) Expected supply temperature in Celsius.

        Returns
        -------
        None
            (aucun retour) The setter stores the supplied temperature.

        Raises
        ------
        ValueError
            (température invalide) If the value is negative or not numeric.
        """
        if valeur < 0 or not isinstance(valeur, (int, float)) :
            raise ValueError("Impossible : Veuillez entrez une valeur de la température physiquement réalisable.") 
        self._cold_water_temperature = valeur


# --- MÉTHODES PHYSIQUES ---

    
    
    def calculate_heating_temperature(self, temp_initial, power_ratio, time_delta_minutes) :
        """
        Compute the temperature increase from resistive heating during a time interval.

        Parameters
        ----------
        temp_initial : float
            (température initiale) Starting water temperature in Celsius.
        power_ratio : float
            (ratio de puissance) Fraction of nominal power applied between 0 and 1.
        time_delta_minutes : float
            (durée en minutes) Duration of the heating period in minutes.

        Returns
        -------
        float
            (température finale) Temperature after applying the calculated heating gain.
        """
        # 1. Calcul de l'énergie apportée (Joules = Watts * Secondes)
        # rate_puissance est le x (entre 0 et 1)
        puissance_effective = self.power * power_ratio
        dt_seconds = time_delta_minutes * 60
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

    def calculate_draw_temperature(self, temp_initial, drawn_volume) :
        """
        Estimate the mixed temperature after drawing a volume and replenishing with cold water.

        Parameters
        ----------
        temp_initial : float
            (température initiale) Starting tank temperature in Celsius.
        drawn_volume : float
            (volume soutiré) Volume drawn from the tank in litres.

        Returns
        -------
        float
            (température mélangée) Temperature after the draw event.
        """
        if self.volume == 0:
            return temp_initial

        # rho est le taux de renouvellement (entre 0 et 1)
        # On sature à 1 si on tire plus que le volume du ballon (ballon vidé)
        rho = min(drawn_volume / self.volume, 1.0)
        
        term_chaud = temp_initial * (1 - rho)
        term_froid = self.cold_water_temperature * rho
        
        return term_chaud + term_froid

    def calculate_temperature_loss(self, temp_init, time_delta_minutes) :
        """
        Apply a fixed temperature loss over a duration to approximate thermal leakage.

        Parameters
        ----------
        temp_init : float
            (température initiale) Temperature before losses in Celsius.
        time_delta_minutes : float
            (durée en minutes) Duration over which losses apply.

        Returns
        -------
        float
            (température ajustée) Temperature after deducting insulation losses.
        """
        # Ici, coefficient_isolation représente des °C perdus par minute
        perte_totale = self.insulation_coefficient * time_delta_minutes
        return temp_init - perte_totale

    def calculate_temperature(self, temp_init, power_ratio, time_delta_minutes, drawn_volume):
        """
        Compute the resulting tank temperature after draw, heating, and losses in one step.

        Parameters
        ----------
        temp_init : float
            (température initiale) Starting temperature before applying the step.
        power_ratio : float
            (ratio de puissance) Fraction of nominal power applied between 0 and 1.
        time_delta_minutes : float
            (durée en minutes) Step duration in minutes.
        drawn_volume : float
            (volume soutiré) Volume extracted during the step in litres.

        Returns
        -------
        float
            (température finale) Final temperature after the combined effects.
        """
        # 1. Mélange
        temp_apres_tirage = self.calculate_draw_temperature(temp_init, drawn_volume)
        # 2. Chauffe
        temp_apres_chauffe = self.calculate_heating_temperature(temp_apres_tirage, power_ratio, time_delta_minutes)
        # 3. Pertes
        temp_finale = self.calculate_temperature_loss(temp_apres_chauffe, time_delta_minutes)
        return temp_finale
    
    def __repr__(self) :
        """
        Return a human-readable description of the water heater.

        Returns
        -------
        str
            (représentation textuelle) Formatted summary.
        """
        sum1 = "Water Heater : \n"
        sum_volume = f"-Volume (Volume): {self.volume}\n" 
        sum_power = f"-Nominal Power (Puissance nominale): {self.power}\n" 
        sum_insula = f"-Insulation coefficient (coefficient de pertes) : {self.insulation_coefficient} °C/min\n" 
        sum_cold = f"-Cold Water considered (Eau froide): {self.cold_water_temperature} °C"
        return sum1 + sum_volume + sum_power + sum_insula + sum_cold 
    