"""
Connection-centric PCB component placement algorithm.
Places components based on connection count, minimizing total connection length.
"""

import logging
import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from ..types import Point
from .base import ComponentWrapper, PlacementAlgorithm
from .bbox import BoundingBox
from .courtyard_collision_improved import CourtyardCollisionDetector

logger = logging.getLogger(__name__)


@dataclass
class ConnectionInfo:
    """Information about a component's connections."""

    total: int
    connected_components: List[str]
    subcircuit: str


class ConnectionCentricPlacement(PlacementAlgorithm):
    """
    Places components based on connection count.
    Components with the most connections are placed first,
    and subsequent components are placed to minimize connection length.
    """

    def __init__(self, min_spacing: float = 2.0, use_courtyard: bool = True):
        """
        Initialize the connection-centric placement algorithm.

        Args:
            min_spacing: Minimum spacing between components in mm
            use_courtyard: If True, use courtyard geometry for collision detection
        """
        self.min_spacing = min_spacing
        self.use_courtyard = use_courtyard
        self.placed_components: Dict[str, ComponentWrapper] = {}
        self.placed_positions: Dict[str, Point] = {}
        self.collision_detector = CourtyardCollisionDetector(spacing=min_spacing)

    def place(
        self,
        components: List[ComponentWrapper],
        connections: List[Tuple[str, str]],
        board_width: float = 100.0,
        board_height: float = 100.0,
        **kwargs,
    ) -> Dict[str, Point]:
        """
        Place components based on connection count.

        Args:
            components: List of components to place
            connections: List of (ref1, ref2) tuples representing connections
            board_width: Board width in mm
            board_height: Board height in mm
            **kwargs: Additional parameters (e.g., min_spacing)

        Returns:
            Dictionary mapping component references to positions
        """
        logger.info(
            f"[ConnectionCentricPlacement] Starting placement for {len(components)} components"
        )

        # Override min_spacing if provided
        if "min_spacing" in kwargs:
            self.min_spacing = kwargs["min_spacing"]

        # Clear previous placement
        self.placed_components.clear()
        self.placed_positions.clear()

        # Analyze connections
        connection_info = self._analyze_connections(components, connections)

        # Group components by subcircuit
        subcircuits = self._group_by_subcircuit(components, connection_info)

        # Place each subcircuit
        subcircuit_offset_x = self.min_spacing

        for subcircuit_name, subcircuit_components in subcircuits.items():
            logger.info(
                f"[ConnectionCentricPlacement] Placing subcircuit '{subcircuit_name}' "
                f"with {len(subcircuit_components)} components"
            )

            # Place this subcircuit
            self._place_subcircuit(
                subcircuit_components,
                connection_info,
                subcircuit_offset_x,
                board_width,
                board_height,
            )

            # Calculate offset for next subcircuit
            if self.placed_positions:
                max_x = 0
                for comp in subcircuit_components:
                    if comp.reference in self.placed_positions:
                        pos = self.placed_positions[comp.reference]
                        comp_right_edge = pos.x + comp.bbox.width() / 2
                        max_x = max(max_x, comp_right_edge)
                subcircuit_offset_x = max_x + self.min_spacing * 3

        logger.info(
            f"[ConnectionCentricPlacement] Placement complete. "
            f"Placed {len(self.placed_positions)} components"
        )

        return self.placed_positions

    def _analyze_connections(
        self, components: List[ComponentWrapper], connections: List[Tuple[str, str]]
    ) -> Dict[str, ConnectionInfo]:
        """Analyze component connections."""
        # Create component lookup
        comp_dict = {comp.reference: comp for comp in components}

        # Initialize connection info
        connection_info = {}
        for comp in components:
            ref = comp.reference
            subcircuit = self._get_subcircuit(ref)
            connection_info[ref] = ConnectionInfo(
                total=0, connected_components=[], subcircuit=subcircuit
            )

        # Count connections
        for ref1, ref2 in connections:
            if ref1 in connection_info and ref2 in connection_info:
                connection_info[ref1].total += 1
                connection_info[ref1].connected_components.append(ref2)
                connection_info[ref2].total += 1
                connection_info[ref2].connected_components.append(ref1)

        # Log connection analysis
        for ref, info in connection_info.items():
            logger.debug(
                f"[ConnectionAnalysis] {ref}: {info.total} connections, "
                f"subcircuit='{info.subcircuit}'"
            )

        return connection_info

    def _get_subcircuit(self, reference: str) -> str:
        """Extract subcircuit from component reference."""
        # Handle hierarchical references like "/PowerSupply/U1"
        if "/" in reference:
            parts = reference.strip("/").split("/")
            if len(parts) > 1:
                return parts[0]
        return "root"

    def _group_by_subcircuit(
        self,
        components: List[ComponentWrapper],
        connection_info: Dict[str, ConnectionInfo],
    ) -> Dict[str, List[ComponentWrapper]]:
        """Group components by subcircuit."""
        subcircuits = {}

        for comp in components:
            subcircuit = connection_info[comp.reference].subcircuit
            if subcircuit not in subcircuits:
                subcircuits[subcircuit] = []
            subcircuits[subcircuit].append(comp)

        return subcircuits

    def _place_subcircuit(
        self,
        components: List[ComponentWrapper],
        connection_info: Dict[str, ConnectionInfo],
        offset_x: float,
        board_width: float,
        board_height: float,
    ):
        """Place components within a subcircuit."""
        # Sort components by connection count (highest first)
        sorted_components = sorted(
            components,
            key=lambda comp: connection_info[comp.reference].total,
            reverse=True,
        )

        for i, comp in enumerate(sorted_components):
            if i == 0:
                # Place first component at subcircuit origin
                position = Point(offset_x + comp.bbox.width() / 2, board_height / 2)
                logger.debug(
                    f"[Placement] Placing first component {comp.reference} at {position}"
                )
            else:
                # Find optimal position based on connections
                position = self._find_optimal_position(
                    comp, connection_info[comp.reference], board_width, board_height
                )
                logger.debug(
                    f"[Placement] Placing {comp.reference} at {position} "
                    f"(connections: {connection_info[comp.reference].total})"
                )

            # Update the component's position for collision detection
            comp.footprint.position = position

            # Store the component and position
            self.placed_components[comp.reference] = comp
            self.placed_positions[comp.reference] = position

    def _find_optimal_position(
        self,
        component: ComponentWrapper,
        conn_info: ConnectionInfo,
        board_width: float,
        board_height: float,
    ) -> Point:
        """Find optimal position for a component based on connections."""
        # Find connected components that are already placed
        connected_placed = [
            ref
            for ref in conn_info.connected_components
            if ref in self.placed_positions
        ]

        if not connected_placed:
            # No connected components placed yet, place at edge
            return self._find_edge_position(component, board_width, board_height)

        # Calculate center of gravity of connected components
        total_x = sum(self.placed_positions[ref].x for ref in connected_placed)
        total_y = sum(self.placed_positions[ref].y for ref in connected_placed)
        ideal_x = total_x / len(connected_placed)
        ideal_y = total_y / len(connected_placed)

        # Find nearest valid position to ideal position
        return self._find_nearest_valid_position(
            component, Point(ideal_x, ideal_y), board_width, board_height
        )

    def _find_nearest_valid_position(
        self,
        component: ComponentWrapper,
        ideal_pos: Point,
        board_width: float,
        board_height: float,
    ) -> Point:
        """Find the nearest valid position to the ideal position."""
        # Start at ideal position
        test_pos = Point(ideal_pos.x, ideal_pos.y)

        # Check if position is valid
        if self._is_valid_position(component, test_pos, board_width, board_height):
            return test_pos

        # Search in expanding spiral pattern
        step = self.min_spacing / 2
        max_radius = max(board_width, board_height)

        for radius in range(int(step), int(max_radius), int(step)):
            # Try positions in a circle around ideal position
            num_points = max(8, int(2 * math.pi * radius / step))
            for i in range(num_points):
                angle = 2 * math.pi * i / num_points
                test_x = ideal_pos.x + radius * math.cos(angle)
                test_y = ideal_pos.y + radius * math.sin(angle)
                test_pos = Point(test_x, test_y)

                if self._is_valid_position(
                    component, test_pos, board_width, board_height
                ):
                    return test_pos

        # Fallback - place at edge
        logger.warning(
            f"[Placement] Could not find valid position near {ideal_pos}, "
            "placing at edge"
        )
        return self._find_edge_position(component, board_width, board_height)

    def _is_valid_position(
        self,
        component: ComponentWrapper,
        position: Point,
        board_width: float,
        board_height: float,
    ) -> bool:
        """Check if a position is valid (no collisions, within board)."""
        # Temporarily set the component position for collision checking
        original_pos = component.footprint.position
        component.footprint.position = position

        try:
            # Get the polygon (courtyard or bounding box) for the component
            polygon = self.collision_detector.get_footprint_polygon(
                component.footprint, use_courtyard=self.use_courtyard
            )

            # Debug: Check if courtyard is being used
            if hasattr(self.collision_detector, "get_courtyard_polygon"):
                courtyard = self.collision_detector.get_courtyard_polygon(
                    component.footprint
                )
                if courtyard:
                    logger.debug(
                        f"[Collision] Component {component.reference} using courtyard for collision detection"
                    )
                else:
                    logger.debug(
                        f"[Collision] Component {component.reference} has no courtyard, using bounding box"
                    )
            bbox = (
                polygon.get_bounding_box()
            )  # Returns tuple (min_x, min_y, max_x, max_y)

            # Check board boundaries
            min_x, min_y, max_x, max_y = bbox
            if min_x < 0 or max_x > board_width or min_y < 0 or max_y > board_height:
                return False

            # Check collisions with placed components using courtyard detection
            for placed_comp in self.placed_components.values():
                if self.collision_detector.check_collision(
                    component.footprint, placed_comp.footprint
                ):
                    return False

            return True

        finally:
            # Restore original position
            component.footprint.position = original_pos

    def _find_edge_position(
        self, component: ComponentWrapper, board_width: float, board_height: float
    ) -> Point:
        """Find a position at the edge of placed components."""
        if not self.placed_components:
            # First component - place at board center
            return Point(board_width / 2, board_height / 2)

        # Find rightmost placed component based on actual positions
        max_x = 0
        for ref, comp in self.placed_components.items():
            placed_pos = self.placed_positions.get(ref)
            if placed_pos:
                comp_right_edge = placed_pos.x + comp.bbox.width() / 2
                max_x = max(max_x, comp_right_edge)

        # Try to place to the right
        test_x = max_x + self.min_spacing + component.bbox.width() / 2
        test_y = board_height / 2

        test_pos = Point(test_x, test_y)
        if self._is_valid_position(component, test_pos, board_width, board_height):
            return test_pos

        # If that doesn't work, search for any valid position
        for x in range(
            int(component.bbox.width() / 2),
            int(board_width - component.bbox.width() / 2),
            int(self.min_spacing),
        ):
            for y in range(
                int(component.bbox.height() / 2),
                int(board_height - component.bbox.height() / 2),
                int(self.min_spacing),
            ):
                test_pos = Point(float(x), float(y))
                if self._is_valid_position(
                    component, test_pos, board_width, board_height
                ):
                    return test_pos

        # Fallback
        return Point(board_width / 2, board_height / 2)
