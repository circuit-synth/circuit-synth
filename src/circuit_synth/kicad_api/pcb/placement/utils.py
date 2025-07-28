"""
Utility functions for PCB placement algorithms.
"""

from typing import List, Optional, Tuple

from circuit_synth.kicad_api.pcb.placement.bbox import BoundingBox
from circuit_synth.kicad_api.pcb.types import Footprint, Point


def calculate_placement_bbox(
    footprints: List[Footprint], margin: float = 10.0
) -> Tuple[float, float, float, float]:
    """
    Calculate the bounding box of placed footprints with margin.

    Args:
        footprints: List of placed footprints
        margin: Margin to add around the bounding box (mm)

    Returns:
        Tuple of (min_x, min_y, max_x, max_y)
    """
    if not footprints:
        return 0, 0, 100, 100  # Default if no footprints

    # Initialize with first footprint
    first_fp = footprints[0]
    min_x = max_x = first_fp.position.x
    min_y = max_y = first_fp.position.y

    # Find actual bounds of all footprints
    for fp in footprints:
        # Get footprint bounding box (approximate)
        fp_bbox = _estimate_footprint_bbox(fp)

        # Update overall bounds
        min_x = min(min_x, fp.position.x - fp_bbox.width() / 2)
        max_x = max(max_x, fp.position.x + fp_bbox.width() / 2)
        min_y = min(min_y, fp.position.y - fp_bbox.height() / 2)
        max_y = max(max_y, fp.position.y + fp_bbox.height() / 2)

    # Add margin
    min_x -= margin
    min_y -= margin
    max_x += margin
    max_y += margin

    # Ensure positive coordinates
    if min_x < 0:
        offset_x = -min_x
        min_x = 0
        max_x += offset_x
    if min_y < 0:
        offset_y = -min_y
        min_y = 0
        max_y += offset_y

    return min_x, min_y, max_x, max_y


def _estimate_footprint_bbox(fp: Footprint) -> BoundingBox:
    """
    Estimate footprint bounding box based on footprint type.

    Args:
        fp: Footprint to estimate

    Returns:
        Estimated bounding box
    """
    fp_name = f"{fp.library}:{fp.name}"

    # Estimate based on footprint type
    if "QFP" in fp_name or "LQFP" in fp_name:
        width = height = 10.0
    elif "SOT" in fp_name:
        width, height = 7.0, 4.0
    elif "USB" in fp_name:
        width, height = 15.0, 10.0
    elif "ESP" in fp_name or "RF_Module" in fp_name:
        width, height = 20.0, 15.0
    elif "LGA" in fp_name:
        width, height = 3.5, 3.0
    elif "Crystal" in fp_name:
        width, height = 5.0, 3.2
    elif "IDC" in fp_name or "Header" in fp_name:
        width, height = 10.0, 8.0
    elif "0603" in fp_name:
        width, height = 1.6, 0.8
    elif "0805" in fp_name:
        width, height = 2.0, 1.25
    elif "LED" in fp_name:
        width, height = 1.6, 0.8
    elif "SOD" in fp_name:
        width, height = 2.0, 1.2
    else:
        width = height = 5.0  # Default

    return BoundingBox(0, 0, width, height)


def optimize_component_rotation(
    fp: Footprint, connected_positions: List[Point]
) -> float:
    """
    Calculate optimal rotation for a component based on connected component positions.

    Args:
        fp: Footprint to rotate
        connected_positions: Positions of connected components

    Returns:
        Optimal rotation angle in degrees (0, 90, 180, or 270)
    """
    if not connected_positions:
        return 0.0

    # Calculate average angle to connected components
    total_angle = 0.0
    for pos in connected_positions:
        dx = pos.x - fp.position.x
        dy = pos.y - fp.position.y
        import math

        angle = math.atan2(dy, dx) * 180 / math.pi
        total_angle += angle

    avg_angle = total_angle / len(connected_positions)

    # Quantize to nearest 90 degrees
    if -45 <= avg_angle < 45:
        return 0.0
    elif 45 <= avg_angle < 135:
        return 90.0
    elif avg_angle >= 135 or avg_angle < -135:
        return 180.0
    else:  # -135 <= avg_angle < -45
        return 270.0
