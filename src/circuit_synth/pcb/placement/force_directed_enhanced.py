"""
Enhanced force-directed placement algorithm for PCB components.

This implementation improves upon the basic force-directed approach with:
- Net connectivity strength based on pin count and net type
- Component functional grouping via hierarchical paths
- Trace length optimization through weighted connections
- Physical constraints (keepouts, board boundaries)
- Multi-phase optimization for better convergence

The algorithm uses a physics-based simulation with:
1. Attraction forces between connected components (spring model)
2. Repulsion forces between all components (electrostatic model)
3. Grouping forces to keep subcircuit components together
4. Boundary forces to keep components within board limits
5. Connection weighting based on net criticality and pin count
"""

import logging
import math
import random
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from ..types import Footprint, Point
from .base import ComponentWrapper, PlacementAlgorithm
from .bbox import BoundingBox
from .courtyard_collision_improved import CourtyardCollisionDetector

logger = logging.getLogger(__name__)


@dataclass
class NetInfo:
    """Information about a net for weighting connections."""

    net_name: str = ""
    pin_count: int = 2
    is_power: bool = False
    is_ground: bool = False
    is_clock: bool = False
    is_high_speed: bool = False
    trace_width: float = 0.25  # Default trace width in mm

    def get_weight(self) -> float:
        """Calculate connection weight based on net characteristics."""
        weight = 1.0

        # Multi-pin nets are more critical (bus, multi-component nets)
        if self.pin_count > 2:
            weight *= 1.0 + math.log(self.pin_count, 2) * 0.5

        # Critical nets get higher weight
        if self.is_power or self.is_ground:
            weight *= 2.0  # Power/ground need short, wide traces
        elif self.is_clock or self.is_high_speed:
            weight *= 1.8  # Clock/high-speed need minimal length

        # Wider traces benefit from shorter routing
        if self.trace_width > 0.5:
            weight *= 1.2

        return weight


@dataclass
class ComponentNode:
    """Node representing a component in the force-directed graph."""

    component: ComponentWrapper
    position: Point = field(default_factory=lambda: Point(0, 0))
    velocity: Point = field(default_factory=lambda: Point(0, 0))
    force: Point = field(default_factory=lambda: Point(0, 0))
    locked: bool = False
    group_id: str = ""  # Hierarchical path for grouping

    @property
    def reference(self) -> str:
        return self.component.reference

    def reset_force(self):
        """Reset accumulated forces to zero."""
        self.force = Point(0, 0)

    def add_force(self, fx: float, fy: float):
        """Add a force vector to the accumulated forces."""
        self.force = Point(self.force.x + fx, self.force.y + fy)

    def update_position(self, damping: float, max_displacement: float):
        """Update position based on accumulated forces."""
        if self.locked:
            return

        # Calculate force magnitude
        force_mag = math.sqrt(self.force.x**2 + self.force.y**2)
        if force_mag < 0.001:
            return

        # Limit displacement
        displacement = min(force_mag, max_displacement)

        # Apply force with damping
        dx = (displacement * self.force.x / force_mag) * damping
        dy = (displacement * self.force.y / force_mag) * damping

        # Update position
        self.position = Point(self.position.x + dx, self.position.y + dy)
        self.component.footprint.position = self.position


@dataclass
class Connection:
    """Weighted connection between two components."""

    source: str
    target: str
    net_info: NetInfo
    weight: float = 1.0

    def __post_init__(self):
        """Calculate weight from net info if not provided."""
        if self.weight == 1.0:  # Default weight
            self.weight = self.net_info.get_weight()


class EnhancedForceDirectedPlacer(PlacementAlgorithm):
    """
    Enhanced force-directed placement with net weighting and functional grouping.

    This algorithm implements a multi-phase optimization approach:

    Phase 1: Coarse placement with strong grouping
    - Large temperature for global optimization
    - Strong grouping forces to keep subcircuits together
    - Focus on gross positioning

    Phase 2: Fine placement with connection optimization
    - Medium temperature for local optimization
    - Emphasis on minimizing trace lengths
    - Weighted by connection criticality

    Phase 3: Collision resolution and final polish
    - Low temperature for stability
    - Resolve any remaining overlaps
    - Final convergence
    """

    def __init__(
        self,
        # Force parameters
        spring_constant: float = 0.15,
        repulsion_constant: float = 1500.0,
        grouping_strength: float = 0.3,
        boundary_strength: float = 15.0,

        # Simulation parameters
        iterations: int = 150,
        initial_temperature: float = 50.0,
        cooling_rate: float = 0.96,
        damping: float = 0.85,

        # Physical constraints
        min_distance: float = 2.0,
        component_spacing: float = 2.0,
        board_margin: float = 5.0,

        # Optimization flags
        enable_grouping: bool = True,
        enable_collision_resolution: bool = True,
        enable_net_weighting: bool = True,

        # Critical net patterns for auto-detection
        power_patterns: List[str] = None,
        ground_patterns: List[str] = None,
        clock_patterns: List[str] = None,
    ):
        """
        Initialize the enhanced force-directed placer.

        Args:
            spring_constant: Strength of attractive forces (higher = stronger pull)
            repulsion_constant: Strength of repulsive forces (higher = more spacing)
            grouping_strength: Strength of subcircuit grouping forces
            boundary_strength: Strength of board boundary forces
            iterations: Total number of simulation iterations
            initial_temperature: Starting temperature for simulated annealing
            cooling_rate: Temperature reduction per iteration (0-1)
            damping: Velocity damping to prevent oscillation (0-1)
            min_distance: Minimum distance between components
            component_spacing: Desired spacing between components
            board_margin: Margin from board edges
            enable_grouping: Enable hierarchical grouping forces
            enable_collision_resolution: Enable final collision resolution
            enable_net_weighting: Enable connection weighting by net type
            power_patterns: Net name patterns for power nets
            ground_patterns: Net name patterns for ground nets
            clock_patterns: Net name patterns for clock/high-speed nets
        """
        self.spring_constant = spring_constant
        self.repulsion_constant = repulsion_constant
        self.grouping_strength = grouping_strength
        self.boundary_strength = boundary_strength

        self.iterations = iterations
        self.initial_temperature = initial_temperature
        self.cooling_rate = cooling_rate
        self.damping = damping

        self.min_distance = min_distance
        self.component_spacing = component_spacing
        self.board_margin = board_margin

        self.enable_grouping = enable_grouping
        self.enable_collision_resolution = enable_collision_resolution
        self.enable_net_weighting = enable_net_weighting

        # Critical net patterns
        self.power_patterns = power_patterns or [
            "VCC", "VDD", "VBUS", "+5V", "+3V3", "+3.3V", "+12V", "PWR", "VIN"
        ]
        self.ground_patterns = ground_patterns or [
            "GND", "VSS", "AGND", "DGND", "PGND", "0V"
        ]
        self.clock_patterns = clock_patterns or [
            "CLK", "CLOCK", "XTAL", "OSC", "USB", "HDMI", "PCIE", "SPI", "I2C"
        ]

        # Internal state
        self.nodes: Dict[str, ComponentNode] = {}
        self.connections: List[Connection] = []
        self.groups: Dict[str, List[str]] = {}  # group_id -> [component_refs]
        self.board_bounds: Optional[BoundingBox] = None

        # Collision detector
        self.collision_detector = CourtyardCollisionDetector(spacing=component_spacing)

    def place(
        self,
        components: List[ComponentWrapper],
        connections: List[Tuple[str, str]],
        board_width: float = 100.0,
        board_height: float = 100.0,
        net_info: Optional[Dict[Tuple[str, str], NetInfo]] = None,
        **kwargs,
    ) -> Dict[str, Point]:
        """
        Place components using enhanced force-directed algorithm.

        Args:
            components: List of components to place
            connections: List of (ref1, ref2) tuples representing connections
            board_width: Board width in mm
            board_height: Board height in mm
            net_info: Optional mapping of connections to NetInfo for weighting
            **kwargs: Additional parameters (e.g., locked_refs, keepout_zones)

        Returns:
            Dictionary mapping component references to positions
        """
        if not components:
            return {}

        logger.info(
            f"Starting enhanced force-directed placement for {len(components)} components"
        )
        logger.info(f"Board: {board_width:.1f}x{board_height:.1f}mm")
        logger.info(f"Connections: {len(connections)}")

        # Initialize board bounds
        self.board_bounds = BoundingBox(0, 0, board_width, board_height)

        # Build nodes from components
        self._build_nodes(components)

        # Build connections with weights
        self._build_connections(connections, net_info)

        # Group components by hierarchy if enabled
        if self.enable_grouping:
            self._build_groups()
            logger.info(f"Found {len(self.groups)} functional groups")

        # Initialize positions
        self._initialize_positions(board_width, board_height)

        # Multi-phase optimization
        logger.info("Phase 1: Coarse placement with grouping")
        self._run_simulation_phase(
            iterations=self.iterations // 3,
            temperature=self.initial_temperature,
            grouping_weight=2.0 if self.enable_grouping else 0.0,
            spring_weight=0.5,
        )

        logger.info("Phase 2: Fine placement with trace optimization")
        self._run_simulation_phase(
            iterations=self.iterations // 3,
            temperature=self.initial_temperature * 0.5,
            grouping_weight=1.0 if self.enable_grouping else 0.0,
            spring_weight=1.5,
        )

        logger.info("Phase 3: Final convergence")
        self._run_simulation_phase(
            iterations=self.iterations // 3,
            temperature=self.initial_temperature * 0.2,
            grouping_weight=0.5 if self.enable_grouping else 0.0,
            spring_weight=2.0,
        )

        # Final collision resolution if enabled
        if self.enable_collision_resolution:
            logger.info("Final collision resolution")
            self._resolve_collisions()

        # Extract final positions
        positions = {ref: node.position for ref, node in self.nodes.items()}

        # Calculate and log metrics
        total_length = self._calculate_total_wire_length()
        logger.info(f"Total wire length: {total_length:.1f}mm")
        logger.info("Enhanced force-directed placement complete")

        return positions

    def _build_nodes(self, components: List[ComponentWrapper]):
        """Build component nodes from component list."""
        self.nodes.clear()

        for comp in components:
            node = ComponentNode(
                component=comp,
                position=comp.footprint.position,
                locked=comp.is_locked,
                group_id=comp.hierarchical_path or "root",
            )
            self.nodes[comp.reference] = node

    def _build_connections(
        self,
        connections: List[Tuple[str, str]],
        net_info: Optional[Dict[Tuple[str, str], NetInfo]],
    ):
        """Build weighted connections from connection list and net info."""
        self.connections.clear()

        for ref1, ref2 in connections:
            if ref1 not in self.nodes or ref2 not in self.nodes:
                continue

            # Get net info if provided, otherwise create default
            conn_key = (ref1, ref2)
            if net_info and conn_key in net_info:
                net = net_info[conn_key]
            else:
                # Auto-detect net type from component values/references
                net = self._auto_detect_net_info(ref1, ref2)

            connection = Connection(source=ref1, target=ref2, net_info=net)
            self.connections.append(connection)

        # Log connection statistics
        if self.enable_net_weighting:
            weights = [c.weight for c in self.connections]
            avg_weight = sum(weights) / len(weights) if weights else 1.0
            max_weight = max(weights) if weights else 1.0
            logger.info(
                f"Connection weights: avg={avg_weight:.2f}, max={max_weight:.2f}"
            )

    def _auto_detect_net_info(self, ref1: str, ref2: str) -> NetInfo:
        """Auto-detect net type from component references and values."""
        node1 = self.nodes[ref1]
        node2 = self.nodes[ref2]

        # Combine values and references for pattern matching
        text = (
            f"{node1.component.value} {node2.component.value} "
            f"{ref1} {ref2}"
        ).upper()

        net = NetInfo(net_name=f"{ref1}-{ref2}")

        # Check for power net
        for pattern in self.power_patterns:
            if pattern in text:
                net.is_power = True
                break

        # Check for ground net
        for pattern in self.ground_patterns:
            if pattern in text:
                net.is_ground = True
                break

        # Check for clock/high-speed net
        for pattern in self.clock_patterns:
            if pattern in text:
                net.is_clock = True
                break

        return net

    def _build_groups(self):
        """Build functional groups based on hierarchical paths."""
        self.groups.clear()

        for ref, node in self.nodes.items():
            group_id = node.group_id
            if group_id not in self.groups:
                self.groups[group_id] = []
            self.groups[group_id].append(ref)

    def _initialize_positions(self, board_width: float, board_height: float):
        """Initialize component positions."""
        # Count components that need initialization (at origin)
        unplaced = [
            node for node in self.nodes.values()
            if not node.locked and (node.position.x == 0 and node.position.y == 0)
        ]

        if not unplaced:
            return

        # Place components in groups if grouping is enabled
        if self.enable_grouping and len(self.groups) > 1:
            self._initialize_grouped_positions(board_width, board_height)
        else:
            self._initialize_grid_positions(unplaced, board_width, board_height)

    def _initialize_grouped_positions(
        self, board_width: float, board_height: float
    ):
        """Initialize positions with groups arranged in a grid."""
        group_list = list(self.groups.values())
        n_groups = len(group_list)

        # Arrange groups in a grid
        cols = math.ceil(math.sqrt(n_groups))
        rows = math.ceil(n_groups / cols)

        cell_width = board_width / cols
        cell_height = board_height / rows

        for idx, group_refs in enumerate(group_list):
            row = idx // cols
            col = idx % cols

            # Center of this group's cell
            center_x = (col + 0.5) * cell_width
            center_y = (row + 0.5) * cell_height

            # Place components in this group in a small grid around center
            self._place_group_grid(group_refs, center_x, center_y, cell_width * 0.8)

    def _place_group_grid(
        self, refs: List[str], center_x: float, center_y: float, max_size: float
    ):
        """Place a group of components in a grid pattern."""
        n = len(refs)
        grid_size = math.ceil(math.sqrt(n))
        spacing = min(max_size / grid_size, self.component_spacing * 3)

        start_x = center_x - (grid_size - 1) * spacing / 2
        start_y = center_y - (grid_size - 1) * spacing / 2

        for idx, ref in enumerate(refs):
            node = self.nodes[ref]
            if node.locked:
                continue

            row = idx // grid_size
            col = idx % grid_size

            node.position = Point(
                start_x + col * spacing,
                start_y + row * spacing
            )

    def _initialize_grid_positions(
        self, nodes: List[ComponentNode], board_width: float, board_height: float
    ):
        """Initialize positions in a simple grid."""
        n = len(nodes)
        grid_size = math.ceil(math.sqrt(n))
        spacing = min(board_width, board_height) / (grid_size + 1)

        for idx, node in enumerate(nodes):
            row = idx // grid_size
            col = idx % grid_size

            node.position = Point(
                (col + 1) * spacing,
                (row + 1) * spacing
            )

    def _run_simulation_phase(
        self,
        iterations: int,
        temperature: float,
        grouping_weight: float,
        spring_weight: float,
    ):
        """Run a phase of the force-directed simulation."""
        temp = temperature

        for iteration in range(iterations):
            # Reset forces
            for node in self.nodes.values():
                node.reset_force()

            # Calculate forces
            self._apply_spring_forces(spring_weight)
            self._apply_repulsion_forces()

            if self.enable_grouping and grouping_weight > 0:
                self._apply_grouping_forces(grouping_weight)

            self._apply_boundary_forces()

            # Update positions with temperature-based displacement limit
            max_displacement = temp
            for node in self.nodes.values():
                node.update_position(self.damping, max_displacement)

            # Cool down
            temp *= self.cooling_rate

            # Log progress
            if iteration % 20 == 0:
                wire_length = self._calculate_total_wire_length()
                logger.debug(
                    f"  Iteration {iteration}/{iterations}: "
                    f"temp={temp:.2f}, wire_length={wire_length:.1f}mm"
                )

    def _apply_spring_forces(self, weight_multiplier: float = 1.0):
        """Apply attractive spring forces between connected components."""
        for conn in self.connections:
            source = self.nodes[conn.source]
            target = self.nodes[conn.target]

            # Calculate distance and direction
            dx = target.position.x - source.position.x
            dy = target.position.y - source.position.y
            distance = math.sqrt(dx * dx + dy * dy)

            if distance < 0.01:
                continue

            # Hooke's law: F = k * x
            # Apply connection weight
            effective_k = self.spring_constant * conn.weight * weight_multiplier
            force_magnitude = effective_k * distance

            # Normalize and scale
            fx = (force_magnitude * dx) / distance
            fy = (force_magnitude * dy) / distance

            # Apply forces (Newton's third law)
            if not source.locked:
                source.add_force(fx, fy)
            if not target.locked:
                target.add_force(-fx, -fy)

    def _apply_repulsion_forces(self):
        """Apply repulsive forces between all components."""
        nodes_list = list(self.nodes.values())

        for i in range(len(nodes_list)):
            node1 = nodes_list[i]
            if node1.locked:
                continue

            for j in range(i + 1, len(nodes_list)):
                node2 = nodes_list[j]

                # Calculate distance
                dx = node2.position.x - node1.position.x
                dy = node2.position.y - node1.position.y
                distance = math.sqrt(dx * dx + dy * dy)

                # Use minimum distance to prevent infinite forces
                distance = max(distance, self.min_distance)

                # Coulomb's law: F = k / r^2
                force_magnitude = self.repulsion_constant / (distance * distance)

                # Normalize and scale
                fx = (force_magnitude * dx) / distance
                fy = (force_magnitude * dy) / distance

                # Apply repulsion (push apart)
                node1.add_force(-fx, -fy)
                if not node2.locked:
                    node2.add_force(fx, fy)

    def _apply_grouping_forces(self, weight_multiplier: float = 1.0):
        """Apply forces to keep components in the same group close together."""
        for group_id, refs in self.groups.items():
            if len(refs) <= 1:
                continue

            # Calculate group centroid
            group_nodes = [self.nodes[ref] for ref in refs if not self.nodes[ref].locked]
            if not group_nodes:
                continue

            centroid_x = sum(n.position.x for n in group_nodes) / len(group_nodes)
            centroid_y = sum(n.position.y for n in group_nodes) / len(group_nodes)

            # Pull each component toward the centroid
            for node in group_nodes:
                dx = centroid_x - node.position.x
                dy = centroid_y - node.position.y
                distance = math.sqrt(dx * dx + dy * dy)

                if distance < 0.01:
                    continue

                # Gentle pull toward centroid
                force_magnitude = (
                    self.grouping_strength * weight_multiplier * distance
                )
                fx = (force_magnitude * dx) / distance
                fy = (force_magnitude * dy) / distance

                node.add_force(fx, fy)

    def _apply_boundary_forces(self):
        """Apply forces to keep components within board boundaries."""
        if not self.board_bounds:
            return

        margin = self.board_margin

        for node in self.nodes.values():
            if node.locked:
                continue

            force_x = 0.0
            force_y = 0.0

            # Left boundary
            if node.position.x < self.board_bounds.min_x + margin:
                penetration = (self.board_bounds.min_x + margin) - node.position.x
                force_x += self.boundary_strength * penetration

            # Right boundary
            if node.position.x > self.board_bounds.max_x - margin:
                penetration = node.position.x - (self.board_bounds.max_x - margin)
                force_x -= self.boundary_strength * penetration

            # Top boundary
            if node.position.y < self.board_bounds.min_y + margin:
                penetration = (self.board_bounds.min_y + margin) - node.position.y
                force_y += self.boundary_strength * penetration

            # Bottom boundary
            if node.position.y > self.board_bounds.max_y - margin:
                penetration = node.position.y - (self.board_bounds.max_y - margin)
                force_y -= self.boundary_strength * penetration

            node.add_force(force_x, force_y)

    def _resolve_collisions(self):
        """Resolve any remaining component collisions."""
        footprints = [node.component.footprint for node in self.nodes.values()]
        max_iterations = 50

        for iteration in range(max_iterations):
            collisions = self.collision_detector.detect_collisions(footprints)

            if not collisions:
                logger.info(f"All collisions resolved after {iteration} iterations")
                return

            if iteration == 0:
                logger.info(f"Resolving {len(collisions)} collisions")

            # Resolve each collision by pushing components apart
            for fp1, fp2 in collisions:
                node1 = self.nodes.get(fp1.reference)
                node2 = self.nodes.get(fp2.reference)

                if not node1 or not node2:
                    continue

                # Don't move locked components
                if node1.locked and node2.locked:
                    continue

                # Calculate separation vector
                dx = node2.position.x - node1.position.x
                dy = node2.position.y - node1.position.y
                distance = math.sqrt(dx * dx + dy * dy)

                if distance < 0.1:
                    # Random separation for overlapping components
                    angle = random.uniform(0, 2 * math.pi)
                    dx = math.cos(angle)
                    dy = math.sin(angle)
                    distance = 1.0

                # Normalize
                dx /= distance
                dy /= distance

                # Push distance
                push = self.component_spacing * 0.5

                # Apply push (both directions or single if one is locked)
                if node1.locked:
                    node2.position = Point(
                        node2.position.x + dx * push * 2,
                        node2.position.y + dy * push * 2
                    )
                elif node2.locked:
                    node1.position = Point(
                        node1.position.x - dx * push * 2,
                        node1.position.y - dy * push * 2
                    )
                else:
                    node1.position = Point(
                        node1.position.x - dx * push,
                        node1.position.y - dy * push
                    )
                    node2.position = Point(
                        node2.position.x + dx * push,
                        node2.position.y + dy * push
                    )

        # Log if collisions remain
        final_collisions = self.collision_detector.detect_collisions(footprints)
        if final_collisions:
            logger.warning(
                f"Could not resolve all collisions: {len(final_collisions)} remain"
            )

    def _calculate_total_wire_length(self) -> float:
        """Calculate total estimated wire length for all connections."""
        total = 0.0

        for conn in self.connections:
            source = self.nodes[conn.source]
            target = self.nodes[conn.target]

            dx = target.position.x - source.position.x
            dy = target.position.y - source.position.y
            distance = math.sqrt(dx * dx + dy * dy)

            # Weight by connection importance
            total += distance * conn.weight

        return total
