# -*- coding: utf-8 -*-
#
# collision_manager.py
#
# Integration between schematic generation and collision detection
#
# Modified so that we *never* move to a new row or enforce
# a maximum sheet width/height. We just keep placing symbols
# further right indefinitely, as requested.

import logging
from typing import Tuple

from .collision_detection import BBox, CollisionDetector

logger = logging.getLogger(__name__)

# Constants for schematic layout
SHEET_MARGIN = 25.4  # Margin from sheet edge (1 inch)
COMPONENT_SPACING = 5  # Horizontal spacing between components (reduced from 10)
ROW_SPACING = 10.0  # Vertical spacing between rows (reduced from 15)
MIN_COMPONENT_SPACING = 5.08  # Minimum spacing between components (200 mil) - increased for better label clearance
RIGHT_EDGE_MARGIN = 25.4  # Margin from right edge for row wrapping (1 inch)
FAR_RIGHT_MARGIN = 40.0  # Margin for collision handling


class CollisionManager:
    """
    Manages collision detection during schematic generation.
    Provides a more robust approach for placing symbols with proper spacing.
    """

    def __init__(self, sheet_size: Tuple[float, float] = (210.0, 297.0), grid=2.54):
        """
        :param sheet_size: (width_mm, height_mm), e.g. (210, 297) for A4
        :param grid: snap spacing in mm, usually 2.54 (100 mil)
        """
        logger.debug(
            "Initializing CollisionManager with sheet_size=%s, grid=%.2f",
            sheet_size,
            grid,
        )
        self.sheet_size = sheet_size
        self.grid = grid
        self.detector = CollisionDetector(
            min_spacing=MIN_COMPONENT_SPACING,
            sheet_size=sheet_size,
            sheet_margin=SHEET_MARGIN,
        )

        # Start at offset positions (center of first grid cell)
        grid_offset = grid / 2
        self.current_x = SHEET_MARGIN + grid_offset
        self.current_y = SHEET_MARGIN + grid_offset
        self.current_row_height = 0.0

        # Track components in row
        self.components_in_row = 0
        self.first_row = True  # Flag to track if we're in the first row

    def snap_to_grid(self, val: float) -> float:
        """
        Snap a value to the internal grid for cleaner schematic layout.
        Offset by half a grid unit to place components in the center of grid cells.
        Ensures components are never placed directly on grid lines.
        """
        # Offset by half a grid unit (1.27mm for a 2.54mm grid)
        offset = self.grid / 2

        # Calculate the nearest grid line
        grid_val = round(val / self.grid) * self.grid

        # Always add the offset to ensure we're in the center of a grid cell
        snapped = grid_val + offset

        logger.debug(
            "Snapped %.2f -> %.2f on grid=%.2f with offset=%.2f",
            val,
            snapped,
            self.grid,
            offset,
        )
        return snapped

    def place_symbol(
        self, symbol_width: float, symbol_height: float
    ) -> Tuple[float, float]:
        """
        Find a collision-free position for a symbol with improved spacing.
        Return (center_x, center_y) for symbol placement.
        """
        logger.debug(
            "Trying to place symbol with bounding box width=%.2f mm, height=%.2f mm.",
            symbol_width,
            symbol_height,
        )

        # Start with current position
        max_attempts = 100  # Prevent infinite loops
        attempt_count = 0

        while attempt_count < max_attempts:
            attempt_count += 1
            test_x = self.snap_to_grid(self.current_x)
            test_y = self.snap_to_grid(self.current_y)

            # We'll assume the symbol is centered at (test_x, test_y)
            # Use minimal padding since bounding box already includes component geometry
            extra_padding = 0.5  # 0.5mm padding for clean separation
            x_min = test_x - (symbol_width / 2) - extra_padding
            y_min = test_y - (symbol_height / 2) - extra_padding
            x_max = test_x + (symbol_width / 2) + extra_padding
            y_max = test_y + (symbol_height / 2) + extra_padding

            test_bbox = BBox(x_min, y_min, x_max, y_max)

            if self.detector.add_bbox(test_bbox):
                logger.debug(
                    "Placed symbol at (%.2f, %.2f) with BBox=%s",
                    test_x,
                    test_y,
                    test_bbox,
                )

                # Update row height if this symbol is taller
                if symbol_height > self.current_row_height:
                    self.current_row_height = symbol_height

                # Update component tracking
                self.components_in_row += 1

                # Use dynamic spacing based on bounding boxes
                # The bounding box already includes the component size and any labels
                # We just need to add the minimum spacing between components
                spacing = MIN_COMPONENT_SPACING  # 2.54mm gap between components

                # Move next symbol's X position
                # Position is: current center + half width + spacing
                # This avoids double-counting the padding
                self.current_x = test_x + (symbol_width / 2) + spacing

                # Check if the next component would fit before wrapping to next row
                # Consider the full width of the next component plus margins
                next_component_end = self.current_x + symbol_width + extra_padding
                if next_component_end > self.sheet_size[0] - RIGHT_EDGE_MARGIN:
                    grid_offset = self.grid / 2
                    self.current_x = (
                        SHEET_MARGIN + grid_offset
                    )  # Reset to left margin with offset

                    # If this is the first row, set a consistent Y position for the next row
                    # This prevents double-counting of component heights
                    if self.first_row:
                        self.current_y = (
                            SHEET_MARGIN
                            + self.current_row_height
                            + ROW_SPACING
                            + grid_offset
                        )
                        self.first_row = False
                    else:
                        self.current_y += (
                            self.current_row_height + ROW_SPACING
                        )  # Move down by row height plus spacing

                    self.current_row_height = 0.0  # Reset row height for next row
                    self.components_in_row = 0  # Reset component count for next row

                return (test_x, test_y)
            else:
                logger.debug("Collision - shifting symbol to the right by 10mm.")
                self.current_x += 10.0

                # If we've tried to move too far right, move to the next row
                if self.current_x > self.sheet_size[0] - FAR_RIGHT_MARGIN:
                    grid_offset = self.grid / 2
                    self.current_x = SHEET_MARGIN + grid_offset

                    # Use consistent approach for row transitions
                    if self.first_row:
                        self.current_y = (
                            SHEET_MARGIN
                            + self.current_row_height
                            + ROW_SPACING
                            + grid_offset
                        )
                        self.first_row = False
                    else:
                        self.current_y += self.current_row_height + ROW_SPACING

                    self.current_row_height = 0.0
                    self.components_in_row = 0

        # If we've reached max attempts, force placement at current position
        logger.warning(
            f"Reached maximum placement attempts ({max_attempts}). Forcing placement at current position."
        )
        test_x = self.snap_to_grid(self.current_x)
        test_y = self.snap_to_grid(self.current_y)

        # Calculate bounding box for the forced placement
        extra_padding = 0.5  # Consistent minimal padding
        x_min = test_x - (symbol_width / 2) - extra_padding
        y_min = test_y - (symbol_height / 2) - extra_padding
        x_max = test_x + (symbol_width / 2) + extra_padding
        y_max = test_y + (symbol_height / 2) + extra_padding

        # IMPORTANT: Add the bounding box to collision detector even for forced placement
        # This prevents future components from overlapping with this one
        forced_bbox = BBox(x_min, y_min, x_max, y_max)
        self.detector.add_bbox(forced_bbox)
        logger.debug(f"Added forced placement bbox: {forced_bbox}")

        # Update row height if needed
        if symbol_height > self.current_row_height:
            self.current_row_height = symbol_height

        # Move to next position (avoid double spacing)
        self.current_x = test_x + (symbol_width / 2) + MIN_COMPONENT_SPACING

        # If the next component won't fit, move to the next row
        next_component_end = self.current_x + symbol_width + extra_padding
        if next_component_end > self.sheet_size[0] - RIGHT_EDGE_MARGIN:
            grid_offset = self.grid / 2
            self.current_x = SHEET_MARGIN + grid_offset
            self.current_y += self.current_row_height + ROW_SPACING
            self.current_row_height = 0.0
            self.components_in_row = 0

        return (test_x, test_y)

    def register_existing_symbol(
        self,
        center_x: float,
        center_y: float,
        symbol_width: float,
        symbol_height: float,
    ):
        """
        Register an existing symbol's position with the collision detector.
        This is used when preserving positions from an existing schematic.

        Args:
            center_x: X coordinate of symbol center
            center_y: Y coordinate of symbol center
            symbol_width: Width of the symbol
            symbol_height: Height of the symbol
        """
        logger.debug(
            f"Registering existing symbol at ({center_x}, {center_y}) "
            f"with size {symbol_width}x{symbol_height}"
        )

        # Create bounding box for the existing symbol
        extra_padding = 0.5  # Consistent minimal padding
        x_min = center_x - (symbol_width / 2) - extra_padding
        y_min = center_y - (symbol_height / 2) - extra_padding
        x_max = center_x + (symbol_width / 2) + extra_padding
        y_max = center_y + (symbol_height / 2) + extra_padding

        bbox = BBox(x_min, y_min, x_max, y_max)
        self.detector.add_bbox(bbox)

        # Update current position tracking if this symbol is further right
        if center_x + symbol_width / 2 + MIN_COMPONENT_SPACING > self.current_x:
            self.current_x = center_x + symbol_width / 2 + MIN_COMPONENT_SPACING

        # Update row height if this symbol is taller
        if symbol_height > self.current_row_height:
            self.current_row_height = symbol_height

    def clear(self):
        """Clear all placed bounding boxes and reset placement counters."""
        logger.debug("Clearing collision manager state.")
        self.detector.clear()
        grid_offset = self.grid / 2
        self.current_x = SHEET_MARGIN + grid_offset
        self.current_y = SHEET_MARGIN + grid_offset
        self.current_row_height = 0.0
        self.components_in_row = 0
        self.first_row = True
