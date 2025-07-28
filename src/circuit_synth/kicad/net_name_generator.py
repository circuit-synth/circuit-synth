import re
from typing import Dict, List, Optional, Tuple

from .driver_priority import DriverPriority
from .net_tracker import NetTracker


class NetNameGenerator:
    """Class for generating net names based on driver priorities and rules."""

    def __init__(self, net_tracker: NetTracker):
        self._net_tracker = net_tracker
        self._name_counter: Dict[str, int] = {}
        self._bus_counters: Dict[str, int] = {}  # Track indices per bus

    def generate_net_name(self, net_id: str) -> str:
        """Generate a net name based on driver priority rules.

        Args:
            net_id: Unique identifier for the net

        Returns:
            Generated net name string
        """
        net_info = self._net_tracker.get_net_info(net_id)
        if not net_info:
            return f"Net-{self._get_next_number('unnamed')}"

        # Use driver source name if available and priority is sufficient
        if (
            net_info.driver_source
            and net_info.driver_priority >= DriverPriority.HIER_LABEL
        ):
            return net_info.driver_source

        # Generate default name based on net ID
        return f"Net-{self._get_next_number('net')}"

    def resolve_bus_names(self, net_ids: List[str], bus_name: str) -> Dict[str, str]:
        """Resolve names for nets that are part of a bus.

        Args:
            net_ids: List of net IDs that are part of the bus
            bus_name: Base name for the bus

        Returns:
            Dictionary mapping net IDs to their resolved bus member names

        Raises:
            ValueError: If bus_name is empty or net_ids list is empty/has duplicates
        """
        self._validate_bus_inputs(net_ids, bus_name)
        resolved_names = {}
        base_name = self._normalize_bus_name(bus_name)
        position_map = {net_id: i for i, net_id in enumerate(net_ids)}

        # First pass: handle high priority names
        for net_id in net_ids:
            net_info = self._net_tracker.get_net_info(net_id)
            if (
                net_info
                and net_info.driver_source
                and net_info.driver_priority >= DriverPriority.HIER_LABEL
                and net_info.driver_priority < DriverPriority.LOCAL_LABEL
            ):
                resolved_names[net_id] = net_info.driver_source

        # Second pass: assign position-based names using original list order
        for net_id in net_ids:
            if net_id not in resolved_names:
                resolved_names[net_id] = f"{base_name}[{position_map[net_id]}]"

        return resolved_names

    def _validate_bus_inputs(self, net_ids: List[str], bus_name: str) -> None:
        """Validate bus naming inputs.

        Args:
            net_ids: List of net IDs to validate
            bus_name: Bus name to validate

        Raises:
            ValueError: If validation fails
        """
        if not bus_name:
            raise ValueError("Bus name cannot be empty")
        if not net_ids:
            raise ValueError("Net ID list cannot be empty")
        if len(set(net_ids)) != len(net_ids):
            raise ValueError("Duplicate net IDs not allowed")

    def _normalize_bus_name(self, bus_name: str) -> str:
        """Normalize bus name by removing any existing array notation.

        Args:
            bus_name: Original bus name

        Returns:
            Normalized bus name
        """
        return re.sub(r"\[\d+\]$", "", bus_name)

    def _extract_existing_index(self, net_id: str) -> Optional[int]:
        """Try to extract existing index from net info.

        Args:
            net_id: Net ID to check

        Returns:
            Extracted index if found, None otherwise
        """
        net_info = self._net_tracker.get_net_info(net_id)
        if net_info and net_info.driver_source:
            match = re.search(r"\[(\d+)\]$", net_info.driver_source)
            if match:
                return int(match.group(1))
        return None

    def _get_next_number(self, prefix: str) -> int:
        """Get next available number for a given name prefix.

        Args:
            prefix: String prefix for the counter

        Returns:
            Next available number
        """
        if prefix not in self._name_counter:
            self._name_counter[prefix] = 0
        self._name_counter[prefix] += 1
        return self._name_counter[prefix]

    def apply_power_net_rules(self, net_id: str) -> str:
        """Apply power net naming rules to generate appropriate name.

        Args:
            net_id: Unique identifier for the net

        Returns:
            Generated net name following power net conventions
        """
        net_info = self._net_tracker.get_net_info(net_id)
        if not net_info:
            return net_id

        # If it's a power net, use standard power net naming
        if net_info.is_power_net:
            # Check if it's a global power net with a driver source
            if (
                net_info.driver_priority == DriverPriority.GLOBAL_POWER_PIN
                and net_info.driver_source
            ):
                # For global power nets with driver source, use the source name
                return net_info.driver_source
            else:
                # For local power nets, generate LOCAL_PWR-N name
                return f"LOCAL_PWR-{self._get_next_number('local_pwr')}"

        # For non-power nets, use standard naming
        return self.generate_net_name(net_id)
