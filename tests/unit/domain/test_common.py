import pytest
from datetime import time

from optimiser_engine.domain import TimeSlot


def test_timeslot_valid_creation_and_ordering():
    slot = TimeSlot(time(6, 0), time(7, 30))
    other = TimeSlot(time(8, 0), time(9, 0))

    assert slot.start == time(6, 0)
    assert slot.end == time(7, 30)
    assert slot < other


def test_timeslot_start_after_end_raises_value_error():
    with pytest.raises(ValueError):
        TimeSlot(time(10, 0), time(9, 59))


def test_timeslot_overlap_and_contains_checks(morning_slot, evening_slot):
    overlapping = TimeSlot(time(7, 30), time(8, 30))

    assert morning_slot.overlaps(overlapping)
    assert not morning_slot.overlaps(evening_slot)
    assert morning_slot.contains(time(6, 0))
    assert morning_slot.contains(time(7, 59))
    assert not morning_slot.contains(time(8, 0))


def test_timeslot_duration_minutes():
    slot = TimeSlot(time(12, 0), time(13, 45))
    assert slot.duration_minutes() == 105
