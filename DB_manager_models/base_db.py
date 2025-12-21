import sqlite3
import os
from datetime import datetime

class Database:
    def __init__(self, chemin_db=None):
        """
        Initialise la classe Database
        
        Args:
            chemin_db (str): Chemin complet du fichier de base de données SQLite
                            Si None, utilise le chemin par défaut dans le répertoire courant
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
            self.connexion.execute("PRAGMA foreign_keys = ON")  # Activer les clés étrangères
            print(f"Connecté à la base de données: {self.chemin_db}")
            return True
        except sqlite3.Error as e:
            raise
        
    def close_db(self):
        """Fermer la connexion à la base de données"""
        if self.connexion:
            self.connexion.close()
            print("Connexion fermée")
    
    def create_all_tables(self, data_initial_wanted=True):
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
        if data_initial_wanted:
            self.insert_initial_data()
        
        # 9. Créer les index
        self.create_index()
        
        print("\nToutes les tables ont été créés avec succès!")

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
    
    # def create_table_clients(self):
    #     """Créer la table basée sur le fichier client_models/client.py et client_models/features_models.py"""
    #     sql = """
    #     CREATE TABLE IF NOT EXISTS clients (
    #         client_id INTEGER PRIMARY KEY AUTOINCREMENT,
    #         nom TEXT,
    #         email TEXT,
    #         latitude REAL,
    #         longitude REAL,
    #         tilt REAL,
    #         azimuth REAL,
    #         router_id TEXT,
    #         pwd TEXT,
    #         gradation INTEGER DEFAULT 0,
    #         mode TEXT DEFAULT 'AutoCons',
    #         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
    #         CHECK (mode IN ('AutoCons', 'cost')),
    #         CHECK (gradation IN (0, 1))
    #     );
    #     """
    #     self.connexion.execute(sql)
    #     print("Table 'clients' créé")
    
    def create_table_constraints(self):
        """Créer la table basée sur le fichier client_models/constraints.py"""
        sql = """
        CREATE TABLE IF NOT EXISTS constraints (
            constraint_id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            temperature_minimale REAL DEFAULT 10.0,
            puissance_maison REAL DEFAULT 0.0,
            
            FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE,
            CHECK (temperature_minimale > 0 AND temperature_minimale < 95),
            CHECK (puissance_maison >= 0)
        );
        """
        self.connexion.execute(sql)
        print("Table 'constraints' créé")

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
    
    def insert_initial_data(self):
        """Insérer les données initiales"""
        
        # 1. Insérer le client admin (comme dans MySQL)
        donnees_admin = (1, 0, 'AutoCons')
        
        try:
            self.connexion.execute("""
                INSERT OR IGNORE INTO clients 
                (client_id, gradation, mode) 
                VALUES (?, ?, ?)
            """, donnees_admin)
        except sqlite3.IntegrityError:
            # ID 1 existe déjà, utiliser AUTOINCREMENT
            donnees_admin = donnees_admin[1:]  # Retirer le client_id
            self.connexion.execute("""
                INSERT OR IGNORE INTO clients 
                (client_id, gradation, mode) 
                VALUES (?, ?, ?)
            """, donnees_admin)
        
        # 2. Insérer les prix par défaut
        prix_base = [
            (1, 'base', 0.18),    # Prix de base par kWh
            (1, 'hp', 0.22),      # Heures de pointe
            (1, 'hc', 0.15),      # Heures creuses
            (1, 'revente', 0.10)  # Prix de revente
        ]
        
        self.connexion.executemany("""
            INSERT OR IGNORE INTO prices (client_id, type, prix) VALUES (?, ?, ?)
        """, prix_base)
        
        # 3. Insérer les horaires de pointe par défaut (exemple: 06h-08h et 17h-19h)
        horaires_hp = [
            (1, '17:00:00', '19:00:00'),
            (1, '06:00:00', '08:00:00')
        ]
        
        self.connexion.executemany("""
            INSERT OR IGNORE INTO creneaux_hp (client_id, heure_debut, heure_fin) VALUES (?, ?, ?)
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
            ("CREATE INDEX IF NOT EXISTS idx_plages_constraint ON plages_interdites(constraint_id)"),

            # Table prices
            ("CREATE INDEX IF NOT EXISTS idx_prices_client ON prices(client_id)"),

            # Table creneaux_hp
            ("CREATE INDEX IF NOT EXISTS idx_creneaux_hp_client ON creneaux_hp(client_id)")
        ]
        
        for sql in index_liste:
            self.connexion.execute(sql)
        
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
    
    def exporter_vers_sql(self, fichier_sql=None):
        """Exporter la structure vers un fichier SQL"""
        if fichier_sql is None:
            # Créer un nom de fichier basé sur le nom de la base
            base_name = os.path.splitext(self.nom_fichier)[0]
            fichier_sql = f"{base_name}_export.sql"
        
        curseur = self.connexion.cursor()
        
        with open(fichier_sql, 'w', encoding='utf-8') as f:
            f.write(f'-- Base SQLite: {self.chemin_db}\n')
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

def demander_chemin_db(prompt="Chemin complet de la base de données: "):
    """Demander un chemin de base de données avec validation"""
    while True:
        chemin = input(prompt).strip()
        
        if not chemin:
            # Utiliser le chemin par défaut
            chemin = os.path.join(os.getcwd(), 'db_engine_sqlite.db')
            print(f"Utilisation du chemin par défaut: {chemin}")
            return chemin
        
        # Vérifier si le chemin a l'extension .db
        if not chemin.lower().endswith(('.db', '.sqlite', '.sqlite3')):
            print("Attention: Le fichier devrait avoir l'extension .db, .sqlite ou .sqlite3")
        
        # Convertir en chemin absolu
        chemin = os.path.abspath(chemin)
        
        # Vérifier si le dossier parent existe
        dossier_parent = os.path.dirname(chemin)
        if dossier_parent and not os.path.exists(dossier_parent):
            creer = input(f"Le dossier '{dossier_parent}' n'existe pas. Le créer? (o/n): ").strip().lower()
            if creer == 'o':
                os.makedirs(dossier_parent, exist_ok=True)
                print(f"Dossier créé: {dossier_parent}")
            else:
                print("Opération annulée.")
                continue
        
        return chemin

def lister_bases_donnees(dossier=None):
    """Lister toutes les bases de données dans un dossier"""
    if dossier is None:
        dossier = os.getcwd()
    
    bases = []
    extensions = ('.db', '.sqlite', '.sqlite3')
    
    for fichier in os.listdir(dossier):
        if fichier.lower().endswith(extensions):
            chemin = os.path.join(dossier, fichier)
            taille = os.path.getsize(chemin)
            bases.append({
                'nom': fichier,
                'chemin': chemin,
                'taille_mb': taille / (1024 * 1024)
            })
    
    return bases

def create_base_complete(chemin_db=None):
    """
    Fonction principale pour créer la base complète
    
    Args:
        chemin_db (str): Chemin complet de la base de données
    
    Returns:
        Database: Instance de la classe Database
    """
    
    if chemin_db is None:
        chemin_db = demander_chemin_db()
    
    info = {
        'chemin': chemin_db,
        'existe': os.path.exists(chemin_db),
        'taille': os.path.getsize(chemin_db) if os.path.exists(chemin_db) else 0
    }
    
    print(f"\nInformations sur la base:")
    print(f"  Chemin: {info['chemin']}")
    print(f"  Existe: {'Oui' if info['existe'] else 'Non'}")
    if info['existe']:
        print(f"  Taille: {info['taille'] / 1024:.1f} KB")
    
    # Demander confirmation si la base existe déjà
    if info['existe']:
        confirmation = input("\nLa base existe déjà. La recréer? (o/n): ").strip().lower()
        if confirmation != 'o':
            print("Opération annulée.")
            return None
        
        # Supprimer l'ancienne base
        os.remove(chemin_db)
        print(f"Ancienne base supprimée: {chemin_db}")
    
    # Créer la base de données
    base_donnees = Database(chemin_db)
    
    try:
        # Se connecter
        if not base_donnees.connect_db():
            return None
        
        # Créer toutes les tables
        base_donnees.create_all_tables()
        
        # Vérifier la structure
        base_donnees.verifier_structure()
        
        return base_donnees
        
    except Exception as e:
        print(f"Erreur: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        if base_donnees and base_donnees.connexion:
            base_donnees.close_db()

def tester_requetes(base_donnees):
    """Tester quelques requêtes sur la base créé"""
    
    if not base_donnees.connect_db():
        return
    
    curseur = base_donnees.connexion.cursor()
    
    print("Test des requêtes:")
    print("=" * 50)
    
    # 1. Lister les clients
    print("\n1. Liste des clients:")
    curseur.execute("SELECT client_id, gradation, mode FROM clients")
    for client in curseur.fetchall():
        print(f"   ID: {client[0]:3} | Gradation: {client[1]} | Mode: {client[2]}")
    
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
        # Essayer d'insérer un doublon dans creneaux hp
        curseur.execute("INSERT INTO creneaux_hp (client_id, heure_debut, heure_fin) VALUES (1, '17:00:00', '19:00:00')")
        print("    ERREUR: Devrait avoir échoué (contrainte UNIQUE)")
    except sqlite3.IntegrityError:
        print("    OK: Contrainte UNIQUE fonctionne")
    
    base_donnees.connexion.commit()
    base_donnees.close_db()

def exemple_utilisation_avancee():
    """Exemple d'utilisation de la base dans une application"""
    
    print("Exemple d'utilisation avancée:")
    print("=" * 50)
    
    # Demander le chemin pour l'exemple
    chemin_db = input("Chemin pour l'exemple [exemple_test.db]: ").strip()
    if not chemin_db:
        chemin_db = os.path.join(os.getcwd(), 'exemple_test.db')
    
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
            INSERT INTO clients (gradation, mode)
            VALUES (?, ?)
        """, (1, 'AutoCons'))
        
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
            SELECT c.client_id, c.gradation, c.mode, 
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
   Gradation: {donnees[1]}
   Mode: {donnees[2]}
   Temp. Minimale: {donnees[3]}°C
   Puissance Maison: {donnees[4]} kW
   Volume Chauffe-eau: {donnees[5]} L
   Puissance Chauffe-eau: {donnees[6]} W
   Total Consignes: {donnees[7]}
   Total Horaires Interdits: {donnees[8]}
        """)
        
        base_donnees.close_db()
        print("Exemple terminé avec succès!")

# ====== MENU INTERACTIF ======

def menu_principal():
    """Menu interactif pour gérer la base de données"""
    
    base_donnees = None
    
    while True:
        print("\n" + "=" * 60)
        print("SYSTEME DE CREATION ET DE TEST DE BASES DE DONNEES SQLite")
        print("=" * 60)
        print("1. Créer une base complète à partir de zéro")
        print("2. Tester des requêtes sur une base existante")
        print("3. Voir un exemple d'utilisation avancée")
        print("4. Exporter la structure vers SQL")
        print("5. Quitter")
        print("-" * 60)
        
        option = input("Choisissez une option (1-5): ").strip()
        
        if option == '1':
            base_donnees = create_base_complete()
            
        elif option == '2':
            if base_donnees is None:
                chemin_db = demander_chemin_db("Chemin de la base à tester: ")
                if os.path.exists(chemin_db):
                    base_donnees = Database(chemin_db)
                else:
                    print(f"Base non trouvée: {chemin_db}")
                    continue
            
            tester_requetes(base_donnees)
            
        elif option == '3':
            exemple_utilisation_avancee()
            
        elif option == '4':
            if base_donnees is None:
                chemin_db = demander_chemin_db("Chemin de la base à exporter: ")
                if os.path.exists(chemin_db):
                    base_donnees = Database(chemin_db)
                else:
                    print(f"Base non trouvée: {chemin_db}")
                    continue
            
            base_donnees.connect_db()
            fichier = base_donnees.exporter_vers_sql()
            base_donnees.close_db()
            print(f"Exporté vers: {fichier}")
            
        elif option == '5':
            print("Au revoir...")
            break
            
        else:
            print("Option invalide!")

# ====== EXÉCUTION DIRECTE ======

if __name__ == "__main__":
    # Exécuter le menu interactif
    menu_principal()
    
    # Ou exécuter directement avec un chemin spécifique:
    # chemin_db = "/chemin/complet/vers/ma_base.db"
    # base_donnees = create_base_complete(chemin_db)
    # if base_donnees:
    #     tester_requetes(base_donnees)