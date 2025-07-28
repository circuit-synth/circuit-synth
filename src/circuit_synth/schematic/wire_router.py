"""
Wire routing algorithms for KiCad schematics.

This module provides various wire routing algorithms for creating
aesthetically pleasing and electrically correct wire connections.
"""

import logging
import math
from dataclasses import dataclass
from typing import List, Optional, Set, Tuple

from ..core.types import Point

logger = logging.getLogger(__name__)


@dataclass
class RoutingConstraints:
    """Constraints for wire routing."""

    grid_size: float = 2.54  # Standard KiCad grid in mm
    min_segment_length: float = 2.54
    prefer_horizontal: bool = True
    avoid_diagonal: bool = True
    max_segments: int = 5


class WireRouter:
    """
    Wire routing engine for schematic connections.

    Provides various routing algorithms:
    - Direct (straight line)
    - Manhattan (horizontal/vertical only)
    - Diagonal (45-degree angles)
    - Smart (obstacle-aware)
    """

    def __init__(self, constraints: Optional[RoutingConstraints] = None):
        """
        Initialize the wire router.

        Args:
            constraints: Routing constraints to use
        """
        self.constraints = constraints or RoutingConstraints()

    def route_direct(
        self, start: Tuple[float, float], end: Tuple[float, float]
    ) -> List[Point]:
        """
        Route a direct connection between two points.

        Args:
            start: Starting point (x, y)
            end: Ending point (x, y)

        Returns:
            List of points defining the wire path
        """
        return [Point(start[0], start[1]), Point(end[0], end[1])]

    def route_manhattan(
        self, start: Tuple[float, float], end: Tuple[float, float]
    ) -> List[Point]:
        """
        Route using Manhattan (L-shaped) routing.

        Args:
            start: Starting point (x, y)
            end: Ending point (x, y)

        Returns:
            List of points defining the wire path
        """
        points = [Point(start[0], start[1])]

        dx = end[0] - start[0]
        dy = end[1] - start[1]

        # Snap to grid
        start_x = self._snap_to_grid(start[0])
        start_y = self._snap_to_grid(start[1])
        end_x = self._snap_to_grid(end[0])
        end_y = self._snap_to_grid(end[1])

        # If already aligned, use direct connection
        if abs(dx) < 0.01 or abs(dy) < 0.01:
            points.append(Point(end_x, end_y))
            return points

        # Determine routing preference
        if self.constraints.prefer_horizontal:
            # Horizontal first
            points.append(Point(end_x, start_y))
        else:
            # Vertical first
            points.append(Point(start_x, end_y))

        points.append(Point(end_x, end_y))

        return points

    def route_diagonal(
        self, start: Tuple[float, float], end: Tuple[float, float]
    ) -> List[Point]:
        """
        Route using 45-degree diagonal segments where appropriate.

        Args:
            start: Starting point (x, y)
            end: Ending point (x, y)

        Returns:
            List of points defining the wire path
        """
        points = [Point(start[0], start[1])]

        dx = end[0] - start[0]
        dy = end[1] - start[1]

        # If Manhattan distance is small, use direct
        if abs(dx) + abs(dy) < self.constraints.min_segment_length * 2:
            points.append(Point(end[0], end[1]))
            return points

        # Calculate 45-degree segments
        diagonal_length = min(abs(dx), abs(dy))

        if diagonal_length > self.constraints.min_segment_length:
            # Add diagonal segment
            diag_x = start[0] + (diagonal_length * (1 if dx > 0 else -1))
            diag_y = start[1] + (diagonal_length * (1 if dy > 0 else -1))
            points.append(Point(self._snap_to_grid(diag_x), self._snap_to_grid(diag_y)))

        # Complete with straight segment
        points.append(Point(end[0], end[1]))

        return points

    def route_smart(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        obstacles: Optional[List[Tuple[float, float, float, float]]] = None,
    ) -> List[Point]:
        """
        Route using obstacle-aware pathfinding.

        This is a simplified version that tries to avoid obstacles
        by routing around them.

        Args:
            start: Starting point (x, y)
            end: Ending point (x, y)
            obstacles: List of obstacle rectangles (x1, y1, x2, y2)

        Returns:
            List of points defining the wire path
        """
        if not obstacles:
            # No obstacles, use Manhattan routing
            return self.route_manhattan(start, end)

        # For now, implement a simple version that tries alternate paths
        # A full implementation would use A* or similar pathfinding

        # Try direct path first
        if not self._path_intersects_obstacles(start, end, obstacles):
            return self.route_direct(start, end)

        # Try L-shaped paths
        # Horizontal first
        mid_point1 = (end[0], start[1])
        if not self._path_intersects_obstacles(
            start, mid_point1, obstacles
        ) and not self._path_intersects_obstacles(mid_point1, end, obstacles):
            return [
                Point(start[0], start[1]),
                Point(mid_point1[0], mid_point1[1]),
                Point(end[0], end[1]),
            ]

        # Vertical first
        mid_point2 = (start[0], end[1])
        if not self._path_intersects_obstacles(
            start, mid_point2, obstacles
        ) and not self._path_intersects_obstacles(mid_point2, end, obstacles):
            return [
                Point(start[0], start[1]),
                Point(mid_point2[0], mid_point2[1]),
                Point(end[0], end[1]),
            ]

        # If simple paths don't work, fall back to Manhattan
        # (In a full implementation, we'd try more complex paths)
        return self.route_manhattan(start, end)

    def route_bus(
        self,
        connections: List[Tuple[Tuple[float, float], Tuple[float, float]]],
        spacing: float = 2.54,
    ) -> List[List[Point]]:
        """
        Route multiple parallel wires as a bus.

        Args:
            connections: List of (start, end) point pairs
            spacing: Spacing between parallel wires

        Returns:
            List of wire paths
        """
        if not connections:
            return []

        paths = []

        # Find common routing direction
        # For simplicity, assume all connections go in roughly the same direction
        avg_dx = sum(c[1][0] - c[0][0] for c in connections) / len(connections)
        avg_dy = sum(c[1][1] - c[0][1] for c in connections) / len(connections)

        # Determine if routing should be primarily horizontal or vertical
        horizontal = abs(avg_dx) > abs(avg_dy)

        # Sort connections by their perpendicular coordinate
        if horizontal:
            sorted_connections = sorted(connections, key=lambda c: c[0][1])
        else:
            sorted_connections = sorted(connections, key=lambda c: c[0][0])

        # Route each connection with appropriate offset
        for i, (start, end) in enumerate(sorted_connections):
            offset = i * spacing

            if horizontal:
                # Offset vertically
                adjusted_start = (start[0], start[1] + offset)
                adjusted_end = (end[0], end[1] + offset)
            else:
                # Offset horizontally
                adjusted_start = (start[0] + offset, start[1])
                adjusted_end = (end[0] + offset, end[1])

            path = self.route_manhattan(adjusted_start, adjusted_end)
            paths.append(path)

        return paths

    def _snap_to_grid(self, value: float) -> float:
        """Snap a coordinate value to the grid."""
        return round(value / self.constraints.grid_size) * self.constraints.grid_size

    def _path_intersects_obstacles(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        obstacles: List[Tuple[float, float, float, float]],
    ) -> bool:
        """
        Check if a line segment intersects any obstacles.

        Args:
            start: Start point of line segment
            end: End point of line segment
            obstacles: List of obstacle rectangles (x1, y1, x2, y2)

        Returns:
            True if path intersects any obstacle
        """
        for obs in obstacles:
            if self._line_intersects_rect(start, end, obs):
                return True
        return False

    def _line_intersects_rect(
        self,
        p1: Tuple[float, float],
        p2: Tuple[float, float],
        rect: Tuple[float, float, float, float],
    ) -> bool:
        """
        Check if a line segment intersects a rectangle.

        This is a simplified check that works for axis-aligned rectangles.
        """
        x1, y1, x2, y2 = rect

        # Check if line is completely outside rectangle bounds
        if (
            max(p1[0], p2[0]) < x1
            or min(p1[0], p2[0]) > x2
            or max(p1[1], p2[1]) < y1
            or min(p1[1], p2[1]) > y2
        ):
            return False

        # Check if either endpoint is inside rectangle
        if x1 <= p1[0] <= x2 and y1 <= p1[1] <= y2:
            return True
        if x1 <= p2[0] <= x2 and y1 <= p2[1] <= y2:
            return True

        # For a more complete check, we'd need to test line-rectangle intersection
        # This simplified version is sufficient for basic routing
        return False

    def optimize_path(self, points: List[Point]) -> List[Point]:
        """
        Optimize a wire path by removing unnecessary points.

        Args:
            points: Original path points

        Returns:
            Optimized path with redundant points removed
        """
        if len(points) <= 2:
            return points

        optimized = [points[0]]

        for i in range(1, len(points) - 1):
            prev = optimized[-1]
            curr = points[i]
            next_pt = points[i + 1]

            # Check if current point is on the line between prev and next
            if not self._point_on_line(curr, prev, next_pt):
                optimized.append(curr)

        optimized.append(points[-1])

        return optimized

    def _point_on_line(
        self, point: Point, line_start: Point, line_end: Point, tolerance: float = 0.01
    ) -> bool:
        """Check if a point lies on a line segment."""
        # Calculate cross product
        cross = (point.y - line_start.y) * (line_end.x - line_start.x) - (
            point.x - line_start.x
        ) * (line_end.y - line_start.y)

        if abs(cross) > tolerance:
            return False

        # Check if point is within line segment bounds
        dot = (point.x - line_start.x) * (line_end.x - line_start.x) + (
            point.y - line_start.y
        ) * (line_end.y - line_start.y)

        squared_length = (line_end.x - line_start.x) ** 2 + (
            line_end.y - line_start.y
        ) ** 2

        if squared_length == 0:
            return (
                math.sqrt((point.x - line_start.x) ** 2 + (point.y - line_start.y) ** 2)
                <= tolerance
            )

        param = dot / squared_length
        return 0 <= param <= 1
