from consignes_models import Planning
from constraints import Constraints 
from features_models import Features
from prices_model import Prices
from water_heater_model import WaterHeater 


class Client :
    def __init__(self, 
                 planning : Planning, 
                 contraintes : Constraints, 
                 features : Features, 
                 prix : Prices, 
                 chauffe_eau : WaterHeater, 
                 client_id = 0) :
        self.client_id = client_id 
        self.planning = planning  
        self.contraintes = contraintes 
        self.features = features
        self.prix = prix
        self.chauffe_eau = chauffe_eau 
    def __repr__(self) :
        return f"client : {self.client_id}" 
