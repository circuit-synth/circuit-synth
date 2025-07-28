"""
Improved hierarchical placement algorithm with spiral search pattern.

This algorithm improves upon the basic hierarchical placement by using
a spiral search pattern to find the nearest valid position for components,
rather than just trying the 4 corners of bounding boxes.
"""

import logging
import math
from typing import Dict, List, Optional, Tuple

from ..types import Footprint, Point
from .base import ComponentWrapper, PlacementAlgorithm
from .bbox import BoundingBox
from .grouping import ComponentGroup, group_by_hierarchy, group_groups
from .hierarchical_placement import HierarchicalPlacer

logger = logging.getLogger(__name__)


class SpiralHierarchicalPlacer(HierarchicalPlacer):
    """
    Improved hierarchical placement using spiral search for optimal positions.

    This algorithm:
    1. Groups components by hierarchy (like the original)
    2. Uses connection information to calculate ideal positions
    3. Searches in a spiral pattern from the ideal position to find valid placement
    4. Ensures minimum spacing between all components
    """

    def __init__(
        self,
        component_spacing: float = 0.5,  # mm
        group_spacing: float = 2.5,  # mm
        spiral_step: float = 0.5,  # mm - step size for spiral search
        max_spiral_radius: float = 50.0,
    ):  # mm - maximum search radius
        """
        Initialize the spiral hierarchical placer.

        Args:
            component_spacing: Spacing between components in mm
            group_spacing: Spacing between hierarchical groups in mm
            spiral_step: Step size for spiral search in mm
            max_spiral_radius: Maximum radius to search in mm
        """
        super().__init__(component_spacing, group_spacing)
        self.spiral_step = spiral_step
        self.max_spiral_radius = max_spiral_radius
        self._connection_map = {}  # Map of component connections
        self._placed_components = {}  # Map of placed component positions

    def place(
        self,
        components: List[ComponentWrapper],
        connections: List[Tuple[str, str]],
        board_width: float = 100.0,
        board_height: float = 100.0,
        **kwargs,
    ) -> Dict[str, Point]:
        """
        Place components using improved hierarchical algorithm with spiral search.

        Args:
            components: List of components to place
            connections: List of (ref1, ref2) tuples representing connections
            board_width: Board width in mm
            board_height: Board height in mm
            **kwargs: Algorithm-specific parameters

        Returns:
            Dictionary mapping component references to positions
        """
        # Build connection map for connection-aware placement
        self._build_connection_map(connections)

        # Clear placed components tracker
        self._placed_components.clear()

        # Call parent implementation which will use our overridden methods
        return super().place(
            components, connections, board_width, board_height, **kwargs
        )

    def _build_connection_map(self, connections: List[Tuple[str, str]]):
        """Build a map of which components are connected to each other."""
        self._connection_map.clear()

        for ref1, ref2 in connections:
            if ref1 not in self._connection_map:
                self._connection_map[ref1] = []
            if ref2 not in self._connection_map:
                self._connection_map[ref2] = []

            self._connection_map[ref1].append(ref2)
            self._connection_map[ref2].append(ref1)

        logger.debug(
            f"Built connection map with {len(self._connection_map)} connected components"
        )

    def _find_best_placement_point(
        self, item, placed_items: List, placement_points: List[Tuple[float, float]]
    ) -> Optional[Tuple[float, float]]:
        """
        Find the best placement point using spiral search from ideal position.

        This method:
        1. Calculates ideal position based on connected components
        2. Searches in a spiral pattern from that position
        3. Returns the nearest valid position that maintains spacing
        """
        # Calculate ideal position based on connections
        ideal_x, ideal_y = self._calculate_ideal_position(item, placed_items)

        # Try the ideal position first
        if self._is_valid_position(item, ideal_x, ideal_y, placed_items):
            logger.debug(
                f"Placing {self._get_reference(item)} at ideal position ({ideal_x:.2f}, {ideal_y:.2f})"
            )
            return (ideal_x, ideal_y)

        # Search in a spiral pattern from the ideal position
        best_position = self._spiral_search(item, ideal_x, ideal_y, placed_items)

        if best_position:
            logger.debug(
                f"Found position for {self._get_reference(item)} at ({best_position[0]:.2f}, {best_position[1]:.2f})"
            )
            return best_position

        # Fallback to original algorithm if spiral search fails
        logger.debug(
            f"Spiral search failed for {self._get_reference(item)}, falling back to corner placement"
        )
        return super()._find_best_placement_point(item, placed_items, placement_points)

    def _calculate_ideal_position(
        self, item, placed_items: List
    ) -> Tuple[float, float]:
        """
        Calculate ideal position based on connected components.

        Returns the "center of gravity" of all connected components that
        have already been placed.
        """
        ref = self._get_reference(item)

        # Get connected components
        connected_refs = self._connection_map.get(ref, [])
        if not connected_refs:
            # No connections, use board center
            return (self.board_outline.center()[0], self.board_outline.center()[1])

        # Find already-placed connected components
        placed_connected = []
        for connected_ref in connected_refs:
            # Check if this connected component is already placed
            for placed_item in placed_items:
                if self._get_reference(placed_item) == connected_ref:
                    placed_connected.append(placed_item)
                    break

        if not placed_connected:
            # No connected components placed yet, use board center
            return (self.board_outline.center()[0], self.board_outline.center()[1])

        # Calculate center of gravity of placed connected components
        total_x = 0
        total_y = 0
        for connected_item in placed_connected:
            bbox = self._get_bbox(connected_item)
            center_x, center_y = bbox.center()
            total_x += center_x
            total_y += center_y

        avg_x = total_x / len(placed_connected)
        avg_y = total_y / len(placed_connected)

        logger.debug(
            f"Ideal position for {ref}: ({avg_x:.2f}, {avg_y:.2f}) based on {len(placed_connected)} connected components"
        )

        return (avg_x, avg_y)

    def _spiral_search(
        self, item, start_x: float, start_y: float, placed_items: List
    ) -> Optional[Tuple[float, float]]:
        """
        Search in a spiral pattern from the starting position.

        Returns the first valid position found, or None if no valid position
        is found within max_spiral_radius.
        """
        # Spiral parameters
        angle = 0
        radius = 0

        while radius <= self.max_spiral_radius:
            # Calculate position on spiral
            x = start_x + radius * math.cos(angle)
            y = start_y + radius * math.sin(angle)

            # Check if this position is valid
            if self._is_valid_position(item, x, y, placed_items):
                return (x, y)

            # Update spiral parameters
            # Increase angle proportionally to maintain consistent spacing
            if radius > 0:
                angle += self.spiral_step / radius
            else:
                angle += math.pi / 4  # 45 degrees for first step

            # Increase radius as we complete rotations
            radius = (angle / (2 * math.pi)) * self.spiral_step

        return None

    def _is_valid_position(self, item, x: float, y: float, placed_items: List) -> bool:
        """
        Check if placing item at (x, y) is valid.

        A position is valid if:
        1. The item doesn't overlap with any placed items
        2. The item is within board boundaries
        3. Minimum spacing is maintained
        """
        # Store original position
        if isinstance(item, ComponentWrapper):
            orig_x = item.footprint.position.x
            orig_y = item.footprint.position.y
        else:
            # ComponentGroup
            orig_bbox = item.bbox

        # Try placing at this position
        self._set_bottom_left(item, x, y)

        # Check board boundaries
        if hasattr(self, "board_outline") and self.board_outline:
            item_bbox = self._get_bbox(item)
            if not self._bbox_within_board(item_bbox):
                # Restore position
                if isinstance(item, ComponentWrapper):
                    item.move_to(orig_x, orig_y)
                else:
                    current_bbox = item.bbox
                    dx = orig_bbox.min_x - current_bbox.min_x
                    dy = orig_bbox.min_y - current_bbox.min_y
                    item.move(dx, dy)
                return False

        # Check for overlaps with placed items
        for placed in placed_items:
            if self._touches(item, placed):
                # Restore position
                if isinstance(item, ComponentWrapper):
                    item.move_to(orig_x, orig_y)
                else:
                    current_bbox = item.bbox
                    dx = orig_bbox.min_x - current_bbox.min_x
                    dy = orig_bbox.min_y - current_bbox.min_y
                    item.move(dx, dy)
                return False

        # Restore position (we'll set it properly later)
        if isinstance(item, ComponentWrapper):
            item.move_to(orig_x, orig_y)
        else:
            current_bbox = item.bbox
            dx = orig_bbox.min_x - current_bbox.min_x
            dy = orig_bbox.min_y - current_bbox.min_y
            item.move(dx, dy)

        return True

    def _get_reference(self, item) -> str:
        """Get the reference designator of an item."""
        if isinstance(item, ComponentWrapper):
            return item.reference
        else:
            # For ComponentGroup, return a representative reference
            if item:
                return f"Group_{id(item)}"
            return "Unknown"

    def _set_bottom_left(self, item, x: float, y: float):
        """
        Override to track placed components.
        """
        super()._set_bottom_left(item, x, y)

        # Track this placement
        ref = self._get_reference(item)
        if ref and isinstance(item, ComponentWrapper):
            self._placed_components[ref] = (x, y)
