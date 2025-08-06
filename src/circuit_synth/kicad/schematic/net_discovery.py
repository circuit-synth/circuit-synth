"""
Net discovery and analysis for KiCad schematics.

This module provides functionality for discovering nets, analyzing their
structure, and suggesting improvements to net organization.
"""

import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from ..core.types import (
    Junction,
    Label,
    LabelType,
    Net,
    Point,
    Schematic,
    SchematicSymbol,
    Wire,
)
from .connection_tracer import ConnectionTracer, NetTrace

logger = logging.getLogger(__name__)


@dataclass
class NetInfo:
    """Information about a discovered net."""

    name: str
    component_pins: List[Tuple[str, str]]  # (component_ref, pin)
    wire_count: int
    label_count: int
    junction_count: int
    total_length: float
    is_power: bool
    is_ground: bool
    is_bus: bool
    bus_members: List[str] = field(default_factory=list)
    hierarchical_scope: str = "local"  # "local", "global", "hierarchical"


@dataclass
class BusNet:
    """Represents a bus (collection of related nets)."""

    name: str
    member_nets: List[str]
    width: int

    @property
    def is_valid(self) -> bool:
        """Check if bus has valid syntax."""
        return bool(re.match(r"^[A-Za-z_]\w*\[\d+:\d+\]$", self.name))

    def get_member_name(self, index: int) -> str:
        """Get the name of a specific bus member."""
        base_name = self.name.split("[")[0]
        return f"{base_name}[{index}]"


@dataclass
class ConnectivityReport:
    """Report on schematic connectivity."""

    total_nets: int
    connected_nets: int
    floating_nets: int
    power_nets: List[str]
    ground_nets: List[str]
    bus_nets: List[BusNet]
    unconnected_pins: Dict[str, List[str]]  # component_ref -> [pins]
    suggested_net_names: Dict[str, str]  # current -> suggested
    connectivity_score: float  # 0-100


@dataclass
class NetStatistics:
    """Statistics about nets in the schematic."""

    total_count: int
    named_count: int
    unnamed_count: int
    power_count: int
    ground_count: int
    bus_count: int
    average_fanout: float
    max_fanout: int
    most_connected_net: Optional[str]
    longest_net: Optional[str]
    shortest_net: Optional[str]


class NetDiscovery:
    """
    Discovers and analyzes nets in a schematic.

    This class provides functionality to:
    - Discover all nets in a schematic
    - Identify bus nets
    - Find floating and unconnected nets
    - Suggest net names
    - Analyze connectivity
    """

    def __init__(self, schematic: Schematic):
        """
        Initialize net discovery.

        Args:
            schematic: The schematic to analyze
        """
        self.schematic = schematic
        self.tracer = ConnectionTracer(schematic)
        self._net_cache = {}

    def discover_all_nets(self) -> List[NetInfo]:
        """
        Discover all nets in the schematic.

        Returns:
            List of discovered nets with information
        """
        discovered_nets = {}
        processed_nodes = set()

        # Start from all labels
        for label in self.schematic.labels:
            if label.uuid in processed_nodes:
                continue

            trace = self.tracer.trace_net(label.text)
            if trace.nodes:
                net_info = self._create_net_info(trace)
                discovered_nets[net_info.name] = net_info

                # Mark nodes as processed
                for node in trace.nodes:
                    for elem_uuid in node.connected_elements:
                        processed_nodes.add(elem_uuid)

        # Find unnamed nets (connected wires without labels)
        unnamed_index = 1
        for wire in self.schematic.wires:
            if wire.uuid in processed_nodes:
                continue

            # Trace from wire start point
            trace = self.tracer.trace_net(wire.points[0])
            if trace.nodes and not trace.net_name:
                # Unnamed net
                net_name = f"Net_{unnamed_index}"
                unnamed_index += 1

                trace.net_name = net_name
                net_info = self._create_net_info(trace)
                discovered_nets[net_name] = net_info

                # Mark nodes as processed
                for node in trace.nodes:
                    for elem_uuid in node.connected_elements:
                        processed_nodes.add(elem_uuid)

        return list(discovered_nets.values())

    def _create_net_info(self, trace: NetTrace) -> NetInfo:
        """Create NetInfo from a net trace."""
        # Count elements
        wire_count = sum(1 for edge in trace.edges if edge.wire_uuid)
        label_count = sum(1 for node in trace.nodes if node.node_type == "label")
        junction_count = sum(1 for node in trace.nodes if node.node_type == "junction")

        # Extract component pins
        component_pins = [
            (pin.component_ref, pin.pin_number) for pin in trace.component_pins
        ]

        # Determine net type
        is_power = self._is_power_net(trace.net_name)
        is_ground = self._is_ground_net(trace.net_name)
        is_bus = self._is_bus_net(trace.net_name)

        # Determine scope
        scope = "local"
        for node in trace.nodes:
            if node.node_type == "label":
                # Check label type from schematic
                for label in self.schematic.labels:
                    if label.position == node.position:
                        if label.label_type == LabelType.GLOBAL:
                            scope = "global"
                        elif label.label_type == LabelType.HIERARCHICAL:
                            scope = "hierarchical"
                        break

        return NetInfo(
            name=trace.net_name,
            component_pins=component_pins,
            wire_count=wire_count,
            label_count=label_count,
            junction_count=junction_count,
            total_length=trace.total_length,
            is_power=is_power,
            is_ground=is_ground,
            is_bus=is_bus,
            hierarchical_scope=scope,
        )

    def _is_power_net(self, net_name: str) -> bool:
        """Check if net is a power net."""
        power_patterns = [
            r"^VCC",
            r"^VDD",
            r"^V\+",
            r"^\+\d+V",
            r"^\+\d+\.\d+V",
            r"^VBAT",
            r"^VBUS",
            r"^VIN",
            r"^VOUT",
        ]
        return any(re.match(pattern, net_name) for pattern in power_patterns)

    def _is_ground_net(self, net_name: str) -> bool:
        """Check if net is a ground net."""
        ground_patterns = [
            r"^GND",
            r"^VSS",
            r"^AGND",
            r"^DGND",
            r"^PGND",
            r"^V-",
            r"^-\d+V",
            r"^0V",
        ]
        return any(re.match(pattern, net_name) for pattern in ground_patterns)

    def _is_bus_net(self, net_name: str) -> bool:
        """Check if net is a bus."""
        return bool(re.match(r"^[A-Za-z_]\w*\[\d+:\d+\]$", net_name))

    def merge_net_aliases(self, nets: List[NetInfo]) -> List[NetInfo]:
        """
        Merge nets that are aliases (connected through labels).

        Args:
            nets: List of discovered nets

        Returns:
            List of merged nets
        """
        # Group nets by connectivity
        net_groups = []
        processed = set()

        for net in nets:
            if net.name in processed:
                continue

            # Find all connected nets
            group = [net]
            processed.add(net.name)

            # Check for nets sharing component pins
            for other_net in nets:
                if other_net.name in processed:
                    continue

                # Check for shared pins
                shared_pins = set(net.component_pins) & set(other_net.component_pins)
                if shared_pins:
                    group.append(other_net)
                    processed.add(other_net.name)

            net_groups.append(group)

        # Merge groups
        merged_nets = []
        for group in net_groups:
            if len(group) == 1:
                merged_nets.append(group[0])
            else:
                # Merge into primary net (prefer named over unnamed)
                primary = sorted(
                    group, key=lambda n: (n.name.startswith("Net_"), n.name)
                )[0]

                # Combine information
                for net in group[1:]:
                    primary.component_pins.extend(net.component_pins)
                    primary.wire_count += net.wire_count
                    primary.label_count += net.label_count
                    primary.junction_count += net.junction_count
                    primary.total_length += net.total_length

                # Remove duplicates
                primary.component_pins = list(set(primary.component_pins))

                merged_nets.append(primary)

        return merged_nets

    def identify_bus_nets(self) -> List[BusNet]:
        """Identify and parse bus nets."""
        bus_nets = []
        bus_pattern = re.compile(r"^([A-Za-z_]\w*)\[(\d+):(\d+)\]$")

        # Find bus labels
        for label in self.schematic.labels:
            match = bus_pattern.match(label.text)
            if match:
                base_name = match.group(1)
                start_idx = int(match.group(2))
                end_idx = int(match.group(3))

                # Create bus net
                width = abs(end_idx - start_idx) + 1
                member_nets = []

                # Generate member names
                if start_idx < end_idx:
                    for i in range(start_idx, end_idx + 1):
                        member_nets.append(f"{base_name}[{i}]")
                else:
                    for i in range(start_idx, end_idx - 1, -1):
                        member_nets.append(f"{base_name}[{i}]")

                bus = BusNet(name=label.text, member_nets=member_nets, width=width)
                bus_nets.append(bus)

        return bus_nets

    def find_floating_nets(self) -> List[NetInfo]:
        """Find nets that don't connect to any components."""
        floating = []

        all_nets = self.discover_all_nets()
        for net in all_nets:
            if not net.component_pins:
                floating.append(net)

        return floating

    def analyze_net_connectivity(self) -> ConnectivityReport:
        """Analyze overall net connectivity."""
        all_nets = self.discover_all_nets()
        merged_nets = self.merge_net_aliases(all_nets)

        # Categorize nets
        connected_nets = []
        floating_nets = []
        power_nets = []
        ground_nets = []

        for net in merged_nets:
            if net.component_pins:
                connected_nets.append(net)
            else:
                floating_nets.append(net)

            if net.is_power:
                power_nets.append(net.name)
            if net.is_ground:
                ground_nets.append(net.name)

        # Find buses
        bus_nets = self.identify_bus_nets()

        # Find unconnected pins (simplified)
        unconnected_pins = {}
        for component in self.schematic.components:
            # Check if component has any connections
            has_connection = False
            for net in connected_nets:
                for comp_ref, pin in net.component_pins:
                    if comp_ref == component.reference:
                        has_connection = True
                        break
                if has_connection:
                    break

            if not has_connection:
                unconnected_pins[component.reference] = ["all"]

        # Suggest net names
        suggested_names = self.suggest_net_names(
            [n for n in merged_nets if n.name.startswith("Net_")]
        )

        # Calculate connectivity score
        total_components = len(self.schematic.components)
        connected_components = total_components - len(unconnected_pins)
        connectivity_score = (
            (connected_components / total_components * 100)
            if total_components > 0
            else 0
        )

        return ConnectivityReport(
            total_nets=len(merged_nets),
            connected_nets=len(connected_nets),
            floating_nets=len(floating_nets),
            power_nets=power_nets,
            ground_nets=ground_nets,
            bus_nets=bus_nets,
            unconnected_pins=unconnected_pins,
            suggested_net_names=suggested_names,
            connectivity_score=connectivity_score,
        )

    def suggest_net_names(self, unnamed_nets: List[NetInfo]) -> Dict[str, str]:
        """
        Suggest meaningful names for unnamed nets.

        Args:
            unnamed_nets: List of nets without meaningful names

        Returns:
            Dictionary mapping current names to suggested names
        """
        suggestions = {}

        for net in unnamed_nets:
            if not net.component_pins:
                continue

            # Analyze connected components
            component_types = defaultdict(list)
            for comp_ref, pin in net.component_pins:
                # Extract component type from reference
                comp_type = re.match(r"^([A-Z]+)", comp_ref)
                if comp_type:
                    component_types[comp_type.group(1)].append((comp_ref, pin))

            # Generate name based on connections
            if len(component_types) == 1:
                # Single component type
                comp_type = list(component_types.keys())[0]
                refs = [ref for ref, _ in component_types[comp_type]]

                if comp_type == "R":
                    suggestions[net.name] = f"R_NET_{min(refs)}"
                elif comp_type == "C":
                    suggestions[net.name] = f"C_NET_{min(refs)}"
                elif comp_type == "U":
                    suggestions[net.name] = f"IC_NET_{min(refs)}"
                else:
                    suggestions[net.name] = f"{comp_type}_NET_{min(refs)}"

            elif len(component_types) == 2:
                # Two component types - might be a specific function
                types = sorted(component_types.keys())

                if "R" in types and "C" in types:
                    suggestions[net.name] = "RC_FILTER"
                elif "R" in types and "U" in types:
                    suggestions[net.name] = (
                        "PULLUP" if len(component_types["R"]) == 1 else "RESISTOR_NET"
                    )
                elif "C" in types and "U" in types:
                    suggestions[net.name] = (
                        "BYPASS" if len(component_types["C"]) == 1 else "CAPACITOR_NET"
                    )
                else:
                    suggestions[net.name] = f"{types[0]}_{types[1]}_NET"

            else:
                # Multiple component types
                suggestions[net.name] = f"SIGNAL_{len(net.component_pins)}"

        return suggestions

    def get_net_statistics(self) -> NetStatistics:
        """Get statistics about all nets."""
        all_nets = self.discover_all_nets()
        merged_nets = self.merge_net_aliases(all_nets)

        if not merged_nets:
            return NetStatistics(
                total_count=0,
                named_count=0,
                unnamed_count=0,
                power_count=0,
                ground_count=0,
                bus_count=0,
                average_fanout=0.0,
                max_fanout=0,
                most_connected_net=None,
                longest_net=None,
                shortest_net=None,
            )

        # Count net types
        named_count = sum(1 for net in merged_nets if not net.name.startswith("Net_"))
        unnamed_count = len(merged_nets) - named_count
        power_count = sum(1 for net in merged_nets if net.is_power)
        ground_count = sum(1 for net in merged_nets if net.is_ground)
        bus_count = sum(1 for net in merged_nets if net.is_bus)

        # Calculate fanout statistics
        fanouts = [len(net.component_pins) for net in merged_nets]
        average_fanout = sum(fanouts) / len(fanouts) if fanouts else 0.0
        max_fanout = max(fanouts) if fanouts else 0

        # Find extremes
        most_connected = max(
            merged_nets, key=lambda n: len(n.component_pins), default=None
        )
        longest = max(merged_nets, key=lambda n: n.total_length, default=None)
        shortest = min(
            merged_nets,
            key=lambda n: n.total_length if n.total_length > 0 else float("inf"),
            default=None,
        )

        return NetStatistics(
            total_count=len(merged_nets),
            named_count=named_count,
            unnamed_count=unnamed_count,
            power_count=power_count,
            ground_count=ground_count,
            bus_count=bus_count,
            average_fanout=average_fanout,
            max_fanout=max_fanout,
            most_connected_net=most_connected.name if most_connected else None,
            longest_net=longest.name if longest else None,
            shortest_net=shortest.name if shortest else None,
        )


class HierarchicalNetDiscovery(NetDiscovery):
    """Extended net discovery for hierarchical designs."""

    def __init__(
        self, root_schematic: Schematic, sheet_schematics: Dict[str, Schematic]
    ):
        """
        Initialize hierarchical net discovery.

        Args:
            root_schematic: The root schematic
            sheet_schematics: Dictionary of sheet filename to schematic
        """
        super().__init__(root_schematic)
        self.sheet_schematics = sheet_schematics

    def discover_hierarchical_nets(self) -> Dict[str, List[NetInfo]]:
        """
        Discover nets across hierarchical sheets.

        Returns:
            Dictionary mapping sheet names to their nets
        """
        hierarchical_nets = {"root": self.discover_all_nets()}

        for sheet_name, sheet_schematic in self.sheet_schematics.items():
            discovery = NetDiscovery(sheet_schematic)
            hierarchical_nets[sheet_name] = discovery.discover_all_nets()

        return hierarchical_nets

    def trace_hierarchical_net(self, net_name: str) -> Dict[str, NetTrace]:
        """
        Trace a net across hierarchy.

        Args:
            net_name: Name of the net to trace

        Returns:
            Dictionary mapping sheet names to net traces
        """
        traces = {}

        # Trace in root
        root_trace = self.tracer.trace_net(net_name)
        if root_trace.nodes:
            traces["root"] = root_trace

        # Trace in sheets
        for sheet_name, sheet_schematic in self.sheet_schematics.items():
            tracer = ConnectionTracer(sheet_schematic)
            sheet_trace = tracer.trace_net(net_name)
            if sheet_trace.nodes:
                traces[sheet_name] = sheet_trace

        return traces
