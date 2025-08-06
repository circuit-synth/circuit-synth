"""Schematic transformation operations."""

import math
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from ..core.types import (
    Junction,
    Label,
    Point,
)
from ..core.types import SchematicSymbol as Component
from ..core.types import (
    Text,
    Wire,
)


@dataclass
class Position:
    x: float
    y: float
    angle: float


@dataclass
class NoConnect:
    at: Position
    uuid: str = ""


@dataclass
class BusEntry:
    at: Position
    size: tuple
    uuid: str = ""


class TransformType(Enum):
    """Types of transformations."""

    ROTATE_90 = "rotate_90"
    ROTATE_180 = "rotate_180"
    ROTATE_270 = "rotate_270"
    MIRROR_X = "mirror_x"
    MIRROR_Y = "mirror_y"
    SCALE = "scale"
    TRANSLATE = "translate"


@dataclass
class TransformMatrix:
    """2D transformation matrix."""

    a: float = 1.0  # Scale X / Rotation
    b: float = 0.0  # Shear X
    c: float = 0.0  # Shear Y
    d: float = 1.0  # Scale Y / Rotation
    tx: float = 0.0  # Translation X
    ty: float = 0.0  # Translation Y

    def apply(self, x: float, y: float) -> Tuple[float, float]:
        """Apply transformation to a point."""
        new_x = self.a * x + self.b * y + self.tx
        new_y = self.c * x + self.d * y + self.ty
        return new_x, new_y

    def compose(self, other: "TransformMatrix") -> "TransformMatrix":
        """Compose with another transformation."""
        return TransformMatrix(
            a=self.a * other.a + self.b * other.c,
            b=self.a * other.b + self.b * other.d,
            c=self.c * other.a + self.d * other.c,
            d=self.c * other.b + self.d * other.d,
            tx=self.a * other.tx + self.b * other.ty + self.tx,
            ty=self.c * other.tx + self.d * other.ty + self.ty,
        )

    @classmethod
    def identity(cls) -> "TransformMatrix":
        """Create identity matrix."""
        return cls()

    @classmethod
    def rotation(cls, angle_degrees: float) -> "TransformMatrix":
        """Create rotation matrix."""
        angle_rad = math.radians(angle_degrees)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        return cls(a=cos_a, b=-sin_a, c=sin_a, d=cos_a)

    @classmethod
    def scale(cls, sx: float, sy: float) -> "TransformMatrix":
        """Create scale matrix."""
        return cls(a=sx, d=sy)

    @classmethod
    def translation(cls, tx: float, ty: float) -> "TransformMatrix":
        """Create translation matrix."""
        return cls(tx=tx, ty=ty)

    @classmethod
    def mirror_x(cls) -> "TransformMatrix":
        """Create horizontal mirror matrix."""
        return cls(a=-1.0)

    @classmethod
    def mirror_y(cls) -> "TransformMatrix":
        """Create vertical mirror matrix."""
        return cls(d=-1.0)


@dataclass
class BoundingBox:
    """Bounding box for schematic elements."""

    min_x: float
    min_y: float
    max_x: float
    max_y: float

    @property
    def width(self) -> float:
        """Get width."""
        return self.max_x - self.min_x

    @property
    def height(self) -> float:
        """Get height."""
        return self.max_y - self.min_y

    @property
    def center(self) -> Tuple[float, float]:
        """Get center point."""
        return (self.min_x + self.max_x) / 2, (self.min_y + self.max_y) / 2

    def expand(self, margin: float) -> "BoundingBox":
        """Expand bounding box by margin."""
        return BoundingBox(
            min_x=self.min_x - margin,
            min_y=self.min_y - margin,
            max_x=self.max_x + margin,
            max_y=self.max_y + margin,
        )

    def contains_point(self, x: float, y: float) -> bool:
        """Check if point is inside bounding box."""
        return self.min_x <= x <= self.max_x and self.min_y <= y <= self.max_y

    def intersects(self, other: "BoundingBox") -> bool:
        """Check if intersects with another bounding box."""
        return not (
            self.max_x < other.min_x
            or self.min_x > other.max_x
            or self.max_y < other.min_y
            or self.min_y > other.max_y
        )


class SchematicTransform:
    """Performs geometric transformations on schematic elements."""

    def __init__(self):
        """Initialize transformer."""
        self._transform_stack: List[TransformMatrix] = []

    def push_transform(self, transform: TransformMatrix):
        """Push transformation onto stack."""
        self._transform_stack.append(transform)

    def pop_transform(self) -> Optional[TransformMatrix]:
        """Pop transformation from stack."""
        if self._transform_stack:
            return self._transform_stack.pop()
        return None

    def get_current_transform(self) -> TransformMatrix:
        """Get current combined transformation."""
        if not self._transform_stack:
            return TransformMatrix.identity()

        result = self._transform_stack[0]
        for transform in self._transform_stack[1:]:
            result = result.compose(transform)
        return result

    def transform_position(self, position: Position) -> Position:
        """Transform a position."""
        transform = self.get_current_transform()
        new_x, new_y = transform.apply(position.x, position.y)

        # Handle rotation angle
        new_angle = position.angle
        if hasattr(transform, "rotation_angle"):
            new_angle = (position.angle + transform.rotation_angle) % 360

        return Position(x=new_x, y=new_y, angle=new_angle)

    def transform_component(
        self, component: Component, transform: Optional[TransformMatrix] = None
    ):
        """Transform a component in place."""
        if transform:
            self.push_transform(transform)

        try:
            # Transform position - SchematicSymbol uses 'position' not 'at'
            if hasattr(component, "position"):
                # Create Position object from Point for transformation
                pos = Position(x=component.position.x, y=component.position.y, angle=0)
                new_pos = self.transform_position(pos)
                component.position = Point(new_pos.x, new_pos.y)
            elif hasattr(component, "at"):
                component.at = self.transform_position(component.at)

            # Transform properties - SchematicSymbol has dict properties
            if isinstance(component.properties, dict):
                # Properties are a simple dict in SchematicSymbol
                pass
            else:
                # Handle old-style properties with at attribute
                for prop in component.properties:
                    if hasattr(prop, "at") and prop.at:
                        prop.at = self.transform_position(prop.at)

            # Handle rotation for symbol orientation
            if isinstance(transform, TransformMatrix):
                # Update symbol transformation matrix if needed
                if hasattr(component, "transform"):
                    # This would need proper matrix multiplication
                    pass

        finally:
            if transform:
                self.pop_transform()

    def transform_wire(self, wire: Wire, transform: Optional[TransformMatrix] = None):
        """Transform a wire in place."""
        if transform:
            self.push_transform(transform)

        try:
            current = self.get_current_transform()

            # Transform all points in the wire
            for i, point in enumerate(wire.points):
                new_x, new_y = current.apply(point.x, point.y)
                wire.points[i] = Point(new_x, new_y)

        finally:
            if transform:
                self.pop_transform()

    def transform_junction(
        self, junction: Junction, transform: Optional[TransformMatrix] = None
    ):
        """Transform a junction in place."""
        if transform:
            self.push_transform(transform)

        try:
            junction.at = self.transform_position(junction.at)

        finally:
            if transform:
                self.pop_transform()

    def transform_text(self, text: Text, transform: Optional[TransformMatrix] = None):
        """Transform text in place."""
        if transform:
            self.push_transform(transform)

        try:
            text.at = self.transform_position(text.at)

        finally:
            if transform:
                self.pop_transform()

    def transform_label(
        self, label: Label, transform: Optional[TransformMatrix] = None
    ):
        """Transform label in place."""
        if transform:
            self.push_transform(transform)

        try:
            label.at = self.transform_position(label.at)

        finally:
            if transform:
                self.pop_transform()

    def rotate_elements(
        self,
        elements: List[Any],
        angle_degrees: float,
        center: Optional[Tuple[float, float]] = None,
    ):
        """Rotate elements around a center point."""
        # Calculate center if not provided
        if center is None:
            bbox = self.calculate_bounding_box(elements)
            center = bbox.center

        # Create rotation transform around center
        cx, cy = center
        transform = (
            TransformMatrix.translation(-cx, -cy)
            .compose(TransformMatrix.rotation(angle_degrees))
            .compose(TransformMatrix.translation(cx, cy))
        )

        # Apply to each element
        for element in elements:
            if isinstance(element, Component):
                self.transform_component(element, transform)
            elif isinstance(element, Wire):
                self.transform_wire(element, transform)
            elif isinstance(element, Junction):
                self.transform_junction(element, transform)
            elif isinstance(element, Text):
                self.transform_text(element, transform)
            elif isinstance(element, Label):
                self.transform_label(element, transform)

    def mirror_elements(
        self,
        elements: List[Any],
        axis: str = "x",
        center: Optional[Tuple[float, float]] = None,
    ):
        """Mirror elements across an axis."""
        # Calculate center if not provided
        if center is None:
            bbox = self.calculate_bounding_box(elements)
            center = bbox.center

        # Create mirror transform around center
        cx, cy = center
        if axis.lower() == "x":
            mirror = TransformMatrix.mirror_x()
        else:
            mirror = TransformMatrix.mirror_y()

        transform = (
            TransformMatrix.translation(-cx, -cy)
            .compose(mirror)
            .compose(TransformMatrix.translation(cx, cy))
        )

        # Apply to each element
        for element in elements:
            if isinstance(element, Component):
                self.transform_component(element, transform)
            elif isinstance(element, Wire):
                self.transform_wire(element, transform)
            elif isinstance(element, Junction):
                self.transform_junction(element, transform)
            elif isinstance(element, Text):
                self.transform_text(element, transform)
            elif isinstance(element, Label):
                self.transform_label(element, transform)

    def scale_elements(
        self,
        elements: List[Any],
        scale_x: float,
        scale_y: float,
        center: Optional[Tuple[float, float]] = None,
    ):
        """Scale elements from a center point."""
        # Calculate center if not provided
        if center is None:
            bbox = self.calculate_bounding_box(elements)
            center = bbox.center

        # Create scale transform around center
        cx, cy = center
        transform = (
            TransformMatrix.translation(-cx, -cy)
            .compose(TransformMatrix.scale(scale_x, scale_y))
            .compose(TransformMatrix.translation(cx, cy))
        )

        # Apply to each element
        for element in elements:
            if isinstance(element, Component):
                self.transform_component(element, transform)
            elif isinstance(element, Wire):
                self.transform_wire(element, transform)
            elif isinstance(element, Junction):
                self.transform_junction(element, transform)
            elif isinstance(element, Text):
                self.transform_text(element, transform)
            elif isinstance(element, Label):
                self.transform_label(element, transform)

    def translate_elements(self, elements: List[Any], dx: float, dy: float):
        """Translate elements by offset."""
        transform = TransformMatrix.translation(dx, dy)

        # Apply to each element
        for element in elements:
            if isinstance(element, Component):
                self.transform_component(element, transform)
            elif isinstance(element, Wire):
                self.transform_wire(element, transform)
            elif isinstance(element, Junction):
                self.transform_junction(element, transform)
            elif isinstance(element, Text):
                self.transform_text(element, transform)
            elif isinstance(element, Label):
                self.transform_label(element, transform)

    def align_elements(
        self,
        elements: List[Any],
        alignment: str = "left",
        spacing: Optional[float] = None,
    ):
        """Align elements horizontally or vertically."""
        if not elements:
            return

        # Calculate bounding boxes
        bboxes = []
        for element in elements:
            bbox = self.calculate_bounding_box([element])
            bboxes.append(bbox)

        # Determine alignment axis and direction
        if alignment in ["left", "right", "center_x"]:
            axis = "x"
        elif alignment in ["top", "bottom", "center_y"]:
            axis = "y"
        else:
            raise ValueError(f"Unknown alignment: {alignment}")

        # Calculate reference position
        if alignment == "left":
            ref_pos = min(bbox.min_x for bbox in bboxes)
        elif alignment == "right":
            ref_pos = max(bbox.max_x for bbox in bboxes)
        elif alignment == "center_x":
            ref_pos = sum(bbox.center[0] for bbox in bboxes) / len(bboxes)
        elif alignment == "top":
            ref_pos = min(bbox.min_y for bbox in bboxes)
        elif alignment == "bottom":
            ref_pos = max(bbox.max_y for bbox in bboxes)
        elif alignment == "center_y":
            ref_pos = sum(bbox.center[1] for bbox in bboxes) / len(bboxes)

        # Apply alignment
        for element, bbox in zip(elements, bboxes):
            if axis == "x":
                if alignment == "left":
                    dx = ref_pos - bbox.min_x
                elif alignment == "right":
                    dx = ref_pos - bbox.max_x
                else:  # center_x
                    dx = ref_pos - bbox.center[0]
                dy = 0
            else:  # axis == 'y'
                dx = 0
                if alignment == "top":
                    dy = ref_pos - bbox.min_y
                elif alignment == "bottom":
                    dy = ref_pos - bbox.max_y
                else:  # center_y
                    dy = ref_pos - bbox.center[1]

            self.translate_elements([element], dx, dy)

    def distribute_elements(
        self,
        elements: List[Any],
        direction: str = "horizontal",
        spacing: Optional[float] = None,
    ):
        """Distribute elements evenly."""
        if len(elements) < 2:
            return

        # Calculate bounding boxes
        bboxes = []
        for element in elements:
            bbox = self.calculate_bounding_box([element])
            bboxes.append(bbox)

        # Sort by position
        if direction == "horizontal":
            sorted_items = sorted(zip(elements, bboxes), key=lambda x: x[1].center[0])
        else:  # vertical
            sorted_items = sorted(zip(elements, bboxes), key=lambda x: x[1].center[1])

        elements = [item[0] for item in sorted_items]
        bboxes = [item[1] for item in sorted_items]

        # Calculate spacing
        if spacing is None:
            if direction == "horizontal":
                total_width = sum(bbox.width for bbox in bboxes)
                total_span = bboxes[-1].max_x - bboxes[0].min_x
                spacing = (total_span - total_width) / (len(elements) - 1)
            else:  # vertical
                total_height = sum(bbox.height for bbox in bboxes)
                total_span = bboxes[-1].max_y - bboxes[0].min_y
                spacing = (total_span - total_height) / (len(elements) - 1)

        # Apply distribution
        if direction == "horizontal":
            current_x = bboxes[0].min_x
            for element, bbox in zip(elements, bboxes):
                dx = current_x - bbox.min_x
                self.translate_elements([element], dx, 0)
                current_x += bbox.width + spacing
        else:  # vertical
            current_y = bboxes[0].min_y
            for element, bbox in zip(elements, bboxes):
                dy = current_y - bbox.min_y
                self.translate_elements([element], 0, dy)
                current_y += bbox.height + spacing

    def calculate_bounding_box(self, elements: List[Any]) -> BoundingBox:
        """Calculate bounding box for elements."""
        if not elements:
            return BoundingBox(0, 0, 0, 0)

        min_x = float("inf")
        min_y = float("inf")
        max_x = float("-inf")
        max_y = float("-inf")

        for element in elements:
            if isinstance(element, Component):
                # Component position - SchematicSymbol uses 'position' not 'at'
                min_x = min(min_x, element.position.x)
                min_y = min(min_y, element.position.y)
                max_x = max(max_x, element.position.x)
                max_y = max(max_y, element.position.y)

                # Include property positions if they exist as dicts
                if isinstance(element.properties, dict):
                    # Properties are a simple dict, not objects with 'at' attribute
                    pass

            elif isinstance(element, Wire):
                # Wire has a points list
                for point in element.points:
                    min_x = min(min_x, point.x)
                    min_y = min(min_y, point.y)
                    max_x = max(max_x, point.x)
                    max_y = max(max_y, point.y)

            elif hasattr(element, "at"):
                min_x = min(min_x, element.at.x)
                min_y = min(min_y, element.at.y)
                max_x = max(max_x, element.at.x)
                max_y = max(max_y, element.at.y)
            elif hasattr(element, "position"):
                min_x = min(min_x, element.position.x)
                min_y = min(min_y, element.position.y)
                max_x = max(max_x, element.position.x)
                max_y = max(max_y, element.position.y)

        # Add some margin for component bodies
        margin = 5.0  # 5mm margin
        return BoundingBox(
            min_x=min_x - margin,
            min_y=min_y - margin,
            max_x=max_x + margin,
            max_y=max_y + margin,
        )

    def auto_arrange(
        self,
        components: List[Component],
        grid_spacing: float = 25.4,  # 1 inch default
        max_columns: int = 5,
    ):
        """Auto-arrange components in a grid."""
        if not components:
            return

        # Sort components by reference for consistent ordering
        sorted_components = sorted(components, key=lambda c: c.reference)

        # Calculate grid positions
        col = 0
        row = 0
        start_x = 0
        start_y = 0

        for comp in sorted_components:
            # Calculate position
            x = start_x + col * grid_spacing
            y = start_y + row * grid_spacing

            # Move component - use position for SchematicSymbol
            dx = x - comp.position.x
            dy = y - comp.position.y
            self.translate_elements([comp], dx, dy)

            # Update grid position
            col += 1
            if col >= max_columns:
                col = 0
                row += 1
