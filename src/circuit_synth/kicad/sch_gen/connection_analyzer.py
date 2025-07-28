# -*- coding: utf-8 -*-
#
# connection_analyzer.py
#
# Analyzes electrical connections between components to support connection-aware placement
#

import logging
from collections import defaultdict
from typing import Dict, List, Set, Tuple

logger = logging.getLogger(__name__)


class ConnectionAnalyzer:
    """
    Analyzes connections between components from circuit nets.
    Provides connection counts, connection strengths, and component grouping.
    """

    def __init__(self):
        # Connection count: component_ref -> count of connections
        self.connection_counts: Dict[str, int] = defaultdict(int)

        # Connection matrix: (comp1_ref, comp2_ref) -> connection count
        # Always stored with comp1_ref < comp2_ref alphabetically
        self.connection_matrix: Dict[Tuple[str, str], int] = defaultdict(int)

        # Component groups based on strong connections
        self.component_groups: List[Set[str]] = []

        # Net membership: component_ref -> set of net names
        self.component_nets: Dict[str, Set[str]] = defaultdict(set)

    def analyze_circuit(self, circuit) -> None:
        """
        Analyze connections in a circuit.

        Args:
            circuit: Circuit object with components and nets
        """
        logger.info(f"Analyzing connections for circuit '{circuit.name}'")
        logger.info(f"  Components: {len(circuit.components)}")
        logger.info(f"  Nets: {len(circuit.nets)}")

        # Reset data structures
        self.connection_counts.clear()
        self.connection_matrix.clear()
        self.component_groups.clear()
        self.component_nets.clear()

        # Build connection data from nets
        for net in circuit.nets:
            # Skip power/ground nets for connection analysis (too many connections)
            if self._is_power_net(net.name):
                logger.debug(f"Skipping power net: {net.name}")
                continue

            # Get all component references in this net
            comp_refs = [conn[0] for conn in net.connections]

            # Update component net membership
            for comp_ref in comp_refs:
                self.component_nets[comp_ref].add(net.name)

            # Count connections for each component
            for comp_ref in comp_refs:
                # Each net adds (n-1) connections for a component where n is the number of components in the net
                self.connection_counts[comp_ref] += len(comp_refs) - 1

            # Build connection matrix (pairwise connections)
            for i in range(len(comp_refs)):
                for j in range(i + 1, len(comp_refs)):
                    comp1, comp2 = sorted([comp_refs[i], comp_refs[j]])
                    self.connection_matrix[(comp1, comp2)] += 1

        # Log connection analysis results
        logger.info("Connection analysis complete:")
        logger.info(
            f"  Total components with connections: {len(self.connection_counts)}"
        )
        logger.info(f"  Total pairwise connections: {len(self.connection_matrix)}")

        # Log top connected components
        sorted_comps = sorted(
            self.connection_counts.items(), key=lambda x: x[1], reverse=True
        )
        logger.info("Top 10 most connected components:")
        for comp_ref, count in sorted_comps[:10]:
            logger.info(f"    {comp_ref}: {count} connections")

        # Identify component groups
        self._identify_groups()

    def _is_power_net(self, net_name: str) -> bool:
        """Check if a net is a power/ground net based on common naming patterns."""
        power_patterns = [
            "VCC",
            "VDD",
            "VSS",
            "GND",
            "GROUND",
            "PWR",
            "+3V3",
            "+5V",
            "+12V",
            "-12V",
            "+1V8",
            "+2V5",
            "VBAT",
            "VBUS",
            "VIN",
            "VOUT",
            "AGND",
            "DGND",
        ]
        net_upper = net_name.upper()
        return any(pattern in net_upper for pattern in power_patterns)

    def _identify_groups(self, min_connections: int = 2) -> None:
        """
        Identify groups of strongly connected components.

        Args:
            min_connections: Minimum number of connections to consider components grouped
        """
        # Use Union-Find algorithm to group components
        parent = {}

        def find(x):
            if x not in parent:
                parent[x] = x
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]

        def union(x, y):
            px, py = find(x), find(y)
            if px != py:
                parent[px] = py

        # Union components with strong connections
        for (comp1, comp2), count in self.connection_matrix.items():
            if count >= min_connections:
                union(comp1, comp2)

        # Collect groups
        groups = defaultdict(set)
        for comp in self.connection_counts:
            root = find(comp)
            groups[root].add(comp)

        # Store groups with more than one component
        self.component_groups = [group for group in groups.values() if len(group) > 1]

        logger.info(f"Identified {len(self.component_groups)} component groups:")
        for i, group in enumerate(self.component_groups):
            logger.info(f"  Group {i+1}: {sorted(group)}")

    def get_connection_count(self, comp_ref: str) -> int:
        """Get the total connection count for a component."""
        return self.connection_counts.get(comp_ref, 0)

    def get_connected_components(self, comp_ref: str) -> List[Tuple[str, int]]:
        """
        Get all components connected to the given component.

        Returns:
            List of (connected_comp_ref, connection_count) tuples
        """
        connected = []
        for (comp1, comp2), count in self.connection_matrix.items():
            if comp1 == comp_ref:
                connected.append((comp2, count))
            elif comp2 == comp_ref:
                connected.append((comp1, count))
        return sorted(connected, key=lambda x: x[1], reverse=True)

    def get_connection_strength(self, comp1_ref: str, comp2_ref: str) -> int:
        """Get the number of connections between two components."""
        comp1, comp2 = sorted([comp1_ref, comp2_ref])
        return self.connection_matrix.get((comp1, comp2), 0)

    def get_component_group(self, comp_ref: str) -> Set[str]:
        """Get the group that contains the given component."""
        for group in self.component_groups:
            if comp_ref in group:
                return group
        return {comp_ref}  # Component is in its own group

    def get_placement_order(self, components) -> List[str]:
        """
        Get the recommended placement order for components.
        Places high-connectivity components first.

        Args:
            components: List of SchematicSymbol objects

        Returns:
            List of component references in placement order
        """
        # Create a list of (ref, connection_count) tuples
        comp_order = []
        for comp in components:
            count = self.get_connection_count(comp.reference)
            comp_order.append((comp.reference, count))

        # Sort by connection count (descending) and then by reference (for stability)
        comp_order.sort(key=lambda x: (-x[1], x[0]))

        # Return just the references
        return [ref for ref, _ in comp_order]

    def calculate_wire_length(
        self, comp_positions: Dict[str, Tuple[float, float]]
    ) -> float:
        """
        Calculate total Manhattan wire length for a given placement.

        Args:
            comp_positions: Dictionary mapping component references to (x, y) positions

        Returns:
            Total wire length in mm
        """
        total_length = 0.0

        for (comp1, comp2), count in self.connection_matrix.items():
            if comp1 in comp_positions and comp2 in comp_positions:
                x1, y1 = comp_positions[comp1]
                x2, y2 = comp_positions[comp2]
                # Manhattan distance
                distance = abs(x2 - x1) + abs(y2 - y1)
                total_length += distance * count

        return total_length
