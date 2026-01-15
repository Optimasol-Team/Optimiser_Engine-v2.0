"""Le but de ce fichier est de regrouper la classe DBManager qui hérite à la fois de ClientManager et DecisionsManager.
Auteur : @laura-campelo

"""

from .decision_manager import DecisionsManager
from .client_manager import ClientManager 

class DBManager(DecisionsManager, ClientManager) :
    def __init__(self, path_db) :
        self.path_db = path_db 
        DecisionsManager.__init__(self, path_db)
        ClientManager.__init__(self, path_db)

    # TODO: Finir l'implementation
