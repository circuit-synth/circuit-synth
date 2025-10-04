"""
Intermediate layout format for LLM-assisted schematic component placement.

This module provides functionality to extract component bounding boxes and
save them in an LLM-friendly JSON format for layout analysis and optimization.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

from ..core.types import Schematic, SchematicSymbol
from .symbol_geometry import SymbolGeometry

logger = logging.getLogger(__name__)


class LayoutIntermediate:
    """Generate intermediate layout representation for LLM analysis."""

    def __init__(self, schematic: Schematic):
        """
        Initialize layout intermediate generator.

        Args:
            schematic: The schematic containing components
        """
        self.schematic = schematic
        self._symbol_geometry = SymbolGeometry()

    def _estimate_component_bbox(
        self, component: SchematicSymbol
    ) -> Tuple[float, float]:
        """
        Estimate component bounding box size.

        Args:
            component: Component to estimate size for

        Returns:
            (width, height) in mm
        """
        logger.debug(
            f"Estimating bbox for {component.reference} ({component.lib_id})"
        )

        # Get actual symbol dimensions from library
        try:
            symbol_width, symbol_height = self._symbol_geometry.get_symbol_bounds(
                component.lib_id
            )
            logger.debug(
                f"Got symbol bounds: {symbol_width:.2f} x {symbol_height:.2f} mm"
            )
        except Exception as e:
            logger.warning(f"Failed to get symbol bounds for {component.lib_id}: {e}")
            # Fallback to estimation
            pin_count = len(component.pins) if component.pins else 2
            if "Regulator" in component.lib_id or "U" in component.reference:
                symbol_width = 15.24  # 600 mil
                symbol_height = 15.24
            elif pin_count > 4:
                symbol_width = 12.7 + (pin_count * 1.27)
                symbol_height = 12.7
            else:
                symbol_width = 7.62  # 300 mil
                symbol_height = 5.08  # 200 mil

        # Calculate text dimensions
        ref_text = component.reference or "?"
        ref_width = SymbolGeometry.calculate_text_width(ref_text, 1.27)
        ref_height = 1.27

        value_text = component.value or ""
        value_width = (
            SymbolGeometry.calculate_text_width(value_text, 1.27) if value_text else 0
        )
        value_height = 1.27 if value_text else 0

        # Add space for pin labels
        max_pin_label_width = 0
        if component.pins:
            for pin in component.pins:
                if pin.name and pin.name != "~":
                    label_width = SymbolGeometry.calculate_text_width(pin.name, 1.0)
                    max_pin_label_width = max(max_pin_label_width, label_width)

        pin_label_padding = (
            max_pin_label_width + 2.54 if max_pin_label_width > 0 else 2.54
        )

        # Total size calculation
        width = symbol_width + (2 * pin_label_padding)
        height = symbol_height + ref_height + 1.27 + value_height + 1.27

        # Ensure text doesn't make component narrower than needed
        width = max(width, ref_width + 2.54, value_width + 2.54)

        logger.info(
            f"Component {component.reference} bbox: {width:.1f} x {height:.1f} mm"
        )

        return (width, height)

    def extract_component_bboxes(self) -> List[Dict[str, Any]]:
        """
        Extract bounding box information for all components.

        Returns:
            List of component bbox dictionaries with structure:
            {
                "ref": "U1",
                "bbox": {
                    "x1": 0, "y1": 0, "x2": 50, "y2": 40,
                    "width": 50, "height": 40
                }
            }
        """
        component_bboxes = []

        print(f"\n{'='*80}")
        print(f"📦 EXTRACTING COMPONENT BOUNDING BOXES")
        print(f"{'='*80}")
        print(f"Total components: {len(self.schematic.components)}\n")

        for i, comp in enumerate(self.schematic.components):
            width, height = self._estimate_component_bbox(comp)

            # Start all components at origin (0, 0)
            x1, y1 = 0.0, 0.0
            x2, y2 = width, height

            bbox_data = {
                "ref": comp.reference,
                "bbox": {
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2,
                    "width": width,
                    "height": height,
                },
            }

            component_bboxes.append(bbox_data)

            print(
                f"  [{i+1:2d}] {comp.reference:6s}: "
                f"{width:6.1f} x {height:6.1f} mm"
            )

        print(f"\n{'='*80}\n")
        return component_bboxes

    def save_to_file(self, output_path: Path, metadata: Dict[str, Any] = None) -> None:
        """
        Save component bounding boxes to JSON file.

        Args:
            output_path: Path to save JSON file
            metadata: Optional metadata to include in the file
        """
        component_bboxes = self.extract_component_bboxes()

        layout_data = {
            "metadata": metadata or {},
            "components": component_bboxes,
        }

        with open(output_path, "w") as f:
            json.dump(layout_data, f, indent=2)

        logger.info(f"Saved layout intermediate to {output_path}")
        print(f"💾 Saved layout intermediate to: {output_path}")
        print(f"   Total components: {len(component_bboxes)}")


def generate_layout_intermediate(
    schematic: Schematic, output_path: Path, metadata: Dict[str, Any] = None
) -> None:
    """
    Convenience function to generate layout intermediate file.

    Args:
        schematic: Schematic containing components
        output_path: Path to save JSON file
        metadata: Optional metadata to include
    """
    layout_gen = LayoutIntermediate(schematic)
    layout_gen.save_to_file(output_path, metadata)
