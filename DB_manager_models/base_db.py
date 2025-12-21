import sqlite3
import os
from datetime import datetime

class Database:
    def __init__(self, nom_db='/home/lacampelo/optimasol/Optimiser_Engine-v2.0/database/db_engine_sqlite.db'):
        """
        Initialise la classe Database
        
        Args:
            nom_db (str): Nom du fichier de base de données SQLite
        """
        self.nom_db = nom_db
        self.connexion = None
        
    def connect_db(self):
        """Établir une connexion à la base de données SQLite"""
        self.connexion = sqlite3.connect(self.nom_db)
        self.connexion.execute("PRAGMA foreign_keys = ON")  # Activer les clés étrangères
        print(f"Connecté à la base de données: {self.nom_db}")
        
    def close_db(self):
        """Fermer la connexion à la base de données"""
        if self.connexion:
            self.connexion.close()
            print("Connexion fermée")
    
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
        
        # 8. Insérer les données initiales
        self.insert_initial_data()
        
        # 9. Créer les index
        self.create_index()
        
        print("\nToutes les tables ont été créées avec succès!")
    
    def create_table_clients(self):
        """Créer la table basée sur le fichier client_models/client.py et client_models/features_models.py"""
        sql = """
        CREATE TABLE IF NOT EXISTS clients (
            client_id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT,
            email TEXT,
            latitude REAL,
            longitude REAL,
            tilt REAL,
            azimuth REAL,
            router_id TEXT,
            pwd TEXT,
            gradation INTEGER DEFAULT 0,
            mode TEXT DEFAULT 'AutoCons',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            CHECK (mode IN ('AutoCons', 'cost')),
            CHECK (gradation IN (0, 1))
        );
        """
        self.connexion.execute(sql)
        print("Table 'clients' créée")
    
    def create_table_constraints(self):
        """Créer la table basée sur le fichier client_models/constraints.py"""
        sql = """
        CREATE TABLE IF NOT EXISTS constraints (
            constraint_id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            temperature_minimale REAL DEFAULT 10.0,
            puissance_maison REAL DEFAULT 0.0,
            
            FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE
        );
        """
        self.connexion.execute(sql)
        print("Table 'constraints' créée")
    
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
            CHECK (volume > 0),
            CHECK (power > 0)
        );
        """
        self.connexion.execute(sql)
        print("Table 'water_heaters' créée")
    
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
        print("Table 'consignes' créée")
    
    def create_table_creneaux_hp(self):
        """Créer la table de creneaux_hp basée sur le fichier client_models/prices_model.py"""
        sql = """
        CREATE TABLE IF NOT EXISTS creneaux_hp (
            creneau_hp_id INTEGER PRIMARY KEY AUTOINCREMENT,
            heure_debut TEXT NOT NULL,
            heure_fin TEXT NOT NULL,
            
            UNIQUE (heure_debut, heure_fin),
            CHECK (heure_debut < heure_fin)
        );
        """
        self.connexion.execute(sql)
        print("Table 'creneaux_hp' créée")
    
    def create_table_prices(self):
        """Créer la table prices de l'énergie basée sur le fichier client_models/prices_model.py"""
        sql = """
        CREATE TABLE IF NOT EXISTS prices (
            type TEXT PRIMARY KEY,
            prix REAL NOT NULL,
            CHECK (type IN ('base', 'hp', 'hc', 'revente')),
            CHECK (prix >= 0)
        );
        """
        self.connexion.execute(sql)
        print("Table 'prices' créée")
    
    def create_table_plages_interdites(self):
        """Créer la table basée sur le fichier client_models/common.py"""
        sql = """
        CREATE TABLE IF NOT EXISTS plages_interdites (
            plage_interdite_id INTEGER PRIMARY KEY AUTOINCREMENT,
            constraint_id INTEGER,
            heure_debut TEXT NOT NULL,
            heure_fin TEXT NOT NULL,
            
            FOREIGN KEY (constraint_id) REFERENCES constraints(constraint_id) ON DELETE CASCADE,
            UNIQUE (constraint_id, heure_debut, heure_fin),
            CHECK (heure_debut < heure_fin)
        );
        """
        self.connexion.execute(sql)
        print("Table 'plages_interdites' créée")
    
    def insert_initial_data(self):
        """Insérer les données initiales"""
        
        # 1. Insérer le client admin (comme dans MySQL)
        donnees_admin = (1, 'Admin', '', 0.0, 0.0, 0.00, 0.00, '', 
                        '$2b$12$YUs0XL4wLsQk79JLhaJmLuvQZrIkzXdc7vjyZNDINpGFR4gxCUBMy')
        
        try:
            self.connexion.execute("""
                INSERT OR IGNORE INTO clients 
                (client_id, nom, email, latitude, longitude, tilt, azimuth, router_id, pwd) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, donnees_admin)
        except sqlite3.IntegrityError:
            # ID 1 existe déjà, utiliser AUTOINCREMENT
            donnees_admin = donnees_admin[1:]  # Retirer le client_id
            self.connexion.execute("""
                INSERT OR IGNORE INTO clients 
                (nom, email, latitude, longitude, tilt, azimuth, router_id, pwd) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, donnees_admin)
        
        # 2. Insérer les prix par défaut
        prix_base = [
            ('base', 0.18),    # Prix de base par kWh
            ('hp', 0.22),      # Heures de pointe
            ('hc', 0.15),      # Heures creuses
            ('revente', 0.10)  # Prix de revente
        ]
        
        self.connexion.executemany("""
            INSERT OR IGNORE INTO prices (type, prix) VALUES (?, ?)
        """, prix_base)
        
        # 3. Insérer les horaires de pointe par défaut (exemple: 06h-08h et 17h-19h)
        horaires_hp = [
            ('17:00:00', '19:00:00'),
            ('06:00:00', '18:00:00')
        ]
        
        self.connexion.executemany("""
            INSERT OR IGNORE INTO creneaux_hp (heure_debut, heure_fin) VALUES (?, ?)
        """, horaires_hp)
        
        self.connexion.commit()
        print("Données initiales insérées")
    
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
            ("CREATE INDEX IF NOT EXISTS idx_plages_constraint ON plages_interdites(constraint_id)")
        ]
        
        for sql in index_liste:
            self.connexion.execute(sql)
        
        print("Index créés")
    
    def verifier_structure(self):
        """Vérifier si toutes les tables ont été créées"""
        curseur = self.connexion.cursor()
        
        # Lister toutes les tables
        curseur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = curseur.fetchall()
        
        print(f"\nStructure de la base '{self.nom_db}':")
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
    
    def exporter_vers_sql(self, fichier_sql='db_engine_sqlite.sql'):
        """Exporter la structure vers un fichier SQL"""
        curseur = self.connexion.cursor()
        
        with open(fichier_sql, 'w', encoding='utf-8') as f:
            f.write(f'-- Base SQLite: {self.nom_db}\n')
            f.write(f'-- Exporté le: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
            
            # Désactiver temporairement les clés étrangères
            f.write('PRAGMA foreign_keys = OFF;\n\n')
            
            # Exporter chaque table
            curseur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = [row[0] for row in curseur.fetchall()]
            
            for table in tables:
                # Obtenir la structure de la table
                curseur.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table,))
                sql_creation = curseur.fetchone()[0]
                f.write(sql_creation + ';\n\n')
                
                # Exporter les données
                curseur.execute(f"SELECT * FROM {table}")
                lignes = curseur.fetchall()
                
                if lignes:
                    curseur.execute(f"PRAGMA table_info({table})")
                    colonnes = [info[1] for info in curseur.fetchall()]
                    
                    for ligne in lignes:
                        valeurs = []
                        for valeur in ligne:
                            if valeur is None:
                                valeurs.append('NULL')
                            elif isinstance(valeur, str):
                                valeurs.append(f"'{valeur.replace("'", "''")}'")
                            else:
                                valeurs.append(str(valeur))
                        
                        sql_insert = f"INSERT INTO {table} ({', '.join(colonnes)}) VALUES ({', '.join(valeurs)});\n"
                        f.write(sql_insert)
                    
                    f.write('\n')
            
            # Réactiver les clés étrangères
            f.write('PRAGMA foreign_keys = ON;\n')
            f.write('\n-- Fin de l\'exportation\n')
        
        print(f"Structure exportée vers: {fichier_sql}")
        return fichier_sql

# ====== FONCTIONS UTILITAIRES ======

def create_base_complete(nom_base='db_engine_sqlite.db'):
    """
    Fonction principale pour créer la base complète
    
    Args:
        nom_base (str): Nom de la base de données
    
    Returns:
        Database: Instance de la classe Database
    """
    
    # Supprimer la base existante si on veut recréer
    if os.path.exists(nom_base):
        os.remove(nom_base)
        print(f" Base précédente supprimée: {nom_base}")
    
    # Créer la base de données
    base_donnees = Database(nom_base)
    
    try:
        # Se connecter
        base_donnees.connect_db()
        
        # Créer toutes les tables
        base_donnees.create_all_tables()
        
        # Vérifier la structure
        base_donnees.verifier_structure()
        
        # Exporter vers SQL
        base_donnees.exporter_vers_sql()
        
        return base_donnees
        
    except Exception as e:
        print(f" Erreur: {e}")
        return None
    finally:
        base_donnees.close_db()

def tester_requetes(base_donnees):
    """Tester quelques requêtes sur la base créée"""
    
    base_donnees.connect_db()
    curseur = base_donnees.connexion.cursor()
    
    print("Test des requêtes:")
    print("=" * 50)
    
    # 1. Lister les clients
    print("\n1. Liste des clients:")
    curseur.execute("SELECT client_id, nom, email, mode FROM clients")
    for client in curseur.fetchall():
        print(f"   ID: {client[0]:3} | Nom: {client[1]:15} | Email: {client[2]:20} | Mode: {client[3]}")
    
    # 2. Vérifier les prix
    print("\n2. Table des prix:")
    curseur.execute("SELECT type, prix FROM prices ORDER BY type")
    for prix in curseur.fetchall():
        print(f"   {prix[0]:10}: €{prix[1]:.3f}/kWh")
    
    # 3. Vérifier les heures de pointe
    print("\n3. Horaires de pointe (HP):")
    curseur.execute("SELECT heure_debut, heure_fin FROM creneaux_hp ORDER BY heure_debut")
    for horaire in curseur.fetchall():
        print(f"   {horaire[0]} - {horaire[1]}")
    
    # 4. Tester les contraintes d'unicité
    print("\n4. Test des contraintes d'unicité...")
    try:
        # Essayer d'insérer un doublon dans prices
        curseur.execute("INSERT INTO prices (type, prix) VALUES ('base', 0.20)")
        print("    ERREUR: Devrait avoir échoué (contrainte UNIQUE)")
    except sqlite3.IntegrityError:
        print("    OK: Contrainte UNIQUE fonctionne")
    
    base_donnees.connexion.commit()
    base_donnees.close_db()

def exemple_utilisation_avancee(chemin_db='exemple_test.db'):
    """Exemple d'utilisation de la base dans une application"""

    # Supprimer la base existante si on veut recréer
    if os.path.exists(chemin_db):
        os.remove(chemin_db)
        print(f" Base précédente supprimée: {chemin_db}")
    
    # Créer la base de données
    base_donnees = Database(chemin_db)
    
    print("Exemple d'utilisation avancée:")
    print("=" * 50)
    
    # Créer la base
    base_donnees = create_base_complete(chemin_db)
    
    if base_donnees:
        # Se reconnecter pour utiliser
        base_donnees.connect_db()
        
        # Exemple: Ajouter un nouveau client avec toutes ses données liées
        print("Ajout d'un nouveau client complet...")
        
        # 1. Insérer le client
        curseur = base_donnees.connexion.cursor()
        curseur.execute("""
            INSERT INTO clients (nom, email, latitude, longitude, tilt, azimuth, router_id, pwd, mode)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'Jean Dupont', 'jean@email.com', -23.550520, -46.633308, 
            30.0, 180.0, 'RT001', 'motdepasse123', 'AutoCons'
        ))
        
        id_client = curseur.lastrowid
        
        # 2. Insérer les contraintes du client
        curseur.execute("""
            INSERT INTO constraints (client_id, temperature_minimale, puissance_maison)
            VALUES (?, ?, ?)
        """, (id_client, 15.0, 2.5))
        
        id_constraint = curseur.lastrowid
        
        # 3. Insérer le chauffe-eau
        curseur.execute("""
            INSERT INTO water_heaters (client_id, volume, power, coeff_isolation)
            VALUES (?, ?, ?, ?)
        """, (id_client, 200.0, 1500.0, 0.05))
        
        # 4. Insérer les consignes (horaires programmés)
        consignes = [
            (id_client, 1, '08:00:00', 50.0, 20.0),  # Lundi, 8h
            (id_client, 1, '20:00:00', 99.0, 105.0), # Lundi, 20h
            (id_client, 3, '09:00:00', 75.0, 49.5),  # Mercredi, 9h
        ]
        
        curseur.executemany("""
            INSERT INTO consignes (client_id, day, moment, temperature, volume)
            VALUES (?, ?, ?, ?, ?)
        """, consignes)
        
        # 5. Insérer les plages interdites (horaires interdits)
        plages = [
            (id_constraint, '23:00:00', '23:59:59'),  # Nuit
            (id_constraint, '00:00:00', '06:00:00'),  # Nuit
            (id_constraint, '13:00:00', '15:00:00'),  # Déjeuner
        ]
        
        curseur.executemany("""
            INSERT INTO plages_interdites (constraint_id, heure_debut, heure_fin)
            VALUES (?, ?, ?)
        """, plages)
        
        base_donnees.connexion.commit()
        
        # Consulter les données insérées
        print("Données du client inséré:")
        curseur.execute("""
            SELECT c.client_id, c.nom, c.mode, 
                   ct.temperature_minimale, ct.puissance_maison,
                   wh.volume, wh.power,
                   COUNT(DISTINCT cs.consigne_id) as total_consignes,
                   COUNT(DISTINCT pi.plage_interdite_id) as total_plages_interdites
            FROM clients c
            LEFT JOIN constraints ct ON c.client_id = ct.client_id
            LEFT JOIN water_heaters wh ON c.client_id = wh.client_id
            LEFT JOIN consignes cs ON c.client_id = cs.client_id
            LEFT JOIN plages_interdites pi ON ct.constraint_id = pi.constraint_id
            WHERE c.client_id = ?
            GROUP BY c.client_id
        """, (id_client,))
        
        donnees = curseur.fetchone()
        print(f"""
   ID Client: {donnees[0]}
   Nom: {donnees[1]}
   Mode: {donnees[2]}
   Temp. Minimale: {donnees[3]}°C
   Puissance Maison: {donnees[4]} kW
   Volume Chauffe-eau: {donnees[5]} L
   Puissance Chauffe-eau: {donnees[6]} W
   Total Consignes: {donnees[7]}
   Total Horaires Interdits: {donnees[8]}
        """)
        
        base_donnees.close_db()
        print(" Exemple terminé avec succès!")

# ====== MENU INTERACTIF ======

def menu_principal():
    """Menu interactif pour gérer la base de données"""
    
    while True:
        print("\n" + "=" * 60)
        print("SYSTEME DE CREATION ET DE TEST DE BASES DE DONNEES SQLite")
        print("=" * 60)
        print("1. Créer une base complète à partir de zéro")
        print("2. Tester des requêtes")
        print("3. Voir un exemple d'utilisation avancée")
        print("4. Exporter la structure vers SQL")
        print("5. Quitter")
        print("-" * 60)
        
        option = input("Choisissez une option (1-5): ").strip()
        
        if option == '1':
            nom = input("Nom de la base [db_engine_sqlite.db]: ") or 'db_engine_sqlite.db'
            create_base_complete(nom)
            
        elif option == '2':
            nom = input("Nom de la base à tester [db_engine_sqlite.db]: ") or 'db_engine_sqlite.db'
            if os.path.exists(nom):
                base_donnees = Database(nom)
                tester_requetes(base_donnees)
            else:
                print(f" Base '{nom}' non trouvée!")
                
        elif option == '3':
            exemple_utilisation_avancee()
            
        elif option == '4':
            nom = input("Nom de la base à exporter [db_engine_sqlite.db]: ") or 'db_engine_sqlite.db'
            if os.path.exists(nom):
                base_donnees = Database(nom)
                base_donnees.connect_db()
                fichier = base_donnees.exporter_vers_sql()
                base_donnees.close_db()
                print(f" Exporté vers: {fichier}")
            else:
                print(f" Base '{nom}' non trouvée!")
                
        elif option == '5':
            print("Au revoir...")
            break
            
        else:
            print(" Option invalide!")

# ====== EXÉCUTION ======

if __name__ == "__main__":
    # Exécuter le menu interactif
    menu_principal()
    
    # Ou exécuter directement:
    # base_donnees = create_base_complete()
    # tester_requetes(base_donnees)