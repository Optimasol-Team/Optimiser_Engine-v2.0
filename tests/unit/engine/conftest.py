import numpy as np
import pytest
from datetime import datetime, time

from optimiser_engine.domain import (
    Client,
    Constraints,
    ConsumptionProfile,
    Features,
    Planning,
    Prices,
    Setpoint,
    WaterHeater,
)
from optimiser_engine.domain.features_models import OptimizationMode
from optimiser_engine.engine.models.external_context import ExternalContext
from optimiser_engine.engine.models.optimisation_inputs import OptimizationInputs
from optimiser_engine.engine.models.system_config import SystemConfig
from optimiser_engine.engine.models.trajectory import TrajectorySystem

DEFAULT_HORIZON_HOURS = 1
DEFAULT_STEP_MINUTES = 15


@pytest.fixture
def reference_datetime() -> datetime:
    return datetime(2024, 1, 1, 6, 0, 0)


@pytest.fixture
def num_steps() -> int:
    return int(DEFAULT_HORIZON_HOURS * 60 / DEFAULT_STEP_MINUTES)


@pytest.fixture
def consumption_profile() -> ConsumptionProfile:
    return ConsumptionProfile(matrix_7x24=np.full((7, 24), 100.0))


@pytest.fixture
def planning_basic() -> Planning:
    planning = Planning()
    planning.setpoints = [
        Setpoint(0, time(7, 0), 55.0, volume=30.0),
        Setpoint(1, time(18, 30), 50.0, volume=15.0),
    ]
    return planning


@pytest.fixture
def prices_base() -> Prices:
    prices = Prices()
    prices.mode = "BASE"
    prices.base = 0.20
    prices.resale_price = 0.05
    return prices


@pytest.fixture
def prices_hphc() -> Prices:
    prices = Prices()
    prices.mode = "HPHC"
    prices.hp = 0.30
    prices.hc = 0.12
    prices.resale_price = 0.06
    return prices


@pytest.fixture
def constraints_basic(consumption_profile: ConsumptionProfile) -> Constraints:
    return Constraints(consumption_profile=consumption_profile, forbidden_slots=[], minimum_temperature=45.0)


@pytest.fixture
def features_autocons() -> Features:
    return Features(gradation=True, mode=OptimizationMode.AUTOCONS)


@pytest.fixture
def features_cost_binary() -> Features:
    return Features(gradation=False, mode=OptimizationMode.COST)


@pytest.fixture
def water_heater() -> WaterHeater:
    heater = WaterHeater(volume=150, power=2500)
    heater.insulation_coefficient = 0.02
    heater.cold_water_temperature = 15
    return heater


@pytest.fixture
def water_heater_binary() -> WaterHeater:
    heater = WaterHeater(volume=120, power=2000)
    heater.insulation_coefficient = 0.03
    heater.cold_water_temperature = 12
    return heater


@pytest.fixture
def client_autocons(
    planning_basic: Planning,
    constraints_basic: Constraints,
    features_autocons: Features,
    prices_base: Prices,
    water_heater: WaterHeater,
) -> Client:
    return Client(
        planning=planning_basic,
        constraints=constraints_basic,
        features=features_autocons,
        prices=prices_base,
        water_heater=water_heater,
        client_id=1,
    )


@pytest.fixture
def client_cost_binary(
    planning_basic: Planning,
    constraints_basic: Constraints,
    features_cost_binary: Features,
    prices_hphc: Prices,
    water_heater_binary: WaterHeater,
) -> Client:
    return Client(
        planning=planning_basic,
        constraints=constraints_basic,
        features=features_cost_binary,
        prices=prices_hphc,
        water_heater=water_heater_binary,
        client_id=2,
    )


@pytest.fixture
def system_config_gradation(client_autocons: Client) -> SystemConfig:
    return SystemConfig.from_client(client_autocons)


@pytest.fixture
def system_config_binary(client_cost_binary: Client) -> SystemConfig:
    return SystemConfig.from_client(client_cost_binary)


@pytest.fixture
def context_arrays(num_steps: int):
    return {
        "prices_purchase": np.full(num_steps, 0.2),
        "prices_sell": np.full(num_steps, 0.05),
        "solar_production": np.array([0.0, 50.0, 0.0, 0.0][:num_steps], dtype=float),
        "house_consumption": np.full(num_steps, 100.0),
        "water_draws": np.array([0.0, 5.0, 0.0, 5.0][:num_steps], dtype=float),
        "future_setpoints": np.full(num_steps, 45.0),
        "availability_on": np.ones(num_steps),
        "off_peak_hours": np.ones(num_steps),
    }


@pytest.fixture
def external_context_with_data(
    num_steps: int, reference_datetime: datetime, context_arrays
) -> ExternalContext:
    return ExternalContext(
        N=num_steps,
        step_minutes=DEFAULT_STEP_MINUTES,
        reference_datetime=reference_datetime,
        prices_purchase=context_arrays["prices_purchase"],
        prices_sell=context_arrays["prices_sell"],
        solar_production=context_arrays["solar_production"],
        house_consumption=context_arrays["house_consumption"],
        water_draws=context_arrays["water_draws"],
        future_setpoints=context_arrays["future_setpoints"],
        availability_on=context_arrays["availability_on"],
        off_peak_hours=context_arrays["off_peak_hours"],
    )


@pytest.fixture
def optimization_inputs_cost(
    system_config_gradation: SystemConfig, external_context_with_data: ExternalContext
) -> OptimizationInputs:
    return OptimizationInputs(
        system_config_gradation,
        external_context_with_data,
        initial_temperature=50.0,
        mode=OptimizationMode.COST,
    )


@pytest.fixture
def optimization_inputs_autocons(
    system_config_gradation: SystemConfig, external_context_with_data: ExternalContext
) -> OptimizationInputs:
    return OptimizationInputs(
        system_config_gradation,
        external_context_with_data,
        initial_temperature=50.0,
        mode=OptimizationMode.AUTOCONS,
    )


@pytest.fixture
def optimization_inputs_binary(
    system_config_binary: SystemConfig, external_context_with_data: ExternalContext
) -> OptimizationInputs:
    return OptimizationInputs(
        system_config_binary,
        external_context_with_data,
        initial_temperature=50.0,
        mode=OptimizationMode.COST,
    )


@pytest.fixture
def empty_trajectory(
    system_config_gradation: SystemConfig, external_context_with_data: ExternalContext
) -> TrajectorySystem:
    return TrajectorySystem(system_config_gradation, external_context_with_data, initial_temperature=50.0)

