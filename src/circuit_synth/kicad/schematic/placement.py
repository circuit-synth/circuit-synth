"""
Schematic Component Placement Module

Provides automatic placement of schematic components using various algorithms.
"""

import logging
import math
import random
import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

from .models import Line, NetConnection, Point, SchematicSymbol

logger = logging.getLogger(__name__)


class PlacementStrategy(Enum):
    """Available placement strategies for arranging components."""

    GRID = "grid"
    CIRCULAR = "circular"
    HIERARCHICAL = "hierarchical"
    FORCE_DIRECTED = "force_directed"
    FUNCTIONAL_BLOCKS = "functional_blocks"
    COMPACT = "compact"


@dataclass
class PlacementConfig:
    """Configuration for component placement."""

    strategy: PlacementStrategy = PlacementStrategy.GRID
    grid_spacing: float = 25.4  # mm (1 inch)
    margin: float = 12.7  # mm (0.5 inch)
    wire_spacing: float = 2.54  # mm (0.1 inch)
    junction_radius: float = 0.635  # mm
    max_iterations: int = 100
    temperature: float = 1.0
    cooling_rate: float = 0.95
    spring_constant: float = 0.1
    repulsion_constant: float = 10000
    attraction_constant: float = 0.01
    min_distance: float = 25.4  # Minimum distance between components


class SchematicPlacer:
    """
    Handles automatic placement of schematic components.

    This class provides various algorithms for arranging components
    in a schematic, including grid, circular, hierarchical, and
    force-directed layouts.
    """

    def __init__(self, config: Optional[PlacementConfig] = None):
        """
        Initialize the schematic placer.

        Args:
            config: Placement configuration (uses defaults if None)
        """
        self.config = config or PlacementConfig()
        self.margin = self.config.margin
        self.grid_spacing = self.config.grid_spacing

    def place_components(
        self,
        components: List[SchematicSymbol],
        connections: List[NetConnection],
        page_size: Tuple[float, float] = (279.4, 215.9),  # A4 landscape in mm
    ) -> None:
        """
        Place components on the schematic using the configured strategy.

        Args:
            components: List of schematic symbols to place
            connections: List of net connections between components
            page_size: Size of the schematic page (width, height) in mm
        """
        if not components:
            logger.warning("No components to place")
            return

        logger.info(
            f"Placing {len(components)} components using {self.config.strategy.value} strategy"
        )

        # Store connections for algorithms that need them
        self.connections = connections

        # Apply the selected placement strategy
        if self.config.strategy == PlacementStrategy.GRID:
            self._place_grid(components, page_size)
        elif self.config.strategy == PlacementStrategy.CIRCULAR:
            self._place_circular(components, page_size)
        elif self.config.strategy == PlacementStrategy.HIERARCHICAL:
            self._place_hierarchical(components, connections, page_size)
        elif self.config.strategy == PlacementStrategy.FORCE_DIRECTED:
            self._place_force_directed(components, connections, page_size)
        elif self.config.strategy == PlacementStrategy.FUNCTIONAL_BLOCKS:
            self._place_functional_blocks(components, connections, page_size)
        elif self.config.strategy == PlacementStrategy.COMPACT:
            self._place_compact(components, page_size)
        else:
            logger.warning(
                f"Unknown placement strategy: {self.config.strategy}, using grid"
            )
            self._place_grid(components, page_size)

        logger.info("Component placement completed")

    def _place_grid(
        self, components: List[SchematicSymbol], page_size: Tuple[float, float]
    ) -> None:
        """
        Place components in a regular grid pattern.

        Args:
            components: Components to place
            page_size: Available page size
        """
        # Calculate grid dimensions
        available_width = page_size[0] - 2 * self.margin
        available_height = page_size[1] - 2 * self.margin

        cols = max(1, int(available_width / self.grid_spacing))
        rows = max(1, int(math.ceil(len(components) / cols)))

        # Adjust spacing if needed to fit on page
        actual_spacing_x = available_width / cols if cols > 1 else self.grid_spacing
        actual_spacing_y = available_height / rows if rows > 1 else self.grid_spacing

        # Place components in grid
        for i, comp in enumerate(components):
            col = i % cols
            row = i // cols

            x = self.margin + col * actual_spacing_x + actual_spacing_x / 2
            y = self.margin + row * actual_spacing_y + actual_spacing_y / 2

            comp.position = Point(x, y)

    def _place_circular(
        self, components: List[SchematicSymbol], page_size: Tuple[float, float]
    ) -> None:
        """
        Place components in a circular pattern.

        Args:
            components: Components to place
            page_size: Available page size
        """
        center_x = page_size[0] / 2
        center_y = page_size[1] / 2

        # Calculate radius to fit within page margins
        max_radius_x = (page_size[0] - 2 * self.margin) / 2
        max_radius_y = (page_size[1] - 2 * self.margin) / 2
        radius = min(max_radius_x, max_radius_y) * 0.8  # 80% of max to leave space

        # Place components around circle
        angle_step = 2 * math.pi / len(components)

        for i, comp in enumerate(components):
            angle = i * angle_step
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            comp.position = Point(x, y)

    def _place_hierarchical(
        self,
        components: List[SchematicSymbol],
        connections: List[NetConnection],
        page_size: Tuple[float, float],
    ) -> None:
        """
        Place components in a hierarchical layout based on signal flow.

        Args:
            components: Components to place
            connections: Connections between components
            page_size: Available page size
        """
        # Build adjacency information
        adjacency = self._build_adjacency_map(components, connections)

        # Find components with no inputs (sources)
        sources = []
        sinks = []
        intermediates = []

        for comp in components:
            inputs = sum(
                1
                for conn in connections
                if any(p.symbol == comp for p in conn.end_points)
            )
            outputs = sum(
                1
                for conn in connections
                if any(p.symbol == comp for p in conn.start_points)
            )

            if inputs == 0:
                sources.append(comp)
            elif outputs == 0:
                sinks.append(comp)
            else:
                intermediates.append(comp)

        # Create layers
        layers = []
        if sources:
            layers.append(sources)
        if intermediates:
            # Simple layering - could be improved with topological sort
            layers.append(intermediates)
        if sinks:
            layers.append(sinks)

        # Place layers
        if layers:
            layer_height = (page_size[1] - 2 * self.margin) / len(layers)

            for layer_idx, layer in enumerate(layers):
                y = self.margin + layer_idx * layer_height + layer_height / 2

                if layer:
                    comp_width = (page_size[0] - 2 * self.margin) / len(layer)
                    for comp_idx, comp in enumerate(layer):
                        x = self.margin + comp_idx * comp_width + comp_width / 2
                        comp.position = Point(x, y)

    def _place_force_directed(
        self,
        components: List[SchematicSymbol],
        connections: List[NetConnection],
        page_size: Tuple[float, float],
    ) -> None:
        """
        Place components using a force-directed algorithm.

        This simulates physical forces between components to achieve
        an aesthetically pleasing layout.

        Args:
            components: Components to place
            connections: Connections between components
            page_size: Available page size
        """
        # Initialize with random positions
        for comp in components:
            x = random.uniform(self.margin, page_size[0] - self.margin)
            y = random.uniform(self.margin, page_size[1] - self.margin)
            comp.position = Point(x, y)

        # Build adjacency for connected components
        adjacency = self._build_adjacency_map(components, connections)

        # Force-directed iterations
        temperature = self.config.temperature

        for iteration in range(self.config.max_iterations):
            forces = {}

            # Calculate forces for each component
            for comp in components:
                force_x = 0.0
                force_y = 0.0

                # Repulsive forces (between all components)
                for other in components:
                    if comp != other:
                        dx = comp.position.x - other.position.x
                        dy = comp.position.y - other.position.y
                        distance = math.sqrt(dx * dx + dy * dy)

                        if distance > 0:
                            # Coulomb's law repulsion
                            force = self.config.repulsion_constant / (distance * distance)
                            force_x += (dx / distance) * force
                            force_y += (dy / distance) * force

                # Attractive forces (between connected components)
                if comp in adjacency:
                    for connected in adjacency[comp]:
                        dx = connected.position.x - comp.position.x
                        dy = connected.position.y - comp.position.y
                        distance = math.sqrt(dx * dx + dy * dy)

                        if distance > 0:
                            # Hooke's law attraction
                            force = self.config.spring_constant * distance
                            force_x += (dx / distance) * force
                            force_y += (dy / distance) * force

                forces[comp] = (force_x, force_y)

            # Apply forces with temperature-based damping
            for comp, (fx, fy) in forces.items():
                # Limit displacement by temperature
                displacement = math.sqrt(fx * fx + fy * fy)
                if displacement > 0:
                    max_displacement = temperature * self.grid_spacing
                    scale = min(1.0, max_displacement / displacement)
                    dx = fx * scale
                    dy = fy * scale

                    # Update position
                    new_x = comp.position.x + dx
                    new_y = comp.position.y + dy

                    # Keep within bounds
                    new_x = max(self.margin, min(page_size[0] - self.margin, new_x))
                    new_y = max(self.margin, min(page_size[1] - self.margin, new_y))

                    comp.position = Point(new_x, new_y)

            # Cool down
            temperature *= self.config.cooling_rate

            # Early termination if converged
            if temperature < 0.01:
                break

    def _place_functional_blocks(
        self,
        components: List[SchematicSymbol],
        connections: List[NetConnection],
        page_size: Tuple[float, float],
    ) -> None:
        """
        Place components in functional blocks based on their types and connections.

        Args:
            components: Components to place
            connections: Connections between components
            page_size: Available page size
        """
        # Group components by type/function
        groups = {}
        for comp in components:
            # Determine group based on reference designator
            if comp.reference.startswith("U"):
                group = "ICs"
            elif comp.reference.startswith("R"):
                group = "Resistors"
            elif comp.reference.startswith("C"):
                group = "Capacitors"
            elif comp.reference.startswith("L"):
                group = "Inductors"
            elif comp.reference.startswith("J") or comp.reference.startswith("P"):
                group = "Connectors"
            elif comp.reference.startswith("Q"):
                group = "Transistors"
            elif comp.reference.startswith("D"):
                group = "Diodes"
            else:
                group = "Other"

            if group not in groups:
                groups[group] = []
            groups[group].append(comp)

        # Arrange groups in blocks
        num_groups = len(groups)
        if num_groups == 0:
            return

        # Calculate block dimensions
        cols = math.ceil(math.sqrt(num_groups))
        rows = math.ceil(num_groups / cols)

        block_width = (page_size[0] - 2 * self.margin) / cols
        block_height = (page_size[1] - 2 * self.margin) / rows

        # Place each group
        for group_idx, (group_name, group_components) in enumerate(groups.items()):
            col = group_idx % cols
            row = group_idx // cols

            block_x = self.margin + col * block_width
            block_y = self.margin + row * block_height

            # Place components within block
            self._place_components_in_block(
                group_components, block_x, block_y, block_width, block_height
            )

    def _place_compact(
        self, components: List[SchematicSymbol], page_size: Tuple[float, float]
    ) -> None:
        """
        Place components in a compact arrangement to minimize total area.

        Args:
            components: Components to place
            page_size: Available page size
        """
        # Sort components by size (approximate)
        sorted_comps = sorted(components, key=lambda c: len(c.pins), reverse=True)

        # Use a simple packing algorithm
        placed_rectangles = []

        for comp in sorted_comps:
            # Estimate component size
            comp_width = self.grid_spacing
            comp_height = self.grid_spacing * 0.8

            # Find position that doesn't overlap with placed components
            best_x = self.margin
            best_y = self.margin
            min_waste = float("inf")

            # Try positions
            for y in range(
                int(self.margin), int(page_size[1] - self.margin - comp_height), 10
            ):
                for x in range(
                    int(self.margin), int(page_size[0] - self.margin - comp_width), 10
                ):
                    # Check overlap
                    overlaps = False
                    for rx, ry, rw, rh in placed_rectangles:
                        if not (
                            x + comp_width <= rx
                            or x >= rx + rw
                            or y + comp_height <= ry
                            or y >= ry + rh
                        ):
                            overlaps = True
                            break

                    if not overlaps:
                        # Calculate wasted space (simple heuristic)
                        waste = x + y
                        if waste < min_waste:
                            min_waste = waste
                            best_x = x
                            best_y = y

            # Place component at best position
            comp.position = Point(best_x + comp_width / 2, best_y + comp_height / 2)
            placed_rectangles.append((best_x, best_y, comp_width, comp_height))

    def _place_components_in_block(
        self,
        components: List[SchematicSymbol],
        block_x: float,
        block_y: float,
        block_width: float,
        block_height: float,
    ) -> None:
        """
        Place components within a rectangular block.

        Args:
            components: Components to place
            block_x: Block left position
            block_y: Block top position
            block_width: Block width
            block_height: Block height
        """
        if not components:
            return

        # Calculate grid within block
        cols = max(1, int(block_width / (self.grid_spacing * 0.8)))
        rows = max(1, math.ceil(len(components) / cols))

        spacing_x = block_width / cols if cols > 1 else self.grid_spacing
        spacing_y = block_height / rows if rows > 1 else self.grid_spacing

        for i, comp in enumerate(components):
            col = i % cols
            row = i // cols

            x = block_x + col * spacing_x + spacing_x / 2
            y = block_y + row * spacing_y + spacing_y / 2

            comp.position = Point(x, y)

    def _build_adjacency_map(
        self,
        components: List[SchematicSymbol],
        connections: List[NetConnection],
    ) -> Dict[SchematicSymbol, Set[SchematicSymbol]]:
        """
        Build an adjacency map showing which components are connected.

        Args:
            components: All components
            connections: Connections between components

        Returns:
            Dictionary mapping each component to its connected components
        """
        adjacency = {}

        for conn in connections:
            # Get all components involved in this connection
            connected_comps = set()
            for point in conn.start_points + conn.end_points:
                if point.symbol:
                    connected_comps.add(point.symbol)

            # Add connections between all pairs
            for comp1 in connected_comps:
                if comp1 not in adjacency:
                    adjacency[comp1] = set()
                for comp2 in connected_comps:
                    if comp1 != comp2:
                        adjacency[comp1].add(comp2)

        return adjacency

    def arrange_components(
        self,
        components: List[SchematicSymbol],
        arrangement: str = "grid",
        **kwargs,
    ) -> None:
        """
        Arrange components using the specified algorithm.

        Args:
            components: Components to arrange
            arrangement: Arrangement algorithm to use
            **kwargs: Additional algorithm-specific parameters
        """
        logger.info(f"Arranging {len(components)} components using {arrangement}")

        if arrangement == "grid":
            self._arrange_grid(components)
        elif arrangement == "circular":
            self._arrange_circular(components)
        elif arrangement == "force_directed":
            self._arrange_force_directed(components)
        else:
            logger.warning(f"Unknown arrangement: {arrangement}, using grid")
            self._arrange_grid(components)

    def _arrange_grid(self, components: List[SchematicSymbol]) -> None:
        """Simple grid arrangement."""
        cols = math.ceil(math.sqrt(len(components)))
        for i, comp in enumerate(components):
            row = i // cols
            col = i % cols
            comp.position = Point(
                self.margin + col * self.grid_spacing,
                self.margin + row * self.grid_spacing,
            )

    def _arrange_circular(self, components: List[SchematicSymbol]) -> None:
        """Circular arrangement."""
        if not components:
            return

        radius = len(components) * self.grid_spacing / (2 * math.pi)
        center_x = radius + self.margin
        center_y = radius + self.margin

        angle_step = 2 * math.pi / len(components)
        for i, comp in enumerate(components):
            angle = i * angle_step
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            comp.position = Point(x, y)

    def _arrange_force_directed(self, components: List[SchematicSymbol]) -> None:
        """
        Simple force-directed placement algorithm.
        
        This is a Python implementation that simulates forces between components
        to achieve an aesthetically pleasing layout.
        """
        # Initialize with random positions
        for comp in components:
            comp.position = Point(
                random.uniform(self.margin, 200),
                random.uniform(self.margin, 200),
            )

        # Run force simulation
        for iteration in range(50):
            forces = {}
            
            for comp in components:
                fx, fy = 0.0, 0.0
                
                # Repulsion between all components
                for other in components:
                    if comp != other:
                        dx = comp.position.x - other.position.x
                        dy = comp.position.y - other.position.y
                        dist = max(0.1, math.sqrt(dx * dx + dy * dy))
                        
                        force = 1000 / (dist * dist)
                        fx += (dx / dist) * force
                        fy += (dy / dist) * force
                
                forces[comp] = (fx, fy)
            
            # Apply forces
            for comp, (fx, fy) in forces.items():
                comp.position = Point(
                    comp.position.x + fx * 0.01,
                    comp.position.y + fy * 0.01,
                )

    def route_connections(
        self, connections: List[NetConnection], components: List[SchematicSymbol]
    ) -> List[Line]:
        """
        Route connections between placed components.

        Args:
            connections: Net connections to route
            components: Placed components

        Returns:
            List of wire lines for the connections
        """
        wires = []

        for conn in connections:
            # Route each connection
            # This is a simplified routing - just direct lines
            if conn.start_points and conn.end_points:
                start = conn.start_points[0]
                end = conn.end_points[0]

                if start.symbol and end.symbol:
                    # Get pin positions
                    start_pos = self._get_pin_position(start.symbol, start.pin)
                    end_pos = self._get_pin_position(end.symbol, end.pin)

                    if start_pos and end_pos:
                        wire = Line(start=start_pos, end=end_pos)
                        wires.append(wire)

        return wires

    def _get_pin_position(
        self, symbol: SchematicSymbol, pin_name: str
    ) -> Optional[Point]:
        """
        Get the position of a pin on a symbol.

        Args:
            symbol: The schematic symbol
            pin_name: Name of the pin

        Returns:
            Position of the pin, or None if not found
        """
        for pin in symbol.pins:
            if pin.name == pin_name or pin.number == pin_name:
                # Calculate pin position relative to symbol
                # This is simplified - actual implementation would consider rotation
                return Point(
                    symbol.position.x + pin.position.x,
                    symbol.position.y + pin.position.y,
                )
        return None