"""Static system configuration objects used by optimisation inputs.

Author: @anaselb
"""

from ...domain import Client


class SystemConfig :
    """
    Stores physical and safety parameters for the domestic system.

    Attributes
    ----------
    power : float
        (puissance de chauffe) Nominal heating power in watts.
    volume : float
        (volume de cuve) Storage tank capacity in litres.
    heat_loss_coefficient : float
        (coefficient de pertes) Fixed temperature loss per minute.
    is_gradation : bool
        (gradation activée) Indicates if partial power modulation is available.
    T_cold_water : float
        (température eau froide) Expected inlet cold water temperature in Celsius.
    T_min_safe : float
        (température minimale) Minimum allowed temperature for safety.
    T_max_safe : float
        (température maximale) Maximum allowed temperature for safety.
    """ 
    def __init__(self, power = None, volume = None, heat_loss_coefficient = None, is_gradation = True, T_cold_water = None, T_min = 5, T_max = 99) :
        """
        Initialize static system parameters.

        Parameters
        ----------
        power : float, optional
            (puissance de chauffe) Nominal heater power in watts.
        volume : float, optional
            (volume de cuve) Tank capacity in litres.
        heat_loss_coefficient : float, optional
            (coefficient de pertes) Temperature loss per minute.
        is_gradation : bool, optional
            (gradation activée) True if partial power control is supported.
        T_cold_water : float, optional
            (température eau froide) Inlet water temperature in Celsius.
        T_min : float, optional
            (température minimale) Minimum safety temperature, default 5°C.
        T_max : float, optional
            (température maximale) Maximum safety temperature, default 99°C.

        Returns
        -------
        None
            (aucun retour) Stores provided configuration values.
        """
        self.power = power 
        self.volume = volume
        self.heat_loss_coefficient = heat_loss_coefficient 
        self.T_cold_water = T_cold_water 
        self.T_min_safe = T_min 
        self.T_max_safe = T_max 
        self.is_gradation = is_gradation 

    @property 
    def power(self) :
        """
        Nominal heating power of the system.

        Returns
        -------
        float or None
            (puissance de chauffe) Power rating in watts.
        """
        return self._power 
    @power.setter 
    def power(self, valeur) :
        """
        Set the nominal heating power with validation.

        Parameters
        ----------
        valeur : float
            (puissance de chauffe) Desired power rating in watts.

        Returns
        -------
        None
            (aucun retour) Updates the stored power.

        Raises
        ------
        TypeError
            (type invalide) If the value is not numeric.
        ValueError
            (valeur négative) If the power is negative.
        """
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
        """
        Storage tank capacity.

        Returns
        -------
        float or None
            (volume de cuve) Volume in litres.
        """
        return self._volume
    @volume.setter 
    def volume(self, valeur) :
        """
        Set the tank capacity after validation.

        Parameters
        ----------
        valeur : float
            (volume de cuve) Desired volume in litres.

        Returns
        -------
        None
            (aucun retour) Records the capacity value.

        Raises
        ------
        TypeError
            (type invalide) If the value is not numeric.
        ValueError
            (valeur négative) If the volume is negative.
        """
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
        """
        Assumed inlet cold water temperature.

        Returns
        -------
        float or None
            (température eau froide) Temperature in Celsius.
        """
        return self._T_cold_water 
    @T_cold_water.setter 
    def T_cold_water(self, valeur) :
        """
        Set the inlet cold water temperature.

        Parameters
        ----------
        valeur : float
            (température eau froide) Expected inlet temperature in Celsius.

        Returns
        -------
        None
            (aucun retour) Saves the cold water setting.

        Raises
        ------
        TypeError
            (type invalide) If the value is not numeric.
        ValueError
            (température invalide) If outside the 0–60°C range.
        """
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
        """
        Minimum safety temperature.

        Returns
        -------
        float or None
            (température minimale) Lower bound in Celsius.
        """
        return self._T_min 
    @T_min_safe.setter 
    def T_min_safe(self, valeur) :
        """
        Define the minimum allowed temperature for safety.

        Parameters
        ----------
        valeur : float
            (température minimale) Minimum safety threshold in Celsius.

        Returns
        -------
        None
            (aucun retour) Updates the minimum safety value.

        Raises
        ------
        TypeError
            (type invalide) If the value is not numeric.
        ValueError
            (température invalide) If outside the 0–50°C range.
        """
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
        """
        Maximum safety temperature.

        Returns
        -------
        float or None
            (température maximale) Upper bound in Celsius.
        """
        return self._T_max
    @T_max_safe.setter 
    def T_max_safe(self, valeur) :
        """
        Set the maximum allowed temperature for safety.

        Parameters
        ----------
        valeur : float
            (température maximale) Upper safety threshold in Celsius.

        Returns
        -------
        None
            (aucun retour) Stores the maximum safety value.

        Raises
        ------
        TypeError
            (type invalide) If the value is not numeric.
        ValueError
            (température invalide) If outside the 50–100°C range.
        """
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
    def heat_loss_coefficient(self) :
        """
        Temperature loss coefficient applied each minute.

        Returns
        -------
        float or None
            (coefficient de pertes) Loss rate expressed in °C per minute.
        """
        return self._heat_loss_coefficient 
    @heat_loss_coefficient.setter 
    def heat_loss_coefficient(self, valeur) :
        """
        Configure the heat loss coefficient.

        Parameters
        ----------
        valeur : float
            (coefficient de pertes) Temperature drop per minute.

        Returns
        -------
        None
            (aucun retour) Updates the stored coefficient.

        Raises
        ------
        TypeError
            (type invalide) If the value is not numeric.
        """
        if valeur is None :
            self._heat_loss_coefficient = None 
        else : 
            if not isinstance(valeur, (int, float)) :
                raise TypeError("Le coefficient de pertes doit être un nombre") 
            else :
                self._heat_loss_coefficient = valeur  

    @property
    def is_gradation(self) :
        """
        Flag indicating whether gradation mode is enabled.

        Returns
        -------
        bool or None
            (gradation activée) True when modulation is supported.
        """
        return self._is_gradation 
    @is_gradation.setter 
    def is_gradation(self, valeur) :
        """
        Set the gradation capability flag.

        Parameters
        ----------
        valeur : bool
            (gradation activée) Whether the system supports partial power control.

        Returns
        -------
        None
            (aucun retour) Stores the gradation setting.

        Raises
        ------
        TypeError
            (type invalide) If the value is not boolean.
        """
        if valeur is None :
            self._is_gradation = valeur 
        else :
            if not isinstance(valeur, bool) :
                raise TypeError(f"La variable {valeur} doit être un booléen") 
            self._is_gradation = valeur 

    @classmethod 
    def from_client(cls, client : Client):
        """
        Build a SystemConfig instance from a domain client.

        Parameters
        ----------
        client : Client
            (client métier) Client object providing asset and constraint data.

        Returns
        -------
        SystemConfig
            (configuration système) Static configuration derived from the client.

        Raises
        ------
        TypeError
            (type invalide) If the provided object is not a Client instance.
        """
        if not isinstance(client, Client):
            raise TypeError(f"La variable {client} doit être de type Client") 
        
        water_heater = client.water_heater
        
        # On récupère les vraies valeurs du métier
        power = water_heater.power
        volume = water_heater.volume
        
        # Conversion du coefficient pour le pas de temps (ex: 15 min)
        # Si le métier stocke une perte par minute, le solveur doit l'intégrer
        c_pertes_par_pas = water_heater.insulation_coefficient 
        
        T_cold = water_heater.cold_water_temperature
        
        # CRUCIAL : On récupère les réglages de l'utilisateur !
        is_gradation = client.features.gradation #
        T_min = client.constraints.minimum_temperature #
        T_max = 95 # Sécurité haute fixe

        return cls(power, volume, c_pertes_par_pas, is_gradation, T_cold, T_min, T_max)
    def __repr__(self) :
        """
        Human-readable summary of the system configuration.

        Returns
        -------
        str
            (représentation textuelle) Description of key static parameters.
        """
        A = f"Paramètres physiques / statiques du système : " \
        f"Puissance de chauffe-eau : {self.power}" \
        f"Volume du chauffe-eau : {self.volume}" \
        f"Coefficient de pertes : {self.heat_loss_coefficient}" \
        f"Température d'eau froide : {self.T_cold_water}" \
        f"Températures de safety minimales et maximales, respectivement : {self.T_min_safe} et {self.T_max_safe}" 
        return A 
