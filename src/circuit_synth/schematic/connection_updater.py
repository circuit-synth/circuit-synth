"""
Connection update functionality for KiCad schematics.

This module provides functionality for updating wire connections
when components change, including automatic wire routing and
net management.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from ..core.types import (
    Junction,
    Label,
    LabelType,
    Point,
    Schematic,
    SchematicSymbol,
    Wire,
)
from .instance_utils import add_symbol_instance
from .wire_manager import WireManager
from .wire_router import RoutingConstraints, WireRouter

logger = logging.getLogger(__name__)


@dataclass
class ConnectionUpdate:
    """Represents a connection update operation."""

    component_ref: str
    pin_nets: Dict[str, str]  # pin_number -> net_name
    routing_style: str = "manhattan"


class ConnectionUpdater:
    """
    Handles updating connections in a schematic.

    This class manages:
    - Removing old connections
    - Creating new connections with proper routing
    - Managing power/ground symbols
    - Creating and placing net labels
    """

    def __init__(self, schematic: Schematic):
        """
        Initialize the connection updater.

        Args:
            schematic: The schematic to update
        """
        self.schematic = schematic
        self.wire_manager = WireManager(schematic)
        self.wire_router = WireRouter()

        # Track power nets for special handling
        self.power_nets = {
            "VCC",
            "VDD",
            "+5V",
            "+3V3",
            "+12V",
            "-12V",
            "GND",
            "VSS",
            "AGND",
            "DGND",
        }

    def update_component_connections(
        self,
        component_ref: str,
        pin_nets: Dict[str, str],
        preserve_routing: bool = False,
    ) -> bool:
        """
        Update all connections for a component.

        Args:
            component_ref: Component reference (e.g., "R1")
            pin_nets: Dict mapping pin numbers to net names
            preserve_routing: Try to preserve existing wire routing

        Returns:
            True if successful, False otherwise
        """
        # Find the component
        component = self.schematic.get_component(component_ref)
        if not component:
            logger.error(f"Component {component_ref} not found")
            return False

        # Get component pin information
        pins = self._get_component_pins(component)
        if not pins:
            logger.warning(f"No pin information for {component_ref}")
            return False

        # Remove existing connections for all pins
        for pin in pins:
            self.wire_manager.remove_pin_connections(component_ref, pin.number)

        # Create new connections
        for pin_num, net_name in pin_nets.items():
            pin = self._find_pin(pins, pin_num)
            if not pin:
                logger.warning(f"Pin {pin_num} not found on {component_ref}")
                continue

            # Calculate pin position
            pin_pos = self._get_pin_position(component, pin)

            # Connect pin to net
            self._connect_pin_to_net(component, pin, pin_pos, net_name)

        return True

    def _get_component_pins(self, component: SchematicSymbol) -> List:
        """
        Get pin information for a component.

        Returns the pins from the component if available.
        """
        return component.pins if hasattr(component, "pins") else []

    def _find_pin(self, pins: List, pin_number: str):
        """Find a pin by number in the pin list."""
        for pin in pins:
            if str(pin.number) == str(pin_number):
                return pin
        return None

    def _get_pin_position(self, component: SchematicSymbol, pin) -> Point:
        """
        Calculate the absolute position of a pin.

        This accounts for component rotation and mirroring.
        """
        # TODO: Implement proper transformation based on rotation/mirroring
        # For now, simple offset
        pin_offset = pin.position if hasattr(pin, "position") else Point(0, 0)
        return Point(
            component.position.x + pin_offset.x, component.position.y + pin_offset.y
        )

    def _connect_pin_to_net(
        self, component: SchematicSymbol, pin, pin_pos: Point, net_name: str
    ):
        """
        Connect a pin to a net, creating wires and labels as needed.

        Args:
            component: The component
            pin: The pin to connect
            pin_pos: Absolute position of the pin
            net_name: Name of the net to connect to
        """
        # Find or create connection point for the net
        net_point = self._find_or_create_net_point(net_name, pin_pos)

        if net_point:
            # Route wire from pin to net point
            wire_path = self.wire_router.route_manhattan(
                (pin_pos.x, pin_pos.y), (net_point.x, net_point.y)
            )

            # Create wire
            wire = Wire(points=wire_path)
            self.schematic.add_wire(wire)

            # Update wire manager
            self.wire_manager.wires[wire.uuid] = wire

            # Add junction if needed
            if self._needs_junction(net_point):
                junction = self.wire_manager.find_or_create_junction(
                    (net_point.x, net_point.y)
                )

    def _find_or_create_net_point(
        self, net_name: str, near_pos: Point
    ) -> Optional[Point]:
        """
        Find an existing connection point for a net or create a new one.

        Args:
            net_name: Name of the net
            near_pos: Position to search near or create at

        Returns:
            Connection point for the net
        """
        # Check if this is a power net
        if net_name in self.power_nets:
            return self._create_power_symbol(net_name, near_pos)

        # Look for existing labels with this net name
        existing_label = self._find_nearest_label(net_name, near_pos)
        if existing_label:
            return existing_label.position

        # Look for existing wires with this net
        # (This would require net tracing functionality)

        # Create a new label for the net
        return self._create_net_label(net_name, near_pos)

    def _create_power_symbol(self, net_name: str, near_pos: Point) -> Point:
        """
        Create a power symbol for power nets.

        Args:
            net_name: Name of the power net (e.g., "VCC", "GND")
            near_pos: Position to place near

        Returns:
            Connection point of the power symbol
        """
        # Determine power symbol library ID
        if net_name in ["GND", "VSS", "AGND", "DGND"]:
            lib_id = "power:GND"
        elif net_name in ["VCC", "VDD"]:
            lib_id = "power:VCC"
        elif net_name == "+5V":
            lib_id = "power:+5V"
        elif net_name == "+3V3":
            lib_id = "power:+3V3"
        elif net_name == "+12V":
            lib_id = "power:+12V"
        elif net_name == "-12V":
            lib_id = "power:-12V"
        else:
            lib_id = "power:PWR_FLAG"

        # Calculate position - offset from component
        offset = 10.0  # mm
        symbol_pos = Point(near_pos.x, near_pos.y - offset)

        # Snap to grid
        symbol_pos.x = round(symbol_pos.x / 2.54) * 2.54
        symbol_pos.y = round(symbol_pos.y / 2.54) * 2.54

        # Create power symbol
        power_symbol = SchematicSymbol(
            reference="#PWR?",  # Will be assigned by KiCad
            value=net_name,
            lib_id=lib_id,
            position=symbol_pos,
        )

        # Add instance using centralized utility
        project_name = getattr(self.schematic, "project_name", "circuit")
        add_symbol_instance(power_symbol, project_name, "/")

        # Add to schematic
        self.schematic.add_component(power_symbol)

        # Return connection point (typically at the pin)
        return Point(
            symbol_pos.x, symbol_pos.y + 2.54
        )  # Assuming pin is 2.54mm below symbol

    def _create_net_label(self, net_name: str, near_pos: Point) -> Point:
        """
        Create a net label.

        Args:
            net_name: Name of the net
            near_pos: Position to place near

        Returns:
            Position of the created label
        """
        # Calculate position - offset from pin
        offset = 5.0  # mm
        label_pos = Point(near_pos.x + offset, near_pos.y)

        # Snap to grid
        label_pos.x = round(label_pos.x / 2.54) * 2.54
        label_pos.y = round(label_pos.y / 2.54) * 2.54

        # Create label
        label = Label(text=net_name, position=label_pos, label_type=LabelType.LOCAL)

        # Add to schematic
        self.schematic.add_label(label)

        return label_pos

    def _find_nearest_label(
        self, net_name: str, pos: Point, max_distance: float = 50.0
    ) -> Optional[Label]:
        """
        Find the nearest label with the given net name.

        Args:
            net_name: Net name to search for
            pos: Position to search from
            max_distance: Maximum search distance in mm

        Returns:
            Nearest label or None
        """
        nearest_label = None
        min_distance = max_distance

        for label in self.schematic.labels:
            if label.text == net_name:
                distance = (
                    (label.position.x - pos.x) ** 2 + (label.position.y - pos.y) ** 2
                ) ** 0.5

                if distance < min_distance:
                    min_distance = distance
                    nearest_label = label

        return nearest_label

    def _needs_junction(self, point: Point) -> bool:
        """
        Check if a junction is needed at a point.

        A junction is needed when 3 or more wires meet.

        Args:
            point: Point to check

        Returns:
            True if junction is needed
        """
        # Count wires at this point
        wires_at_point = self.wire_manager._find_wires_at_point(point)

        # Need junction if 3 or more wires meet
        return len(wires_at_point) >= 3

    def update_net_connections(self, net_updates: List[Tuple[str, str, str]]):
        """
        Update multiple net connections.

        Args:
            net_updates: List of (component_ref, pin, net_name) tuples
        """
        # Group by component
        component_updates: Dict[str, Dict[str, str]] = {}

        for comp_ref, pin, net_name in net_updates:
            if comp_ref not in component_updates:
                component_updates[comp_ref] = {}
            component_updates[comp_ref][pin] = net_name

        # Update each component
        for comp_ref, pin_nets in component_updates.items():
            self.update_component_connections(comp_ref, pin_nets)

    def remove_floating_wires(self):
        """Remove any wires that are not connected to components."""
        # This would require component pin detection
        # For now, this is a placeholder
        pass

    def optimize_wire_routing(self):
        """Optimize existing wire routing for better appearance."""
        optimized_wires = []

        for wire in self.schematic.wires:
            # Optimize the path
            optimized_points = self.wire_router.optimize_path(wire.points)

            # Create new wire with optimized path
            if len(optimized_points) != len(wire.points):
                wire.points = optimized_points

            optimized_wires.append(wire)

        self.schematic.wires = optimized_wires
