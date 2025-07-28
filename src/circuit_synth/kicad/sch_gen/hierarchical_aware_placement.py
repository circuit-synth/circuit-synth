"""
Hierarchical-aware placement that handles sheet boundaries properly.
"""

import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class HierarchicalPlacementCoordinator:
    """
    Coordinates placement across hierarchical sheets to prevent overlaps.
    """

    def __init__(self):
        self.sheet_boundaries = {}  # sheet_name -> BBox
        self.sheet_margins = 20.0  # mm margin around sheets

    def allocate_sheet_region(
        self,
        sheet_name: str,
        estimated_components: int,
        paper_size: Tuple[float, float],
    ) -> Tuple[float, float, float, float]:
        """
        Allocate a region for a hierarchical sheet.

        Args:
            sheet_name: Name of the sheet
            estimated_components: Estimated number of components
            paper_size: (width, height) of the paper

        Returns:
            (x_min, y_min, x_max, y_max) for the sheet region
        """
        # Estimate required space based on component count
        # Assume average component needs 20x20mm including spacing
        avg_component_area = 400  # mm²
        required_area = estimated_components * avg_component_area * 1.5  # 50% overhead

        # Calculate dimensions maintaining aspect ratio
        aspect_ratio = 1.5  # width/height
        height = (required_area / aspect_ratio) ** 0.5
        width = height * aspect_ratio

        # Find available space
        x, y = self._find_available_space(width, height, paper_size)

        # Store the allocation
        self.sheet_boundaries[sheet_name] = (x, y, x + width, y + height)

        logger.info(
            f"Allocated region for '{sheet_name}': "
            f"({x:.1f}, {y:.1f}) to ({x + width:.1f}, {y + height:.1f})"
        )

        return (x, y, x + width, y + height)

    def _find_available_space(
        self, width: float, height: float, paper_size: Tuple[float, float]
    ) -> Tuple[float, float]:
        """
        Find available space for a new sheet region.

        Returns:
            (x, y) position for the top-left corner
        """
        margin = 20.0  # mm from paper edge

        if not self.sheet_boundaries:
            # First sheet - place at top-left with margin
            return (margin, margin)

        # Try to place to the right of existing sheets
        max_x = max(bounds[2] for bounds in self.sheet_boundaries.values())
        if max_x + self.sheet_margins + width + margin <= paper_size[0]:
            # Fits to the right
            return (max_x + self.sheet_margins, margin)

        # Try to place below existing sheets
        max_y = max(bounds[3] for bounds in self.sheet_boundaries.values())
        if max_y + self.sheet_margins + height + margin <= paper_size[1]:
            # Fits below
            return (margin, max_y + self.sheet_margins)

        # Force placement (may need larger paper)
        logger.warning(f"Sheet may not fit on current paper size {paper_size}")
        return (margin, max_y + self.sheet_margins)

    def get_sheet_offset(self, sheet_name: str) -> Tuple[float, float]:
        """
        Get the offset for components within a sheet.

        Returns:
            (x_offset, y_offset) to add to component positions
        """
        if sheet_name in self.sheet_boundaries:
            x_min, y_min, _, _ = self.sheet_boundaries[sheet_name]
            return (x_min, y_min)
        return (0, 0)

    def get_sheet_bounds(
        self, sheet_name: str
    ) -> Optional[Tuple[float, float, float, float]]:
        """
        Get the bounds for a sheet.

        Returns:
            (x_min, y_min, x_max, y_max) or None if not allocated
        """
        return self.sheet_boundaries.get(sheet_name)
