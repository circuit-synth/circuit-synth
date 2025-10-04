"""
Text-flow component placement algorithm.

Places components left-to-right, wrapping to new rows when reaching sheet edge.
Implements the algorithm defined in text_flow_placement_prd.md
"""

import logging
from typing import List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


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
SHEET_SIZES = [
    SheetDef("A4", 210.0, 297.0, 12.7, 12.7, 176.53, 196.85),
    SheetDef("A3", 297.0, 420.0, 12.7, 12.7, 407.67, 252.73),
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

        # Initialize bounding box position (top-left corner)
        bbox_x = sheet.min_x
        bbox_y = sheet.min_y
        current_row_height = 0.0

        for i, (ref, width, height) in enumerate(component_bboxes):
            # Check if component fits in current row
            if bbox_x + width > sheet.max_x:
                # Wrap to next row
                bbox_x = sheet.min_x
                bbox_y += current_row_height + self.spacing
                current_row_height = 0.0
                print(f"  ↓ Row wrap at y={bbox_y:.1f}mm")

            # Check if component fits on sheet vertically
            if bbox_y + height > sheet.max_y:
                print(f"  ⚠️  Component {ref} overflows at y={bbox_y:.1f}mm (max={sheet.max_y:.1f}mm)")
                return placements, False

            # Calculate component center position
            center_x = bbox_x + width / 2
            center_y = bbox_y + height / 2

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
