"""
Improved courtyard-based collision detection for PCB component placement.

This module implements collision detection using actual courtyard geometry
from footprints, with proper handling of KiCad's inverted Y axis and
true polygon-polygon intersection testing.
"""

import logging
import math
from dataclasses import dataclass
from typing import List, Optional, Set, Tuple, Union

from ..types import Footprint, Line, Point, Rectangle

logger = logging.getLogger(__name__)


@dataclass
class Vector2D:
    """2D vector for geometric calculations."""

    x: float
    y: float

    def __sub__(self, other: "Vector2D") -> "Vector2D":
        return Vector2D(self.x - other.x, self.y - other.y)

    def dot(self, other: "Vector2D") -> float:
        return self.x * other.x + self.y * other.y

    def perp_dot(self, other: "Vector2D") -> float:
        """Perpendicular dot product (2D cross product)."""
        return self.x * other.y - self.y * other.x


@dataclass
class Polygon:
    """A 2D polygon represented by its vertices."""

    vertices: List[Tuple[float, float]]

    def __init__(self, vertices: List[Tuple[float, float]]):
        """Initialize polygon, ensuring vertices are in counter-clockwise order."""
        self.vertices = vertices
        # In KiCad, Y increases downward, so we need to adjust our CCW calculation
        if self._calculate_signed_area() > 0:  # Inverted for KiCad
            self.vertices = list(reversed(self.vertices))

    def _calculate_signed_area(self) -> float:
        """Calculate signed area of polygon (negative if CCW in KiCad coords)."""
        area = 0.0
        n = len(self.vertices)
        for i in range(n):
            j = (i + 1) % n
            area += self.vertices[i][0] * self.vertices[j][1]
            area -= self.vertices[j][0] * self.vertices[i][1]
        return area / 2.0

    def get_edges(self) -> List[Tuple[Vector2D, Vector2D]]:
        """Get all edges as pairs of vertices."""
        edges = []
        n = len(self.vertices)
        for i in range(n):
            j = (i + 1) % n
            v1 = Vector2D(self.vertices[i][0], self.vertices[i][1])
            v2 = Vector2D(self.vertices[j][0], self.vertices[j][1])
            edges.append((v1, v2))
        return edges

    def get_axes(self) -> List[Vector2D]:
        """Get all perpendicular axes for SAT collision detection."""
        axes = []
        edges = self.get_edges()
        for v1, v2 in edges:
            edge = v2 - v1
            # Perpendicular vector (rotated 90 degrees)
            # In KiCad coords, this needs to account for inverted Y
            normal = Vector2D(-edge.y, edge.x)
            # Normalize
            length = math.sqrt(normal.x * normal.x + normal.y * normal.y)
            if length > 0:
                normal.x /= length
                normal.y /= length
                axes.append(normal)
        return axes

    def project_onto_axis(self, axis: Vector2D) -> Tuple[float, float]:
        """Project polygon onto axis and return min/max values."""
        vertices_2d = [Vector2D(v[0], v[1]) for v in self.vertices]
        projections = [v.dot(axis) for v in vertices_2d]
        return min(projections), max(projections)

    def contains_point(self, x: float, y: float) -> bool:
        """Check if a point is inside the polygon using ray casting algorithm."""
        n = len(self.vertices)
        inside = False

        p1x, p1y = self.vertices[0]
        for i in range(1, n + 1):
            p2x, p2y = self.vertices[i % n]
            # Adjusted for KiCad's inverted Y axis
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y

        return inside

    def get_bounding_box(self) -> Tuple[float, float, float, float]:
        """Get axis-aligned bounding box as (min_x, min_y, max_x, max_y)."""
        if not self.vertices:
            return 0, 0, 0, 0

        xs = [v[0] for v in self.vertices]
        ys = [v[1] for v in self.vertices]
        return min(xs), min(ys), max(xs), max(ys)

    def transform(self, dx: float, dy: float, angle_deg: float = 0) -> "Polygon":
        """Create a transformed copy of the polygon."""
        angle_rad = math.radians(angle_deg)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)

        new_vertices = []
        for x, y in self.vertices:
            # Rotate (accounting for KiCad's inverted Y)
            rx = x * cos_a - y * sin_a
            ry = x * sin_a + y * cos_a
            # Translate
            new_vertices.append((rx + dx, ry + dy))

        return Polygon(new_vertices)

    def intersects(self, other: "Polygon") -> bool:
        """
        Check if this polygon intersects with another using SAT.

        Separating Axis Theorem (SAT): Two convex polygons don't intersect
        if there exists an axis where their projections don't overlap.
        """
        # Check all axes from both polygons
        all_axes = self.get_axes() + other.get_axes()

        for axis in all_axes:
            # Project both polygons onto this axis
            min1, max1 = self.project_onto_axis(axis)
            min2, max2 = other.project_onto_axis(axis)

            # Check for separation
            if max1 < min2 or max2 < min1:
                # Found a separating axis, polygons don't intersect
                return False

        # No separating axis found, polygons intersect
        return True

    def expand(self, distance: float) -> "Polygon":
        """Expand polygon outward by given distance (for spacing)."""
        if len(self.vertices) < 3:
            return self

        # Calculate offset vertices
        new_vertices = []
        n = len(self.vertices)

        for i in range(n):
            # Get three consecutive vertices
            prev_idx = (i - 1) % n
            curr_idx = i
            next_idx = (i + 1) % n

            p0 = Vector2D(self.vertices[prev_idx][0], self.vertices[prev_idx][1])
            p1 = Vector2D(self.vertices[curr_idx][0], self.vertices[curr_idx][1])
            p2 = Vector2D(self.vertices[next_idx][0], self.vertices[next_idx][1])

            # Calculate edge vectors
            v1 = p1 - p0
            v2 = p2 - p1

            # Normalize
            len1 = math.sqrt(v1.x * v1.x + v1.y * v1.y)
            len2 = math.sqrt(v2.x * v2.x + v2.y * v2.y)

            if len1 > 0:
                v1.x /= len1
                v1.y /= len1
            if len2 > 0:
                v2.x /= len2
                v2.y /= len2

            # Calculate normals (perpendicular, pointing outward)
            # For KiCad's inverted Y, we adjust the perpendicular calculation
            n1 = Vector2D(-v1.y, v1.x)
            n2 = Vector2D(-v2.y, v2.x)

            # Average normal direction
            avg_normal = Vector2D((n1.x + n2.x) / 2, (n1.y + n2.y) / 2)

            # Normalize average
            avg_len = math.sqrt(
                avg_normal.x * avg_normal.x + avg_normal.y * avg_normal.y
            )
            if avg_len > 0:
                avg_normal.x /= avg_len
                avg_normal.y /= avg_len

            # Offset vertex
            new_x = p1.x + avg_normal.x * distance
            new_y = p1.y + avg_normal.y * distance
            new_vertices.append((new_x, new_y))

        return Polygon(new_vertices)


class CourtyardCollisionDetector:
    """
    Improved collision detector with proper polygon-polygon intersection testing.

    Features:
    - True polygon-polygon intersection using SAT
    - Proper handling of KiCad's inverted Y axis
    - Support for expanded polygons (spacing)
    - Efficient broad-phase collision detection using bounding boxes
    """

    def __init__(self, spacing: float = 0.0):
        """
        Initialize collision detector.

        Args:
            spacing: Minimum spacing between components (mm)
        """
        self.spacing = spacing
        self._polygon_cache = {}  # Cache transformed polygons

    def detect_collisions(
        self, footprints: List[Footprint]
    ) -> List[Tuple[Footprint, Footprint]]:
        """
        Detect all collisions between footprints.

        Returns:
            List of (footprint1, footprint2) tuples that are colliding
        """
        collisions = []
        n = len(footprints)

        # Clear cache for new detection run
        self._polygon_cache.clear()

        # Check all pairs
        for i in range(n):
            for j in range(i + 1, n):
                fp1 = footprints[i]
                fp2 = footprints[j]

                # Broad phase: Check bounding boxes first
                if self._bounding_boxes_overlap(fp1, fp2):
                    # Narrow phase: Check actual polygons
                    if self.check_collision(fp1, fp2):
                        collisions.append((fp1, fp2))
                        logger.debug(
                            f"Collision detected: {fp1.reference} <-> {fp2.reference}"
                        )

        return collisions

    def _bounding_boxes_overlap(self, fp1: Footprint, fp2: Footprint) -> bool:
        """Quick bounding box overlap check for broad phase."""
        poly1 = self._get_cached_polygon(fp1)
        poly2 = self._get_cached_polygon(fp2)

        bbox1 = poly1.get_bounding_box()
        bbox2 = poly2.get_bounding_box()

        # Check if bounding boxes overlap
        return not (
            bbox1[2] < bbox2[0]  # box1 right < box2 left
            or bbox2[2] < bbox1[0]  # box2 right < box1 left
            or bbox1[3] < bbox2[1]  # box1 bottom < box2 top (KiCad Y)
            or bbox2[3] < bbox1[1]
        )  # box2 bottom < box1 top (KiCad Y)

    def check_collision(self, fp1: Footprint, fp2: Footprint) -> bool:
        """
        Check if two footprints collide using polygon intersection.

        Args:
            fp1: First footprint
            fp2: Second footprint

        Returns:
            True if footprints collide
        """
        poly1 = self._get_cached_polygon(fp1)
        poly2 = self._get_cached_polygon(fp2)

        # Expand polygons by spacing if needed
        if self.spacing > 0:
            poly1 = poly1.expand(self.spacing / 2)
            poly2 = poly2.expand(self.spacing / 2)

        return poly1.intersects(poly2)

    def _get_cached_polygon(self, footprint: Footprint) -> Polygon:
        """Get polygon for footprint, using cache if available."""
        cache_key = (
            footprint.reference,
            footprint.position.x,
            footprint.position.y,
            footprint.rotation,
        )

        if cache_key in self._polygon_cache:
            return self._polygon_cache[cache_key]

        # Get base polygon
        base_poly = self.get_footprint_polygon(footprint)

        # Cache and return
        self._polygon_cache[cache_key] = base_poly
        return base_poly

    def get_courtyard_polygon(self, footprint: Footprint) -> Optional[Polygon]:
        """Extract courtyard polygon from footprint graphics."""
        courtyard_lines = []
        courtyard_rects = []

        # Look for courtyard lines
        for line in footprint.lines:
            if hasattr(line, "layer") and line.layer in ["F.CrtYd", "B.CrtYd"]:
                courtyard_lines.append(line)

        # Look for courtyard rectangles
        for rect in footprint.rectangles:
            if hasattr(rect, "layer") and rect.layer in ["F.CrtYd", "B.CrtYd"]:
                courtyard_rects.append(rect)

        # Try to build polygon from rectangles first
        if courtyard_rects:
            rect = courtyard_rects[0]  # Use first rectangle
            vertices = [
                (rect.start.x, rect.start.y),
                (rect.end.x, rect.start.y),
                (rect.end.x, rect.end.y),
                (rect.start.x, rect.end.y),
            ]
            return Polygon(vertices)

        # Try to build polygon from connected lines
        if courtyard_lines:
            vertices = self._trace_polygon_from_lines(courtyard_lines)
            if vertices:
                return Polygon(vertices)

        return None

    def _trace_polygon_from_lines(
        self, lines: List[Line]
    ) -> Optional[List[Tuple[float, float]]]:
        """Trace a closed polygon from a list of line segments."""
        if not lines:
            return None

        # Build adjacency list of line endpoints
        from collections import defaultdict

        connections = defaultdict(list)

        for line in lines:
            start = (line.start.x, line.start.y)
            end = (line.end.x, line.end.y)
            connections[start].append(end)
            connections[end].append(start)

        # Check if all vertices have exactly 2 connections (closed polygon)
        for vertex, neighbors in connections.items():
            if len(neighbors) != 2:
                return None  # Not a closed polygon

        # Trace the polygon starting from any vertex
        vertices = []
        start_vertex = next(iter(connections))
        current = start_vertex
        prev = None

        while True:
            vertices.append(current)

            # Find next vertex (not the one we came from)
            neighbors = connections[current]
            next_vertex = neighbors[0] if neighbors[0] != prev else neighbors[1]

            if next_vertex == start_vertex:
                # We've completed the loop
                break

            prev = current
            current = next_vertex

            if len(vertices) > len(lines):
                # Something went wrong, avoid infinite loop
                return None

        return vertices

    def get_footprint_polygon(
        self, footprint: Footprint, use_courtyard: bool = True
    ) -> Polygon:
        """
        Get polygon representation of footprint.

        Args:
            footprint: The footprint to get polygon for
            use_courtyard: If True, use courtyard if available, otherwise use bounding box

        Returns:
            Polygon representing the footprint outline
        """
        # Try to get courtyard polygon if requested
        if use_courtyard:
            courtyard = self.get_courtyard_polygon(footprint)
            if courtyard:
                # Transform courtyard to footprint position and rotation
                return courtyard.transform(
                    footprint.position.x, footprint.position.y, footprint.rotation
                )
            else:
                logger.debug(
                    f"No courtyard found for {footprint.reference}, using bounding box"
                )

        # Fall back to bounding box from pads and graphics
        min_x, min_y, max_x, max_y = self._calculate_footprint_bbox(footprint)

        # Add margin for components without courtyards
        margin = 0.5  # mm
        min_x -= margin
        min_y -= margin
        max_x += margin
        max_y += margin

        logger.debug(
            f"Bbox for {footprint.reference}: ({min_x:.2f}, {min_y:.2f}) to ({max_x:.2f}, {max_y:.2f})"
        )

        # Create rectangle polygon
        vertices = [(min_x, min_y), (max_x, min_y), (max_x, max_y), (min_x, max_y)]

        # Transform to footprint position and rotation
        polygon = Polygon(vertices)
        return polygon.transform(
            footprint.position.x, footprint.position.y, footprint.rotation
        )

    def _calculate_footprint_bbox(
        self, footprint: Footprint
    ) -> Tuple[float, float, float, float]:
        """Calculate bounding box from footprint elements."""
        points = []

        # Add pad corners
        for pad in footprint.pads:
            half_width = pad.size[0] / 2
            half_height = pad.size[1] / 2

            # Pad corners in local coordinates
            corners = [
                (pad.position.x - half_width, pad.position.y - half_height),
                (pad.position.x + half_width, pad.position.y - half_height),
                (pad.position.x + half_width, pad.position.y + half_height),
                (pad.position.x - half_width, pad.position.y + half_height),
            ]

            # Rotate corners if pad has rotation
            if hasattr(pad, "rotation") and pad.rotation != 0:
                angle_rad = math.radians(pad.rotation)
                cos_a = math.cos(angle_rad)
                sin_a = math.sin(angle_rad)

                rotated_corners = []
                for x, y in corners:
                    rx = x * cos_a - y * sin_a
                    ry = x * sin_a + y * cos_a
                    rotated_corners.append((rx, ry))
                corners = rotated_corners

            points.extend(corners)

        # Add graphics bounds from lines
        for line in footprint.lines:
            if hasattr(line, "layer") and "SilkS" in line.layer:
                points.append((line.start.x, line.start.y))
                points.append((line.end.x, line.end.y))

        # Add graphics bounds from rectangles
        for rect in footprint.rectangles:
            if hasattr(rect, "layer") and "SilkS" in rect.layer:
                points.append((rect.start.x, rect.start.y))
                points.append((rect.end.x, rect.end.y))

        if not points:
            # No elements found, use a default size
            return -1, -1, 1, 1

        xs = [p[0] for p in points]
        ys = [p[1] for p in points]

        return min(xs), min(ys), max(xs), max(ys)

    def get_collision_vector(
        self, fp1: Footprint, fp2: Footprint
    ) -> Optional[Tuple[float, float]]:
        """
        Get vector to resolve collision between two footprints.

        Returns:
            (dx, dy) vector to move fp1 to resolve collision, or None if no collision
        """
        if not self.check_collision(fp1, fp2):
            return None

        # Get polygon centers
        poly1 = self._get_cached_polygon(fp1)
        poly2 = self._get_cached_polygon(fp2)

        bbox1 = poly1.get_bounding_box()
        bbox2 = poly2.get_bounding_box()

        center1_x = (bbox1[0] + bbox1[2]) / 2
        center1_y = (bbox1[1] + bbox1[3]) / 2
        center2_x = (bbox2[0] + bbox2[2]) / 2
        center2_y = (bbox2[1] + bbox2[3]) / 2

        # Calculate separation vector
        dx = center1_x - center2_x
        dy = center1_y - center2_y
        distance = math.sqrt(dx * dx + dy * dy)

        if distance < 0.1:
            # Components are on top of each other
            import random

            angle = random.uniform(0, 2 * math.pi)
            dx = math.cos(angle)
            dy = math.sin(angle)
            distance = 1.0

        # Normalize
        dx /= distance
        dy /= distance

        # Calculate required separation distance
        # This is a simplified approach - for exact separation we'd need
        # to use the SAT projection overlap amount
        size1 = math.sqrt((bbox1[2] - bbox1[0]) * (bbox1[3] - bbox1[1]))
        size2 = math.sqrt((bbox2[2] - bbox2[0]) * (bbox2[3] - bbox2[1]))
        required_distance = (size1 + size2) / 2 + self.spacing

        # Calculate movement needed
        move_distance = required_distance - distance

        return (dx * move_distance / 2, dy * move_distance / 2)
