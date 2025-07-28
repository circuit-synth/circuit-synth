"""
Sheet symbol placement and sizing utilities.

This module provides functionality for calculating sheet symbol sizes
and placing them properly in hierarchical schematics.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Constants for sheet symbol sizing
MIN_SHEET_WIDTH = 25.4  # 1 inch minimum width
MIN_SHEET_HEIGHT = 20.32  # 0.8 inch minimum height
PIN_SPACING = 2.54  # 100 mil between pins
SHEET_PADDING = 5.08  # 200 mil padding top/bottom
SHEET_MARGIN = 2.54  # 100 mil margin for text
TEXT_HEIGHT = 1.27  # 50 mil text height
SHEET_SPACING = 12.7  # 500 mil between sheet symbols


@dataclass
class SheetDimensions:
    """Calculated dimensions for a sheet symbol."""

    width: float
    height: float
    position: Tuple[float, float]


class SheetPlacement:
    """Handles sheet symbol sizing and placement."""

    def __init__(self, start_position: Tuple[float, float] = (50.8, 50.8)):
        """
        Initialize sheet placement manager.

        Args:
            start_position: Starting position for first sheet (x, y) in mm
        """
        self.start_x, self.start_y = start_position
        self.current_x = self.start_x
        self.placed_sheets: List[SheetDimensions] = []

    def calculate_sheet_size(
        self, pin_count: int, sheet_name: str
    ) -> Tuple[float, float]:
        """
        Calculate appropriate sheet symbol size based on pin count.

        Args:
            pin_count: Number of hierarchical pins
            sheet_name: Name of the sheet (affects width)

        Returns:
            Tuple of (width, height) in mm
        """
        # Calculate height based on pin count
        # Need space for pins plus padding
        pin_area_height = pin_count * PIN_SPACING
        height = max(MIN_SHEET_HEIGHT, pin_area_height + (2 * SHEET_PADDING))

        # Calculate width based on sheet name length
        # Approximate character width as 1.5mm per character
        char_width = 1.5
        name_width = len(sheet_name) * char_width + (2 * SHEET_MARGIN)
        width = max(MIN_SHEET_WIDTH, name_width)

        # Round to grid
        grid = 1.27  # 50 mil grid
        width = round(width / grid) * grid
        height = round(height / grid) * grid

        logger.debug(f"Sheet '{sheet_name}' with {pin_count} pins: {width}x{height}mm")

        return width, height

    def get_next_position(self, width: float, height: float) -> Tuple[float, float]:
        """
        Get the next available position for a sheet symbol.

        Args:
            width: Sheet width in mm
            height: Sheet height in mm

        Returns:
            Tuple of (x, y) position for top-left corner
        """
        # Simple horizontal placement for now
        position = (self.current_x, self.start_y)

        # Update current position for next sheet
        self.current_x += width + SHEET_SPACING

        # Track placed sheet
        self.placed_sheets.append(SheetDimensions(width, height, position))

        return position

    def place_sheet(self, pin_count: int, sheet_name: str) -> SheetDimensions:
        """
        Calculate size and position for a sheet symbol.

        Args:
            pin_count: Number of hierarchical pins
            sheet_name: Name of the sheet

        Returns:
            SheetDimensions with calculated values
        """
        width, height = self.calculate_sheet_size(pin_count, sheet_name)
        x, y = self.get_next_position(width, height)

        return SheetDimensions(width, height, (x, y))

    def calculate_pin_positions(
        self, sheet_dims: SheetDimensions, pin_names: List[str]
    ) -> List[Tuple[str, float, float]]:
        """
        Calculate positions for sheet pins.

        Args:
            sheet_dims: Sheet dimensions and position
            pin_names: List of pin names

        Returns:
            List of (name, x, y) tuples for pin positions
        """
        x, y = sheet_dims.position
        sheet_right = x + sheet_dims.width

        # Start pins below the sheet name
        start_y = y + SHEET_PADDING

        positions = []
        for i, name in enumerate(pin_names):
            pin_y = start_y + (i * PIN_SPACING)
            # Pins are placed on the right edge
            positions.append((name, sheet_right, pin_y))

        return positions


def create_sheet_symbols(
    circuits: Dict[str, any], start_position: Tuple[float, float] = (50.8, 50.8)
) -> Dict[str, SheetDimensions]:
    """
    Create sheet symbols for multiple subcircuits.

    Args:
        circuits: Dictionary of circuit name to circuit object
        start_position: Starting position for placement

    Returns:
        Dictionary mapping circuit name to SheetDimensions
    """
    placement = SheetPlacement(start_position)
    sheet_info = {}

    for name, circuit in circuits.items():
        # Count the number of nets (which become hierarchical pins)
        pin_count = len(circuit._nets) if hasattr(circuit, "_nets") else 10

        # Calculate and place sheet
        dims = placement.place_sheet(pin_count, name)
        sheet_info[name] = dims

        logger.info(
            f"Placed sheet '{name}' at {dims.position} with size {dims.width}x{dims.height}"
        )

    return sheet_info
