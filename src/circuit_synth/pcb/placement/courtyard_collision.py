"""
Courtyard-based collision detection for PCB component placement.

This module implements collision detection using actual courtyard geometry
from footprints, supporting both rectangular and polygonal courtyards.
"""

import logging
import math
from dataclasses import dataclass
from typing import List, Optional, Tuple, Union

from ..types import Footprint, Line, Point, Rectangle

logger = logging.getLogger(__name__)


@dataclass
class Polygon:
    """A 2D polygon represented by its vertices."""

    vertices: List[Tuple[float, float]]

    def __init__(self, vertices: List[Tuple[float, float]]):
        """Initialize polygon, ensuring vertices are in counter-clockwise order."""
        self.vertices = vertices
        # Ensure counter-clockwise order
        if self._calculate_signed_area() < 0:
            self.vertices = list(reversed(self.vertices))

    def _calculate_signed_area(self) -> float:
        """Calculate signed area of polygon (positive if CCW, negative if CW)."""
        area = 0.0
        n = len(self.vertices)
        for i in range(n):
            j = (i + 1) % n
            area += self.vertices[i][0] * self.vertices[j][1]
            area -= self.vertices[j][0] * self.vertices[i][1]
        return area / 2.0

    def contains_point(self, x: float, y: float) -> bool:
        """Check if a point is inside the polygon using ray casting algorithm."""
        n = len(self.vertices)
        inside = False

        p1x, p1y = self.vertices[0]
        for i in range(1, n + 1):
            p2x, p2y = self.vertices[i % n]
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
            # Rotate
            rx = x * cos_a - y * sin_a
            ry = x * sin_a + y * cos_a
            # Translate
            new_vertices.append((rx + dx, ry + dy))

        return Polygon(new_vertices)


class CourtyardCollisionDetector:
    """
    Collision detector that uses actual courtyard geometry from footprints.

    Supports:
    - Rectangular courtyards (from fp_rect elements)
    - Polygonal courtyards (from connected fp_line segments)
    - Rotation of footprints
    - Configurable spacing between courtyards
    """

    def __init__(self, spacing: float = 0.0):
        """
        Initialize collision detector.

        Args:
            spacing: Additional spacing to add between courtyards (mm)
        """
        self.spacing = spacing

    def get_courtyard_polygon(self, footprint: Footprint) -> Optional[Polygon]:
        """
        Extract courtyard polygon from footprint.

        Returns the courtyard as a polygon, or None if no courtyard found.
        Enhanced to handle more courtyard shapes and types.
        """
        # First, check for courtyard rectangles
        courtyard_rects = [
            rect
            for rect in footprint.rectangles
            if rect.layer in ["F.CrtYd", "B.CrtYd"]
        ]

        if courtyard_rects:
            # If multiple rectangles, use the one with the largest area
            best_rect = max(
                courtyard_rects,
                key=lambda r: abs((r.end.x - r.start.x) * (r.end.y - r.start.y)),
            )

            # Convert rectangle to polygon vertices (ensure correct winding)
            vertices = [
                (best_rect.start.x, best_rect.start.y),
                (best_rect.end.x, best_rect.start.y),
                (best_rect.end.x, best_rect.end.y),
                (best_rect.start.x, best_rect.end.y),
            ]
            return Polygon(vertices)

        # Check for courtyard circles (if circle support exists in footprint type)
        if hasattr(footprint, "circles"):
            courtyard_circles = [
                circle
                for circle in footprint.circles
                if circle.layer in ["F.CrtYd", "B.CrtYd"]
            ]

            if courtyard_circles:
                # Convert largest circle to polygon approximation
                circle = max(courtyard_circles, key=lambda c: c.radius)
                vertices = self._circle_to_polygon(
                    circle.center.x, circle.center.y, circle.radius
                )
                return Polygon(vertices)

        # Check for courtyard arcs (if arc support exists)
        if hasattr(footprint, "arcs"):
            courtyard_arcs = [
                arc for arc in footprint.arcs if arc.layer in ["F.CrtYd", "B.CrtYd"]
            ]

            if courtyard_arcs:
                # Try to combine arcs into a polygon
                arc_vertices = self._arcs_to_polygon(courtyard_arcs)
                if arc_vertices and len(arc_vertices) >= 3:
                    return Polygon(arc_vertices)

        # Next, check for courtyard lines
        courtyard_lines = [
            line for line in footprint.lines if line.layer in ["F.CrtYd", "B.CrtYd"]
        ]

        if courtyard_lines:
            # Try to build a polygon from connected lines
            polygon_vertices = self._lines_to_polygon(courtyard_lines)
            if polygon_vertices and len(polygon_vertices) >= 3:
                return Polygon(polygon_vertices)

        # No courtyard found - this should not happen in modern footprints
        logger.error(
            f"No courtyard layer found for footprint {footprint.reference} ({footprint.name})"
        )
        raise ValueError(
            f"Footprint {footprint.reference} ({footprint.name}) is missing required courtyard layer (F.CrtYd or B.CrtYd). All footprints must have courtyards for proper placement."
        )

    def _lines_to_polygon(
        self, lines: List[Line]
    ) -> Optional[List[Tuple[float, float]]]:
        """
        Convert a list of lines into a polygon by connecting endpoints.

        Returns None if lines don't form a closed polygon.
        """
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

    def _circle_to_polygon(
        self, center_x: float, center_y: float, radius: float, segments: int = 32
    ) -> List[Tuple[float, float]]:
        """
        Convert a circle to a polygon approximation.

        Args:
            center_x, center_y: Circle center coordinates
            radius: Circle radius
            segments: Number of line segments to approximate the circle

        Returns:
            List of (x, y) vertices forming the polygon
        """
        vertices = []
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            vertices.append((x, y))
        return vertices

    def _arcs_to_polygon(self, arcs) -> Optional[List[Tuple[float, float]]]:
        """
        Convert a list of arcs into a polygon by approximating each arc with line segments.

        Args:
            arcs: List of arc objects

        Returns:
            List of (x, y) vertices forming the polygon, or None if arcs don't form a closed shape
        """
        # This is a simplified implementation - proper arc handling would need
        # to consider arc parameters like start/end angles, direction, etc.
        # For now, we'll just return the arc endpoints
        vertices = []
        for arc in arcs:
            if hasattr(arc, "start") and hasattr(arc, "end"):
                vertices.append((arc.start.x, arc.start.y))
                vertices.append((arc.end.x, arc.end.y))

        # Try to connect the endpoints into a closed polygon
        if len(vertices) >= 6:  # Need at least 3 complete points
            # Remove duplicates and return unique vertices
            unique_vertices = []
            for vertex in vertices:
                if vertex not in unique_vertices:
                    unique_vertices.append(vertex)
            return unique_vertices if len(unique_vertices) >= 3 else None

        return None

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
        # Always require courtyard for modern PCB design
        if use_courtyard:
            courtyard = self.get_courtyard_polygon(footprint)
            # Transform courtyard to footprint position and rotation
            return courtyard.transform(
                footprint.position.x, footprint.position.y, footprint.rotation
            )
        else:
            # Legacy mode: fall back to bounding box from pads and graphics
            min_x, min_y, max_x, max_y = self._calculate_footprint_bbox(footprint)

            logger.debug(
                f"Calculated bbox for {footprint.reference}: ({min_x:.2f}, {min_y:.2f}) to ({max_x:.2f}, {max_y:.2f})"
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
            # (Note: individual pad rotation is not common but possible)
            points.extend(corners)

        # Add line endpoints
        for line in footprint.lines:
            points.append((line.start.x, line.start.y))
            points.append((line.end.x, line.end.y))

        # Add rectangle corners
        for rect in footprint.rectangles:
            points.extend(
                [
                    (rect.start.x, rect.start.y),
                    (rect.end.x, rect.start.y),
                    (rect.end.x, rect.end.y),
                    (rect.start.x, rect.end.y),
                ]
            )

        if not points:
            # Default small box if no elements
            return -1, -1, 1, 1

        xs = [p[0] for p in points]
        ys = [p[1] for p in points]

        return min(xs), min(ys), max(xs), max(ys)

    def check_collision(self, footprint1: Footprint, footprint2: Footprint) -> bool:
        """
        Check if two footprints collide.

        Uses courtyard polygons if available, otherwise falls back to bounding boxes.

        Args:
            footprint1: First footprint
            footprint2: Second footprint

        Returns:
            True if footprints collide (including spacing), False otherwise
        """
        # Get polygons for both footprints
        poly1 = self.get_footprint_polygon(footprint1)
        poly2 = self.get_footprint_polygon(footprint2)

        # Quick check using bounding boxes first
        bbox1 = poly1.get_bounding_box()
        bbox2 = poly2.get_bounding_box()

        logger.debug(
            f"Checking collision between {footprint1.reference} and {footprint2.reference}"
        )
        logger.debug(
            f"  {footprint1.reference} bbox: ({bbox1[0]:.2f}, {bbox1[1]:.2f}) to ({bbox1[2]:.2f}, {bbox1[3]:.2f})"
        )
        logger.debug(
            f"  {footprint2.reference} bbox: ({bbox2[0]:.2f}, {bbox2[1]:.2f}) to ({bbox2[2]:.2f}, {bbox2[3]:.2f})"
        )

        # Inflate bboxes by spacing
        half_spacing = self.spacing / 2
        bbox1_inflated = (
            bbox1[0] - half_spacing,
            bbox1[1] - half_spacing,
            bbox1[2] + half_spacing,
            bbox1[3] + half_spacing,
        )
        bbox2_inflated = (
            bbox2[0] - half_spacing,
            bbox2[1] - half_spacing,
            bbox2[2] + half_spacing,
            bbox2[3] + half_spacing,
        )

        # Check if bounding boxes overlap
        if not self._bboxes_overlap(bbox1_inflated, bbox2_inflated):
            return False  # No collision possible

        logger.debug(
            f"  Bounding boxes overlap! Checking polygon collision with spacing={self.spacing}mm"
        )

        # Perform proper polygon-polygon collision detection
        return self._polygons_intersect(poly1, poly2)

    def _bboxes_overlap(
        self,
        bbox1: Tuple[float, float, float, float],
        bbox2: Tuple[float, float, float, float],
    ) -> bool:
        """Check if two bounding boxes overlap."""
        return not (
            bbox1[2] < bbox2[0]  # bbox1 right < bbox2 left
            or bbox2[2] < bbox1[0]  # bbox2 right < bbox1 left
            or bbox1[3] < bbox2[1]  # bbox1 top < bbox2 bottom
            or bbox2[3] < bbox1[1]
        )  # bbox2 top < bbox1 bottom

    def check_collision_with_placed(
        self, footprint: Footprint, placed_footprints: List[Footprint]
    ) -> bool:
        """
        Check if a footprint collides with any already placed footprints.

        Args:
            footprint: Footprint to check
            placed_footprints: List of already placed footprints

        Returns:
            True if collision detected, False otherwise
        """
        for placed in placed_footprints:
            if self.check_collision(footprint, placed):
                return True
        return False

    def find_valid_position(
        self,
        footprint: Footprint,
        ideal_x: float,
        ideal_y: float,
        placed_footprints: List[Footprint],
        board_outline: Optional[Polygon] = None,
        search_radius: float = 50.0,
        search_step: float = 0.5,
    ) -> Optional[Tuple[float, float]]:
        """
        Find a valid position near the ideal position using spiral search.

        Args:
            footprint: Footprint to place
            ideal_x, ideal_y: Ideal position to place near
            placed_footprints: List of already placed footprints
            board_outline: Optional board outline polygon
            search_radius: Maximum search radius in mm
            search_step: Step size for spiral search in mm

        Returns:
            (x, y) tuple if valid position found, None otherwise
        """
        # Store original position
        original_pos = footprint.position

        # Check ideal position first
        footprint.position = Point(ideal_x, ideal_y)
        if not self.check_collision_with_placed(footprint, placed_footprints):
            if board_outline is None or self._is_inside_board(footprint, board_outline):
                return ideal_x, ideal_y

        # Spiral search
        angle = 0.0
        radius = 0.0
        angle_step = math.pi / 8  # 22.5 degrees

        while radius < search_radius:
            # Try current position
            x = ideal_x + radius * math.cos(angle)
            y = ideal_y + radius * math.sin(angle)

            footprint.position = Point(x, y)

            if not self.check_collision_with_placed(footprint, placed_footprints):
                if board_outline is None or self._is_inside_board(
                    footprint, board_outline
                ):
                    # Restore original position before returning
                    footprint.position = original_pos
                    return x, y

            # Update spiral
            angle += angle_step
            if angle >= 2 * math.pi:
                angle -= 2 * math.pi
                radius += search_step

        # Restore original position
        footprint.position = original_pos
        return None

    def _polygons_intersect(self, poly1: Polygon, poly2: Polygon) -> bool:
        """
        Check if two polygons intersect using Separating Axis Theorem (SAT).

        Two convex polygons intersect if there is no separating axis between them.
        For each edge of each polygon, we test if the projections of both polygons
        onto the perpendicular axis overlap.
        """
        # Inflate polygons by spacing if needed
        if self.spacing > 0:
            poly1 = self._inflate_polygon(poly1, self.spacing / 2)
            poly2 = self._inflate_polygon(poly2, self.spacing / 2)

        # Get all edge normals (perpendicular vectors) to test as separating axes
        axes = []

        # Add normals from poly1 edges
        for i in range(len(poly1.vertices)):
            j = (i + 1) % len(poly1.vertices)
            edge = (
                poly1.vertices[j][0] - poly1.vertices[i][0],
                poly1.vertices[j][1] - poly1.vertices[i][1],
            )
            # Perpendicular to edge (rotate 90 degrees)
            normal = (-edge[1], edge[0])
            # Normalize
            length = math.sqrt(normal[0] ** 2 + normal[1] ** 2)
            if length > 0:
                axes.append((normal[0] / length, normal[1] / length))

        # Add normals from poly2 edges
        for i in range(len(poly2.vertices)):
            j = (i + 1) % len(poly2.vertices)
            edge = (
                poly2.vertices[j][0] - poly2.vertices[i][0],
                poly2.vertices[j][1] - poly2.vertices[i][1],
            )
            # Perpendicular to edge (rotate 90 degrees)
            normal = (-edge[1], edge[0])
            # Normalize
            length = math.sqrt(normal[0] ** 2 + normal[1] ** 2)
            if length > 0:
                axes.append((normal[0] / length, normal[1] / length))

        # Test each axis
        for axis in axes:
            # Project both polygons onto this axis
            proj1 = self._project_polygon(poly1, axis)
            proj2 = self._project_polygon(poly2, axis)

            # Check if projections overlap
            if proj1[1] < proj2[0] or proj2[1] < proj1[0]:
                # Found separating axis - polygons don't intersect
                return False

        # No separating axis found - polygons intersect
        return True

    def _project_polygon(
        self, polygon: Polygon, axis: Tuple[float, float]
    ) -> Tuple[float, float]:
        """Project polygon onto axis and return (min, max) projection values."""
        projections = []
        for vertex in polygon.vertices:
            # Dot product of vertex with axis
            proj = vertex[0] * axis[0] + vertex[1] * axis[1]
            projections.append(proj)
        return (min(projections), max(projections))

    def _inflate_polygon(self, polygon: Polygon, distance: float) -> Polygon:
        """
        Inflate polygon outward by given distance.
        Simple implementation using vertex offset along averaged normals.
        """
        if distance <= 0:
            return polygon

        vertices = polygon.vertices
        n = len(vertices)
        if n < 3:
            return polygon

        new_vertices = []

        for i in range(n):
            # Get adjacent vertices
            prev_i = (i - 1) % n
            next_i = (i + 1) % n

            # Calculate edge vectors
            prev_edge = (
                vertices[i][0] - vertices[prev_i][0],
                vertices[i][1] - vertices[prev_i][1],
            )
            next_edge = (
                vertices[next_i][0] - vertices[i][0],
                vertices[next_i][1] - vertices[i][1],
            )

            # Calculate edge normals (outward)
            prev_normal = self._normalize_vector((-prev_edge[1], prev_edge[0]))
            next_normal = self._normalize_vector((-next_edge[1], next_edge[0]))

            # Average the normals
            avg_normal = (
                (prev_normal[0] + next_normal[0]) / 2,
                (prev_normal[1] + next_normal[1]) / 2,
            )
            avg_normal = self._normalize_vector(avg_normal)

            # Offset vertex
            new_x = vertices[i][0] + avg_normal[0] * distance
            new_y = vertices[i][1] + avg_normal[1] * distance
            new_vertices.append((new_x, new_y))

        return Polygon(new_vertices)

    def _normalize_vector(self, vector: Tuple[float, float]) -> Tuple[float, float]:
        """Normalize a 2D vector."""
        length = math.sqrt(vector[0] ** 2 + vector[1] ** 2)
        if length == 0:
            return (0, 0)
        return (vector[0] / length, vector[1] / length)

    def _is_inside_board(self, footprint: Footprint, board_outline: Polygon) -> bool:
        """Check if footprint is completely inside board outline."""
        # Get footprint polygon
        fp_poly = self.get_footprint_polygon(footprint)

        # Check if all vertices are inside board outline
        for vertex in fp_poly.vertices:
            if not board_outline.contains_point(vertex[0], vertex[1]):
                return False

        return True
