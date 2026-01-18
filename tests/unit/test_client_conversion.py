import sys
import unittest
from datetime import time
from pathlib import Path

import numpy as np

ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from optimiser_engine.domain.client import Client
from optimiser_engine.domain.common import TimeSlot
from optimiser_engine.domain.consignes_models import Planning, Setpoint
from optimiser_engine.domain.constraints import Constraints, ConsumptionProfile
from optimiser_engine.domain.features_models import Features, OptimizationMode
from optimiser_engine.domain.prices_model import Prices
from optimiser_engine.domain.water_heater_model import WaterHeater


class ClientConversionTest(unittest.TestCase):
    def test_to_dict_from_dict_round_trip(self):
        water_heater = WaterHeater(volume=200.0, power=2500.0)
        water_heater.insulation_coefficient = 0.1
        water_heater.cold_water_temperature = 12.0

        prices = Prices(mode="HPHC")
        prices.hp = 0.25
        prices.hc = 0.15
        prices.resale_price = 0.10
        prices.hp_slots = [TimeSlot(time(6, 0), time(22, 0))]

        features = Features(gradation=True, mode=OptimizationMode.COST)

        profile_matrix = np.array([[300 + hour for hour in range(24)] for _ in range(7)])
        consumption_profile = ConsumptionProfile(matrix_7x24=profile_matrix)
        constraints = Constraints(
            consumption_profile=consumption_profile,
            forbidden_slots=[TimeSlot(time(12, 0), time(14, 0))],
            minimum_temperature=42.0,
        )

        planning = Planning()
        planning.setpoints = [
            Setpoint(day=0, time_of_day=time(18, 15), temperature=55.0, volume=10.0),
            Setpoint(day=2, time_of_day=time(7, 30), temperature=52.0, volume=8.0),
        ]

        client = Client(
            planning=planning,
            constraints=constraints,
            features=features,
            prices=prices,
            water_heater=water_heater,
            client_id=987,
        )

        client_dict = client.to_dict()
        rebuilt_client = Client.from_dict(client_dict)
        rebuilt_dict = rebuilt_client.to_dict()

        self.assertEqual(client_dict, rebuilt_dict)


if __name__ == "__main__":
    unittest.main()
