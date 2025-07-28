"""
Spiral placement algorithm for PCB components.

This module implements a spiral search pattern for finding valid component positions
that maintain proper spacing while keeping connected components close together.
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from circuit_synth.kicad_api.pcb.placement.base import BoundingBox
from circuit_synth.kicad_api.pcb.types import Footprint, Point


@dataclass
class PlacementResult:
    """Result of a placement operation."""

    success: bool
    message: str = ""


@dataclass
class ConnectionInfo:
    """Information about component connections."""

    component_ref: str
    connected_refs: Set[str]
    connection_count: int


class SpiralPlacementAlgorithm:
    """
    Placement algorithm using spiral search patterns to find optimal positions.

    This algorithm:
    1. Places components based on their connections
    2. Uses a spiral search pattern to find valid positions
    3. Keeps connected components close together
    4. Maintains proper spacing between all components
    """

    def __init__(self, component_spacing: float = 5.0, spiral_step: float = 0.5):
        """
        Initialize the spiral placement algorithm.

        Args:
            component_spacing: Minimum spacing between components in mm
            spiral_step: Step size for spiral search in mm
        """
        self.component_spacing = component_spacing
        self.spiral_step = spiral_step
        self.placed_components: Dict[str, Footprint] = {}
        self.placed_bboxes: List[BoundingBox] = []

    def place_components(
        self,
        components: List[Footprint],
        board_outline: BoundingBox,
        connections: Optional[List[Tuple[str, str]]] = None,
    ) -> PlacementResult:
        """
        Place components using spiral search with connection awareness.

        Args:
            components: List of components to place
            board_outline: Board boundary
            connections: List of (ref1, ref2) tuples indicating connections

        Returns:
            PlacementResult with placement success and any error messages
        """
        if not components:
            return PlacementResult(success=True, message="No components to place")

        # Reset placement state
        self.placed_components.clear()
        self.placed_bboxes.clear()

        # Build connection graph
        connection_graph = self._build_connection_graph(components, connections or [])

        # Sort components by connection count (most connected first)
        sorted_components = sorted(
            components,
            key=lambda c: connection_graph.get(
                c.reference, ConnectionInfo(c.reference, set(), 0)
            ).connection_count,
            reverse=True,
        )

        # Place first component at board center
        board_center_x = (board_outline.min_x + board_outline.max_x) / 2
        board_center_y = (board_outline.min_y + board_outline.max_y) / 2

        first_comp = sorted_components[0]
        first_comp.position = Point(board_center_x, board_center_y)
        self.placed_components[first_comp.reference] = first_comp
        self.placed_bboxes.append(self._get_inflated_bbox(first_comp))

        # Place remaining components
        for component in sorted_components[1:]:
            # Calculate ideal position based on connections
            ideal_x, ideal_y = self._calculate_ideal_position(
                component, connection_graph
            )

            # Find nearest valid position using spiral search
            valid_x, valid_y = self._find_nearest_valid_position(
                component, ideal_x, ideal_y, board_outline
            )

            if valid_x is None or valid_y is None:
                return PlacementResult(
                    success=False,
                    message=f"Could not find valid position for {component.reference}",
                )

            # Place component
            component.position = Point(valid_x, valid_y)
            self.placed_components[component.reference] = component
            self.placed_bboxes.append(self._get_inflated_bbox(component))

        return PlacementResult(
            success=True, message="Spiral placement completed successfully"
        )

    def _build_connection_graph(
        self, components: List[Footprint], connections: List[Tuple[str, str]]
    ) -> Dict[str, ConnectionInfo]:
        """Build a graph of component connections."""
        # Create component lookup
        comp_dict = {comp.reference: comp for comp in components}

        # Initialize connection info for all components
        connection_graph = {}
        for comp in components:
            connection_graph[comp.reference] = ConnectionInfo(
                component_ref=comp.reference, connected_refs=set(), connection_count=0
            )

        # Add connections
        for ref1, ref2 in connections:
            if ref1 in comp_dict and ref2 in comp_dict:
                connection_graph[ref1].connected_refs.add(ref2)
                connection_graph[ref1].connection_count += 1
                connection_graph[ref2].connected_refs.add(ref1)
                connection_graph[ref2].connection_count += 1

        return connection_graph

    def _calculate_ideal_position(
        self, component: Footprint, connection_graph: Dict[str, ConnectionInfo]
    ) -> Tuple[float, float]:
        """
        Calculate ideal position based on connected components.

        Uses center of gravity of already-placed connected components.
        """
        conn_info = connection_graph.get(component.reference)
        if not conn_info or not conn_info.connected_refs:
            # No connections, place at center of placed components
            if self.placed_components:
                sum_x = sum(comp.position.x for comp in self.placed_components.values())
                sum_y = sum(comp.position.y for comp in self.placed_components.values())
                return sum_x / len(self.placed_components), sum_y / len(
                    self.placed_components
                )
            else:
                return 50.0, 50.0  # Default center

        # Calculate center of gravity of connected components
        connected_placed = [
            self.placed_components[ref]
            for ref in conn_info.connected_refs
            if ref in self.placed_components
        ]

        if not connected_placed:
            # No connected components placed yet, use center of all placed
            if self.placed_components:
                sum_x = sum(comp.position.x for comp in self.placed_components.values())
                sum_y = sum(comp.position.y for comp in self.placed_components.values())
                return sum_x / len(self.placed_components), sum_y / len(
                    self.placed_components
                )
            else:
                return 50.0, 50.0

        # Calculate weighted center (could add connection strength as weight)
        sum_x = sum(comp.position.x for comp in connected_placed)
        sum_y = sum(comp.position.y for comp in connected_placed)

        return sum_x / len(connected_placed), sum_y / len(connected_placed)

    def _find_nearest_valid_position(
        self,
        component: Footprint,
        start_x: float,
        start_y: float,
        board_outline: BoundingBox,
    ) -> Tuple[Optional[float], Optional[float]]:
        """
        Find the nearest valid position using spiral search.

        Returns:
            (x, y) tuple if valid position found, (None, None) otherwise
        """
        # Check if starting position is valid
        if self._is_position_valid(component, start_x, start_y, board_outline):
            return start_x, start_y

        # Spiral search parameters
        angle = 0.0
        radius = 0.0
        angle_step = math.pi / 8  # 22.5 degrees

        # Maximum search radius (diagonal of board)
        max_radius = math.sqrt(
            (board_outline.max_x - board_outline.min_x) ** 2
            + (board_outline.max_y - board_outline.min_y) ** 2
        )

        while radius < max_radius:
            # Try current position
            x = start_x + radius * math.cos(angle)
            y = start_y + radius * math.sin(angle)

            if self._is_position_valid(component, x, y, board_outline):
                return x, y

            # Update spiral
            angle += angle_step
            if angle >= 2 * math.pi:
                angle -= 2 * math.pi
                radius += self.spiral_step

        return None, None

    def _is_position_valid(
        self, component: Footprint, x: float, y: float, board_outline: BoundingBox
    ) -> bool:
        """Check if a position is valid for the component."""
        # Temporarily set position to check
        original_pos = component.position
        component.position = Point(x, y)

        # Get component bounding box with spacing
        comp_bbox = self._get_inflated_bbox(component)

        # Restore original position
        component.position = original_pos

        # Check board boundaries
        if not self._is_within_board(comp_bbox, board_outline):
            return False

        # Check collisions with placed components
        for placed_bbox in self.placed_bboxes:
            if self._boxes_overlap(comp_bbox, placed_bbox):
                return False

        return True

    def _get_inflated_bbox(self, component: Footprint) -> BoundingBox:
        """Get component bounding box inflated by spacing."""
        # Calculate bounding box from pads and footprint size
        # This is a simplified version - in reality we'd parse the footprint
        # For now, use a default size based on footprint type

        x = component.position.x
        y = component.position.y

        # Estimate size based on footprint name
        if "0603" in component.name:
            width, height = 1.6, 0.8
        elif "0805" in component.name:
            width, height = 2.0, 1.25
        elif "SOT-23" in component.name:
            width, height = 2.9, 1.3
        elif "SOT-223" in component.name:
            width, height = 6.5, 3.5
        elif "SOIC-8" in component.name:
            width, height = 3.9, 4.9
        elif "LQFP-48" in component.name:
            width, height = 7.0, 7.0
        elif "ESP32" in component.name:
            width, height = 15.4, 20.5
        elif "USB_C" in component.name:
            width, height = 8.94, 7.3
        elif "IDC-Header" in component.name:
            width, height = 7.62, 5.08
        elif "LGA-14" in component.name:
            width, height = 3.0, 2.5
        elif "D_SOD-523" in component.name:
            width, height = 1.2, 0.8
        else:
            # Default size
            width, height = 2.0, 2.0

        half_spacing = self.component_spacing / 2

        return BoundingBox(
            min_x=x - width / 2 - half_spacing,
            min_y=y - height / 2 - half_spacing,
            max_x=x + width / 2 + half_spacing,
            max_y=y + height / 2 + half_spacing,
        )

    def _is_within_board(self, bbox: BoundingBox, board_outline: BoundingBox) -> bool:
        """Check if bounding box is within board outline."""
        return (
            bbox.min_x >= board_outline.min_x
            and bbox.max_x <= board_outline.max_x
            and bbox.min_y >= board_outline.min_y
            and bbox.max_y <= board_outline.max_y
        )

    def _boxes_overlap(self, box1: BoundingBox, box2: BoundingBox) -> bool:
        """Check if two bounding boxes overlap."""
        return not (
            box1.max_x < box2.min_x
            or box2.max_x < box1.min_x
            or box1.max_y < box2.min_y
            or box2.max_y < box1.min_y
        )
