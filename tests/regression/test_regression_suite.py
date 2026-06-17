"""Core regression scenarios from the validation plan."""

import time

from framework.assertions import assert_state


def test_normal_temperature(thermal_api, fan_api, power_api, propagate_delay) -> None:
    thermal_api.set_temperature(60)
    time.sleep(propagate_delay)
    assert_state(fan_api.get_speed().speed.value, "LOW", component="Fan")
    assert_state(power_api.get_state().state.value, "NORMAL", component="Power")


def test_warning_temperature(thermal_api, fan_api, power_api, propagate_delay) -> None:
    thermal_api.set_temperature(80)
    time.sleep(propagate_delay)
    assert_state(fan_api.get_speed().speed.value, "MEDIUM", component="Fan")
    assert_state(power_api.get_state().state.value, "NORMAL", component="Power")


def test_overheat_temperature(thermal_api, fan_api, power_api, propagate_delay) -> None:
    thermal_api.set_temperature(95)
    time.sleep(propagate_delay)
    assert_state(fan_api.get_speed().speed.value, "HIGH", component="Fan")
    assert_state(power_api.get_state().state.value, "THROTTLED", component="Power")


def test_critical_temperature(thermal_api, fan_api, power_api, propagate_delay) -> None:
    thermal_api.set_temperature(105)
    time.sleep(propagate_delay)
    assert_state(fan_api.get_speed().speed.value, "MAX", component="Fan")
    assert_state(power_api.get_state().state.value, "EMERGENCY", component="Power")
