"""Component placement strategies for KiCad schematics.

This module provides placement algorithms for organizing components in a schematic.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from .geometry import ComponentGeometryHandler, create_geometry_handler


@dataclass
class PlacementNode:
    """Represents a component's placement information."""

    component: "Component"
    x: float = 0
    y: float = 0
    rotation: float = 0
    placed: bool = False
    connected_components: Set["Component"] = None
    geometry_handler: Optional[ComponentGeometryHandler] = None

    def __post_init__(self):
        """Initialize after creation."""
        if self.connected_components is None:
            self.connected_components = set()
        if self.geometry_handler is None:
            self.geometry_handler = create_geometry_handler(
                self.component.name, self.component.library
            )


class ComponentPlacer:
    """Handles intelligent placement of components in a schematic."""

    def __init__(self, base_x: float = 77.47, base_y: float = 44.45):
        """Initialize the component placer."""
        self.base_x = base_x
        self.base_y = base_y
        self.spacing_x = 2.54  # Horizontal spacing between components
        self.spacing_y = 2.54  # Vertical spacing between components
        self.placement_nodes: Dict[str, PlacementNode] = {}
        self.occupied_positions: List[Tuple[float, float, float, float]] = []
        self.component_positions = {}

    def analyze_connectivity(self, circuit: "Circuit") -> None:
        """Build a connectivity graph from the circuit nets."""
        # Initialize placement nodes for each component
        self.placement_nodes = {
            comp.ref: PlacementNode(component=comp) for comp in circuit.components
        }

        # Analyze nets to build connectivity information
        for net in circuit.get_nets():
            connected_components = set()
            for pin in net.pins:
                connected_components.add(pin.parent)

            # Update connectivity information for each component
            for comp in connected_components:
                node = self.placement_nodes[comp.ref]
                node.connected_components.update(
                    c for c in connected_components if c != comp
                )

    def _check_collision(self, node: PlacementNode) -> bool:
        """Check if component would collide with any placed components."""
        bounds = node.geometry_handler.get_bounding_box(node.x, node.y, node.rotation)
        x1, y1, w1, h1 = bounds

        for x2, y2, w2, h2 in self.occupied_positions:
            # Check for overlap in both x and y
            if x1 < x2 + w2 and x1 + w1 > x2 and y1 < y2 + h2 and y1 + h1 > y2:
                return True
        return False

    def _find_non_colliding_position(self, node: PlacementNode) -> Tuple[float, float]:
        """Find a nearby position that doesn't collide with existing components."""
        original_x, original_y = node.x, node.y
        offset = self.spacing_x
        spiral = 1

        while True:
            # Try positions in a spiral pattern
            positions = [
                (original_x + offset, original_y),  # Right
                (original_x - offset, original_y),  # Left
                (original_x, original_y + offset),  # Down
                (original_x, original_y - offset),  # Up
            ]

            for new_x, new_y in positions:
                node.x, node.y = new_x, new_y
                if not self._check_collision(node):
                    return new_x, new_y

            offset += self.spacing_x
            spiral += 1
            if spiral > 10:  # Limit search to prevent infinite loops
                return original_x, original_y

    def _determine_component_rotation(
        self, node: PlacementNode, connected_to: List[Tuple["Component", str]]
    ) -> float:
        """Determine optimal component rotation based on connections."""
        comp = node.component

        if comp.library == "power":
            return 0  # Power symbols always upright

        # For resistors, determine rotation based on connections
        if comp.name == "R":
            # Check for power connections first
            power_connections = [c for c, _ in connected_to if c.library == "power"]
            if power_connections:
                if any("+3V3" in c.name for c in power_connections):
                    return 180  # Pin 1 faces up to 3V3
                elif any("GND" in c.name for c in power_connections):
                    return 0  # Pin 2 faces down to GND

            # For resistors in series, alternate orientations
            resistor_connections = [(c, p) for c, p in connected_to if c.name == "R"]
            if resistor_connections:
                # Get the connected resistor's reference number
                connected_ref_num = int(
                    next(c.ref.replace("R", "") for c, _ in resistor_connections)
                )
                # Get current resistor's reference number
                current_ref_num = int(comp.ref.replace("R", ""))
                # Alternate orientation based on position in chain
                return 180 if current_ref_num % 2 == 1 else 0

        return 180  # Default to pin 1 up

    def place_components(
        self, circuit: "Circuit"
    ) -> Dict[str, Tuple[float, float, float]]:
        """Place all components in the circuit and return their positions."""
        self.analyze_connectivity(circuit)
        self.occupied_positions = []

        # First pass: determine rotations and initial positions
        placed_components = {}

        # Group components by their connections
        net_groups = {}
        for net in circuit.get_nets():
            connected = []
            for pin in net.pins:
                connected.append((pin.parent, pin.number))
            for comp, pin in connected:
                if comp.ref not in net_groups:
                    net_groups[comp.ref] = []
                net_groups[comp.ref].extend((c, p) for c, p in connected if c != comp)

        # Sort components by reference designator
        sorted_components = sorted(
            [comp for comp in circuit.components if comp.library != "power"],
            key=lambda x: (x.name, int(x.ref.replace(x.name, ""))),
        )

        # Place non-power components first
        y_offset = 0
        for comp in sorted_components:
            node = self.placement_nodes[comp.ref]
            connected_to = net_groups.get(comp.ref, [])

            # Determine rotation
            rotation = self._determine_component_rotation(node, connected_to)
            node.rotation = rotation

            # Place component
            node.x = self.base_x
            node.y = self.base_y + y_offset
            print(f"\nPlacing {comp.ref} at initial position ({node.x}, {node.y})")
            print(f"Component dimensions: {node.geometry_handler._dimensions}")
            print(f"Rotation: {rotation} degrees")

            # Check for collisions and adjust if needed
            if self._check_collision(node):
                print(f"Collision detected for {comp.ref}, finding new position...")
                node.x, node.y = self._find_non_colliding_position(node)
                print(f"New position for {comp.ref}: ({node.x}, {node.y})")

            # Update placement info
            node.placed = True
            placed_components[comp.ref] = (node.x, node.y, node.rotation)

            # Add to occupied positions
            bounds = node.geometry_handler.get_bounding_box(
                node.x, node.y, node.rotation
            )
            self.occupied_positions.append(bounds)

            # Increment y offset for next component
            y_offset += self.spacing_y + node.geometry_handler._dimensions.height

        # Then place power components
        for comp in circuit.components:
            if comp.library == "power":
                node = self.placement_nodes[comp.ref]
                connected_to = net_groups.get(comp.ref, [])

                # Find the component this power symbol connects to
                connected_comp = next(
                    (c for c, _ in connected_to if c.library != "power"), None
                )
                if connected_comp and connected_comp.ref in placed_components:
                    comp_pos = placed_components[connected_comp.ref]
                    pin_number = next(p for c, p in connected_to if c == connected_comp)

                    # Get connected component's geometry handler
                    connected_node = self.placement_nodes[connected_comp.ref]

                    # Calculate position relative to the connected component's pin
                    pin_loc = connected_node.geometry_handler.get_pin_location(
                        pin_number, comp_pos[2]
                    )
                    if pin_loc:
                        # Calculate absolute pin position of connected component
                        abs_pin_x = comp_pos[0] + pin_loc[0]
                        abs_pin_y = comp_pos[1] + pin_loc[1]

                        print(f"\nPlacing power component {comp.ref}")
                        print(f"Connected to {connected_comp.ref} at pin {pin_number}")
                        print(f"Connected component pin at: ({abs_pin_x}, {abs_pin_y})")

                        # Get power component's pin offset
                        power_pin_loc = node.geometry_handler.get_pin_location("1", 0)
                        print(f"Power component pin offset: {power_pin_loc}")

                        # Place power component so its pin aligns with component pin
                        x = abs_pin_x
                        if "+3V3" in comp.name:
                            y = (
                                abs_pin_y - power_pin_loc[1]
                            )  # Align power pin with component pin
                            print(
                                f"Placing 3V3 at y={y} to align with pin at y={abs_pin_y}"
                            )
                        else:  # GND
                            y = (
                                abs_pin_y - power_pin_loc[1]
                            )  # Align power pin with component pin
                            print(
                                f"Placing GND at y={y} to align with pin at y={abs_pin_y}"
                            )

                        node.x = x
                        node.y = y
                        node.rotation = 0
                        node.placed = True

                        placed_components[comp.ref] = (x, y, 0)
                        bounds = node.geometry_handler.get_bounding_box(x, y, 0)
                        self.occupied_positions.append(bounds)

        # Store positions for wire routing
        self.component_positions = placed_components

        return placed_components
