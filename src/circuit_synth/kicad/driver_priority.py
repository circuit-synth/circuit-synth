from enum import IntEnum


class DriverPriority(IntEnum):
    """Enum defining priority levels for net drivers.

    Higher values indicate higher priority in determining net names.
    """

    INVALID = -1
    NONE = 0
    PIN = 1
    SHEET_PIN = 2
    HIER_LABEL = 3
    LOCAL_LABEL = 4
    LOCAL_POWER_PIN = 5
    GLOBAL_POWER_PIN = 6
    GLOBAL = 6
