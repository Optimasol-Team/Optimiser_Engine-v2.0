from datetime import timedelta

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("scipy.optimize")

from optimiser_engine.engine.models.optimisation_inputs import OptimizationInputs
from optimiser_engine.engine.models.Exceptions import WeatherNotValid
from optimiser_engine.engine.service import OptimizerService


def test_optimizer_service_horizon_and_step_validation():
    service = OptimizerService(horizon_hours=2, step_minutes=15)
    assert service.horizon == 2
    assert service.step_minutes == 15

    with pytest.raises(ValueError):
        OptimizerService(horizon_hours=0.5, step_minutes=15)

    with pytest.raises(ValueError):
        OptimizerService(horizon_hours=2, step_minutes=400)

    with pytest.raises(ValueError):
        service.step_minutes = 1  # below minimum


def test_is_df_valid_and_normalize(reference_datetime):
    service = OptimizerService(horizon_hours=1, step_minutes=15)
    start = reference_datetime
    good_df = pd.DataFrame({"prod": [1, 2, 3, 4, 5]}, index=pd.date_range(start, periods=5, freq="15T"))

    assert service._is_df_valid(good_df, start, start + timedelta(hours=1))

    bad_gap_df = pd.DataFrame({"prod": [1.0, 2.0]}, index=[start, start + timedelta(minutes=90)])
    assert service._is_df_valid(bad_gap_df, start, start + timedelta(hours=1)) is False

    normalized = service._normalize_df(good_df, start)
    assert len(normalized) == 5
    assert normalized.index[0] == start


def test_to_array_rejects_empty_df():
    service = OptimizerService(horizon_hours=1, step_minutes=15)
    with pytest.raises(ValueError):
        service._to_array(pd.DataFrame(columns=["prod"]))


def test_trajectory_of_client_uses_solver(monkeypatch, client_autocons, reference_datetime, num_steps):
    service = OptimizerService(horizon_hours=1, step_minutes=15)
    production_df = pd.DataFrame(
        {"prod": np.arange(num_steps + 1, dtype=float)},
        index=pd.date_range(reference_datetime, periods=num_steps + 1, freq="15T"),
    )

    def fake_to_array(self, df_normalized):
        arr = df_normalized.iloc[:, 0].to_numpy(dtype=float)
        return arr[:num_steps]

    monkeypatch.setattr(OptimizerService, "_to_array", fake_to_array)

    captured = {}

    class DummySolver:
        def solve(self, inputs):
            captured["inputs"] = inputs
            return "trajectory"

    monkeypatch.setattr("optimiser_engine.engine.service.Solver", lambda: DummySolver())

    trajectory = service.trajectory_of_client(
        client_autocons,
        start_datetime=reference_datetime,
        initial_temperature=50.0,
        production_df=production_df,
    )

    assert trajectory == "trajectory"
    assert isinstance(captured["inputs"], OptimizationInputs)


def test_trajectory_of_client_raises_weather_error(monkeypatch, client_autocons, reference_datetime):
    service = OptimizerService(horizon_hours=1, step_minutes=15)
    bad_df = pd.DataFrame({"prod": []})

    with pytest.raises(WeatherNotValid):
        service.trajectory_of_client(
            client_autocons,
            start_datetime=reference_datetime,
            initial_temperature=50.0,
            production_df=bad_df,
        )
