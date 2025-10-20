"""
Net-tie insertion for component grouping.

This module provides utilities for automatically inserting net-ties to make
component relationships explicit, particularly for decoupling capacitors and
power distribution networks.

Net-ties are zero-ohm connections that:
- Make power distribution topology explicit in the schematic
- Guide placement algorithms (components connected via net-tie should be adjacent)
- Show which decoupling cap serves which power pin
- Improve readability without affecting electrical behavior

Example:
    MCU VDD_CORE → C1 → NetTie1 → VCC
    MCU VDD_IO → C2 → NetTie2 → VCC

This makes it clear that C1 decouples VDD_CORE and C2 decouples VDD_IO,
rather than having both caps simply connect to VCC.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

from ._logger import context_logger
from .component import Component
from .exception import CircuitSynthError
from .net import Net
from .pin import Pin


@dataclass
class NetTieConfig:
    """Configuration for net-tie insertion."""

    # Auto-insert net-ties for decoupling capacitors
    auto_decoupling: bool = True

    # Minimum capacitance to consider for decoupling (in farads)
    # Default: 1nF (1e-9F). Caps below this are likely for other purposes.
    min_decoupling_cap: float = 1e-9

    # Maximum capacitance to consider for decoupling (in farads)
    # Default: 1000uF (1e-3F). Caps above this are likely bulk storage.
    max_decoupling_cap: float = 1e-3

    # Net-tie reference prefix
    net_tie_prefix: str = "NT"

    # Net-tie symbol to use
    net_tie_symbol: str = "Device:NetTie_2"

    # Net-tie footprint (usually none - it's schematic-only)
    net_tie_footprint: str = ""


class NetTieInserter:
    """
    Handles automatic insertion of net-ties to make component relationships explicit.
    """

    def __init__(self, config: Optional[NetTieConfig] = None):
        """
        Initialize net-tie inserter.

        Args:
            config: Configuration for net-tie insertion. If None, uses defaults.
        """
        self.config = config or NetTieConfig()
        self._net_ties: List[Component] = []

    def insert_decoupling_net_ties(
        self,
        circuit: "Circuit",
        target_component: Optional[Component] = None
    ) -> List[Component]:
        """
        Insert net-ties for decoupling capacitors.

        For each decoupling capacitor:
        1. Identify which power pin it decouples
        2. Insert a net-tie between the cap and the power rail
        3. Create topology: IC_PIN → CAP → NET_TIE → POWER_RAIL

        Args:
            circuit: The circuit to process
            target_component: If specified, only process decoupling caps for this component.
                            If None, process all components in the circuit.

        Returns:
            List of inserted net-tie components
        """
        context_logger.info(
            "Inserting decoupling net-ties",
            component="NET_TIE",
            auto_decoupling=self.config.auto_decoupling,
            target=target_component.ref if target_component else "all"
        )

        if not self.config.auto_decoupling:
            return []

        # Find all decoupling capacitors in the circuit
        decoupling_caps = self._find_decoupling_capacitors(circuit, target_component)

        inserted_net_ties = []

        for cap_info in decoupling_caps:
            cap = cap_info['component']
            power_pin = cap_info['power_pin']
            power_net = cap_info['power_net']
            gnd_net = cap_info['gnd_net']

            # Create a net-tie component
            net_tie = self._create_net_tie(circuit)

            # Create intermediate net between cap and net-tie
            intermediate_net = Net(f"{power_net.name}_to_{cap.ref}")

            # Reconnect: IC_PIN → CAP → INTERMEDIATE_NET → NET_TIE → POWER_NET
            # The cap's positive pin is already connected to power_net
            # We need to:
            # 1. Disconnect cap from power_net
            # 2. Connect cap to intermediate_net
            # 3. Connect net_tie pin 1 to intermediate_net
            # 4. Connect net_tie pin 2 to power_net

            cap_power_pin = cap["1"]  # Assume pin 1 is the positive pin

            # Disconnect from power net
            if hasattr(cap_power_pin, '_net') and cap_power_pin._net:
                old_net = cap_power_pin._net
                if cap_power_pin in old_net._pins:
                    old_net._pins.remove(cap_power_pin)
                cap_power_pin._net = None

            # Connect to intermediate net
            cap_power_pin.connect_to_net(intermediate_net)

            # Connect net-tie
            net_tie["1"].connect_to_net(intermediate_net)
            net_tie["2"].connect_to_net(power_net)

            # Store metadata about the relationship
            net_tie._extra_fields['groups_with'] = cap.ref
            net_tie._extra_fields['associated_ic'] = power_pin.component.ref if power_pin else None

            inserted_net_ties.append(net_tie)

            context_logger.debug(
                f"Inserted net-tie for decoupling cap",
                component="NET_TIE",
                net_tie=net_tie.ref,
                capacitor=cap.ref,
                power_net=power_net.name,
                ic_pin=f"{power_pin.component.ref}.{power_pin.name}" if power_pin else "unknown"
            )

        self._net_ties.extend(inserted_net_ties)
        return inserted_net_ties

    def insert_manual_net_tie(
        self,
        circuit: "Circuit",
        component1: Component,
        pin1: str,
        component2: Component,
        pin2: str,
        power_net: Net
    ) -> Component:
        """
        Manually insert a net-tie between two components.

        This creates the topology:
        component1[pin1] → intermediate_net → NET_TIE → power_net ← component2[pin2]

        Args:
            circuit: The circuit to add the net-tie to
            component1: First component to group
            pin1: Pin name on component1
            component2: Second component to group
            pin2: Pin name on component2
            power_net: The power net they should connect to via the net-tie

        Returns:
            The inserted net-tie component
        """
        # Create net-tie
        net_tie = self._create_net_tie(circuit)

        # Create intermediate net
        intermediate_net = Net(f"{component1.ref}_{component2.ref}_tie")

        # Connect components through intermediate net
        component1[pin1].connect_to_net(intermediate_net)
        component2[pin2].connect_to_net(intermediate_net)

        # Connect net-tie
        net_tie["1"].connect_to_net(intermediate_net)
        net_tie["2"].connect_to_net(power_net)

        # Store metadata
        net_tie._extra_fields['groups_with'] = f"{component1.ref},{component2.ref}"

        self._net_ties.append(net_tie)

        context_logger.info(
            f"Inserted manual net-tie",
            component="NET_TIE",
            net_tie=net_tie.ref,
            component1=component1.ref,
            component2=component2.ref,
            power_net=power_net.name
        )

        return net_tie

    def _create_net_tie(self, circuit: "Circuit") -> Component:
        """
        Create a net-tie component.

        Args:
            circuit: The circuit to add the net-tie to

        Returns:
            A new net-tie component
        """
        net_tie = Component(
            symbol=self.config.net_tie_symbol,
            ref=self.config.net_tie_prefix,
            value="NetTie",
            footprint=self.config.net_tie_footprint,
            description="Net tie for component grouping"
        )

        # Net-ties should not appear in BOM
        net_tie._extra_fields['exclude_from_bom'] = True

        return net_tie

    def _find_decoupling_capacitors(
        self,
        circuit: "Circuit",
        target_component: Optional[Component] = None
    ) -> List[Dict[str, Any]]:
        """
        Find all decoupling capacitors in a circuit.

        A capacitor is considered a decoupling cap if:
        1. It's a capacitor (symbol contains "Device:C")
        2. One pin connects to a power net (VCC, VDD, etc.)
        3. Other pin connects to ground (GND, VSS, etc.)
        4. Value is within decoupling range (typically 0.1uF - 100uF)
        5. If target_component specified, must share a power net with it

        Args:
            circuit: The circuit to search
            target_component: If specified, only find caps that decouple this component

        Returns:
            List of dicts with keys: 'component', 'power_net', 'gnd_net', 'power_pin'
        """
        decoupling_caps = []

        # Get all components
        for comp in circuit._component_list:
            # Check if it's a capacitor
            if not self._is_capacitor(comp):
                continue

            # Check if value is in decoupling range
            if not self._is_decoupling_value(comp.value):
                continue

            # Check pin connections
            cap_info = self._analyze_capacitor_connections(comp)
            if not cap_info:
                continue

            # If target component specified, check if this cap decouples it
            if target_component:
                if not self._decouples_component(cap_info, target_component):
                    continue

            decoupling_caps.append(cap_info)

        context_logger.debug(
            f"Found {len(decoupling_caps)} decoupling capacitors",
            component="NET_TIE"
        )

        return decoupling_caps

    def _is_capacitor(self, comp: Component) -> bool:
        """Check if component is a capacitor."""
        return "Device:C" in comp.symbol or comp.symbol.endswith(":C")

    def _is_decoupling_value(self, value: Optional[str]) -> bool:
        """
        Check if capacitor value is in typical decoupling range.

        Args:
            value: Capacitor value string (e.g., "100nF", "0.1uF", "10uF")

        Returns:
            True if value is in decoupling range
        """
        if not value:
            return False

        # Parse value to farads
        try:
            cap_farads = self._parse_capacitance(value)
            return (
                self.config.min_decoupling_cap <= cap_farads <= self.config.max_decoupling_cap
            )
        except ValueError:
            # Can't parse value, be conservative and assume it might be decoupling
            context_logger.warning(
                f"Could not parse capacitor value: {value}",
                component="NET_TIE"
            )
            return True

    def _parse_capacitance(self, value: str) -> float:
        """
        Parse capacitance value string to farads.

        Args:
            value: Capacitor value string (e.g., "100nF", "0.1uF", "10uF")

        Returns:
            Capacitance in farads

        Raises:
            ValueError: If value cannot be parsed
        """
        value = value.strip().upper()

        # Extract numeric part and unit
        import re
        match = re.match(r'([\d.]+)\s*([A-Z]*)', value)
        if not match:
            raise ValueError(f"Cannot parse capacitance: {value}")

        numeric = float(match.group(1))
        unit = match.group(2)

        # Convert to farads
        multipliers = {
            'F': 1,
            'UF': 1e-6,
            'µF': 1e-6,
            'NF': 1e-9,
            'PF': 1e-12,
        }

        multiplier = multipliers.get(unit, 1e-6)  # Default to uF if no unit
        return numeric * multiplier

    def _analyze_capacitor_connections(self, cap: Component) -> Optional[Dict[str, Any]]:
        """
        Analyze a capacitor's connections to determine if it's a decoupling cap.

        Args:
            cap: Capacitor component to analyze

        Returns:
            Dict with 'component', 'power_net', 'gnd_net', 'power_pin' if it's a
            decoupling cap, None otherwise
        """
        # Get the two pins
        pins = list(cap._pins.values())
        if len(pins) != 2:
            return None

        pin1, pin2 = pins

        # Get nets they're connected to
        net1 = pin1._net if hasattr(pin1, '_net') else None
        net2 = pin2._net if hasattr(pin2, '_net') else None

        if not net1 or not net2:
            return None

        # Check if one is power and one is ground
        power_net, gnd_net = None, None

        if self._is_power_net(net1) and self._is_ground_net(net2):
            power_net, gnd_net = net1, net2
        elif self._is_ground_net(net1) and self._is_power_net(net2):
            gnd_net, power_net = net1, net2
        else:
            return None

        # Find which IC power pin this cap is associated with
        power_pin = self._find_associated_power_pin(power_net, cap)

        return {
            'component': cap,
            'power_net': power_net,
            'gnd_net': gnd_net,
            'power_pin': power_pin
        }

    def _is_power_net(self, net: Net) -> bool:
        """Check if a net is a power net."""
        if not net.name:
            return False

        power_patterns = [
            'VCC', 'VDD', 'VEE', 'VSS', 'VBUS', 'VBAT',
            'V3V3', 'V5V', 'V12V', 'V1V8', 'V2V5',
            '+3V3', '+5V', '+12V', '+1V8', '+2V5',
            'VDDA', 'VDDD', 'VDDIO', 'VDDCORE'
        ]

        name_upper = net.name.upper()
        return any(pattern in name_upper for pattern in power_patterns)

    def _is_ground_net(self, net: Net) -> bool:
        """Check if a net is a ground net."""
        if not net.name:
            return False

        ground_patterns = ['GND', 'VSS', 'VSSA', 'AGND', 'DGND']

        name_upper = net.name.upper()
        return any(pattern in name_upper for pattern in ground_patterns)

    def _find_associated_power_pin(
        self,
        power_net: Net,
        cap: Component
    ) -> Optional[Pin]:
        """
        Find which IC power pin this capacitor is decoupling.

        Looks for power pins on the same net that aren't the capacitor itself.

        Args:
            power_net: The power net
            cap: The capacitor component

        Returns:
            The associated IC power pin, or None if not found
        """
        # Get all pins on this power net
        for pin in power_net._pins:
            # Skip pins on the capacitor itself
            if pin.component == cap:
                continue

            # Check if this is a power pin on an IC
            if self._is_ic_power_pin(pin):
                return pin

        return None

    def _is_ic_power_pin(self, pin: Pin) -> bool:
        """
        Check if a pin is an IC power pin.

        Args:
            pin: Pin to check

        Returns:
            True if this appears to be an IC power pin
        """
        comp = pin.component

        # Skip capacitors, resistors, and other passives
        if any(x in comp.symbol for x in ['Device:C', 'Device:R', 'Device:L']):
            return False

        # Check if pin name suggests it's a power pin
        if pin.name:
            name_upper = pin.name.upper()
            power_pin_patterns = [
                'VCC', 'VDD', 'VEE', 'VSS', 'VBUS', 'VBAT',
                'VDDA', 'VDDD', 'VDDIO', 'VDDCORE', 'AVDD', 'DVDD'
            ]
            return any(pattern in name_upper for pattern in power_pin_patterns)

        return False

    def _decouples_component(
        self,
        cap_info: Dict[str, Any],
        target_component: Component
    ) -> bool:
        """
        Check if a capacitor decouples a specific component.

        Args:
            cap_info: Capacitor info dict from _analyze_capacitor_connections
            target_component: Component to check

        Returns:
            True if the cap decouples this component
        """
        power_pin = cap_info['power_pin']

        if not power_pin:
            return False

        return power_pin.component == target_component

    def get_net_tie_groups(self) -> Dict[str, List[str]]:
        """
        Get component groupings defined by net-ties.

        Returns:
            Dict mapping net-tie reference to list of grouped component references
        """
        groups = {}

        for net_tie in self._net_ties:
            if 'groups_with' in net_tie._extra_fields:
                grouped_refs = net_tie._extra_fields['groups_with'].split(',')
                groups[net_tie.ref] = grouped_refs

        return groups
