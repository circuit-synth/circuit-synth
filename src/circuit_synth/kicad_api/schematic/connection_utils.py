"""
Connection utilities for wire management.
Provides helper functions for pin position resolution, grid snapping, and geometry calculations.
"""

import math
from typing import Any, Dict, List, Optional, Tuple

from ..core.symbol_cache import get_symbol_cache
from ..core.types import Point, SchematicPin, SchematicSymbol


def snap_to_grid(
    position: Tuple[float, float], grid_size: float = 2.54
) -> Tuple[float, float]:
    """
    Snap a position to the nearest grid point.

    Args:
        position: (x, y) coordinate
        grid_size: Grid size in mm (default 2.54mm = 0.1 inch)

    Returns:
        Grid-aligned (x, y) coordinate
    """
    x, y = position
    aligned_x = round(x / grid_size) * grid_size
    aligned_y = round(y / grid_size) * grid_size
    return (aligned_x, aligned_y)


def points_equal(p1: Point, p2: Point, tolerance: float = 0.01) -> bool:
    """
    Check if two points are equal within tolerance.

    Args:
        p1: First point
        p2: Second point
        tolerance: Distance tolerance

    Returns:
        True if points are equal within tolerance
    """
    return abs(p1.x - p2.x) < tolerance and abs(p1.y - p2.y) < tolerance


def distance_between_points(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """
    Calculate distance between two points.

    Args:
        p1: First point (x, y)
        p2: Second point (x, y)

    Returns:
        Distance between points
    """
    return math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)


def apply_transformation(
    point: Tuple[float, float],
    origin: Point,
    rotation: float,
    mirror: Optional[str] = None,
) -> Tuple[float, float]:
    """
    Apply rotation and mirroring transformation to a point.

    Args:
        point: Point to transform (x, y) relative to origin
        origin: Component origin
        rotation: Rotation in degrees (0, 90, 180, 270)
        mirror: Mirror axis ("x" or "y" or None)

    Returns:
        Transformed absolute position (x, y)
    """
    x, y = point

    # Apply mirroring first
    if mirror == "x":
        x = -x
    elif mirror == "y":
        y = -y

    # Apply rotation
    if rotation == 90:
        x, y = -y, x
    elif rotation == 180:
        x, y = -x, -y
    elif rotation == 270:
        x, y = y, -x

    # Translate to absolute position
    return (origin.x + x, origin.y + y)


def get_pin_position(
    component: SchematicSymbol, pin_number: str
) -> Optional[Tuple[float, float]]:
    """
    Get the absolute position of a component pin.

    Args:
        component: Component containing the pin
        pin_number: Pin number to find

    Returns:
        Absolute (x, y) position of the pin, or None if not found
    """
    # First check if pin is already in component data
    for pin in component.pins:
        if pin.number == pin_number:
            return apply_transformation(
                (pin.position.x, pin.position.y),
                component.position,
                component.rotation,
                component.mirror,
            )

    # If not, try to get from symbol library
    symbol_cache = get_symbol_cache()
    symbol_def = symbol_cache.get_symbol(component.lib_id)

    if not symbol_def:
        return None

    # Look for pin in symbol definition
    for pin_def in symbol_def.get("pins", []):
        if pin_def.get("number") == pin_number:
            # Get pin position from definition
            pin_x = pin_def.get("x", 0)
            pin_y = pin_def.get("y", 0)

            return apply_transformation(
                (pin_x, pin_y), component.position, component.rotation, component.mirror
            )

    return None


def find_pin_by_name(component: SchematicSymbol, pin_name: str) -> Optional[str]:
    """
    Find pin number by pin name.

    Args:
        component: Component to search
        pin_name: Pin name to find

    Returns:
        Pin number if found, None otherwise
    """
    # Check component pins
    for pin in component.pins:
        if pin.name == pin_name:
            return pin.number

    # Check symbol library
    symbol_cache = get_symbol_cache()
    symbol_def = symbol_cache.get_symbol(component.lib_id)

    if symbol_def:
        for pin_def in symbol_def.get("pins", []):
            if pin_def.get("name") == pin_name:
                return pin_def.get("number")

    return None


def segment_intersection(
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    p3: Tuple[float, float],
    p4: Tuple[float, float],
) -> Optional[Tuple[float, float]]:
    """
    Find intersection point of two line segments.

    Args:
        p1, p2: First line segment endpoints
        p3, p4: Second line segment endpoints

    Returns:
        Intersection point (x, y) if segments intersect, None otherwise
    """
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4

    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)

    if abs(denom) < 1e-10:
        # Lines are parallel
        return None

    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
    u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom

    if 0 <= t <= 1 and 0 <= u <= 1:
        # Segments intersect
        x = x1 + t * (x2 - x1)
        y = y1 + t * (y2 - y1)
        return (x, y)

    return None


def point_on_segment(
    point: Tuple[float, float],
    seg_start: Tuple[float, float],
    seg_end: Tuple[float, float],
    tolerance: float = 0.01,
) -> bool:
    """
    Check if a point lies on a line segment.

    Args:
        point: Point to check
        seg_start: Segment start point
        seg_end: Segment end point
        tolerance: Distance tolerance

    Returns:
        True if point is on segment
    """
    px, py = point
    x1, y1 = seg_start
    x2, y2 = seg_end

    # Check if point is on the line
    cross = (py - y1) * (x2 - x1) - (px - x1) * (y2 - y1)
    if abs(cross) > tolerance:
        return False

    # Check if point is within segment bounds
    dot = (px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)
    squared_length = (x2 - x1) ** 2 + (y2 - y1) ** 2

    if squared_length == 0:
        return distance_between_points(point, seg_start) <= tolerance

    param = dot / squared_length
    return 0 <= param <= 1


def get_wire_segments(
    points: List[Point],
) -> List[Tuple[Tuple[float, float], Tuple[float, float]]]:
    """
    Convert a list of points to line segments.

    Args:
        points: List of points defining a wire

    Returns:
        List of ((x1, y1), (x2, y2)) segments
    """
    segments = []
    for i in range(len(points) - 1):
        p1 = points[i]
        p2 = points[i + 1]
        segments.append(((p1.x, p1.y), (p2.x, p2.y)))
    return segments


def simplify_points(points: List[Point], tolerance: float = 0.01) -> List[Point]:
    """
    Remove unnecessary collinear points from a path.

    Args:
        points: List of points
        tolerance: Collinearity tolerance

    Returns:
        Simplified list of points
    """
    if len(points) <= 2:
        return points

    simplified = [points[0]]

    for i in range(1, len(points) - 1):
        prev = points[i - 1]
        curr = points[i]
        next = points[i + 1]

        # Check if points are collinear
        cross = (curr.y - prev.y) * (next.x - curr.x) - (curr.x - prev.x) * (
            next.y - curr.y
        )
        if abs(cross) > tolerance:
            simplified.append(curr)

    simplified.append(points[-1])
    return simplified
