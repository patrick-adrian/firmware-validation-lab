"""Power manager models."""

from enum import Enum

from pydantic import BaseModel


class PowerState(str, Enum):
    """Discrete power throttling states."""

    NORMAL = "NORMAL"
    THROTTLED = "THROTTLED"
    EMERGENCY = "EMERGENCY"


class PowerStateStatus(BaseModel):
    """Published power state."""

    state: PowerState
