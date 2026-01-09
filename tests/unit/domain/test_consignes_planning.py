import pytest
from datetime import time

from optimiser_engine.domain import Setpoint, Planning


def test_setpoint_valid_initialization():
    consigne = Setpoint(day=1, time_of_day=time(8, 15), temperature=60.0, volume=35.0)

    assert consigne.day == 1
    assert consigne.time == time(8, 15)
    assert consigne.temperature == 60.0
    assert consigne.drawn_volume == 35.0


@pytest.mark.parametrize("day_value", [-1, 7, 3.5])
def test_setpoint_rejects_invalid_day(day_value):
    with pytest.raises(ValueError):
        Setpoint(day=day_value, time_of_day=time(8, 0), temperature=55.0, volume=20.0)


def test_setpoint_rejects_invalid_time_type():
    with pytest.raises(ValueError):
        Setpoint(day=0, time_of_day="08:00", temperature=55.0, volume=20.0)


@pytest.mark.parametrize("temperature", [20.0, 120.0, "hot"])
def test_setpoint_rejects_temperature_out_of_range(temperature):
    with pytest.raises(ValueError):
        Setpoint(day=0, time_of_day=time(7, 0), temperature=temperature, volume=20.0)


def test_setpoint_rejects_negative_volume():
    with pytest.raises(ValueError):
        Setpoint(day=0, time_of_day=time(7, 0), temperature=55.0, volume=-1.0)


def test_planning_setter_validates_list_content():
    planning = Planning()

    with pytest.raises(TypeError):
        planning.setpoints = "invalid"

    with pytest.raises(TypeError):
        planning.setpoints = ["not-setpoint"]


def test_planning_sorts_and_keeps_hottest_duplicate():
    planning = Planning()
    s1 = Setpoint(0, time(7, 0), 55.0, volume=20.0)
    s2 = Setpoint(0, time(7, 0), 60.0, volume=15.0)  # hotter duplicate
    s3 = Setpoint(0, time(6, 30), 50.0, volume=10.0)

    planning.setpoints = [s1, s2, s3]

    assert [c.temperature for c in planning.setpoints] == [50.0, 60.0]
    assert planning.setpoints[0].time < planning.setpoints[1].time


def test_add_setpoint_preserves_order_and_validation(planning_single_setpoint):
    planning = planning_single_setpoint
    later = Setpoint(0, time(9, 0), 52.0, volume=10.0)
    planning.add_setpoint(later)

    assert planning.setpoints[-1].time == later.time

    with pytest.raises(TypeError):
        planning.add_setpoint("not-a-setpoint")


def test_remove_setpoint_returns_boolean(planning_single_setpoint):
    planning = planning_single_setpoint
    removed = planning.remove_setpoint(jour=0, heure=time(7, 0))

    assert removed is True
    assert planning.setpoints == []
    assert planning.remove_setpoint(jour=0, heure=time(7, 0)) is False


def test_get_future_setpoints_respects_horizon_and_week_wrap():
    planning = Planning()
    sunday_evening = Setpoint(6, time(23, 30), 50.0, volume=10.0)
    monday_morning = Setpoint(0, time(1, 0), 55.0, volume=20.0)
    tuesday_event = Setpoint(1, time(10, 0), 48.0, volume=5.0)
    planning.setpoints = [monday_morning, sunday_evening, tuesday_event]

    results = planning.get_future_setpoints(
        jour_actuel=6, heure_actuelle=time(23, 0), horizon_heures=3
    )

    assert [c.time for c in results] == [time(23, 30), time(1, 0)]
    assert all(c.day in (6, 0) for c in results)
