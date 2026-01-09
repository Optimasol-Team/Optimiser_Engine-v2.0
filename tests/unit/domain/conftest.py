import pytest
import numpy as np
from datetime import time
import yaml

from optimiser_engine.domain import (
    TimeSlot,
    Setpoint,
    Planning,
    ConsumptionProfile,
    Constraints,
    Features,
    Prices,
    WaterHeater,
    OptimizationMode,
)


@pytest.fixture
def morning_slot():
    return TimeSlot(time(6, 0), time(8, 0))


@pytest.fixture
def evening_slot():
    return TimeSlot(time(18, 0), time(20, 0))


@pytest.fixture
def forbidden_slot():
    return TimeSlot(time(22, 0), time(23, 0))


@pytest.fixture
def consumption_matrix():
    return np.full((7, 24), 250.0)


@pytest.fixture
def consumption_profile(consumption_matrix):
    return ConsumptionProfile(matrix_7x24=consumption_matrix)


@pytest.fixture
def valid_constraints(consumption_profile, forbidden_slot):
    return Constraints(
        consumption_profile=consumption_profile,
        forbidden_slots=[forbidden_slot],
        minimum_temperature=45.0,
    )


@pytest.fixture
def valid_features():
    return Features(gradation=True, mode=OptimizationMode.AUTOCONS)


@pytest.fixture
def base_prices():
    prices = Prices()
    prices.mode = "BASE"
    prices.base = 0.21
    prices.resale_price = 0.05
    return prices


@pytest.fixture
def hphc_prices(morning_slot, evening_slot):
    prices = Prices()
    prices.mode = "HPHC"
    prices.hp = 0.30
    prices.hc = 0.12
    prices.hp_slots = [morning_slot, evening_slot]
    prices.resale_price = 0.06
    return prices


@pytest.fixture
def water_heater():
    heater = WaterHeater(volume=150, power=2500)
    heater.insulation_coefficient = 0.02
    heater.cold_water_temperature = 15
    return heater


@pytest.fixture
def planning_single_setpoint():
    planning = Planning()
    planning.setpoints = [Setpoint(0, time(7, 0), 55.0, volume=30.0)]
    return planning


@pytest.fixture
def client_dict_base(consumption_matrix):
    return {
        "client_id": 42,
        "water_heater": {
            "volume": 150,
            "power": 2500,
            "insulation_coeff": 0.02,
            "temp_cold_water": 15,
        },
        "prices": {
            "mode": "BASE",
            "base_price": 0.21,
            "resell_price": 0.05,
        },
        "features": {
            "gradation": True,
            "mode": "AutoCons",
        },
        "constraints": {
            "min_temp": 45.0,
            "forbidden_slots": [
                {"start": "22:00", "end": "23:00"},
            ],
            "consumption_profile": [[float(v) for v in row] for row in consumption_matrix.tolist()],
        },
        "planning": [
            {"day": 0, "time": "07:00", "target_temp": 55.0, "volume": 30.0},
            {"day": 2, "time": "19:30", "target_temp": 50.0, "volume": 20.0},
        ],
    }


@pytest.fixture
def client_dict_hphc(consumption_matrix):
    return {
        "water_heater": {"volume": 200, "power": 3000},
        "prices": {
            "mode": "HPHC",
            "hp_price": 0.28,
            "hc_price": 0.11,
            "resell_price": 0.07,
            "hp_slots": [
                {"start": "06:00", "end": "08:00"},
                {"start": "18:00", "end": "20:00"},
            ],
        },
        "features": {"gradation": False, "mode": "cost"},
        "constraints": {
            "min_temp": 50.0,
            "forbidden_slots": [],
            "consumption_profile": [[100.0] * 24 for _ in range(7)],
        },
        "planning": [
            {"day": 1, "time": "06:30", "target_temp": 52.0, "volume": 25.0},
        ],
    }


@pytest.fixture
def client_yaml_content(client_dict_base):
    return yaml.safe_dump(client_dict_base)
