"""
Canonical form classes for KiCad synchronization.

This module provides data structures and conversion methods for representing
circuits in a canonical form that enables robust component matching between
Python Circuit objects and KiCad schematics.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from ..core.circuit import Circuit

logger = logging.getLogger(__name__)


@dataclass
class CanonicalConnection:
    """
    Represents a single connection in canonical form.

    This is the fundamental unit of the canonical representation, describing
    one pin of one component connected to one net.

    Attributes:
        component_index: Order of component in circuit (0-based)
        pin: Pin number or name (e.g., "1", "2", "A", "K")
        net_name: Name of the connected net (e.g., "VCC", "GND", "VOUT")
        component_type: Type and value in format "symbol:value" (e.g., "R:1k", "C:100nF")
    """

    component_index: int
    pin: str
    net_name: str
    component_type: str

    def __repr__(self) -> str:
        """Compact representation for debugging."""
        return f"({self.component_index},'{self.pin}','{self.net_name}','{self.component_type}')"


class CanonicalCircuit:
    """
    Represents a complete circuit in canonical form.

    A canonical circuit is an ordered list of connections that uniquely
    identifies the circuit topology independent of component references
    or net names.
    """

    def __init__(self, connections: List[CanonicalConnection]):
        """
        Initialize a canonical circuit from a list of connections.

        Args:
            connections: List of CanonicalConnection objects
        """
        self.connections = connections
        self._components = self._group_by_component()

    def _group_by_component(self) -> Dict[int, List[CanonicalConnection]]:
        """
        Group connections by component index.

        Returns:
            Dictionary mapping component index to list of its connections
        """
        components = {}
        for conn in self.connections:
            if conn.component_index not in components:
                components[conn.component_index] = []
            components[conn.component_index].append(conn)
        return components

    @property
    def components(self) -> Dict[int, List[CanonicalConnection]]:
        """Get connections grouped by component."""
        return self._components

    @property
    def component_count(self) -> int:
        """Get the number of components in the circuit."""
        return len(self._components)

    @classmethod
    def from_circuit(cls, circuit) -> "CanonicalCircuit":
        """
        Convert a Circuit object to canonical form.
        Handles both circuit_synth.core.circuit.Circuit and netlist_importer.Circuit objects.

        Args:
            circuit: Circuit object to convert (either type)

        Returns:
            CanonicalCircuit representation
        """
        connections = []
        component_idx = 0

        # Check if this is a netlist_importer Circuit (has 'root' attribute)
        if hasattr(circuit, "root"):
            # This is a Circuit from netlist_importer - process hierarchically
            logger.debug("Processing netlist_importer Circuit object")
            cls._process_subcircuit_recursive(circuit.root, connections, component_idx)
        else:
            # This is a circuit_synth.core.circuit.Circuit - process flat
            logger.debug("Processing circuit_synth.core.circuit.Circuit object")
            # Process components in the order they appear in the circuit
            for idx, component in enumerate(circuit.components):
                # Determine component type in symbol:value format
                # Handle both circuit_synth components (with 'symbol' attr) and SchematicSymbol objects (with 'lib_id' attr)
                if hasattr(component, "symbol"):
                    # This is a circuit_synth component
                    symbol = (
                        component.symbol.split(":")[-1]
                        if ":" in component.symbol
                        else component.symbol
                    )
                elif hasattr(component, "lib_id"):
                    # This is a SchematicSymbol from schematic reader
                    symbol = (
                        component.lib_id.split(":")[-1]
                        if ":" in component.lib_id
                        else component.lib_id
                    )
                else:
                    logger.warning(f"Unknown component type: {type(component)}")
                    symbol = "unknown"

                # For both types, value is stored in the value field
                value = component.value if component.value else ""
                component_type = f"{symbol}:{value}"

                # Process each pin connection
                if hasattr(component, "__iter__"):
                    # This is a circuit_synth component (iterable)
                    for pin in component:
                        if pin.net:
                            conn = CanonicalConnection(
                                component_index=idx,
                                pin=str(pin.num),
                                net_name=pin.net.name,
                                component_type=component_type,
                            )
                            connections.append(conn)
                            logger.debug(f"Added connection: {conn}")
                elif hasattr(component, "pins"):
                    # This is a SchematicSymbol (has pins attribute)
                    for pin in component.pins:
                        if (
                            pin.net_name
                        ):  # SchematicPin has net_name instead of pin.net.name
                            conn = CanonicalConnection(
                                component_index=idx,
                                pin=str(
                                    pin.number
                                ),  # SchematicPin has number instead of num
                                net_name=pin.net_name,
                                component_type=component_type,
                            )
                            connections.append(conn)
                            logger.debug(f"Added connection: {conn}")
                else:
                    logger.warning(
                        f"Component {component} has no pins or is not iterable"
                    )

        logger.info(f"Created canonical form with {len(connections)} connections")

        return cls(connections)

    @classmethod
    def _process_subcircuit_recursive(
        cls, subcircuit, connections: List[CanonicalConnection], component_idx_ref: int
    ) -> int:
        """
        Recursively process a subcircuit from netlist_importer to extract connections.

        Args:
            subcircuit: Subcircuit object from netlist_importer
            connections: List to append connections to
            component_idx_ref: Current component index (modified in place)

        Returns:
            Updated component index
        """
        # Process components in this subcircuit
        for component in subcircuit.components.values():
            # Determine component type
            symbol = (
                component.symbol.split(":")[-1]
                if ":" in component.symbol
                else component.symbol
            )
            value = component.value or ""
            component_type = f"{symbol}:{value}"

            # Process nets for this component
            for net_name, net in subcircuit.nets.items():
                for node in net.nodes:
                    if node.component_ref == component.reference:
                        conn = CanonicalConnection(
                            component_index=component_idx_ref,
                            pin=str(node.pin_number),
                            net_name=net_name,
                            component_type=component_type,
                        )
                        connections.append(conn)
                        logger.debug(f"Added connection from netlist: {conn}")

            component_idx_ref += 1

        # Recursively process child subcircuits
        for child in subcircuit.children.values():
            component_idx_ref = cls._process_subcircuit_recursive(
                child, connections, component_idx_ref
            )

        return component_idx_ref

    @classmethod
    def from_kicad(cls, schematic_data: Dict[str, Any]) -> "CanonicalCircuit":
        """
        Convert a KiCad schematic to canonical form.

        Args:
            schematic_data: Parsed KiCad schematic data (S-expression as dict/list)

        Returns:
            CanonicalCircuit representation
        """
        connections = []
        component_index = 0

        # Build a map of component UUID to net connections
        # First, we need to extract wire connections to build net associations
        net_connections = cls._extract_net_connections(schematic_data)

        # Extract all symbol components from the schematic
        symbols = cls._extract_symbols(schematic_data)

        # Process each symbol to create canonical connections
        for symbol in symbols:
            # Skip power symbols and other non-component elements
            if cls._is_power_symbol(symbol):
                logger.debug(
                    f"Skipping power symbol: {symbol.get('lib_id', 'unknown')}"
                )
                continue

            # Extract component properties
            properties = cls._extract_properties(symbol)
            reference = properties.get("Reference", "")
            value = properties.get("Value", "")

            if not reference or not value:
                logger.debug(f"Skipping symbol without reference or value")
                continue

            # Get the symbol library info
            lib_id = symbol.get("lib_id", "")
            if not lib_id:
                logger.debug(f"Skipping symbol {reference} without lib_id")
                continue

            # Extract symbol type from lib_id (e.g., "Device:R" -> "R")
            symbol_type = lib_id.split(":")[-1] if ":" in lib_id else lib_id

            # Create component type in "symbol:value" format
            component_type = f"{symbol_type}:{value}"

            # Get the component UUID
            comp_uuid = symbol.get("uuid", "")

            # Process each pin of the component
            # In KiCad schematics, pin connections are determined by wires connecting to the symbol
            pin_connections = cls._get_pin_connections(
                symbol, comp_uuid, net_connections
            )

            for pin_num, net_name in pin_connections.items():
                conn = CanonicalConnection(
                    component_index=component_index,
                    pin=str(pin_num),
                    net_name=net_name,
                    component_type=component_type,
                )
                connections.append(conn)
                logger.debug(f"Added connection: {conn}")

            # Only increment component index if we added connections
            if pin_connections:
                component_index += 1

        logger.info(
            f"Created canonical form with {len(connections)} connections "
            f"from {component_index} components"
        )

        return cls(connections)

    @staticmethod
    def _extract_symbols(schematic_data: Any) -> List[Dict[str, Any]]:
        """Extract all symbol elements from the schematic data."""
        symbols = []

        if isinstance(schematic_data, list):
            for item in schematic_data:
                if isinstance(item, list) and len(item) > 0:
                    # Check if this is a symbol element
                    if str(item[0]) == "symbol":
                        # Convert S-expression to dict-like structure
                        symbol_dict = CanonicalCircuit._parse_symbol(item)
                        if symbol_dict:
                            symbols.append(symbol_dict)
                    # Recursively search for symbols in nested structures
                    symbols.extend(CanonicalCircuit._extract_symbols(item))

        return symbols

    @staticmethod
    def _parse_symbol(symbol_expr: List) -> Dict[str, Any]:
        """Parse a symbol S-expression into a dictionary."""
        symbol_dict = {}

        # Extract basic attributes
        for item in symbol_expr[1:]:  # Skip 'symbol' token
            if isinstance(item, list) and len(item) >= 2:
                key = str(item[0])
                if key == "lib_id" and len(item) > 1:
                    symbol_dict["lib_id"] = str(item[1])
                elif key == "uuid" and len(item) > 1:
                    symbol_dict["uuid"] = str(item[1])
                elif key == "property":
                    # Properties have format: (property "name" "value" ...)
                    if len(item) >= 3:
                        prop_name = str(item[1]).strip('"')
                        prop_value = str(item[2]).strip('"')
                        if "properties" not in symbol_dict:
                            symbol_dict["properties"] = {}
                        symbol_dict["properties"][prop_name] = prop_value

        return symbol_dict

    @staticmethod
    def _extract_properties(symbol: Dict[str, Any]) -> Dict[str, str]:
        """Extract properties from a symbol."""
        return symbol.get("properties", {})

    @staticmethod
    def _is_power_symbol(symbol: Dict[str, Any]) -> bool:
        """Check if a symbol is a power symbol (reference starts with #PWR)."""
        properties = symbol.get("properties", {})
        reference = properties.get("Reference", "")
        return reference.startswith("#PWR")

    @staticmethod
    def _extract_net_connections(schematic_data: Any) -> Dict[str, str]:
        """
        Extract net connections from wire data.
        Returns a map of point coordinates to net names.
        """
        net_map = {}
        wires = []
        labels = []

        # Extract wires and labels
        if isinstance(schematic_data, list):
            CanonicalCircuit._extract_wires_and_labels(schematic_data, wires, labels)

        # Build net connectivity from wires
        # This is a simplified version - in reality, you'd need to trace
        # connected wire segments to determine complete nets

        # For now, we'll use labels to assign net names
        for label in labels:
            if "at" in label and "text" in label:
                x, y = label["at"]
                net_name = label["text"]
                # Store the position with the net name
                net_map[f"{x},{y}"] = net_name

        return net_map

    @staticmethod
    def _extract_wires_and_labels(data: Any, wires: List, labels: List) -> None:
        """Recursively extract wire and label elements."""
        if isinstance(data, list):
            for item in data:
                if isinstance(item, list) and len(item) > 0:
                    element_type = str(item[0])

                    if element_type == "wire":
                        wire_dict = CanonicalCircuit._parse_wire(item)
                        if wire_dict:
                            wires.append(wire_dict)

                    elif element_type == "label":
                        label_dict = CanonicalCircuit._parse_label(item)
                        if label_dict:
                            labels.append(label_dict)

                    # Recurse into nested structures
                    CanonicalCircuit._extract_wires_and_labels(item, wires, labels)

    @staticmethod
    def _parse_wire(wire_expr: List) -> Dict[str, Any]:
        """Parse a wire S-expression."""
        wire_dict = {}

        for item in wire_expr[1:]:
            if isinstance(item, list) and len(item) >= 2:
                key = str(item[0])
                if key == "pts" and len(item) > 1:
                    # Parse points
                    points = []
                    for pt in item[1:]:
                        if isinstance(pt, list) and str(pt[0]) == "xy" and len(pt) >= 3:
                            x = float(pt[1])
                            y = float(pt[2])
                            points.append((x, y))
                    wire_dict["points"] = points
                elif key == "uuid":
                    wire_dict["uuid"] = str(item[1])

        return wire_dict

    @staticmethod
    def _parse_label(label_expr: List) -> Dict[str, Any]:
        """Parse a label S-expression."""
        label_dict = {}

        for item in label_expr[1:]:
            if isinstance(item, list) and len(item) >= 2:
                key = str(item[0])
                if key == "at" and len(item) >= 3:
                    x = float(item[1])
                    y = float(item[2])
                    label_dict["at"] = (x, y)
                elif key == "uuid":
                    label_dict["uuid"] = str(item[1])
            elif isinstance(item, str):
                # The text content of the label
                label_dict["text"] = item.strip('"')

        return label_dict

    @staticmethod
    def _get_pin_connections(
        symbol: Dict[str, Any], comp_uuid: str, net_connections: Dict[str, str]
    ) -> Dict[str, str]:
        """
        Get pin connections for a component.

        In a real implementation, this would trace wires from symbol pins
        to determine net connections. For now, we'll create a simplified version.
        """
        pin_connections = {}

        # In KiCad, components typically have standard pin numbers
        # For a basic implementation, we'll assume 2-pin components
        # and assign generic net names

        lib_id = symbol.get("lib_id", "")
        properties = symbol.get("properties", {})
        reference = properties.get("Reference", "")

        # Simple heuristic based on component type
        if "R" in lib_id or reference.startswith("R"):
            # Resistor - 2 pins
            pin_connections["1"] = f"Net_{reference}_1"
            pin_connections["2"] = f"Net_{reference}_2"
        elif "C" in lib_id or reference.startswith("C"):
            # Capacitor - 2 pins
            pin_connections["1"] = f"Net_{reference}_1"
            pin_connections["2"] = f"Net_{reference}_2"
        elif "L" in lib_id or reference.startswith("L"):
            # Inductor - 2 pins
            pin_connections["1"] = f"Net_{reference}_1"
            pin_connections["2"] = f"Net_{reference}_2"
        elif "D" in lib_id or reference.startswith("D"):
            # Diode - 2 pins (A, K)
            pin_connections["A"] = f"Net_{reference}_A"
            pin_connections["K"] = f"Net_{reference}_K"
        elif "Q" in lib_id or reference.startswith("Q"):
            # Transistor - 3 pins
            pin_connections["1"] = f"Net_{reference}_1"
            pin_connections["2"] = f"Net_{reference}_2"
            pin_connections["3"] = f"Net_{reference}_3"

        # TODO: In a real implementation, you would:
        # 1. Get the symbol's position and pin locations
        # 2. Find wires that connect to those pin locations
        # 3. Trace the wires to determine the actual net names
        # 4. Handle hierarchical sheets and net naming

        return pin_connections

    def get_component_type(self, component_index: int) -> Optional[str]:
        """
        Get the type of a component by its index.

        Args:
            component_index: Index of the component

        Returns:
            Component type string or None if not found
        """
        if component_index in self._components:
            # All connections for a component have the same type
            return self._components[component_index][0].component_type
        return None

    def get_component_nets(self, component_index: int) -> List[Tuple[str, str]]:
        """
        Get all nets connected to a component.

        Args:
            component_index: Index of the component

        Returns:
            List of (pin, net_name) tuples
        """
        if component_index not in self._components:
            return []

        return [(conn.pin, conn.net_name) for conn in self._components[component_index]]

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"CanonicalCircuit({self.component_count} components, {len(self.connections)} connections)"

    def __str__(self) -> str:
        """Detailed string representation."""
        lines = [f"Canonical Circuit with {self.component_count} components:"]
        for idx in sorted(self._components.keys()):
            comp_type = self.get_component_type(idx)
            lines.append(f"  Component {idx} ({comp_type}):")
            for conn in self._components[idx]:
                lines.append(f"    Pin {conn.pin} -> {conn.net_name}")
        return "\n".join(lines)


class CircuitMatcher:
    """
    Matches components between two canonical circuits.

    This class implements the matching algorithm that identifies corresponding
    components between an old circuit (e.g., from KiCad) and a new circuit
    (e.g., from Python), enabling synchronization while preserving manual work.
    """

    def __init__(self):
        """Initialize the circuit matcher."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def match(
        self, old_circuit: CanonicalCircuit, new_circuit: CanonicalCircuit
    ) -> Dict[int, int]:
        """
        Match components between two canonical circuits.

        Args:
            old_circuit: The existing circuit (e.g., from KiCad)
            new_circuit: The new circuit (e.g., from Python)

        Returns:
            Dictionary mapping old component index to new component index.
            Returns -1 for components that have no match.
        """
        self.logger.info(
            f"Starting component matching: {old_circuit.component_count} old components, "
            f"{new_circuit.component_count} new components"
        )

        # Initialize the mapping with -1 (no match) for all old components
        matches: Dict[int, int] = {idx: -1 for idx in old_circuit.components.keys()}

        # Group components by type in both circuits
        old_by_type = self._group_components_by_type(old_circuit)
        new_by_type = self._group_components_by_type(new_circuit)

        # Track which new components have been matched
        matched_new_components = set()

        # Process each component type
        for component_type, old_indices in old_by_type.items():
            new_indices = new_by_type.get(component_type, [])

            self.logger.debug(
                f"Processing type '{component_type}': "
                f"{len(old_indices)} old, {len(new_indices)} new"
            )

            if not new_indices:
                # No components of this type in new circuit
                self.logger.debug(
                    f"No new components of type '{component_type}' - skipping"
                )
                continue

            if len(old_indices) == 1 and len(new_indices) == 1:
                # Simple case: exactly one component of this type in both circuits
                old_idx = old_indices[0]
                new_idx = new_indices[0]
                matches[old_idx] = new_idx
                matched_new_components.add(new_idx)
                self.logger.debug(
                    f"Direct match for single '{component_type}': "
                    f"old[{old_idx}] -> new[{new_idx}]"
                )
            else:
                # Multiple components of same type - use connectivity pattern matching
                self._match_by_connectivity(
                    old_circuit,
                    new_circuit,
                    old_indices,
                    new_indices,
                    matches,
                    matched_new_components,
                    component_type,
                )

        # Log summary of matching results
        matched_count = sum(1 for v in matches.values() if v != -1)
        self.logger.info(
            f"Matching complete: {matched_count}/{len(matches)} components matched"
        )

        # Log unmatched components for debugging
        unmatched_old = [idx for idx, match in matches.items() if match == -1]
        if unmatched_old:
            self.logger.warning(f"Unmatched old components: {unmatched_old}")

        unmatched_new = [
            idx
            for idx in new_circuit.components.keys()
            if idx not in matched_new_components
        ]
        if unmatched_new:
            self.logger.info(f"New components to be added: {unmatched_new}")

        return matches

    def _group_components_by_type(
        self, circuit: CanonicalCircuit
    ) -> Dict[str, List[int]]:
        """
        Group component indices by their type.

        Args:
            circuit: The canonical circuit to process

        Returns:
            Dictionary mapping component type to list of component indices
        """
        type_groups: Dict[str, List[int]] = {}

        for idx in circuit.components.keys():
            comp_type = circuit.get_component_type(idx)
            if comp_type:
                if comp_type not in type_groups:
                    type_groups[comp_type] = []
                type_groups[comp_type].append(idx)

        return type_groups

    def _match_by_connectivity(
        self,
        old_circuit: CanonicalCircuit,
        new_circuit: CanonicalCircuit,
        old_indices: List[int],
        new_indices: List[int],
        matches: Dict[int, int],
        matched_new_components: set,
        component_type: str,
    ) -> None:
        """
        Match components of the same type using connectivity patterns.

        This method updates the matches dictionary in-place.

        Args:
            old_circuit: The old canonical circuit
            new_circuit: The new canonical circuit
            old_indices: Indices of old components of this type
            new_indices: Indices of new components of this type
            matches: Dictionary to update with matches
            matched_new_components: Set to track matched new components
            component_type: The component type being matched
        """
        self.logger.debug(
            f"Matching {len(old_indices)} old '{component_type}' components "
            f"with {len(new_indices)} new ones using connectivity"
        )

        # Calculate connectivity scores between all pairs
        scores: List[Tuple[int, int, float]] = []

        for old_idx in old_indices:
            for new_idx in new_indices:
                if new_idx in matched_new_components:
                    continue  # Skip already matched components

                score = self._calculate_connectivity_score(
                    old_circuit, new_circuit, old_idx, new_idx
                )
                scores.append((old_idx, new_idx, score))
                self.logger.debug(
                    f"Connectivity score: old[{old_idx}] <-> new[{new_idx}] = {score:.3f}"
                )

        # Sort by score (highest first) and match greedily
        scores.sort(key=lambda x: x[2], reverse=True)

        for old_idx, new_idx, score in scores:
            # Skip if either component is already matched
            if matches[old_idx] != -1 or new_idx in matched_new_components:
                continue

            # Only match if score is above threshold
            if score > 0.0:  # Could adjust threshold if needed
                matches[old_idx] = new_idx
                matched_new_components.add(new_idx)
                self.logger.debug(
                    f"Matched '{component_type}': old[{old_idx}] -> new[{new_idx}] "
                    f"(score: {score:.3f})"
                )

    def _calculate_connectivity_score(
        self,
        old_circuit: CanonicalCircuit,
        new_circuit: CanonicalCircuit,
        old_idx: int,
        new_idx: int,
    ) -> float:
        """
        Calculate a connectivity score between two components.

        The score indicates how similar the connection patterns are between
        the two components. A higher score means a better match.

        Args:
            old_circuit: The old canonical circuit
            new_circuit: The new canonical circuit
            old_idx: Index of component in old circuit
            new_idx: Index of component in new circuit

        Returns:
            Score between 0.0 and 1.0, where 1.0 is a perfect match
        """
        old_nets = old_circuit.get_component_nets(old_idx)
        new_nets = new_circuit.get_component_nets(new_idx)

        if not old_nets or not new_nets:
            return 0.0

        # Create pin-to-net mappings
        old_pin_nets = {pin: net for pin, net in old_nets}
        new_pin_nets = {pin: net for pin, net in new_nets}

        # Check if pin counts match
        if len(old_pin_nets) != len(new_pin_nets):
            # Different number of pins - penalize but don't disqualify
            pin_count_penalty = 0.5
        else:
            pin_count_penalty = 1.0

        # Calculate matches based on pin-to-net connections
        matching_connections = 0
        total_pins = max(len(old_pin_nets), len(new_pin_nets))

        # Check if the actual net connections match
        for pin, old_net in old_pin_nets.items():
            if pin in new_pin_nets:
                new_net = new_pin_nets[pin]
                # Use strict net name matching - exact match only
                if old_net == new_net:
                    matching_connections += 1
                else:
                    # Different nets on same pin - this is a connection change!
                    # Give a small score to indicate same pin exists but different net
                    matching_connections += 0.1

        # Calculate final score
        if total_pins > 0:
            score = (matching_connections / total_pins) * pin_count_penalty
        else:
            score = 0.0

        return min(score, 1.0)  # Ensure score doesn't exceed 1.0
