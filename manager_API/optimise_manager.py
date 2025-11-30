"""Le but de ce fichier est de contenir la classe OptimiseManager qui gère l'optimisation pour un client donné.
Auteur : @anaselb""" 

from ..models import Client, Features, Planning, Constraints, Prices, WaterHeater
from pathlib import Path
import pandas as pd 
from datetime import time 
class OptimiseManager :
    Horizon = 24 #en heures C'est lhorizon d'optimisation 
    pas = 15 #en minutes c'est la distance entre deux points successis (discrétisation)
    def __init__(self, path_db) :
        self.path_db = path_db 

    def decisions_of_client(self, client : Client, production_prevue : pd.DataFrame, T_initial : time = None) -> dict :
        """Fonction qui fournit les décisions optimales pour un client donné.
        Args : 
        - client : Objet du type Client (voir models) 
        - production_prevue : DataFrame pandas avec une colonne 'time' (type time) et une colonne 'production' (float) qui donne la production prévue d'énergie renouvelable à chaque instant.
        - T_initial : moment de la journée (type time) à partir duquel l'optimisation doit commencer. Si None, on part de maintenant.
        Returns : 
        - resultats : dict contenant les résultats de l'optimisation. Ce dict des dates <-> décisions. 
              Les dates commencent à partir de T_initial et s'étalent sur l'horizon défini (24h par défaut) avec un pas défini (15 minutes par défaut).
        Raises : 
        - OptimizationError : Si l'optimisation échoue pour une raison quelconque. 
        - ValueError : Si les entrées ne sont pas conformes. 

        """
        #TODO : Le but est de prendre le client, ses données et d'effectuer l'optimisation selon ses contraintes et préférences. 
        pass

    def update_decisions_in_db(self, client : Client, production_prevue : pd.DataFrame, T_initial : time = None) -> None :
        """Fonction qui met à jour les décisions optimales dans la BDD pour un client donné.  
          Args : 
          - client : Objet du type Client (voir models)
          - production_prevue : DataFrame pandas avec une colonne 'time' (type time) et une colonne 'production' (float) qui donne la production prévue d'énergie renouvelable à chaque instant.
          - T_initial : moment de la journée (type time) à partir duquel l'optimisation doit commencer. Si None, on part de maintenant.
          Returns :
          - None : Rien, sauf mise à jour dans la BDD.
          Raises :
          - OptimizationError : Si l'optimisation échoue pour une raison quelconque.
          - ValueError : Si les entrées ne sont pas conformes.
          - DataBaseError : Si l'accès à la BDD est impossible.
          - ClientNotFound : Si le client n'existe pas dans la base de données. 
          """