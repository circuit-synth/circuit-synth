"""
Ratsnest Generation for PCB Design

This module generates ratsnest (airwire) connections between pads on the same net,
providing visual representation of unrouted connections in KiCad PCB files.
"""

import logging
import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


@dataclass
class PadInfo:
    """Information about a pad for ratsnest calculations."""

    reference: str
    pad_number: str
    net_number: int
    net_name: str
    position: Tuple[float, float]
    layer: str


@dataclass
class RatsnestConnection:
    """Represents a ratsnest connection between two pads."""

    from_pad: PadInfo
    to_pad: PadInfo
    length: float
    net_number: int
    net_name: str


class RatsnestGenerator:
    """
    Generates ratsnest connections for PCB designs.

    The ratsnest shows unrouted connections between pads that belong to the
    same net, helping designers understand the required routing topology.
    """

    def __init__(self):
        """Initialize the ratsnest generator."""
        self.connections: List[RatsnestConnection] = []
        self.pad_positions: Dict[int, List[PadInfo]] = defaultdict(list)

    def extract_pad_info(self, pcb_data: Dict[str, Any]) -> Dict[int, List[PadInfo]]:
        """
        Extract pad information from PCB data.

        Args:
            pcb_data: PCB data structure containing footprints

        Returns:
            Dictionary mapping net numbers to lists of PadInfo objects
        """
        pad_positions = defaultdict(list)

        # Extract footprints from the PCB data
        footprints = pcb_data.get("footprints", [])

        for footprint in footprints:
            ref = getattr(footprint, "reference", "Unknown")
            fp_position = getattr(footprint, "position", None)

            if fp_position is None:
                logger.warning(f"Footprint {ref} has no position, skipping")
                continue

            # Get footprint position
            fp_x = getattr(fp_position, "x", 0.0)
            fp_y = getattr(fp_position, "y", 0.0)

            # Process each pad in the footprint
            pads = getattr(footprint, "pads", [])
            for pad in pads:
                pad_number = getattr(pad, "number", "")
                net_number = getattr(pad, "net", 0)
                net_name = getattr(pad, "net_name", "")

                # Skip unconnected pads (net 0)
                if net_number == 0:
                    continue

                # Calculate absolute pad position
                pad_pos = getattr(pad, "at", None)
                if pad_pos:
                    # Pad position is relative to footprint
                    if hasattr(pad_pos, "x") and hasattr(pad_pos, "y"):
                        pad_x = fp_x + pad_pos.x
                        pad_y = fp_y + pad_pos.y
                    else:
                        # Handle list format [x, y, rotation]
                        pad_x = fp_x + pad_pos[0] if len(pad_pos) > 0 else fp_x
                        pad_y = fp_y + pad_pos[1] if len(pad_pos) > 1 else fp_y
                else:
                    # No pad offset, use footprint position
                    pad_x = fp_x
                    pad_y = fp_y

                # Get pad layer
                layers = getattr(pad, "layers", ["F.Cu"])
                primary_layer = layers[0] if layers else "F.Cu"

                pad_info = PadInfo(
                    reference=ref,
                    pad_number=pad_number,
                    net_number=net_number,
                    net_name=net_name,
                    position=(pad_x, pad_y),
                    layer=primary_layer,
                )

                pad_positions[net_number].append(pad_info)
                logger.debug(
                    f"Added pad {ref}.{pad_number} at ({pad_x:.2f}, {pad_y:.2f}) on net {net_number} ({net_name})"
                )

        return pad_positions

    def calculate_distance(
        self, pos1: Tuple[float, float], pos2: Tuple[float, float]
    ) -> float:
        """Calculate Euclidean distance between two positions."""
        dx = pos1[0] - pos2[0]
        dy = pos1[1] - pos2[1]
        return math.sqrt(dx * dx + dy * dy)

    def generate_minimum_spanning_tree(
        self, pads: List[PadInfo]
    ) -> List[RatsnestConnection]:
        """
        Generate minimum spanning tree connections for pads on the same net.

        Uses Prim's algorithm to create the most efficient ratsnest topology.

        Args:
            pads: List of pads on the same net

        Returns:
            List of ratsnest connections forming a minimum spanning tree
        """
        if len(pads) < 2:
            return []

        connections = []
        connected = {0}  # Start with first pad
        unconnected = set(range(1, len(pads)))

        while unconnected:
            min_distance = float("inf")
            best_connection = None

            # Find shortest connection between connected and unconnected pads
            for connected_idx in connected:
                for unconnected_idx in unconnected:
                    distance = self.calculate_distance(
                        pads[connected_idx].position, pads[unconnected_idx].position
                    )

                    if distance < min_distance:
                        min_distance = distance
                        best_connection = (connected_idx, unconnected_idx)

            if best_connection:
                from_idx, to_idx = best_connection
                connection = RatsnestConnection(
                    from_pad=pads[from_idx],
                    to_pad=pads[to_idx],
                    length=min_distance,
                    net_number=pads[from_idx].net_number,
                    net_name=pads[from_idx].net_name,
                )
                connections.append(connection)

                # Move pad from unconnected to connected
                connected.add(to_idx)
                unconnected.remove(to_idx)

        return connections

    def generate_star_topology(self, pads: List[PadInfo]) -> List[RatsnestConnection]:
        """
        Generate star topology connections (all pads connect to first pad).

        Args:
            pads: List of pads on the same net

        Returns:
            List of ratsnest connections in star topology
        """
        if len(pads) < 2:
            return []

        connections = []
        center_pad = pads[0]

        for i in range(1, len(pads)):
            distance = self.calculate_distance(center_pad.position, pads[i].position)

            connection = RatsnestConnection(
                from_pad=center_pad,
                to_pad=pads[i],
                length=distance,
                net_number=center_pad.net_number,
                net_name=center_pad.net_name,
            )
            connections.append(connection)

        return connections

    def generate_ratsnest(
        self, pcb_data: Dict[str, Any], topology: str = "mst"
    ) -> List[RatsnestConnection]:
        """
        Generate ratsnest connections for all nets in the PCB.

        Args:
            pcb_data: PCB data structure
            topology: Ratsnest topology ("mst" for minimum spanning tree, "star" for star)

        Returns:
            List of all ratsnest connections
        """
        logger.info(f"Generating ratsnest with {topology} topology")

        # Extract pad positions grouped by net
        pad_positions = self.extract_pad_info(pcb_data)

        all_connections = []
        net_count = 0

        for net_number, pads in pad_positions.items():
            if len(pads) < 2:
                continue  # Skip nets with less than 2 pads

            if topology == "mst":
                connections = self.generate_minimum_spanning_tree(pads)
            elif topology == "star":
                connections = self.generate_star_topology(pads)
            else:
                logger.warning(f"Unknown topology '{topology}', using MST")
                connections = self.generate_minimum_spanning_tree(pads)

            all_connections.extend(connections)
            net_count += 1

            logger.debug(
                f"Net {net_number} ({pads[0].net_name}): {len(pads)} pads, {len(connections)} connections"
            )

        logger.info(
            f"Generated {len(all_connections)} ratsnest connections across {net_count} nets"
        )
        self.connections = all_connections
        return all_connections

    def generate_kicad_ratsnest_elements(
        self, connections: Optional[List[RatsnestConnection]] = None
    ) -> List[str]:
        """
        Generate KiCad S-expression ratsnest elements.

        Note: KiCad doesn't typically store ratsnest in the PCB file - they are
        generated dynamically. This method creates visual lines for reference.

        Args:
            connections: List of ratsnest connections (uses internal if None)

        Returns:
            List of S-expression strings for ratsnest visualization
        """
        if connections is None:
            connections = self.connections

        ratsnest_elements = []

        for connection in connections:
            # Create a line element to represent the ratsnest connection
            # Using a thin line on a technical layer for visualization
            from_x, from_y = connection.from_pad.position
            to_x, to_y = connection.to_pad.position

            line_element = f"""(gr_line
    (start {from_x:.4f} {from_y:.4f})
    (end {to_x:.4f} {to_y:.4f})
    (stroke (width 0.05) (type dash))
    (layer "Dwgs.User")
    (uuid "{self._generate_uuid()}")
)"""
            ratsnest_elements.append(line_element)

        return ratsnest_elements

    def _generate_uuid(self) -> str:
        """Generate a UUID for PCB elements."""
        import uuid

        return str(uuid.uuid4())

    def add_ratsnest_to_pcb(
        self,
        pcb_data: Dict[str, Any],
        topology: str = "mst",
        layer: str = "Dwgs.User",
        line_width: float = 0.05,
    ) -> int:
        """
        Add ratsnest visualization directly to PCB data structure.

        Args:
            pcb_data: PCB data structure to modify
            topology: Ratsnest topology ("mst" or "star")
            layer: Layer to place ratsnest lines on
            line_width: Width of ratsnest lines

        Returns:
            Number of ratsnest connections added
        """
        # Generate ratsnest connections
        connections = self.generate_ratsnest(pcb_data, topology)

        if not connections:
            logger.warning("No ratsnest connections generated")
            return 0

        # Ensure graphics list exists
        if "graphics" not in pcb_data:
            pcb_data["graphics"] = []

        # Add ratsnest lines as graphics elements
        for connection in connections:
            from_x, from_y = connection.from_pad.position
            to_x, to_y = connection.to_pad.position

            # Create line graphic element
            line_graphic = {
                "type": "gr_line",
                "start": {"x": from_x, "y": from_y},
                "end": {"x": to_x, "y": to_y},
                "stroke": {"width": line_width, "type": "dash"},
                "layer": layer,
                "uuid": self._generate_uuid(),
            }

            pcb_data["graphics"].append(line_graphic)

        logger.info(
            f"Added {len(connections)} ratsnest connections to PCB on layer '{layer}'"
        )
        return len(connections)

    def export_ratsnest_report(
        self, connections: Optional[List[RatsnestConnection]] = None
    ) -> str:
        """
        Export a text report of ratsnest connections.

        Args:
            connections: List of connections to report (uses internal if None)

        Returns:
            Formatted text report
        """
        if connections is None:
            connections = self.connections

        if not connections:
            return "No ratsnest connections found.\n"

        report = ["Ratsnest Connection Report", "=" * 30, ""]

        # Group by net
        by_net = defaultdict(list)
        for conn in connections:
            by_net[conn.net_number].append(conn)

        for net_num in sorted(by_net.keys()):
            net_connections = by_net[net_num]
            net_name = net_connections[0].net_name

            report.append(f"Net {net_num} ({net_name}):")

            total_length = 0
            for i, conn in enumerate(net_connections, 1):
                from_ref = f"{conn.from_pad.reference}.{conn.from_pad.pad_number}"
                to_ref = f"{conn.to_pad.reference}.{conn.to_pad.pad_number}"

                report.append(f"  {i}. {from_ref} -> {to_ref} ({conn.length:.2f}mm)")
                total_length += conn.length

            report.append(f"  Total length: {total_length:.2f}mm")
            report.append("")

        overall_length = sum(conn.length for conn in connections)
        report.append(f"Overall ratsnest length: {overall_length:.2f}mm")
        report.append(f"Total connections: {len(connections)}")

        return "\n".join(report)


def generate_pcb_ratsnest(
    pcb_file: str, output_file: Optional[str] = None, topology: str = "mst"
) -> List[RatsnestConnection]:
    """
    Convenience function to generate ratsnest for a PCB file.

    Args:
        pcb_file: Path to input PCB file
        output_file: Optional path to save modified PCB file
        topology: Ratsnest topology ("mst" or "star")

    Returns:
        List of ratsnest connections
    """
    from .pcb_formatter import PCBFormatter
    from .pcb_parser import PCBParser

    # Load PCB
    parser = PCBParser()
    pcb_data = parser.parse_file(pcb_file)

    # Generate ratsnest
    generator = RatsnestGenerator()
    connections = generator.add_ratsnest_to_pcb(pcb_data, topology)

    # Save modified PCB if requested
    if output_file:
        from .pcb_formatter import PCBFormatter

        formatter = PCBFormatter()

        # Convert PCB data to S-expression and format it
        formatted_pcb = formatter.format_pcb(pcb_data)

        # Write to file
        with open(output_file, "w") as f:
            f.write(formatted_pcb)
        logger.info(f"Saved PCB with ratsnest to {output_file}")

    return generator.connections
