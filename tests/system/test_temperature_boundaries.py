"""Temperature boundary validation."""

import time

from framework.assertions import assert_state


def test_temperature_boundaries(thermal_api, fan_api, power_api, propagate_delay) -> None:
    cases = [
        (60, "LOW", "NORMAL"),
        (80, "MEDIUM", "NORMAL"),
        (95, "HIGH", "THROTTLED"),
        (105, "MAX", "EMERGENCY"),
    ]

    for temperature, expected_fan, expected_power in cases:
        thermal_api.set_temperature(temperature)
        time.sleep(propagate_delay)

        fan = fan_api.get_speed()
        power = power_api.get_state()
        assert_state(fan.speed.value, expected_fan, component=f"Fan@{temperature}C")
        assert_state(power.state.value, expected_power, component=f"Power@{temperature}C")
