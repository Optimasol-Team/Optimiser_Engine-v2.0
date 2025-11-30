"""Le but de ce fichier est de regrouper la classe Optimiser qui hérite à la fois de ClientManager et OptimiseManager.
Auteur : @anaselb 

"""

from .optimise_manager import OptimiseManager
from .client_manager import ClientManager 

class Optimiser(OptimiseManager, ClientManager) :
    def __init__(self, path_db) :
        self.path_db = path_db 
        OptimiseManager.__init__(self, path_db)
        ClientManager.__init__(self, path_db) 
