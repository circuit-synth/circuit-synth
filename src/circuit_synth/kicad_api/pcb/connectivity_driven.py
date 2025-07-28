"""
Connectivity-driven placement algorithm for PCB components.

This algorithm optimizes component placement based on connectivity patterns,
prioritizing highly connected components and critical nets.
"""

import heapq
import logging
import math
from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple

from ..types import Point
from .base import ComponentWrapper, PlacementAlgorithm

logger = logging.getLogger(__name__)


class ConnectivityDrivenPlacer(PlacementAlgorithm):
    """
    Places components based on connectivity patterns.

    This algorithm:
    1. Analyzes connectivity to find highly connected component clusters
    2. Prioritizes placement of critical nets (power, ground, high-speed)
    3. Minimizes total connection length and crossings
    4. Places components in order of connectivity strength
    """

    def __init__(
        self,
        component_spacing: float = 2.0,
        cluster_spacing: float = 5.0,
        critical_net_weight: float = 2.0,
        crossing_penalty: float = 1.5,
    ):
        """
        Initialize the connectivity-driven placer.

        Args:
            component_spacing: Minimum spacing between components in mm
            cluster_spacing: Spacing between component clusters in mm
            critical_net_weight: Weight multiplier for critical nets
            crossing_penalty: Penalty factor for crossing connections
        """
        self.component_spacing = component_spacing
        self.cluster_spacing = cluster_spacing
        self.critical_net_weight = critical_net_weight
        self.crossing_penalty = crossing_penalty

        # Critical net patterns
        self.critical_net_patterns = {
            "power": ["VCC", "VDD", "+5V", "+3V3", "+12V", "PWR"],
            "ground": ["GND", "VSS", "AGND", "DGND", "0V"],
            "high_speed": ["CLK", "CLOCK", "XTAL", "OSC", "USB", "HDMI", "PCIE"],
        }

    def place(
        self,
        components: List[ComponentWrapper],
        connections: List[Tuple[str, str]],
        board_width: float = 100.0,
        board_height: float = 100.0,
    ) -> Dict[str, Point]:
        """
        Place components using connectivity-driven algorithm.

        Args:
            components: List of components to place
            connections: List of (ref1, ref2) tuples representing connections
            board_width: Board width in mm
            board_height: Board height in mm

        Returns:
            Dictionary mapping component references to positions
        """
        if not components:
            return {}

        logger.info(
            f"Starting connectivity-driven placement for {len(components)} components"
        )

        # Build connectivity graph
        connectivity = self._build_connectivity_graph(components, connections)

        # Identify critical nets
        critical_nets = self._identify_critical_nets(components, connections)

        # Find component clusters based on connectivity
        clusters = self._find_clusters(components, connectivity, critical_nets)

        # Calculate placement order based on connectivity strength
        placement_order = self._calculate_placement_order(
            components, connectivity, critical_nets
        )

        # Place components
        positions = {}
        placed_components = set()

        # Place components in order of connectivity strength
        for ref in placement_order:
            component = next((c for c in components if c.reference == ref), None)
            if not component:
                continue

            # Find best position for this component
            if ref in placed_components:
                continue

            position = self._find_best_position(
                component,
                components,
                positions,
                connectivity,
                critical_nets,
                board_width,
                board_height,
            )

            positions[ref] = position
            placed_components.add(ref)

            logger.debug(f"Placed {ref} at ({position.x:.2f}, {position.y:.2f})")

        # Optimize placement to minimize crossings
        positions = self._minimize_crossings(
            positions, connections, board_width, board_height
        )

        logger.info(f"Connectivity-driven placement complete")
        return positions

    def _build_connectivity_graph(
        self, components: List[ComponentWrapper], connections: List[Tuple[str, str]]
    ) -> Dict[str, Dict[str, int]]:
        """Build a graph of component connectivity with connection counts."""
        connectivity = defaultdict(lambda: defaultdict(int))

        for ref1, ref2 in connections:
            connectivity[ref1][ref2] += 1
            connectivity[ref2][ref1] += 1

        return dict(connectivity)

    def _identify_critical_nets(
        self, components: List[ComponentWrapper], connections: List[Tuple[str, str]]
    ) -> Set[Tuple[str, str]]:
        """Identify connections that are part of critical nets."""
        critical_connections = set()

        # For now, use a simple heuristic based on component values and net names
        # In a real implementation, this would use actual net information
        for ref1, ref2 in connections:
            comp1 = next((c for c in components if c.reference == ref1), None)
            comp2 = next((c for c in components if c.reference == ref2), None)

            if comp1 and comp2:
                # Check if either component is likely part of a critical net
                is_critical = False

                # Check component values for critical patterns
                for pattern_type, patterns in self.critical_net_patterns.items():
                    for pattern in patterns:
                        if (
                            pattern in str(comp1.value).upper()
                            or pattern in str(comp2.value).upper()
                        ):
                            is_critical = True
                            break

                # Power components (voltage regulators, etc.)
                if any(
                    ref.startswith(prefix)
                    for prefix in ["U", "VR"]
                    for ref in [ref1, ref2]
                ):
                    if any(
                        val in str(comp1.value).upper() + str(comp2.value).upper()
                        for val in ["REG", "780", "117", "LDO"]
                    ):
                        is_critical = True

                if is_critical:
                    critical_connections.add((ref1, ref2))

        logger.info(f"Identified {len(critical_connections)} critical connections")
        return critical_connections

    def _find_clusters(
        self,
        components: List[ComponentWrapper],
        connectivity: Dict[str, Dict[str, int]],
        critical_nets: Set[Tuple[str, str]],
    ) -> List[Set[str]]:
        """Find clusters of highly connected components."""
        # Simple clustering based on connection strength
        clusters = []
        assigned = set()

        # Start with components that have the most connections
        connection_counts = {
            comp.reference: sum(connectivity.get(comp.reference, {}).values())
            for comp in components
        }

        sorted_refs = sorted(
            connection_counts.keys(), key=lambda x: connection_counts[x], reverse=True
        )

        for ref in sorted_refs:
            if ref in assigned:
                continue

            # Create a new cluster
            cluster = {ref}
            assigned.add(ref)

            # Add strongly connected neighbors
            if ref in connectivity:
                neighbors = sorted(
                    connectivity[ref].items(), key=lambda x: x[1], reverse=True
                )

                for neighbor_ref, count in neighbors:
                    if neighbor_ref not in assigned and count >= 2:
                        cluster.add(neighbor_ref)
                        assigned.add(neighbor_ref)

                        # Also add neighbors of neighbors if strongly connected
                        if neighbor_ref in connectivity:
                            for nn_ref, nn_count in connectivity[neighbor_ref].items():
                                if (
                                    nn_ref not in assigned
                                    and nn_count >= 2
                                    and nn_ref in cluster
                                ):
                                    cluster.add(nn_ref)
                                    assigned.add(nn_ref)

            if len(cluster) > 1:
                clusters.append(cluster)

        # Add single components as individual clusters
        for comp in components:
            if comp.reference not in assigned:
                clusters.append({comp.reference})

        logger.info(f"Found {len(clusters)} component clusters")
        return clusters

    def _calculate_placement_order(
        self,
        components: List[ComponentWrapper],
        connectivity: Dict[str, Dict[str, int]],
        critical_nets: Set[Tuple[str, str]],
    ) -> List[str]:
        """Calculate the order in which to place components."""
        # Score each component based on:
        # 1. Number of connections
        # 2. Number of critical connections
        # 3. Connection strength (multiple connections to same component)

        scores = {}
        for comp in components:
            ref = comp.reference
            score = 0

            # Base score from number of connections
            if ref in connectivity:
                score += len(connectivity[ref]) * 10

                # Add connection strength
                score += sum(connectivity[ref].values()) * 5

                # Bonus for critical connections
                for neighbor_ref in connectivity[ref]:
                    if (ref, neighbor_ref) in critical_nets or (
                        neighbor_ref,
                        ref,
                    ) in critical_nets:
                        score += 20 * self.critical_net_weight

            # Bonus for power-related components
            if ref.startswith("U") or ref.startswith("VR"):
                score += 15
            elif ref.startswith("C"):
                # Capacitors often need to be close to ICs
                score += 5

            scores[ref] = score

        # Sort by score (highest first)
        sorted_refs = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

        logger.debug(f"Placement order scores: {dict(list(scores.items())[:10])}...")
        return sorted_refs

    def _find_best_position(
        self,
        component: ComponentWrapper,
        all_components: List[ComponentWrapper],
        existing_positions: Dict[str, Point],
        connectivity: Dict[str, Dict[str, int]],
        critical_nets: Set[Tuple[str, str]],
        board_width: float,
        board_height: float,
    ) -> Point:
        """Find the best position for a component."""
        ref = component.reference

        # If no components placed yet, start at center
        if not existing_positions:
            return Point(board_width / 2, board_height / 2)

        # Find connected components that are already placed
        connected_refs = []
        if ref in connectivity:
            for neighbor_ref, count in connectivity[ref].items():
                if neighbor_ref in existing_positions:
                    # Weight by connection count and criticality
                    weight = count
                    if (ref, neighbor_ref) in critical_nets or (
                        neighbor_ref,
                        ref,
                    ) in critical_nets:
                        weight *= self.critical_net_weight
                    connected_refs.append((neighbor_ref, weight))

        if not connected_refs:
            # No connected components placed yet, find a spot near existing components
            return self._find_empty_spot(
                component, existing_positions, board_width, board_height
            )

        # Calculate weighted center of connected components
        weighted_x = 0
        weighted_y = 0
        total_weight = 0

        for conn_ref, weight in connected_refs:
            pos = existing_positions[conn_ref]
            weighted_x += pos.x * weight
            weighted_y += pos.y * weight
            total_weight += weight

        if total_weight > 0:
            target_x = weighted_x / total_weight
            target_y = weighted_y / total_weight
        else:
            target_x = board_width / 2
            target_y = board_height / 2

        # Find the closest valid position to the target
        best_pos = self._find_closest_valid_position(
            Point(target_x, target_y),
            component,
            existing_positions,
            board_width,
            board_height,
        )

        return best_pos

    def _find_empty_spot(
        self,
        component: ComponentWrapper,
        existing_positions: Dict[str, Point],
        board_width: float,
        board_height: float,
    ) -> Point:
        """Find an empty spot for a component with no placed connections."""
        # Try positions in a grid pattern
        grid_size = max(self.component_spacing * 2, 5.0)

        # Start from center and spiral outward
        center_x = board_width / 2
        center_y = board_height / 2

        for radius in range(0, int(max(board_width, board_height) / grid_size)):
            for angle in range(0, 360, 45):
                x = center_x + radius * grid_size * math.cos(math.radians(angle))
                y = center_y + radius * grid_size * math.sin(math.radians(angle))

                pos = Point(x, y)
                if self._is_valid_position(
                    pos, component, existing_positions, board_width, board_height
                ):
                    return pos

        # Fallback to corner
        return Point(self.component_spacing, self.component_spacing)

    def _find_closest_valid_position(
        self,
        target: Point,
        component: ComponentWrapper,
        existing_positions: Dict[str, Point],
        board_width: float,
        board_height: float,
    ) -> Point:
        """Find the closest valid position to a target point."""
        # Search in expanding circles around the target
        search_radius = self.component_spacing
        search_step = 1.0  # 1mm steps
        max_radius = max(board_width, board_height)

        while search_radius < max_radius:
            # Try positions in a circle around the target
            num_points = int(2 * math.pi * search_radius / search_step)
            for i in range(num_points):
                angle = 2 * math.pi * i / num_points
                x = target.x + search_radius * math.cos(angle)
                y = target.y + search_radius * math.sin(angle)

                pos = Point(x, y)
                if self._is_valid_position(
                    pos, component, existing_positions, board_width, board_height
                ):
                    return pos

            search_radius += search_step

        # Fallback
        return Point(board_width / 2, board_height / 2)

    def _is_valid_position(
        self,
        pos: Point,
        component: ComponentWrapper,
        existing_positions: Dict[str, Point],
        board_width: float,
        board_height: float,
    ) -> bool:
        """Check if a position is valid for a component."""
        # Check board boundaries
        margin = self.component_spacing
        if (
            pos.x < margin
            or pos.x > board_width - margin
            or pos.y < margin
            or pos.y > board_height - margin
        ):
            return False

        # Check distance from other components
        for ref, other_pos in existing_positions.items():
            distance = math.sqrt(
                (pos.x - other_pos.x) ** 2 + (pos.y - other_pos.y) ** 2
            )
            if distance < self.component_spacing:
                return False

        return True

    def _minimize_crossings(
        self,
        positions: Dict[str, Point],
        connections: List[Tuple[str, str]],
        board_width: float,
        board_height: float,
    ) -> Dict[str, Point]:
        """Optimize placement to minimize connection crossings."""
        # Simple optimization: try swapping nearby components to reduce crossings
        improved = True
        iterations = 0
        max_iterations = 10

        while improved and iterations < max_iterations:
            improved = False
            iterations += 1

            # Calculate current crossing count
            current_crossings = self._count_crossings(positions, connections)

            # Try swapping pairs of components
            refs = list(positions.keys())
            for i in range(len(refs)):
                for j in range(i + 1, len(refs)):
                    ref1, ref2 = refs[i], refs[j]

                    # Only consider swapping nearby components
                    dist = math.sqrt(
                        (positions[ref1].x - positions[ref2].x) ** 2
                        + (positions[ref1].y - positions[ref2].y) ** 2
                    )
                    if dist > self.cluster_spacing * 2:
                        continue

                    # Try swapping
                    positions[ref1], positions[ref2] = positions[ref2], positions[ref1]
                    new_crossings = self._count_crossings(positions, connections)

                    if new_crossings < current_crossings:
                        # Keep the swap
                        current_crossings = new_crossings
                        improved = True
                        logger.debug(
                            f"Swapped {ref1} and {ref2}, crossings: {new_crossings}"
                        )
                    else:
                        # Revert the swap
                        positions[ref1], positions[ref2] = (
                            positions[ref2],
                            positions[ref1],
                        )

        return positions

    def _count_crossings(
        self, positions: Dict[str, Point], connections: List[Tuple[str, str]]
    ) -> int:
        """Count the number of crossing connections."""
        crossings = 0

        for i, (ref1a, ref1b) in enumerate(connections):
            if ref1a not in positions or ref1b not in positions:
                continue

            p1a = positions[ref1a]
            p1b = positions[ref1b]

            for j, (ref2a, ref2b) in enumerate(connections[i + 1 :], i + 1):
                if ref2a not in positions or ref2b not in positions:
                    continue

                p2a = positions[ref2a]
                p2b = positions[ref2b]

                # Check if lines cross
                if self._lines_intersect(p1a, p1b, p2a, p2b):
                    crossings += 1

        return crossings

    def _lines_intersect(self, p1: Point, p2: Point, p3: Point, p4: Point) -> bool:
        """Check if two line segments intersect."""

        def ccw(A, B, C):
            return (C.y - A.y) * (B.x - A.x) > (B.y - A.y) * (C.x - A.x)

        return ccw(p1, p3, p4) != ccw(p2, p3, p4) and ccw(p1, p2, p3) != ccw(p1, p2, p4)
