from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from .driver_priority import DriverPriority


@dataclass
class NetInfo:
    """Class for storing information about a net."""

    name: str
    driver_priority: DriverPriority = DriverPriority.NONE
    sheet_paths: Set[str] = field(default_factory=set)
    driver_source: Optional[str] = None
    is_power_net: bool = False


class NetTracker:
    """Class for tracking and analyzing net information."""

    def __init__(self):
        self._nets: Dict[str, NetInfo] = {}

    def analyze_net_drivers(self, net_id: str, drivers: List[Dict]) -> DriverPriority:
        """Analyze drivers on a net to determine highest priority driver.

        Args:
            net_id: Unique identifier for the net
            drivers: List of driver dictionaries containing type and source info

        Returns:
            DriverPriority indicating the highest priority driver found
        """
        if net_id not in self._nets:
            self._nets[net_id] = NetInfo(name=net_id)

        highest_priority = DriverPriority.NONE
        driver_source = None

        for driver in drivers:
            driver_type = driver.get("type", "")
            priority = self._get_driver_priority(driver_type)

            if priority > highest_priority:
                highest_priority = priority
                driver_source = driver.get("source")

        self._nets[net_id].driver_priority = highest_priority
        self._nets[net_id].driver_source = driver_source
        return highest_priority

    def track_net_usage(self, net_id: str, sheet_path: str) -> None:
        """Track which sheets a net appears in.

        Args:
            net_id: Unique identifier for the net
            sheet_path: Hierarchical sheet path where net is used
        """
        if net_id not in self._nets:
            self._nets[net_id] = NetInfo(name=net_id)
        self._nets[net_id].sheet_paths.add(sheet_path)

    def _get_driver_priority(self, driver_type: str) -> DriverPriority:
        """Convert driver type string to DriverPriority enum value.

        Args:
            driver_type: String indicating the type of driver

        Returns:
            Corresponding DriverPriority enum value
        """
        priority_map = {
            "pin": DriverPriority.PIN,
            "sheet_pin": DriverPriority.SHEET_PIN,
            "hierarchical_label": DriverPriority.HIER_LABEL,
            "hier_label": DriverPriority.HIER_LABEL,  # Support both formats
            "local_label": DriverPriority.LOCAL_LABEL,
            "local_power_pin": DriverPriority.LOCAL_POWER_PIN,
            "global_power_pin": DriverPriority.GLOBAL_POWER_PIN,
            "global": DriverPriority.GLOBAL,
        }
        return priority_map.get(driver_type.lower(), DriverPriority.INVALID)

    def get_net_info(self, net_id: str) -> Optional[NetInfo]:
        """Get stored information about a net.

        Args:
            net_id: Unique identifier for the net

        Returns:
            NetInfo object if net exists, None otherwise
        """
        return self._nets.get(net_id)

    def detect_power_nets(self, net_id: str, pins: List[Dict]) -> bool:
        """Detect if a net is a power net based on connected pins.

        Args:
            net_id: Unique identifier for the net
            pins: List of pin dictionaries with electrical_type info

        Returns:
            True if net is determined to be a power net
        """
        if net_id not in self._nets:
            self._nets[net_id] = NetInfo(name=net_id)

        # Count power pin types
        power_pin_count = 0
        total_pins = len(pins)

        for pin in pins:
            electrical_type = pin.get("electrical_type", "").lower()
            if electrical_type in ["power_in", "power_out"]:
                power_pin_count += 1

        # A net is considered a power net if:
        # 1. All pins are power pins, OR
        # 2. More than 50% of pins are power pins and there are at least 2 power pins
        is_power = (power_pin_count == total_pins and total_pins > 0) or (
            power_pin_count >= 2 and power_pin_count / total_pins > 0.5
        )

        # Update net info
        self._nets[net_id].is_power_net = is_power

        # If it's a power net, update driver priority
        if is_power:
            # Assuming power nets should have global power pin priority
            self._nets[net_id].driver_priority = DriverPriority.GLOBAL_POWER_PIN

        # Note: Sheet path tracking is done separately via track_net_usage

        return is_power
