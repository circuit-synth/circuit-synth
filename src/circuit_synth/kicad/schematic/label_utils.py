"""
Utility functions for label and text operations in KiCad schematics.
"""

import logging
from enum import Enum
from typing import Dict, List, Optional, Tuple

from ..core.types import Label, LabelType, Point, SchematicSymbol, Text, Wire

logger = logging.getLogger(__name__)


class LabelPosition(Enum):
    """Label positioning relative to connection point."""

    ABOVE = "above"
    BELOW = "below"
    LEFT = "left"
    RIGHT = "right"
    AUTO = "auto"


def suggest_label_position(
    connection_point: Tuple[float, float],
    connected_wires: List[Wire],
    offset: float = 2.54,
) -> Tuple[Tuple[float, float], int]:
    """
    Suggest optimal position and orientation for a label based on connected wires.

    Args:
        connection_point: Point where label should be placed
        connected_wires: Wires connected at this point
        offset: Distance from connection point

    Returns:
        Tuple of (position, orientation)
    """
    x, y = connection_point

    if not connected_wires:
        # Default: place to the right
        return ((x + offset, y), 0)

    # Analyze wire directions at connection point
    directions = []
    for wire in connected_wires:
        direction = get_wire_direction_at_point(wire, connection_point)
        if direction:
            directions.append(direction)

    # Determine best position based on wire directions
    if not directions:
        return ((x + offset, y), 0)

    # Count directions
    horizontal_count = sum(1 for d in directions if d in ["left", "right"])
    vertical_count = sum(1 for d in directions if d in ["up", "down"])

    if horizontal_count > vertical_count:
        # Wires are mostly horizontal, place label above or below
        if y < 50:  # Near top of schematic
            return ((x, y + offset), 0)
        else:
            return ((x, y - offset), 0)
    else:
        # Wires are mostly vertical, place label left or right
        if x < 50:  # Near left of schematic
            return ((x + offset, y), 0)
        else:
            return ((x - offset, y), 0)


def get_wire_direction_at_point(
    wire: Wire, point: Tuple[float, float]
) -> Optional[str]:
    """
    Get the direction of a wire at a specific point.

    Args:
        wire: Wire to analyze
        point: Point on the wire

    Returns:
        Direction string: 'left', 'right', 'up', 'down', or None
    """
    test_point = Point(*point)

    # Find the point in the wire
    for i, wire_point in enumerate(wire.points):
        if (
            abs(wire_point.x - test_point.x) < 0.1
            and abs(wire_point.y - test_point.y) < 0.1
        ):
            # Found the point, determine direction
            if i > 0:
                # Check previous point
                prev_point = wire.points[i - 1]
                dx = wire_point.x - prev_point.x
                dy = wire_point.y - prev_point.y

                if abs(dx) > abs(dy):
                    return "right" if dx > 0 else "left"
                else:
                    return "down" if dy > 0 else "up"

            if i < len(wire.points) - 1:
                # Check next point
                next_point = wire.points[i + 1]
                dx = next_point.x - wire_point.x
                dy = next_point.y - wire_point.y

                if abs(dx) > abs(dy):
                    return "right" if dx > 0 else "left"
                else:
                    return "down" if dy > 0 else "up"

    return None


def format_net_name(raw_name: str) -> str:
    """
    Format a net name according to KiCad conventions.

    Args:
        raw_name: Raw net name

    Returns:
        Formatted net name
    """
    # Remove invalid characters
    formatted = raw_name.replace(" ", "_")
    formatted = formatted.replace("-", "_")

    # Ensure it starts with a letter or underscore
    if formatted and formatted[0].isdigit():
        formatted = "_" + formatted

    # Convert to uppercase for global labels
    # (This is a convention, not a requirement)

    return formatted


def validate_hierarchical_label_name(name: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a hierarchical label name.

    Args:
        name: Label name to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not name:
        return False, "Label name cannot be empty"

    if len(name) > 50:
        return False, "Label name too long (max 50 characters)"

    # Check for invalid characters
    invalid_chars = ["/", "\\", ":", "*", "?", '"', "<", ">", "|"]
    for char in invalid_chars:
        if char in name:
            return False, f"Invalid character '{char}' in label name"

    return True, None


def group_labels_by_net(labels: List[Label]) -> Dict[str, List[Label]]:
    """
    Group labels by their net name.

    Args:
        labels: List of labels to group

    Returns:
        Dictionary mapping net names to lists of labels
    """
    groups = {}

    for label in labels:
        net_name = label.text
        if net_name not in groups:
            groups[net_name] = []
        groups[net_name].append(label)

    return groups


def find_connected_labels(
    start_label: Label, all_labels: List[Label], wires: List[Wire]
) -> List[Label]:
    """
    Find all labels connected to a starting label through wires.

    Args:
        start_label: Starting label
        all_labels: All labels in schematic
        wires: All wires in schematic

    Returns:
        List of connected labels (including start_label)
    """
    connected = [start_label]
    to_check = [start_label]
    checked = set()

    while to_check:
        current_label = to_check.pop(0)
        if current_label.uuid in checked:
            continue
        checked.add(current_label.uuid)

        # Find wires at this label's position
        label_wires = []
        for wire in wires:
            for point in wire.points:
                if (
                    abs(point.x - current_label.position.x) < 0.1
                    and abs(point.y - current_label.position.y) < 0.1
                ):
                    label_wires.append(wire)
                    break

        # Find other labels on these wires
        for wire in label_wires:
            for label in all_labels:
                if label.uuid == current_label.uuid:
                    continue

                # Check if label is on this wire
                for point in wire.points:
                    if (
                        abs(point.x - label.position.x) < 0.1
                        and abs(point.y - label.position.y) < 0.1
                    ):
                        if label not in connected:
                            connected.append(label)
                            to_check.append(label)
                        break

    return connected


def suggest_label_for_component_pin(
    component: SchematicSymbol,
    pin_number: str,
    label_type: LabelType = LabelType.LOCAL,
    offset: float = 2.54,
) -> Tuple[str, Tuple[float, float], int]:
    """
    Suggest a label for a component pin.

    Args:
        component: Component with the pin
        pin_number: Pin number to label
        label_type: Type of label to create
        offset: Distance from pin

    Returns:
        Tuple of (suggested_text, position, orientation)
    """
    # Find the pin
    pin = None
    for p in component.pins:
        if p.number == pin_number:
            pin = p
            break

    if not pin:
        logger.warning(f"Pin {pin_number} not found on component {component.reference}")
        return ("", (component.position.x, component.position.y), 0)

    # Calculate absolute pin position
    pin_x = component.position.x + pin.position.x
    pin_y = component.position.y + pin.position.y

    # Determine label position based on pin orientation
    # This is simplified - in reality, we'd consider component rotation
    if pin.position.x < 0:  # Pin on left side
        label_x = pin_x - offset
        label_y = pin_y
        orientation = 0
    elif pin.position.x > 0:  # Pin on right side
        label_x = pin_x + offset
        label_y = pin_y
        orientation = 0
    elif pin.position.y < 0:  # Pin on top
        label_x = pin_x
        label_y = pin_y - offset
        orientation = 0
    else:  # Pin on bottom
        label_x = pin_x
        label_y = pin_y + offset
        orientation = 0

    # Suggest text based on pin name
    suggested_text = format_net_name(pin.name) if pin.name else f"NET_{pin_number}"

    return (suggested_text, (label_x, label_y), orientation)


def calculate_text_bounds(
    text: Text, char_width: float = 1.0, char_height: float = 1.27
) -> Tuple[float, float, float, float]:
    """
    Calculate approximate bounding box for text.

    Args:
        text: Text object
        char_width: Approximate character width
        char_height: Approximate character height

    Returns:
        Tuple of (min_x, min_y, max_x, max_y)
    """
    # Count lines and max line length
    lines = text.content.split("\n")
    max_line_length = max(len(line) for line in lines)
    num_lines = len(lines)

    # Calculate dimensions
    width = max_line_length * char_width * text.size
    height = num_lines * char_height * text.size

    # Apply rotation
    if text.orientation in [0, 180]:
        box_width = width
        box_height = height
    else:  # 90 or 270
        box_width = height
        box_height = width

    # Calculate bounds
    if text.orientation == 0:
        min_x = text.position.x
        min_y = text.position.y
    elif text.orientation == 90:
        min_x = text.position.x - box_width
        min_y = text.position.y
    elif text.orientation == 180:
        min_x = text.position.x - box_width
        min_y = text.position.y - box_height
    else:  # 270
        min_x = text.position.x
        min_y = text.position.y - box_height

    max_x = min_x + box_width
    max_y = min_y + box_height

    return (min_x, min_y, max_x, max_y)
