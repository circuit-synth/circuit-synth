"""
Base classes for PCB component placement.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple

from ..types import Footprint, Pad, Point
from .bbox import BoundingBox
from .courtyard_collision import CourtyardCollisionDetector


class ComponentWrapper:
    """Wrapper around footprint with placement-specific methods."""

    def __init__(self, *args, **kwargs):
        """
        Initialize ComponentWrapper.

        Can be initialized in multiple ways:
        1. With a Footprint object: ComponentWrapper(footprint)
        2. With positional args: ComponentWrapper(ref, footprint, value, position, pads)
        3. With keyword args: ComponentWrapper(reference="R1", footprint="R_0603", ...)
        """
        if len(args) == 1 and isinstance(args[0], Footprint):
            # Single Footprint object
            self.footprint = args[0]
        elif len(args) > 1 or (len(args) == 1 and isinstance(args[0], str)):
            # Positional arguments: ref, footprint, value, position, pads
            reference = args[0] if len(args) > 0 else ""
            footprint_name = args[1] if len(args) > 1 else ""
            value = args[2] if len(args) > 2 else ""
            position = args[3] if len(args) > 3 else Point(0, 0)
            pads = args[4] if len(args) > 4 else []
            hierarchical_path = kwargs.get("hierarchical_path", "")

            # Parse library and name from footprint string
            if ":" in footprint_name:
                library, name = footprint_name.split(":", 1)
            else:
                # Guess library from footprint name
                if footprint_name.startswith("R_"):
                    library = "Resistor_SMD"
                elif footprint_name.startswith("C_"):
                    library = "Capacitor_SMD"
                elif "SOIC" in footprint_name:
                    library = "Package_SO"
                elif "QFP" in footprint_name:
                    library = "Package_QFP"
                else:
                    library = "Generic"
                name = footprint_name

            self.footprint = Footprint(
                library=library,
                name=name,
                position=position,
                reference=reference,
                value=value,
                pads=pads,
                path=hierarchical_path,
            )
        else:
            # Keyword arguments
            reference = kwargs.get("reference", "")
            footprint_name = kwargs.get("footprint", "")
            value = kwargs.get("value", "")
            position = kwargs.get("position", Point(0, 0))
            pads = kwargs.get("pads", [])
            hierarchical_path = kwargs.get("hierarchical_path", "")

            # Parse library and name from footprint string
            if ":" in footprint_name:
                library, name = footprint_name.split(":", 1)
            else:
                # Guess library from footprint name
                if footprint_name.startswith("R_"):
                    library = "Resistor_SMD"
                elif footprint_name.startswith("C_"):
                    library = "Capacitor_SMD"
                elif "SOIC" in footprint_name:
                    library = "Package_SO"
                elif "QFP" in footprint_name:
                    library = "Package_QFP"
                else:
                    library = "Generic"
                name = footprint_name

            self.footprint = Footprint(
                library=library,
                name=name,
                position=position,
                reference=reference,
                value=value,
                pads=pads,
                path=hierarchical_path,
            )

        self._bbox_cache = None
        self._courtyard_detector = CourtyardCollisionDetector()

    @property
    def reference(self) -> str:
        """Get the component reference."""
        return self.footprint.reference

    @property
    def position(self) -> Point:
        """Get the component position."""
        return self.footprint.position

    @property
    def value(self) -> str:
        """Get the component value."""
        return self.footprint.value

    @property
    def bbox(self) -> BoundingBox:
        """Get the bounding box of the component."""
        if self._bbox_cache is None:
            self._calculate_bbox()
        return self._bbox_cache

    @property
    def original_bbox(self) -> BoundingBox:
        """Get the original (non-inflated) bounding box of the component."""
        if (
            not hasattr(self, "_original_bbox_cache")
            or self._original_bbox_cache is None
        ):
            self._calculate_bbox()
            self._original_bbox_cache = self._bbox_cache
        return self._original_bbox_cache

    def _calculate_bbox(self):
        """Calculate the bounding box from footprint elements, prioritizing courtyard layer."""
        # First, try to get bounding box from courtyard layer
        try:
            courtyard_polygon = self._courtyard_detector.get_courtyard_polygon(
                self.footprint
            )
            # Use courtyard bounding box, transformed to footprint position and rotation
            transformed_polygon = courtyard_polygon.transform(
                self.footprint.position.x,
                self.footprint.position.y,
                self.footprint.rotation,
            )
            min_x, min_y, max_x, max_y = transformed_polygon.get_bounding_box()
            self._bbox_cache = BoundingBox(min_x, min_y, max_x, max_y)
            return
        except ValueError as e:
            # Courtyard missing - log warning and fall back to calculated bounding box
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(
                f"Falling back to calculated bounding box for {self.footprint.reference}: {e}"
            )

        # Fallback: Calculate bounding box from footprint elements
        points = []

        # Add pad positions
        for pad in self.footprint.pads:
            # Convert pad position to absolute coordinates
            x = self.footprint.position.x + pad.position.x
            y = self.footprint.position.y + pad.position.y

            # Add pad corners based on size (tuple: width, height)
            half_width = pad.size[0] / 2
            half_height = pad.size[1] / 2

            points.extend(
                [(x - half_width, y - half_height), (x + half_width, y + half_height)]
            )

        # Add graphic lines
        for line in self.footprint.lines:
            points.append(
                (
                    self.footprint.position.x + line.start.x,
                    self.footprint.position.y + line.start.y,
                )
            )
            points.append(
                (
                    self.footprint.position.x + line.end.x,
                    self.footprint.position.y + line.end.y,
                )
            )

        # Add text positions (approximate)
        for text in self.footprint.texts:
            x = self.footprint.position.x + text.position.x
            y = self.footprint.position.y + text.position.y
            # Approximate text size
            points.extend([(x - 2, y - 1), (x + 2, y + 1)])

        # Create bounding box from all points
        if points:
            self._bbox_cache = BoundingBox.from_points(points)
        else:
            # Default small bbox if no elements
            x, y = self.footprint.position.x, self.footprint.position.y
            self._bbox_cache = BoundingBox(x - 1, y - 1, x + 1, y + 1)

    @property
    def area(self) -> float:
        """Get the area of the component's bounding box."""
        return self.bbox.area()

    @property
    def hierarchical_path(self) -> str:
        """Get the hierarchical path of the component."""
        # Extract from path property if it exists
        path = getattr(self.footprint, "path", "")
        if not path:
            # Try to extract from tstamp or other properties
            for prop in self.footprint.properties:
                if prop.name == "Sheetfile" or prop.name == "Sheetname":
                    path = prop.value
                    break

        # Return the path as-is, it's already in the correct format
        return path

    @property
    def is_locked(self) -> bool:
        """Check if the component is locked in place."""
        return self.footprint.locked

    def move_to(self, x: float, y: float):
        """Move the component to a new position."""
        if not self.is_locked:
            self.footprint.position.x = x
            self.footprint.position.y = y
            # Invalidate bbox cache
            self._bbox_cache = None

    def set_bottom_left(self, x: float, y: float):
        """Set the position based on the bottom-left corner."""
        if not self.is_locked:
            # Calculate offset from current bottom-left to center using original bbox
            # We use original bbox here because we want to position the actual component,
            # not the inflated spacing envelope
            bl_x, bl_y = self.original_bbox.bottom_left()
            center_x, center_y = self.original_bbox.center()
            offset_x = center_x - bl_x
            offset_y = center_y - bl_y

            # Move to new position
            self.move_to(x + offset_x, y + offset_y)

    def touches(self, other: "ComponentWrapper") -> bool:
        """Check if this component's bounding box touches another's."""
        # Slightly shrink the bounding boxes to avoid false positives
        # when components are exactly adjacent
        bbox1 = self.bbox.inflate(-0.01)
        bbox2 = other.bbox.inflate(-0.01)
        return bbox1.intersects(bbox2)


class PlacementAlgorithm(ABC):
    """Abstract base class for placement algorithms."""

    @abstractmethod
    def place(
        self,
        components: List[ComponentWrapper],
        connections: List[Tuple[str, str]],
        board_width: float = 100.0,
        board_height: float = 100.0,
        **kwargs,
    ) -> Dict[str, Point]:
        """
        Place components on the board.

        Args:
            components: List of components to place
            connections: List of (ref1, ref2) tuples representing connections
            board_width: Board width in mm
            board_height: Board height in mm
            **kwargs: Algorithm-specific parameters

        Returns:
            Dictionary mapping component references to positions
        """
        pass
