import sqlite3
import os
from datetime import datetime
from ...exceptions import *

class Database:
    def __init__(self, chemin_db=None):
        """
        Initialise la classe Database
        
        Args :
            chemin_db (str): Chemin complet du fichier de base de données SQLite
                            Si None, utilise le chemin par défaut dans le répertoire courant

        Raises :
        - DatabaseConnexionError : si accès impossible à la DB.
        - DatabaseIntegrityError : si entrées non respectés.
        """
        if chemin_db is None:
            # Chemin par défaut dans le répertoire courant
            self.chemin_db = os.path.join(os.getcwd(), 'db_engine_sqlite.db')
        else:
            # Utiliser le chemin fourni
            self.chemin_db = chemin_db
        
        # S'assurer que le chemin est absolu
        if not os.path.isabs(self.chemin_db):
            self.chemin_db = os.path.join(os.getcwd(), self.chemin_db)
        
        # Extraire le nom du fichier pour les affichages
        self.nom_fichier = os.path.basename(self.chemin_db)
        self.dossier_parent = os.path.dirname(self.chemin_db)
        
        self.connexion = None
        
        # Créer le dossier parent si nécessaire
        if self.dossier_parent and not os.path.exists(self.dossier_parent):
            os.makedirs(self.dossier_parent)
            print(f"Dossier créé: {self.dossier_parent}")
    
    def obtenir_info_db(self):
        """Retourne des informations sur la base de données"""
        return {
            'chemin_complet': self.chemin_db,
            'nom_fichier': self.nom_fichier,
            'dossier_parent': self.dossier_parent,
            'existe': os.path.exists(self.chemin_db),
            'taille_octets': os.path.getsize(self.chemin_db) if os.path.exists(self.chemin_db) else 0,
            'taille_mb': os.path.getsize(self.chemin_db) / (1024 * 1024) if os.path.exists(self.chemin_db) else 0
        }
    
    def connect_db(self):
        """Établir une connexion à la base de données SQLite"""
        try:
            self.connexion = sqlite3.connect(self.chemin_db)
        except sqlite3.OperationalError:
            raise DatabaseConnexionError("Impossible de se connecter à la base de données.")
        self.connexion.execute("PRAGMA foreign_keys = ON")  # Activer les clés étrangères
        print(f"Connecté à la base de données: {self.chemin_db}")
        return True
        
    def close_db(self):
        """Fermer la connexion à la base de données"""
        if self.connexion:
            try:
                self.connexion.close()
            except sqlite3.ProgrammingError:
                print("Connexion déjà fermée")
            except sqlite3.OperationalError:
                raise DatabaseConnexionError("Erreur lors de la déconnexion de la base de données.")
            print("Connexion fermée")

    def create_table_clients(self):
        """Créer la table basée sur le fichier client_models/client.py et client_models/features_models.py"""
        sql = """
        CREATE TABLE IF NOT EXISTS clients (
            client_id INTEGER PRIMARY KEY AUTOINCREMENT,
            gradation INTEGER DEFAULT 0,
            mode TEXT DEFAULT 'AutoCons',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            CHECK (mode IN ('AutoCons', 'cost')),
            CHECK (gradation IN (0, 1))
        );
        """
        self.connexion.execute(sql)
        print("Table 'clients' créé")

    def create_table_constraints(self):
        """Créer la table basée sur le fichier client_models/constraints.py"""
        # CORRECTION : On remplace 'puissance_maison' (REAL) par 'profil_conso_json' (TEXT)
        sql = """
        CREATE TABLE IF NOT EXISTS constraints (
            constraint_id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            temperature_minimale REAL DEFAULT 10.0,
            profil_conso_json TEXT, 
            
            FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE,
            UNIQUE (client_id),
            CHECK (temperature_minimale > 0 AND temperature_minimale < 95),
        );
        """
        self.connexion.execute(sql)
        print("Table 'constraints' créé (Version JSON)")

    def create_table_plages_interdites(self):
        """Créer la table basée sur le fichier client_models/common.py"""
        sql = """
        CREATE TABLE IF NOT EXISTS plages_interdites (
            plage_interdite_id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            heure_debut TEXT NOT NULL,
            heure_fin TEXT NOT NULL,
            
            FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE,
            UNIQUE (client_id, heure_debut, heure_fin),
            CHECK (heure_debut < heure_fin)
        );
        """
        self.connexion.execute(sql)
        print("Table 'plages_interdites' créé")
    
    def create_table_water_heaters(self):
        """Créer la table basée sur le fichier client_models/water_heaters.py"""
        sql = """
        CREATE TABLE IF NOT EXISTS water_heaters (
            water_heater_id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            volume REAL NOT NULL,
            power REAL NOT NULL,
            coeff_isolation REAL DEFAULT 0.0,
            temperature_eau_froide_celsius REAL DEFAULT 10.0,
            
            FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE,
            UNIQUE (client_id),
            CHECK (volume > 0),
            CHECK (power > 0)
        );
        """
        self.connexion.execute(sql)
        print("Table 'water_heaters' créé")
    
    def create_table_consignes(self):
        """Créer la table basée sur le fichier client_models/consignes_models.py"""
        sql = """
        CREATE TABLE IF NOT EXISTS consignes (
            consigne_id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            day INTEGER NOT NULL,
            moment TEXT NOT NULL,
            temperature REAL,
            volume REAL DEFAULT 30.0,
            
            FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE,
            UNIQUE (client_id, day, moment),
            CHECK (day >= 0 AND day <= 6),
            CHECK (temperature >= 30 AND temperature <= 99),
            CHECK (volume > 0)            
        );
        """
        self.connexion.execute(sql)
        print("Table 'consignes' créé")
    
    def create_table_creneaux_hp(self):
        """Créer la table de creneaux_hp basée sur le fichier client_models/prices_model.py"""
        sql = """
        CREATE TABLE IF NOT EXISTS creneaux_hp (
            creneau_hp_id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            heure_debut TEXT NOT NULL,
            heure_fin TEXT NOT NULL,
            
            FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE,
            UNIQUE (client_id, heure_debut, heure_fin),
            CHECK (heure_debut < heure_fin)
        );
        """
        self.connexion.execute(sql)
        print("Table 'creneaux_hp' créé")
    
    def create_table_prices(self):
        """Créer la table prices de l'énergie basée sur le fichier client_models/prices_model.py"""
        sql = """
        CREATE TABLE IF NOT EXISTS prices (
            client_id INTEGER,
            type TEXT,
            prix REAL NOT NULL,

            PRIMARY KEY (client_id, type),
            FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE,
            CHECK (type IN ('base', 'hp', 'hc', 'revente')),
            CHECK (prix >= 0)
        );
        """
        self.connexion.execute(sql)
        print("Table 'prices' créé")
    
    def create_all_tables(self):
        """Créer le schéma de la base de données"""
        
        # 1. Table clients
        self.create_table_clients()
        
        # 2. Table constraints
        self.create_table_constraints()
        
        # 3. Table water_heaters
        self.create_table_water_heaters()
        
        # 4. Table consignes
        self.create_table_consignes()
        
        # 5. Table creneaux_hp
        self.create_table_creneaux_hp()
        
        # 6. Table prices
        self.create_table_prices()
        
        # 7. Table plages_interdites
        self.create_table_plages_interdites()
        
        # 8. Créer les index
        self.create_index()
        
        print("\nToutes les tables ont été créés avec succès!")
    
    def create_index(self):
        """Créer des index pour améliorer les performances"""
        
        index_liste = [            
            # Table constraints
            ("CREATE INDEX IF NOT EXISTS idx_constraints_client ON constraints(client_id)"),
            
            # Table water_heaters
            ("CREATE INDEX IF NOT EXISTS idx_water_heaters_client ON water_heaters(client_id)"),
            
            # Table consignes
            ("CREATE INDEX IF NOT EXISTS idx_consignes_client ON consignes(client_id)"),
            ("CREATE INDEX IF NOT EXISTS idx_consignes_day ON consignes(day)"),
            
            # Table plages_interdites
            ("CREATE INDEX IF NOT EXISTS idx_plages_constraint ON plages_interdites(constraint_id)"),

            # Table prices
            ("CREATE INDEX IF NOT EXISTS idx_prices_client ON prices(client_id)"),

            # Table creneaux_hp
            ("CREATE INDEX IF NOT EXISTS idx_creneaux_hp_client ON creneaux_hp(client_id)")
        ]
        
        for sql in index_liste:
            self.connexion.execute(sql)
        
        self.connexion.commit()
        print("Index créés")
    
    def verifier_structure(self):
        """Vérifier si toutes les tables ont été créés"""
        curseur = self.connexion.cursor()
        
        # Lister toutes les tables
        curseur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = curseur.fetchall()
        
        print(f"\nStructure de la base '{self.chemin_db}':")
        print("=" * 60)
        
        for table in tables:
            nom_table = table[0]
            curseur.execute(f"PRAGMA table_info({nom_table})")
            colonnes = curseur.fetchall()
            
            print(f"\nTable: {nom_table}")
            print("-" * 40)
            for colonne in colonnes:
                print(f"  {colonne[1]:20} {colonne[2]:10} {'PK' if colonne[5] else '':3}")
        
        # Compter les enregistrements
        print("\nStatistiques:")
        for table in tables:
            curseur.execute(f"SELECT COUNT(*) FROM {table[0]}")
            compte = curseur.fetchone()[0]
            print(f"  {table[0]:20}: {compte:4} enregistrements")
        
        print("=" * 60)