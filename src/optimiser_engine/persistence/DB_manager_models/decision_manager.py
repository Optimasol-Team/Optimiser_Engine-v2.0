"""Le but de ce fichier est de contenir la classe DecisionsManager qui gère les décisions pour un client donné.
Auteur : @laura-campelo""" 

from ...domain import Client, Features, Planning, Constraints, Prices, WaterHeater
from pathlib import Path
import pandas as pd 
from datetime import time, datetime
from .base_db import Database
from .exceptions_db import *
import sqlite3

class DecisionsManager :
    def __init__(self, path_db) :
        self.path_db = path_db
        self.db = Database(path_db)

    def create_decision_in_db(self, client_id : int, date : datetime, puissance : float) -> None:
        """Fonction pour ajouter les données d'une décision dans la BDD. 
        Args : 
        - client_id : int (un entier unique représentant le client dans la BDD)
        - date : datetime (la date de la décision)
        - puissance : float (un float représentant la puissance utilisé dans un instant)
        Returns : 
        - None (Rien car seulement écriture dans la BDD). 
        Raises : 
        - DatabaseConnexionError : si accès impossible à la BDD. 
        - ValueError : si entrées non respectés. 
        - ClientNotFound : Si aucun client n'a l'ID client_id.
        """
        # Test de type de l'ID du client
        if not isinstance(client_id, int):
            raise ValueError("L'ID du client doit être un doit être un nombre entier.")

        # Connection avec le BDD
        try:
            self.db.connect_db()        
        except DatabaseConnexionError:
            raise DatabaseConnexionError(
                f"Impossible de se connecter à la base de données.\n"
                f"Chemin: {self.path_db}\n"
            )         

        print(f"Connecté à la base de données: {self.path_db}")
            
        # Configurer pour retourner des dictionnaires
        self.db.connexion.row_factory = sqlite3.Row
        
        # Créer un curseur pour exécuter les requêtes
        curseur = self.db.connexion.cursor()
        
        self.db.create_table_decisions()
        donnees_client = (client_id, date.isoformat(), puissance) 
        try:
            curseur.execute("""
                INSERT INTO decisions 
                (client_id, date, puissance) 
                VALUES (?, ?, ?)
            """, donnees_client)
        except DatabaseIntegrityError:
            self.db.connexion.rollback() # Efacez TOUT depuis le début.
            curseur.close()
            self.db.close_db()
            raise ValueError(
                f"Valeur invalide envoyée dans la décision.\n"
                f"Interruption complète de l'insertion.\n"
            )
        
        self.db.connexion.commit() # Sauvegarder en disque
        curseur.close()
        self.db.close_db()

    def reconstitute_all_decisions(self, client_id : int) :
        """Fonction pour reconstituer toutes les decisions à partir de l'ID du client en ordre cronologique. 
        Args : 
        - client_id : int (un entier unique représentant le client dans la BDD) 
        Returns : 
        - decision : une liste du type [client_id, date, puissance] 
        Raises : 
        - DatabaseConnexionError : Si accès impossible à la base de données 
        - ClientNotFound : Si aucun client n'a l'ID client_id 
        - ValueError : Si l'entrée n'est pas conforme.
        """

        # Test de type de l'ID du client
        if not isinstance(client_id, int):
            raise ValueError("L'ID du client doit être un doit être un nombre entier.")

        # Connection avec le BDD
        try:
            self.db.connect_db()        
        except DatabaseConnexionError:
            raise DatabaseConnexionError(
                f"Impossible de se connecter à la base de données.\n"
                f"Chemin: {self.path_db}\n"
            )         

        print(f"Connecté à la base de données: {self.path_db}")
            
        # Configurer pour retourner des dictionnaires
        self.db.connexion.row_factory = sqlite3.Row
        
        # Créer un curseur pour exécuter les requêtes
        curseur = self.db.connexion.cursor()
        
        curseur.execute("SELECT date, puissance FROM decisions WHERE client_id=?", (client_id,))
        
        # Récupérer tous les résultats
        enregistrements = curseur.fetchall()
        
        if not enregistrements:
            curseur.close()
            self.db.close_db()
            raise ClientNotFound(f"Aucun client avec l'ID {client_id}\n")
        else:
            # Convertir en liste de dictionnaires
            decisions = []
            for ligne in enregistrements:
                decisions.append(dict(ligne))  # Convertit Row en dictionnaire
            for dec in decisions:
                dec["date"] = datetime.fromisoformat(dec["date"])
            decisions_ordonnees = sorted(decisions, key=lambda d: d["date"])
            curseur.close()
            self.db.close_db()
            return decisions_ordonnees

    def reconstitute_decisions(self, client_id : int, date_debut : datetime, date_fin : datetime):
        """Fonction pour reconstituer une serie de decisions entre date_debut et date_fin d'un client_id. 
        Args : 
        - client_id : int (un entier unique représentant le client dans la BDD) 
        - date_debut : datetime (date de début des consultations)
        - date_fin : datetime (date de fin des consultations)
        Returns : 
        - decisions : une liste de dictionaires du type {'client_id' = int, 'date' = datetime, 'puissance' = float} 
        Raises : 
        - DatabaseConnexionError : Si accès impossible à la base de données 
        - ClientNotFound : Si aucun client n'a l'ID client_id 
        - ValueError : Si l'entrée n'est pas conforme.
        - DecisionNotFoun : Si n'existe pas une décision dans la période desirée.
        """

        # Test de type de l'ID du client
        if not isinstance(client_id, int):
            raise ValueError("L'ID du client doit être un doit être un nombre entier.")

        # Validation de dates
        if date_debut > date_fin:
            raise ValueError("Dates invalides pour retrouver les decisions")

        # Trouver toutes les décisions de ce client
        try:
            decisions_ordonnees = self.reconstitute_all_decisions(client_id=client_id)
        except DatabaseConnexionError:
            raise
        except ClientNotFound:
            raise
        except ValueError:
            raise

        debut = -1
        fin = -1
        for d in decisions_ordonnees:
            if d["date"] < date_debut:
                debut += 1
            elif d["date"] < date_fin:
                fin += 1
            else:
                break
        
        if fin > -1:
            if debut > -1:
                return decisions_ordonnees[debut:fin]
            else:
                return decisions_ordonnees[:fin]
        else:
            raise DecisionNotFound("Période sans aucune décision.")         

    def delete_decision(self, client_id : int, date : datetime) :
        """Fonction qui supprime une decision de la BDD. 
        Args : 
        - client_id : entier représentant l'ID du client 
        - date : datetime (la date de la décision)
        Returns : 
        - None : Rien sauf suppression dans la BDD. 
        Raises : 
        - ValueError : Si l'entrée n'est pas conforme. 
        - DatabaseConnexionError : Si l'accès à la BDD est impossible 
        - ClientNotFound : Si le client n'existe pas dans la base de données. """ 

        # Test de type de l'ID du client
        if not isinstance(client_id, int):
            raise ValueError("L'ID du client doit être un doit être un nombre entier.")

        # Connection avec le BDD
        try:
            self.db.connect_db()        
        except DatabaseConnexionError:
            raise DatabaseConnexionError(
                f"Impossible de se connecter à la base de données.\n"
                f"Chemin: {self.path_db}\n"
            )         

        print(f"Connecté à la base de données: {self.path_db}")
            
        # Configurer pour retourner des dictionnaires
        self.db.connexion.row_factory = sqlite3.Row
        
        # Créer un curseur pour exécuter le requête
        curseur = self.db.connexion.cursor()

        curseur.execute("DELETE FROM decisions WHERE client_id = ? and date = ?", (client_id, date,))
        
        # Récupérer tous les résultats
        lignes_concernees = curseur.rowcount()

        self.db.connexion.commit() # Sauvegarder en disque
        curseur.close()
        self.db.close_db()
        
        if not lignes_concernees:
            raise ClientNotFound(f"Aucun client avec l'ID {client_id}\n")

    def update_decisions_in_db(self, client_id : int, date : datetime, puissance : float) -> None :
        """Fonction pour mêttre à jour les données d'une décision dans la BDD. 
        Args : 
        - client_id : int (un entier unique représentant le client dans la BDD)
        - date : datetime (la date de la décision)
        - puissance : float (un float représentant la puissance utilisé dans un instant)
        Returns : 
        - None (Rien car seulement écriture dans la BDD). 
        Raises : 
        - DatabaseConnexionError : si accès impossible à la BDD. 
        - ValueError : si entrées non respectés. 
        - ClientNotFound : Si aucun client n'a l'ID client_id.
        """
        # Test de type de l'ID du client
        if not isinstance(client_id, int):
            raise ValueError("L'ID du client doit être un doit être un nombre entier.")

        # Connection avec le BDD
        try:
            self.db.connect_db()        
        except DatabaseConnexionError:
            raise DatabaseConnexionError(
                f"Impossible de se connecter à la base de données.\n"
                f"Chemin: {self.path_db}\n"
            )         

        print(f"Connecté à la base de données: {self.path_db}")
            
        # Configurer pour retourner des dictionnaires
        self.db.connexion.row_factory = sqlite3.Row
        
        # Créer un curseur pour exécuter les requêtes
        curseur = self.db.connexion.cursor()
        
        self.db.create_table_decisions()
        donnees_client = (puissance, client_id, date.isoformat()) 
        try:
            curseur.execute("""
                UPDATE decisions 
                SET puissance ? 
                WHERE client_id = ? and date = ?
            """, donnees_client)
        except DatabaseIntegrityError:
            curseur.close()
            self.db.close_db()
            raise ValueError(
                f"Valeur invalide envoyée dans la décision.\n"
                f"Interruption complète du changement.\n"
            )
        
        # Récupérer tous les résultats
        lignes_concernees = curseur.rowcount()

        self.db.connexion.commit() # Sauvegarder en disque
        curseur.close()
        self.db.close_db()
        
        if not lignes_concernees:
            raise ClientNotFound(f"Aucun client avec l'ID {client_id}\n")
