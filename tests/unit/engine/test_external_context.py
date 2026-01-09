import numpy as np
import pytest

from optimiser_engine.engine.models.Exceptions import DimensionNotRespected
from optimiser_engine.engine.models.external_context import ExternalContext


def test_external_context_accepts_valid_arrays(external_context_with_data, num_steps):
    ctx = external_context_with_data

    assert ctx.N == num_steps
    assert ctx.step_minutes == 15
    assert ctx.solar_production.shape == (num_steps,)
    assert ctx.house_consumption.shape == (num_steps,)
    assert ctx.future_setpoints.min() >= 0
    assert np.all(ctx.availability_on == 1)


def test_check_array_validations(num_steps):
    with pytest.raises(DimensionNotRespected):
        ExternalContext.check_array(np.ones((num_steps, 1)), num_steps)

    with pytest.raises(TypeError):
        ExternalContext.check_array([1, 2, 3], num_steps)

    with pytest.raises(TypeError):
        ExternalContext.check_array(np.array([1, "a", 3]), num_steps)


def test_from_client_builds_expected_vectors(client_autocons, reference_datetime, num_steps):
    solar = np.zeros(num_steps, dtype=float)
    ctx = ExternalContext.from_client(
        client=client_autocons,
        reference_datetime=reference_datetime,
        solar_productions=solar,
        horizon=1,
        time_step_minutes=15,
    )

    assert ctx.N == num_steps
    assert ctx.prices_purchases.shape == (num_steps,)
    assert ctx.prices_sell.shape == (num_steps,)
    assert ctx.water_draws.shape == (num_steps,)
    assert ctx.future_setpoints.shape == (num_steps,)
    assert (ctx.off_peak_hours >= 0).all()


def test_from_client_rejects_invalid_params(client_autocons, reference_datetime):
    with pytest.raises(TypeError):
        ExternalContext.from_client(client_autocons, reference_datetime, np.zeros(4), horizon="24", time_step_minutes=15)

    with pytest.raises(TypeError):
        ExternalContext.from_client(client_autocons, "not-a-date", np.zeros(4), horizon=1, time_step_minutes=15)

