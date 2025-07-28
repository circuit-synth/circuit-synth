"""
Force-directed placement algorithm for PCB components with proper KiCad Y-axis handling.

This implementation uses a two-level hierarchical approach:
1. Level 1: Optimize component positions within each subcircuit
2. Level 2: Optimize subcircuit group positions relative to each other
3. Level 3: Final collision detection and resolution across all components

CRITICAL: KiCad uses inverted Y axis (Y increases downward)
"""

import logging
import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from ..types import Footprint, Point
from .base import ComponentWrapper, PlacementAlgorithm
from .bbox import BoundingBox
from .courtyard_collision_improved import CourtyardCollisionDetector

logger = logging.getLogger(__name__)


@dataclass
class Force:
    """2D force vector."""

    fx: float
    fy: float

    def __add__(self, other: "Force") -> "Force":
        return Force(self.fx + other.fx, self.fy + other.fy)

    def __mul__(self, scalar: float) -> "Force":
        return Force(self.fx * scalar, self.fy * scalar)

    def magnitude(self) -> float:
        return math.sqrt(self.fx * self.fx + self.fy * self.fy)


@dataclass
class SubcircuitGroup:
    """Group of components belonging to the same subcircuit."""

    path: str
    components: List[Footprint]
    center: Point
    bbox: BoundingBox
    connections_to_other_groups: Dict[str, int]  # group_path -> connection_count


class ForceDirectedPlacement(PlacementAlgorithm):
    """
    Force-directed placement algorithm with proper KiCad Y-axis handling.

    Parameters:
        component_spacing: Minimum spacing between components (mm)
        attraction_strength: Strength of attraction between connected components
        repulsion_strength: Strength of repulsion between all components
        iterations_per_level: Number of iterations for each optimization level
        damping: Damping factor to prevent oscillation (0-1)
        initial_temperature: Initial temperature for simulated annealing
        cooling_rate: Temperature reduction rate per iteration
        enable_rotation: Whether to optimize component rotations
        internal_force_multiplier: Multiplier for forces within subcircuits
    """

    def __init__(
        self,
        component_spacing: float = 2.0,
        attraction_strength: float = 1.5,  # Increased for stronger connections
        repulsion_strength: float = 50.0,
        iterations_per_level: int = 100,
        damping: float = 0.8,
        initial_temperature: float = 10.0,
        cooling_rate: float = 0.95,
        enable_rotation: bool = True,
        internal_force_multiplier: float = 2.0,
    ):

        self.component_spacing = component_spacing
        self.attraction_strength = attraction_strength
        self.repulsion_strength = repulsion_strength
        self.iterations_per_level = iterations_per_level
        self.damping = damping
        self.initial_temperature = initial_temperature
        self.cooling_rate = cooling_rate
        self.enable_rotation = enable_rotation
        self.internal_force_multiplier = internal_force_multiplier

        # Collision detector with reduced spacing for tighter packing
        self.collision_detector = CourtyardCollisionDetector(
            spacing=component_spacing * 0.5
        )

    def place(
        self,
        components: List[ComponentWrapper],
        connections: List[Tuple[str, str]],
        board_width: float = 100.0,
        board_height: float = 100.0,
        **kwargs,
    ) -> Dict[str, Point]:
        """
        Place components using two-level force-directed algorithm.

        Args:
            components: List of components to place
            connections: List of (ref1, ref2) tuples representing connections
            board_width: Board width in mm
            board_height: Board height in mm

        Returns:
            Dictionary mapping component references to positions
        """
        logger.info(
            f"Starting force-directed placement for {len(components)} components"
        )
        logger.info(
            f"Board dimensions: {board_width}x{board_height}mm (Y-axis inverted)"
        )

        # Extract footprints and build connection graph
        footprints = [comp.footprint for comp in components]
        connection_graph = self._build_connection_graph(footprints, connections)

        # Group components by subcircuit
        groups = self._group_by_subcircuit(footprints)
        logger.info(f"Found {len(groups)} subcircuit groups")

        # Board outline (Y-axis: 0 at top, increases downward)
        board_outline = BoundingBox(0, 0, board_width, board_height)

        # Level 1: Optimize within each subcircuit
        logger.info("Level 1: Optimizing component placement within subcircuits")
        for group_path, group in groups.items():
            logger.debug(
                f"Optimizing group {group_path} with {len(group.components)} components"
            )
            self._optimize_subcircuit(group, connection_graph, board_outline)
            self._update_group_properties(group)

        # Level 2: Optimize subcircuit group positions
        if len(groups) > 1:
            logger.info("Level 2: Optimizing subcircuit group positions")
            self._count_inter_group_connections(groups, connection_graph)
            self._optimize_group_positions(groups, board_outline)

        # Level 3: Final collision detection and resolution across all components
        logger.info("Level 3: Final collision detection and resolution")
        all_footprints = []
        for group in groups.values():
            all_footprints.extend(group.components)
        self._enforce_minimum_spacing(all_footprints, connection_graph)

        # Extract final positions
        positions = {}
        for comp in components:
            positions[comp.reference] = comp.footprint.position

        return positions

    def _build_connection_graph(
        self, footprints: List[Footprint], connections: List[Tuple[str, str]]
    ) -> Dict[str, Set[str]]:
        """Build a graph of component connections."""
        graph = {fp.reference: set() for fp in footprints}

        for ref1, ref2 in connections:
            if ref1 in graph and ref2 in graph:
                graph[ref1].add(ref2)
                graph[ref2].add(ref1)

        return graph

    def _group_by_subcircuit(
        self, footprints: List[Footprint]
    ) -> Dict[str, SubcircuitGroup]:
        """Group components by their subcircuit path."""
        groups = {}

        for fp in footprints:
            # Extract subcircuit path from hierarchical path
            path = getattr(fp, "path", "")
            if not path:
                path = "root"  # Components without path go to root

            if path not in groups:
                groups[path] = SubcircuitGroup(
                    path=path,
                    components=[],
                    center=Point(0, 0),
                    bbox=BoundingBox(0, 0, 0, 0),
                    connections_to_other_groups={},
                )

            groups[path].components.append(fp)

        # Initialize group positions
        for group in groups.values():
            self._initialize_group_positions(group)

        return groups

    def _initialize_group_positions(self, group: SubcircuitGroup):
        """Initialize component positions within a group."""
        if not group.components:
            return

        # Place components in a grid initially
        grid_size = math.ceil(math.sqrt(len(group.components)))
        spacing = self.component_spacing * 3  # Initial spacing

        for i, comp in enumerate(group.components):
            row = i // grid_size
            col = i % grid_size
            # Y increases downward in KiCad
            comp.position = Point(col * spacing, row * spacing)

    def _optimize_subcircuit(
        self,
        group: SubcircuitGroup,
        connection_graph: Dict[str, Set[str]],
        board_outline: BoundingBox,
    ):
        """Optimize component positions within a subcircuit using force-directed layout."""
        components = group.components
        if len(components) <= 1:
            return

        # Create a mapping for quick lookup
        comp_dict = {comp.reference: comp for comp in components}

        # Initialize temperature for simulated annealing
        temperature = self.initial_temperature

        # Track convergence
        convergence_threshold = 1.0  # Total displacement threshold
        convergence_count = 0
        convergence_iterations = 15  # Number of stable iterations before stopping

        # Force-directed optimization
        for iteration in range(self.iterations_per_level):
            forces = {}
            total_displacement = 0.0

            # Calculate forces for each component
            for comp in components:
                force = Force(0, 0)

                # Attraction forces from connections
                for connected_ref in connection_graph.get(comp.reference, set()):
                    if connected_ref in comp_dict:
                        connected = comp_dict[connected_ref]
                        force = force + self._calculate_attraction(
                            comp, connected, is_internal=True
                        )

                # Repulsion forces from all other components in group
                for other in components:
                    if other.reference != comp.reference:
                        force = force + self._calculate_repulsion(comp, other)

                # Boundary forces
                force = force + self._calculate_boundary_force(comp, board_outline)

                # Apply damping
                force = force * self.damping

                forces[comp.reference] = force

            # Apply forces with temperature-based movement
            for comp in components:
                force = forces[comp.reference]

                # Limit movement based on temperature
                max_move = temperature * self.component_spacing
                move_x = max(-max_move, min(max_move, force.fx))
                move_y = max(-max_move, min(max_move, force.fy))

                # Update position
                old_pos = comp.position
                comp.position = Point(old_pos.x + move_x, old_pos.y + move_y)

                # Track displacement
                displacement = math.sqrt(move_x**2 + move_y**2)
                total_displacement += displacement

            # Cool down temperature
            temperature *= self.cooling_rate

            # Check for convergence
            if total_displacement < convergence_threshold:
                convergence_count += 1
                if convergence_count >= convergence_iterations:
                    logger.debug(
                        f"Subcircuit converged after {iteration + 1} iterations"
                    )
                    break
            else:
                convergence_count = 0

            # Rotate components if enabled
            if self.enable_rotation and iteration % 10 == 0:
                self._optimize_rotations(components, connection_graph)

    def _optimize_rotations(
        self, components: List[Footprint], connection_graph: Dict[str, Set[str]]
    ):
        """Optimize component rotations to minimize connection distances."""
        comp_dict = {comp.reference: comp for comp in components}

        for comp in components:
            connected_refs = connection_graph.get(comp.reference, set())
            if not connected_refs:
                continue

            # Try different rotations
            best_rotation = comp.rotation
            best_distance = float("inf")

            for rotation in [0, 90, 180, 270]:
                comp.rotation = rotation

                # Calculate total connection distance for this rotation
                total_distance = 0
                for connected_ref in connected_refs:
                    if connected_ref in comp_dict:
                        connected = comp_dict[connected_ref]
                        dx = connected.position.x - comp.position.x
                        dy = connected.position.y - comp.position.y
                        total_distance += math.sqrt(dx * dx + dy * dy)

                if total_distance < best_distance:
                    best_distance = total_distance
                    best_rotation = rotation

            comp.rotation = best_rotation

    def _update_group_properties(self, group: SubcircuitGroup):
        """Update group center and bounding box based on component positions."""
        if not group.components:
            return

        # Calculate center
        sum_x = sum(comp.position.x for comp in group.components)
        sum_y = sum(comp.position.y for comp in group.components)
        group.center = Point(
            sum_x / len(group.components), sum_y / len(group.components)
        )

        # Calculate bounding box
        xs = [comp.position.x for comp in group.components]
        ys = [comp.position.y for comp in group.components]
        margin = self.component_spacing * 2

        group.bbox = BoundingBox(
            min(xs) - margin, min(ys) - margin, max(xs) + margin, max(ys) + margin
        )

    def _count_inter_group_connections(
        self, groups: Dict[str, SubcircuitGroup], connection_graph: Dict[str, Set[str]]
    ):
        """Count connections between different subcircuit groups."""
        # Build reference to group mapping
        ref_to_group = {}
        for group_path, group in groups.items():
            for comp in group.components:
                ref_to_group[comp.reference] = group_path

        # Count connections
        for group_path, group in groups.items():
            group.connections_to_other_groups.clear()

            for comp in group.components:
                for connected_ref in connection_graph.get(comp.reference, set()):
                    connected_group = ref_to_group.get(connected_ref)
                    if connected_group and connected_group != group_path:
                        if connected_group not in group.connections_to_other_groups:
                            group.connections_to_other_groups[connected_group] = 0
                        group.connections_to_other_groups[connected_group] += 1

    def _optimize_group_positions(
        self, groups: Dict[str, SubcircuitGroup], board_outline: BoundingBox
    ):
        """Optimize positions of subcircuit groups relative to each other."""
        if len(groups) <= 1:
            return

        group_list = list(groups.values())
        temperature = self.initial_temperature * 2  # Higher temperature for groups

        for iteration in range(self.iterations_per_level // 2):
            forces = {group.path: Force(0, 0) for group in group_list}

            # Calculate forces between groups
            for i, group1 in enumerate(group_list):
                # Attraction to connected groups
                for (
                    connected_path,
                    connection_count,
                ) in group1.connections_to_other_groups.items():
                    if connected_path in groups:
                        group2 = groups[connected_path]
                        # Stronger attraction for more connections
                        attraction = self._calculate_group_attraction(
                            group1, group2, connection_count
                        )
                        forces[group1.path] = forces[group1.path] + attraction

                # Repulsion from all other groups
                for j, group2 in enumerate(group_list):
                    if i != j:
                        repulsion = self._calculate_group_repulsion(group1, group2)
                        forces[group1.path] = forces[group1.path] + repulsion

                # Boundary forces
                boundary = self._calculate_group_boundary_force(group1, board_outline)
                forces[group1.path] = forces[group1.path] + boundary

            # Apply forces to move groups
            for group in group_list:
                force = forces[group.path] * self.damping

                # Limit movement
                max_move = temperature * self.component_spacing * 2
                move_x = max(-max_move, min(max_move, force.fx))
                move_y = max(-max_move, min(max_move, force.fy))

                # Move all components in the group
                for comp in group.components:
                    comp.position = Point(
                        comp.position.x + move_x, comp.position.y + move_y
                    )

                # Update group properties
                self._update_group_properties(group)

            # Cool down
            temperature *= self.cooling_rate

    def _calculate_attraction(
        self, comp1: Footprint, comp2: Footprint, is_internal: bool = False
    ) -> Force:
        """Calculate attraction force between connected components."""
        dx = comp2.position.x - comp1.position.x
        dy = comp2.position.y - comp1.position.y
        distance = math.sqrt(dx * dx + dy * dy)

        if distance < 0.1:  # Avoid division by zero
            return Force(0, 0)

        # Normalize direction
        dx /= distance
        dy /= distance

        # Calculate force magnitude
        # Stronger attraction for internal connections
        strength = self.attraction_strength
        if is_internal:
            strength *= self.internal_force_multiplier

        # Linear attraction (could also use log or other functions)
        magnitude = strength * distance / self.component_spacing

        # Force direction is toward the other component
        return Force(magnitude * dx, magnitude * dy)

    def _calculate_repulsion(self, comp1: Footprint, comp2: Footprint) -> Force:
        """Calculate repulsion force between components."""
        dx = comp2.position.x - comp1.position.x
        dy = comp2.position.y - comp1.position.y
        distance = math.sqrt(dx * dx + dy * dy)

        if distance < 0.1:  # Avoid division by zero
            # Random repulsion for overlapping components
            import random

            angle = random.uniform(0, 2 * math.pi)
            return Force(
                self.repulsion_strength * math.cos(angle),
                self.repulsion_strength * math.sin(angle),
            )

        # Normalize direction
        dx /= distance
        dy /= distance

        # Calculate force magnitude (inverse square law)
        # Clamp minimum distance to component spacing
        effective_distance = max(distance, self.component_spacing)
        magnitude = (
            self.repulsion_strength * (self.component_spacing / effective_distance) ** 2
        )

        # Repulsion is in opposite direction (away from other component)
        return Force(-magnitude * dx, -magnitude * dy)

    def _calculate_boundary_force(
        self, comp: Footprint, board_outline: BoundingBox
    ) -> Force:
        """Calculate force to keep component within board boundaries."""
        force = Force(0, 0)
        margin = 10.0  # Keep components away from edges
        strength = 10.0

        # Check each boundary
        # Left boundary
        if comp.position.x < board_outline.min_x + margin:
            force.fx += (
                strength * (board_outline.min_x + margin - comp.position.x) / margin
            )

        # Right boundary
        if comp.position.x > board_outline.max_x - margin:
            force.fx -= (
                strength * (comp.position.x - (board_outline.max_x - margin)) / margin
            )

        # Top boundary (Y=0 is at top in KiCad)
        if comp.position.y < board_outline.min_y + margin:
            force.fy += (
                strength * (board_outline.min_y + margin - comp.position.y) / margin
            )

        # Bottom boundary (Y increases downward)
        if comp.position.y > board_outline.max_y - margin:
            force.fy -= (
                strength * (comp.position.y - (board_outline.max_y - margin)) / margin
            )

        return force

    def _calculate_group_attraction(
        self, group1: SubcircuitGroup, group2: SubcircuitGroup, connection_count: int
    ) -> Force:
        """Calculate attraction between connected groups."""
        dx = group2.center.x - group1.center.x
        dy = group2.center.y - group1.center.y
        distance = math.sqrt(dx * dx + dy * dy)

        if distance < 0.1:
            return Force(0, 0)

        # Normalize
        dx /= distance
        dy /= distance

        # Stronger attraction for more connections
        magnitude = (
            self.attraction_strength * math.log(connection_count + 1) * distance / 50.0
        )

        return Force(magnitude * dx, magnitude * dy)

    def _calculate_group_repulsion(
        self, group1: SubcircuitGroup, group2: SubcircuitGroup
    ) -> Force:
        """Calculate repulsion between groups."""
        dx = group2.center.x - group1.center.x
        dy = group2.center.y - group1.center.y
        distance = math.sqrt(dx * dx + dy * dy)

        if distance < 0.1:
            import random

            angle = random.uniform(0, 2 * math.pi)
            return Force(
                self.repulsion_strength * 2 * math.cos(angle),
                self.repulsion_strength * 2 * math.sin(angle),
            )

        # Consider group sizes
        size1 = math.sqrt(
            (group1.bbox.max_x - group1.bbox.min_x)
            * (group1.bbox.max_y - group1.bbox.min_y)
        )
        size2 = math.sqrt(
            (group2.bbox.max_x - group2.bbox.min_x)
            * (group2.bbox.max_y - group2.bbox.min_y)
        )
        min_distance = (size1 + size2) / 2 + self.component_spacing * 2

        # Normalize
        dx /= distance
        dy /= distance

        # Stronger repulsion when groups are too close
        effective_distance = max(distance, min_distance)
        magnitude = (
            self.repulsion_strength * 2 * (min_distance / effective_distance) ** 2
        )

        return Force(-magnitude * dx, -magnitude * dy)

    def _calculate_group_boundary_force(
        self, group: SubcircuitGroup, board_outline: BoundingBox
    ) -> Force:
        """Calculate force to keep group within board boundaries."""
        force = Force(0, 0)
        strength = 20.0

        # Check each boundary
        if group.bbox.min_x < board_outline.min_x:
            force.fx += strength * (board_outline.min_x - group.bbox.min_x)

        if group.bbox.max_x > board_outline.max_x:
            force.fx -= strength * (group.bbox.max_x - board_outline.max_x)

        if group.bbox.min_y < board_outline.min_y:
            force.fy += strength * (board_outline.min_y - group.bbox.min_y)

        if group.bbox.max_y > board_outline.max_y:
            force.fy -= strength * (group.bbox.max_y - board_outline.max_y)

        return force

    def _enforce_minimum_spacing(
        self, footprints: List[Footprint], connection_graph: Dict[str, Set[str]]
    ):
        """
        Enforce minimum spacing between all components with connectivity awareness.
        Uses a two-pass approach:
        1. First pass: Gentle connectivity-aware collision resolution
        2. Second pass: Strict collision resolution if needed
        """
        max_iterations = 50

        # Build connectivity info
        connectivity = self._build_connectivity_from_graph(footprints, connection_graph)

        # First pass: Gentle connectivity-aware resolution
        logger.info("First pass: Connectivity-aware collision resolution")
        for iteration in range(max_iterations // 2):
            collisions = self.collision_detector.detect_collisions(footprints)
            if not collisions:
                logger.info(f"No collisions detected after {iteration + 1} iterations")
                return

            logger.debug(
                f"Iteration {iteration + 1}: Found {len(collisions)} collisions"
            )

            # Resolve collisions with connectivity awareness
            resolved = self._connectivity_aware_collision_resolution(
                footprints, collisions, connectivity, gentle=True
            )

            if resolved == 0:
                logger.warning("No collisions resolved in this iteration")
                break

        # Second pass: Strict resolution if collisions remain
        remaining_collisions = self.collision_detector.detect_collisions(footprints)
        if remaining_collisions:
            logger.info(
                f"Second pass: Strict collision resolution for {len(remaining_collisions)} remaining collisions"
            )

            for iteration in range(max_iterations // 2):
                collisions = self.collision_detector.detect_collisions(footprints)
                if not collisions:
                    logger.info(
                        f"All collisions resolved after {iteration + 1} strict iterations"
                    )
                    return

                # Use stronger forces for persistent collisions
                resolved = self._connectivity_aware_collision_resolution(
                    footprints, collisions, connectivity, gentle=False
                )

                if resolved == 0:
                    logger.warning("Cannot resolve remaining collisions")
                    break

        # Log final collision status
        final_collisions = self.collision_detector.detect_collisions(footprints)
        if final_collisions:
            logger.warning(f"Failed to resolve {len(final_collisions)} collisions:")
            for fp1, fp2 in final_collisions[:5]:  # Show first 5
                logger.warning(f"  - {fp1.reference} <-> {fp2.reference}")

    def _build_connectivity_from_graph(
        self, footprints: List[Footprint], connection_graph: Dict[str, Set[str]]
    ) -> Dict[str, Set[str]]:
        """Build connectivity map from connection graph."""
        connectivity = {}

        for fp in footprints:
            ref = fp.reference
            connectivity[ref] = connection_graph.get(ref, set())

        return connectivity

    def _connectivity_aware_collision_resolution(
        self,
        footprints: List[Footprint],
        collisions: List[Tuple[Footprint, Footprint]],
        connectivity: Dict[str, Set[str]],
        gentle: bool = True,
    ) -> int:
        """
        Resolve collisions with awareness of component connectivity.

        Args:
            footprints: All footprints
            collisions: List of collision pairs
            connectivity: Map of component reference to connected components
            gentle: If True, use gentler forces for connected components

        Returns:
            Number of collisions resolved
        """
        resolved_count = 0

        for fp1, fp2 in collisions:
            # Check if components are connected
            are_connected = fp2.reference in connectivity.get(
                fp1.reference, set()
            ) or fp1.reference in connectivity.get(fp2.reference, set())

            # Calculate separation vector
            dx = fp2.position.x - fp1.position.x
            dy = fp2.position.y - fp1.position.y
            distance = math.sqrt(dx * dx + dy * dy)

            if distance < 0.1:
                # Components are on top of each other, use random separation
                import random

                angle = random.uniform(0, 2 * math.pi)
                dx = math.cos(angle)
                dy = math.sin(angle)
                distance = 1.0
            else:
                # Normalize
                dx /= distance
                dy /= distance

            # Determine force multiplier based on connectivity
            if gentle:
                if are_connected:
                    # Very gentle push for connected components
                    force_multiplier = 0.1
                else:
                    # Moderate push for unconnected components
                    force_multiplier = 0.3
            else:
                # Strict mode: stronger forces
                if are_connected:
                    force_multiplier = 0.3
                else:
                    force_multiplier = 0.6

            # Calculate push distance
            push_distance = self.component_spacing * force_multiplier

            # Apply symmetric push
            fp1.position = Point(
                fp1.position.x - dx * push_distance, fp1.position.y - dy * push_distance
            )
            fp2.position = Point(
                fp2.position.x + dx * push_distance, fp2.position.y + dy * push_distance
            )

            resolved_count += 1

            # Log resolution
            if are_connected:
                logger.debug(
                    f"Gently separating connected components {fp1.reference} and {fp2.reference}"
                )
            else:
                logger.debug(
                    f"Separating unconnected components {fp1.reference} and {fp2.reference}"
                )

        return resolved_count
