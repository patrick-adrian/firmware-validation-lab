"""Cooling recovery validation."""

import time

from framework.assertions import assert_state


def test_cooling_recovery(thermal_api, fan_api, power_api, propagate_delay) -> None:
    thermal_api.set_temperature(105)
    time.sleep(propagate_delay)

    fan = fan_api.get_speed()
    power = power_api.get_state()
    assert_state(fan.speed.value, "MAX", component="Fan")
    assert_state(power.state.value, "EMERGENCY", component="Power")

    thermal_api.set_temperature(65)
    time.sleep(propagate_delay)

    fan = fan_api.get_speed()
    power = power_api.get_state()
    assert_state(fan.speed.value, "LOW", component="Fan")
    assert_state(power.state.value, "NORMAL", component="Power")
