import numpy as np
import pytest

from optimiser_engine.engine.models.Exceptions import NotEnoughVariables
from optimiser_engine.engine.models.optimisation_inputs import OptimizationInputs


def test_equality_matrices_have_expected_shapes(optimization_inputs_cost, num_steps):
    A_eq = optimization_inputs_cost.A_eq()
    B_eq = optimization_inputs_cost.B_eq()

    assert A_eq.shape == (2 * num_steps + 1, 4 * num_steps + 1)
    assert B_eq.shape == (2 * num_steps + 1,)
    assert B_eq[0] == pytest.approx(optimization_inputs_cost.initial_temperature)


def test_bounds_length_and_limits(optimization_inputs_cost, num_steps):
    bounds = optimization_inputs_cost.get_bounds()

    assert len(bounds) == 4 * num_steps + 1
    assert bounds[0] == (0, 1)  # decision variable bounds
    assert bounds[num_steps][0] == 0  # first temperature lower bound
    assert bounds[-1][1] is None  # exports upper bound is open (+inf)


def test_integrality_vector_for_binary_mode(optimization_inputs_binary, num_steps):
    integrality = optimization_inputs_binary.get_integrality_vector()

    assert integrality.shape == (4 * num_steps + 1,)
    assert np.all(integrality[:num_steps] == 1)
    assert np.all(integrality[num_steps:] == 0)


def test_missing_values_raise_not_enough_variables(optimization_inputs_cost):
    optimization_inputs_cost.context.water_draws = None
    with pytest.raises(NotEnoughVariables):
        optimization_inputs_cost.A_eq()

    optimization_inputs_cost.context = None
    with pytest.raises(NotEnoughVariables):
        optimization_inputs_cost.C_cost()


def test_cost_vector_requires_prices(optimization_inputs_cost):
    optimization_inputs_cost.context.prices_purchases = None
    with pytest.raises(NotEnoughVariables):
        optimization_inputs_cost.C_cost()

