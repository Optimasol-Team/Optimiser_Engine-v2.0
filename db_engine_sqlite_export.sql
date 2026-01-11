-- Base SQLite: /home/lacampelo/optimasol/Optimiser_Engine-v2.0/db_engine_sqlite.db
-- Exporté le: 2026-01-11 14:56:26
PRAGMA foreign_keys = OFF;

CREATE TABLE clients (
            client_id INTEGER PRIMARY KEY AUTOINCREMENT,
            gradation INTEGER DEFAULT 0,
            mode TEXT DEFAULT 'AutoCons',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            CHECK (mode IN ('AutoCons', 'cost')),
            CHECK (gradation IN (0, 1))
        );

INSERT INTO clients (client_id, gradation, mode, created_at) VALUES (1, 0, 'AutoCons', '2026-01-11 13:54:01');

CREATE TABLE consignes (
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

CREATE TABLE constraints (
            constraint_id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            temperature_minimale REAL DEFAULT 10.0,
            profil_conso_json TEXT, 
            
            FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE,
            CHECK (temperature_minimale > 0 AND temperature_minimale < 95)
        );

CREATE TABLE creneaux_hp (
            creneau_hp_id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            heure_debut TEXT NOT NULL,
            heure_fin TEXT NOT NULL,
            
            FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE,
            UNIQUE (client_id, heure_debut, heure_fin),
            CHECK (heure_debut < heure_fin)
        );

INSERT INTO creneaux_hp (creneau_hp_id, client_id, heure_debut, heure_fin) VALUES (1, 1, '17:00:00', '19:00:00');
INSERT INTO creneaux_hp (creneau_hp_id, client_id, heure_debut, heure_fin) VALUES (2, 1, '06:00:00', '08:00:00');

CREATE TABLE plages_interdites (
            plage_interdite_id INTEGER PRIMARY KEY AUTOINCREMENT,
            constraint_id INTEGER,
            heure_debut TEXT NOT NULL,
            heure_fin TEXT NOT NULL,
            
            FOREIGN KEY (constraint_id) REFERENCES constraints(constraint_id) ON DELETE CASCADE,
            UNIQUE (constraint_id, heure_debut, heure_fin),
            CHECK (heure_debut < heure_fin)
        );

CREATE TABLE prices (
            client_id INTEGER,
            type TEXT,
            prix REAL NOT NULL,

            PRIMARY KEY (client_id, type),
            FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE,
            CHECK (type IN ('base', 'hp', 'hc', 'revente')),
            CHECK (prix >= 0)
        );

INSERT INTO prices (client_id, type, prix) VALUES (1, 'base', 0.18);
INSERT INTO prices (client_id, type, prix) VALUES (1, 'hp', 0.22);
INSERT INTO prices (client_id, type, prix) VALUES (1, 'hc', 0.15);
INSERT INTO prices (client_id, type, prix) VALUES (1, 'revente', 0.1);

CREATE TABLE sqlite_sequence(name,seq);

INSERT INTO sqlite_sequence (name, seq) VALUES ('clients', 1);
INSERT INTO sqlite_sequence (name, seq) VALUES ('creneaux_hp', 2);

CREATE TABLE water_heaters (
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

PRAGMA foreign_keys = ON;

-- Fin de l'exportation
