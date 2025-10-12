"""
ComponentUnit - A unified representation of a component with its labels and bounding box.

This module provides the ComponentUnit dataclass which treats a component, its hierarchical
labels, and visual bounding box as a single movable unit. This ensures that bbox dimensions
are independent of placement location and all elements move together atomically.
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple

from kicad_sch_api.core.types import SchematicSymbol, Label, Rectangle


@dataclass
class ComponentUnit:
    """
    A component with its labels and bounding box, treated as a single movable unit.

    All coordinates are in GLOBAL schematic coordinates.

    The key insight: bbox dimensions are calculated once based on the component's
    connected labels, then the entire unit (component + labels + bbox) can be moved
    to any position without recalculating dimensions.
    """

    # Core component
    component: SchematicSymbol  # The KiCad component

    # Connected labels (in global coordinates)
    labels: List[Label]  # Only hierarchical labels created for this component's pins

    # Bounding box (in global coordinates)
    bbox_min_x: float  # Left edge
    bbox_min_y: float  # Top edge
    bbox_max_x: float  # Right edge
    bbox_max_y: float  # Bottom edge

    # Visual element
    bbox_graphic: Optional[Rectangle] = None  # The drawn rectangle (if draw_bounding_boxes=True)

    @property
    def width(self) -> float:
        """Bounding box width in mm"""
        return self.bbox_max_x - self.bbox_min_x

    @property
    def height(self) -> float:
        """Bounding box height in mm"""
        return self.bbox_max_y - self.bbox_min_y

    @property
    def center(self) -> Tuple[float, float]:
        """Component center position (x, y) in mm"""
        return (self.component.position.x, self.component.position.y)

    @property
    def reference(self) -> str:
        """Component reference designator (e.g., 'U1', 'C1')"""
        return self.component.reference

    def move_to(self, new_center_x: float, new_center_y: float) -> None:
        """
        Move the entire unit to a new center position.

        Updates component position, all labels, and bbox graphic atomically.
        Bbox dimensions remain unchanged.

        Args:
            new_center_x: New X coordinate for component center (mm)
            new_center_y: New Y coordinate for component center (mm)
        """
        # Calculate offset from current position
        old_x, old_y = self.center
        dx = new_center_x - old_x
        dy = new_center_y - old_y

        # Move component
        self.component.position = Point(new_center_x, new_center_y)

        # Move all labels by the same offset
        for label in self.labels:
            label.position = Point(label.position.x + dx, label.position.y + dy)

        # Move bounding box edges
        self.bbox_min_x += dx
        self.bbox_min_y += dy
        self.bbox_max_x += dx
        self.bbox_max_y += dy

        # Move bbox graphic if it exists
        if self.bbox_graphic:
            self.bbox_graphic.start.x += dx
            self.bbox_graphic.start.y += dy
            self.bbox_graphic.end.x += dx
            self.bbox_graphic.end.y += dy

    def __repr__(self) -> str:
        """String representation for debugging"""
        return (
            f"ComponentUnit({self.reference}, "
            f"center=({self.center[0]:.1f}, {self.center[1]:.1f}), "
            f"bbox={self.width:.1f}×{self.height:.1f}mm, "
            f"labels={len(self.labels)})"
        )
