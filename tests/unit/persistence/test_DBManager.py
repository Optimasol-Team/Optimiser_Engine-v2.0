# command a partir de Optimiser_Engine-v2.0/: python3 -m tests.unit.persistence.test_DBManager

import unittest
import os
import json
import numpy as np
from datetime import datetime, time

import sys
from pathlib import Path

# Adiciona a pasta 'src' ao caminho de busca do Python
# (Isso sobe dois níveis a partir de tests/unit/persistence/ até a raiz do projeto)
path_to_src = Path(__file__).resolve().parents[3] / "src"
sys.path.append(str(path_to_src))

# Agora você importa normalmente a partir do pacote optimiser_engine
from optimiser_engine.persistence.DB_manager_models.exceptions_db import ClientNotFound
from optimiser_engine.persistence.DB_manager_models.main_manager import DBManager
from optimiser_engine.domain import (
    Client, Features, WaterHeater, Constraints, 
    ConsumptionProfile, Planning, Prices, OptimizationMode, TimeSlot
)

class TestDBManagerFull(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.db_path = "test_integration.db"
        cls.manager = DBManager(cls.db_path)

    def setUp(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.manager.db.connect_db()
        self.manager.db.create_all_tables()
        self.manager.db.close_db()

    def tearDown(self):
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except:
                pass

    def create_dummy_client(self, client_id):
        """Helper para criar um objeto Client completo exigido pelo seu domínio"""
        features = Features(gradation=False, mode=OptimizationMode.AUTOCONS)
        water_heater = WaterHeater(volume=150.0, power=2000.0)
        profile = ConsumptionProfile(matrix_7x24=np.zeros((7, 24)))
        constraints = Constraints(consumption_profile=profile, minimum_temperature=45.0)
        planning = Planning()
        prices = Prices(mode="HPHC")
        prices.hp_slots = [TimeSlot(start=time(8, 0), end=time(12, 0)), TimeSlot(start=time(18, 0), end=time(22, 0))]
        
        return Client(
            client_id=client_id,
            features=features,
            water_heater=water_heater,
            planning=planning,
            constraints=constraints,
            prices=prices
        )

    def test_constraints_json_integrity(self):
        client_id = 101
        test_matrix = np.random.rand(7, 24)
        
        # Criando cliente com matriz real
        client = self.create_dummy_client(client_id)
        client.constraints.consumption_profile = ConsumptionProfile(matrix_7x24=test_matrix)

        self.manager.create_client_in_db(client)

        # 1. Verifica se o nome da coluna no DB está correto (profil_conso_json)
        self.manager.db.connect_db()
        cursor = self.manager.db.connexion.cursor()
        cursor.execute("SELECT profil_conso_json FROM constraints WHERE client_id = ?", (client_id,))
        raw_json = cursor.fetchone()[0]
        self.manager.db.close_db()

        self.assertIsInstance(raw_json, str)
        
        # 2. Verifica a reconstituição do objeto
        reconstituted = self.manager.reconstitute_client(client_id)
        np.testing.assert_array_almost_equal(
            reconstituted.constraints.consumption_profile.data, 
            test_matrix
        )

    def test_full_client_cycle(self):
        client_id = 500
        client = self.create_dummy_client(client_id)
        
        self.manager.create_client_in_db(client)
        
        all_ids = self.manager.list_all_clients()
        self.assertIn(client_id, all_ids)
        
        self.manager.delete_client(client_id)
        with self.assertRaises(ClientNotFound):
            self.manager.reconstitute_client(client_id)

    def test_decisions_history(self):
        client_id = 303
        self.manager.create_client_in_db(self.create_dummy_client(client_id))
        
        now = datetime.now().replace(microsecond=0)
        self.manager.create_decision_in_db(client_id, now, 1200.0)

        history = self.manager.reconstitute_all_decisions(client_id)
        self.assertEqual(len(history), 1)
        self.assertEqual(float(history[0]['puissance']), 1200.0)

if __name__ == "__main__":
    unittest.main()