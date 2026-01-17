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

client_id = 10
features = Features(gradation=True, mode=OptimizationMode.AUTOCONS)
water_heater = WaterHeater(volume=200.0, power=2400.0)
profile = ConsumptionProfile(matrix_7x24=np.ones((7, 24)) * 0.5)
constraints = Constraints(consumption_profile=profile, minimum_temperature=50.0)

# Adicionando alguns slots de planejamento
planning = Planning()
planning.add_setpoint(Setpoint(day=0, time_of_day=time(10,0), temperature=60.0, volume=200.0))

prices = Prices(mode="HPHC")
prices.hp_slots = [TimeSlot(start=time(8, 0), end=time(12, 0))]

cli = Client(
    client_id=client_id,
    features=features,
    water_heater=water_heater,
    planning=planning,
    constraints=constraints,
    prices=prices
)

a = DBManager("a.db")
try:
    """Testa: create_decision_in_db, reconstitute_decisions, update_decision e delete_decisions"""
    a.create_client_in_db(cli)

    now = datetime.now().replace(microsecond=0)
    tomorrow = now + timedelta(days=1)

    # 1. Create Decision
    a.create_decision_in_db(client_id, now, 1000.0)
    a.create_decision_in_db(client_id, tomorrow, 500.0)

    # 2. Get Decisions (Intervalo)
    # Note: reconstitute_decisions geralmente retorna um DataFrame se seguir o padrão anterior
    history = a.reconstitute_decisions(client_id, now, tomorrow)
    print(history)
except:
    pass
finally:
    a.delete_client(client_id)