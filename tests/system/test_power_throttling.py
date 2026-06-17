"""Power throttling validation."""

import time

from framework.assertions import assert_state


def test_power_throttling(thermal_api, fan_api, power_api, propagate_delay) -> None:
    thermal_api.set_temperature(80)
    time.sleep(propagate_delay)
    assert_state(power_api.get_state().state.value, "NORMAL", component="Power@warning")

    thermal_api.set_temperature(90)
    time.sleep(propagate_delay)
    assert_state(power_api.get_state().state.value, "THROTTLED", component="Power@overheat")
    assert_state(fan_api.get_speed().speed.value, "HIGH", component="Fan@overheat")

    thermal_api.set_temperature(102)
    time.sleep(propagate_delay)
    assert_state(power_api.get_state().state.value, "EMERGENCY", component="Power@critical")
