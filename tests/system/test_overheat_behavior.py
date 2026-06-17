"""Overheat behavior validation."""

import time

from framework.assertions import assert_state


def test_overheat_behavior(thermal_api, fan_api, power_api, propagate_delay) -> None:
    thermal_api.set_temperature(95)
    time.sleep(propagate_delay)

    fan = fan_api.get_speed()
    power = power_api.get_state()

    assert_state(fan.speed.value, "HIGH", component="Fan")
    assert_state(power.state.value, "THROTTLED", component="Power")
