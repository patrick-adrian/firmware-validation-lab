"""Fan controller models."""

from enum import Enum

from pydantic import BaseModel


class FanSpeed(str, Enum):
    """Discrete fan speed levels."""

    OFF = "OFF"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    MAX = "MAX"


class FanSpeedStatus(BaseModel):
    """Published fan speed status."""

    speed: FanSpeed
