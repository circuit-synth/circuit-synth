"""
Symbol geometry calculation module.
Provides accurate bounding box calculations based on actual KiCad symbol geometry.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ...kicad.kicad_symbol_parser import parse_kicad_sym_file
from ..core.symbol_cache import get_symbol_cache

logger = logging.getLogger(__name__)


class SymbolGeometry:
    """
    Calculates accurate symbol dimensions from KiCad symbol library files.
    """

    # KiCad font metrics (approximate)
    # Based on KiCad's default font size of 1.27mm (50 mil)
    CHAR_WIDTH_FACTOR = (
        0.8  # Character width is ~80% of font height (increased for better accuracy)
    )
    CHAR_HEIGHT = 1.27  # Default font height in mm

    # Common symbol dimensions in mils (will be converted to mm)
    # Based on KiCad standard library conventions
    DEFAULT_DIMENSIONS = {
        "R": (200, 750),  # Resistor: 200x750 mil (5.08x19.05 mm)
        "C": (200, 750),  # Capacitor: 200x750 mil
        "L": (200, 750),  # Inductor
        "D": (200, 400),  # Diode
        "LED": (200, 400),  # LED
        "Q": (400, 400),  # Transistor
        "U": (600, 400),  # Generic IC
        "Thermistor": (300, 850),  # Thermistor: 300x850 mil (7.62x21.59 mm)
        "P": (400, 600),  # Connector: 400x600 mil (10.16x15.24 mm)
        "J": (400, 600),  # Jack/Connector
        "USB": (400, 600),  # USB Connector
    }

    def __init__(self):
        self._cache = {}
        self._symbol_lib_cache = get_symbol_cache()

    def get_symbol_bounds(self, lib_id: str) -> Tuple[float, float]:
        """
        Get the bounding box dimensions for a symbol.

        Args:
            lib_id: Library ID like "Device:R" or "Device:C"

        Returns:
            (width, height) in mm
        """
        if lib_id in self._cache:
            logger.debug(f"Using cached bounds for {lib_id}: {self._cache[lib_id]}")
            return self._cache[lib_id]

        # Try to parse the actual symbol
        try:
            logger.debug(f"Calculating bounds for {lib_id}")
            bounds = self._calculate_symbol_bounds(lib_id)
            self._cache[lib_id] = bounds
            logger.info(
                f"Calculated bounds for {lib_id}: {bounds[0]:.2f} x {bounds[1]:.2f} mm"
            )
            return bounds
        except Exception as e:
            logger.warning(f"Failed to parse symbol {lib_id}: {e}")
            # Fall back to defaults
            default_bounds = self._get_default_bounds(lib_id)
            logger.info(
                f"Using default bounds for {lib_id}: {default_bounds[0]:.2f} x {default_bounds[1]:.2f} mm"
            )
            return default_bounds

    def _calculate_symbol_bounds(self, lib_id: str) -> Tuple[float, float]:
        """
        Calculate bounds from actual symbol geometry.
        """
        # Parse library and symbol name
        parts = lib_id.split(":")
        if len(parts) != 2:
            raise ValueError(f"Invalid lib_id format: {lib_id}")

        lib_name, symbol_name = parts

        # Get symbol from cache
        try:
            symbol_def = self._symbol_lib_cache.get_symbol(lib_id)
            if not symbol_def:
                raise ValueError(f"Symbol not found: {lib_id}")
        except Exception as e:
            raise ValueError(f"Failed to get symbol: {e}")

        # Calculate bounds from graphics elements
        min_x, min_y = float("inf"), float("inf")
        max_x, max_y = float("-inf"), float("-inf")

        # Process graphics elements from symbol definition
        if symbol_def.graphic_elements:
            for graphic in symbol_def.graphic_elements:
                bounds = self._update_bounds_from_graphic_element(
                    graphic, min_x, min_y, max_x, max_y
                )
                min_x, min_y, max_x, max_y = bounds

        # Process pins
        if symbol_def.pins:
            for pin in symbol_def.pins:
                x = pin.position.x
                y = pin.position.y
                length = pin.length
                orientation = pin.orientation

            # Calculate pin endpoint
            if orientation == 0:  # Right
                end_x = x + length
                end_y = y
            elif orientation == 90:  # Up
                end_x = x
                end_y = y + length
            elif orientation == 180:  # Left
                end_x = x - length
                end_y = y
            else:  # 270 - Down
                end_x = x
                end_y = y - length

            min_x = min(min_x, x, end_x)
            max_x = max(max_x, x, end_x)
            min_y = min(min_y, y, end_y)
            max_y = max(max_y, y, end_y)

        # Calculate dimensions
        if min_x == float("inf"):
            # No graphics found, use defaults
            return self._get_default_bounds(lib_id)

        width = max_x - min_x
        height = max_y - min_y

        # Ensure minimum size
        width = max(width, 2.54)  # At least 100 mil
        height = max(height, 2.54)

        logger.debug(f"Symbol {lib_id} bounds: {width:.2f} x {height:.2f} mm")

        return (width, height)

    def _update_bounds_from_graphic_element(
        self, graphic, min_x: float, min_y: float, max_x: float, max_y: float
    ) -> Tuple[float, float, float, float]:
        """
        Update bounds based on a graphic element from SymbolDefinition.
        """
        shape_type = graphic.get("type", "")

        if shape_type == "rectangle":
            start = graphic.get("start", {"x": 0, "y": 0})
            end = graphic.get("end", {"x": 0, "y": 0})
            min_x = min(min_x, start["x"], end["x"])
            max_x = max(max_x, start["x"], end["x"])
            min_y = min(min_y, start["y"], end["y"])
            max_y = max(max_y, start["y"], end["y"])

        elif shape_type == "circle":
            center = graphic.get("center", {"x": 0, "y": 0})
            radius = graphic.get("radius", 0)
            min_x = min(min_x, center["x"] - radius)
            max_x = max(max_x, center["x"] + radius)
            min_y = min(min_y, center["y"] - radius)
            max_y = max(max_y, center["y"] + radius)

        elif shape_type == "polyline":
            points = graphic.get("points", [])
            for point in points:
                if isinstance(point, dict):
                    px = point.get("x", 0)
                    py = point.get("y", 0)
                else:
                    px, py = point
                min_x = min(min_x, px)
                max_x = max(max_x, px)
                min_y = min(min_y, py)
                max_y = max(max_y, py)

        elif shape_type == "arc":
            # Simplified arc handling - use start/end points
            start = graphic.get("start", {"x": 0, "y": 0})
            end = graphic.get("end", {"x": 0, "y": 0})
            if isinstance(start, dict):
                min_x = min(min_x, start["x"], end["x"])
                max_x = max(max_x, start["x"], end["x"])
                min_y = min(min_y, start["y"], end["y"])
                max_y = max(max_y, start["y"], end["y"])
            else:
                min_x = min(min_x, start[0], end[0])
                max_x = max(max_x, start[0], end[0])
                min_y = min(min_y, start[1], end[1])
                max_y = max(max_y, start[1], end[1])

        return (min_x, min_y, max_x, max_y)

    def _get_default_bounds(self, lib_id: str) -> Tuple[float, float]:
        """
        Get default bounds based on symbol type.
        """
        # Extract symbol base name
        symbol_name = lib_id.split(":")[-1]

        # Check for exact matches first
        if symbol_name in self.DEFAULT_DIMENSIONS:
            width_mil, height_mil = self.DEFAULT_DIMENSIONS[symbol_name]
        else:
            # Check for partial matches
            for key, dims in self.DEFAULT_DIMENSIONS.items():
                if key in symbol_name:
                    width_mil, height_mil = dims
                    break
            else:
                # Default fallback
                width_mil, height_mil = 400, 400

        # Convert mils to mm (1 mil = 0.0254 mm)
        width_mm = width_mil * 0.0254
        height_mm = height_mil * 0.0254

        return (width_mm, height_mm)

    @staticmethod
    def calculate_text_width(text: str, font_size: float = 1.27) -> float:
        """
        Calculate the width of text based on character count and font size.

        Args:
            text: The text string
            font_size: Font height in mm (default 1.27mm)

        Returns:
            Estimated width in mm
        """
        if not text:
            return 0

        # Character width is approximately 60% of font height
        char_width = font_size * SymbolGeometry.CHAR_WIDTH_FACTOR

        # Account for different character widths
        # Narrow characters (i, l, etc.)
        narrow_chars = "iIl1!|"
        narrow_count = sum(1 for c in text if c in narrow_chars)

        # Wide characters (W, M, etc.)
        wide_chars = "WMmw"
        wide_count = sum(1 for c in text if c in wide_chars)

        # Regular characters
        regular_count = len(text) - narrow_count - wide_count

        # Calculate total width with weights
        total_width = (
            narrow_count * char_width * 0.5  # Narrow chars are ~50% width
            + regular_count * char_width
            + wide_count * char_width * 1.3  # Wide chars are ~130% width
        )

        return total_width
