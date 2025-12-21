"""Le but de fichier est de regrouper la classe ClientManager qui est une partie de l'API. 
Auteur : @anaselb 

"""

import sys
from pathlib import Path

chemin_base = Path(__file__).parent.parent
sys.path.append(str(chemin_base / 'client_models'))

from client_models import Client, Features, Planning, Constraints, Prices, WaterHeater 
from base_db import Database
import sqlite3
import os
from datetime import datetime


class ClientManager :
    def __init__(self, path_db) :
        self.path_db = path_db
        self.db = Database(path_db)

    def create_client_in_db(self, client : Client) -> None :
        """Fonction pour ajouter les données d'un client dans la BDD. 
        Args : 
        -client : Objet du type Client (voir models) 
        Returns : 
        - None (Rien car seulement écriture dans la BDD). 
        Raises : 
        - ConnectionError si accès impossible à la DB. 
        - ValueError : Si entrées non respectés. 
        """
        #TODO : Le but est : prendre le client et mettre ses données dans la BDD. 

        # Connection avec le BDD
        try:
            self.db.connect_db()
            print(f"Connecté à la base de données: {self.path_db}")

            # Table 'clients'
            self.db.create_table_clients()
            donnees_client = (client.client_id, client.features.gradation(), client.features.mode()) 
            try:
                self.db.connexion.execute("""
                    INSERT OR IGNORE INTO clients 
                    (client_id, gradation, mode) 
                    VALUES (?, ?, ?)
                """, donnees_client)
            except sqlite3.IntegrityError as e:
                self.db.connexion.rollback() # Efacez TOUT depuis le début.
                self.db.close_db()
                raise ValueError(
                    f"ID du client déjà existe.\n"
                    f"Interruption complète de l'insertion.\n"
                    f"Erreur SQLite: {e}"
                ) from e

            # Table 'consignes'
            self.db.create_table_consignes()
            if client.planning:
                list_consignes = client.planning.consignes()
                for consigne in list_consignes:
                    donnees_client = (client.client_id, consigne.day(), consigne.moment(), 
                                      consigne.temperature(), consigne.volume()) 
                    try:
                        self.db.connexion.execute("""
                        INSERT OR IGNORE INTO consignes 
                        (client_id, day, moment, temperature, volume) 
                        VALUES (?, ?, ?, ?, ?)
                    """, donnees_client)
                    except sqlite3.IntegrityError as e:
                        self.db.connexion.rollback() # Efacez TOUT depuis le début.
                        self.db.close_db()
                        raise ValueError(
                            f"Valeur invalide envoyée dans le planning.\n"
                            f"Interruption complète de l'insertion.\n"
                            f"Erreur SQLite: {e}"
                        ) from e
                    
            # Table 'constraints'
            self.db.create_table_constraints()
            if client.contraintes:
                donnees_client = (client.client_id, client.contraintes.temperature_minimale(), 
                                  client.contraintes.puissance_maison())
                try:
                    self.db.connexion.execute("""
                    INSERT OR IGNORE INTO constraints 
                    (client_id, temperature_minimale, puissance_maison) 
                    VALUES (?, ?, ?)
                """, donnees_client)
                    contraint_id = self.db.connexion.lastrowid

            # Table 'plages_interdites'
                    self.db.create_table_plages_interdites()
                    list_plages_interdites = client.contraintes.plages_interdites()
                    for plage_interdite in list_plages_interdites:
                        donnees_client = (contraint_id, plage_interdite.debut, plage_interdite.fin)
                        try:
                            self.db.connexion.execute("""
                            INSERT OR IGNORE INTO plages_interdites
                            (client_id, day, moment, temperature, volume) 
                            VALUES (?, ?, ?, ?, ?)
                        """, donnees_client)
                        except sqlite3.IntegrityError as e:
                            self.db.connexion.rollback() # Efacez TOUT depuis le début.
                            self.db.close_db()
                            raise ValueError(
                                f"Valeur invalide envoyée dans les plages interdites.\n"
                                f"Interruption complète de l'insertion.\n"
                                f"Erreur SQLite: {e}"
                            ) from e
                except sqlite3.IntegrityError as e:
                    self.db.connexion.rollback() # Efacez TOUT depuis le début.
                    self.db.close_db()
                    raise ValueError(
                        f"Valeur invalide envoyée dans les contraintes.\n"
                        f"Interruption complète de l'insertion.\n"
                        f"Erreur SQLite: {e}"
                    ) from e
                
            # Table 'prices'
            self.db.create_table_prices()
            if client.prix:
                if client.prix.mode() == 'BASE':
                    donnees_client = [(client.client_id, 'base', client.prix.base()),
                                        (client.client_id, 'revente', client.prix.revente())]
                    try:
                        self.db.connexion.executemany("""
                            INSERT OR IGNORE INTO prices 
                            (client_id, type, prix) 
                            VALUES (?, ?, ?)
                        """, donnees_client)
                    except sqlite3.IntegrityError as e:
                        self.db.connexion.rollback() # Efacez TOUT depuis le début.
                        self.db.close_db()
                        raise ValueError(
                            f"Valeur invalide envoyée dans les prix.\n"
                            f"Interruption complète de l'insertion.\n"
                            f"Erreur SQLite: {e}"
                        ) from e
                elif client.prix.mode() == 'HPHC':
                    donnees_client = [(client.client_id, 'hp', client.prix.hp()),
                                        (client.client_id, 'hc', client.prix.hc()),
                                        (client.client_id, 'revente', client.prix.revente())]
                    try:
                        self.db.connexion.executemany("""
                            INSERT OR IGNORE INTO prices 
                            (client_id, type, prix) 
                            VALUES (?, ?, ?)
                        """, donnees_client)

            # Table 'creneaux_hp'
                        self.db.create_table_creneaux_hp()
                        list_creneaux_hp = client.prix.creneaux_hp()
                        for creneau_hp in list_creneaux_hp:
                            donnees_client = (client.client_id, creneau_hp.debut, creneau_hp.fin)
                            try:
                                self.db.connexion.executemany("""
                                    INSERT OR IGNORE INTO prices 
                                    (client_id, heure_debut, heure_fin) 
                                    VALUES (?, ?, ?)
                                """, donnees_client)
                            except sqlite3.IntegrityError as e:
                                self.db.connexion.rollback() # Efacez TOUT depuis le début.
                                self.db.close_db()
                                raise ValueError(
                                    f"Valeur invalide envoyée dans les creneaux_hp.\n"
                                    f"Interruption complète de l'insertion.\n"
                                    f"Erreur SQLite: {e}"
                                ) from e

                    except sqlite3.IntegrityError as e:
                        self.db.connexion.rollback() # Efacez TOUT depuis le début.
                        self.db.close_db()
                        raise ValueError(
                            f"Valeur invalide envoyée dans les prix.\n"
                            f"Interruption complète de l'insertion.\n"
                            f"Erreur SQLite: {e}"
                        ) from e
                else:
                    self.db.connexion.rollback() # Efacez TOUT depuis le début.
                    self.db.close_db()
                    raise ValueError(
                        f"Mode invalide dans les prix.\n"
                        f"Interruption complète de l'insertion.\n"
                    )

            # Table 'water_heaters'
            if client.chauffe_eau:
                self.db.create_table_water_heaters()
                donnees_client = (client.client_id, client.chauffe_eau.volume(), 
                                client.chauffe_eau.power(), client.chauffe_eau.coefficient_isolation(), 
                                client.chauffe_eau.temperature_eau_froide())
                try:
                    self.db.connexion.execute("""
                        INSERT OR IGNORE INTO water_heaters
                        (client_id, volume, power, coeff_isolation, temperature_eau_froide_celsius) 
                        VALUES (?, ?, ?, ?, ?)
                    """, donnees_client)
                except sqlite3.IntegrityError as e:
                    self.db.connexion.rollback() # Efacez TOUT depuis le début.
                    self.db.close_db()
                    raise ValueError(
                        f"Valeur invalide envoyée dans les water_heaters.\n"
                        f"Interruption complète de l'insertion.\n"
                        f"Erreur SQLite: {e}"
                    ) from e

            self.db.connexion.commit() # Sauvegarder en disque

        except sqlite3.Error as e:
            raise ConnectionError(
                f"Impossible de se connecter à la base de données.\n"
                f"Chemin: {self.path_db}\n"
                f"Erreur SQLite: {e}"
            ) from e
        finally:
            self.db.close_db()
        

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



















