"""External context holding forecast data and constraints for optimisation runs.

Author: @anaselb
"""



from datetime import datetime, timedelta
import numpy as np 
from ...domain import Client 
from .Exceptions import DimensionNotRespected 



class ExternalContext :
    """
    Encapsulates forecast data and availability masks for an optimisation horizon.

    Attributes
    ----------
    N : int
        (nombre de pas) Number of time steps in the horizon.
    step_minutes : int
        (pas en minutes) Duration of each step in minutes.
    reference_datetime : datetime.datetime
        (référence temporelle) Starting timestamp for the forecast window.
    prices_purchases : numpy.ndarray
        (prix d'achat) Purchase prices per step.
    prices_sell : numpy.ndarray
        (prix de revente) Resale prices per step.
    solar_production : numpy.ndarray
        (production solaire) Forecast solar production in watts for each step.
    house_consumption : numpy.ndarray
        (consommation maison) Baseline household consumption in watts.
    water_draws : numpy.ndarray
        (tirages d'eau) Expected hot water draws in litres for each step.
    future_setpoints : numpy.ndarray
        (consignes futures) Minimum required temperatures aligned with the horizon.
    availability_on : numpy.ndarray
        (disponibilité chauffe) Binary mask indicating when heating is allowed.
    off_peak_hours : numpy.ndarray
        (heures creuses) Binary signal representing off-peak grid availability.
    """
    def __init__(self, 
                 N : int = 96,                              #Nombre de pas de temps. 
                 step_minutes : int = 15 ,                  #Le pas en minutes. 
                 reference_datetime : datetime = None,              #Date et heure du contexte. 
                 prices_purchase : np.ndarray = None,       #Le tableau des prix (ligne), à partir de maintenant.  
                 prices_sell : np.ndarray = None,           #Le tableau (ligne) des prix de revente. 
                 solar_production : np.ndarray = None,      #Le tableau (ligne) de la production solaire. 
                 house_consumption : np.ndarray = None,     #Le tableau (ligne) de la consommation domestique. 
                 water_draws : np.ndarray = None,           #LE tableau (ligne) de la consommation d'eau. 
                 future_setpoints : np.ndarray = None,       #Le tableau (ligne) des consignes écrasées dans un tableau.   
                 availability_on : np.ndarray = None,       #Le tableau (ligne) des 0/1 pour possibilité de chauffe ou pas.
                 off_peak_hours : np.ndarray = None         #Le tableau (ligne) de HPHC (info utile pour simulations - génération trajectoire standard) 
                 ) :
        """
        Initialize the external context vectors for a given horizon.

        Parameters
        ----------
        N : int, optional
            (nombre de pas) Number of time steps across the horizon.
        step_minutes : int, optional
            (pas en minutes) Duration of each step in minutes.
        reference_datetime : datetime.datetime, optional
            (référence temporelle) Starting timestamp for the data.
        prices_purchase : numpy.ndarray, optional
            (prix d'achat) Purchase prices per step.
        prices_sell : numpy.ndarray, optional
            (prix de revente) Resale prices per step.
        solar_production : numpy.ndarray, optional
            (production solaire) Forecast solar production values.
        house_consumption : numpy.ndarray, optional
            (consommation maison) Baseline household consumption values.
        water_draws : numpy.ndarray, optional
            (tirages d'eau) Expected hot water draws aligned to the horizon.
        future_setpoints : numpy.ndarray, optional
            (consignes futures) Minimum temperature requirements per step.
        availability_on : numpy.ndarray, optional
            (disponibilité chauffe) Binary mask indicating allowed heating intervals.
        off_peak_hours : numpy.ndarray, optional
            (heures creuses) Binary signal for off-peak availability.

        Returns
        -------
        None
            (aucun retour) Populates the context attributes.
        """
        self.N = N 
        self.step_minutes = step_minutes
        self.reference_datetime = reference_datetime 
        self.prices_purchases = prices_purchase 
        self.prices_sell = prices_sell 
        self.solar_production = solar_production 
        self.house_consumption = house_consumption 
        self.water_draws = water_draws 
        self.future_setpoints = future_setpoints 
        self.availability_on = availability_on 
        self.off_peak_hours = off_peak_hours
        
    
    @property 
    def N(self) :
        """
        Number of time steps in the context horizon.

        Returns
        -------
        int
            (nombre de pas) Count of steps across the prediction window.
        """
        return self._N 
    @N.setter 
    def N(self, valeur) :
        """
        Set the number of steps while enforcing positivity.

        Parameters
        ----------
        valeur : int
            (nombre de pas) Desired number of time steps.

        Returns
        -------
        None
            (aucun retour) Updates the horizon length.

        Raises
        ------
        TypeError
            (type invalide) If the value is not an integer.
        ValueError
            (valeur négative) If the value is negative.
        """
        if not isinstance(valeur, int) :
            raise TypeError(f"Le paramètre {valeur} doit être un entier positif.") 
        elif valeur < 0 :
            raise ValueError(f"Le nombre {valeur} doit être positif") 
        else :
            self._N = valeur 

    @property 
    def step_minutes(self) :
        """
        Duration of each time step in minutes.

        Returns
        -------
        int
            (pas en minutes) Step length in minutes.
        """
        return self._step_minutes 
    @step_minutes.setter 
    def step_minutes(self, valeur) :
        """
        Define the step duration with minimum validation.

        Parameters
        ----------
        valeur : int
            (pas en minutes) Length of each time step in minutes.

        Returns
        -------
        None
            (aucun retour) Stores the provided step value.

        Raises
        ------
        TypeError
            (type invalide) If the value is not an integer.
        ValueError
            (pas invalide) If the duration is less than one minute.
        """
        if not isinstance(valeur, int) :
            raise TypeError("Le pas doit être un entier") 
        if valeur < 1 :
            raise ValueError("Le pas doit valoir au moins une minute") 
        self._step_minutes = valeur 

    @property
    def prices_purchases(self) :
        """
        Purchase price vector across the horizon.

        Returns
        -------
        numpy.ndarray or None
            (prix d'achat) Array of purchase prices per step.
        """
        return self._prices_purchases 
    @prices_purchases.setter 
    def prices_purchases(self, tab) :
        """
        Set the purchase prices vector after validating shape.

        Parameters
        ----------
        tab : numpy.ndarray or None
            (prix d'achat) Price values aligned with the horizon.

        Returns
        -------
        None
            (aucun retour) Stores the provided array.

        Raises
        ------
        TypeError
            (type invalide) If the input is not an array when provided.
        DimensionNotRespected
            (dimension incorrecte) If the array does not match the expected length.
        """
        if tab is None:
            self._prices_purchases = None
        else:
            ExternalContext.check_array(tab,self.N) 
            self._prices_purchases = tab 
    
    @property
    def prices_sell(self) :
        """
        Resale price vector across the horizon.

        Returns
        -------
        numpy.ndarray or None
            (prix de revente) Array of resale prices per step.
        """
        return self._prices_sell 
    @prices_sell.setter 
    def prices_sell(self, tab) :
        """
        Set the resale prices vector after validation.

        Parameters
        ----------
        tab : numpy.ndarray or None
            (prix de revente) Resale prices aligned with the horizon.

        Returns
        -------
        None
            (aucun retour) Stores the provided array.

        Raises
        ------
        TypeError
            (type invalide) If the input is not an array when provided.
        DimensionNotRespected
            (dimension incorrecte) If the array does not match the expected length.
        """
        if tab is None:
            self._prices_sell = None
        else:
            ExternalContext.check_array(tab,self.N) 
            self._prices_sell = tab 
    
    @property
    def solar_production(self) :
        """
        Forecast solar production values per step.

        Returns
        -------
        numpy.ndarray or None
            (production solaire) Solar production in watts for each step.
        """
        return self._solar_production 
    @solar_production.setter 
    def solar_production(self, tab) :
        """
        Set the solar production forecast vector.

        Parameters
        ----------
        tab : numpy.ndarray or None
            (production solaire) Forecast production aligned with the horizon.

        Returns
        -------
        None
            (aucun retour) Saves the provided array.

        Raises
        ------
        TypeError
            (type invalide) If the input is not an array when provided.
        DimensionNotRespected
            (dimension incorrecte) If the array length is inconsistent with N.
        """
        if tab is None:
            self._solar_production = None
        else:
            ExternalContext.check_array(tab,self.N) 
            self._solar_production = tab 
    
    @property
    def house_consumption(self) :
        """
        Baseline household consumption vector.

        Returns
        -------
        numpy.ndarray or None
            (consommation maison) Consumption values in watts per step.
        """
        return self._house_consumption 
    @house_consumption.setter 
    def house_consumption(self, tab) :
        """
        Set the household consumption profile.

        Parameters
        ----------
        tab : numpy.ndarray or None
            (consommation maison) Baseline demand values aligned to the horizon.

        Returns
        -------
        None
            (aucun retour) Stores the provided consumption vector.

        Raises
        ------
        TypeError
            (type invalide) If the input is not an array when provided.
        DimensionNotRespected
            (dimension incorrecte) If the array does not match the expected length.
        """
        if tab is None:
            self._house_consumption = None
        else:
            ExternalContext.check_array(tab,self.N) 
            self._house_consumption = tab 
    
    @property
    def water_draws(self) :
        """
        Expected hot water draw vector in litres.

        Returns
        -------
        numpy.ndarray or None
            (tirages d'eau) Draw volumes for each step.
        """
        return self._water_draws 
    @water_draws.setter 
    def water_draws(self, tab) :
        """
        Set the water draw vector with shape validation.

        Parameters
        ----------
        tab : numpy.ndarray or None
            (tirages d'eau) Volume draws aligned to the horizon.

        Returns
        -------
        None
            (aucun retour) Saves the provided draws.

        Raises
        ------
        TypeError
            (type invalide) If the input is not an array when provided.
        DimensionNotRespected
            (dimension incorrecte) If the array length differs from N.
        """
        if tab is None:
            self._water_draws = None
        else:
            ExternalContext.check_array(tab,self.N) 
            self._water_draws = tab 
    
    @property
    def future_setpoints(self) :
        """
        Vector of minimum required temperatures per step.

        Returns
        -------
        numpy.ndarray or None
            (consignes futures) Setpoint temperatures aligned to the horizon.
        """
        return self._future_setpoints 
    @future_setpoints.setter 
    def future_setpoints(self, tab) :
        """
        Set the future setpoints vector with validation.

        Parameters
        ----------
        tab : numpy.ndarray or None
            (consignes futures) Target temperatures aligned with the horizon.

        Returns
        -------
        None
            (aucun retour) Stores the provided setpoints.

        Raises
        ------
        TypeError
            (type invalide) If the input is not an array when provided.
        DimensionNotRespected
            (dimension incorrecte) If the array length differs from N.
        """
        if tab is None:
            self._future_setpoints = None
        else:
            ExternalContext.check_array(tab,self.N) 
            self._future_setpoints = tab 
    
    @property
    def availability_on(self) :
        """
        Binary availability mask for heater operation.

        Returns
        -------
        numpy.ndarray or None
            (disponibilité chauffe) Mask indicating when heating is permitted.
        """
        return self._availability_on 
    @availability_on.setter 
    def availability_on(self, tab) :
        """
        Set the heater availability mask.

        Parameters
        ----------
        tab : numpy.ndarray or None
            (disponibilité chauffe) Binary availability values aligned to the horizon.

        Returns
        -------
        None
            (aucun retour) Saves the provided mask.

        Raises
        ------
        TypeError
            (type invalide) If the input is not an array when provided.
        DimensionNotRespected
            (dimension incorrecte) If the array length differs from N.
        """
        if tab is None:
            self._availability_on = None
        else:
            ExternalContext.check_array(tab,self.N) 
            self._availability_on = tab 

    @property
    def off_peak_hours(self) :
        """
        Off-peak hour indicator across the horizon.

        Returns
        -------
        numpy.ndarray or None
            (heures creuses) Binary signal where 1 denotes off-peak availability.
        """
        return self._off_peaks 
    @off_peak_hours.setter 
    def off_peak_hours(self,tab) :
        """
        Set the off-peak indicator vector.

        Parameters
        ----------
        tab : numpy.ndarray or None
            (heures creuses) Binary representation of off-peak periods.

        Returns
        -------
        None
            (aucun retour) Stores the provided off-peak mask.

        Raises
        ------
        TypeError
            (type invalide) If the input is not an array when provided.
        DimensionNotRespected
            (dimension incorrecte) If the array length differs from N.
        """
        if tab is None:
            self._off_peaks = None
        else:
            ExternalContext.check_array(tab,self.N) 
            self._off_peaks = tab 


    @staticmethod
    def check_array(Tab : np.array, N_expected : int) :
        """
        Validate that an array matches the expected length and numeric type.

        Parameters
        ----------
        Tab : numpy.ndarray
            (tableau testé) Array to validate.
        N_expected : int
            (taille attendue) Required length of the array.

        Returns
        -------
        None
            (aucun retour) Performs validation without returning a value.

        Raises
        ------
        TypeError
            (type invalide) If the object is not an ndarray or contains non-numeric elements.
        DimensionNotRespected
            (dimension incorrecte) If the array length does not equal the expected size.
        """
        if not isinstance(Tab, np.ndarray) :
            raise TypeError(f"L'élément {Tab} n'est pas un numpy array.") 
        else :
            if Tab.shape != (N_expected,) :
                raise DimensionNotRespected(f"Le tableau {Tab} doit être une ligne de dimension {N_expected}") 
            else :
                for x in Tab :
                    if not isinstance(x,(int, float)) :
                        raise TypeError(f"L'élément {x} n'est pas un nombre.")  
        
    @classmethod 
    def from_client(cls, 
                    client : Client,                #Client concerné
                    reference_datetime : datetime = None,   #date à mettre dans le contexte. 
                    solar_productions : np.ndarray = None,                #un DF normalisé selon date/heure, pas, N. 
                    horizon : int = 24,             #l'horizon en heures.  
                    time_step_minutes : int = 15            #Pas de temps en minutes. 
                    ) :
        """
        Build an ExternalContext instance from a domain client definition.

        Parameters
        ----------
        client : Client
            (client métier) Client providing pricing, constraints, and planning data.
        reference_datetime : datetime.datetime, optional
            (référence temporelle) Timestamp marking the start of the horizon.
        solar_productions : numpy.ndarray, optional
            (production solaire) Optional solar production values aligned to the horizon.
        horizon : int, optional
            (horizon en heures) Length of the planning window in hours.
        time_step_minutes : int, optional
            (pas en minutes) Duration of each step in minutes.

        Returns
        -------
        ExternalContext
            (contexte externe) Populated context derived from the client configuration.

        Raises
        ------
        TypeError
            (paramètre invalide) If inputs have incorrect types or inconsistent dimensions.
        """
        if not isinstance(horizon,(int)) :
            raise TypeError("L'horizon doit être un entier.") 
        if horizon < 0 or horizon > 100 :
            raise TypeError("L'horizon doit être positif et ne doit pas dépasser 100 heures.") 
        if not isinstance(time_step_minutes,(int)) :
            raise TypeError("Le pas doit être un entier.") 
        if time_step_minutes < 0 or time_step_minutes > (horizon*60)/2 :
            raise TypeError("Le pas doit être positif et ne doit pas dépasser un demi de l'horizon") 

        N = int((horizon*60)/time_step_minutes)  
        if not isinstance(reference_datetime,datetime) :
            raise TypeError(f"{reference_datetime} n'est pas un objet de type datetime.") 
        if not isinstance(client, Client) :
            raise TypeError(f"{client} n'est pas un objet de type Client") 
        
        if solar_productions is not None :
            cls.check_array(solar_productions,N) 
        
        ####Maintenant, on commence les extractions. 
        #1 : prices purchases : 
        prices = np.zeros(N) 

        #2 : prices_sell : 
        prix_revente = client.prices.resale_price 
        prices_sell = np.full(N, prix_revente) 

        #3 : house consumption : 
        planning = client.constraints.consumption_profile
        h_cons = planning.get_vector(reference_datetime, N, time_step_minutes)  
        
        #4 : water draws / future setpoints : 
        # A. Initialisation
        w_draws = np.zeros(N)
        future_setpoints_vec = np.full(N, client.constraints.minimum_temperature)
        
        # B. Appel de la fonction recuperer_consignes_futures (on récupère la liste triée et filtrée)
        # On passe le jour et l'heure du début de la simulation
        events_list = client.planning.get_future_setpoints(
            jour_actuel=reference_datetime.weekday(), # 0=Lundi
            heure_actuelle=reference_datetime.time(),
            horizon_heures=horizon
        )
        #eventslist est une liste qui contient les poinconsignes triés commençant par reference_datetime et allant jusqu'à reference_datetime+horizon. 
        # C. Mapping "Push" : On place les événements dans les cases du vecteur
        minutes_in_week = 7 * 24 * 60 # Constante pour gérer le modulo semaine
        
        # On calcule le "temps absolu" du début de la simu en minutes depuis le début de la semaine
        # (Pour pouvoir comparer avec les consignes)
        t_start_week = reference_datetime.weekday() * 1440 + reference_datetime.hour * 60 + reference_datetime.minute
        
        for evt in events_list:
            # 1. Temps de l'événement en minutes depuis début de semaine (Lundi 00:00)
            t_evt_week = evt.day * 1440 + evt.time.hour * 60 + evt.time.minute
            
            # 2. Calcul du Delta (Combien de minutes entre le début simu et l'événement ?)
            delta_minutes = t_evt_week - t_start_week
            
            # Si négatif, c'est que l'événement est la semaine prochaine (bouclage)
            # Votre fonction 'recuperer_consignes_futures' ne renvoyant que du futur, 
            # si c'est "avant" dans la semaine, c'est forcément "après" temporellement.
            if delta_minutes < 0:
                delta_minutes += minutes_in_week
                
            # 3. Calcul de l'index (Le fameux "Bucket")
            # Ex: delta=12min, pas=15min -> index=0. (Ça tombe bien dans le premier quart d'heure)
            idx = int(delta_minutes / time_step_minutes)
            
            # 4. Remplissage (Sécurité bornes)
            if 0 <= idx < N:
                # On cumule les volumes (si 2 douches dans le même quart d'heure)
                w_draws[idx] += evt.drawn_volume
                
                # On prend la température la plus exigeante (future_setpoints_vec contient déjà la t_minimale) 
                future_setpoints_vec[idx] = max(future_setpoints_vec[idx], evt.temperature) 
        
        #5. availability :
        tab_availability = np.zeros(N) 

        for i in range(N):
            #Le temps à i est dt_i = date_actuelle + i*time_step_minutes. 
            dt_i = reference_datetime + timedelta(minutes=i * time_step_minutes)
            t_i = dt_i.time() 
            a = client.prices.get_current_purchase_price(t_i) 
            prices[i] = a 

            #On checke si dti = reference_datetime + i*pas tombe dans true ou bien false. 
            is_allowed = client.constraints.is_allowed(t_i) 
            if is_allowed :
                tab_availability[i] = 1 
        #6. Construction de off_peak_hours : 
        # Par défaut, on initialise à 1 (Le courant passe partout, correspond au mode BASE)
        off_peak_hours = np.ones(N) 
        
        # Si on est en HPHC, on vient "sculpter" les trous (les 0) correspondant aux Heures Pleines
        if client.prices.mode == "HPHC":
            hp_slots = client.prices.hp_slots
            for i in range(N):
                dt_i = reference_datetime + timedelta(minutes=i * time_step_minutes)
                t_i = dt_i.time()
                
                # Vérification si l'instant t est dans un créneau HP
                is_peak_hour = any(c.start <= t_i < c.end for c in hp_slots)
                
                if is_peak_hour:
                    off_peak_hours[i] = 0 # Le contacteur est ouvert (coupure)

        A = cls(N,
                time_step_minutes, 
                reference_datetime, 
                prices, 
                prices_sell, 
                solar_productions, 
                h_cons, 
                w_draws, 
                future_setpoints_vec,
                tab_availability,
                off_peak_hours) 
        
        return A 
