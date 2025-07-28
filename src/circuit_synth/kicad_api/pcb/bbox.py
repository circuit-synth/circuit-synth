"""
Bounding box utilities for PCB component placement.
"""

from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class BoundingBox:
    """Represents a 2D bounding box."""

    min_x: float
    min_y: float
    max_x: float
    max_y: float

    def area(self) -> float:
        """Calculate the area of the bounding box."""
        return (self.max_x - self.min_x) * (self.max_y - self.min_y)

    def center(self) -> Tuple[float, float]:
        """Get the center point of the bounding box."""
        return ((self.min_x + self.max_x) / 2, (self.min_y + self.max_y) / 2)

    def intersects(self, other: "BoundingBox") -> bool:
        """Check if this bounding box intersects with another."""
        return not (
            self.max_x < other.min_x
            or self.min_x > other.max_x
            or self.max_y < other.min_y
            or self.min_y > other.max_y
        )

    def inflate(self, amount: float) -> "BoundingBox":
        """Return a new bounding box inflated by the given amount on all sides."""
        return BoundingBox(
            self.min_x - amount,
            self.min_y - amount,
            self.max_x + amount,
            self.max_y + amount,
        )

    def merge(self, other: "BoundingBox") -> "BoundingBox":
        """Return a new bounding box that encompasses both this and the other bbox."""
        return BoundingBox(
            min(self.min_x, other.min_x),
            min(self.min_y, other.min_y),
            max(self.max_x, other.max_x),
            max(self.max_y, other.max_y),
        )

    def top_left(self) -> Tuple[float, float]:
        """Get the top-left corner coordinates."""
        return (self.min_x, self.max_y)

    def bottom_right(self) -> Tuple[float, float]:
        """Get the bottom-right corner coordinates."""
        return (self.max_x, self.min_y)

    def bottom_left(self) -> Tuple[float, float]:
        """Get the bottom-left corner coordinates."""
        return (self.min_x, self.min_y)

    def width(self) -> float:
        """Get the width of the bounding box."""
        return self.max_x - self.min_x

    def height(self) -> float:
        """Get the height of the bounding box."""
        return self.max_y - self.min_y

    @classmethod
    def from_points(cls, points: list[Tuple[float, float]]) -> Optional["BoundingBox"]:
        """Create a bounding box from a list of points."""
        if not points:
            return None

        xs = [p[0] for p in points]
        ys = [p[1] for p in points]

        return cls(min(xs), min(ys), max(xs), max(ys))
