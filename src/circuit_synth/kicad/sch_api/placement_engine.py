"""
Placement Engine for KiCad Schematic API.

Handles automatic component placement with various strategies including
edge placement, grid-based placement, and contextual placement.
"""

import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

from .models import PlacementInfo, PlacementStrategy

logger = logging.getLogger(__name__)


@dataclass
class BoundingBox:
    """Represents a bounding box for collision detection."""

    min_x: float
    min_y: float
    max_x: float
    max_y: float

    def contains_point(self, x: float, y: float) -> bool:
        """Check if a point is inside the bounding box."""
        return self.min_x <= x <= self.max_x and self.min_y <= y <= self.max_y

    def intersects(self, other: "BoundingBox") -> bool:
        """Check if this bounding box intersects with another."""
        return not (
            self.max_x < other.min_x
            or self.min_x > other.max_x
            or self.max_y < other.min_y
            or self.min_y > other.max_y
        )

    def expand(self, margin: float) -> "BoundingBox":
        """Return an expanded bounding box with the given margin."""
        return BoundingBox(
            self.min_x - margin,
            self.min_y - margin,
            self.max_x + margin,
            self.max_y + margin,
        )


class PlacementEngine:
    """
    Handles automatic component placement in schematics.

    This engine provides multiple placement strategies to automatically
    position components in a schematic while avoiding collisions and
    maintaining good layout practices.
    """

    # Constants for placement (in mm, matching KiCad units)
    GRID_SIZE = 2.54  # 100 mil standard grid
    COMPONENT_SPACING = 25.4  # 1000 mil between components
    MARGIN = 12.7  # 500 mil margin from edges
    MIN_SPACING = 7.62  # 300 mil minimum spacing

    # Component size estimates (width x height in mm)
    COMPONENT_SIZES = {
        "R": (10.16, 5.08),  # Resistor: 400x200 mil
        "C": (10.16, 5.08),  # Capacitor: 400x200 mil
        "L": (10.16, 5.08),  # Inductor: 400x200 mil
        "D": (10.16, 5.08),  # Diode: 400x200 mil
        "Q": (12.7, 10.16),  # Transistor: 500x400 mil
        "U": (20.32, 15.24),  # IC: 800x600 mil
        "J": (15.24, 12.7),  # Connector: 600x500 mil
        "SW": (10.16, 10.16),  # Switch: 400x400 mil
        "Y": (12.7, 7.62),  # Crystal: 500x300 mil
        "T": (25.4, 25.4),  # Transformer: 1000x1000 mil
        "K": (20.32, 15.24),  # Relay: 800x600 mil
        "F": (7.62, 5.08),  # Fuse: 300x200 mil
        "FB": (7.62, 5.08),  # Ferrite bead: 300x200 mil
        "BT": (15.24, 10.16),  # Battery: 600x400 mil
        "M": (30.48, 30.48),  # Motor: 1200x1200 mil
    }

    def __init__(self):
        """Initialize the placement engine."""
        self._component_positions: Dict[str, Tuple[float, float]] = {}
        self._bounding_boxes: Dict[str, BoundingBox] = {}
        self._type_groups: Dict[str, List[str]] = defaultdict(list)

    def find_next_position(
        self,
        schematic: Any,
        symbol_data: Dict[str, Any],
        strategy: Optional[PlacementStrategy] = None,
    ) -> Tuple[float, float]:
        """
        Find the optimal position for a new component.

        Args:
            schematic: The schematic object containing existing components
            symbol_data: Symbol data including type information
            strategy: Optional placement strategy to use

        Returns:
            Tuple of (x, y) coordinates for the component position
        """
        # Update internal state with current schematic
        self._update_state(schematic)

        # Determine strategy if not specified
        if strategy is None:
            strategy = self._determine_strategy(schematic, symbol_data)

        logger.debug(f"Using placement strategy: {strategy}")

        # Apply the selected strategy
        if strategy == PlacementStrategy.EDGE:
            return self._edge_placement(schematic, symbol_data)
        elif strategy == PlacementStrategy.GRID:
            return self._grid_placement(schematic, symbol_data)
        elif strategy == PlacementStrategy.CONTEXTUAL:
            return self._contextual_placement(schematic, symbol_data)
        else:
            # Fallback to edge placement
            return self._edge_placement(schematic, symbol_data)

    def snap_to_grid(self, position: Tuple[float, float]) -> Tuple[float, float]:
        """
        Snap a position to the nearest grid point.

        Args:
            position: The (x, y) position to snap

        Returns:
            Grid-aligned (x, y) position
        """
        x = round(position[0] / self.GRID_SIZE) * self.GRID_SIZE
        y = round(position[1] / self.GRID_SIZE) * self.GRID_SIZE
        return (x, y)

    def check_collision(
        self,
        position: Tuple[float, float],
        size: Tuple[float, float],
        exclude_refs: Optional[Set[str]] = None,
    ) -> Optional[str]:
        """
        Check if placing a component at the given position would cause a collision.

        Args:
            position: The (x, y) position to check
            size: The (width, height) of the component
            exclude_refs: Set of reference designators to exclude from collision check

        Returns:
            Reference of colliding component or None if no collision
        """
        if exclude_refs is None:
            exclude_refs = set()

        new_bbox = self._create_bounding_box(position, size)

        for ref, bbox in self._bounding_boxes.items():
            if ref not in exclude_refs and bbox.intersects(new_bbox):
                return ref

        return None

    def _update_state(self, schematic: Any) -> None:
        """Update internal state based on current schematic."""
        self._component_positions.clear()
        self._bounding_boxes.clear()
        self._type_groups.clear()

        for component in schematic.components:
            if hasattr(component, "position") and component.position:
                pos = (component.position[0], component.position[1])
                self._component_positions[component.reference] = pos

                # Estimate component size
                prefix = self._get_component_prefix(component.reference)
                size = self.COMPONENT_SIZES.get(
                    prefix, (15.24, 10.16)
                )  # Default 600x400 mil

                # Create bounding box
                bbox = self._create_bounding_box(pos, size)
                self._bounding_boxes[component.reference] = bbox

                # Group by type
                self._type_groups[prefix].append(component.reference)

    def _determine_strategy(
        self, schematic: Any, symbol_data: Dict[str, Any]
    ) -> PlacementStrategy:
        """Determine the best placement strategy based on context."""
        component_count = len(schematic.components)

        # For first few components, use edge placement
        if component_count < 10:
            return PlacementStrategy.EDGE

        # For larger schematics, consider grid placement
        if component_count > 50:
            return PlacementStrategy.GRID

        # Check if this is a related component type
        lib_id = symbol_data.get("lib_id", "")
        if self._has_related_components(lib_id):
            return PlacementStrategy.CONTEXTUAL

        return PlacementStrategy.EDGE

    def _edge_placement(
        self, schematic: Any, symbol_data: Dict[str, Any]
    ) -> Tuple[float, float]:
        """
        Place component at the right edge of existing components.

        This strategy places new components in a column to the right of
        existing components, maintaining vertical grouping by type.
        """
        if not self._component_positions:
            # First component - place at origin with margin
            return self.snap_to_grid((self.MARGIN, self.MARGIN))

        # Find rightmost position
        max_x = max(pos[0] for pos in self._component_positions.values())

        # Get component type for vertical grouping
        lib_id = symbol_data.get("lib_id", "")
        prefix = self._get_prefix_from_lib_id(lib_id)

        # Find Y position based on type grouping
        y_position = self._get_type_based_y_position(
            prefix, max_x + self.COMPONENT_SPACING
        )

        # Calculate new position
        new_x = max_x + self.COMPONENT_SPACING
        new_y = y_position

        return self.snap_to_grid((new_x, new_y))

    def _grid_placement(
        self, schematic: Any, symbol_data: Dict[str, Any]
    ) -> Tuple[float, float]:
        """
        Place component on a regular grid pattern.

        This strategy fills a grid from left to right, top to bottom,
        skipping occupied positions.
        """
        # Define grid parameters
        grid_cols = 10  # Number of columns in grid
        grid_spacing_x = self.COMPONENT_SPACING
        grid_spacing_y = self.COMPONENT_SPACING * 0.8  # Slightly tighter vertical

        # Get component size
        lib_id = symbol_data.get("lib_id", "")
        prefix = self._get_prefix_from_lib_id(lib_id)
        size = self.COMPONENT_SIZES.get(prefix, (15.24, 10.16))

        # Search for next available grid position
        row = 0
        while True:
            for col in range(grid_cols):
                x = self.MARGIN + (col * grid_spacing_x)
                y = self.MARGIN + (row * grid_spacing_y)

                # Check if position is available
                if not self.check_collision((x, y), size):
                    return self.snap_to_grid((x, y))

            row += 1
            if row > 100:  # Safety limit
                # Fallback to edge placement
                return self._edge_placement(schematic, symbol_data)

    def _contextual_placement(
        self, schematic: Any, symbol_data: Dict[str, Any]
    ) -> Tuple[float, float]:
        """
        Place component near related components.

        This strategy groups related components together, such as
        placing bypass capacitors near ICs or pull-up resistors near switches.
        """
        lib_id = symbol_data.get("lib_id", "")
        prefix = self._get_prefix_from_lib_id(lib_id)

        # Find related components
        related_refs = self._find_related_components(prefix, lib_id)

        if not related_refs:
            # No related components, use edge placement
            return self._edge_placement(schematic, symbol_data)

        # Calculate center of related components
        related_positions = [
            self._component_positions[ref]
            for ref in related_refs
            if ref in self._component_positions
        ]

        if not related_positions:
            return self._edge_placement(schematic, symbol_data)

        center_x = sum(pos[0] for pos in related_positions) / len(related_positions)
        center_y = sum(pos[1] for pos in related_positions) / len(related_positions)

        # Find nearest free position around the center
        size = self.COMPONENT_SIZES.get(prefix, (15.24, 10.16))
        position = self._find_nearest_free_position((center_x, center_y), size)

        return self.snap_to_grid(position)

    def _get_type_based_y_position(self, prefix: str, x: float) -> float:
        """Get Y position based on component type grouping."""
        # Define vertical zones for different component types
        type_zones = {
            "R": 0,  # Resistors at top
            "C": 1,  # Capacitors below resistors
            "L": 2,  # Inductors
            "D": 3,  # Diodes
            "Q": 4,  # Transistors
            "U": 5,  # ICs
            "J": 6,  # Connectors
            "SW": 7,  # Switches
            "default": 8,
        }

        zone = type_zones.get(prefix, type_zones["default"])
        base_y = self.MARGIN + (zone * self.COMPONENT_SPACING * 0.8)

        # Check if there are already components of this type at this X
        same_type_at_x = []
        for ref in self._type_groups.get(prefix, []):
            if ref in self._component_positions:
                pos = self._component_positions[ref]
                if abs(pos[0] - x) < self.MIN_SPACING:
                    same_type_at_x.append(pos[1])

        # If there are components of same type, place below them
        if same_type_at_x:
            return max(same_type_at_x) + self.COMPONENT_SPACING * 0.8

        return base_y

    def _find_nearest_free_position(
        self, center: Tuple[float, float], size: Tuple[float, float]
    ) -> Tuple[float, float]:
        """Find the nearest free position to a center point."""
        # Search in expanding circles
        search_radius = self.MIN_SPACING
        max_radius = self.COMPONENT_SPACING * 5

        while search_radius < max_radius:
            # Try positions in a circle around the center
            for angle in range(0, 360, 45):  # Check 8 directions
                import math

                rad = math.radians(angle)
                x = center[0] + search_radius * math.cos(rad)
                y = center[1] + search_radius * math.sin(rad)

                # Snap to grid
                pos = self.snap_to_grid((x, y))

                # Check if position is free
                if not self.check_collision(pos, size):
                    return pos

            search_radius += self.MIN_SPACING

        # Fallback to edge placement
        return self._edge_placement(None, {})

    def _create_bounding_box(
        self, position: Tuple[float, float], size: Tuple[float, float]
    ) -> BoundingBox:
        """Create a bounding box for a component."""
        half_width = size[0] / 2
        half_height = size[1] / 2

        return BoundingBox(
            position[0] - half_width,
            position[1] - half_height,
            position[0] + half_width,
            position[1] + half_height,
        )

    def _get_component_prefix(self, reference: str) -> str:
        """Extract prefix from component reference."""
        import re

        match = re.match(r"^([A-Z]+)\d+", reference)
        return match.group(1) if match else ""

    def _get_prefix_from_lib_id(self, lib_id: str) -> str:
        """Get component prefix from library ID."""
        # This is a simplified version - in practice, would use ReferenceManager
        prefix_map = {
            "Device:R": "R",
            "Device:C": "C",
            "Device:L": "L",
            "Device:D": "D",
            "Device:Q_": "Q",
            "Amplifier_": "U",
            "MCU_": "U",
            "Connector": "J",
            "Switch": "SW",
        }

        for pattern, prefix in prefix_map.items():
            if lib_id.startswith(pattern):
                return prefix

        return "U"  # Default

    def _has_related_components(self, lib_id: str) -> bool:
        """Check if there are related components in the schematic."""
        prefix = self._get_prefix_from_lib_id(lib_id)
        return bool(self._type_groups.get(prefix))

    def _find_related_components(self, prefix: str, lib_id: str) -> List[str]:
        """Find components that are related to the given type."""
        # For now, just return components with the same prefix
        # In a more sophisticated implementation, this could consider
        # actual relationships (e.g., bypass caps near ICs)
        return self._type_groups.get(prefix, [])
