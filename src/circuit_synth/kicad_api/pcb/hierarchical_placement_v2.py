"""
Hierarchical placement algorithm for PCB components with courtyard collision detection.

This is an updated version that uses actual courtyard geometry for collision detection
instead of simple bounding boxes.
"""

import logging
from typing import Dict, List, Optional, Tuple

from ..types import Footprint, Point
from .base import ComponentWrapper, PlacementAlgorithm
from .bbox import BoundingBox
from .courtyard_collision import CourtyardCollisionDetector, Polygon
from .grouping import ComponentGroup, group_by_hierarchy, group_groups

logger = logging.getLogger(__name__)


class HierarchicalPlacerV2(PlacementAlgorithm):
    """
    Implements hierarchical placement of PCB components with courtyard collision detection.

    Components are grouped by their hierarchical path and packed using
    a greedy algorithm that places larger components first.
    Uses actual courtyard geometry for accurate collision detection.
    """

    def __init__(
        self,
        component_spacing: float = 0.5,  # mm
        group_spacing: float = 2.5,  # mm
        use_courtyard: bool = True,
    ):  # Use courtyard for collision
        """
        Initialize the hierarchical placer.

        Args:
            component_spacing: Spacing between components in mm
            group_spacing: Spacing between hierarchical groups in mm
            use_courtyard: If True, use courtyard geometry for collision detection
        """
        self.component_spacing = component_spacing
        self.group_spacing = group_spacing
        self.use_courtyard = use_courtyard
        self.collision_detector = CourtyardCollisionDetector(spacing=component_spacing)
        self.placed_footprints: List[Footprint] = []

    def place(
        self,
        components: List[ComponentWrapper],
        connections: List[Tuple[str, str]],
        board_width: float = 100.0,
        board_height: float = 100.0,
        **kwargs,
    ) -> Dict[str, Point]:
        """
        Place components using hierarchical algorithm with courtyard collision detection.

        Args:
            components: List of components to place
            connections: List of (ref1, ref2) tuples representing connections
            board_width: Board width in mm
            board_height: Board height in mm
            **kwargs: Algorithm-specific parameters

        Returns:
            Dictionary mapping component references to positions
        """
        # Reset placed footprints list
        self.placed_footprints.clear()

        # Convert ComponentWrappers to footprints for backward compatibility
        footprints = [comp.footprint for comp in components]

        # Create board outline polygon
        board_vertices = [
            (0, 0),
            (board_width, 0),
            (board_width, board_height),
            (0, board_height),
        ]
        self.board_outline = Polygon(board_vertices)

        # Call the placement method
        self.place_components(footprints, BoundingBox(0, 0, board_width, board_height))

        # Extract positions from footprints
        positions = {}
        for comp in components:
            positions[comp.reference] = comp.footprint.position

        return positions

    def place_components(
        self, footprints: List[Footprint], board_outline: Optional[BoundingBox] = None
    ) -> None:
        """
        Place components using hierarchical packing algorithm with courtyard collision.

        Args:
            footprints: List of footprints to place
            board_outline: Optional board outline to constrain placement
        """
        logger.info(
            f"Starting hierarchical placement v2 of {len(footprints)} components"
        )
        logger.info(f"Using courtyard collision detection: {self.use_courtyard}")

        # Store board outline for constraint checking
        self.board_bbox = board_outline or BoundingBox(0, 0, 100, 100)
        logger.info(f"Board outline: {self.board_bbox}")

        # Wrap footprints in placement-aware wrappers
        components = [ComponentWrapper(fp) for fp in footprints]

        # Filter out locked components
        unlocked_components = [c for c in components if not c.is_locked]
        logger.info(f"Found {len(unlocked_components)} unlocked components to place")

        if not unlocked_components:
            logger.warning("No unlocked components to place")
            return

        # Group components by hierarchy
        groups = self._group_by_hierarchy(unlocked_components)
        logger.info(f"Grouped components into {len(groups)} hierarchical groups")

        # Pack each group
        for path, group in groups.items():
            logger.debug(f"Packing group '{path}' with {len(group)} components")
            self._pack_group(group)

        # Recursively pack groups into super-groups
        while len(groups) > 1:
            # Group the groups at the next level up
            groups = self._group_groups(groups)
            logger.debug(f"Packing {len(groups)} super-groups")

            for path, super_group in groups.items():
                self._pack_group(super_group)

        logger.info("Hierarchical placement v2 complete")

    def _group_by_hierarchy(
        self, components: List[ComponentWrapper]
    ) -> Dict[str, ComponentGroup]:
        """Group components by their hierarchical level."""
        return group_by_hierarchy(components)

    def _group_groups(
        self, groups: Dict[str, ComponentGroup]
    ) -> Dict[str, ComponentGroup]:
        """Group component groups by the next level up in hierarchy."""
        return group_groups(groups)

    def _pack_group(self, group: ComponentGroup) -> None:
        """
        Pack components in a group using greedy algorithm with courtyard collision.

        Components are placed in order of decreasing area, using
        corner-based placement points to minimize total area.
        """
        if not group:
            return

        # Sort by decreasing area
        sorted_items = sorted(
            group, key=lambda item: self._get_area(item), reverse=True
        )

        placement_points = []  # List of (x, y) tuples

        for item in sorted_items:
            if self._is_locked(item):
                continue

            if placement_points:
                # Find best placement point
                best_point = self._find_best_placement_point(item, placement_points)

                if best_point:
                    self._set_position(item, best_point[0], best_point[1])
                    # Only remove from placement_points if it was actually in the list
                    if best_point in placement_points:
                        placement_points.remove(best_point)
                else:
                    # No valid placement point found, try to place within board
                    self._place_at_board_edge(item)
            else:
                # First item - place at top-left with margin
                if not self.placed_footprints:
                    # Place first item with margin from board edge
                    margin = 10.0  # 10mm margin from board edge
                    self._set_position(item, margin, margin)

            # Add the placed footprint to our tracking list
            if isinstance(item, ComponentWrapper):
                self.placed_footprints.append(item.footprint)

            # Add new placement points based on the placed item
            item_pos = self._get_position(item)
            item_polygon = self._get_item_polygon(item)
            bbox = item_polygon.get_bounding_box()

            # Add placement points around the item with spacing
            spacing = self._get_spacing(item)
            placement_points.extend(
                [
                    (bbox[0] - spacing, bbox[1]),  # Left side
                    (bbox[2] + spacing, bbox[1]),  # Right side
                    (bbox[0], bbox[1] - spacing),  # Top side
                    (bbox[0], bbox[3] + spacing),  # Bottom side
                ]
            )

    def _find_best_placement_point(
        self, item, placement_points: List[Tuple[float, float]]
    ) -> Optional[Tuple[float, float]]:
        """
        Find the best placement point that minimizes bounding box expansion.

        Uses courtyard collision detection to ensure no overlaps.

        Returns None if no valid placement point is found.
        """
        best_point = None
        smallest_size = float("inf")

        # Get the footprint from the item
        footprint = item.footprint if isinstance(item, ComponentWrapper) else None
        if not footprint:
            return None

        # Store original position
        orig_pos = footprint.position

        for point in placement_points:
            # Try placing item at this point
            footprint.position = Point(point[0], point[1])

            # Check if placement is within board boundaries
            if not self._is_within_board(footprint):
                continue

            # Check for collisions using courtyard detection
            if self.collision_detector.check_collision_with_placed(
                footprint, self.placed_footprints
            ):
                continue

            # Calculate resulting bounding box size
            all_footprints = self.placed_footprints + [footprint]
            bbox = self._get_combined_bbox_footprints(all_footprints)

            # Minimize area + aspect ratio penalty
            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]
            size = (
                width * height + abs(width - height) * 0.1
            )  # Prefer square-ish layouts

            if size < smallest_size:
                smallest_size = size
                best_point = point

        # Restore original position
        footprint.position = orig_pos

        return best_point

    def _place_at_board_edge(self, item):
        """Try to place item at board edge when no placement points work."""
        footprint = item.footprint if isinstance(item, ComponentWrapper) else None
        if not footprint:
            return

        # Try different positions along board edges
        margin = 5.0
        positions_to_try = [
            (margin, margin),  # Top-left
            (self.board_bbox.max_x - margin, margin),  # Top-right
            (margin, self.board_bbox.max_y - margin),  # Bottom-left
            (
                self.board_bbox.max_x - margin,
                self.board_bbox.max_y - margin,
            ),  # Bottom-right
        ]

        for x, y in positions_to_try:
            footprint.position = Point(x, y)
            if self._is_within_board(
                footprint
            ) and not self.collision_detector.check_collision_with_placed(
                footprint, self.placed_footprints
            ):
                return  # Successfully placed

        # If all else fails, use spiral search from center
        center_x = self.board_bbox.width() / 2
        center_y = self.board_bbox.height() / 2

        valid_pos = self.collision_detector.find_valid_position(
            footprint,
            center_x,
            center_y,
            self.placed_footprints,
            self.board_outline,
            search_radius=50.0,
            search_step=1.0,
        )

        if valid_pos:
            footprint.position = Point(valid_pos[0], valid_pos[1])
        else:
            logger.warning(f"Could not find valid position for {footprint.reference}")

    def _get_area(self, item) -> float:
        """Get area of an item (component or group)."""
        if isinstance(item, ComponentWrapper):
            return item.area
        else:
            # It's a ComponentGroup
            return item.bbox.area()

    def _is_locked(self, item) -> bool:
        """Check if an item is locked."""
        if isinstance(item, ComponentWrapper):
            return item.is_locked
        else:
            # ComponentGroup
            return item.is_locked

    def _set_position(self, item, x: float, y: float):
        """Set the position of an item."""
        if isinstance(item, ComponentWrapper):
            item.footprint.position = Point(x, y)
        else:
            # ComponentGroup - move all components
            current_bbox = item.bbox
            dx = x - current_bbox.min_x
            dy = y - current_bbox.min_y
            item.move(dx, dy)

    def _get_position(self, item) -> Point:
        """Get the position of an item."""
        if isinstance(item, ComponentWrapper):
            return item.footprint.position
        else:
            # ComponentGroup - return bottom-left corner
            bbox = item.bbox
            return Point(bbox.min_x, bbox.min_y)

    def _get_item_polygon(self, item) -> Polygon:
        """Get polygon representation of an item."""
        if isinstance(item, ComponentWrapper):
            return self.collision_detector.get_footprint_polygon(
                item.footprint, use_courtyard=self.use_courtyard
            )
        else:
            # ComponentGroup - create polygon from bounding box
            bbox = item.bbox
            vertices = [
                (bbox.min_x, bbox.min_y),
                (bbox.max_x, bbox.min_y),
                (bbox.max_x, bbox.max_y),
                (bbox.min_x, bbox.max_y),
            ]
            return Polygon(vertices)

    def _get_spacing(self, item) -> float:
        """Get the appropriate spacing for an item."""
        if isinstance(item, ComponentWrapper):
            return self.component_spacing
        else:
            return self.group_spacing

    def _is_within_board(self, footprint: Footprint) -> bool:
        """Check if a footprint is within the board outline."""
        polygon = self.collision_detector.get_footprint_polygon(
            footprint, use_courtyard=self.use_courtyard
        )
        bbox = polygon.get_bounding_box()

        # Add a small margin from board edge
        margin = 2.0  # 2mm margin

        return (
            bbox[0] >= self.board_bbox.min_x + margin
            and bbox[2] <= self.board_bbox.max_x - margin
            and bbox[1] >= self.board_bbox.min_y + margin
            and bbox[3] <= self.board_bbox.max_y - margin
        )

    def _get_combined_bbox_footprints(
        self, footprints: List[Footprint]
    ) -> Tuple[float, float, float, float]:
        """Get the combined bounding box of multiple footprints."""
        if not footprints:
            return 0, 0, 0, 0

        min_x = float("inf")
        min_y = float("inf")
        max_x = float("-inf")
        max_y = float("-inf")

        for fp in footprints:
            polygon = self.collision_detector.get_footprint_polygon(
                fp, use_courtyard=self.use_courtyard
            )
            bbox = polygon.get_bounding_box()

            min_x = min(min_x, bbox[0])
            min_y = min(min_y, bbox[1])
            max_x = max(max_x, bbox[2])
            max_y = max(max_y, bbox[3])

        return min_x, min_y, max_x, max_y
