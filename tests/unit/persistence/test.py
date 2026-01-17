# Execução a partir de Optimiser_Engine-v2.0/: 
# python3 -m tests.unit.persistence.test

import unittest
import os
import numpy as np
from datetime import datetime, time, timedelta
import sys
from pathlib import Path

# Configuração de Path para localizar o pacote src
path_to_src = Path(__file__).resolve().parents[3] / "src"
sys.path.append(str(path_to_src))

from optimiser_engine.persistence.DB_manager_models.main_manager import DBManager
from optimiser_engine.persistence.DB_manager_models.exceptions_db import (
    ClientNotFound, DecisionNotFound, DatabaseIntegrityError
)
from optimiser_engine.domain import (
    Client, Features, WaterHeater, Constraints, 
    ConsumptionProfile, Planning, Prices, OptimizationMode, TimeSlot, Setpoint
)

class TestDBManagerFull(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.db_path = "test_integration_complete.db"
        cls.manager = DBManager(cls.db_path)

    def setUp(self):
        # Limpa o banco antes de cada teste para garantir isolamento
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
        """Cria um objeto Client populado para testes"""
        features = Features(gradation=True, mode=OptimizationMode.AUTOCONS)
        water_heater = WaterHeater(volume=200.0, power=2400.0)
        profile = ConsumptionProfile(matrix_7x24=np.ones((7, 24)) * 0.5)
        constraints = Constraints(consumption_profile=profile, minimum_temperature=50.0)
        
        # Adicionando alguns slots de planejamento
        planning = Planning()
        planning.add_setpoint(Setpoint(day=0, time_of_day=time(10,0), temperature=60.0, volume=200.0))
        
        prices = Prices(mode="HPHC")
        prices.hp_slots = [TimeSlot(start=time(8, 0), end=time(12, 0))]
        
        return Client(
            client_id=client_id,
            features=features,
            water_heater=water_heater,
            planning=planning,
            constraints=constraints,
            prices=prices
        )

    # =========================================================================
    # TESTES DO CLIENT_MANAGER
    # =========================================================================

    def test_client_lifecycle(self):
        """Testa: create_client_in_db, reconstitute_client, list_all_clients e delete_client"""
        client_id = 1
        client = self.create_dummy_client(client_id)

        # 1. Teste de Criação
        self.manager.create_client_in_db(client)
        
        # 2. Teste de Listagem
        all_ids = self.manager.list_all_clients()
        self.assertIn(client_id, all_ids)

        # 3. Teste de Reconstituição (Integridade de dados)
        reconstituted = self.manager.reconstitute_client(client_id)
        self.assertEqual(reconstituted.client_id, client_id)
        self.assertEqual(reconstituted.water_heater.volume, 200.0)
        self.assertEqual(len(reconstituted.planning.setpoints), 1)

        # 4. Teste de Deleção
        self.manager.delete_client(client_id)
        with self.assertRaises(ClientNotFound):
            self.manager.reconstitute_client(client_id)

    def test_update_client_partial(self):
        """Testa: update_client_in_db"""
        client_id = 2
        client = self.create_dummy_client(client_id)
        self.manager.create_client_in_db(client)

        # Novo planejamento para atualização
        new_planning = Planning()
        new_planning.add_setpoint(Setpoint(day=1, time_of_day=time(14,0), temperature=55.0, volume=200.0))
        
        # Atualiza apenas o planning
        self.manager.update_client_in_db(client_id, planning=new_planning)
        
        reconstituted = self.manager.reconstitute_client(client_id)
        self.assertEqual(reconstituted.planning.setpoints[0].day, 1)
        self.assertEqual(reconstituted.water_heater.volume, 200.0) # Mantém original

    # =========================================================================
    # TESTES DO DECISIONS_MANAGER
    # =========================================================================

    def test_decisions_full_flow(self):
        """Testa: create_decision_in_db, reconstitute_decisions, update_decision e delete_decisions"""
        client_id = 10
        self.manager.create_client_in_db(self.create_dummy_client(client_id))
        
        now = datetime.now().replace(microsecond=0)
        tomorrow = now + timedelta(days=1)

        # 1. Create Decision
        self.manager.create_decision_in_db(client_id, now, 1000.0)
        self.manager.create_decision_in_db(client_id, tomorrow, 500.0)

        # 2. Get Decisions (Intervalo)
        # Note: reconstitute_decisions geralmente retorna um DataFrame se seguir o padrão anterior
        history = self.manager.reconstitute_decisions(client_id, now, tomorrow)
        self.assertEqual(len(history), 2)

        # 3. Update Decision
        self.manager.update_decisions_in_db(client_id, now, 2000.0)
        updated_history = self.manager.reconstitute_decisions(client_id, now, now)
        # Verifica se o primeiro registro mudou para 2000.0
        # self.assertEqual(float(updated_history.iloc[0]['puissance']), 2000.0)
        self.assertEqual(float(updated_history[0]['puissance']), 2000.0)

        # 4. Delete Decisions for client
        self.manager.delete_all_decisions(client_id)
        with self.assertRaises(DecisionNotFound):
            self.manager.reconstitute_decisions(client_id, now, tomorrow)

    # =========================================================================
    # TESTES DE EXCEÇÕES (PARA O TIME DE UI)
    # =========================================================================

    def test_exceptions_raised(self):
        """Verifica se os erros corretos são disparados para a interface"""
        
        # Caso 1: ClientNotFound ao tentar ler ID inexistente
        with self.assertRaises(ClientNotFound):
            self.manager.reconstitute_client(999)

        # Caso 2: ClientNotFound ao tentar salvar decisão para cliente inexistente
        with self.assertRaises(ClientNotFound):
            self.manager.create_decision_in_db(999, datetime.now(), 100.0)

        # Caso 3: DecisionNotFound em intervalo vazio
        client_id = 50
        self.manager.create_client_in_db(self.create_dummy_client(client_id))
        with self.assertRaises(DecisionNotFound):
            self.manager.reconstitute_decisions(client_id, datetime(2000,1,1), datetime(2000,1,2))

if __name__ == "__main__":
    unittest.main()