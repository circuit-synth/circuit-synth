"""
SES (Specctra Session) importer for KiCad PCB files.

This module provides functionality to import routed boards from Freerouting
back into KiCad PCB format by parsing SES files and applying the routing
to the original PCB.
"""

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..pcb_parser import PCBParser
from ..types import Point, Track, Via

logger = logging.getLogger(__name__)


@dataclass
class Wire:
    """Represents a routed wire segment."""

    net_name: str
    layer: str
    width: float
    points: List[Tuple[float, float]]
    wire_type: str = "route"  # route, protect, fix


@dataclass
class SESVia:
    """Represents a via from SES file."""

    net_name: str
    position: Tuple[float, float]
    padstack: str
    layers: List[str] = field(default_factory=list)


@dataclass
class RoutingSession:
    """Contains all routing data from a SES file."""

    wires: List[Wire] = field(default_factory=list)
    vias: List[SESVia] = field(default_factory=list)
    resolution: float = 1.0
    unit: str = "mm"

    def add_wire(self, wire: Wire):
        """Add a wire to the session."""
        self.wires.append(wire)

    def add_via(self, via: SESVia):
        """Add a via to the session."""
        self.vias.append(via)


class SESParser:
    """Parser for Specctra Session (SES) files."""

    def __init__(self, ses_file: str):
        """
        Initialize the SES parser.

        Args:
            ses_file: Path to the SES file
        """
        self.ses_file = Path(ses_file)
        self.content = ""
        self.position = 0
        self.session = RoutingSession()
        self.layer_map = {}  # Map SES layer names to KiCad layer names

    def parse(self) -> RoutingSession:
        """
        Parse the SES file and return routing session data.

        Returns:
            RoutingSession object containing all routing data
        """
        logger.info(f"Parsing SES file: {self.ses_file}")

        # Read file content
        with open(self.ses_file, "r", encoding="utf-8") as f:
            self.content = f.read()

        # Remove comments
        self.content = re.sub(r"#.*$", "", self.content, flags=re.MULTILINE)

        # Parse main session block
        self._parse_session()

        logger.info(
            f"Parsed {len(self.session.wires)} wires and {len(self.session.vias)} vias"
        )
        return self.session

    def _parse_session(self):
        """Parse the main session block."""
        # Find session block - handle both quoted and unquoted session names
        session_match = re.search(r'\(session\s+(?:"[^"]*"|\S+)', self.content)
        if not session_match:
            raise ValueError("No session block found in SES file")

        # Parse resolution
        self._parse_resolution()

        # Parse routes
        self._parse_routes()

        # Parse vias
        self._parse_vias()

    def _parse_resolution(self):
        """Parse resolution and units."""
        # Look for resolution block
        res_match = re.search(r"\(resolution\s+(\w+)\s+([\d.]+)\)", self.content)
        if res_match:
            self.session.unit = res_match.group(1)
            self.session.resolution = float(res_match.group(2))
            logger.debug(f"Resolution: {self.session.resolution} {self.session.unit}")

    def _parse_routes(self):
        """Parse all route blocks."""
        logger.info("=== Starting SES route parsing ===")

        # Find routes block
        routes_match = re.search(r"\(routes\s*(.*)\)\s*\)", self.content, re.DOTALL)
        if not routes_match:
            logger.warning("No routes block found")
            return

        routes_content = routes_match.group(1)
        logger.debug(f"Found routes block with {len(routes_content)} characters")

        # Look for network_out block first (Freerouting format)
        # Use manual extraction to ensure we get the complete content
        network_out_start = re.search(r"\(network_out\s*", routes_content)
        if network_out_start:
            start_pos = network_out_start.end()
            paren_count = 1
            i = start_pos

            while i < len(routes_content) and paren_count > 0:
                if routes_content[i] == "(":
                    paren_count += 1
                elif routes_content[i] == ")":
                    paren_count -= 1
                i += 1

            if paren_count == 0:
                network_content = routes_content[start_pos : i - 1]
            else:
                # Fallback to regex if manual extraction fails
                network_out_match = re.search(
                    r"\(network_out\s*(.*)\)\s*\)", routes_content, re.DOTALL
                )
                if network_out_match:
                    network_content = network_out_match.group(1)
                else:
                    logger.warning("No network_out block found")
                    return
            # Parse net blocks within network_out
            logger.info("Parsing nets from network_out block")
            pos = 0
            net_count = 0
            while True:
                # Handle both quoted and unquoted net names
                net_match = re.search(
                    r'\(net\s+(?:"([^"]+)"|(\S+))', network_content[pos:]
                )
                if not net_match:
                    break

                # Get the net name from whichever group matched
                net_name = (
                    net_match.group(1) if net_match.group(1) else net_match.group(2)
                )
                start_pos = pos + net_match.start()
                logger.info(f"Found net: '{net_name}'")
                net_count += 1

                # Find the matching closing parenthesis
                paren_count = 1
                i = pos + net_match.end()
                net_start = i
                while i < len(network_content) and paren_count > 0:
                    if network_content[i] == "(":
                        paren_count += 1
                    elif network_content[i] == ")":
                        paren_count -= 1
                    i += 1

                if paren_count == 0:
                    net_content = network_content[net_start : i - 1]
                    self._parse_network_routes(net_name, net_content)

                pos = i
            logger.info(f"=== Parsed {net_count} nets from network_out ===")
        else:
            # Fall back to looking for individual network blocks
            pos = 0
            net_count = 0
            while True:
                network_match = re.search(
                    r'\(network\s+"([^"]+)"', routes_content[pos:]
                )
                if not network_match:
                    break

                net_name = network_match.group(1)
                start_pos = pos + network_match.start()

                # Find the matching closing parenthesis
                paren_count = 1
                i = pos + network_match.end()
                net_start = i
                while i < len(routes_content) and paren_count > 0:
                    if routes_content[i] == "(":
                        paren_count += 1
                    elif routes_content[i] == ")":
                        paren_count -= 1
                    i += 1

                if paren_count == 0:
                    net_content = routes_content[net_start : i - 1]
                    self._parse_network_routes(net_name, net_content)
                    net_count += 1

                pos = i

            logger.info(
                f"=== Parsed {net_count} nets from individual network blocks ==="
            )

    def _parse_network_routes(self, net_name: str, content: str):
        """Parse routes for a specific network."""
        logger.debug(f"Parsing routes for net '{net_name}'")

        # Parse wire segments - handle both path and protect types
        # Also handle optional (type ...) element that Freerouting adds

        # Pattern for path wires
        path_pattern = r"\(wire\s*\(path\s+([^\s]+)\s+([\d.]+)((?:\s+[\d.-]+\s+[\d.-]+)+)\s*\)(?:\s*\(type\s+\w+\))?\s*\)"

        # Pattern for protected wires
        protect_pattern = r"\(wire\s*\(protect\s+([^\s]+)\s+([\d.]+)((?:\s+[\d.-]+\s+[\d.-]+)+)\s*\)\s*\)"

        wire_count = 0

        # Parse path wires
        for match in re.finditer(path_pattern, content, re.DOTALL):
            layer = match.group(1)
            width = float(match.group(2)) / self.session.resolution
            coords_str = match.group(3)

            # Parse coordinates
            coords = []
            coord_pairs = re.findall(r"([\d.-]+)\s+([\d.-]+)", coords_str)
            for x, y in coord_pairs:
                coords.append(
                    (
                        float(x) / self.session.resolution,
                        float(y) / self.session.resolution,
                    )
                )

            if len(coords) >= 2:
                wire = Wire(
                    net_name=net_name,
                    layer=layer,
                    width=width,
                    points=coords,
                    wire_type="path",
                )
                self.session.add_wire(wire)
                wire_count += 1
                logger.debug(
                    f"  Added path wire {wire_count} on layer {layer}: {len(coords)} points, width={width}"
                )

        # Parse protected wires
        for match in re.finditer(protect_pattern, content, re.DOTALL):
            layer = match.group(1)
            width = float(match.group(2)) / self.session.resolution
            coords_str = match.group(3)

            # Parse coordinates
            coords = []
            coord_pairs = re.findall(r"([\d.-]+)\s+([\d.-]+)", coords_str)
            for x, y in coord_pairs:
                coords.append(
                    (
                        float(x) / self.session.resolution,
                        float(y) / self.session.resolution,
                    )
                )

            if len(coords) >= 2:
                wire = Wire(
                    net_name=net_name,
                    layer=layer,
                    width=width,
                    points=coords,
                    wire_type="protect",
                )
                self.session.add_wire(wire)
                wire_count += 1
                logger.debug(
                    f"  Added protected wire {wire_count} on layer {layer}: {len(coords)} points, width={width}"
                )

        logger.info(f"  Found {wire_count} wires for net '{net_name}'")

    def _parse_vias(self):
        """Parse all via blocks."""
        # Find vias in routes
        via_pattern = r'\(via\s+"([^"]+)"\s+([\d.-]+)\s+([\d.-]+)\s*\)'

        for match in re.finditer(via_pattern, self.content):
            padstack = match.group(1)
            x = float(match.group(2)) / self.session.resolution
            y = float(match.group(3)) / self.session.resolution

            # Try to find the net name from context
            # Look backwards for the nearest network declaration
            pos = match.start()
            net_search = self.content[:pos]
            net_match = re.findall(r'\(network\s+"([^"]+)"', net_search)
            net_name = net_match[-1] if net_match else ""

            via = SESVia(net_name=net_name, position=(x, y), padstack=padstack)
            self.session.add_via(via)


class SESImporter:
    """Imports SES routing data into KiCad PCB files."""

    # KiCad layer mapping
    LAYER_MAP = {
        "F.Cu": "F.Cu",
        "B.Cu": "B.Cu",
        "In1.Cu": "In1.Cu",
        "In2.Cu": "In2.Cu",
        "In3.Cu": "In3.Cu",
        "In4.Cu": "In4.Cu",
        "front": "F.Cu",
        "back": "B.Cu",
        "signal1": "In1.Cu",
        "signal2": "In2.Cu",
        "signal3": "In3.Cu",
        "signal4": "In4.Cu",
        "0": "F.Cu",
        "31": "B.Cu",
        "1": "In1.Cu",
        "2": "In2.Cu",
        "3": "In3.Cu",
        "4": "In4.Cu",
    }

    def __init__(self, pcb_file: str, ses_file: str):
        """
        Initialize the SES importer.

        Args:
            pcb_file: Path to the original KiCad PCB file
            ses_file: Path to the SES file with routing data
        """
        self.pcb_file = Path(pcb_file)
        self.ses_file = Path(ses_file)
        self.parser = PCBParser()
        self.board = None
        self.net_map = {}  # Map net names to net codes

    def import_routing(self, output_file: Optional[str] = None) -> str:
        """
        Import routing from SES file into PCB.

        Args:
            output_file: Output PCB file path (defaults to input with _routed suffix)

        Returns:
            Path to the output PCB file
        """
        logger.info(f"Importing routing from {self.ses_file} to {self.pcb_file}")

        # Parse PCB file
        self.board = self.parser.parse_file(self.pcb_file)

        # Build net name to code mapping
        self._build_net_map()

        # Remove existing tracks and vias
        self._remove_existing_routing()

        # Parse SES file
        ses_parser = SESParser(str(self.ses_file))
        session = ses_parser.parse()

        # Import wires as tracks
        self._import_wires(session.wires)

        # Import vias
        self._import_vias(session.vias)

        # Write output file
        if not output_file:
            output_file = str(self.pcb_file.with_stem(f"{self.pcb_file.stem}_routed"))

        self.parser.write_file(self.board, output_file)

        logger.info(f"Routing imported successfully to {output_file}")
        return output_file

    def _build_net_map(self):
        """Build mapping from net names to net codes."""
        self.net_map = {}

        # Find all nets in the board
        nets = self.board.get("nets", [])
        for net in nets:
            if hasattr(net, "number") and hasattr(net, "name"):
                net_code = net.number
                net_name = net.name
            else:
                # Handle dictionary format
                net_code = net.get("number", 0)
                net_name = net.get("name", "")

            if net_name:
                self.net_map[net_name] = net_code
                # Also map without quotes
                self.net_map[net_name.strip('"')] = net_code

        logger.debug(f"Built net map with {len(self.net_map)} nets")

    def _remove_existing_routing(self):
        """Remove existing tracks and vias from the board."""
        # Clear tracks list
        self.board["tracks"] = []

        # Clear vias list
        self.board["vias"] = []

        logger.debug("Removed existing routing")

    def _import_wires(self, wires: List[Wire]):
        """Import wires as PCB tracks."""
        tracks = []

        for wire in wires:
            # Get net code - try with and without quotes
            net_name = wire.net_name.strip('"')
            net_code = self.net_map.get(net_name, 0)
            if net_code == 0:
                # Try with the original name (with quotes if present)
                net_code = self.net_map.get(wire.net_name, 0)
            if net_code == 0:
                logger.warning(f"Unknown net: {wire.net_name}")
                continue

            # Map layer name
            layer = self.LAYER_MAP.get(wire.layer, wire.layer)

            # Create tracks for each pair of points
            for i in range(len(wire.points) - 1):
                start = wire.points[i]
                end = wire.points[i + 1]

                # The coordinates from the parser are in micrometers after dividing by resolution
                # Convert from micrometers to nanometers (KiCad's internal units)
                track = Track(
                    start=Point(start[0] * 1000, start[1] * 1000),
                    end=Point(end[0] * 1000, end[1] * 1000),
                    width=wire.width * 1000,
                    layer=layer,
                    net=net_code,
                    net_name=wire.net_name,
                )

                tracks.append(track)

        # Add tracks to board
        if tracks:
            self.board["tracks"].extend(tracks)
            logger.info(f"Imported {len(tracks)} track segments")

    def _import_vias(self, vias: List[SESVia]):
        """Import vias into the PCB."""
        pcb_vias = []

        for via in vias:
            # Get net code - try with and without quotes
            net_name = via.net_name.strip('"')
            net_code = self.net_map.get(net_name, 0)
            if net_code == 0:
                # Try with the original name (with quotes if present)
                net_code = self.net_map.get(via.net_name, 0)
            if net_code == 0:
                logger.warning(f"Unknown net for via: {via.net_name}")
                continue

            # Parse padstack for via size
            # Common padstack formats: "Via[0-1]_800:400_um"
            size = 0.8  # Default 0.8mm
            drill = 0.4  # Default 0.4mm

            padstack_match = re.search(r"(\d+):(\d+)", via.padstack)
            if padstack_match:
                size = float(padstack_match.group(1)) / 1000.0  # Convert to mm
                drill = float(padstack_match.group(2)) / 1000.0

            # The coordinates from the parser are in micrometers after dividing by resolution
            # Convert from micrometers to nanometers (KiCad's internal units)
            pcb_via = Via(
                position=Point(via.position[0] * 1000, via.position[1] * 1000),
                size=size * 1000,
                drill=drill * 1000,
                layers=["F.Cu", "B.Cu"],  # Default to through via
                net=net_code,
            )

            pcb_vias.append(pcb_via)

        # Add vias to board
        if pcb_vias:
            self.board["vias"].extend(pcb_vias)
            logger.info(f"Imported {len(pcb_vias)} vias")


def import_ses_to_pcb(
    pcb_file: str, ses_file: str, output_file: Optional[str] = None
) -> str:
    """
    Import SES routing data into a KiCad PCB file.

    Args:
        pcb_file: Path to the original KiCad PCB file
        ses_file: Path to the SES file with routing data
        output_file: Output PCB file path (optional)

    Returns:
        Path to the output PCB file
    """
    importer = SESImporter(pcb_file, ses_file)
    return importer.import_routing(output_file)
