import pytest
from datetime import time

from optimiser_engine.domain.features_models import Features, OptimizationMode
from optimiser_engine.domain.prices_model import Prices, ModeIncompatibleError
from optimiser_engine.domain.common import TimeSlot


def test_features_valid_initialization(valid_features):
    assert valid_features.gradation is True
    assert valid_features.mode == OptimizationMode.AUTOCONS


def test_features_rejects_invalid_inputs():
    with pytest.raises(TypeError):
        Features(gradation="yes", mode=OptimizationMode.COST)
    with pytest.raises(TypeError):
        Features(gradation=True, mode="COST")


def test_prices_base_mode_blocks_hphc_attributes():
    prices = Prices()
    prices.mode = "BASE"
    prices.base = 0.19

    assert prices.get_current_purchase_price(time(12, 0)) == 0.19
    with pytest.raises(ModeIncompatibleError):
        _ = prices.hp
    with pytest.raises(ModeIncompatibleError):
        prices.hp_slots


def test_prices_switch_to_hphc_and_compute_current_price(morning_slot, evening_slot):
    prices = Prices()
    prices.mode = "HPHC"
    prices.hp = 0.28
    prices.hc = 0.11
    prices.hp_slots = [evening_slot, morning_slot]  # deliberately unsorted
    prices.resale_price = 0.07

    # slots should be sorted inside the setter
    assert prices.hp_slots[0].start == morning_slot.start
    assert prices.get_current_purchase_price(time(6, 30)) == 0.28
    assert prices.get_current_purchase_price(time(9, 0)) == 0.11

    with pytest.raises(ModeIncompatibleError):
        _ = prices.base


def test_hp_slots_validation_errors():
    prices = Prices()
    prices.mode = "HPHC"

    with pytest.raises(TypeError):
        prices.hp_slots = "not-a-list"

    with pytest.raises(TypeError):
        prices.hp_slots = [TimeSlot(time(6, 0), time(7, 0)), "bad"]

    with pytest.raises(ValueError):
        prices.hp_slots = [
            TimeSlot(time(6, 0), time(8, 0)),
            TimeSlot(time(7, 30), time(9, 0)),
        ]

    with pytest.raises(ValueError):
        prices.hp_slots = []


def test_prices_mode_validation_and_resale_price():
    prices = Prices()
    with pytest.raises(ValueError):
        prices.mode = "INVALID"

    with pytest.raises(ValueError):
        prices.resale_price = -1
