"""
Hierarchical placement algorithm for PCB components.

Based on the HierPlace algorithm, this arranges components based on their
schematic hierarchy using a greedy packing approach.
"""

import logging
from typing import Dict, List, Optional, Tuple

from ..types import Footprint, Point
from .base import ComponentWrapper, PlacementAlgorithm
from .bbox import BoundingBox
from .grouping import ComponentGroup, group_by_hierarchy, group_groups

logger = logging.getLogger(__name__)


class HierarchicalPlacer(PlacementAlgorithm):
    """
    Implements hierarchical placement of PCB components.

    Components are grouped by their hierarchical path and packed using
    a greedy algorithm that places larger components first.
    """

    def __init__(
        self, component_spacing: float = 0.5, group_spacing: float = 2.5  # mm
    ):  # mm
        """
        Initialize the hierarchical placer.

        Args:
            component_spacing: Spacing between components in mm
            group_spacing: Spacing between hierarchical groups in mm
        """
        self.component_spacing = component_spacing
        self.group_spacing = group_spacing

    def place(
        self,
        components: List[ComponentWrapper],
        connections: List[Tuple[str, str]],
        board_width: float = 100.0,
        board_height: float = 100.0,
        **kwargs,
    ) -> Dict[str, Point]:
        """
        Place components using hierarchical algorithm.

        Args:
            components: List of components to place
            connections: List of (ref1, ref2) tuples representing connections
            board_width: Board width in mm
            board_height: Board height in mm
            **kwargs: Algorithm-specific parameters

        Returns:
            Dictionary mapping component references to positions
        """
        # Convert ComponentWrappers to footprints for backward compatibility
        footprints = [comp.footprint for comp in components]

        # Create board outline
        board_outline = BoundingBox(0, 0, board_width, board_height)

        # Call the existing placement method
        self.place_components(footprints, board_outline)

        # Extract positions from footprints
        positions = {}
        for comp in components:
            positions[comp.reference] = comp.footprint.position

        return positions

    def place_components(
        self, footprints: List[Footprint], board_outline: Optional[BoundingBox] = None
    ) -> None:
        """
        Place components using hierarchical packing algorithm.

        Args:
            footprints: List of footprints to place
            board_outline: Optional board outline to constrain placement
        """
        logger.info(f"Starting hierarchical placement of {len(footprints)} components")

        # Store board outline for constraint checking
        self.board_outline = board_outline or BoundingBox(0, 0, 100, 100)
        logger.info(f"Board outline: {self.board_outline}")

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

        logger.info("Hierarchical placement complete")

    def _group_by_hierarchy(
        self, components: List[ComponentWrapper]
    ) -> Dict[str, ComponentGroup]:
        """Group components by their hierarchical level."""
        groups = group_by_hierarchy(components)

        # Apply component spacing to each group
        for group in groups.values():
            for component in group:
                # Inflate the component's bounding box by the spacing
                # Force calculation of bbox if not cached
                original_bbox = component.bbox  # This will calculate and cache the bbox
                # Save the original bbox
                component._original_bbox_cache = original_bbox
                # Now inflate it for collision detection
                component._bbox_cache = original_bbox.inflate(self.component_spacing)
                logger.debug(
                    f"Component {component.reference}: original bbox {original_bbox}, inflated to {component._bbox_cache}"
                )

        return groups

    def _group_groups(
        self, groups: Dict[str, ComponentGroup]
    ) -> Dict[str, ComponentGroup]:
        """Group component groups by the next level up in hierarchy."""
        super_groups = group_groups(groups)

        # Apply group spacing
        for super_group in super_groups.values():
            for group in super_group:
                if isinstance(group, ComponentGroup):
                    # For groups, we need to apply spacing around the whole group
                    # This is handled in the packing algorithm
                    pass

        return super_groups

    def _pack_group(self, group: ComponentGroup) -> None:
        """
        Pack components in a group using greedy algorithm.

        Components are placed in order of decreasing area, using
        corner-based placement points to minimize total area.
        """
        if not group:
            return

        # Sort by decreasing area
        sorted_items = sorted(
            group, key=lambda item: self._get_area(item), reverse=True
        )

        placed_items = []
        placement_points = []  # List of (x, y) tuples

        for item in sorted_items:
            if self._is_locked(item):
                continue

            if placement_points:
                # Find best placement point
                best_point = self._find_best_placement_point(
                    item, placed_items, placement_points
                )

                if best_point:
                    self._set_bottom_left(item, best_point[0], best_point[1])
                    # Only remove from placement_points if it was actually in the list
                    if best_point in placement_points:
                        placement_points.remove(best_point)
                else:
                    # No valid placement point found, try to place within board
                    bbox = self._get_combined_bbox(placed_items)
                    spacing = self._get_spacing(item)

                    # Try placing to the right
                    new_x = bbox.max_x + spacing
                    new_y = bbox.min_y
                    self._set_bottom_left(item, new_x, new_y)

                    # Check if within board
                    if hasattr(self, "board_outline") and self.board_outline:
                        item_bbox = self._get_bbox(item)
                        if not self._bbox_within_board(item_bbox):
                            # Try placing below instead
                            new_x = bbox.min_x
                            new_y = bbox.max_y + spacing
                            self._set_bottom_left(item, new_x, new_y)

                            # If still outside, place at board margin
                            item_bbox = self._get_bbox(item)
                            if not self._bbox_within_board(item_bbox):
                                margin = 5.0
                                self._set_bottom_left(item, margin, margin)
            else:
                # First item - place at top-left with margin
                if not placed_items:
                    # Place first item with margin from board edge
                    margin = 10.0  # 10mm margin from board edge

                    # Get board bounds
                    board_min_x = self.board_outline.min_x
                    board_min_y = self.board_outline.min_y

                    # Place item at top-left corner with margin
                    self._set_bottom_left(
                        item, board_min_x + margin, board_min_y + margin
                    )

            # Add new placement points based on the original bbox plus spacing
            # We use the original bbox and add spacing to ensure components don't touch
            if hasattr(item, "_original_bbox_cache") and item._original_bbox_cache:
                orig_bbox = item._original_bbox_cache
            elif hasattr(item, "original_bbox"):
                orig_bbox = item.original_bbox
            else:
                # Fallback: get current bbox and deflate it by spacing to get original
                current_bbox = self._get_bbox(item)
                if isinstance(item, ComponentWrapper):
                    # Deflate to get original size
                    orig_bbox = current_bbox.inflate(-self.component_spacing)
                else:
                    orig_bbox = current_bbox

            # Get the appropriate spacing
            spacing = self._get_spacing(item)

            # Add placement points with spacing
            placement_points.extend(
                [
                    (
                        orig_bbox.min_x - spacing,
                        orig_bbox.min_y,
                    ),  # Left side with spacing
                    (
                        orig_bbox.max_x + spacing,
                        orig_bbox.min_y,
                    ),  # Right side with spacing
                    (
                        orig_bbox.min_x,
                        orig_bbox.min_y - spacing,
                    ),  # Top side with spacing
                    (
                        orig_bbox.min_x,
                        orig_bbox.max_y + spacing,
                    ),  # Bottom side with spacing
                ]
            )

            placed_items.append(item)

    def _find_best_placement_point(
        self, item, placed_items: List, placement_points: List[Tuple[float, float]]
    ) -> Optional[Tuple[float, float]]:
        """
        Find the best placement point that minimizes bounding box expansion.

        Returns None if no valid placement point is found.
        """
        best_point = None
        smallest_size = float("inf")

        # Store original position
        if isinstance(item, ComponentWrapper):
            orig_x = item.footprint.position.x
            orig_y = item.footprint.position.y
        else:
            # It's a ComponentGroup
            orig_bbox = item.bbox

        for point in placement_points:
            # Try placing item at this point
            self._set_bottom_left(item, point[0], point[1])

            # Check if placement is within board boundaries
            if hasattr(self, "board_outline") and self.board_outline:
                item_bbox = self._get_bbox(item)
                if not self._bbox_within_board(item_bbox):
                    continue

            # Check for overlaps
            overlaps = False
            for placed in placed_items:
                if self._touches(item, placed):
                    overlaps = True
                    break

            if not overlaps:
                # Calculate resulting bounding box size
                temp_items = placed_items + [item]
                bbox = self._get_combined_bbox(temp_items)

                # Minimize area + aspect ratio penalty
                width = bbox.width()
                height = bbox.height()
                size = (
                    bbox.area() + abs(width - height) * 0.1
                )  # Prefer square-ish layouts

                if size < smallest_size:
                    smallest_size = size
                    best_point = point

        # Restore original position
        if isinstance(item, ComponentWrapper):
            item.move_to(orig_x, orig_y)
        else:
            # Restore group position
            current_bbox = item.bbox
            dx = orig_bbox.min_x - current_bbox.min_x
            dy = orig_bbox.min_y - current_bbox.min_y
            item.move(dx, dy)

        return best_point

    def _get_bbox(self, item) -> BoundingBox:
        """Get bounding box of an item (component or group)."""
        if isinstance(item, ComponentWrapper):
            return item.bbox
        else:
            # It's a ComponentGroup
            bbox = item.bbox
            # Apply group spacing
            return bbox.inflate(self.group_spacing)

    def _get_area(self, item) -> float:
        """Get area of an item (component or group)."""
        return self._get_bbox(item).area()

    def _is_locked(self, item) -> bool:
        """Check if an item is locked."""
        if isinstance(item, ComponentWrapper):
            return item.is_locked
        else:
            # ComponentGroup
            return item.is_locked

    def _set_bottom_left(self, item, x: float, y: float):
        """Set the bottom-left position of an item."""
        if isinstance(item, ComponentWrapper):
            item.set_bottom_left(x, y)
        else:
            # ComponentGroup
            item.set_bottom_left(x, y)

    def _set_center(self, item, x: float, y: float):
        """Set the center position of an item."""
        bbox = self._get_bbox(item)
        width = bbox.max_x - bbox.min_x
        height = bbox.max_y - bbox.min_y

        # Calculate bottom-left from center
        bl_x = x - width / 2
        bl_y = y - height / 2

        self._set_bottom_left(item, bl_x, bl_y)

    def _touches(self, item1, item2) -> bool:
        """Check if two items touch/overlap."""
        bbox1 = self._get_bbox(item1)
        bbox2 = self._get_bbox(item2)
        # Slightly shrink to avoid false positives
        return bbox1.inflate(-0.01).intersects(bbox2.inflate(-0.01))

    def _get_combined_bbox(self, items: List) -> BoundingBox:
        """Get the combined bounding box of multiple items."""
        if not items:
            return BoundingBox(0, 0, 0, 0)

        bbox = self._get_bbox(items[0])
        for item in items[1:]:
            bbox = bbox.merge(self._get_bbox(item))

        return bbox

    def _get_spacing(self, item) -> float:
        """Get the appropriate spacing for an item."""
        if isinstance(item, ComponentWrapper):
            return self.component_spacing
        else:
            return self.group_spacing

    def _bbox_within_board(self, bbox: BoundingBox) -> bool:
        """Check if a bounding box is within the board outline."""
        if not hasattr(self, "board_outline") or not self.board_outline:
            return True  # No board outline to check against

        # Add a small margin from board edge
        margin = 2.0  # 2mm margin

        return (
            bbox.min_x >= self.board_outline.min_x + margin
            and bbox.max_x <= self.board_outline.max_x - margin
            and bbox.min_y >= self.board_outline.min_y + margin
            and bbox.max_y <= self.board_outline.max_y - margin
        )
