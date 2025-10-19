"""
Text-flow component placement algorithm.

Places components left-to-right, wrapping to new rows when reaching sheet edge.
Implements the algorithm defined in text_flow_placement_prd.md
"""

import logging
from typing import List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


def snap_to_grid(value: float, grid_size: float = 2.54) -> float:
    """
    Snap a coordinate value to the nearest grid point.

    KiCad uses a 2.54mm (100mil) grid by default for professional schematics.

    Args:
        value: Coordinate value in mm
        grid_size: Grid size in mm (default: 2.54mm = 100mil)

    Returns:
        Value snapped to nearest grid point
    """
    snapped = round(value / grid_size) * grid_size
    logger.debug(f"snap_to_grid({value:.3f}) = {snapped:.3f} (grid={grid_size})")
    return snapped


@dataclass
class SheetDef:
    """Sheet size definition."""
    name: str
    width: float  # Total sheet width in mm
    height: float  # Total sheet height in mm
    min_x: float  # Usable area left boundary
    min_y: float  # Usable area top boundary
    max_x: float  # Usable area right boundary
    max_y: float  # Usable area bottom boundary


# Supported sheet sizes with usable areas (avoiding title blocks)
# A4 portrait: 210×297mm, usable area leaves ~10mm margins
# A3 landscape: 420×297mm, usable area leaves ~10mm margins
SHEET_SIZES = [
    SheetDef("A4", 297.0, 210.0, 12.7, 12.7, 284.48, 165.10),
    SheetDef("A3", 420.0, 297.0, 12.7, 12.7, 407.0, 277.0),
]


class TextFlowPlacer:
    """
    Place components using text-flow algorithm per PRD.

    Components flow left-to-right with 2.54mm spacing, wrapping to new rows.
    Rows are aligned by top of bounding box with 2.54mm spacing between rows.
    """

    def __init__(self, spacing: float = 2.54):
        """
        Initialize text-flow placer.

        Args:
            spacing: Spacing between components and rows in mm (default: 2.54mm = 100mil)
        """
        self.spacing = spacing

    def place_components(
        self, component_bboxes: List[Tuple[str, float, float]]
    ) -> Tuple[List[Tuple[str, float, float]], str]:
        """
        Place components using text-flow algorithm.
        Tries A4 first, then A3 if overflow. Throws error if A3 overflows.

        Args:
            component_bboxes: List of (ref, width, height) tuples

        Returns:
            Tuple of (placements, selected_sheet_size)
            where placements = [(ref, center_x, center_y), ...]

        Raises:
            ValueError: If components don't fit on A3 sheet
        """
        print(f"\n{'='*80}")
        print(f"🔤 TEXT-FLOW PLACEMENT ALGORITHM")
        print(f"{'='*80}")
        print(f"Components to place: {len(component_bboxes)}")
        print(f"Spacing: {self.spacing}mm\n")

        # Try each sheet size
        for sheet in SHEET_SIZES:
            print(f"Trying {sheet.name} ({sheet.width}×{sheet.height}mm)")
            print(f"  Usable area: ({sheet.min_x}, {sheet.min_y}) to ({sheet.max_x}, {sheet.max_y})")

            placements, success = self._try_place_on_sheet(component_bboxes, sheet)

            if success:
                print(f"✅ All components fit on {sheet.name}!")
                print(f"{'='*80}\n")
                return placements, sheet.name
            else:
                print(f"❌ Overflow on {sheet.name}, trying next size...\n")

        # If we get here, even A3 overflowed
        raise ValueError(
            f"Components do not fit on A3 sheet (largest supported size). "
            f"Reduce component count or implement larger sheet support."
        )

    def _try_place_on_sheet(
        self,
        component_bboxes: List[Tuple[str, float, float]],
        sheet: SheetDef
    ) -> Tuple[List[Tuple[str, float, float]], bool]:
        """
        Try to place components on given sheet size.

        Args:
            component_bboxes: List of (ref, width, height)
            sheet: Sheet definition

        Returns:
            Tuple of (placements, success)
            placements = [(ref, center_x, center_y), ...]
            success = True if all components fit
        """
        placements = []

        # Sort components by area (largest first), then by width
        # This ensures better space utilization
        sorted_bboxes = sorted(
            component_bboxes,
            key=lambda x: (x[1] * x[2], x[1]),  # (area, width)
            reverse=True
        )

        print(f"  Sorted components (largest first):")
        for i, (ref, width, height) in enumerate(sorted_bboxes[:5]):
            print(f"    [{i+1}] {ref}: {width:.1f}×{height:.1f}mm (area={width*height:.1f}mm²)")
        if len(sorted_bboxes) > 5:
            print(f"    ... and {len(sorted_bboxes)-5} more")
        print()

        # Initialize bounding box position (top-left corner)
        # Add extra left margin for first component to account for leftward hierarchical labels
        LEFT_MARGIN_PADDING = 12.0  # Extra space for labels extending left from first component
        bbox_x = sheet.min_x + LEFT_MARGIN_PADDING
        bbox_y = sheet.min_y
        current_row_height = 0.0

        for i, (ref, width, height) in enumerate(sorted_bboxes):
            # Check if component fits in current row
            if bbox_x + width > sheet.max_x:
                # Wrap to next row - add left padding again
                bbox_x = sheet.min_x + LEFT_MARGIN_PADDING
                bbox_y += current_row_height + self.spacing
                current_row_height = 0.0
                print(f"  ↓ Row wrap at y={bbox_y:.1f}mm")

            # Check if component fits on sheet vertically
            if bbox_y + height > sheet.max_y:
                print(f"  ⚠️  Component {ref} overflows at y={bbox_y:.1f}mm (max={sheet.max_y:.1f}mm)")
                return placements, False

            # Calculate component center position and snap to grid
            center_x_raw = bbox_x + width / 2
            center_y_raw = bbox_y + height / 2

            # Snap to 2.54mm (100mil) grid for professional KiCad appearance
            center_x = snap_to_grid(center_x_raw, 2.54)
            center_y = snap_to_grid(center_y_raw, 2.54)

            placements.append((ref, center_x, center_y))

            print(
                f"  [{i+1:2d}] {ref:6s} ({width:5.1f}×{height:5.1f}mm) "
                f"bbox=({bbox_x:6.1f},{bbox_y:6.1f}) center=({center_x:6.1f},{center_y:6.1f})"
            )

            # Update for next component
            bbox_x += width + self.spacing
            current_row_height = max(current_row_height, height)

        return placements, True


def place_with_text_flow(
    component_bboxes: List[Tuple[str, float, float]],
    spacing: float = 2.54
) -> Tuple[List[Tuple[str, float, float]], str]:
    """
    Convenience function for text-flow placement.

    Args:
        component_bboxes: List of (ref, width, height) tuples
        spacing: Spacing in mm (default 2.54mm = 100mil)

    Returns:
        Tuple of (placements, sheet_size)
        where placements = [(ref, center_x, center_y), ...]
    """
    placer = TextFlowPlacer(spacing=spacing)
    return placer.place_components(component_bboxes)
