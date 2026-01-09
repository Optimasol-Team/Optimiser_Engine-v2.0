import numpy as np
import pytest

pytest.importorskip("scipy.optimize")

from optimiser_engine.engine.solver import Solver


def test_solver_calls_linprog_for_gradation(monkeypatch, optimization_inputs_cost, num_steps):
    calls = {}

    class DummyRes:
        def __init__(self):
            self.success = True
            self.x = np.arange(4 * num_steps + 1, dtype=float)
            self.fun = 12.0
            self.message = "ok"

    def fake_linprog(c, A_eq, b_eq, bounds, method, options):
        calls["c"] = c
        calls["bounds"] = bounds
        calls["options"] = options
        return DummyRes()

    monkeypatch.setattr("optimiser_engine.engine.solver.linprog", fake_linprog)

    solver = Solver(timeout=3)
    traj = solver.solve(optimization_inputs_cost)

    assert traj.X.shape == (4 * num_steps + 1,)
    assert traj.compute_cost() == pytest.approx(12.0)
    assert calls["options"]["time_limit"] == 3
    assert len(calls["bounds"]) == 4 * num_steps + 1


def test_solver_raises_runtime_error_on_milp_failure(monkeypatch, optimization_inputs_binary, num_steps):
    class DummyRes:
        def __init__(self):
            self.success = False
            self.x = np.zeros(4 * num_steps + 1)
            self.message = "failed"

    def fake_milp(**kwargs):
        return DummyRes()

    monkeypatch.setattr("optimiser_engine.engine.solver.milp", fake_milp)

    solver = Solver(timeout=1)
    with pytest.raises(RuntimeError):
        solver.solve(optimization_inputs_binary)


def test_solver_uses_integrality_vector_for_milp(monkeypatch, optimization_inputs_binary, num_steps):
    captured = {}

    class DummyRes:
        def __init__(self):
            self.success = True
            self.x = np.ones(4 * num_steps + 1, dtype=float)
            self.fun = 2.5
            self.message = "ok"

    def fake_milp(c, constraints, integrality, bounds, options):
        captured["integrality"] = integrality
        captured["bounds"] = bounds
        return DummyRes()

    monkeypatch.setattr("optimiser_engine.engine.solver.milp", fake_milp)

    solver = Solver(timeout=2)
    traj = solver.solve(optimization_inputs_binary)

    assert captured["integrality"] is not None
    assert np.all(captured["integrality"][:num_steps] == 1)
    assert len(captured["bounds"].lb) == 4 * num_steps + 1
    assert traj.X.shape == (4 * num_steps + 1,)
