"""Event propagation validation."""

import time

from analytics.log_parser import parse_component_logs
from framework.assertions import assert_state


def test_event_propagation(thermal_api, fan_api, power_api, propagate_delay) -> None:
    thermal_api.set_temperature(95)
    time.sleep(propagate_delay)

    assert_state(fan_api.get_speed().speed.value, "HIGH", component="Fan")
    assert_state(power_api.get_state().state.value, "THROTTLED", component="Power")

    logs = parse_component_logs()
    components = {entry.get("component") for entry in logs if entry.get("event") == "OVERHEAT"}
    assert "thermal_manager" in components
    assert "fan_controller" in components
    assert "power_manager" in components
