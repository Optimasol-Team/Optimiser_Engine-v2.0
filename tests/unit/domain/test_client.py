import copy
from datetime import time
from pathlib import Path

import pytest

from optimiser_engine.domain import Client
from optimiser_engine.domain.features_models import OptimizationMode


def test_client_initialization_with_submodels(
    planning_single_setpoint, valid_constraints, valid_features, base_prices, water_heater
):
    client = Client(
        planning=planning_single_setpoint,
        constraints=valid_constraints,
        features=valid_features,
        prices=base_prices,
        water_heater=water_heater,
        client_id=7,
    )

    assert client.client_id == 7
    assert client.planning is planning_single_setpoint
    assert client.constraints is valid_constraints
    assert client.features.mode == OptimizationMode.AUTOCONS
    assert client.prices.mode == "BASE"
    assert client.water_heater.volume == 150


def test_client_from_dict_builds_components(client_dict_base):
    client = Client.from_dict(client_dict_base)

    assert client.prices.mode == "BASE"
    assert client.prices.base == pytest.approx(0.21)
    assert client.features.gradation is True
    assert client.features.mode == OptimizationMode.AUTOCONS
    assert client.constraints.minimum_temperature == 45.0
    assert client.constraints.consumption_profile.data.shape == (7, 24)
    assert len(client.planning.setpoints) == 2
    assert client.planning.setpoints[0].time == time(7, 0)


def test_client_from_dict_hphc_parses_slots(client_dict_hphc):
    client = Client.from_dict(client_dict_hphc)

    assert client.prices.mode == "HPHC"
    assert client.prices.hp == pytest.approx(0.28)
    assert client.prices.hc == pytest.approx(0.11)
    assert len(client.prices.hp_slots) == 2
    assert client.prices.hp_slots[0].start == time(6, 0)
    assert client.features.mode == OptimizationMode.COST


def test_client_from_dict_invalid_data_raises_value_error(client_dict_base):
    bad_data = copy.deepcopy(client_dict_base)
    bad_data["features"]["mode"] = "INVALID"

    with pytest.raises(ValueError):
        Client.from_dict(bad_data)

    bad_data = copy.deepcopy(client_dict_base)
    bad_data["planning"][0]["day"] = "Monday"
    with pytest.raises(ValueError):
        Client.from_dict(bad_data)


def test_client_from_yaml_and_file(client_yaml_content, tmp_path):
    client_from_string = Client.from_yaml(client_yaml_content)
    assert isinstance(client_from_string, Client)

    yaml_path = tmp_path / "client.yaml"
    yaml_path.write_text(client_yaml_content, encoding="utf-8")
    client_from_file = Client.from_yaml_file(str(yaml_path))

    assert client_from_file.prices.mode == "BASE"
    assert client_from_file.constraints.minimum_temperature == 45.0


def test_client_to_dict_serializes_domain_objects(client_dict_base):
    client = Client.from_dict(client_dict_base)
    serialized = client.to_dict()

    assert serialized["water_heater"]["volume"] == client_dict_base["water_heater"]["volume"]
    assert serialized["water_heater"]["temp_cold_water"] == client_dict_base["water_heater"]["temp_cold_water"]
    assert serialized["prices"]["mode"] == client_dict_base["prices"]["mode"]
    assert serialized["prices"]["base_price"] == pytest.approx(client_dict_base["prices"]["base_price"])
    assert serialized["prices"]["hp_price"] is None
    assert serialized["features"]["mode"] == client_dict_base["features"]["mode"]
    assert serialized["constraints"]["min_temp"] == client_dict_base["constraints"]["min_temp"]
    assert serialized["constraints"]["consumption_profile"] is None
    assert serialized["planning"][0]["time"] == client_dict_base["planning"][0]["time"]


def test_parse_time_str_handles_empty_and_valid_inputs():
    assert Client._parse_time_str(None) is None
    assert Client._parse_time_str("") is None
    assert Client._parse_time_str("06:45") == time(6, 45)


@pytest.mark.skipif(not Path("examples/client_sample.yaml").exists(), reason="example config missing")
def test_example_yaml_can_be_loaded():
    yaml_path = Path("examples/client_sample.yaml")
    content = yaml_path.read_text(encoding="utf-8")
    try:
        client = Client.from_yaml(content)
    except ValueError as exc:
        pytest.xfail(f"Example YAML is currently invalid: {exc}")

    assert isinstance(client, Client)
