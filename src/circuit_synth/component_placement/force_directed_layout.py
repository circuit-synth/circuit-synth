"""Force-directed layout algorithm for component placement.

This module implements a force-directed layout algorithm for placing components
in a schematic based on their connectivity and physical constraints.

Key features:
- Uses component connectivity to determine attractive forces
- Uses component size/spacing for repulsive forces
- Iteratively adjusts positions until equilibrium
"""

import math
import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .geometry import ComponentGeometryHandler, create_geometry_handler
from .placement import PlacementNode


@dataclass
class ForceVector:
    """Represents a 2D force vector."""

    x: float
    y: float

    def __add__(self, other: "ForceVector") -> "ForceVector":
        return ForceVector(self.x + other.x, self.y + other.y)

    def scale(self, factor: float) -> "ForceVector":
        return ForceVector(self.x * factor, self.y * factor)

    def magnitude(self) -> float:
        return math.sqrt(self.x * self.x + self.y * self.y)


class ForceDirectedLayout:
    """Force-directed layout algorithm for component placement."""

    def __init__(
        self,
        attractive_force: float = 0.3,
        repulsive_force: float = 100.0,
        damping: float = 0.85,
        min_distance: float = 15.0,
        max_iterations: int = 100,
        convergence_threshold: float = 0.1,
    ):
        """Initialize the force-directed layout algorithm.

        Args:
            attractive_force: Strength of attractive forces between connected components
            repulsive_force: Strength of repulsive forces between all components
            damping: Damping factor to prevent oscillation (0-1)
            min_distance: Minimum distance between components
            max_iterations: Maximum number of iterations
            convergence_threshold: Stop when max force is below this threshold
        """
        self.attractive_force = attractive_force
        self.repulsive_force = repulsive_force
        self.damping = damping
        self.min_distance = min_distance
        self.max_iterations = max_iterations
        self.convergence_threshold = convergence_threshold
        self.placement_nodes: Dict[str, PlacementNode] = {}
        self.velocities: Dict[str, ForceVector] = {}

    def _calculate_attractive_force(
        self, node1: PlacementNode, node2: PlacementNode
    ) -> ForceVector:
        """Calculate attractive force between two connected components."""
        dx = node2.x - node1.x
        dy = node2.y - node1.y
        distance = math.sqrt(dx * dx + dy * dy)

        if distance < 0.0001:  # Prevent division by zero
            return ForceVector(0, 0)

        # Force proportional to distance (Hooke's law)
        force = self.attractive_force * distance
        fx = (force * dx) / distance
        fy = (force * dy) / distance

        return ForceVector(fx, fy)

    def _calculate_repulsive_force(
        self, node1: PlacementNode, node2: PlacementNode
    ) -> ForceVector:
        """Calculate repulsive force between two components."""
        dx = node2.x - node1.x
        dy = node2.y - node1.y
        distance = math.sqrt(dx * dx + dy * dy)

        if distance < 0.0001:  # Prevent division by zero
            # Add small random offset to prevent components from stacking
            return ForceVector(
                0.1 * (0.5 - random.random()), 0.1 * (0.5 - random.random())
            )

        # Force inversely proportional to distance squared (Coulomb's law)
        force = -self.repulsive_force / (distance * distance)
        fx = (force * dx) / distance
        fy = (force * dy) / distance

        return ForceVector(fx, fy)

    def _apply_forces(self) -> float:
        """Apply forces to all components for one iteration.

        Returns:
            float: Maximum force magnitude applied in this iteration
        """
        forces: Dict[str, ForceVector] = {}
        max_force = 0.0

        # Initialize forces
        for ref in self.placement_nodes:
            forces[ref] = ForceVector(0, 0)

        # Calculate all forces
        nodes = list(self.placement_nodes.values())
        for i, node1 in enumerate(nodes):
            for node2 in nodes[i + 1 :]:
                # Skip if either component is fixed (e.g. power symbols)
                if (
                    node1.component.library == "power"
                    or node2.component.library == "power"
                ):
                    continue

                # Calculate repulsive force between all components
                repulsive = self._calculate_repulsive_force(node1, node2)
                forces[node1.component.ref] += repulsive
                forces[node2.component.ref] += repulsive.scale(-1)

                # Calculate attractive force between connected components
                if node2.component in node1.connected_components:
                    attractive = self._calculate_attractive_force(node1, node2)
                    forces[node1.component.ref] += attractive
                    forces[node2.component.ref] += attractive.scale(-1)

        # Apply forces and update velocities
        for ref, node in self.placement_nodes.items():
            if node.component.library != "power":  # Don't move power symbols
                force = forces[ref]
                velocity = self.velocities[ref]

                # Update velocity (with damping)
                new_velocity = velocity.scale(self.damping) + force
                self.velocities[ref] = new_velocity

                # Update position
                node.x += new_velocity.x
                node.y += new_velocity.y

                # Track maximum force
                max_force = max(max_force, force.magnitude())

        return max_force

    def layout(
        self,
        circuit: "Circuit",
        initial_positions: Optional[Dict[str, Tuple[float, float, float]]] = None,
    ) -> Dict[str, Tuple[float, float, float]]:
        """Apply force-directed layout to position components.

        Args:
            circuit: The circuit to layout
            initial_positions: Optional dict of initial component positions (x, y, rotation)

        Returns:
            Dict mapping component references to (x, y, rotation) tuples
        """
        # Initialize placement nodes
        self.placement_nodes = {
            comp.ref: PlacementNode(
                component=comp,
                geometry_handler=create_geometry_handler(comp.name, comp.library),
            )
            for comp in circuit.components
        }

        # Set initial positions
        if initial_positions:
            for ref, (x, y, rot) in initial_positions.items():
                if ref in self.placement_nodes:
                    self.placement_nodes[ref].x = x
                    self.placement_nodes[ref].y = y
                    self.placement_nodes[ref].rotation = rot
        else:
            # Start with grid layout if no initial positions
            grid_size = math.ceil(math.sqrt(len(circuit.components)))
            spacing = self.min_distance * 2
            i = 0
            for node in self.placement_nodes.values():
                if node.component.library != "power":
                    node.x = (i % grid_size) * spacing
                    node.y = (i // grid_size) * spacing
                    i += 1

        # Initialize velocities
        self.velocities = {ref: ForceVector(0, 0) for ref in self.placement_nodes}

        # Build connectivity graph
        for net in circuit.get_nets():
            connected_components = set()
            for pin in net.pins:
                connected_components.add(pin.parent)

            for comp in connected_components:
                node = self.placement_nodes[comp.ref]
                node.connected_components.update(
                    c for c in connected_components if c != comp
                )

        # Main layout loop
        for iteration in range(self.max_iterations):
            max_force = self._apply_forces()
            if max_force < self.convergence_threshold:
                break

        # Return final positions
        return {
            ref: (node.x, node.y, node.rotation)
            for ref, node in self.placement_nodes.items()
        }
