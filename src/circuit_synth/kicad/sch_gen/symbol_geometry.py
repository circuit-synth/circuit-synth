"""
symbol_geometry.py

Calculate accurate bounding boxes for KiCad symbols based on their graphical elements.
This ensures proper spacing and collision detection in schematic layouts.
"""

import logging
import math
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class SymbolBoundingBoxCalculator:
    """Calculate the actual bounding box of a symbol from its graphical elements."""

    # KiCad default text size in mm
    # Increased to better match actual KiCad rendering
    DEFAULT_TEXT_HEIGHT = 2.54  # 100 mils (doubled from 50 mils)
    DEFAULT_PIN_LENGTH = 2.54  # 100 mils
    DEFAULT_PIN_NAME_OFFSET = 0.508  # 20 mils
    DEFAULT_PIN_NUMBER_SIZE = 1.27  # 50 mils
    # Increased text width ratio to better match KiCad's actual rendering
    # KiCad uses proportional fonts where character width varies, but for
    # conservative bounding box calculation, we use a larger ratio
    DEFAULT_PIN_TEXT_WIDTH_RATIO = (
        2.0  # Width to height ratio for pin text (increased from 1.5)
    )

    @classmethod
    def calculate_bounding_box(
        cls,
        symbol_data: Dict[str, Any],
        include_properties: bool = True,
        hierarchical_labels: Optional[List[Dict[str, Any]]] = None,
    ) -> Tuple[float, float, float, float]:
        """
        Calculate the actual bounding box of a symbol from its graphical elements.

        Args:
            symbol_data: Dictionary containing symbol definition from KiCad library
            include_properties: Whether to include space for Reference/Value labels
            hierarchical_labels: List of hierarchical labels attached to this symbol

        Returns:
            Tuple of (min_x, min_y, max_x, max_y) in mm

        Raises:
            ValueError: If symbol data is invalid or bounding box cannot be calculated
        """
        if not symbol_data:
            raise ValueError("Symbol data is None or empty")

        min_x = float("inf")
        min_y = float("inf")
        max_x = float("-inf")
        max_y = float("-inf")

        # Process main symbol shapes (handle both 'shapes' and 'graphics' keys)
        shapes = symbol_data.get("shapes", []) or symbol_data.get("graphics", [])
        for shape in shapes:
            shape_bounds = cls._get_shape_bounds(shape)
            if shape_bounds:
                s_min_x, s_min_y, s_max_x, s_max_y = shape_bounds
                min_x = min(min_x, s_min_x)
                min_y = min(min_y, s_min_y)
                max_x = max(max_x, s_max_x)
                max_y = max(max_y, s_max_y)

        # Process pins (including their labels)
        pins = symbol_data.get("pins", [])
        for pin in pins:
            pin_bounds = cls._get_pin_bounds(pin)
            if pin_bounds:
                p_min_x, p_min_y, p_max_x, p_max_y = pin_bounds
                min_x = min(min_x, p_min_x)
                min_y = min(min_y, p_min_y)
                max_x = max(max_x, p_max_x)
                max_y = max(max_y, p_max_y)

        # Process sub-symbols
        sub_symbols = symbol_data.get("sub_symbols", [])
        for sub in sub_symbols:
            # Sub-symbols can have their own shapes and pins (handle both 'shapes' and 'graphics' keys)
            sub_shapes = sub.get("shapes", []) or sub.get("graphics", [])
            for shape in sub_shapes:
                shape_bounds = cls._get_shape_bounds(shape)
                if shape_bounds:
                    s_min_x, s_min_y, s_max_x, s_max_y = shape_bounds
                    min_x = min(min_x, s_min_x)
                    min_y = min(min_y, s_min_y)
                    max_x = max(max_x, s_max_x)
                    max_y = max(max_y, s_max_y)

            sub_pins = sub.get("pins", [])
            for pin in sub_pins:
                pin_bounds = cls._get_pin_bounds(pin)
                if pin_bounds:
                    p_min_x, p_min_y, p_max_x, p_max_y = pin_bounds
                    min_x = min(min_x, p_min_x)
                    min_y = min(min_y, p_min_y)
                    max_x = max(max_x, p_max_x)
                    max_y = max(max_y, p_max_y)

        # Check if we found any geometry
        if min_x == float("inf") or max_x == float("-inf"):
            raise ValueError(f"No valid geometry found in symbol data")

        # Add small margin for text that might extend beyond shapes
        margin = 0.254  # 10 mils
        min_x -= margin
        min_y -= margin
        max_x += margin
        max_y += margin

        # Include space for component properties (Reference, Value, Footprint)
        if include_properties:
            # Reference is placed 5mm above center
            # Value is placed 5mm below center
            # Footprint is placed 10mm below center
            # Assume average text width of 10mm for properties
            property_width = 10.0  # Conservative estimate
            property_height = cls.DEFAULT_TEXT_HEIGHT

            # Reference label above
            min_y -= 5.0 + property_height

            # Value and Footprint labels below
            max_y += 10.0 + property_height

            # Extend horizontally for property text
            center_x = (min_x + max_x) / 2
            min_x = min(min_x, center_x - property_width / 2)
            max_x = max(max_x, center_x + property_width / 2)

        logger.debug(
            f"Calculated bounding box: ({min_x:.2f}, {min_y:.2f}) to ({max_x:.2f}, {max_y:.2f})"
        )

        return (min_x, min_y, max_x, max_y)

    @classmethod
    def get_symbol_dimensions(
        cls, symbol_data: Dict[str, Any], include_properties: bool = True
    ) -> Tuple[float, float]:
        """
        Get the width and height of a symbol.

        Args:
            symbol_data: Dictionary containing symbol definition
            include_properties: Whether to include space for Reference/Value labels

        Returns:
            Tuple of (width, height) in mm
        """
        min_x, min_y, max_x, max_y = cls.calculate_bounding_box(
            symbol_data, include_properties
        )
        width = max_x - min_x
        height = max_y - min_y
        return (width, height)

    @classmethod
    def _get_shape_bounds(
        cls, shape: Dict[str, Any]
    ) -> Optional[Tuple[float, float, float, float]]:
        """Get bounding box for a graphical shape."""
        shape_type = shape.get("shape_type", "")

        if shape_type == "rectangle":
            start = shape.get("start", [0, 0])
            end = shape.get("end", [0, 0])
            return (
                min(start[0], end[0]),
                min(start[1], end[1]),
                max(start[0], end[0]),
                max(start[1], end[1]),
            )

        elif shape_type == "circle":
            center = shape.get("center", [0, 0])
            radius = shape.get("radius", 0)
            return (
                center[0] - radius,
                center[1] - radius,
                center[0] + radius,
                center[1] + radius,
            )

        elif shape_type == "arc":
            # For arcs, we need to consider start, mid, and end points
            start = shape.get("start", [0, 0])
            mid = shape.get("mid", [0, 0])
            end = shape.get("end", [0, 0])

            # Simple approach: use bounding box of all three points
            # More accurate would be to calculate the actual arc bounds
            min_x = min(start[0], mid[0], end[0])
            min_y = min(start[1], mid[1], end[1])
            max_x = max(start[0], mid[0], end[0])
            max_y = max(start[1], mid[1], end[1])

            return (min_x, min_y, max_x, max_y)

        elif shape_type == "polyline":
            points = shape.get("points", [])
            if not points:
                return None

            min_x = min(p[0] for p in points)
            min_y = min(p[1] for p in points)
            max_x = max(p[0] for p in points)
            max_y = max(p[1] for p in points)

            return (min_x, min_y, max_x, max_y)

        elif shape_type == "text":
            # Text bounding box estimation
            at = shape.get("at", [0, 0])
            text = shape.get("text", "")
            # Rough estimation: each character is about 1.27mm wide
            text_width = len(text) * cls.DEFAULT_TEXT_HEIGHT * 0.6
            text_height = cls.DEFAULT_TEXT_HEIGHT

            return (
                at[0] - text_width / 2,
                at[1] - text_height / 2,
                at[0] + text_width / 2,
                at[1] + text_height / 2,
            )

        return None

    @classmethod
    def _get_pin_bounds(
        cls, pin: Dict[str, Any]
    ) -> Optional[Tuple[float, float, float, float]]:
        """Get bounding box for a pin including its labels."""
        # Handle both formats: 'at' array or separate x/y/orientation
        if "at" in pin:
            at = pin.get("at", [0, 0])
            x, y = at[0], at[1]
            angle = at[2] if len(at) > 2 else 0
        else:
            # Handle the format from symbol cache
            x = pin.get("x", 0)
            y = pin.get("y", 0)
            angle = pin.get("orientation", 0)

        length = pin.get("length", cls.DEFAULT_PIN_LENGTH)

        # Calculate pin endpoint based on angle
        angle_rad = math.radians(angle)
        end_x = x + length * math.cos(angle_rad)
        end_y = y + length * math.sin(angle_rad)

        # Start with pin line bounds
        min_x = min(x, end_x)
        min_y = min(y, end_y)
        max_x = max(x, end_x)
        max_y = max(y, end_y)

        # Add space for pin name and number
        pin_name = pin.get("name", "")
        pin_number = pin.get("number", "")

        if pin_name and pin_name != "~":  # ~ means no name
            # Pin labels are placed directly on the pin and extend outward
            # The text extends based on its length and height
            name_width = (
                len(pin_name)
                * cls.DEFAULT_TEXT_HEIGHT
                * cls.DEFAULT_PIN_TEXT_WIDTH_RATIO
            )

            # Adjust bounds based on pin orientation
            # The label starts at the pin end and extends outward
            if angle == 0:  # Right - label extends to the right
                max_x = end_x + name_width
            elif angle == 180:  # Left - label extends to the left
                min_x = end_x - name_width
            elif angle == 90:  # Up - label extends upward
                max_y = end_y + name_width  # Use name_width for vertical text too
            elif angle == 270:  # Down - label extends downward
                min_y = end_y - name_width  # Use name_width for vertical text too

        # Pin numbers are typically placed near the component body
        if pin_number:
            num_width = (
                len(pin_number)
                * cls.DEFAULT_PIN_NUMBER_SIZE
                * cls.DEFAULT_PIN_TEXT_WIDTH_RATIO
            )
            # Add some space for the pin number
            margin = (
                cls.DEFAULT_PIN_NUMBER_SIZE * 1.5
            )  # Increase margin for better spacing
            min_x -= margin
            min_y -= margin
            max_x += margin
            max_y += margin

        return (min_x, min_y, max_x, max_y)
