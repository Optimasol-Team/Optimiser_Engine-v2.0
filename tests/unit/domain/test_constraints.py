import pytest
import numpy as np
from datetime import datetime, time

from optimiser_engine.domain.constraints import ConsumptionProfile, Constraints, DimensionNotRespected
from optimiser_engine.domain.common import TimeSlot


def test_consumption_profile_defaults_use_background_noise():
    profile = ConsumptionProfile()

    assert profile.data.shape == (7, 24)
    assert np.all(profile.data == profile.background_noise)


def test_consumption_profile_rejects_invalid_shape():
    with pytest.raises(DimensionNotRespected):
        ConsumptionProfile(matrix_7x24=np.zeros((7, 23)))


def test_consumption_profile_get_vector_interpolates_linearly():
    matrix = np.arange(7 * 24).reshape(7, 24)
    profile = ConsumptionProfile(matrix_7x24=matrix)
    start = datetime(2024, 1, 1, 0, 30)  # Monday

    vector = profile.get_vector(start_date=start, N=2, step_min=60)

    np.testing.assert_allclose(vector, [0.5, 1.5])


def test_consumption_profile_get_vector_validations():
    profile = ConsumptionProfile()
    start = datetime(2024, 1, 1, 0, 0)

    with pytest.raises(TypeError):
        profile.get_vector(start_date="2024-01-01", N=2, step_min=60)
    with pytest.raises(ValueError):
        profile.get_vector(start_date=start, N=0, step_min=60)
    with pytest.raises(ValueError):
        profile.get_vector(start_date=start, N=2, step_min=0)


def test_constraints_defaults_and_type_enforcement():
    constraints = Constraints()

    assert isinstance(constraints.consumption_profile, ConsumptionProfile)
    assert constraints.forbidden_slots == []
    assert constraints.minimum_temperature == 10.0

    with pytest.raises(TypeError):
        constraints.forbidden_slots = "not-a-list"
    with pytest.raises(TypeError):
        constraints.forbidden_slots = ["bad-item"]


def test_constraints_forbidden_slots_overlap_validation():
    c = Constraints()
    slot_a = TimeSlot(time(8, 0), time(10, 0))
    slot_b = TimeSlot(time(9, 30), time(11, 0))

    c.forbidden_slots = [slot_a]
    with pytest.raises(ValueError):
        c.forbidden_slots = [slot_a, slot_b]

    c.forbidden_slots = [slot_a]
    with pytest.raises(ValueError):
        c.add_forbidden_slot(start=time(9, 45), end=time(10, 30))


def test_constraints_is_allowed_checks_time(forbidden_slot):
    c = Constraints(forbidden_slots=[forbidden_slot])

    assert c.is_allowed(time(21, 59)) is True
    assert c.is_allowed(time(22, 0)) is False
    assert c.is_allowed(time(22, 30)) is False
    assert c.is_allowed(time(23, 0)) is True


@pytest.mark.parametrize("temp_value", [-1, 120, "hot"])
def test_constraints_minimum_temperature_validation(temp_value):
    c = Constraints()
    with pytest.raises(ValueError):
        c.minimum_temperature = temp_value


def test_constraints_consumption_profile_type_validation():
    c = Constraints()
    with pytest.raises(TypeError):
        c.consumption_profile = "not-a-profile"
