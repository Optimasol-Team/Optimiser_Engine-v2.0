import pytest

from optimiser_engine.engine.models.system_config import SystemConfig


def test_system_config_valid_initialization():
    cfg = SystemConfig(
        power=2000,
        volume=180,
        heat_loss_coefficient=0.02,
        is_gradation=True,
        T_cold_water=12,
        T_min=8,
        T_max=95,
    )

    assert cfg.power == 2000
    assert cfg.volume == 180
    assert cfg.heat_loss_coefficient == pytest.approx(0.02)
    assert cfg.T_cold_water == 12
    assert cfg.T_min_safe == 8
    assert cfg.T_max_safe == 95
    assert cfg.is_gradation is True


def test_system_config_from_client_inherits_values(system_config_gradation, client_autocons):
    cfg = system_config_gradation

    assert cfg.power == client_autocons.water_heater.power
    assert cfg.volume == client_autocons.water_heater.volume
    assert cfg.is_gradation == client_autocons.features.gradation
    assert cfg.T_min_safe == client_autocons.constraints.minimum_temperature
    assert cfg.T_max_safe == 95  # safety value is fixed in factory


def test_system_config_rejects_invalid_inputs():
    with pytest.raises(TypeError):
        SystemConfig(power="high", volume=150, heat_loss_coefficient=0.01, T_cold_water=10)

    with pytest.raises(ValueError):
        SystemConfig(power=1500, volume=-10, heat_loss_coefficient=0.01, T_cold_water=10)

    with pytest.raises(TypeError):
        SystemConfig(power=1500, volume=120, heat_loss_coefficient="fast")

    with pytest.raises(ValueError):
        SystemConfig(power=1500, volume=120, heat_loss_coefficient=0.01, T_cold_water=80)

