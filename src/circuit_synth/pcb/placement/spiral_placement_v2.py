"""
Spiral placement algorithm for PCB components with courtyard collision detection.

This module implements a spiral search pattern for finding valid component positions
that maintain proper spacing while keeping connected components close together.
Uses actual courtyard geometry for accurate collision detection.
"""

import math
from dataclasses import dataclass

# Using simplified placement - removed complex courtyard collision for now
from typing import Dict, List, NamedTuple, Optional, Set, Tuple

from circuit_synth.pcb.types import Footprint, Point


class BoundingBox(NamedTuple):
    x: float
    y: float
    width: float
    height: float


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


class SpiralPlacementAlgorithmV2:
    """
    Placement algorithm using spiral search patterns with courtyard collision detection.

    This algorithm:
    1. Places components based on their connections
    2. Uses a spiral search pattern to find valid positions
    3. Keeps connected components close together
    4. Maintains proper spacing using actual courtyard geometry
    """

    def __init__(
        self,
        component_spacing: float = 5.0,
        spiral_step: float = 0.5,
        use_courtyard: bool = True,
    ):
        """
        Initialize the spiral placement algorithm.

        Args:
            component_spacing: Minimum spacing between components in mm
            spiral_step: Step size for spiral search in mm
            use_courtyard: If True, use courtyard geometry for collision detection
        """
        self.component_spacing = component_spacing
        self.spiral_step = spiral_step
        self.use_courtyard = use_courtyard
        self.collision_detector = CourtyardCollisionDetector(spacing=component_spacing)
        self.placed_components: Dict[str, Footprint] = {}

    def place_components(
        self,
        components: List[Footprint],
        board_outline: BoundingBox,
        connections: Optional[List[Tuple[str, str]]] = None,
    ) -> PlacementResult:
        """
        Place components using spiral search with connection awareness and courtyard collision.

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

        # Create board outline polygon
        board_vertices = [
            (board_outline.min_x, board_outline.min_y),
            (board_outline.max_x, board_outline.min_y),
            (board_outline.max_x, board_outline.max_y),
            (board_outline.min_x, board_outline.max_y),
        ]
        self.board_polygon = Polygon(board_vertices)

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

        # Log courtyard detection info for first component
        courtyard = self.collision_detector.get_courtyard_polygon(first_comp)
        if courtyard:
            print(
                f"[DEBUG] Component {first_comp.reference} has courtyard polygon with {len(courtyard.vertices)} vertices"
            )
        else:
            print(
                f"[DEBUG] Component {first_comp.reference} has no courtyard, using bounding box"
            )

        # Place remaining components
        for component in sorted_components[1:]:
            # Calculate ideal position based on connections
            ideal_x, ideal_y = self._calculate_ideal_position(
                component, connection_graph
            )

            # Find nearest valid position using spiral search
            valid_pos = self._find_nearest_valid_position(
                component, ideal_x, ideal_y, board_outline
            )

            if valid_pos is None:
                return PlacementResult(
                    success=False,
                    message=f"Could not find valid position for {component.reference}",
                )

            # Place component
            component.position = Point(valid_pos[0], valid_pos[1])
            self.placed_components[component.reference] = component

            # Log courtyard info
            courtyard = self.collision_detector.get_courtyard_polygon(component)
            if courtyard:
                print(
                    f"[DEBUG] Component {component.reference} placed with courtyard at ({valid_pos[0]:.2f}, {valid_pos[1]:.2f})"
                )

        return PlacementResult(
            success=True,
            message="Spiral placement with courtyard collision completed successfully",
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
    ) -> Optional[Tuple[float, float]]:
        """
        Find the nearest valid position using spiral search with courtyard collision detection.

        Returns:
            (x, y) tuple if valid position found, None otherwise
        """
        # Get list of already placed footprints
        placed_footprints = list(self.placed_components.values())

        # Use the collision detector's spiral search
        valid_pos = self.collision_detector.find_valid_position(
            component,
            start_x,
            start_y,
            placed_footprints,
            self.board_polygon,
            search_radius=max(board_outline.width(), board_outline.height()),
            search_step=self.spiral_step,
        )

        return valid_pos

    def get_placement_info(self) -> Dict[str, Dict[str, any]]:
        """
        Get detailed information about the placement.

        Returns:
            Dictionary with placement statistics and component info
        """
        info = {
            "total_components": len(self.placed_components),
            "use_courtyard": self.use_courtyard,
            "component_spacing": self.component_spacing,
            "components": {},
        }

        for ref, footprint in self.placed_components.items():
            courtyard = self.collision_detector.get_courtyard_polygon(footprint)
            polygon = self.collision_detector.get_footprint_polygon(
                footprint, self.use_courtyard
            )
            bbox = polygon.get_bounding_box()

            info["components"][ref] = {
                "position": (footprint.position.x, footprint.position.y),
                "rotation": footprint.rotation,
                "has_courtyard": courtyard is not None,
                "bbox": bbox,
                "footprint": footprint.get_library_id(),
            }

        return info
