"""
Force-directed placement algorithm for PCB components with two-level hierarchy.

This module implements a force-directed placement algorithm that respects the
hierarchical structure of circuits:
- Level 1: Force-directed placement within each subcircuit
- Level 2: Force-directed placement of subcircuit groups

The algorithm uses:
- Attraction forces between connected components
- Repulsion forces between all components
- Stronger internal forces within subcircuits
- Courtyard-based collision detection
"""

import logging
import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from circuit_synth.kicad_api.pcb.placement.base import (
    ComponentWrapper,
    PlacementAlgorithm,
)
from circuit_synth.kicad_api.pcb.placement.bbox import BoundingBox
from circuit_synth.kicad_api.pcb.placement.courtyard_collision import (
    CourtyardCollisionDetector,
    Polygon,
)
from circuit_synth.kicad_api.pcb.types import Footprint, Point

logger = logging.getLogger(__name__)


@dataclass
class Force:
    """Represents a 2D force vector."""

    fx: float
    fy: float

    def __add__(self, other: "Force") -> "Force":
        return Force(self.fx + other.fx, self.fy + other.fy)

    def __mul__(self, scalar: float) -> "Force":
        return Force(self.fx * scalar, self.fy * scalar)

    def magnitude(self) -> float:
        return math.sqrt(self.fx * self.fx + self.fy * self.fy)

    def normalize(self) -> "Force":
        mag = self.magnitude()
        if mag > 0:
            return Force(self.fx / mag, self.fy / mag)
        return Force(0, 0)


@dataclass
class SubcircuitGroup:
    """Represents a group of components in the same subcircuit."""

    path: str
    components: List[Footprint]
    center: Point
    bbox: BoundingBox
    connections_to_other_groups: Dict[str, int]  # group_path -> connection_count


class ForceDirectedPlacement(PlacementAlgorithm):
    """
    Two-level force-directed placement algorithm.

    Parameters:
        component_spacing: Minimum spacing between components (mm)
        attraction_strength: Strength of attraction between connected components
        repulsion_strength: Strength of repulsion between all components
        internal_force_multiplier: Multiplier for forces within subcircuits
        iterations_per_level: Number of iterations for each optimization level
        damping: Damping factor to prevent oscillations (0-1)
        use_courtyard: Use courtyard geometry for collision detection
        initial_temperature: Initial temperature for simulated annealing (default: 10.0)
        cooling_rate: Temperature reduction factor per iteration (default: 0.95)
    """

    def __init__(
        self,
        component_spacing: float = 5.0,
        attraction_strength: float = 0.8,
        repulsion_strength: float = 15.0,
        internal_force_multiplier: float = 2.0,
        iterations_per_level: int = 100,
        damping: float = 0.85,
        use_courtyard: bool = True,
        initial_temperature: float = 10.0,
        cooling_rate: float = 0.95,
        enable_rotation: bool = True,
    ):
        self.component_spacing = component_spacing
        self.attraction_strength = (
            attraction_strength * 1.5
        )  # Increase attraction to keep connected components closer
        self.repulsion_strength = repulsion_strength
        self.internal_force_multiplier = internal_force_multiplier
        self.iterations_per_level = iterations_per_level
        self.damping = damping
        self.use_courtyard = use_courtyard
        self.initial_temperature = initial_temperature
        self.cooling_rate = cooling_rate
        self.enable_rotation = enable_rotation
        # Use smaller spacing for collision detection to avoid being too aggressive
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

        # Extract footprints and build connection graph
        footprints = [comp.footprint for comp in components]
        connection_graph = self._build_connection_graph(footprints, connections)

        # Group components by subcircuit
        groups = self._group_by_subcircuit(footprints)
        logger.info(f"Found {len(groups)} subcircuit groups")

        # Board outline
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
        self._enforce_minimum_spacing(all_footprints)

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

            # Calculate average angle to connected components
            angles = []
            for connected_ref in connected_refs:
                if connected_ref in comp_dict:
                    connected = comp_dict[connected_ref]
                    dx = connected.position.x - comp.position.x
                    dy = connected.position.y - comp.position.y
                    angle = math.atan2(dy, dx)
                    angles.append(angle)

            if angles:
                # Try different rotations and pick the best
                best_rotation = comp.rotation
                best_score = float("inf")

                for rotation in [0, 90, 180, 270]:
                    # Calculate score (sum of connection distances)
                    score = 0
                    for connected_ref in connected_refs:
                        if connected_ref in comp_dict:
                            connected = comp_dict[connected_ref]
                            # Simple distance calculation
                            dx = connected.position.x - comp.position.x
                            dy = connected.position.y - comp.position.y
                            score += math.sqrt(dx * dx + dy * dy)

                    if score < best_score:
                        best_score = score
                        best_rotation = rotation

                comp.rotation = best_rotation

    def _update_group_properties(self, group: SubcircuitGroup):
        """Update group center and bounding box based on component positions."""
        if not group.components:
            return

        # Calculate bounding box
        min_x = min(comp.position.x for comp in group.components)
        max_x = max(comp.position.x for comp in group.components)
        min_y = min(comp.position.y for comp in group.components)
        max_y = max(comp.position.y for comp in group.components)

        # Add component dimensions to bbox
        for comp in group.components:
            # Approximate component size (should use actual footprint dimensions)
            size = self.component_spacing
            min_x = min(min_x, comp.position.x - size / 2)
            max_x = max(max_x, comp.position.x + size / 2)
            min_y = min(min_y, comp.position.y - size / 2)
            max_y = max(max_y, comp.position.y + size / 2)

        group.bbox = BoundingBox(min_x, min_y, max_x, max_y)
        group.center = Point((min_x + max_x) / 2, (min_y + max_y) / 2)

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
        """Optimize positions of subcircuit groups."""
        group_list = list(groups.values())
        if len(group_list) <= 1:
            return

        # Initialize temperature
        temperature = self.initial_temperature * 2  # Higher initial temp for groups

        # Force-directed optimization for groups
        for iteration in range(
            self.iterations_per_level // 2
        ):  # Fewer iterations for groups
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

        # Repulsion is in opposite direction
        return Force(-magnitude * dx, -magnitude * dy)

    def _calculate_boundary_force(
        self, comp: Footprint, board_outline: BoundingBox
    ) -> Force:
        """Calculate force to keep component within board boundaries."""
        force = Force(0, 0)
        margin = 10.0  # Keep components away from edges
        strength = 10.0

        # Check each boundary
        if comp.position.x < board_outline.min_x + margin:
            force.fx += (
                strength * (board_outline.min_x + margin - comp.position.x) / margin
            )

        if comp.position.x > board_outline.max_x - margin:
            force.fx += (
                strength * (board_outline.max_x - margin - comp.position.x) / margin
            )

        if comp.position.y < board_outline.min_y + margin:
            force.fy += (
                strength * (board_outline.min_y + margin - comp.position.y) / margin
            )

        if comp.position.y > board_outline.max_y - margin:
            force.fy += (
                strength * (board_outline.max_y - margin - comp.position.y) / margin
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
            self.attraction_strength * math.log(connection_count + 1) * distance / 50
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
        size1 = max(
            group1.bbox.max_x - group1.bbox.min_x, group1.bbox.max_y - group1.bbox.min_y
        )
        size2 = max(
            group2.bbox.max_x - group2.bbox.min_x, group2.bbox.max_y - group2.bbox.min_y
        )
        min_distance = (size1 + size2) / 2 + self.component_spacing * 2

        # Normalize
        dx /= distance
        dy /= distance

        # Repulsion magnitude
        if distance < min_distance:
            magnitude = self.repulsion_strength * 2 * (min_distance / distance) ** 2
        else:
            magnitude = 0

        return Force(-magnitude * dx, -magnitude * dy)

    def _calculate_group_boundary_force(
        self, group: SubcircuitGroup, board_outline: BoundingBox
    ) -> Force:
        """Calculate force to keep group within board boundaries."""
        force = Force(0, 0)
        margin = 15.0
        strength = 20.0

        # Check group bounding box against board
        if group.bbox.min_x < board_outline.min_x + margin:
            force.fx += strength * (board_outline.min_x + margin - group.bbox.min_x)

        if group.bbox.max_x > board_outline.max_x - margin:
            force.fx += strength * (board_outline.max_x - margin - group.bbox.max_x)

        if group.bbox.min_y < board_outline.min_y + margin:
            force.fy += strength * (board_outline.min_y + margin - group.bbox.min_y)

        if group.bbox.max_y > board_outline.max_y - margin:
            force.fy += strength * (board_outline.max_y - margin - group.bbox.max_y)

        return force

    def _enforce_minimum_spacing(
        self, components: List[Footprint], max_iterations: int = 20
    ):
        """
        Enforce minimum spacing between components with connectivity awareness.

        Args:
            components: List of footprints to check
            max_iterations: Maximum number of iterations to resolve collisions
        """
        logger.debug(f"Enforcing minimum spacing for {len(components)} components")

        # Build connectivity map from board nets
        connectivity = self._build_connectivity_from_board(components)

        # First pass: gentle connectivity-aware resolution
        self._connectivity_aware_collision_resolution(
            components, connectivity, max_iterations // 2
        )

        # Second pass: strict collision resolution if needed
        for iteration in range(max_iterations // 2):
            # Sort components by position to optimize collision checking
            sorted_comps = sorted(
                components, key=lambda c: (c.position.x, c.position.y)
            )

            collision_count = 0
            separation_count = 0

            # Check each pair and separate if too close
            for i, comp1 in enumerate(sorted_comps):
                for j in range(i + 1, len(sorted_comps)):
                    comp2 = sorted_comps[j]

                    # Skip if x distance is already large enough
                    if comp2.position.x - comp1.position.x > self.component_spacing * 3:
                        break

                    # Check if components are colliding or too close
                    if self.collision_detector.check_collision(comp1, comp2):
                        collision_count += 1

                        # Calculate separation vector
                        dx = comp2.position.x - comp1.position.x
                        dy = comp2.position.y - comp1.position.y
                        distance = math.sqrt(dx * dx + dy * dy)

                        if distance < 0.1:  # Nearly overlapping
                            # Push apart in random direction
                            import random

                            angle = random.uniform(0, 2 * math.pi)
                            dx = math.cos(angle)
                            dy = math.sin(angle)
                            distance = 1.0

                        # Normalize direction
                        dx /= distance
                        dy /= distance

                        # Very gentle separation
                        margin_factor = 1.1
                        required_separation = self.component_spacing * margin_factor

                        # Move components apart equally
                        move_distance = (required_separation - distance) / 2

                        # Limit maximum move distance
                        max_move = self.component_spacing * 0.3
                        move_distance = min(move_distance, max_move)

                        if move_distance > 0:
                            comp1.position = Point(
                                comp1.position.x - dx * move_distance,
                                comp1.position.y - dy * move_distance,
                            )
                            comp2.position = Point(
                                comp2.position.x + dx * move_distance,
                                comp2.position.y + dy * move_distance,
                            )

                            separation_count += 1

            if collision_count == 0:
                logger.info(
                    f"All collisions resolved after {iteration + 1} strict iterations"
                )
                break
            else:
                logger.warning(
                    f"Strict iteration {iteration + 1}: Found {collision_count} collisions, separated {separation_count} component pairs"
                )

                if iteration == max_iterations // 2 - 1:
                    logger.error(
                        f"Failed to resolve all collisions! {collision_count} collisions remain."
                    )

    def _build_connectivity_from_board(
        self, components: List[Footprint]
    ) -> Dict[str, Set[str]]:
        """Build connectivity map from board nets."""
        connectivity = {comp.reference: set() for comp in components}

        # Access board through the first component
        if components and hasattr(components[0], "parent_board"):
            board = components[0].parent_board
            if hasattr(board, "nets"):
                for net in board.nets.values():
                    if net.name and net.name != "":  # Skip empty nets
                        connected_refs = []
                        for pad in net.pads:
                            if (
                                hasattr(pad, "parent")
                                and pad.parent.reference in connectivity
                            ):
                                connected_refs.append(pad.parent.reference)

                        # Mark all pairs as connected
                        for i in range(len(connected_refs)):
                            for j in range(i + 1, len(connected_refs)):
                                connectivity[connected_refs[i]].add(connected_refs[j])
                                connectivity[connected_refs[j]].add(connected_refs[i])

        return connectivity

    def _connectivity_aware_collision_resolution(
        self,
        components: List[Footprint],
        connectivity: Dict[str, Set[str]],
        max_iterations: int,
    ):
        """Resolve collisions while considering connectivity between components."""
        logger.info("Starting connectivity-aware collision resolution")

        for iteration in range(max_iterations):
            moves = {}  # Accumulate moves
            collision_count = 0

            # Check all pairs of components
            for i in range(len(components)):
                for j in range(i + 1, len(components)):
                    comp1 = components[i]
                    comp2 = components[j]

                    # Check for collision
                    if self.collision_detector.check_collision(comp1, comp2):
                        collision_count += 1

                        # Calculate separation vector
                        dx = comp2.position.x - comp1.position.x
                        dy = comp2.position.y - comp1.position.y
                        dist = math.sqrt(dx**2 + dy**2)

                        if dist < 0.01:  # Components are at same position
                            import random

                            angle = random.uniform(0, 2 * math.pi)
                            dx = math.cos(angle)
                            dy = math.sin(angle)
                            dist = 1.0

                        # Normalize direction
                        dx /= dist
                        dy /= dist

                        # Check if components are connected
                        are_connected = comp2.reference in connectivity.get(
                            comp1.reference, set()
                        )

                        # Adjust separation force based on connectivity
                        if are_connected:
                            # Very gentle separation for connected components
                            force_multiplier = 0.1
                            margin = 1.05  # Minimal margin
                        else:
                            # Normal separation for unconnected components
                            force_multiplier = 0.3
                            margin = 1.15

                        required_separation = self.component_spacing * margin
                        move_dist = (required_separation - dist) * force_multiplier

                        if move_dist > 0:
                            # Accumulate moves
                            move_x = dx * move_dist / 2
                            move_y = dy * move_dist / 2

                            if comp1.reference not in moves:
                                moves[comp1.reference] = [0, 0]
                            if comp2.reference not in moves:
                                moves[comp2.reference] = [0, 0]

                            moves[comp1.reference][0] -= move_x
                            moves[comp1.reference][1] -= move_y
                            moves[comp2.reference][0] += move_x
                            moves[comp2.reference][1] += move_y

            # Apply accumulated moves
            for comp in components:
                if comp.reference in moves:
                    move_x, move_y = moves[comp.reference]
                    comp.position = Point(
                        comp.position.x + move_x, comp.position.y + move_y
                    )

            if collision_count == 0:
                logger.info(
                    f"Connectivity-aware resolution complete after {iteration + 1} iterations"
                )
                break
            else:
                logger.debug(
                    f"Connectivity iteration {iteration + 1}: {collision_count} collisions found"
                )
