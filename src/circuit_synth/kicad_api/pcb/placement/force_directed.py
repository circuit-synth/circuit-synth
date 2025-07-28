"""
Force-directed placement algorithm for PCB components.

This algorithm uses physics simulation to optimize component placement
by treating components as nodes and connections as springs.
"""

import logging
import math
import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from ..types import Footprint, Point
from .base import ComponentWrapper, PlacementAlgorithm
from .bbox import BoundingBox

logger = logging.getLogger(__name__)


@dataclass
class Node:
    """Represents a component in the force-directed graph."""

    component: ComponentWrapper
    x: float
    y: float
    vx: float = 0.0  # velocity x
    vy: float = 0.0  # velocity y
    fx: float = 0.0  # force x
    fy: float = 0.0  # force y
    locked: bool = False

    @property
    def reference(self) -> str:
        return self.component.reference


@dataclass
class Edge:
    """Represents a connection between components."""

    source: str  # reference of source component
    target: str  # reference of target component
    weight: float = 1.0  # connection strength/importance


class ForceDirectedPlacer(PlacementAlgorithm):
    """
    Force-directed placement algorithm for PCB components.

    This algorithm simulates physical forces between components:
    - Connected components attract each other (spring forces)
    - All components repel each other (electrostatic forces)
    - Components are attracted to the center (gravity)
    """

    def __init__(
        self,
        iterations: int = 100,
        temperature: float = 100.0,
        cooling_rate: float = 0.95,
        spring_constant: float = 0.1,
        repulsion_constant: float = 1000.0,
        gravity_constant: float = 0.01,
        min_distance: float = 10.0,
    ):
        """
        Initialize the force-directed placer.

        Args:
            iterations: Number of simulation iterations
            temperature: Initial temperature for simulated annealing
            cooling_rate: Temperature reduction factor per iteration
            spring_constant: Strength of attractive forces between connected nodes
            repulsion_constant: Strength of repulsive forces between all nodes
            gravity_constant: Strength of attraction to center
            min_distance: Minimum distance between components
        """
        self.iterations = iterations
        self.temperature = temperature
        self.cooling_rate = cooling_rate
        self.spring_constant = spring_constant
        self.repulsion_constant = repulsion_constant
        self.gravity_constant = gravity_constant
        self.min_distance = min_distance

        self.nodes: Dict[str, Node] = {}
        self.edges: List[Edge] = []
        self.center_x = 0.0
        self.center_y = 0.0

    def add_component(self, footprint: Footprint, locked: bool = False):
        """Add a component to the placement graph."""
        wrapper = ComponentWrapper(footprint)
        node = Node(
            component=wrapper,
            x=footprint.position.x,
            y=footprint.position.y,
            locked=locked,
        )
        self.nodes[footprint.reference] = node

    def add_connection(self, ref1: str, ref2: str, weight: float = 1.0):
        """Add a connection between two components."""
        if ref1 in self.nodes and ref2 in self.nodes:
            self.edges.append(Edge(ref1, ref2, weight))
        else:
            logger.warning(
                f"Cannot add connection between {ref1} and {ref2}: component not found"
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
        Place components using force-directed algorithm.

        Args:
            components: List of components to place
            connections: List of (ref1, ref2) tuples representing connections
            board_width: Board width in mm
            board_height: Board height in mm
            **kwargs: Algorithm-specific parameters (e.g., locked_refs)

        Returns:
            Dictionary mapping component references to positions
        """
        # Clear any existing nodes/edges
        self.nodes.clear()
        self.edges.clear()

        # Add components
        for comp in components:
            # Use the component's is_locked property
            self.add_component(comp.footprint, locked=comp.is_locked)

        # Add connections
        for ref1, ref2 in connections:
            self.add_connection(ref1, ref2)

        # Set center to board center
        self.center_x = board_width / 2
        self.center_y = board_height / 2

        # Run the placement algorithm
        positions = self._run_placement()

        # Convert tuples to Points
        return {ref: Point(x, y) for ref, (x, y) in positions.items()}

    def _run_placement(self) -> Dict[str, Tuple[float, float]]:
        """
        Run the force-directed placement algorithm.

        Returns:
            Dictionary mapping component references to (x, y) positions
        """
        if not self.nodes:
            return {}

        # Calculate center of mass
        self._calculate_center()

        # Initialize random positions for components without positions
        self._initialize_positions()

        # Run simulation
        temp = self.temperature
        for iteration in range(self.iterations):
            # Reset forces
            for node in self.nodes.values():
                node.fx = 0.0
                node.fy = 0.0

            # Calculate forces
            self._apply_spring_forces()
            self._apply_repulsion_forces()
            self._apply_gravity_forces()

            # Update positions
            self._update_positions(temp)

            # Cool down
            temp *= self.cooling_rate

            # Log progress
            if iteration % 10 == 0:
                logger.debug(
                    f"Force-directed iteration {iteration}/{self.iterations}, temp={temp:.2f}"
                )

        # Return final positions
        return {ref: (node.x, node.y) for ref, node in self.nodes.items()}

    def _calculate_center(self):
        """Calculate the center of mass of all components."""
        if not self.nodes:
            return

        sum_x = sum(node.x for node in self.nodes.values())
        sum_y = sum(node.y for node in self.nodes.values())
        self.center_x = sum_x / len(self.nodes)
        self.center_y = sum_y / len(self.nodes)

    def _initialize_positions(self):
        """Initialize random positions for components at (0, 0)."""
        # Find components at origin
        at_origin = [
            node for node in self.nodes.values() if node.x == 0 and node.y == 0
        ]

        if at_origin:
            # Spread them in a circle around the center
            angle_step = 2 * math.pi / len(at_origin)
            radius = 50.0  # Initial spread radius

            for i, node in enumerate(at_origin):
                angle = i * angle_step
                node.x = self.center_x + radius * math.cos(angle)
                node.y = self.center_y + radius * math.sin(angle)

    def _apply_spring_forces(self):
        """Apply attractive forces between connected components."""
        for edge in self.edges:
            if edge.source not in self.nodes or edge.target not in self.nodes:
                continue

            source = self.nodes[edge.source]
            target = self.nodes[edge.target]

            # Calculate distance and direction
            dx = target.x - source.x
            dy = target.y - source.y
            distance = math.sqrt(dx * dx + dy * dy)

            if distance < 0.01:  # Avoid division by zero
                continue

            # Spring force (Hooke's law)
            force = self.spring_constant * distance * edge.weight
            fx = force * dx / distance
            fy = force * dy / distance

            # Apply forces (Newton's third law)
            if not source.locked:
                source.fx += fx
                source.fy += fy
            if not target.locked:
                target.fx -= fx
                target.fy -= fy

    def _apply_repulsion_forces(self):
        """Apply repulsive forces between all components."""
        nodes_list = list(self.nodes.values())

        for i in range(len(nodes_list)):
            for j in range(i + 1, len(nodes_list)):
                node1 = nodes_list[i]
                node2 = nodes_list[j]

                # Calculate distance and direction
                dx = node2.x - node1.x
                dy = node2.y - node1.y
                distance = math.sqrt(dx * dx + dy * dy)

                if distance < self.min_distance:
                    distance = self.min_distance

                # Coulomb's law (electrostatic repulsion)
                force = self.repulsion_constant / (distance * distance)
                fx = force * dx / distance
                fy = force * dy / distance

                # Apply forces
                if not node1.locked:
                    node1.fx -= fx
                    node1.fy -= fy
                if not node2.locked:
                    node2.fx += fx
                    node2.fy += fy

    def _apply_gravity_forces(self):
        """Apply attractive force toward the center."""
        for node in self.nodes.values():
            if node.locked:
                continue

            # Direction to center
            dx = self.center_x - node.x
            dy = self.center_y - node.y
            distance = math.sqrt(dx * dx + dy * dy)

            if distance < 0.01:
                continue

            # Gravity force
            force = self.gravity_constant * distance
            node.fx += force * dx / distance
            node.fy += force * dy / distance

    def _update_positions(self, temperature: float):
        """Update node positions based on forces."""
        for node in self.nodes.values():
            if node.locked:
                continue

            # Calculate displacement
            force_magnitude = math.sqrt(node.fx * node.fx + node.fy * node.fy)
            if force_magnitude < 0.01:
                continue

            # Limit displacement by temperature
            displacement = min(force_magnitude, temperature)
            dx = displacement * node.fx / force_magnitude
            dy = displacement * node.fy / force_magnitude

            # Update position
            node.x += dx
            node.y += dy

            # Update component position
            node.component.footprint.position = Point(node.x, node.y)


def apply_force_directed_placement(
    footprints: List[Footprint],
    connections: List[Tuple[str, str]],
    locked_refs: Optional[Set[str]] = None,
    **kwargs,
) -> Dict[str, Tuple[float, float]]:
    """
    Apply force-directed placement to a list of footprints.

    Args:
        footprints: List of footprints to place
        connections: List of (ref1, ref2) tuples representing connections
        locked_refs: Set of reference designators that should not be moved
        **kwargs: Additional parameters for ForceDirectedPlacer

    Returns:
        Dictionary mapping reference designators to (x, y) positions
    """
    placer = ForceDirectedPlacer(**kwargs)
    locked_refs = locked_refs or set()

    # Add components
    for footprint in footprints:
        placer.add_component(footprint, locked=footprint.reference in locked_refs)

    # Add connections
    for ref1, ref2 in connections:
        placer.add_connection(ref1, ref2)

    # Run placement
    return placer.place()
