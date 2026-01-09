import pytest

from optimiser_engine.domain.water_heater_model import WaterHeater


def test_water_heater_valid_initialization(water_heater):
    assert water_heater.volume == 150
    assert water_heater.power == 2500
    assert water_heater.insulation_coefficient == 0.02
    assert water_heater.cold_water_temperature == 15


@pytest.mark.parametrize(
    "attr_name, value",
    [
        ("volume", -1),
        ("power", -5),
    ],
)
def test_water_heater_rejects_negative_numbers(attr_name, value):
    heater = WaterHeater(volume=100, power=2000)
    with pytest.raises(ValueError):
        setattr(heater, attr_name, value)


@pytest.mark.parametrize("value", [-0.1, "bad"])
def test_insulation_coefficient_validation(value):
    heater = WaterHeater(volume=100, power=2000)
    with pytest.raises(ValueError):
        heater.insulation_coefficient = value


@pytest.mark.parametrize("value", [-5, "cold"])
def test_cold_water_temperature_validation(value):
    heater = WaterHeater(volume=100, power=2000)
    with pytest.raises(ValueError):
        heater.cold_water_temperature = value


def test_calculate_heating_temperature_increases_linearly():
    heater = WaterHeater(volume=120, power=2400)
    delta = heater.calculate_heating_temperature(temp_initial=40.0, power_ratio=0.5, time_delta_minutes=30)

    assert delta == pytest.approx(44.3, rel=1e-2)


def test_calculate_draw_temperature_mixes_cold_water():
    heater = WaterHeater(volume=200, power=2000)
    heater.cold_water_temperature = 15

    mixed_temp = heater.calculate_draw_temperature(temp_initial=60.0, drawn_volume=50.0)

    assert mixed_temp == pytest.approx(48.75, rel=1e-3)


def test_calculate_temperature_combines_steps(water_heater):
    result = water_heater.calculate_temperature(
        temp_init=50.0,
        power_ratio=0.5,
        time_delta_minutes=10,
        drawn_volume=20.0,
    )

    assert result == pytest.approx(46.33, rel=1e-2)
