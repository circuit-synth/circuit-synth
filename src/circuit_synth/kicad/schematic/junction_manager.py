"""
Junction management for KiCad schematics.
Handles automatic junction detection and placement where wires meet.
"""

import logging
from collections import defaultdict
from typing import Dict, List, Set, Tuple

from ..core.types import Junction, Point, Schematic, Wire
from .connection_utils import get_wire_segments, points_equal, segment_intersection

logger = logging.getLogger(__name__)


class JunctionManager:
    """
    Manages wire junctions in the schematic.
    Automatically detects where junctions are needed and manages their lifecycle.
    """

    def __init__(self, schematic: Schematic):
        """
        Initialize junction manager with a schematic.

        Args:
            schematic: The schematic to manage
        """
        self.schematic = schematic
        self._junction_index = self._build_junction_index()

    def _build_junction_index(self) -> Dict[Tuple[float, float], Junction]:
        """Build an index of junctions by position for fast lookup."""
        index = {}
        for junction in self.schematic.junctions:
            pos = (junction.position.x, junction.position.y)
            index[pos] = junction
        return index

    def update_junctions(self):
        """
        Update all junctions in the schematic.
        Adds junctions where needed and removes orphaned ones.
        """
        # Find all points where junctions might be needed
        junction_points = self._find_junction_points()

        # Remove junctions that are no longer needed
        positions_to_remove = []
        for pos, junction in self._junction_index.items():
            if pos not in junction_points:
                positions_to_remove.append(pos)

        for pos in positions_to_remove:
            self._remove_junction_at_position(pos)

        # Add new junctions where needed
        for point in junction_points:
            if point not in self._junction_index:
                self._add_junction_at_position(point)

        logger.info(
            f"Updated junctions: {len(junction_points)} total, "
            f"{len(positions_to_remove)} removed, "
            f"{len(junction_points) - len(self._junction_index) + len(positions_to_remove)} added"
        )

    def _find_junction_points(self) -> Set[Tuple[float, float]]:
        """
        Find all points where junctions are needed.
        A junction is needed where 3 or more wire segments meet.

        Returns:
            Set of (x, y) positions where junctions are needed
        """
        # Count connections at each point
        connection_count = defaultdict(int)

        # Process all wires
        for wire in self.schematic.wires:
            # Count endpoints
            start, end = wire.get_endpoints()
            connection_count[(start.x, start.y)] += 1
            connection_count[(end.x, end.y)] += 1

            # Check for T-junctions (wire passing through another wire's endpoint)
            for other_wire in self.schematic.wires:
                if wire == other_wire:
                    continue

                # Check if other wire passes through this wire's endpoints
                if other_wire.contains_point(start):
                    connection_count[(start.x, start.y)] += 1
                if other_wire.contains_point(end):
                    connection_count[(end.x, end.y)] += 1

        # Also check for wire crossings (4-way junctions)
        crossing_points = self._find_wire_crossings()
        for point in crossing_points:
            connection_count[point] = max(connection_count[point], 4)

        # Return points with 3 or more connections
        return {point for point, count in connection_count.items() if count >= 3}

    def _find_wire_crossings(self) -> Set[Tuple[float, float]]:
        """
        Find all points where wires cross.

        Returns:
            Set of (x, y) positions where wires cross
        """
        crossings = set()
        wires = self.schematic.wires

        # Check each pair of wires
        for i, wire1 in enumerate(wires):
            segments1 = get_wire_segments(wire1.points)

            for j, wire2 in enumerate(wires[i + 1 :], i + 1):
                segments2 = get_wire_segments(wire2.points)

                # Check each segment pair for intersection
                for seg1 in segments1:
                    for seg2 in segments2:
                        intersection = segment_intersection(
                            seg1[0], seg1[1], seg2[0], seg2[1]
                        )
                        if intersection:
                            crossings.add(intersection)

        return crossings

    def _add_junction_at_position(self, position: Tuple[float, float]):
        """Add a junction at the specified position."""
        x, y = position
        junction = Junction(position=Point(x, y), diameter=1.0)  # Default diameter
        self.schematic.junctions.append(junction)
        self._junction_index[position] = junction
        logger.debug(f"Added junction at ({x}, {y})")

    def _remove_junction_at_position(self, position: Tuple[float, float]):
        """Remove the junction at the specified position."""
        junction = self._junction_index.get(position)
        if junction:
            self.schematic.junctions.remove(junction)
            del self._junction_index[position]
            logger.debug(f"Removed junction at {position}")

    def add_junction(self, x: float, y: float, diameter: float = 1.0) -> Junction:
        """
        Manually add a junction at a specific position.

        Args:
            x: X coordinate
            y: Y coordinate
            diameter: Junction diameter

        Returns:
            Created junction
        """
        position = (x, y)

        # Check if junction already exists at this position
        if position in self._junction_index:
            logger.warning(f"Junction already exists at ({x}, {y})")
            return self._junction_index[position]

        junction = Junction(position=Point(x, y), diameter=diameter)
        self.schematic.junctions.append(junction)
        self._junction_index[position] = junction

        logger.info(f"Manually added junction at ({x}, {y})")
        return junction

    def remove_junction(self, junction: Junction) -> bool:
        """
        Remove a specific junction.

        Args:
            junction: Junction to remove

        Returns:
            True if removed, False if not found
        """
        position = (junction.position.x, junction.position.y)

        if position in self._junction_index:
            self.schematic.junctions.remove(junction)
            del self._junction_index[position]
            logger.info(f"Removed junction at {position}")
            return True

        logger.warning(f"Junction not found at {position}")
        return False

    def get_junction_at(self, x: float, y: float, tolerance: float = 0.01) -> Junction:
        """
        Get junction at a specific position.

        Args:
            x: X coordinate
            y: Y coordinate
            tolerance: Position tolerance

        Returns:
            Junction if found, None otherwise
        """
        # First try exact match
        junction = self._junction_index.get((x, y))
        if junction:
            return junction

        # Try with tolerance
        test_point = Point(x, y)
        for pos, junction in self._junction_index.items():
            if points_equal(junction.position, test_point, tolerance):
                return junction

        return None

    def find_junctions_in_area(
        self, x1: float, y1: float, x2: float, y2: float
    ) -> List[Junction]:
        """
        Find all junctions within a rectangular area.

        Args:
            x1, y1: Bottom-left corner
            x2, y2: Top-right corner

        Returns:
            List of junctions in the area
        """
        # Ensure correct ordering
        x_min, x_max = min(x1, x2), max(x1, x2)
        y_min, y_max = min(y1, y2), max(y1, y2)

        junctions = []
        for junction in self.schematic.junctions:
            x, y = junction.position.x, junction.position.y
            if x_min <= x <= x_max and y_min <= y <= y_max:
                junctions.append(junction)

        return junctions

    def validate_junctions(self) -> Tuple[bool, List[str]]:
        """
        Validate junction placement in the schematic.

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []

        # Check for orphaned junctions (no wires)
        junction_points = self._find_junction_points()
        for pos, junction in self._junction_index.items():
            if pos not in junction_points:
                issues.append(f"Orphaned junction at {pos} (no wires connect here)")

        # Check for missing junctions
        for point in junction_points:
            if point not in self._junction_index:
                issues.append(f"Missing junction at {point} (3+ wires meet here)")

        # Check for duplicate junctions
        seen_positions = set()
        for junction in self.schematic.junctions:
            pos = (junction.position.x, junction.position.y)
            if pos in seen_positions:
                issues.append(f"Duplicate junction at {pos}")
            seen_positions.add(pos)

        is_valid = len(issues) == 0
        return is_valid, issues
