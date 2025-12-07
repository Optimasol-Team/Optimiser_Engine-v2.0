"""Le but de fichier est de regrouper la classe ClientManager qui est une partie de l'API. 
Auteur : @anaselb 

"""

from ..models import Client, Features, Planning, Constraints, Prices, WaterHeater 
from pathlib import Path 


class ClientManager :
    def __init__(self, path_db) :
        self.path_db = path_db 

    def create_client_in_db(self, client : Client) -> None :
        """Fonction pour ajouter les données d'un client dans la BDD. 
        Args : 
        -client : Objet du type Client (voir models) 
        Returns : 
        - None (Rien car seulement écriture dans la BDD). 
        Raises : 
        - DataBaseError si accès impossible à la DB. 
        - ValueError : Si entrées non respectés. 
        """
        #TODO : Le but est : prendre le client et mettre ses données dans la BDD. 
        pass 

    def reconstitute_client(self, client_id : int = 0) -> Client :
        """Fonction pour reconstituer un client à partir de son ID. 
        Args : 
        - client_id : int (un entier unique représentant le client dans la BDD) 
        Returns : 
        - client : Objet de type Client reconstitué (voir models) 
        Raises : 
        - DataBaseError : Si accès impossible à la base de données 
        - ClientNotFound : Si aucun client n'a l'ID client_id 
        - ValueError : Si entrées non conformes. 
        """
        #TODO : Prend le client_id et renvoie le client qui porte ce id. 
        #La fonction va aller chercher dans la BDD pour reconstituer les éléments concrets du client. 
        pass 
    
    def delete_client(self, client_id : int) :
        """Fonction qui supprime le client de la BDD. 
        Args : 
        - client_id : entier représentant l'ID du client 
        Returns : 
        - None : Rien sauf suppression dans la BDD. 
        Raises : 
        - ValueError : Si l'entrée n'est pas conforme. 
        - DataBaseError : Si l'accès à la BDD est impossible 
        - ClientNotFound : Si le client n'existe pas dans la base de données. """ 
        #TODO : Cette fonction supprime le client de la BDD. 
        pass

    def update_client_in_db(self, client : Client, 
                      planning : Planning = None, 
                      features : Features = None, 
                      contraintes : Constraints = None, 
                      prix : Prices = None, 
                      chauffe_eau : WaterHeater = None
                      ) :
        """Fonction qui met à jour le client dans la BDD. 
        Args : 
        - client : Objet de type Client (voir models)
        - planning : Objet de type Planning (voir models), optionnel
        - features : Objet de type Features (voir models), optionnel
        - contraintes : Objet de type Constraints (voir models), optionnel
        - prix : Objet de type Prices (voir models), optionnel
        - chauffe_eau : Objet de type WaterHeater (voir models), optionnel 
        La fonction met à jour uniquement les éléments qui ne sont pas des None.
        Returns :
        - None : Rien sauf mise à jour dans la BDD. 
        Raises :
        - ValueError : Si les entrées ne sont pas conformes.
        - DataBaseError : Si l'accès à la BDD est impossible.
        - ClientNotFound : Si le client n'existe pas dans la base de données."""
        #Todo : Cette fonction, prend en argument les éléments qui sont pas des None et met à jour le client dans la BDD. 
        pass 
        #Cette fonction est super intéressante pour le module de gestionnaire d'habitudes qui met à jour constamment le planning. 
    def list_all_clients(self) -> list :
        """Fonction qui liste tous les clients dans la BDD. 
        Args : 
        - Rien 
        Returns : 
        - liste_clients : liste d'objets de type int (les clients_id)  
        Raises : 
        - DataBaseError : Si l'accès à la BDD est impossible. 
        """
        #TODO : Le but est de retourner la liste de tous les clients dans la BDD. 
        pass



















