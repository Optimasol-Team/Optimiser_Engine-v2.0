


from datetime import datetime, timedelta
import numpy as np 
from ...domain import Client 
from .Exceptions import DimensionNotRespected 



class ExternalContext :
    """
    Classe définissant le contexte externe pour l'optimisation.
    
    Cette classe encapsule l'ensemble des données prévisionnelles et contraintes temporelles
    nécessaires à la planification du système sur un horizon de N pas de temps.
    
    Attributes:
        date_heure (datetime): Moment de référence (timestamp) marquant le début du contexte.
                               Représente l'instant t=0 de l'horizon de prévision.
        
        prices_purchase (np.ndarray): Vecteur des prix d'achat de l'électricité [€/kWh].
                                      Taille (N,). Chaque élément correspond au prix applicable
                                      au pas de temps t, depuis l'instant date_heure.
        
        prices_sell (np.ndarray): Vecteur des prix de revente de l'électricité au réseau [€/kWh].
                                  Taille (N,). Définit le tarif de rachat pour chaque pas de temps.
        
        solar_production (np.ndarray): Vecteur de la production photovoltaïque prévisionnelle [Watts].
                                       Taille (N,). Représente la puissance solaire estimée disponible
                                       à chaque pas de temps sur l'horizon.
        
        house_consumption (np.ndarray): Vecteur de la consommation électrique basale de la maison [Watts].
                                        Taille (N,). Correspond à la charge domestique hors chauffe-eau
                                        (électroménager, éclairage, etc.) prévue pour chaque pas.
        
        water_draws (np.ndarray): Vecteur des tirages d'eau chaude [Litres].
                                  Taille (N,). Indique le volume d'eau puisé par l'utilisateur
                                  à chaque pas de temps (lié au planning de consignes).
        
        future_consigns (np.ndarray): Vecteur des consignes de température imposées [°C].
                                      Taille (N,). Représente les températures minimales requises
                                      par le client pour assurer son confort thermique, extraites
                                      du planning et alignées sur la grille temporelle.
         availability_on (np.ndarray): Masque binaire de disponibilité du chauffe-eau [bool ou 0/1].
                                      Taille (N,). Valeur 1 (ou True) = chauffe autorisée,
                                      Valeur 0 (ou False) = chauffe interdite (heures pleines,
                                      contraintes réseau, etc.).
    """
    def __init__(self, 
                 N : int = 96,                              #Nombre de pas de temps. 
                 step_minutes : int = 15 ,                  #Le pas en minutes. 
                 date_heure : datetime = None,              #Date et heure du contexte. 
                 prices_purchase : np.ndarray = None,       #Le tableau des prix (ligne), à partir de maintenant.  
                 prices_sell : np.ndarray = None,           #Le tableau (ligne) des prix de revente. 
                 solar_production : np.ndarray = None,      #Le tableau (ligne) de la production solaire. 
                 house_consumption : np.ndarray = None,     #Le tableau (ligne) de la consommation domestique. 
                 water_draws : np.ndarray = None,           #LE tableau (ligne) de la consommation d'eau. 
                 future_consigns : np.ndarray = None,       #Le tableau (ligne) des consignes écrasées dans un tableau.   
                 availability_on : np.ndarray = None,       #Le tableau (ligne) des 0/1 pour possibilité de chauffe ou pas.
                 off_peak_hours : np.ndarray = None         #Le tableau (ligne) de HPHC (info utile pour simulations - génération trajectoire standard) 
                 ) :
        self.N = N 
        self.step_minutes = step_minutes
        self.date_heure = date_heure 
        self.prices_purchases = prices_purchase 
        self.prices_sell = prices_sell 
        self.solar_production = solar_production 
        self.house_consumption = house_consumption 
        self.water_draws = water_draws 
        self.future_consigns = future_consigns 
        self.availability_on = availability_on 
        self.off_peak_hours = off_peak_hours
        
    
    @property 
    def N(self) :
        return self._N 
    @N.setter 
    def N(self, valeur) :
        if not isinstance(valeur, int) :
            raise TypeError(f"Le paramètre {valeur} doit être un entier positif.") 
        elif valeur < 0 :
            raise ValueError(f"Le nombre {valeur} doit être positif") 
        else :
            self._N = valeur 

    @property 
    def step_minutes(self) :
        return self._step_minutes 
    @step_minutes.setter 
    def step_minutes(self, valeur) :
        if not isinstance(valeur, int) :
            raise TypeError("Le pas doit être un entier") 
        if valeur < 1 :
            raise ValueError("Le pas doit valoir au moins une minute") 
        self._step_minutes = valeur 

    @property
    def prices_purchases(self) :
        return self._prices_purchases 
    @prices_purchases.setter 
    def prices_purchases(self, tab) :
        if tab is None:
            self._prices_purchases = None
        else:
            ExternalContext.check_array(tab,self.N) 
            self._prices_purchases = tab 
    
    @property
    def prices_sell(self) :
        return self._prices_sell 
    @prices_sell.setter 
    def prices_sell(self, tab) :
        if tab is None:
            self._prices_sell = None
        else:
            ExternalContext.check_array(tab,self.N) 
            self._prices_sell = tab 
    
    @property
    def solar_production(self) :
        return self._solar_production 
    @solar_production.setter 
    def solar_production(self, tab) :
        if tab is None:
            self._solar_production = None
        else:
            ExternalContext.check_array(tab,self.N) 
            self._solar_production = tab 
    
    @property
    def house_consumption(self) :
        return self._house_consumption 
    @house_consumption.setter 
    def house_consumption(self, tab) :
        if tab is None:
            self._house_consumption = None
        else:
            ExternalContext.check_array(tab,self.N) 
            self._house_consumption = tab 
    
    @property
    def water_draws(self) :
        return self._water_draws 
    @water_draws.setter 
    def water_draws(self, tab) :
        if tab is None:
            self._water_draws = None
        else:
            ExternalContext.check_array(tab,self.N) 
            self._water_draws = tab 
    
    @property
    def future_consigns(self) :
        return self._future_consigns 
    @future_consigns.setter 
    def future_consigns(self, tab) :
        if tab is None:
            self._future_consigns = None
        else:
            ExternalContext.check_array(tab,self.N) 
            self._future_consigns = tab 
    
    @property
    def availability_on(self) :
        return self._availability_on 
    @availability_on.setter 
    def availability_on(self, tab) :
        if tab is None:
            self._availability_on = None
        else:
            ExternalContext.check_array(tab,self.N) 
            self._availability_on = tab 

    @property
    def off_peak_hours(self) :
        return self._off_peaks 
    @off_peak_hours.setter 
    def off_peak_hours(self,tab) :
        if tab is None:
            self._off_peaks = None
        else:
            ExternalContext.check_array(tab,self.N) 
            self._off_peaks = tab 


    @staticmethod
    def check_array(Tab : np.array, N_expected : int) :
        """
        Fonction qui checke si Tab est un array, de N éléments, entiers ou flottants. 
        Raises : 
        - TypeError : Si Tab n'est pas un array ou bien si l'un de ses éléments n'est pas un nombre (float ou int) 
        - Dimension_not_respected : Si Tab n'est pas de taille self.N. 
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
                    date_heure : datetime = None,   #date à mettre dans le contexte. 
                    solar_productions : np.ndarray = None,                #un DF normalisé selon date/heure, pas, N. 
                    horizon : int = 24,             #l'horizon en heures.  
                    pas_temps : int = 15            #Pas de temps en minutes. 
                    ) :
        """Fonction qui extrait les data depuis un client."""
        if not isinstance(horizon,(int)) :
            raise TypeError("L'horizon doit être un entier.") 
        if horizon < 0 or horizon > 100 :
            raise TypeError("L'horizon doit être positif et ne doit pas dépasser 100 heures.") 
        if not isinstance(pas_temps,(int)) :
            raise TypeError("Le pas doit être un entier.") 
        if pas_temps < 0 or pas_temps > (horizon*60)/2 :
            raise TypeError("Le pas doit être positif et ne doit pas dépasser un demi de l'horizon") 

        N = int((horizon*60)/pas_temps)  
        if not isinstance(date_heure,datetime) :
            raise TypeError(f"{date_heure} n'est pas un objet de type datetime.") 
        if not isinstance(client, Client) :
            raise TypeError(f"{client} n'est pas un objet de type Client") 
        
        if solar_productions is not None :
            cls.check_array(solar_productions,N) 
        
        ####Maintenant, on commence les extractions. 
        #1 : prices purchases : 
        prices = np.zeros(N) 

        #2 : prices_sell : 
        prix_revente = client.prix.revente 
        prices_sell = np.full(N, prix_revente) 

        #3 : house consumption : 
        planning = client.contraintes.planning_consommation
        h_cons = planning.get_vector(date_heure, N, pas_temps)  
        
        #4 : water draws / future consignes : 
        # A. Initialisation
        w_draws = np.zeros(N)
        f_consignes = np.full(N, client.contraintes.temperature_minimale)
        
        # B. Appel de la fonction recuperer_consignes_futures (on récupère la liste triée et filtrée)
        # On passe le jour et l'heure du début de la simulation
        events_list = client.planning.recuperer_consignes_futures(
            jour_actuel=date_heure.weekday(), # 0=Lundi
            heure_actuelle=date_heure.time(),
            horizon_heures=horizon
        )
        #eventslist est une liste qui contient les poinconsignes triés commençant par date_heure et allant jusqu'à date_heure+horizon. 
        # C. Mapping "Push" : On place les événements dans les cases du vecteur
        minutes_semaine = 7 * 24 * 60 # Constante pour gérer le modulo semaine
        
        # On calcule le "temps absolu" du début de la simu en minutes depuis le début de la semaine
        # (Pour pouvoir comparer avec les consignes)
        t_start_week = date_heure.weekday() * 1440 + date_heure.hour * 60 + date_heure.minute
        
        for evt in events_list:
            # 1. Temps de l'événement en minutes depuis début de semaine (Lundi 00:00)
            t_evt_week = evt.day * 1440 + evt.moment.hour * 60 + evt.moment.minute
            
            # 2. Calcul du Delta (Combien de minutes entre le début simu et l'événement ?)
            delta_minutes = t_evt_week - t_start_week
            
            # Si négatif, c'est que l'événement est la semaine prochaine (bouclage)
            # Votre fonction 'recuperer_consignes_futures' ne renvoyant que du futur, 
            # si c'est "avant" dans la semaine, c'est forcément "après" temporellement.
            if delta_minutes < 0:
                delta_minutes += minutes_semaine
                
            # 3. Calcul de l'index (Le fameux "Bucket")
            # Ex: delta=12min, pas=15min -> index=0. (Ça tombe bien dans le premier quart d'heure)
            idx = int(delta_minutes / pas_temps)
            
            # 4. Remplissage (Sécurité bornes)
            if 0 <= idx < N:
                # On cumule les volumes (si 2 douches dans le même quart d'heure)
                w_draws[idx] += evt.volume_tire
                
                # On prend la température la plus exigeante (f_consignes contient déjà la t_minimale) 
                f_consignes[idx] = max(f_consignes[idx], evt.temperature) 
        
        #5. availability :
        tab_availability = np.zeros(N) 

        for i in range(N):
            #Le temps à i est dt_i = date_actuelle + i*pas_temps. 
            dt_i = date_heure + timedelta(minutes=i * pas_temps)
            t_i = dt_i.time() 
            a = client.prix.get_prix_achat_actuel(t_i) 
            prices[i] = a 

            #On checke si dti = date_heure + i*pas tombe dans true ou bien false. 
            autorise = client.contraintes.est_autorise(t_i) 
            if autorise :
                tab_availability[i] = 1 
        #6. Construction de off_peak_hours : 
        # Par défaut, on initialise à 1 (Le courant passe partout, correspond au mode BASE)
        off_peak_hours = np.ones(N) 
        
        # Si on est en HPHC, on vient "sculpter" les trous (les 0) correspondant aux Heures Pleines
        if client.prix.mode == "HPHC":
            creneaux_hp = client.prix.creneaux_hp
            for i in range(N):
                dt_i = date_heure + timedelta(minutes=i * pas_temps)
                t_i = dt_i.time()
                
                # Vérification si l'instant t est dans un créneau HP
                est_hp = any(c.debut <= t_i < c.fin for c in creneaux_hp)
                
                if est_hp:
                    off_peak_hours[i] = 0 # Le contacteur est ouvert (coupure)

        A = cls(N,
                pas_temps, 
                date_heure, 
                prices, 
                prices_sell, 
                solar_productions, 
                h_cons, 
                w_draws, 
                f_consignes,
                tab_availability,
                off_peak_hours) 
        
        return A 