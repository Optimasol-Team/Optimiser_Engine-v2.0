import numpy as np
import pytest

from optimiser_engine.engine.models.Exceptions import DimensionNotRespected, PermissionDeniedError
from optimiser_engine.engine.models.trajectory import RouterMode, TrajectorySystem
from optimiser_engine.engine.models.warnings import UpdateRequired


def test_setting_x_validates_and_warns(empty_trajectory, num_steps, system_config_binary):
    traj = empty_trajectory
    with pytest.warns(UpdateRequired):
        traj.x = np.full(num_steps, 0.5)

    assert traj.X.shape == (4 * num_steps + 1,)

    with pytest.raises(DimensionNotRespected):
        traj.x = np.array([0.1, 0.2])

    traj.make_solver_delivered_traj()
    with pytest.raises(PermissionDeniedError):
        traj.x = np.full(num_steps, 0.1)

    traj_binary = TrajectorySystem(system_config_binary, traj.context, initial_temperature=50.0)
    with pytest.raises(ValueError):
        traj_binary.x = np.full(num_steps, 0.5)


def test_update_X_and_accessors_produce_vectors(empty_trajectory, num_steps):
    traj = empty_trajectory
    with pytest.warns(UpdateRequired):
        traj.x = np.zeros(num_steps)

    traj.update_X()

    temperatures = traj.get_temperatures()
    imports = traj.get_imports()
    exports = traj.get_exports()

    assert temperatures[0] == pytest.approx(traj.initial_temperature)
    assert temperatures.shape == (num_steps + 1,)
    assert imports.shape == (num_steps,)
    assert exports.shape == (num_steps,)

    cost = traj.compute_cost()
    assert isinstance(cost, float)
    ratio = traj.compute_self_consumption()
    assert 0.0 <= ratio <= 1.0


def test_compute_cost_returns_cached_when_solver_delivered(empty_trajectory, num_steps):
    traj = empty_trajectory
    with pytest.warns(UpdateRequired):
        traj.x = np.zeros(num_steps)
    traj.update_X()
    first_cost = traj.compute_cost()

    traj.make_solver_traj()
    traj.upload_cost(first_cost + 1.0)
    traj.make_solver_delivered_traj()

    assert traj.compute_cost() == pytest.approx(first_cost + 1.0)


def test_generate_standard_and_router_trajectories(empty_trajectory, num_steps):
    std_traj = TrajectorySystem.generate_standard_trajectory(
        context=empty_trajectory.context,
        config_system=empty_trajectory.config_system,
        initial_temperature=45.0,
    )

    assert std_traj.get_decisions().shape == (num_steps,)
    assert std_traj.X.shape == (4 * num_steps + 1,)

    router_traj = TrajectorySystem.generate_router_only_trajectory(
        context=empty_trajectory.context,
        config_system=empty_trajectory.config_system,
        initial_temperature=45.0,
        router_mode=RouterMode.SELF_CONSUMPTION_ONLY,
    )

    assert router_traj.X.shape == (4 * num_steps + 1,)
    assert router_traj.get_exports().shape == (num_steps,)


def test_upload_methods_enforce_mode(empty_trajectory, num_steps):
    traj = empty_trajectory
    with pytest.raises(PermissionDeniedError):
        traj.upload_X_vector(np.zeros(4 * num_steps + 1))

    traj.make_solver_traj()
    with pytest.raises(DimensionNotRespected):
        traj.upload_X_vector(np.zeros(2))

    full_vec = np.arange(4 * num_steps + 1, dtype=float)
    traj.upload_X_vector(full_vec)
    traj.upload_cost(1.5)

    assert traj.compute_cost() == pytest.approx(1.5)
