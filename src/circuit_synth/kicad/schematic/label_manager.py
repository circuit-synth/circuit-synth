"""
Label management for KiCad schematics.
Provides add, remove, update, and search operations for schematic labels.
"""

import logging
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from ..core.types import Label, LabelType, Point, Schematic, Wire
from .connection_utils import points_equal, snap_to_grid

logger = logging.getLogger(__name__)


class LabelManager:
    """
    Manages labels in a KiCad schematic.
    Provides high-level operations for adding, removing, and manipulating labels.
    """

    def __init__(self, schematic: Schematic):
        """
        Initialize label manager with a schematic.

        Args:
            schematic: The schematic to manage
        """
        self.schematic = schematic
        self._label_index = self._build_label_index()

    def _build_label_index(self) -> Dict[str, Label]:
        """Build an index of labels by UUID for fast lookup."""
        return {label.uuid: label for label in self.schematic.labels}

    def _generate_uuid(self) -> str:
        """Generate a new UUID for a label."""
        return str(uuid.uuid4())

    def add_label(
        self,
        text: str,
        position: Tuple[float, float],
        label_type: LabelType = LabelType.LOCAL,
        orientation: int = 0,
        snap_points: bool = True,
        effects: Optional[Dict[str, Any]] = None,
    ) -> Optional[Label]:
        """
        Add a label to the schematic.

        Args:
            text: Label text
            position: (x, y) position
            label_type: Type of label (LOCAL, GLOBAL, HIERARCHICAL)
            orientation: Rotation angle (0, 90, 180, 270)
            snap_points: Whether to snap position to grid
            effects: Optional text effects (font, size, etc.)

        Returns:
            Created label or None if invalid
        """
        if not text:
            logger.error("Label text cannot be empty")
            return None

        # Validate orientation
        if orientation not in [0, 90, 180, 270]:
            logger.error(
                f"Invalid orientation {orientation}, must be 0, 90, 180, or 270"
            )
            return None

        # Convert position to Point and optionally snap to grid
        x, y = position
        if snap_points:
            x, y = snap_to_grid((x, y))
        label_position = Point(x, y)

        # Create label
        label = Label(
            text=text,
            position=label_position,
            label_type=label_type,
            orientation=orientation,
            effects=effects,
            uuid=self._generate_uuid(),
        )

        # Add to schematic
        self.schematic.add_label(label)
        self._label_index[label.uuid] = label

        logger.info(f"Added {label_type.value} label '{text}' at ({x}, {y})")
        return label

    def remove_label(self, label_uuid: str) -> bool:
        """
        Remove a label from the schematic.

        Args:
            label_uuid: UUID of label to remove

        Returns:
            True if removed, False if not found
        """
        label = self._label_index.get(label_uuid)
        if not label:
            logger.warning(f"Label {label_uuid} not found")
            return False

        # Remove from schematic
        self.schematic.labels.remove(label)
        del self._label_index[label_uuid]

        logger.info(f"Removed label '{label.text}'")
        return True

    def update_label(self, label_uuid: str, **properties) -> bool:
        """
        Update label properties.

        Args:
            label_uuid: UUID of label to update
            **properties: Properties to update (text, position, orientation, etc.)

        Returns:
            True if updated, False if not found
        """
        label = self._label_index.get(label_uuid)
        if not label:
            logger.warning(f"Label {label_uuid} not found")
            return False

        # Update properties
        for key, value in properties.items():
            if hasattr(label, key):
                if key == "position" and isinstance(value, tuple):
                    # Convert tuple to Point
                    x, y = value
                    if properties.get("snap_points", True):
                        x, y = snap_to_grid((x, y))
                    value = Point(x, y)
                elif key == "orientation":
                    # Validate orientation
                    if value not in [0, 90, 180, 270]:
                        logger.error(f"Invalid orientation {value}")
                        continue

                setattr(label, key, value)
                logger.debug(f"Updated label {key} to {value}")

        return True

    def find_labels_at_point(
        self, point: Tuple[float, float], tolerance: float = 0.1
    ) -> List[Label]:
        """
        Find labels at or near a specific point.

        Args:
            point: (x, y) coordinates to search
            tolerance: Distance tolerance for matching

        Returns:
            List of labels at or near the point
        """
        test_point = Point(*point)
        matching_labels = []

        for label in self.schematic.labels:
            if points_equal(label.position, test_point, tolerance):
                matching_labels.append(label)

        return matching_labels

    def find_labels_by_text(
        self, pattern: str, exact_match: bool = False
    ) -> List[Label]:
        """
        Find labels by text pattern.

        Args:
            pattern: Text pattern to search for
            exact_match: If True, require exact match; if False, substring match

        Returns:
            List of matching labels
        """
        matching_labels = []

        for label in self.schematic.labels:
            if exact_match:
                if label.text == pattern:
                    matching_labels.append(label)
            else:
                if pattern.lower() in label.text.lower():
                    matching_labels.append(label)

        return matching_labels

    def auto_position_label(
        self,
        text: str,
        near_point: Tuple[float, float],
        label_type: LabelType = LabelType.LOCAL,
        offset: float = 2.54,
    ) -> Optional[Label]:
        """
        Automatically position a label near a point (e.g., wire endpoint).

        Args:
            text: Label text
            near_point: Point to position label near
            label_type: Type of label
            offset: Distance from point (in mm)

        Returns:
            Created label or None if failed
        """
        x, y = near_point

        # Find nearby wires to determine best orientation
        nearby_wires = self._find_wires_near_point(near_point)

        if nearby_wires:
            # Position based on wire direction
            wire = nearby_wires[0]

            # Determine wire direction at the point
            if self._is_horizontal_wire(wire):
                # Place label above or below horizontal wire
                label_y = y - offset if y > 50 else y + offset
                label_position = (x, label_y)
                orientation = 0
            else:
                # Place label left or right of vertical wire
                label_x = x - offset if x > 50 else x + offset
                label_position = (label_x, y)
                orientation = 0
        else:
            # Default positioning if no wires found
            label_position = (x + offset, y)
            orientation = 0

        return self.add_label(
            text=text,
            position=label_position,
            label_type=label_type,
            orientation=orientation,
        )

    def _find_wires_near_point(
        self, point: Tuple[float, float], tolerance: float = 2.54
    ) -> List[Wire]:
        """Find wires near a specific point."""
        test_point = Point(*point)
        nearby_wires = []

        for wire in self.schematic.wires:
            for wire_point in wire.points:
                if points_equal(wire_point, test_point, tolerance):
                    nearby_wires.append(wire)
                    break

        return nearby_wires

    def _is_horizontal_wire(self, wire: Wire) -> bool:
        """Check if a wire is primarily horizontal."""
        if len(wire.points) < 2:
            return True

        # Check first segment
        p1, p2 = wire.points[0], wire.points[1]
        dx = abs(p2.x - p1.x)
        dy = abs(p2.y - p1.y)

        return dx > dy

    def get_label_by_uuid(self, label_uuid: str) -> Optional[Label]:
        """Get a label by its UUID."""
        return self._label_index.get(label_uuid)

    def get_labels_by_type(self, label_type: LabelType) -> List[Label]:
        """Get all labels of a specific type."""
        return [
            label for label in self.schematic.labels if label.label_type == label_type
        ]

    def validate_hierarchical_labels(self) -> List[str]:
        """
        Validate hierarchical labels.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        hierarchical_labels = self.get_labels_by_type(LabelType.HIERARCHICAL)

        # Check for duplicate hierarchical label names
        label_names = {}
        for label in hierarchical_labels:
            if label.text in label_names:
                errors.append(f"Duplicate hierarchical label: {label.text}")
            else:
                label_names[label.text] = label

        # Additional validation could check against sheet pins

        return errors
