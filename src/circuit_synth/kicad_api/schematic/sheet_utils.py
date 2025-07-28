"""
Utility functions for sheet management in KiCad schematics.

This module provides helper functions for working with hierarchical sheets,
including size calculations, pin placement, and validation.
"""

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..core.types import BoundingBox, Point, SchematicSymbol, Sheet, SheetPin

logger = logging.getLogger(__name__)


class PinSide:
    """Constants for sheet pin sides."""

    LEFT = "left"
    RIGHT = "right"
    TOP = "top"
    BOTTOM = "bottom"

    @classmethod
    def all_sides(cls) -> List[str]:
        """Get all valid sides."""
        return [cls.LEFT, cls.RIGHT, cls.TOP, cls.BOTTOM]


def calculate_sheet_size_from_content(
    components: List[SchematicSymbol], margin: float = 25.4
) -> Tuple[float, float]:
    """
    Calculate appropriate sheet size based on component layout.

    Args:
        components: List of components to fit in the sheet
        margin: Margin around components in mm (default 1 inch)

    Returns:
        Tuple of (width, height) in mm
    """
    if not components:
        # Default minimum size
        return (127.0, 101.6)  # 5" x 4"

    # Find bounding box of all components
    min_x = float("inf")
    max_x = float("-inf")
    min_y = float("inf")
    max_y = float("-inf")

    for component in components:
        bbox = component.get_bounding_box()
        min_x = min(min_x, bbox.x1)
        max_x = max(max_x, bbox.x2)
        min_y = min(min_y, bbox.y1)
        max_y = max(max_y, bbox.y2)

    # Calculate size with margin
    width = max_x - min_x + 2 * margin
    height = max_y - min_y + 2 * margin

    # Round to standard grid (1 inch = 25.4mm)
    grid = 25.4
    width = round(width / grid) * grid
    height = round(height / grid) * grid

    # Enforce minimum size
    min_width = 127.0  # 5 inches
    min_height = 101.6  # 4 inches
    width = max(width, min_width)
    height = max(height, min_height)

    # Enforce maximum size
    max_width = 431.8  # 17 inches (A3 landscape)
    max_height = 279.4  # 11 inches (A3 portrait)
    width = min(width, max_width)
    height = min(height, max_height)

    return (width, height)


def suggest_pin_side(
    net_direction: str, existing_pins: Optional[List[SheetPin]] = None
) -> str:
    """
    Suggest which side of a sheet a pin should be placed on.

    Args:
        net_direction: Direction of the net ("input", "output", "bidirectional")
        existing_pins: List of existing pins to avoid crowding

    Returns:
        Suggested side (left, right, top, bottom)
    """
    # Default suggestions based on direction
    if net_direction == "input":
        preferred_side = PinSide.LEFT
        alternate_side = PinSide.TOP
    elif net_direction == "output":
        preferred_side = PinSide.RIGHT
        alternate_side = PinSide.BOTTOM
    elif net_direction == "bidirectional":
        preferred_side = PinSide.TOP
        alternate_side = PinSide.BOTTOM
    else:  # passive, tri_state, etc.
        preferred_side = PinSide.LEFT
        alternate_side = PinSide.RIGHT

    # If no existing pins, use preferred side
    if not existing_pins:
        return preferred_side

    # Count pins on each side
    side_counts = {side: 0 for side in PinSide.all_sides()}
    for pin in existing_pins:
        side = _get_pin_side(pin)
        if side:
            side_counts[side] += 1

    # Use preferred side if it has fewer pins
    if side_counts[preferred_side] <= side_counts[alternate_side]:
        return preferred_side
    else:
        return alternate_side


def match_hierarchical_labels_to_pins(
    sheet: Sheet, labels: List[Dict[str, str]]
) -> Dict[str, str]:
    """
    Match hierarchical labels to sheet pins.

    Args:
        sheet: The sheet to match pins for
        labels: List of hierarchical labels with 'name' and 'direction'

    Returns:
        Dictionary mapping label names to pin names
    """
    matches = {}

    # Create lookup for sheet pins
    pin_lookup = {pin.name: pin for pin in sheet.pins}

    for label in labels:
        label_name = label.get("name", "")

        # Direct match
        if label_name in pin_lookup:
            matches[label_name] = label_name
            continue

        # Try case-insensitive match
        for pin_name, pin in pin_lookup.items():
            if label_name.lower() == pin_name.lower():
                matches[label_name] = pin_name
                break
        else:
            # Try partial match
            for pin_name, pin in pin_lookup.items():
                if label_name in pin_name or pin_name in label_name:
                    matches[label_name] = pin_name
                    break

    return matches


def validate_sheet_filename(filename: str) -> bool:
    """
    Validate a sheet filename.

    Args:
        filename: Filename to validate

    Returns:
        True if valid, False otherwise
    """
    # Must have .kicad_sch extension
    if not filename.endswith(".kicad_sch"):
        return False

    # No path separators
    if "/" in filename or "\\" in filename:
        return False

    # Valid characters only
    if not re.match(r"^[a-zA-Z0-9_\-]+\.kicad_sch$", filename):
        return False

    # Reasonable length
    if len(filename) > 255:
        return False

    return True


def resolve_sheet_filepath(base_path: Path, sheet_filename: str) -> Path:
    """
    Resolve a sheet filename to its full path.

    Args:
        base_path: Base directory (usually project directory)
        sheet_filename: Sheet filename

    Returns:
        Full path to sheet file
    """
    # Sheets are always in the same directory as the parent
    return base_path / sheet_filename


def calculate_pin_spacing(
    num_pins: int, sheet_height: float, margin: float = 10.0
) -> float:
    """
    Calculate optimal spacing between pins.

    Args:
        num_pins: Number of pins to place
        sheet_height: Height of the sheet in mm
        margin: Margin from top/bottom in mm

    Returns:
        Spacing between pins in mm
    """
    if num_pins <= 1:
        return 0.0

    available_height = sheet_height - 2 * margin

    # Calculate spacing
    spacing = available_height / (num_pins - 1)

    # Snap to grid (2.54mm standard)
    grid = 2.54
    spacing = round(spacing / grid) * grid

    # Minimum spacing
    min_spacing = 5.08  # 2 grid units
    spacing = max(spacing, min_spacing)

    return spacing


def group_pins_by_function(pins: List[SheetPin]) -> Dict[str, List[SheetPin]]:
    """
    Group sheet pins by their function/type.

    Args:
        pins: List of sheet pins

    Returns:
        Dictionary mapping function to list of pins
    """
    groups = {
        "power": [],
        "ground": [],
        "clock": [],
        "reset": [],
        "data": [],
        "address": [],
        "control": [],
        "other": [],
    }

    for pin in pins:
        pin_name_upper = pin.name.upper()

        # Categorize by name patterns
        if any(pwr in pin_name_upper for pwr in ["VCC", "VDD", "V+", "+V", "PWR"]):
            groups["power"].append(pin)
        elif any(gnd in pin_name_upper for gnd in ["GND", "VSS", "V-", "-V", "0V"]):
            groups["ground"].append(pin)
        elif any(clk in pin_name_upper for clk in ["CLK", "CLOCK", "SCK", "SCLK"]):
            groups["clock"].append(pin)
        elif any(rst in pin_name_upper for rst in ["RST", "RESET", "NRST", "RES"]):
            groups["reset"].append(pin)
        elif any(addr in pin_name_upper for addr in ["A0", "A1", "ADDR", "ADDRESS"]):
            groups["address"].append(pin)
        elif any(
            ctrl in pin_name_upper for ctrl in ["CS", "CE", "EN", "WR", "RD", "OE"]
        ):
            groups["control"].append(pin)
        elif any(data in pin_name_upper for data in ["D0", "D1", "DATA", "DQ", "IO"]):
            groups["data"].append(pin)
        else:
            groups["other"].append(pin)

    # Remove empty groups
    return {k: v for k, v in groups.items() if v}


def suggest_sheet_position(
    existing_sheets: List[Sheet],
    new_sheet_size: Tuple[float, float],
    spacing: float = 25.4,
) -> Tuple[float, float]:
    """
    Suggest a position for a new sheet that doesn't overlap existing ones.

    Args:
        existing_sheets: List of existing sheets
        new_sheet_size: Size of the new sheet (width, height)
        spacing: Minimum spacing between sheets in mm

    Returns:
        Suggested position (x, y) in mm
    """
    if not existing_sheets:
        # First sheet - place at origin with margin
        return (50.0, 50.0)

    # Try placing to the right of existing sheets
    max_x = max(sheet.position.x + sheet.size[0] for sheet in existing_sheets)
    suggested_x = max_x + spacing
    suggested_y = existing_sheets[0].position.y  # Align with first sheet

    # Check if this position works
    new_bbox = BoundingBox(
        suggested_x,
        suggested_y,
        suggested_x + new_sheet_size[0],
        suggested_y + new_sheet_size[1],
    )

    # Check for overlaps
    for sheet in existing_sheets:
        sheet_bbox = BoundingBox(
            sheet.position.x,
            sheet.position.y,
            sheet.position.x + sheet.size[0],
            sheet.position.y + sheet.size[1],
        )

        if new_bbox.intersects(sheet_bbox):
            # Try below existing sheets
            max_y = max(sheet.position.y + sheet.size[1] for sheet in existing_sheets)
            suggested_x = existing_sheets[0].position.x
            suggested_y = max_y + spacing
            break

    return (suggested_x, suggested_y)


def create_sheet_instance_name(base_name: str, existing_names: List[str]) -> str:
    """
    Create a unique instance name for a sheet.

    Args:
        base_name: Base name for the sheet
        existing_names: List of existing sheet names

    Returns:
        Unique instance name
    """
    # Clean base name
    clean_name = re.sub(r"[^a-zA-Z0-9_]", "_", base_name)

    # If base name is unique, use it
    if clean_name not in existing_names:
        return clean_name

    # Add numeric suffix
    counter = 1
    while True:
        instance_name = f"{clean_name}_{counter}"
        if instance_name not in existing_names:
            return instance_name
        counter += 1


def _get_pin_side(pin: SheetPin) -> Optional[str]:
    """Get the side of a sheet that a pin is on based on orientation."""
    orientation_to_side = {
        0: PinSide.LEFT,
        90: PinSide.TOP,
        180: PinSide.RIGHT,
        270: PinSide.BOTTOM,
    }
    return orientation_to_side.get(pin.orientation)


def estimate_sheet_complexity(
    sheet: Sheet, schematic_contents: Optional[Dict] = None
) -> str:
    """
    Estimate the complexity of a sheet.

    Args:
        sheet: The sheet to analyze
        schematic_contents: Optional parsed schematic contents

    Returns:
        Complexity level: "simple", "moderate", "complex"
    """
    # Base complexity on pin count
    pin_count = len(sheet.pins)

    if pin_count <= 10:
        base_complexity = "simple"
    elif pin_count <= 25:
        base_complexity = "moderate"
    else:
        base_complexity = "complex"

    # Adjust based on contents if available
    if schematic_contents:
        component_count = len(schematic_contents.get("components", []))

        if component_count > 50:
            return "complex"
        elif component_count > 20 and base_complexity == "simple":
            return "moderate"

    return base_complexity


def generate_sheet_documentation(sheet: Sheet) -> str:
    """
    Generate documentation string for a sheet.

    Args:
        sheet: The sheet to document

    Returns:
        Documentation string
    """
    doc_lines = [
        f"Sheet: {sheet.name}",
        f"File: {sheet.filename}",
        f"Size: {sheet.size[0]:.1f} x {sheet.size[1]:.1f} mm",
        f"Position: ({sheet.position.x:.1f}, {sheet.position.y:.1f})",
        f"Pins: {len(sheet.pins)}",
        "",
    ]

    if sheet.pins:
        # Group pins by side
        pins_by_side = {}
        for pin in sheet.pins:
            side = _get_pin_side(pin)
            if side not in pins_by_side:
                pins_by_side[side] = []
            pins_by_side[side].append(pin)

        # Document pins by side
        for side in PinSide.all_sides():
            if side in pins_by_side:
                doc_lines.append(f"{side.capitalize()} pins:")
                for pin in pins_by_side[side]:
                    doc_lines.append(f"  - {pin.name} ({pin.shape})")
                doc_lines.append("")

    return "\n".join(doc_lines)
