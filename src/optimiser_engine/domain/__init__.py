from .client import Client 
from .constraints import Constraints 
from .consignes_models import Planning, PointConsign
from .features_models import Features 
from .prices_model import Prices
from .water_heater_model import WaterHeater
from .common import Creneau 

"""
Ce package contient les programmes nécessaires pour définir la structure de données d'un client. 
Le fichier client.py est le fichier principal qui implémente la classe Client. 
Un client est défini par : 
- Un planning : instance d'une classe Planning définie dans consignes_models.py 
- Des contraintes : instance d'une classe Constraints définie dans constraints.py 
- des fonctionnalités : Instance d'une classe Features définie dans features_models.py 
- des prix : Instance d'une classe Prices définie dans prices_models.py 
- un chauffe_eau : Instance de WaterHeater définie dans water_heater_model.py 
Le fichier common.py contient une classe Creneau qui définit les créneaux. 

"""