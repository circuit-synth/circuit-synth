# -*- coding: utf-8 -*-
#
# The MIT License (MIT)
#
# collision_detection.py
#
# Collision detection for schematic symbols and labels

import logging
from typing import List

logger = logging.getLogger(__name__)


class BBox:
    """Simple bounding box class with min/max points (in mm)."""

    def __init__(self, x_min: float, y_min: float, x_max: float, y_max: float):
        self.x_min = x_min
        self.y_min = y_min
        self.x_max = x_max
        self.y_max = y_max

    def intersects(self, other: "BBox") -> bool:
        """
        Check if this bounding box intersects another, returning True if so.
        We account for edges overlapping as intersection as well.
        """
        overlap = not (
            self.x_max < other.x_min
            or other.x_max < self.x_min
            or self.y_max < other.y_min
            or other.y_max < self.y_min
        )
        logger.debug(
            "Checking intersection:\n"
            "  This BBox=(%.2f, %.2f, %.2f, %.2f)\n"
            "  Other BBox=(%.2f, %.2f, %.2f, %.2f)\n"
            "  Overlap=%s",
            self.x_min,
            self.y_min,
            self.x_max,
            self.y_max,
            other.x_min,
            other.y_min,
            other.x_max,
            other.y_max,
            overlap,
        )
        return overlap

    def __repr__(self):
        return (
            f"BBox(x_min={self.x_min}, y_min={self.y_min}, "
            f"x_max={self.x_max}, y_max={self.y_max})"
        )


class CollisionDetector:
    """
    Simple collision detection manager that tracks placed bounding boxes
    and attempts to find a new location that doesn't overlap with existing boxes.
    Also ensures components stay within sheet boundaries.
    """

    def __init__(
        self,
        min_spacing: float = 2.54,
        sheet_size: tuple = (210.0, 297.0),
        sheet_margin: float = 25.4,
    ):
        """
        :param min_spacing: minimal spacing (in mm) between bounding boxes
        :param sheet_size: (width, height) of the sheet in mm
        :param sheet_margin: margin from sheet edge in mm
        """
        logger.debug(
            "Initializing CollisionDetector with min_spacing=%.2f, sheet_margin=%.2f",
            min_spacing,
            sheet_margin,
        )
        self.min_spacing = min_spacing
        self.sheet_size = sheet_size
        self.sheet_margin = sheet_margin
        self.placed_bboxes: List[BBox] = []

        # Add virtual bounding boxes for sheet boundaries
        self._add_sheet_boundaries()

    def add_bbox(self, bbox: BBox) -> bool:
        """
        Check if `bbox` collides with existing bounding boxes (with a margin).
        If no collision, add it. Return True if successfully added, otherwise False.
        """
        logger.debug("Attempting to add BBox: %s", bbox)
        for existing in self.placed_bboxes:
            # Expand existing bounding box by min_spacing in each direction
            expanded = BBox(
                existing.x_min - self.min_spacing,
                existing.y_min - self.min_spacing,
                existing.x_max + self.min_spacing,
                existing.y_max + self.min_spacing,
            )
            if expanded.intersects(bbox):
                logger.debug("Collision detected with existing BBox: %s", existing)
                return False
        self.placed_bboxes.append(bbox)
        logger.debug("BBox added successfully.")
        return True

    def _add_sheet_boundaries(self):
        """
        Add virtual bounding boxes around the sheet edges to prevent components
        from being placed too close to the edges.
        """
        sheet_width, sheet_height = self.sheet_size
        margin = self.sheet_margin

        # Left boundary
        self.placed_bboxes.append(
            BBox(
                x_min=-1000.0,  # Far left
                y_min=-1000.0,  # Far top
                x_max=margin,  # Up to margin
                y_max=sheet_height + 1000.0,  # Far bottom
            )
        )

        # Top boundary
        self.placed_bboxes.append(
            BBox(
                x_min=-1000.0,  # Far left
                y_min=-1000.0,  # Far top
                x_max=sheet_width + 1000.0,  # Far right
                y_max=margin,  # Full margin from top
            )
        )

        # Right boundary
        self.placed_bboxes.append(
            BBox(
                x_min=sheet_width - margin,  # From margin
                y_min=-1000.0,  # Far top
                x_max=sheet_width + 1000.0,  # Far right
                y_max=sheet_height + 1000.0,  # Far bottom
            )
        )

        # Bottom boundary
        self.placed_bboxes.append(
            BBox(
                x_min=-1000.0,  # Far left
                y_min=sheet_height - margin,  # From margin
                x_max=sheet_width + 1000.0,  # Far right
                y_max=sheet_height + 1000.0,  # Far bottom
            )
        )

        logger.debug(
            "Added virtual bounding boxes for sheet boundaries with margin=%.2f", margin
        )

    def clear(self):
        """
        Clear all placed bounding boxes (e.g. if you regenerate or place in a new row).
        """
        logger.debug("Clearing all placed bounding boxes.")
        self.placed_bboxes.clear()
        # Re-add sheet boundaries
        self._add_sheet_boundaries()
