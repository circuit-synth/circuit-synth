# -*- coding: utf-8 -*-
#
# connection_aware_collision_manager.py
#
# Connection-aware placement algorithm that extends CollisionManager
# Places components based on their electrical connections to minimize wire length
#

import logging
import math
from typing import Dict, List, Optional, Set, Tuple

from .collision_detection import BBox
from .collision_manager import MIN_COMPONENT_SPACING, CollisionManager
from .connection_analyzer import ConnectionAnalyzer

logger = logging.getLogger(__name__)


class ConnectionAwareCollisionManager(CollisionManager):
    """
    Extends CollisionManager with connection-aware placement.
    Places components to minimize total wire length while avoiding collisions.
    """

    def __init__(self, sheet_size: Tuple[float, float] = (210.0, 297.0), grid=2.54):
        """
        Initialize connection-aware collision manager.

        Args:
            sheet_size: (width_mm, height_mm), e.g. (210, 297) for A4
            grid: snap spacing in mm, usually 2.54 (100 mil)
        """
        super().__init__(sheet_size, grid)
        self.connection_analyzer = ConnectionAnalyzer()
        self.placed_components: Dict[str, Tuple[float, float]] = {}
        self.component_dimensions: Dict[str, Tuple[float, float]] = {}

        # Placement parameters
        self.search_radius_increment = 10.0  # mm
        self.max_search_radius = 100.0  # mm
        self.angular_steps = 8  # Number of angles to try in spiral search

    def analyze_connections(self, circuit) -> None:
        """
        Analyze circuit connections before placement.

        Args:
            circuit: Circuit object with components and nets
        """
        self.connection_analyzer.analyze_circuit(circuit)

    def place_component_connection_aware(
        self, comp_ref: str, symbol_width: float, symbol_height: float
    ) -> Tuple[float, float]:
        """
        Place a component considering its connections to already-placed components.

        Args:
            comp_ref: Component reference (e.g., "R1")
            symbol_width: Width of the symbol in mm
            symbol_height: Height of the symbol in mm

        Returns:
            (center_x, center_y) position for the component
        """
        logger.debug(
            f"Connection-aware placement for {comp_ref} ({symbol_width:.2f}x{symbol_height:.2f}mm)"
        )

        # Store dimensions for later use
        self.component_dimensions[comp_ref] = (symbol_width, symbol_height)

        # Get connected components that are already placed
        connected_comps = self.connection_analyzer.get_connected_components(comp_ref)
        placed_connections = [
            (ref, count)
            for ref, count in connected_comps
            if ref in self.placed_components
        ]

        if not placed_connections:
            # No connected components placed yet, use regular placement
            logger.debug(
                f"No connected components placed yet for {comp_ref}, using default placement"
            )
            position = self.place_symbol(symbol_width, symbol_height)
        else:
            # Calculate ideal position based on connected components
            ideal_x, ideal_y = self._calculate_ideal_position(
                comp_ref, placed_connections
            )
            logger.debug(
                f"Ideal position for {comp_ref}: ({ideal_x:.2f}, {ideal_y:.2f})"
            )

            # Find nearest valid position using spiral search
            position = self._find_nearest_valid_position(
                ideal_x, ideal_y, symbol_width, symbol_height
            )

            if position is None:
                # Fallback to regular placement if no valid position found
                logger.warning(
                    f"Could not find valid position near ideal for {comp_ref}, using fallback"
                )
                position = self.place_symbol(symbol_width, symbol_height)

        # Record the placement
        self.placed_components[comp_ref] = position
        logger.debug(f"Placed {comp_ref} at ({position[0]:.2f}, {position[1]:.2f})")

        return position

    def _calculate_ideal_position(
        self, comp_ref: str, placed_connections: List[Tuple[str, int]]
    ) -> Tuple[float, float]:
        """
        Calculate ideal position as weighted center of connected components.

        Args:
            comp_ref: Component being placed
            placed_connections: List of (connected_ref, connection_count) for placed components

        Returns:
            (ideal_x, ideal_y) position
        """
        total_weight = 0.0
        weighted_x = 0.0
        weighted_y = 0.0

        for connected_ref, connection_count in placed_connections:
            pos_x, pos_y = self.placed_components[connected_ref]
            weight = float(connection_count)

            weighted_x += pos_x * weight
            weighted_y += pos_y * weight
            total_weight += weight

        if total_weight > 0:
            ideal_x = weighted_x / total_weight
            ideal_y = weighted_y / total_weight
        else:
            # Fallback to center of sheet
            ideal_x = self.sheet_size[0] / 2
            ideal_y = self.sheet_size[1] / 2

        return (ideal_x, ideal_y)

    def _find_nearest_valid_position(
        self, ideal_x: float, ideal_y: float, symbol_width: float, symbol_height: float
    ) -> Optional[Tuple[float, float]]:
        """
        Find the nearest collision-free position to the ideal position using spiral search.

        Args:
            ideal_x, ideal_y: Ideal position
            symbol_width, symbol_height: Component dimensions

        Returns:
            (x, y) position or None if no valid position found
        """
        # First try the ideal position
        test_x = self.snap_to_grid(ideal_x)
        test_y = self.snap_to_grid(ideal_y)

        if self._try_position(test_x, test_y, symbol_width, symbol_height):
            return (test_x, test_y)

        # Spiral search pattern
        radius = self.search_radius_increment

        while radius <= self.max_search_radius:
            # Try positions in a circle at current radius
            for i in range(self.angular_steps):
                angle = (2 * math.pi * i) / self.angular_steps

                # Calculate test position
                offset_x = radius * math.cos(angle)
                offset_y = radius * math.sin(angle)

                test_x = self.snap_to_grid(ideal_x + offset_x)
                test_y = self.snap_to_grid(ideal_y + offset_y)

                if self._try_position(test_x, test_y, symbol_width, symbol_height):
                    return (test_x, test_y)

            # Increase radius for next iteration
            radius += self.search_radius_increment

        return None

    def _try_position(
        self,
        center_x: float,
        center_y: float,
        symbol_width: float,
        symbol_height: float,
    ) -> bool:
        """
        Try to place a component at the given position.

        Args:
            center_x, center_y: Center position to try
            symbol_width, symbol_height: Component dimensions

        Returns:
            True if position is valid and component was placed
        """
        # Calculate bounding box with proper spacing
        # Use MIN_COMPONENT_SPACING for consistent spacing
        padding = MIN_COMPONENT_SPACING / 2  # Half on each side
        x_min = center_x - (symbol_width / 2) - padding
        y_min = center_y - (symbol_height / 2) - padding
        x_max = center_x + (symbol_width / 2) + padding
        y_max = center_y + (symbol_height / 2) + padding

        test_bbox = BBox(x_min, y_min, x_max, y_max)

        # Try to add the bounding box
        if self.detector.add_bbox(test_bbox):
            # Update tracking variables
            if symbol_height > self.current_row_height:
                self.current_row_height = symbol_height

            # Update next position for fallback placement
            self.current_x = center_x + (symbol_width / 2) + MIN_COMPONENT_SPACING

            return True

        return False

    def get_placement_metrics(self) -> Dict[str, float]:
        """
        Calculate metrics for the current placement.

        Returns:
            Dictionary with placement metrics
        """
        metrics = {
            "total_components": len(self.placed_components),
            "total_wire_length": 0.0,
            "average_wire_length": 0.0,
            "max_wire_length": 0.0,
            "placement_density": 0.0,
        }

        if not self.placed_components:
            return metrics

        # Calculate wire lengths
        wire_lengths = []
        for (comp1, comp2), count in self.connection_analyzer.connection_matrix.items():
            if comp1 in self.placed_components and comp2 in self.placed_components:
                x1, y1 = self.placed_components[comp1]
                x2, y2 = self.placed_components[comp2]
                distance = abs(x2 - x1) + abs(y2 - y1)  # Manhattan distance
                wire_lengths.extend([distance] * count)

        if wire_lengths:
            metrics["total_wire_length"] = sum(wire_lengths)
            metrics["average_wire_length"] = sum(wire_lengths) / len(wire_lengths)
            metrics["max_wire_length"] = max(wire_lengths)

        # Calculate placement density
        if self.placed_components:
            min_x = min(pos[0] for pos in self.placed_components.values())
            max_x = max(pos[0] for pos in self.placed_components.values())
            min_y = min(pos[1] for pos in self.placed_components.values())
            max_y = max(pos[1] for pos in self.placed_components.values())

            area_used = (max_x - min_x) * (max_y - min_y)
            total_component_area = sum(
                w * h for w, h in self.component_dimensions.values()
            )

            if area_used > 0:
                metrics["placement_density"] = total_component_area / area_used

        return metrics

    def reset_placement(self):
        """Reset placement state while keeping connection analysis."""
        self.clear()  # Clear collision detection
        self.placed_components.clear()
        self.component_dimensions.clear()
