"""Le but de fichier est de regrouper la classe ClientManager qui est une partie de l'API. 
Auteur : @anaselb 

"""

import sys
from pathlib import Path

################LES IMPORTS AJOUTÉS : ###################################################################  
import sys
import json  # <--- AJOUTER CECI
import numpy as np # <--- AJOUTER CECI
from ...domain import Client, Features, Planning, Constraints, Prices, WaterHeater, Setpoint, TimeSlot, ConsumptionProfile
########################################################################################################

chemin_base = Path(__file__).parent.parent
sys.path.append(str(chemin_base / 'client_models'))
from .base_db import Database
import sqlite3
import os
from datetime import datetime
import copy


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

        # Connection avec le BDD
        try:
            self.db.connect_db()
            print(f"Connecté à la base de données: {self.path_db}")
            cursor = self.db.connexion.cursor()

            # Table 'clients'
            self.db.create_table_clients()
            donnees_client = (client.client_id, client.features.gradation(), client.features.mode()) 
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO clients 
                    (client_id, gradation, mode) 
                    VALUES (?, ?, ?)
                """, donnees_client)
            except sqlite3.IntegrityError as e:
                self.db.connexion.rollback() # Efacez TOUT depuis le début.
                cursor.close()
                self.db.close_db()
                raise ValueError(
                    f"ID du client déjà existe.\n"
                    f"Interruption complète de l'insertion.\n"
                    f"Erreur SQLite: {e}"
                ) from e

            # Table 'consignes'
            self.db.create_table_consignes()
            if client.planning:
                list_consignes = client.planning.setpoints
                for consigne in list_consignes:
                    donnees_client = (client.client_id, consigne.day, consigne.time, 
                                      consigne.temperature, consigne.drawn_volume) 
                    try:
                        cursor.execute("""
                        INSERT OR IGNORE INTO consignes 
                        (client_id, day, moment, temperature, volume) 
                        VALUES (?, ?, ?, ?, ?)
                    """, donnees_client)
                    except sqlite3.IntegrityError as e:
                        self.db.connexion.rollback() # Efacez TOUT depuis le début.
                        cursor.close()
                        self.db.close_db()
                        raise ValueError(
                            f"Valeur invalide envoyée dans le planning.\n"
                            f"Interruption complète de l'insertion.\n"
                            f"Erreur SQLite: {e}"
                        ) from e

            ################# BLOC DE CONSTRAINTS AJOUTÉ ######################## : 
            # Table 'constraints'
            self.db.create_table_constraints()
            contraint_id = None # Initialisation importante
            if client.constraints:
                # 1. On récupère la matrice numpy (le tableau de chiffres)
                matrice_numpy = client.constraints.consumption_profile.data
                
                # 2. On la transforme en texte JSON pour la BDD
                # .tolist() transforme le numpy array en liste Python standard
                profil_json = json.dumps(matrice_numpy.tolist())

                # 3. On prépare les données (Notez qu'on utilise profil_json au lieu de puissance)
                donnees_constraints = (client.client_id, 
                                     client.constraints.minimum_temperature, 
                                     profil_json)
                try:
                    # ATTENTION: J'ai changé le nom de la colonne dans la requête SQL ci-dessous
                    cursor.execute("""
                    INSERT OR IGNORE INTO constraints 
                    (client_id, temperature_minimale, profil_conso_json) 
                    VALUES (?, ?, ?)
                """, donnees_constraints)
                    
                    contraint_id = cursor.lastrowid
                


            #Ancienne table supprimée : ##################################################################
            # Table 'constraints'
            #
            # if client.contraintes:
                #donnees_client = (client.client_id, client.contraintes.temperature_minimale(), 
                                  #client.contraintes.puissance_maison())
                #try:
                   # cursor.execute("""
                    #INSERT OR IGNORE INTO constraints 
                    #(client_id, temperature_minimale, puissance_maison) 
                    #VALUES (?, ?, ?)
                #""", donnees_client)
                   # contraint_id = cursor.lastrowid() 
#############################################################################################################

            # Table 'plages_interdites'
                    self.db.create_table_plages_interdites()
                    list_plages_interdites = client.constraints.forbidden_slots
                    for plage_interdite in list_plages_interdites:
                        donnees_client = (contraint_id, plage_interdite.start, plage_interdite.end)
                        try:
                            cursor.execute("""
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
                    cursor.close()
                    self.db.close_db()
                    raise ValueError(
                        f"Valeur invalide envoyée dans les contraintes.\n"
                        f"Interruption complète de l'insertion.\n"
                        f"Erreur SQLite: {e}"
                    ) from e
                
            # Table 'prices'
            self.db.create_table_prices()
            if client.prices:
                if client.prices.mode == 'BASE':
                    donnees_client = [(client.client_id, 'base', client.prices.base),
                                        (client.client_id, 'revente', client.prices.resale_price)]
                    try:
                        cursor.executemany("""
                            INSERT OR IGNORE INTO prices 
                            (client_id, type, prix) 
                            VALUES (?, ?, ?)
                        """, donnees_client)
                    except sqlite3.IntegrityError as e:
                        self.db.connexion.rollback() # Efacez TOUT depuis le début.
                        cursor.close()
                        self.db.close_db()
                        raise ValueError(
                            f"Valeur invalide envoyée dans les prix.\n"
                            f"Interruption complète de l'insertion.\n"
                            f"Erreur SQLite: {e}"
                        ) from e
                elif client.prices.mode == 'HPHC':
                    donnees_client = [(client.client_id, 'hp', client.prices.hp),
                                        (client.client_id, 'hc', client.prices.hc),
                                        (client.client_id, 'revente', client.prices.resale_price)]
                    try:
                        cursor.executemany("""
                            INSERT OR IGNORE INTO prices 
                            (client_id, type, prix) 
                            VALUES (?, ?, ?)
                        """, donnees_client)

            # Table 'creneaux_hp'
                        self.db.create_table_creneaux_hp()
                        list_creneaux_hp = client.prices.hp_slots
                        for creneau_hp in list_creneaux_hp:
                            donnees_client = (client.client_id, creneau_hp.start, creneau_hp.end)
                            try:
                                cursor.executemany("""
                                    INSERT OR IGNORE INTO prices 
                                    (client_id, heure_debut, heure_fin) 
                                    VALUES (?, ?, ?)
                                """, donnees_client)
                            except sqlite3.IntegrityError as e:
                                self.db.connexion.rollback() # Efacez TOUT depuis le début.
                                cursor.close()
                                self.db.close_db()
                                raise ValueError(
                                    f"Valeur invalide envoyée dans les creneaux_hp.\n"
                                    f"Interruption complète de l'insertion.\n"
                                    f"Erreur SQLite: {e}"
                                ) from e

                    except sqlite3.IntegrityError as e:
                        self.db.connexion.rollback() # Efacez TOUT depuis le début.
                        cursor.close()
                        self.db.close_db()
                        raise ValueError(
                            f"Valeur invalide envoyée dans les prix.\n"
                            f"Interruption complète de l'insertion.\n"
                            f"Erreur SQLite: {e}"
                        ) from e
                else:
                    self.db.connexion.rollback() # Efacez TOUT depuis le début.
                    cursor.close()
                    self.db.close_db()
                    raise ValueError(
                        f"Mode invalide dans les prix.\n"
                        f"Interruption complète de l'insertion.\n"
                    )

            # Table 'water_heaters'
            if client.water_heater:
                self.db.create_table_water_heaters()
                donnees_client = (client.client_id, client.water_heater.volume, 
                                client.water_heater.power, client.water_heater.insulation_coefficient, 
                                client.water_heater.cold_water_temperature)
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO water_heaters
                        (client_id, volume, power, coeff_isolation, temperature_eau_froide_celsius) 
                        VALUES (?, ?, ?, ?, ?)
                    """, donnees_client)
                except sqlite3.IntegrityError as e:
                    self.db.connexion.rollback() # Efacez TOUT depuis le début.
                    cursor.close()
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
            cursor.close()
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

        # Connection avec le BDD
        try:
            self.db.connect_db()
            print(f"Connecté à la base de données: {self.path_db}")
            
            # Configurer pour retourner des dictionnaires
            self.db.connexion.row_factory = sqlite3.Row
            
            # Créer un curseur pour exécuter les requêtes
            curseur = self.db.connexion.cursor()
            
            ########################################################################
            #  Exécuter la requête SQL pour trouver les donnees de la table 'clients'
            ########################################################################
            curseur.execute("SELECT client_id, gradation, mode FROM clients WHERE client_id=?", (client_id,))
            
            # Récupérer tous les résultats
            enregistrements = curseur.fetchall()
            
            if not enregistrements:
                raise ValueError(f"Aucun client avec l'ID {client_id}\n")
            
            # Convertir en liste de dictionnaires
            resultats = []
            for ligne in enregistrements:
                resultats.append(dict(ligne))  # Convertit Row en dictionnaire
            donnes_client = resultats[0]

            ####################################################################################################
            #  Exécuter la requête SQL pour trouver les donnees de la table 'constraints' et 'plages_interdites'
            ####################################################################################################
            
            #BOLC AJOUTÉ : CONSTRAINTS : ##############################################################
            curseur.execute(
                """SELECT ct.temperature_minimale, ct.profil_conso_json, pi.heure_debut, pi.heure_fin
                FROM constraints ct LEFT JOIN plages_interdites pi ON pi.constraint_id = ct.constraint_id
                WHERE ct.client_id=?""", (client_id,)
                )
            #######################FIN DU BLOC#####################################################
            
            
            ################################ANCIEN BLOC : ###########################################
            #curseur.execute(
               # """SELECT ct.temperature_minimale, ct.puissance_maison, pi.heure_debut, pi.heure_fin
              #  FROM constraints ct LEFT JOIN plages_interdites pi ON pi.constraint_id = ct.constraint_id
              #  WHERE ct.client_id=?""", (client_id,)
              #  )
            ###########################################################################################@





            # Récupérer tous les résultats
            enregistrements = curseur.fetchall()
            
            if not enregistrements:
                list_donnes_constraints = None
            else:
                # Convertir en liste de dictionnaires
                resultats = []
                for ligne in enregistrements:
                    resultats.append(dict(ligne))  # Convertit Row en dictionnaire
                list_donnes_constraints = copy.deepcopy(resultats)

            ###############################################################################
            #  Exécuter la requête SQL pour trouver les donnees de la table 'water_heaters'
            ###############################################################################
            curseur.execute("""SELECT volume, power, coeff_isolation, temperature_eau_froide_celsius
                            FROM water_heaters
                            WHERE client_id=?""", (client_id,))
            
            # Récupérer tous les résultats
            enregistrements = curseur.fetchall()
            
            if not enregistrements:
                donnes_water_heaters = None
            else:
                # Convertir en liste de dictionnaires
                resultats = []
                for ligne in enregistrements:
                    resultats.append(dict(ligne))  # Convertit Row en dictionnaire
                donnes_water_heaters = resultats[0]

            ###########################################################################
            #  Exécuter la requête SQL pour trouver les donnees de la table 'consignes'
            ###########################################################################
            curseur.execute("""SELECT day, moment, temperature, volume
                            FROM consignes
                            WHERE client_id=?""", (client_id,))
            
            # Récupérer tous les résultats
            enregistrements = curseur.fetchall()
            
            if not enregistrements:
                list_donnes_consignes = None
            else:
                # Convertir en liste de dictionnaires
                resultats = []
                for ligne in enregistrements:
                    resultats.append(dict(ligne))  # Convertit Row en dictionnaire
                list_donnes_consignes = copy.deepcopy(resultats)

            ########################################################################
            #  Exécuter la requête SQL pour trouver les donnees de la table 'prices'
            ########################################################################
            curseur.execute(
                """SELECT type, prix
                FROM prices
                WHERE p.client_id=?""", (client_id,)
                )
            
            # Récupérer tous les résultats
            enregistrements = curseur.fetchall()
            
            if not enregistrements:
                list_donnes_prices = None
            else:
                # Convertir en liste de dictionnaires
                resultats = []
                for ligne in enregistrements:
                    resultats.append(dict(ligne))  # Convertit Row en dictionnaire
                list_donnes_prices = copy.deepcopy(resultats)

            #############################################################################
            #  Exécuter la requête SQL pour trouver les donnees de la table 'creneaux_hp'
            #############################################################################
            curseur.execute(
                """SELECT heure_debut, heure_fin
                FROM creneaux_hp
                WHERE p.client_id=?""", (client_id,)
                )
            
            # Récupérer tous les résultats
            enregistrements = curseur.fetchall()
            
            if not enregistrements:
                list_donnes_creneaux_hp = None
            else:
                # Convertir en liste de dictionnaires
                resultats = []
                for ligne in enregistrements:
                    resultats.append(dict(ligne))  # Convertit Row en dictionnaire
                list_donnes_creneaux_hp = copy.deepcopy(resultats)

            ##################
            #  Reconstruction
            ##################

            # Partie Planning
            planning_reconstruit = Planning()
            if list_donnes_consignes:
                list_setpoints = []
                for consigne in list_donnes_consignes:
                    list_setpoints.append(Setpoint(consigne['day'], consigne['moment'],
                                                   consigne['temperature'], consigne['volume']))
                planning_reconstruit.setpoints = list_setpoints

            #NOUVELLE PARTIE CONTRAINTES ###############################################################################
            #---------------------------------------------------------------------------------------------------------######
            # Partie Constraints (VERSION CORRIGÉE JSON)
            # Note: Assurez-vous d'avoir "from client_models import ProfilConsommation" en haut
            
            constraints_reconstruit = None
            
            if list_donnes_constraints:
                # 1. Gestion des Plages Interdites
                list_creneaux = []
                for constraint in list_donnes_constraints:
                    # Vérification de sécurité si les champs sont non-nuls
                    if constraint['heure_debut'] and constraint['heure_fin']:
                        # Conversion robuste str -> time
                        h_debut = constraint['heure_debut']
                        if isinstance(h_debut, str): 
                            h_debut = datetime.strptime(h_debut, '%H:%M:%S').time()
                            
                        h_fin = constraint['heure_fin']
                        if isinstance(h_fin, str): 
                            h_fin = datetime.strptime(h_fin, '%H:%M:%S').time()
                            
                        list_creneaux.append(TimeSlot(h_debut, h_fin))
                
                info_constraint = list_donnes_constraints[0]
                
                # 2. Gestion du Profil de Consommation (Lecture du JSON)
                json_text = info_constraint['profil_conso_json']
                
                if json_text:
                    # On transforme le texte JSON de la BDD en objet ProfilConsommation
                    data_list = json.loads(json_text)
                    matrice_numpy = np.array(data_list)
                    profil_objet = ConsumptionProfile(matrix_7x24=matrice_numpy)
                else:
                    profil_objet = ConsumptionProfile() # Profil par défaut si vide
                
                # 3. Création de l'objet final
                # L'ordre des arguments respecte maintenant votre constraints.py
                constraints_reconstruit = Constraints(
                    consumption_profile=profil_objet,
                    forbidden_slots=list_creneaux,
                    minimum_temperature=info_constraint['temperature_minimale']
                )
            else:
                # Si le client n'a aucune contrainte en BDD
                constraints_reconstruit = Constraints()





            # Partie Constraints - en commentaires (à supprimer) : 
            #if list_donnes_constraints:
              #  list_creneaux = []
               # for constraint in list_donnes_constraints:
                 #   list_creneaux.append(Creneau(constraint['heure_debut'], constraint['heure_fin']))
                #constraint = list_donnes_constraints[0]
                #constraints_reconstruit = Constraints(list_creneaux, constraint['temperature_minimale'],
                                                      #constraint['puissance_maison'])
           # else:
                #constraints_reconstruit = Constraints()

            # Partie Features
            if donnes_client['gradation'] == 1:
                features_reconstruit = Features(True, donnes_client['mode'])
            else:
                features_reconstruit = Features(False, donnes_client['mode'])
                    
            # Partie Prices
            prix_reconstruit = Prices()
            if list_donnes_prices:
                for price in list_donnes_prices:
                    if price['type'] == 'base':
                        prix_reconstruit.base = price['prix']
                    elif price['type'] == 'revente':
                        prix_reconstruit.resale_price = price['prix']
                prix_reconstruit.mode = 'HPHC'
                for price in list_donnes_prices:
                    if price['type'] == 'hp':
                        prix_reconstruit.hp = price['prix']
                    elif price['type'] == 'hc':
                        prix_reconstruit.hc = price['prix']
                list_creneaux_hp = []
                for creneau_hp in list_donnes_creneaux_hp:
                    list_creneaux_hp.append(TimeSlot(creneau_hp['heure_debut'], creneau_hp['heure_fin']))
                prix_reconstruit.hp_slots = list_creneaux_hp

            # Partie WaterHeater
            water_heater_reconstruit = WaterHeater(donnes_water_heaters['volume'],
                                                   donnes_water_heaters['power'])
            water_heater_reconstruit.insulation_coefficient = donnes_water_heaters['coeff_isolation']
            water_heater_reconstruit.cold_water_temperature = donnes_water_heaters['temperature_eau_froide_celsius']

                
            client_reconstruit = Client(
                planning=planning_reconstruit, 
                constraints=constraints_reconstruit, 
                features=features_reconstruit, 
                prices=prix_reconstruit, 
                water_heater=water_heater_reconstruit, 
                client_id=donnes_client['client_id']
            )
            
            return client_reconstruit
        
        except sqlite3.Error as e:
            raise ConnectionError(
                f"Impossible de se connecter à la base de données.\n"
                f"Chemin: {self.path_db}\n"
                f"Erreur SQLite: {e}"
            ) from e
        finally:
            curseur.close()
            self.db.close_db()
    
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

    def update_client_in_db(self, client : Client, 
                      planning : Planning = None, 
                      features : Features = None, 
                      constraints : Constraints = None, 
                      prices : Prices = None, 
                      water_heater : WaterHeater = None
                      ) :
        """Fonction qui met à jour le client dans la BDD. 
        Args : 
        - client : Objet de type Client (voir models)
        - planning : Objet de type Planning (voir models), optionnel
        - features : Objet de type Features (voir models), optionnel
        - constraints : Objet de type Constraints (voir models), optionnel
        - prices : Objet de type Prices (voir models), optionnel
        - water_heater : Objet de type WaterHeater (voir models), optionnel 
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













