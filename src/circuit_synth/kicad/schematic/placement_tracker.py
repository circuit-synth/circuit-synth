"""
Track component placements and update intermediate JSON file in real-time.
"""

import json
from pathlib import Path
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class PlacementTracker:
    """Tracks component placements and updates JSON file."""

    _instance = None
    _json_path: Optional[Path] = None
    _layout_data = None

    @classmethod
    def initialize(cls, json_path: Path):
        """
        Initialize the placement tracker with a JSON file path.

        Args:
            json_path: Path to the layout JSON file
        """
        cls._json_path = json_path

        # Load existing JSON if it exists
        if json_path.exists():
            with open(json_path, 'r') as f:
                cls._layout_data = json.load(f)
        else:
            cls._layout_data = {
                "metadata": {
                    "algorithm": "text_flow",
                    "spacing_mm": 5.08,
                    "margin_mm": 25.4,
                },
                "components": []
            }

        logger.info(f"PlacementTracker initialized with {json_path}")

    @classmethod
    def update_component_position(
        cls,
        reference: str,
        position: Tuple[float, float],
        width: float,
        height: float
    ):
        """
        Update a component's position in the JSON file.

        Args:
            reference: Component reference (e.g., "U1")
            position: (x, y) position in mm (center point)
            width: Component bounding box width in mm
            height: Component bounding box height in mm
        """
        if cls._layout_data is None:
            logger.warning("PlacementTracker not initialized, skipping update")
            return

        x, y = position

        # Calculate bounding box corners from center position
        x1 = x - width / 2
        y1 = y - height / 2
        x2 = x + width / 2
        y2 = y + height / 2

        # Find existing component or create new entry
        component_entry = None
        for comp in cls._layout_data["components"]:
            if comp["ref"] == reference:
                component_entry = comp
                break

        if component_entry is None:
            # Create new entry
            component_entry = {
                "ref": reference,
                "bbox": {}
            }
            cls._layout_data["components"].append(component_entry)

        # Update bounding box
        component_entry["bbox"] = {
            "x1": x1,
            "y1": y1,
            "x2": x2,
            "y2": y2,
            "width": width,
            "height": height
        }

        # Write updated JSON
        if cls._json_path:
            with open(cls._json_path, 'w') as f:
                json.dump(cls._layout_data, f, indent=2)

        print(f"  📍 {reference:6s} positioned at ({x:6.1f}, {y:6.1f}) -> JSON updated")

    @classmethod
    def get_layout_data(cls):
        """Get the current layout data."""
        return cls._layout_data

    @classmethod
    def finalize(cls):
        """Finalize tracking and ensure JSON is written."""
        if cls._json_path and cls._layout_data:
            with open(cls._json_path, 'w') as f:
                json.dump(cls._layout_data, f, indent=2)
            logger.info(f"PlacementTracker finalized, wrote to {cls._json_path}")
