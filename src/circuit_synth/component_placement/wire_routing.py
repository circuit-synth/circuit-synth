"""Wire routing for KiCad schematics.

This module handles the routing of wires between component pins.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple

from .placement import PlacementNode


@dataclass
class WireSegment:
    """Represents a wire segment in the schematic."""

    start: Tuple[float, float]
    end: Tuple[float, float]
    net_name: str
    connected_pins: List[Tuple[str, str]]  # List of (component_ref, pin_number)


class WireRouter:
    """Handles routing of wires between components."""

    def __init__(self):
        """Initialize the wire router."""
        self.wire_segments: List[WireSegment] = []

    def route_net(
        self, net: "Net", placement_nodes: Dict[str, PlacementNode]
    ) -> List[WireSegment]:
        """Route wires for a single net."""
        if len(net.pins) < 2:
            return []

        print(f"\nRouting net: {net.name}")
        print(f"Number of pins to connect: {len(net.pins)}")

        # Get component positions and pin locations
        connected_points = []
        for pin in net.pins:
            comp = pin.parent
            node = placement_nodes[comp.ref]

            # Get pin location relative to component center
            pin_loc = node.geometry_handler.get_pin_location(pin.number, node.rotation)
            if pin_loc:
                # Calculate absolute pin position
                abs_x = node.x + pin_loc[0]
                abs_y = node.y + pin_loc[1]
                print(f"Pin {pin.number} of {comp.ref}:")
                print(f"  Component center: ({node.x}, {node.y})")
                print(f"  Pin offset: ({pin_loc[0]}, {pin_loc[1]})")
                print(f"  Absolute pin position: ({abs_x}, {abs_y})")
                connected_points.append(((abs_x, abs_y), (comp.ref, pin.number)))

        # Sort points based on component type and position
        def sort_key(point_info):
            point, pin_info = point_info
            comp_ref = pin_info[0]
            node = placement_nodes[comp_ref]
            # Power components should be at their respective ends
            if node.component.library == "power":
                if "+3V3" in node.component.name:
                    return -float("inf")  # Place 3V3 at start
                elif "GND" in node.component.name:
                    return float("inf")  # Place GND at end
            return point[1]  # Sort other components by y-position

        connected_points.sort(key=sort_key)

        # Create wire segments
        segments = []
        for i in range(len(connected_points) - 1):
            start_point, start_pin = connected_points[i]
            end_point, end_pin = connected_points[i + 1]

            # For power connections, ensure proper direction
            if any(
                "power" == placement_nodes[pin[0]].component.library
                for pin in [start_pin, end_pin]
            ):
                # Get the power component's pin info
                power_pin = (
                    start_pin
                    if placement_nodes[start_pin[0]].component.library == "power"
                    else end_pin
                )
                comp_pin = (
                    end_pin
                    if placement_nodes[start_pin[0]].component.library == "power"
                    else start_pin
                )

                # Determine wire direction based on power type
                if "+3V3" in placement_nodes[power_pin[0]].component.name:
                    wire_start = start_point
                    wire_end = end_point
                else:  # GND
                    wire_start = end_point
                    wire_end = start_point

                segments.append(
                    WireSegment(
                        start=wire_start,
                        end=wire_end,
                        net_name=net.name,
                        connected_pins=[start_pin, end_pin],
                    )
                )
            # For component-to-component connections, use L-shaped path if needed
            else:
                # If points are vertically aligned (within tolerance)
                if abs(start_point[0] - end_point[0]) < 0.1:
                    segments.append(
                        WireSegment(
                            start=start_point,
                            end=end_point,
                            net_name=net.name,
                            connected_pins=[start_pin, end_pin],
                        )
                    )
                else:
                    print(
                        f"\nRouting between {start_pin[0]} pin {start_pin[1]} and {end_pin[0]} pin {end_pin[1]}"
                    )
                    print(f"Start point: ({start_point[0]}, {start_point[1]})")
                    print(f"End point: ({end_point[0]}, {end_point[1]})")

                    # Calculate midpoint between components for better routing
                    mid_y = (start_point[1] + end_point[1]) / 2
                    print(f"Using midpoint y={mid_y} for routing")

                    # Create vertical segments first, then horizontal
                    segments.extend(
                        [
                            # Vertical segment from start
                            WireSegment(
                                start=start_point,
                                end=(start_point[0], mid_y),
                                net_name=net.name,
                                connected_pins=[start_pin],
                            ),
                            # Horizontal segment
                            WireSegment(
                                start=(start_point[0], mid_y),
                                end=(end_point[0], mid_y),
                                net_name=net.name,
                                connected_pins=[],
                            ),
                            # Vertical segment to end
                            WireSegment(
                                start=(end_point[0], mid_y),
                                end=end_point,
                                net_name=net.name,
                                connected_pins=[end_pin],
                            ),
                        ]
                    )

        return segments
