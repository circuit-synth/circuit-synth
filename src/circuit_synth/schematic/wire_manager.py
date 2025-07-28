"""
Wire management for KiCad schematics.

This module provides functionality for managing wires, junctions, and connections
in KiCad schematics, including tracking wire-to-component mappings and routing.
"""

import logging
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from ..core.types import (
    Junction,
    Label,
    LabelType,
    Point,
    Schematic,
    SchematicPin,
    SchematicSymbol,
    Wire,
)

logger = logging.getLogger(__name__)


@dataclass
class ConnectionPoint:
    """Represents a connection point in the schematic."""

    position: Point
    connected_elements: Set[str] = field(
        default_factory=set
    )  # UUIDs of connected elements
    net_name: Optional[str] = None

    def add_connection(self, element_uuid: str):
        """Add a connected element."""
        self.connected_elements.add(element_uuid)


class WireManager:
    """
    Manages wires and connections in a schematic.

    This class provides functionality for:
    - Tracking wire-to-component pin connections
    - Managing junctions where wires meet
    - Finding and manipulating wire connections
    - Routing new wires between points
    """

    def __init__(self, schematic: Schematic):
        """
        Initialize the wire manager.

        Args:
            schematic: The schematic to manage wires for
        """
        self.schematic = schematic
        self.wires: Dict[str, Wire] = {}
        self.junctions: Dict[str, Junction] = {}
        self.pin_connections: Dict[Tuple[str, str], List[str]] = (
            {}
        )  # (comp_ref, pin) -> [wire_ids]
        self.connection_points: Dict[Tuple[float, float], ConnectionPoint] = {}

        # Build initial wire database
        self._build_wire_database()

    def _build_wire_database(self):
        """Build the initial wire database from the schematic."""
        # Index all wires
        for wire in self.schematic.wires:
            self.wires[wire.uuid] = wire

            # Track connection points
            for point in wire.points:
                pos_key = (point.x, point.y)
                if pos_key not in self.connection_points:
                    self.connection_points[pos_key] = ConnectionPoint(point)
                self.connection_points[pos_key].add_connection(wire.uuid)

        # Index all junctions
        for junction in self.schematic.junctions:
            self.junctions[junction.uuid] = junction

            # Junctions are connection points
            pos_key = (junction.position.x, junction.position.y)
            if pos_key not in self.connection_points:
                self.connection_points[pos_key] = ConnectionPoint(junction.position)
            self.connection_points[pos_key].add_connection(junction.uuid)

        # Build pin-to-wire mappings
        self._build_pin_connections()

    def _build_pin_connections(self):
        """Build mappings from component pins to connected wires."""
        # This requires knowledge of component pin positions
        # For now, we'll implement a basic version that can be enhanced later
        for component in self.schematic.components:
            # Get component pins (this would need symbol library data)
            pins = self._get_component_pins(component)

            for pin in pins:
                pin_pos = self._get_pin_position(component, pin)

                # Find wires connected to this pin
                connected_wires = self._find_wires_at_point(pin_pos)
                if connected_wires:
                    key = (component.reference, pin.number)
                    self.pin_connections[key] = [w.uuid for w in connected_wires]

    def _get_component_pins(self, component: SchematicSymbol) -> List[SchematicPin]:
        """
        Get pins for a component.

        Note: This is a placeholder. In a full implementation, this would
        query the symbol library cache to get actual pin data.
        """
        # TODO: Integrate with symbol library cache
        return []

    def _get_pin_position(self, component: SchematicSymbol, pin: SchematicPin) -> Point:
        """
        Calculate the absolute position of a pin.

        Args:
            component: The component containing the pin
            pin: The pin to get position for

        Returns:
            Absolute position of the pin in schematic coordinates
        """
        # This would need to account for component rotation and mirroring
        # For now, return a simple offset from component position
        return Point(
            component.position.x + pin.position.x, component.position.y + pin.position.y
        )

    def _find_wires_at_point(self, point: Point, tolerance: float = 0.01) -> List[Wire]:
        """
        Find all wires that pass through or end at a given point.

        Args:
            point: The point to check
            tolerance: Distance tolerance for matching

        Returns:
            List of wires at the point
        """
        wires = []

        for wire in self.wires.values():
            # Check endpoints
            start, end = wire.get_endpoints()
            if self._points_equal(start, point, tolerance) or self._points_equal(
                end, point, tolerance
            ):
                wires.append(wire)
            # Check if point lies on wire
            elif wire.contains_point(point, tolerance):
                wires.append(wire)

        return wires

    def _points_equal(self, p1: Point, p2: Point, tolerance: float) -> bool:
        """Check if two points are equal within tolerance."""
        return abs(p1.x - p2.x) <= tolerance and abs(p1.y - p2.y) <= tolerance

    def find_wires_for_pin(self, component_ref: str, pin_number: str) -> List[Wire]:
        """
        Find all wires connected to a specific component pin.

        Args:
            component_ref: Component reference (e.g., "R1")
            pin_number: Pin number/name

        Returns:
            List of wires connected to the pin
        """
        key = (component_ref, pin_number)
        wire_uuids = self.pin_connections.get(key, [])
        return [self.wires[uuid] for uuid in wire_uuids if uuid in self.wires]

    def remove_pin_connections(self, component_ref: str, pin_number: str):
        """
        Remove all wires connected to a specific pin.

        Args:
            component_ref: Component reference (e.g., "R1")
            pin_number: Pin number/name
        """
        wires_to_remove = self.find_wires_for_pin(component_ref, pin_number)

        for wire in wires_to_remove:
            # Remove from schematic
            self.schematic.wires = [
                w for w in self.schematic.wires if w.uuid != wire.uuid
            ]

            # Remove from our tracking
            if wire.uuid in self.wires:
                del self.wires[wire.uuid]

            # Update connection points
            for point in wire.points:
                pos_key = (point.x, point.y)
                if pos_key in self.connection_points:
                    self.connection_points[pos_key].connected_elements.discard(
                        wire.uuid
                    )

        # Remove from pin connections
        key = (component_ref, pin_number)
        if key in self.pin_connections:
            del self.pin_connections[key]

    def add_wire_between_points(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        net_name: Optional[str] = None,
    ) -> Wire:
        """
        Add a new wire between two points.

        Args:
            start: Starting point (x, y)
            end: Ending point (x, y)
            net_name: Optional net name for the wire

        Returns:
            The created wire
        """
        # Create wire with simple direct connection
        wire = Wire(
            points=[Point(start[0], start[1]), Point(end[0], end[1])],
            uuid=str(uuid.uuid4()),
        )

        # Add to schematic
        self.schematic.add_wire(wire)

        # Add to our tracking
        self.wires[wire.uuid] = wire

        # Update connection points
        for point in wire.points:
            pos_key = (point.x, point.y)
            if pos_key not in self.connection_points:
                self.connection_points[pos_key] = ConnectionPoint(point)
            self.connection_points[pos_key].add_connection(wire.uuid)
            if net_name:
                self.connection_points[pos_key].net_name = net_name

        return wire

    def route_wire(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        routing_style: str = "manhattan",
    ) -> Wire:
        """
        Route a wire between two points using specified routing style.

        Args:
            start: Starting point (x, y)
            end: Ending point (x, y)
            routing_style: Routing style ("direct", "manhattan", "diagonal")

        Returns:
            The created wire with routed path
        """
        if routing_style == "direct":
            # Simple direct connection
            return self.add_wire_between_points(start, end)

        elif routing_style == "manhattan":
            # Manhattan routing (horizontal/vertical only)
            points = self._manhattan_route(start, end)

            wire = Wire(points=points, uuid=str(uuid.uuid4()))

            # Add to schematic and tracking
            self.schematic.add_wire(wire)
            self.wires[wire.uuid] = wire

            # Update connection points
            for point in wire.points:
                pos_key = (point.x, point.y)
                if pos_key not in self.connection_points:
                    self.connection_points[pos_key] = ConnectionPoint(point)
                self.connection_points[pos_key].add_connection(wire.uuid)

            return wire

        else:
            # Default to direct for unsupported styles
            logger.warning(f"Unsupported routing style: {routing_style}, using direct")
            return self.add_wire_between_points(start, end)

    def _manhattan_route(
        self, start: Tuple[float, float], end: Tuple[float, float]
    ) -> List[Point]:
        """
        Create Manhattan-style routing between two points.

        Args:
            start: Starting point (x, y)
            end: Ending point (x, y)

        Returns:
            List of points defining the wire path
        """
        points = [Point(start[0], start[1])]

        # Simple L-shaped routing
        if abs(start[0] - end[0]) > abs(start[1] - end[1]):
            # Horizontal first
            points.append(Point(end[0], start[1]))
        else:
            # Vertical first
            points.append(Point(start[0], end[1]))

        points.append(Point(end[0], end[1]))

        return points

    def find_or_create_junction(self, position: Tuple[float, float]) -> Junction:
        """
        Find an existing junction at a position or create a new one.

        Args:
            position: Position to check (x, y)

        Returns:
            Existing or newly created junction
        """
        # Check if junction already exists at this position
        for junction in self.junctions.values():
            if (
                abs(junction.position.x - position[0]) < 0.01
                and abs(junction.position.y - position[1]) < 0.01
            ):
                return junction

        # Create new junction
        junction = Junction(
            position=Point(position[0], position[1]), uuid=str(uuid.uuid4())
        )

        # Add to schematic and tracking
        self.schematic.junctions.append(junction)
        self.junctions[junction.uuid] = junction

        # Update connection points
        pos_key = position
        if pos_key not in self.connection_points:
            self.connection_points[pos_key] = ConnectionPoint(junction.position)
        self.connection_points[pos_key].add_connection(junction.uuid)

        return junction

    def get_net_at_point(self, position: Tuple[float, float]) -> Optional[str]:
        """
        Get the net name at a specific point.

        Args:
            position: Position to check (x, y)

        Returns:
            Net name if found, None otherwise
        """
        pos_key = position
        if pos_key in self.connection_points:
            return self.connection_points[pos_key].net_name

        # Check labels at this position
        for label in self.schematic.labels:
            if (
                abs(label.position.x - position[0]) < 0.01
                and abs(label.position.y - position[1]) < 0.01
            ):
                return label.text

        return None
