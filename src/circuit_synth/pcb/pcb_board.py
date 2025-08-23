"""
Main PCB board class providing a simple API for PCB manipulation.
"""

import logging
import uuid as uuid_module
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from .footprint_library import FootprintInfo, get_footprint_cache
from .pcb_parser import PCBParser
from .types import (
    Arc,
    Footprint,
    Line,
    Net,
    Pad,
    Point,
    Property,
    Rectangle,
    Text,
    Track,
    Via,
    Zone,
)
from .validation import PCBValidator, ValidationResult

logger = logging.getLogger(__name__)


class PCBBoard:
    """
    High-level API for creating and manipulating KiCad PCB files.

    Provides simple methods for common PCB operations like adding,
    moving, and removing footprints.
    """

    def __init__(self, filepath: Optional[Union[str, Path]] = None):
        """
        Initialize a PCB board.

        Args:
            filepath: Optional path to load an existing PCB file
        """
        self.parser = PCBParser()
        self.pcb_data = self._create_empty_pcb()
        self._filepath = None

        if filepath:
            self.load(filepath)

    def _create_empty_pcb(self) -> Dict[str, Any]:
        """Create an empty PCB data structure with minimal required elements."""
        return {
            "version": 20241229,  # KiCad 9 version
            "generator": "pcbnew",
            "generator_version": "9.0",
            "general": {"thickness": 1.6, "legacy_teardrops": False},
            "paper": "A4",
            "layers": self._get_default_layers(),
            "setup": self._get_default_setup(),
            "nets": [Net(0, "")],  # Net 0 is always unconnected
            "footprints": [],
            "vias": [],
            "tracks": [],
            "zones": [],
            "groups": [],
            "embedded_fonts": False,
        }

    def _get_default_layers(self) -> List[Dict[str, Any]]:
        """Get default layer stack for a 2-layer board."""
        return [
            {"number": 0, "canonical_name": "F.Cu", "type": "signal"},
            {"number": 2, "canonical_name": "B.Cu", "type": "signal"},
            {
                "number": 9,
                "canonical_name": "F.Adhes",
                "type": "user",
                "user_name": "F.Adhesive",
            },
            {
                "number": 11,
                "canonical_name": "B.Adhes",
                "type": "user",
                "user_name": "B.Adhesive",
            },
            {"number": 13, "canonical_name": "F.Paste", "type": "user"},
            {"number": 15, "canonical_name": "B.Paste", "type": "user"},
            {
                "number": 5,
                "canonical_name": "F.SilkS",
                "type": "user",
                "user_name": "F.Silkscreen",
            },
            {
                "number": 7,
                "canonical_name": "B.SilkS",
                "type": "user",
                "user_name": "B.Silkscreen",
            },
            {"number": 1, "canonical_name": "F.Mask", "type": "user"},
            {"number": 3, "canonical_name": "B.Mask", "type": "user"},
            {
                "number": 17,
                "canonical_name": "Dwgs.User",
                "type": "user",
                "user_name": "User.Drawings",
            },
            {
                "number": 19,
                "canonical_name": "Cmts.User",
                "type": "user",
                "user_name": "User.Comments",
            },
            {
                "number": 21,
                "canonical_name": "Eco1.User",
                "type": "user",
                "user_name": "User.Eco1",
            },
            {
                "number": 23,
                "canonical_name": "Eco2.User",
                "type": "user",
                "user_name": "User.Eco2",
            },
            {"number": 25, "canonical_name": "Edge.Cuts", "type": "user"},
            {"number": 27, "canonical_name": "Margin", "type": "user"},
            {
                "number": 31,
                "canonical_name": "F.CrtYd",
                "type": "user",
                "user_name": "F.Courtyard",
            },
            {
                "number": 29,
                "canonical_name": "B.CrtYd",
                "type": "user",
                "user_name": "B.Courtyard",
            },
            {"number": 35, "canonical_name": "F.Fab", "type": "user"},
            {"number": 33, "canonical_name": "B.Fab", "type": "user"},
        ]

    def _get_default_setup(self) -> List:
        """Get default setup section."""
        import sexpdata

        # Return a minimal setup section as S-expression
        return [
            sexpdata.Symbol("setup"),
            [sexpdata.Symbol("pad_to_mask_clearance"), 0],
            [
                sexpdata.Symbol("allow_soldermask_bridges_in_footprints"),
                sexpdata.Symbol("no"),
            ],
            [
                sexpdata.Symbol("tenting"),
                sexpdata.Symbol("front"),
                sexpdata.Symbol("back"),
            ],
            [
                sexpdata.Symbol("pcbplotparams"),
                [
                    sexpdata.Symbol("layerselection"),
                    "0x00000000_00000000_55555555_5755f5df",
                ],
                [
                    sexpdata.Symbol("plot_on_all_layers_selection"),
                    "0x00000000_00000000_00000000_00000000",
                ],
                [sexpdata.Symbol("disableapertmacros"), sexpdata.Symbol("no")],
                [sexpdata.Symbol("usegerberextensions"), sexpdata.Symbol("no")],
                [sexpdata.Symbol("usegerberattributes"), sexpdata.Symbol("yes")],
                [
                    sexpdata.Symbol("usegerberadvancedattributes"),
                    sexpdata.Symbol("yes"),
                ],
                [sexpdata.Symbol("creategerberjobfile"), sexpdata.Symbol("yes")],
                [sexpdata.Symbol("dashed_line_dash_ratio"), 12.0],
                [sexpdata.Symbol("dashed_line_gap_ratio"), 3.0],
                [sexpdata.Symbol("svgprecision"), 4],
                [sexpdata.Symbol("plotframeref"), sexpdata.Symbol("no")],
                [sexpdata.Symbol("mode"), 1],
                [sexpdata.Symbol("useauxorigin"), sexpdata.Symbol("no")],
                [sexpdata.Symbol("hpglpennumber"), 1],
                [sexpdata.Symbol("hpglpenspeed"), 20],
                [sexpdata.Symbol("hpglpendiameter"), 15.0],
                [
                    sexpdata.Symbol("pdf_front_fp_property_popups"),
                    sexpdata.Symbol("yes"),
                ],
                [
                    sexpdata.Symbol("pdf_back_fp_property_popups"),
                    sexpdata.Symbol("yes"),
                ],
                [sexpdata.Symbol("pdf_metadata"), sexpdata.Symbol("yes")],
                [sexpdata.Symbol("pdf_single_document"), sexpdata.Symbol("no")],
                [sexpdata.Symbol("dxfpolygonmode"), sexpdata.Symbol("yes")],
                [sexpdata.Symbol("dxfimperialunits"), sexpdata.Symbol("yes")],
                [sexpdata.Symbol("dxfusepcbnewfont"), sexpdata.Symbol("yes")],
                [sexpdata.Symbol("psnegative"), sexpdata.Symbol("no")],
                [sexpdata.Symbol("psa4output"), sexpdata.Symbol("no")],
                [sexpdata.Symbol("plot_black_and_white"), sexpdata.Symbol("yes")],
                [sexpdata.Symbol("plotinvisibletext"), sexpdata.Symbol("no")],
                [sexpdata.Symbol("sketchpadsonfab"), sexpdata.Symbol("no")],
                [sexpdata.Symbol("plotpadnumbers"), sexpdata.Symbol("no")],
                [sexpdata.Symbol("hidednponfab"), sexpdata.Symbol("no")],
                [sexpdata.Symbol("sketchdnponfab"), sexpdata.Symbol("yes")],
                [sexpdata.Symbol("crossoutdnponfab"), sexpdata.Symbol("yes")],
                [sexpdata.Symbol("subtractmaskfromsilk"), sexpdata.Symbol("no")],
                [sexpdata.Symbol("outputformat"), 1],
                [sexpdata.Symbol("mirror"), sexpdata.Symbol("no")],
                [sexpdata.Symbol("drillshape"), 1],
                [sexpdata.Symbol("scaleselection"), 1],
                [sexpdata.Symbol("outputdirectory"), ""],
            ],
        ]

    def load(self, filepath: Union[str, Path]):
        """
        Load a PCB file.

        Args:
            filepath: Path to the .kicad_pcb file
        """
        logger.info(f"Loading PCB from {filepath}")
        self.pcb_data = self.parser.parse_file(filepath)
        logger.info(f"Loaded {len(self.pcb_data['footprints'])} footprints")

    def save(self, filepath: Union[str, Path]):
        """
        Save the PCB to a file.

        Args:
            filepath: Path to save the .kicad_pcb file
        """
        save_path = Path(filepath)
        logger.info(f"Saving PCB to {save_path}")
        self.parser.write_file(self.pcb_data, save_path)

        # Update stored filepath
        self._filepath = save_path
        logger.info("PCB saved successfully")

    def add_footprint(
        self,
        reference: str,
        footprint_lib: str,
        x: float,
        y: float,
        rotation: float = 0.0,
        value: Optional[str] = None,
        layer: str = "F.Cu",
    ) -> Footprint:
        """
        Add a footprint to the PCB.

        Args:
            reference: Component reference (e.g., "R1")
            footprint_lib: Footprint library ID (e.g., "Resistor_SMD:R_0603_1608Metric")
            x: X position in mm
            y: Y position in mm
            rotation: Rotation in degrees (default: 0)
            value: Component value (e.g., "10k")
            layer: PCB layer (default: "F.Cu")

        Returns:
            The created Footprint object
        """
        # Parse library and name
        if ":" in footprint_lib:
            library, name = footprint_lib.split(":", 1)
        else:
            library = ""
            name = footprint_lib

        # Create footprint
        footprint = Footprint(
            library=library,
            name=name,
            position=Point(x, y),
            rotation=rotation,
            layer=layer,
            reference=reference,
            value=value or "",
            uuid=str(uuid_module.uuid4()),
        )

        # Add default properties
        ref_prop = Property(
            name="Reference",
            value=reference,
            position=Point(0, -1.43),  # Standard offset
            layer="F.SilkS",
            uuid=str(uuid_module.uuid4()),
        )
        footprint.properties.append(ref_prop)

        if value:
            val_prop = Property(
                name="Value",
                value=value,
                position=Point(0, 1.43),  # Standard offset
                layer="F.Fab",
                uuid=str(uuid_module.uuid4()),
            )
            footprint.properties.append(val_prop)

        # Add default pads based on footprint type
        self._add_default_pads(footprint)

        # Add to PCB
        self.pcb_data["footprints"].append(footprint)
        logger.debug(f"Added footprint {reference} at ({x}, {y})")

        return footprint

    def _add_default_pads(self, footprint: Footprint):
        """
        Add default pads to a footprint based on its type.

        This is a simplified implementation that adds standard 2-pad
        configuration for passive components.
        """
        # Determine pad configuration based on footprint name
        if any(x in footprint.name.lower() for x in ["r_", "c_", "l_"]):
            # Standard 2-pad passive component (resistor, capacitor, inductor)
            if "0603" in footprint.name:
                pad_spacing = 1.65  # 0603 pad spacing
                pad_size = (0.8, 0.95)
            elif "0805" in footprint.name:
                pad_spacing = 2.0  # 0805 pad spacing
                pad_size = (1.0, 1.25)
            elif "1206" in footprint.name:
                pad_spacing = 3.2  # 1206 pad spacing
                pad_size = (1.2, 1.6)
            else:
                # Default spacing
                pad_spacing = 2.0
                pad_size = (1.0, 1.0)

            # Add pad 1 (left)
            pad1 = Pad(
                number="1",
                type="smd",
                shape="roundrect",
                position=Point(-pad_spacing / 2, 0),
                size=pad_size,
                layers=["F.Cu", "F.Mask", "F.Paste"],
                roundrect_rratio=0.25,
                uuid=str(uuid_module.uuid4()),
            )
            footprint.pads.append(pad1)

            # Add pad 2 (right)
            pad2 = Pad(
                number="2",
                type="smd",
                shape="roundrect",
                position=Point(pad_spacing / 2, 0),
                size=pad_size,
                layers=["F.Cu", "F.Mask", "F.Paste"],
                roundrect_rratio=0.25,
                uuid=str(uuid_module.uuid4()),
            )
            footprint.pads.append(pad2)

        elif "soic" in footprint.name.lower():
            # SOIC package - add 8 pads as example
            pitch = 1.27  # Standard SOIC pitch
            pad_size = (0.6, 1.5)

            for i in range(8):
                pad_num = str(i + 1)
                if i < 4:
                    # Left side pads
                    pad = Pad(
                        number=pad_num,
                        type="smd",
                        shape="rect",
                        position=Point(-2.7, 1.905 - i * pitch),
                        size=pad_size,
                        layers=["F.Cu", "F.Mask", "F.Paste"],
                        uuid=str(uuid_module.uuid4()),
                    )
                else:
                    # Right side pads
                    pad = Pad(
                        number=pad_num,
                        type="smd",
                        shape="rect",
                        position=Point(2.7, -1.905 + (i - 4) * pitch),
                        size=pad_size,
                        layers=["F.Cu", "F.Mask", "F.Paste"],
                        uuid=str(uuid_module.uuid4()),
                    )
                footprint.pads.append(pad)

    def remove_footprint(self, reference: str) -> bool:
        """
        Remove a footprint from the PCB.

        Args:
            reference: Component reference to remove

        Returns:
            True if footprint was found and removed, False otherwise
        """
        initial_count = len(self.pcb_data["footprints"])
        self.pcb_data["footprints"] = [
            fp for fp in self.pcb_data["footprints"] if fp.reference != reference
        ]

        removed = len(self.pcb_data["footprints"]) < initial_count
        if removed:
            logger.info(f"Removed footprint {reference}")
        else:
            logger.warning(f"Footprint {reference} not found")

        return removed

    def move_footprint(
        self, reference: str, x: float, y: float, rotation: Optional[float] = None
    ) -> bool:
        """
        Move a footprint to a new position.

        Args:
            reference: Component reference to move
            x: New X position in mm
            y: New Y position in mm
            rotation: Optional new rotation in degrees

        Returns:
            True if footprint was found and moved, False otherwise
        """
        footprint = self.get_footprint(reference)
        if not footprint:
            logger.warning(f"Footprint {reference} not found")
            return False

        footprint.position = Point(x, y)
        if rotation is not None:
            footprint.rotation = rotation

        logger.debug(f"Moved footprint {reference} to ({x}, {y})")
        return True

    def get_footprint(self, reference: str) -> Optional[Footprint]:
        """
        Get a footprint by reference.

        Args:
            reference: Component reference

        Returns:
            Footprint object if found, None otherwise
        """
        for footprint in self.pcb_data["footprints"]:
            if footprint.reference == reference:
                return footprint
        return None

    def list_footprints(self) -> List[Tuple[str, str, float, float]]:
        """
        List all footprints on the board.

        Returns:
            List of tuples (reference, value, x, y)
        """
        footprints = []
        for fp in self.pcb_data["footprints"]:
            footprints.append((fp.reference, fp.value, fp.position.x, fp.position.y))
        return footprints

    def update_footprint_value(self, reference: str, value: str) -> bool:
        """
        Update the value of a footprint.

        Args:
            reference: Component reference
            value: New value

        Returns:
            True if footprint was found and updated, False otherwise
        """
        footprint = self.get_footprint(reference)
        if not footprint:
            logger.warning(f"Footprint {reference} not found")
            return False

        footprint.value = value
        footprint.set_property("Value", value)

        logger.debug(f"Updated footprint {reference} value to {value}")
        return True

    def add_net(self, net_name: str) -> int:
        """
        Add a new net to the PCB.

        Args:
            net_name: Name of the net

        Returns:
            Net number assigned
        """
        # Find highest net number
        max_net = max(net.number for net in self.pcb_data["nets"])
        new_net_num = max_net + 1

        # Add new net
        new_net = Net(new_net_num, net_name)
        self.pcb_data["nets"].append(new_net)

        logger.debug(f"Added net {new_net_num}: {net_name}")
        return new_net_num

    def get_net_by_name(self, net_name: str) -> Optional[Net]:
        """
        Get a net by name.

        Args:
            net_name: Name of the net

        Returns:
            Net object if found, None otherwise
        """
        for net in self.pcb_data["nets"]:
            if net.name == net_name:
                return net
        return None

    def get_board_outline(self) -> Optional[List[Tuple[float, float]]]:
        """
        Get the board outline from Edge.Cuts layer.

        Returns:
            List of (x, y) points defining the board outline, or None
        """
        # This would need to parse zones or graphics on Edge.Cuts layer
        # For now, return None as a placeholder
        return None

    def set_board_outline(self, points: List[Tuple[float, float]]):
        """
        Set the board outline on Edge.Cuts layer.

        Args:
            points: List of (x, y) points defining the board outline
        """
        # This would create graphics on Edge.Cuts layer
        # For now, just log
        logger.info(f"Setting board outline with {len(points)} points")

    def get_footprint_count(self) -> int:
        """Get the number of footprints on the board."""
        return len(self.pcb_data["footprints"])

    def get_net_count(self) -> int:
        """Get the number of nets on the board."""
        return len(self.pcb_data["nets"])

    def clear_footprints(self):
        """Remove all footprints from the board."""
        self.pcb_data["footprints"] = []
        logger.info("Cleared all footprints")

    def get_board_info(self) -> Dict[str, Any]:
        """
        Get general information about the board.

        Returns:
            Dictionary with board information
        """
        return {
            "version": self.pcb_data.get("version"),
            "generator": self.pcb_data.get("generator"),
            "generator_version": self.pcb_data.get("generator_version"),
            "paper_size": self.pcb_data.get("paper"),
            "thickness": self.pcb_data["general"].get("thickness"),
            "footprint_count": self.get_footprint_count(),
            "net_count": self.get_net_count(),
            "via_count": len(self.pcb_data.get("vias", [])),
            "track_count": len(self.pcb_data.get("tracks", [])),
        }

    # Ratsnest and connectivity methods

    def get_ratsnest(self) -> List[Dict[str, Any]]:
        """
        Get the ratsnest (unrouted connections) for the board.

        Returns:
            List of ratsnest connections, each containing:
            - from_ref: Source component reference
            - from_pad: Source pad number
            - to_ref: Destination component reference
            - to_pad: Destination pad number
            - net_name: Name of the net
            - net_number: Net number
            - distance: Distance between pads in mm
        """
        ratsnest = []

        # Group pads by net
        net_pads = {}
        for footprint in self.pcb_data["footprints"]:
            for pad in footprint.pads:
                if pad.net is not None and pad.net > 0:
                    if pad.net not in net_pads:
                        net_pads[pad.net] = []
                    net_pads[pad.net].append({"footprint": footprint, "pad": pad})

        # For each net with multiple pads, create ratsnest connections
        for net_num, pads in net_pads.items():
            if len(pads) < 2:
                continue

            # Get net name
            net_name = ""
            for net in self.pcb_data["nets"]:
                if net.number == net_num:
                    net_name = net.name
                    break

            # Create connections between all pads in the net
            # In a real implementation, this would use minimum spanning tree
            # For now, we'll connect each pad to the next
            for i in range(len(pads) - 1):
                from_pad_info = pads[i]
                to_pad_info = pads[i + 1]

                # Calculate absolute pad positions
                from_pos = Point(
                    from_pad_info["footprint"].position.x
                    + from_pad_info["pad"].position.x,
                    from_pad_info["footprint"].position.y
                    + from_pad_info["pad"].position.y,
                )
                to_pos = Point(
                    to_pad_info["footprint"].position.x + to_pad_info["pad"].position.x,
                    to_pad_info["footprint"].position.y + to_pad_info["pad"].position.y,
                )

                # Calculate distance
                dx = to_pos.x - from_pos.x
                dy = to_pos.y - from_pos.y
                distance = (dx * dx + dy * dy) ** 0.5

                ratsnest.append(
                    {
                        "from_ref": from_pad_info["footprint"].reference,
                        "from_pad": from_pad_info["pad"].number,
                        "to_ref": to_pad_info["footprint"].reference,
                        "to_pad": to_pad_info["pad"].number,
                        "net_name": net_name,
                        "net_number": net_num,
                        "distance": round(distance, 3),
                    }
                )

        return ratsnest

    def get_connections(self, reference: str) -> List[Dict[str, Any]]:
        """
        Get all connections for a specific component.

        Args:
            reference: Component reference

        Returns:
            List of connections, each containing pad info and connected components
        """
        footprint = self.get_footprint(reference)
        if not footprint:
            return []

        connections = []

        for pad in footprint.pads:
            if pad.net is None or pad.net == 0:
                continue

            # Find all other pads on the same net
            connected_to = []
            for other_fp in self.pcb_data["footprints"]:
                if other_fp.reference == reference:
                    continue

                for other_pad in other_fp.pads:
                    if other_pad.net == pad.net:
                        connected_to.append(
                            {
                                "reference": other_fp.reference,
                                "pad": other_pad.number,
                                "value": other_fp.value,
                            }
                        )

            connections.append(
                {
                    "pad": pad.number,
                    "net": pad.net,
                    "net_name": pad.net_name or "",
                    "connected_to": connected_to,
                }
            )

        return connections

    def connect_pads(
        self, ref1: str, pad1: str, ref2: str, pad2: str, net_name: Optional[str] = None
    ) -> bool:
        """
        Connect two pads with a net.

        Args:
            ref1: First component reference
            pad1: First component pad number
            ref2: Second component reference
            pad2: Second component pad number
            net_name: Optional net name (auto-generated if not provided)

        Returns:
            True if connection was made, False otherwise
        """
        # Get footprints
        fp1 = self.get_footprint(ref1)
        fp2 = self.get_footprint(ref2)

        if not fp1 or not fp2:
            logger.warning(f"Could not find footprints {ref1} or {ref2}")
            return False

        # Find pads
        pad1_obj = None
        pad2_obj = None

        for pad in fp1.pads:
            if pad.number == pad1:
                pad1_obj = pad
                break

        for pad in fp2.pads:
            if pad.number == pad2:
                pad2_obj = pad
                break

        if not pad1_obj or not pad2_obj:
            logger.warning(f"Could not find pads {pad1} or {pad2}")
            return False

        # Check if either pad already has a net
        if pad1_obj.net and pad2_obj.net and pad1_obj.net != pad2_obj.net:
            logger.warning(f"Pads are already on different nets")
            return False

        # Use existing net or create new one
        net_num = pad1_obj.net or pad2_obj.net

        if not net_num:
            # Create new net
            if not net_name:
                net_name = f"Net-({ref1}-Pad{pad1})"
            net_num = self.add_net(net_name)
        else:
            # Get existing net name
            for net in self.pcb_data["nets"]:
                if net.number == net_num:
                    net_name = net.name
                    break

        # Assign net to both pads
        pad1_obj.net = net_num
        pad1_obj.net_name = net_name
        pad2_obj.net = net_num
        pad2_obj.net_name = net_name

        logger.debug(
            f"Connected {ref1}.{pad1} to {ref2}.{pad2} on net {net_num} ({net_name})"
        )
        return True

    def disconnect_pad(self, reference: str, pad_number: str) -> bool:
        """
        Disconnect a pad from its net.

        Args:
            reference: Component reference
            pad_number: Pad number to disconnect

        Returns:
            True if pad was disconnected, False otherwise
        """
        footprint = self.get_footprint(reference)
        if not footprint:
            return False

        for pad in footprint.pads:
            if pad.number == pad_number:
                if pad.net:
                    logger.debug(
                        f"Disconnected {reference}.{pad_number} from net {pad.net}"
                    )
                    pad.net = None
                    pad.net_name = None
                    return True
                else:
                    logger.debug(f"Pad {reference}.{pad_number} was not connected")
                    return True

        logger.warning(f"Pad {reference}.{pad_number} not found")
        return False

    def get_net_info(self, net_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific net.

        Args:
            net_name: Name of the net

        Returns:
            Dictionary with net info including connected pads
        """
        # Find net
        net_obj = self.get_net_by_name(net_name)
        if not net_obj:
            return None

        # Find all pads on this net
        connected_pads = []
        for footprint in self.pcb_data["footprints"]:
            for pad in footprint.pads:
                if pad.net == net_obj.number:
                    connected_pads.append(
                        {
                            "reference": footprint.reference,
                            "pad": pad.number,
                            "value": footprint.value,
                            "position": {
                                "x": footprint.position.x + pad.position.x,
                                "y": footprint.position.y + pad.position.y,
                            },
                        }
                    )

        return {
            "number": net_obj.number,
            "name": net_obj.name,
            "pad_count": len(connected_pads),
            "connected_pads": connected_pads,
        }

    # Track routing methods

    def add_track(
        self,
        start_x: float,
        start_y: float,
        end_x: float,
        end_y: float,
        width: float = 0.25,
        layer: str = "F.Cu",
        net: Optional[int] = None,
    ) -> Track:
        """
        Add a track (copper trace) to the PCB.

        Args:
            start_x: Starting X position in mm
            start_y: Starting Y position in mm
            end_x: Ending X position in mm
            end_y: Ending Y position in mm
            width: Track width in mm (default: 0.25mm)
            layer: PCB layer (default: "F.Cu" for front copper)
            net: Net number (optional)

        Returns:
            The created Track object
        """
        track = Track(
            start=Point(start_x, start_y),
            end=Point(end_x, end_y),
            width=width,
            layer=layer,
            net=net.number if net else None,
            uuid=str(uuid_module.uuid4()),
        )

        self.pcb_data["tracks"].append(track)
        logger.debug(f"Added track from ({start_x}, {start_y}) to ({end_x}, {end_y})")

        return track

    def route_connection(
        self,
        ref1: str,
        pad1: str,
        ref2: str,
        pad2: str,
        width: float = 0.25,
        layer: str = "F.Cu",
    ) -> List[Track]:
        """
        Route a connection between two pads with a track.

        This is a simple point-to-point routing. For complex routing,
        use add_track() with intermediate points.

        Args:
            ref1: First component reference
            pad1: First component pad number
            ref2: Second component reference
            pad2: Second component pad number
            width: Track width in mm (default: 0.25mm)
            layer: PCB layer (default: "F.Cu")

        Returns:
            List of created tracks (currently just one direct track)
        """
        # Get footprints and pads
        fp1 = self.get_footprint(ref1)
        fp2 = self.get_footprint(ref2)

        if not fp1 or not fp2:
            logger.warning(f"Could not find footprints {ref1} or {ref2}")
            return []

        # Find pads
        pad1_obj = None
        pad2_obj = None

        for pad in fp1.pads:
            if pad.number == pad1:
                pad1_obj = pad
                break

        for pad in fp2.pads:
            if pad.number == pad2:
                pad2_obj = pad
                break

        if not pad1_obj or not pad2_obj:
            logger.warning(f"Could not find pads {pad1} or {pad2}")
            return []

        # Check if pads are on the same net
        if pad1_obj.net != pad2_obj.net or pad1_obj.net is None:
            logger.warning(f"Pads are not on the same net")
            return []

        # Calculate absolute pad positions
        start_pos = Point(
            fp1.position.x + pad1_obj.position.x, fp1.position.y + pad1_obj.position.y
        )
        end_pos = Point(
            fp2.position.x + pad2_obj.position.x, fp2.position.y + pad2_obj.position.y
        )

        # Create track
        track = self.add_track(
            start_pos.x,
            start_pos.y,
            end_pos.x,
            end_pos.y,
            width=width,
            layer=layer,
            net=pad1_obj.net,
        )

        logger.debug(f"Routed {ref1}.{pad1} to {ref2}.{pad2}")
        return [track]

    def route_ratsnest(self, width: float = 0.25, layer: str = "F.Cu") -> List[Track]:
        """
        Route all connections in the ratsnest.

        This creates simple point-to-point tracks for all unrouted connections.

        Args:
            width: Track width in mm (default: 0.25mm)
            layer: PCB layer (default: "F.Cu")

        Returns:
            List of created tracks
        """
        tracks = []
        ratsnest = self.get_ratsnest()

        for conn in ratsnest:
            new_tracks = self.route_connection(
                conn["from_ref"],
                conn["from_pad"],
                conn["to_ref"],
                conn["to_pad"],
                width=width,
                layer=layer,
            )
            tracks.extend(new_tracks)

        logger.debug(f"Routed {len(tracks)} connections")
        return tracks

    def get_tracks(self) -> List[Track]:
        """Get all tracks on the board."""
        return self.pcb_data.get("tracks", [])

    def remove_track(self, track: Track) -> bool:
        """
        Remove a track from the board.

        Args:
            track: Track object to remove

        Returns:
            True if track was removed, False otherwise
        """
        if track in self.pcb_data["tracks"]:
            self.pcb_data["tracks"].remove(track)
            logger.debug("Removed track")
            return True
        return False

    def clear_tracks(self):
        """Remove all tracks from the board."""
        self.pcb_data["tracks"] = []
        logger.debug("Cleared all tracks")

    def add_via(
        self,
        x: float,
        y: float,
        size: float = 0.8,
        drill: float = 0.4,
        net: Optional[int] = None,
        layers: Optional[List[str]] = None,
    ) -> Via:
        """
        Add a via to the PCB.

        Args:
            x: X position in mm
            y: Y position in mm
            size: Via diameter in mm (default: 0.8mm)
            drill: Drill diameter in mm (default: 0.4mm)
            net: Net number (optional)
            layers: List of layers the via connects (default: ["F.Cu", "B.Cu"])

        Returns:
            The created Via object
        """
        if layers is None:
            layers = ["F.Cu", "B.Cu"]

        via = Via(
            position=Point(x, y),
            size=size,
            drill=drill,
            layers=layers,
            net=net,
            uuid=str(uuid_module.uuid4()),
        )

        self.pcb_data["vias"].append(via)
        logger.debug(f"Added via at ({x}, {y})")

        return via

    # Board outline methods

    def set_board_outline_rect(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        corner_radius: float = 0.0,
    ) -> Rectangle:
        """
        Set a rectangular board outline on the Edge.Cuts layer.

        Args:
            x: X position of top-left corner in mm
            y: Y position of top-left corner in mm
            width: Board width in mm
            height: Board height in mm
            corner_radius: Corner radius in mm (0 for sharp corners)

        Returns:
            Rectangle object forming the outline
        """
        # Clear existing edge cuts
        self.clear_edge_cuts()

        if corner_radius > 0:
            # Rectangle with rounded corners
            # This is simplified - proper arc support would be needed
            logger.warning(
                "Rounded corners not yet fully implemented - using sharp corners"
            )

        # Create rectangle
        rect = Rectangle(
            start=Point(x, y),
            end=Point(x + width, y + height),
            layer="Edge.Cuts",
            width=0.05,  # Standard width for edge cuts
            fill=False,
            uuid=str(uuid_module.uuid4()),
        )

        self._add_graphic_item(rect)

        logger.info(f"Set rectangular board outline: {width}x{height}mm at ({x}, {y})")
        return rect

    def set_board_outline_polygon(
        self, points: List[Tuple[float, float]]
    ) -> List[Line]:
        """
        Set a polygonal board outline on the Edge.Cuts layer.

        Args:
            points: List of (x, y) tuples defining the polygon vertices in mm

        Returns:
            List of Line objects forming the outline
        """
        if len(points) < 3:
            logger.error("Polygon must have at least 3 points")
            return []

        # Clear existing edge cuts
        self.clear_edge_cuts()

        lines = []

        # Create lines between consecutive points
        for i in range(len(points)):
            start = Point(points[i][0], points[i][1])
            end = Point(
                points[(i + 1) % len(points)][0], points[(i + 1) % len(points)][1]
            )

            line = Line(
                start=start,
                end=end,
                layer="Edge.Cuts",
                width=0.1,
                uuid=str(uuid_module.uuid4()),
            )
            lines.append(line)
            self._add_graphic_item(line)

        logger.info(f"Set polygonal board outline with {len(points)} vertices")
        return lines

    def add_edge_cut_line(
        self, x1: float, y1: float, x2: float, y2: float, width: float = 0.1
    ) -> Line:
        """
        Add a single line to the Edge.Cuts layer.

        Args:
            x1, y1: Start point in mm
            x2, y2: End point in mm
            width: Line width in mm (default: 0.1mm)

        Returns:
            The created Line object
        """
        line = Line(
            start=Point(x1, y1),
            end=Point(x2, y2),
            layer="Edge.Cuts",
            width=width,
            uuid=str(uuid_module.uuid4()),
        )

        self._add_graphic_item(line)
        logger.debug(f"Added edge cut line from ({x1}, {y1}) to ({x2}, {y2})")

        return line

    def clear_edge_cuts(self):
        """Remove all items from the Edge.Cuts layer."""
        if "graphics" not in self.pcb_data:
            return

        # Remove all graphics items on Edge.Cuts layer
        self.pcb_data["graphics"] = [
            item
            for item in self.pcb_data["graphics"]
            if not (hasattr(item, "layer") and item.layer == "Edge.Cuts")
        ]

        logger.debug("Cleared all edge cuts")

    def get_board_outline(self) -> List[Union[Line, Rectangle]]:
        """
        Get all graphics items on the Edge.Cuts layer.

        Returns:
            List of Line and Rectangle objects forming the board outline
        """
        if "graphics" not in self.pcb_data:
            return []

        edge_cuts = []
        for item in self.pcb_data["graphics"]:
            if hasattr(item, "layer") and item.layer == "Edge.Cuts":
                edge_cuts.append(item)

        return edge_cuts

    def get_board_outline_bbox(self) -> "BoundingBox":
        """
        Get the bounding box of the board outline.

        Returns:
            BoundingBox object representing the board boundaries
        """
        from .placement.base import BoundingBox

        # Get all outline elements
        outline_elements = self.get_board_outline()

        if not outline_elements:
            # Default board size if no outline
            return BoundingBox(min_x=0, min_y=0, max_x=100, max_y=100)

        # Find min/max coordinates
        min_x = float("inf")
        min_y = float("inf")
        max_x = float("-inf")
        max_y = float("-inf")

        for element in outline_elements:
            if isinstance(element, Line):
                min_x = min(min_x, element.start.x, element.end.x)
                min_y = min(min_y, element.start.y, element.end.y)
                max_x = max(max_x, element.start.x, element.end.x)
                max_y = max(max_y, element.start.y, element.end.y)
            elif isinstance(element, Rectangle):
                min_x = min(min_x, element.start.x, element.end.x)
                min_y = min(min_y, element.start.y, element.end.y)
                max_x = max(max_x, element.start.x, element.end.x)
                max_y = max(max_y, element.start.y, element.end.y)

        return BoundingBox(min_x=min_x, min_y=min_y, max_x=max_x, max_y=max_y)

    def _add_graphic_item(self, item: Union[Line, Rectangle]):
        """Add a graphic item to the PCB."""
        if "graphics" not in self.pcb_data:
            self.pcb_data["graphics"] = []
        self.pcb_data["graphics"].append(item)

    # Zone (copper pour) methods

    def add_zone(
        self,
        polygon: List[Tuple[float, float]],
        layer: str = "F.Cu",
        net_name: Optional[str] = None,
        filled: bool = False,
    ) -> Zone:
        """
        Add a zone (copper pour area) to the PCB.

        Args:
            polygon: List of (x, y) tuples defining the zone boundary in mm
            layer: PCB layer(s) - can be single layer or space-separated list
            net_name: Net name to connect the zone to (optional)
            filled: Whether the zone should be filled (default: False)

        Returns:
            The created Zone object
        """
        # Create zone
        zone = Zone(
            layer=layer, net_name=net_name, filled=filled, uuid=str(uuid_module.uuid4())
        )

        # Convert polygon points
        for x, y in polygon:
            zone.polygon.append(Point(x, y))

        # Find net number if net name provided
        if net_name:
            net = self.get_net_by_name(net_name)
            if net:
                zone.net = net.number

        # Add to PCB
        self.pcb_data["zones"].append(zone)

        logger.debug(f"Added zone on layer {layer} with {len(polygon)} vertices")
        return zone

    def get_zones(self, layer: Optional[str] = None) -> List[Zone]:
        """
        Get all zones, optionally filtered by layer.

        Args:
            layer: Layer to filter by (optional)

        Returns:
            List of Zone objects
        """
        zones = self.pcb_data.get("zones", [])

        if layer:
            # Filter by layer (handle multi-layer zones)
            zones = [z for z in zones if layer in z.layer]

        return zones

    def remove_zone(self, zone_uuid: str) -> bool:
        """
        Remove a zone by its UUID.

        Args:
            zone_uuid: UUID of the zone to remove

        Returns:
            True if zone was found and removed, False otherwise
        """
        initial_count = len(self.pcb_data.get("zones", []))
        self.pcb_data["zones"] = [
            z for z in self.pcb_data.get("zones", []) if z.uuid != zone_uuid
        ]

        removed = len(self.pcb_data.get("zones", [])) < initial_count
        if removed:
            logger.debug(f"Removed zone {zone_uuid}")
        else:
            logger.warning(f"Zone {zone_uuid} not found")

        return removed

    def clear_zones(self):
        """Remove all zones from the board."""
        self.pcb_data["zones"] = []
        logger.debug("Cleared all zones")

    def fill_zone(self, zone_uuid: str) -> bool:
        """
        Mark a zone as filled.

        Args:
            zone_uuid: UUID of the zone to fill

        Returns:
            True if zone was found and filled, False otherwise
        """
        for zone in self.pcb_data.get("zones", []):
            if zone.uuid == zone_uuid:
                zone.filled = True
                logger.debug(f"Filled zone {zone_uuid}")
                return True

        logger.warning(f"Zone {zone_uuid} not found")
        return False

    def unfill_zone(self, zone_uuid: str) -> bool:
        """
        Mark a zone as unfilled.

        Args:
            zone_uuid: UUID of the zone to unfill

        Returns:
            True if zone was found and unfilled, False otherwise
        """
        for zone in self.pcb_data.get("zones", []):
            if zone.uuid == zone_uuid:
                zone.filled = False
                logger.debug(f"Unfilled zone {zone_uuid}")
                return True

        logger.warning(f"Zone {zone_uuid} not found")
        return False

    # Component placement methods

    def auto_place_components(self, algorithm: str = "hierarchical", **kwargs) -> None:
        """
        Automatically place components using specified algorithm.

        Args:
            algorithm: Placement algorithm to use ("hierarchical", "force_directed", "spiral", "advanced", "external", etc.)
            **kwargs: Algorithm-specific parameters
                For hierarchical placement:
                - component_spacing: Spacing between components in mm (default: 0.5)
                - group_spacing: Spacing between hierarchical groups in mm (default: 2.5)
                - use_courtyard: Use courtyard geometry for collision (default: True)
                For force_directed placement:
                - component_spacing: Minimum spacing between components (default: 5.0)
                - attraction_strength: Strength of attraction between connected components (default: 0.1)
                - repulsion_strength: Strength of repulsion between all components (default: 100.0)
                - internal_force_multiplier: Multiplier for forces within subcircuits (default: 2.0)
                - iterations_per_level: Number of iterations for each optimization level (default: 100)
                - damping: Damping factor to prevent oscillations (default: 0.8)
                - use_courtyard: Use courtyard geometry for collision detection (default: True)
                For spiral placement:
                - component_spacing: Minimum spacing between components (default: 5.0)
                - spiral_step: Step size for spiral search (default: 0.5)
                - use_courtyard: Use courtyard geometry for collision (default: True)
                For advanced placement:
                - signal_net_weight: Weight for signal nets (default: 1.0)
                - power_net_weight: Weight for power/ground nets (default: 0.1)
                - differential_weight: Weight for differential pairs (default: 1.5)
                - min_component_spacing: Minimum spacing between components (default: 5.0)
                - decoupling_cap_offset: Distance from IC for decoupling caps (default: 2.0)
                - decoupling_cap_max_distance: Max distance for decoupling caps (default: 5.0)
                - enable_rotation_optimization: Enable component rotation optimization (default: True)
                - enable_global_optimization: Enable global optimization phase (default: True)
                - enable_decoupling_optimization: Enable special decoupling cap placement (default: True)
                - enable_passive_grouping: Enable passive component grouping (default: True)
                For external placement:
                - cutout_start_x: X coordinate of cutout start (default: 100.0)
                - cutout_start_y: Y coordinate of cutout start (default: 100.0)
                - cutout_end_x: X coordinate of cutout end (default: 200.0)
                - cutout_end_y: Y coordinate of cutout end (default: 200.0)

        Raises:
            ValueError: If unknown algorithm is specified
        """
        if algorithm == "hierarchical":
            from .placement.hierarchical_placement_v2 import HierarchicalPlacerV2

            # Filter out parameters that hierarchical placement doesn't use
            hierarchical_kwargs = {
                "component_spacing": kwargs.get("component_spacing", 0.5),
                "group_spacing": kwargs.get("group_spacing", 2.5),
                "use_courtyard": kwargs.get("use_courtyard", True),
            }
            placer = HierarchicalPlacerV2(**hierarchical_kwargs)

            # Wrap footprints
            from .placement.base import ComponentWrapper

            components = [ComponentWrapper(fp) for fp in self.footprints.values()]

            # Get board dimensions
            board_width = kwargs.get("board_width", 100.0)
            board_height = kwargs.get("board_height", 100.0)

            # Extract connections if provided
            connections = kwargs.get("connections", [])

            # Place components
            positions = placer.place(components, connections, board_width, board_height)

            # Update footprint positions
            for ref, pos in positions.items():
                if ref in self.footprints:
                    self.footprints[ref].position = pos

            logger.debug(
                f"Completed {algorithm} placement with courtyard collision detection"
            )

        elif algorithm == "spiral":
            from .placement.spiral_placement_v2 import SpiralPlacementAlgorithmV2

            # Extract connections if provided
            connections = kwargs.get("connections", [])
            spiral_kwargs = {
                "component_spacing": kwargs.get("component_spacing", 5.0),
                "spiral_step": kwargs.get("spiral_step", 0.5),
                "use_courtyard": kwargs.get("use_courtyard", True),
            }
            placer = SpiralPlacementAlgorithmV2(**spiral_kwargs)

            # Get board outline
            board_outline = self.get_board_outline_bbox()

            # Run placement directly with footprints
            result = placer.place_components(
                list(self.footprints.values()), board_outline, connections
            )

            if result.success:
                logger.debug(f"Completed {algorithm} placement: {result.message}")
                return result
            else:
                logger.error(f"Spiral placement failed: {result.message}")
                raise ValueError(f"Placement failed: {result.message}")

        elif algorithm == "force_directed":
            from .placement.base import ComponentWrapper
            from .placement.force_directed_placement_fixed import ForceDirectedPlacement

            logger.debug(
                f"Starting force-directed placement with {len(self.footprints)} components"
            )

            # Extract parameters
            force_kwargs = {
                "component_spacing": kwargs.get("component_spacing", 5.0),
                "attraction_strength": kwargs.get("attraction_strength", 0.1),
                "repulsion_strength": kwargs.get("repulsion_strength", 100.0),
                "internal_force_multiplier": kwargs.get(
                    "internal_force_multiplier", 2.0
                ),
                "iterations_per_level": kwargs.get("iterations_per_level", 100),
                "damping": kwargs.get("damping", 0.8),
            }

            placer = ForceDirectedPlacement(**force_kwargs)

            # Wrap footprints
            components = [ComponentWrapper(fp) for fp in self.footprints.values()]

            # Get board dimensions
            board_outline = self.get_board_outline_bbox()
            board_width = (
                board_outline.width()
                if board_outline
                else kwargs.get("board_width", 100.0)
            )
            board_height = (
                board_outline.height()
                if board_outline
                else kwargs.get("board_height", 100.0)
            )

            # Extract connections
            connections = kwargs.get("connections", [])

            # Place components
            positions = placer.place(components, connections, board_width, board_height)

            # Update footprint positions
            for ref, pos in positions.items():
                if ref in self.footprints:
                    self.footprints[ref].position = pos

            logger.debug(f"Completed force-directed placement with two-level hierarchy")

        elif algorithm == "spiral_hierarchical":
            from .placement.base import ComponentWrapper
            from .placement.spiral_hierarchical_placement import (
                SpiralHierarchicalPlacer,
            )

            logger.debug(
                f"Starting spiral placement with {len(self.footprints)} footprints"
            )

            # Create component wrappers
            wrappers = []
            for footprint in self.footprints.values():
                wrapper = ComponentWrapper(footprint)
                wrappers.append(wrapper)
                logger.debug(
                    f"Created wrapper for {footprint.reference} at ({footprint.position.x}, {footprint.position.y})"
                )

            # Extract connections from ratsnest
            connections = []
            ratsnest = self.get_ratsnest()
            logger.debug(f"Ratsnest has {len(ratsnest)} connections")
            for connection in ratsnest:
                ref1 = connection["from_ref"]
                ref2 = connection["to_ref"]
                connections.append((ref1, ref2))
                logger.debug(f"Connection: {ref1} <-> {ref2}")

            # Get board dimensions (default to 100x100 if not specified)
            board_width = kwargs.get("board_width", 100.0)
            board_height = kwargs.get("board_height", 100.0)
            logger.debug(f"Board dimensions: {board_width}x{board_height}mm")

            # Create placer with specified parameters
            placer = SpiralHierarchicalPlacer(
                component_spacing=kwargs.get("component_spacing", 0.5),
                group_spacing=kwargs.get("group_spacing", 2.5),
                spiral_step=kwargs.get("spiral_step", 0.5),
                max_spiral_radius=kwargs.get("max_spiral_radius", 50.0),
            )
            logger.debug(
                f"Created spiral placer with spacing={kwargs.get('component_spacing', 0.5)}mm, spiral_step={kwargs.get('spiral_step', 0.5)}mm"
            )

            # Run placement
            logger.debug("Running spiral placement algorithm...")
            positions = placer.place(wrappers, connections, board_width, board_height)
            logger.debug(f"Placement returned {len(positions)} positions")

            # Update footprint positions
            updated_count = 0
            for ref, position in positions.items():
                if ref in self.footprints:
                    old_pos = self.footprints[ref].position
                    self.footprints[ref].position = position
                    logger.debug(
                        f"Updated {ref}: ({old_pos.x}, {old_pos.y}) -> ({position.x}, {position.y})"
                    )
                    updated_count += 1
                else:
                    logger.warning(f"Position for unknown footprint: {ref}")

            logger.debug(f"Updated {updated_count} footprint positions")
            logger.debug(
                f"Completed {algorithm} placement with {len(connections)} connections"
            )

        elif algorithm == "advanced":
            from .placement.advanced_placement import (
                AdvancedPlacementAlgorithm,
                AdvancedPlacementConfig,
            )
            from .placement.base import ComponentWrapper

            logger.debug(
                f"Starting advanced placement with {len(self.footprints)} components"
            )

            # Create configuration
            config = AdvancedPlacementConfig(
                signal_net_weight=kwargs.get("signal_net_weight", 1.0),
                power_net_weight=kwargs.get("power_net_weight", 0.1),
                differential_weight=kwargs.get("differential_weight", 1.5),
                min_component_spacing=kwargs.get("min_component_spacing", 5.0),
                decoupling_cap_offset=kwargs.get("decoupling_cap_offset", 2.0),
                decoupling_cap_max_distance=kwargs.get(
                    "decoupling_cap_max_distance", 5.0
                ),
                enable_rotation_optimization=kwargs.get(
                    "enable_rotation_optimization", True
                ),
                enable_global_optimization=kwargs.get(
                    "enable_global_optimization", True
                ),
                enable_decoupling_optimization=kwargs.get(
                    "enable_decoupling_optimization", True
                ),
                enable_passive_grouping=kwargs.get("enable_passive_grouping", True),
            )

            # Check if LLM classifier should be used
            use_llm_classifier = kwargs.get("use_llm_classifier", False)
            placer = AdvancedPlacementAlgorithm(
                config, use_llm_classifier=use_llm_classifier
            )

            # Wrap footprints
            components = [ComponentWrapper(fp) for fp in self.footprints.values()]
            logger.debug(
                f"Created {len(components)} component wrappers from {len(self.footprints)} footprints"
            )

            # Get board outline
            board_outline = self.get_board_outline_bbox()

            # Extract connections with net names from ratsnest
            connections = []
            ratsnest = self.get_ratsnest()

            # Build a more complete connection graph by analyzing all nets
            # Group connections by net to find all components on each net
            net_components = defaultdict(set)
            for connection in ratsnest:
                net_name = connection.get("net_name", "unknown")
                net_components[net_name].add(connection["from_ref"])
                net_components[net_name].add(connection["to_ref"])

            # Filter to only include components that actually exist
            valid_refs = set(self.footprints.keys())
            logger.debug(f"Valid component references: {valid_refs}")

            # Create connections between all components on the same net
            # This gives a more complete picture than just the ratsnest
            for net_name, net_comps in net_components.items():
                # Filter to only valid components
                valid_components = [c for c in net_comps if c in valid_refs]
                if len(valid_components) < 2:
                    continue

                # Create connections between all pairs
                for i in range(len(valid_components)):
                    for j in range(i + 1, len(valid_components)):
                        connections.append(
                            (valid_components[i], valid_components[j], net_name)
                        )

            logger.debug(
                f"Extracted {len(connections)} connections from {len(net_components)} nets"
            )

            # Place components
            result = placer.place(components, board_outline, connections)

            if result.success:
                logger.debug(f"Completed advanced placement: {result.message}")
                if result.metrics:
                    logger.debug(f"Placement metrics: {result.metrics}")
            else:
                logger.error(f"Advanced placement failed: {result.message}")
                raise ValueError(f"Placement failed: {result.message}")

        elif algorithm == "force_directed":
            from .placement.force_directed import apply_force_directed_placement

            # Extract connections from ratsnest
            connections = []
            ratsnest = self.get_ratsnest()
            for connection in ratsnest:
                ref1 = connection["from_ref"]
                ref2 = connection["to_ref"]
                connections.append((ref1, ref2))

            # Get locked components
            locked_refs = {
                fp.reference for fp in self.pcb_data["footprints"] if fp.locked
            }

            # Run force-directed placement
            positions = apply_force_directed_placement(
                list(self.footprints.values()),
                connections,
                locked_refs=locked_refs,
                **kwargs,
            )

            # Update footprint positions
            for ref, (x, y) in positions.items():
                if ref in self.footprints:
                    self.footprints[ref].position = Point(x, y)

            logger.debug(
                f"Completed {algorithm} placement with {len(connections)} connections"
            )

        elif algorithm == "connectivity_driven":
            from .placement.base import ComponentWrapper
            from .placement.connectivity_driven import ConnectivityDrivenPlacer

            # Create component wrappers
            wrappers = []
            for footprint in self.footprints.values():
                if not footprint.locked:
                    wrapper = ComponentWrapper(
                        reference=footprint.reference,
                        footprint=footprint.name,
                        value=footprint.value,
                        position=footprint.position,
                        pads=footprint.pads,
                    )
                    wrappers.append(wrapper)

            # Extract connections from ratsnest
            connections = []
            ratsnest = self.get_ratsnest()
            for connection in ratsnest:
                ref1 = connection["from_ref"]
                ref2 = connection["to_ref"]
                connections.append((ref1, ref2))

            # Get board dimensions
            outline = self.get_board_outline()
            if outline and "rect" in outline:
                board_width = outline["rect"]["width"]
                board_height = outline["rect"]["height"]
            else:
                # Default board size
                board_width = 100.0
                board_height = 100.0

            # Create placer and run algorithm
            placer = ConnectivityDrivenPlacer(
                component_spacing=kwargs.get("component_spacing", 2.0),
                cluster_spacing=kwargs.get("cluster_spacing", 5.0),
                critical_net_weight=kwargs.get("critical_net_weight", 2.0),
                crossing_penalty=kwargs.get("crossing_penalty", 1.5),
            )

            positions = placer.place(wrappers, connections, board_width, board_height)

            # Update footprint positions
            for ref, pos in positions.items():
                if ref in self.footprints:
                    self.footprints[ref].position = pos

            logger.debug(
                f"Completed {algorithm} placement with {len(connections)} connections"
            )

        elif algorithm == "connection_centric":
            from .placement.base import ComponentWrapper
            from .placement.connection_centric import ConnectionCentricPlacement

            logger.debug(
                f"Starting connection-centric placement with {len(self.footprints)} components"
            )

            # Extract connections if provided
            connections = kwargs.get("connections", [])
            if not connections:
                # Try to extract from nets by looking at footprint pads
                connections = []
                net_components = {}  # net_number -> set of component references

                # Group components by net
                for footprint in self.pcb_data["footprints"]:
                    for pad in footprint.pads:
                        if pad.net is not None and pad.net > 0:
                            if pad.net not in net_components:
                                net_components[pad.net] = set()
                            net_components[pad.net].add(footprint.reference)

                # Create connections between all pairs of components on the same net
                for net_num, refs in net_components.items():
                    refs_list = list(refs)
                    if len(refs_list) >= 2:
                        for i in range(len(refs_list)):
                            for j in range(i + 1, len(refs_list)):
                                connections.append((refs_list[i], refs_list[j]))

            logger.debug(f"Found {len(connections)} connections")

            # Get board dimensions
            board_outline = self.get_board_outline_bbox()
            if board_outline:
                board_width = board_outline.width()
                board_height = board_outline.height()
            else:
                board_width = kwargs.get("board_width", 100.0)
                board_height = kwargs.get("board_height", 100.0)

            # Create placement algorithm
            min_spacing = kwargs.get("component_spacing", 2.0)
            use_courtyard = kwargs.get("use_courtyard", True)
            placer = ConnectionCentricPlacement(
                min_spacing=min_spacing, use_courtyard=use_courtyard
            )

            # Wrap footprints
            wrappers = [ComponentWrapper(fp) for fp in self.footprints.values()]

            # Run placement
            logger.debug("Running connection-centric placement algorithm...")
            positions = placer.place(wrappers, connections, board_width, board_height)

            # Update footprint positions
            updated_count = 0
            for ref, pos in positions.items():
                if ref in self.footprints:
                    self.footprints[ref].position = pos
                    updated_count += 1
                else:
                    logger.warning(f"Reference {ref} not found in footprints")

            logger.debug(f"Updated {updated_count} footprint positions")
            logger.debug(
                f"Completed {algorithm} placement with {len(connections)} connections"
            )

        elif algorithm == "external":
            # External placement: all components at origin (0,0) with cutout rectangle
            logger.error(f"🔥🔥🔥 EXTERNAL PLACEMENT ALGORITHM STARTED 🔥🔥🔥")
            logger.error(f"🔥 Starting external placement with {len(self.footprints)} components")
            logger.error(f"🔥 Available footprints: {list(self.footprints.keys())}")
            
            # Place all components at origin (0,0)
            updated_count = 0
            for footprint in self.footprints.values():
                old_pos = footprint.position
                logger.error(f"🔥 BEFORE: {footprint.reference} at ({old_pos.x}, {old_pos.y})")
                footprint.position = Point(0.0, 0.0)
                footprint.rotation = 0.0  # Reset rotation to 0
                logger.error(f"🔥 AFTER: {footprint.reference} at ({footprint.position.x}, {footprint.position.y})")
                updated_count += 1
            
            logger.error(f"🔥 All components positioned at origin: {updated_count} components updated")
            
            # Clear existing Edge.Cuts and add only our cutout rectangle
            logger.error(f"🔥 Clearing existing edge cuts...")
            self.clear_edge_cuts()
            logger.error(f"🔥 Edge cuts cleared")
            
            # Add cutout rectangle on Edge.Cuts layer from (100,100) to (200,200)
            cutout_start_x = kwargs.get("cutout_start_x", 100.0)
            cutout_start_y = kwargs.get("cutout_start_y", 100.0) 
            cutout_end_x = kwargs.get("cutout_end_x", 200.0)
            cutout_end_y = kwargs.get("cutout_end_y", 200.0)
            
            logger.error(f"🔥 Creating cutout rectangle: ({cutout_start_x}, {cutout_start_y}) to ({cutout_end_x}, {cutout_end_y})")
            
            # Create cutout rectangle on Edge.Cuts layer
            cutout_rect = Rectangle(
                start=Point(cutout_start_x, cutout_start_y),
                end=Point(cutout_end_x, cutout_end_y),
                layer="Edge.Cuts",
                width=0.05,  # Standard width for edge cuts
                fill=False,
                uuid=str(uuid_module.uuid4()),
            )
            
            logger.error(f"🔥 Adding cutout rectangle to board...")
            self._add_graphic_item(cutout_rect)
            logger.error(f"🔥 Cutout rectangle added")
            
            logger.error(f"🔥🔥🔥 EXTERNAL PLACEMENT COMPLETED SUCCESSFULLY 🔥🔥🔥")
            logger.error(f"🔥 Final component positions after external placement:")
            for footprint in self.footprints.values():
                logger.error(f"🔥   {footprint.reference}: ({footprint.position.x}, {footprint.position.y})")
            
            logger.info(f"External placement completed: {updated_count} components at origin")
            logger.info(f"Added cutout rectangle: ({cutout_start_x}, {cutout_start_y}) to ({cutout_end_x}, {cutout_end_y})")
            
        else:
            raise ValueError(f"Unknown placement algorithm: {algorithm}")

        # Return success for algorithms that don't have explicit return
        from .placement.spiral_placement_v2 import PlacementResult

        return PlacementResult(
            success=True, message=f"Completed {algorithm} placement successfully"
        )

    def get_placement_bbox(self) -> Optional[Tuple[float, float, float, float]]:
        """
        Get bounding box of all placed components.

        Returns:
            Tuple of (min_x, min_y, max_x, max_y) or None if no components
        """
        if not self.pcb_data["footprints"]:
            return None

        from .placement.base import ComponentWrapper
        from .placement.bbox import BoundingBox

        # Get bounding boxes of all footprints
        bboxes = []
        for footprint in self.pcb_data["footprints"]:
            wrapper = ComponentWrapper(footprint)
            bboxes.append(wrapper.bbox)

        if not bboxes:
            return None

        # Merge all bboxes
        combined = bboxes[0]
        for bbox in bboxes[1:]:
            combined = combined.merge(bbox)

        return (combined.min_x, combined.min_y, combined.max_x, combined.max_y)

    @property
    def footprints(self) -> Dict[str, Footprint]:
        """Get footprints as a dictionary keyed by reference."""
        return {fp.reference: fp for fp in self.pcb_data["footprints"]}

    def add_footprint_object(self, footprint: Footprint) -> None:
        """
        Add a pre-created Footprint object to the PCB.

        Args:
            footprint: The Footprint object to add
        """
        # Ensure footprint has a UUID
        if not footprint.uuid:
            footprint.uuid = str(uuid_module.uuid4())

        # Add to PCB
        self.pcb_data["footprints"].append(footprint)
        logger.debug(
            f"Added footprint {footprint.reference} at ({footprint.position.x}, {footprint.position.y})"
        )

    # Design Rule Check (DRC) methods

    def run_drc(
        self,
        output_file: Optional[Union[str, Path]] = None,
        severity: str = "error",
        format: str = "json",
        save_before_drc: bool = True,
        temp_file: bool = False,
    ) -> "DRCResult":
        """
        Run Design Rule Check on this PCB.

        This method saves the PCB to a file (if needed) and runs KiCad's DRC tool.

        Args:
            output_file: Optional output file for the DRC report. If not provided,
                        will use the PCB filename with .drc extension
            severity: Minimum severity to report ("error", "warning", "info")
            format: Output format ("json", "report")
            save_before_drc: Whether to save the PCB before running DRC
            temp_file: If True and no filepath is set, use a temporary file

        Returns:
            DRCResult object with violations, warnings, and unconnected items

        Raises:
            RuntimeError: If PCB has no filepath and temp_file is False
            KiCadCLIError: If DRC command fails
        """
        from .kicad_cli import DRCResult, get_kicad_cli

        # Determine PCB file path
        if hasattr(self, "_filepath") and self._filepath:
            pcb_path = Path(self._filepath)
        elif temp_file:
            import tempfile

            with tempfile.NamedTemporaryFile(suffix=".kicad_pcb", delete=False) as tf:
                pcb_path = Path(tf.name)
                self.save(pcb_path)
                save_before_drc = False  # Already saved
        else:
            raise RuntimeError(
                "PCB has no filepath. Either load from a file, save to a file first, "
                "or use temp_file=True"
            )

        # Save if requested
        if save_before_drc:
            self.save(pcb_path)

        # Run DRC
        cli = get_kicad_cli()
        result = cli.run_drc(
            pcb_file=pcb_path, output_file=output_file, severity=severity, format=format
        )

        # Clean up temp file if used
        if temp_file and pcb_path.exists():
            pcb_path.unlink()

        return result

    def check_basic_rules(self) -> Dict[str, List[str]]:
        """
        Perform basic design rule checks without using KiCad CLI.

        This provides quick validation of common issues:
        - Components outside board outline
        - Overlapping footprints
        - Unconnected pads
        - Tracks with zero width
        - Missing board outline

        Returns:
            Dictionary with rule names as keys and lists of violation messages
        """
        violations = {
            "board_outline": [],
            "component_placement": [],
            "connectivity": [],
            "tracks": [],
        }

        # Check for board outline
        edge_cuts = [
            item
            for item in self.pcb_data.get("graphics", [])
            if hasattr(item, "layer") and item.layer == "Edge.Cuts"
        ]
        if not edge_cuts:
            violations["board_outline"].append("No board outline defined")

        # Check for overlapping footprints (simple bounding box check)
        footprints = self.pcb_data.get("footprints", [])
        for i, fp1 in enumerate(footprints):
            for fp2 in footprints[i + 1 :]:
                # Simple distance check - could be improved with actual bbox
                dx = abs(fp1.position.x - fp2.position.x)
                dy = abs(fp1.position.y - fp2.position.y)
                if dx < 5 and dy < 5:  # Within 5mm - potentially overlapping
                    violations["component_placement"].append(
                        f"Potential overlap: {fp1.reference} and {fp2.reference}"
                    )

        # Check for unconnected pads
        ratsnest = self.get_ratsnest()
        if ratsnest:
            violations["connectivity"].append(
                f"{len(ratsnest)} unrouted connections in ratsnest"
            )

        # Check tracks
        tracks = self.pcb_data.get("tracks", [])
        for track in tracks:
            if hasattr(track, "width") and track.width <= 0:
                violations["tracks"].append(
                    f"Track with zero or negative width at ({track.start.x}, {track.start.y})"
                )

        # Remove empty violation categories
        violations = {k: v for k, v in violations.items() if v}

        return violations

    def export_gerbers(
        self,
        output_dir: Union[str, Path],
        layers: Optional[List[str]] = None,
        save_before_export: bool = True,
    ) -> List[Path]:
        """
        Export Gerber files for manufacturing.

        Args:
            output_dir: Directory to save Gerber files
            layers: Optional list of layer names to export. If None, exports standard set
            save_before_export: Whether to save the PCB before exporting

        Returns:
            List of generated Gerber file paths

        Raises:
            RuntimeError: If PCB has no filepath
        """
        from .kicad_cli import get_kicad_cli

        # Ensure PCB is saved
        if not hasattr(self, "_filepath") or not self._filepath:
            raise RuntimeError("PCB must be saved to a file before exporting Gerbers")

        if save_before_export:
            self.save()

        # Default layers if not specified
        if layers is None:
            layers = [
                "F.Cu",
                "B.Cu",  # Copper layers
                "F.Mask",
                "B.Mask",  # Solder mask
                "F.SilkS",
                "B.SilkS",  # Silkscreen
                "F.Paste",
                "B.Paste",  # Solder paste
                "Edge.Cuts",  # Board outline
            ]

        cli = get_kicad_cli()
        return cli.export_gerbers(
            pcb_file=self._filepath, output_dir=output_dir, layers=layers
        )

    def export_drill(
        self, output_dir: Union[str, Path], save_before_export: bool = True
    ) -> Tuple[Optional[Path], Optional[Path]]:
        """
        Export drill files for manufacturing.

        Args:
            output_dir: Directory to save drill files
            save_before_export: Whether to save the PCB before exporting

        Returns:
            Tuple of (plated_holes_file, non_plated_holes_file)

        Raises:
            RuntimeError: If PCB has no filepath
        """
        from .kicad_cli import get_kicad_cli

        if not hasattr(self, "_filepath") or not self._filepath:
            raise RuntimeError(
                "PCB must be saved to a file before exporting drill files"
            )

        if save_before_export:
            self.save()

        cli = get_kicad_cli()
        return cli.export_drill(pcb_file=self._filepath, output_dir=output_dir)

    def export_pick_and_place(
        self,
        output_file: Union[str, Path],
        side: str = "both",
        smd_only: bool = False,
        save_before_export: bool = True,
    ) -> Path:
        """
        Export pick and place file for assembly.

        Args:
            output_file: Output file path
            side: Which side to export ("front", "back", "both")
            smd_only: Only include SMD components
            save_before_export: Whether to save the PCB before exporting

        Returns:
            Path to generated position file

        Raises:
            RuntimeError: If PCB has no filepath
        """
        from .kicad_cli import get_kicad_cli

        if not hasattr(self, "_filepath") or not self._filepath:
            raise RuntimeError(
                "PCB must be saved to a file before exporting position file"
            )

        if save_before_export:
            self.save()

        cli = get_kicad_cli()
        return cli.export_pos(
            pcb_file=self._filepath,
            output_file=output_file,
            side=side,
            smd_only=smd_only,
        )

    # Footprint library integration methods

    def search_footprints(
        self, query: str = "", filters: Optional[Dict[str, Any]] = None
    ) -> List[FootprintInfo]:
        """
        Search for footprints in the library cache.

        Args:
            query: Search string (searches in name, description, tags, keywords)
            filters: Dictionary of filters:
                - footprint_type: "SMD", "THT", "Mixed"
                - pad_count: exact number or range (min, max)
                - max_size: maximum size in mm (width, height)
                - library: specific library name

        Returns:
            List of matching FootprintInfo objects

        Example:
            # Search for 0603 SMD resistors
            results = pcb.search_footprints("0603", filters={"footprint_type": "SMD"})

            # Search for 8-pin SOIC packages
            results = pcb.search_footprints("SOIC", filters={"pad_count": 8})
        """
        cache = get_footprint_cache()
        return cache.search_footprints(query, filters)

    def get_footprint_info(self, footprint_id: str) -> Optional[FootprintInfo]:
        """
        Get detailed information about a specific footprint.

        Args:
            footprint_id: Footprint ID in format "Library:Footprint"

        Returns:
            FootprintInfo object or None if not found

        Example:
            info = pcb.get_footprint_info("Resistor_SMD:R_0603_1608Metric")
            if info:
                print(f"Footprint: {info.name}")
                print(f"Pads: {info.pad_count}")
                print(f"Size: {info.body_size[0]}x{info.body_size[1]}mm")
        """
        cache = get_footprint_cache()
        return cache.get_footprint(footprint_id)

    def add_footprint_from_library(
        self,
        footprint_id: str,
        reference: str,
        x: float,
        y: float,
        rotation: float = 0.0,
        value: Optional[str] = None,
    ) -> Optional[Footprint]:
        """
        Add a footprint from the library cache with full pad and courtyard information.

        Args:
            footprint_id: Footprint ID in format "Library:Footprint"
            reference: Reference designator (e.g., "R1", "U1")
            x: X position in mm
            y: Y position in mm
            rotation: Rotation in degrees (default: 0)
            value: Component value (optional)

        Returns:
            The created Footprint object or None if footprint not found

        Example:
            # Add a 0603 resistor from the library
            footprint = pcb.add_footprint_from_library(
                "Resistor_SMD:R_0603_1608Metric",
                "R1", 50, 50, value="10k"
            )
        """
        cache = get_footprint_cache()
        footprint_data = cache.get_footprint_data(footprint_id)

        if not footprint_data:
            logger.error(f"Footprint {footprint_id} not found in library cache")
            return None

        # Parse library and name from footprint_id
        if ":" in footprint_id:
            library, name = footprint_id.split(":", 1)
        else:
            library = "Unknown"
            name = footprint_id

        # Create footprint with full data from library
        footprint = self._create_footprint_from_library_data(
            library, name, reference, x, y, rotation, value, footprint_data
        )

        if footprint:
            self.pcb_data["footprints"].append(footprint)
            logger.debug(f"Added footprint {reference} ({footprint_id}) at ({x}, {y})")

        return footprint

    def _create_footprint_from_library_data(
        self,
        library: str,
        name: str,
        reference: str,
        x: float,
        y: float,
        rotation: float,
        value: Optional[str],
        library_data: Dict[str, Any],
    ) -> Optional[Footprint]:
        """Create a Footprint object from library data."""
        try:
            # Start with basic footprint
            footprint = Footprint(
                library=library,
                name=name,
                position=Point(x, y),
                rotation=rotation,
                reference=reference,
                value=value or "",
                uuid=str(uuid_module.uuid4()),
            )

            # Add properties
            footprint.properties = [
                Property("Reference", reference, Point(0, -2), "F.SilkS"),
                Property("Value", value or "", Point(0, 2), "F.Fab"),
                Property("Footprint", f"{library}:{name}", Point(0, 0), "F.Fab"),
                Property("Datasheet", "", Point(0, 0), "F.Fab"),
            ]

            # Parse pads from library data
            if "pad" in library_data:
                for pad_data in library_data["pad"]:
                    pad = self._parse_library_pad(pad_data)
                    if pad:
                        footprint.pads.append(pad)

            # Parse graphics (lines, arcs, text) from library data
            if "fp_line" in library_data:
                for line_data in library_data["fp_line"]:
                    line = self._parse_library_line(line_data)
                    if line:
                        footprint.lines.append(line)

            if "fp_arc" in library_data:
                for arc_data in library_data["fp_arc"]:
                    arc = self._parse_library_arc(arc_data)
                    if arc:
                        footprint.arcs.append(arc)

            if "fp_text" in library_data:
                for text_data in library_data["fp_text"]:
                    text = self._parse_library_text(text_data)
                    if text:
                        # Replace placeholders with actual values
                        if text.text == "${REFERENCE}":
                            text.text = reference
                        elif text.text == "${VALUE}":
                            text.text = value or ""
                        footprint.texts.append(text)

            if "fp_rect" in library_data:
                for rect_data in library_data["fp_rect"]:
                    rect = self._parse_library_rect(rect_data)
                    if rect:
                        footprint.rectangles.append(rect)

            # Set attributes
            if "attr" in library_data:
                for attr_data in library_data["attr"]:
                    if "value_0" in attr_data:
                        attr_value = str(attr_data["value_0"])
                        if attr_value == "smd":
                            footprint.attr = "smd"
                        elif attr_value == "through_hole":
                            footprint.attr = "through_hole"

            return footprint

        except Exception as e:
            logger.error(f"Error creating footprint from library data: {e}")
            return None

    def _parse_library_pad(
        self, pad_data: Union[List, Dict[str, Any]]
    ) -> Optional[Pad]:
        """Parse pad data from library format."""
        try:
            # The pad_data from _sexp_to_dict is always a list format
            # pad_data is like ['1', 'smd', 'rect', ['at', x, y], ['size', w, h], ...]
            if not isinstance(pad_data, list) or len(pad_data) < 3:
                logger.error(f"Invalid pad data format: {pad_data}")
                return None

            pad_num = str(pad_data[0]) if len(pad_data) > 0 else ""
            pad_type = str(pad_data[1]) if len(pad_data) > 1 else "smd"
            pad_shape = str(pad_data[2]) if len(pad_data) > 2 else "rect"

            # Find position and size in the list
            x = y = rotation = 0
            width = height = 1.0
            layers = []
            drill = None
            net = None
            net_name = None
            pinfunction = None
            pintype = None
            roundrect_rratio = None
            properties = {}

            for item in pad_data[3:]:
                if isinstance(item, list) and len(item) > 0:
                    cmd = str(item[0])
                    if cmd == "at" and len(item) >= 3:
                        x = float(item[1])
                        y = float(item[2])
                        rotation = float(item[3]) if len(item) > 3 else 0
                    elif cmd == "size" and len(item) >= 3:
                        width = float(item[1])
                        height = float(item[2])
                    elif cmd == "layers":
                        # Layers are the remaining items in the list
                        for layer in item[1:]:
                            if isinstance(layer, str):
                                layers.append(layer)
                            elif isinstance(layer, sexpdata.Symbol):
                                layers.append(str(layer))
                    elif cmd == "drill" and len(item) >= 2:
                        # Check if it's an oval drill
                        logger.debug(f"Processing drill item: {item}")
                        try:
                            # Try to parse as a simple float first
                            drill = float(item[1])
                            logger.debug(f"Found circular drill: diameter={drill}")
                        except (ValueError, TypeError):
                            # Not a simple float, check if it's an oval drill
                            if len(item) >= 4 and str(item[1]) == "oval":
                                # Oval drill: [drill, 'oval', width, height]
                                logger.debug(
                                    f"Found oval drill: width={item[2]}, height={item[3]}"
                                )
                                drill = {
                                    "shape": "oval",
                                    "width": float(item[2]),
                                    "height": float(item[3]),
                                }
                            else:
                                logger.warning(f"Unknown drill format: {item}")
                                drill = None
                    elif cmd == "net" and len(item) >= 3:
                        # Net connection: ['net', number, name]
                        net = int(item[1])
                        net_name = str(item[2])
                    elif cmd == "pinfunction" and len(item) >= 2:
                        pinfunction = str(item[1])
                    elif cmd == "pintype" and len(item) >= 2:
                        pintype = str(item[1])
                    elif cmd == "roundrect_rratio" and len(item) >= 2:
                        roundrect_rratio = float(item[1])
                    elif cmd == "property" and len(item) >= 2:
                        # Property like pad_prop_heatsink
                        prop_name = str(item[1])
                        properties[prop_name] = True

            # Default layers if none specified
            if not layers:
                if pad_type == "smd":
                    layers = ["F.Cu", "F.Paste", "F.Mask"]
                else:
                    layers = ["*.Cu", "*.Mask"]

            # Map pad type
            if pad_type in ["thru_hole", "smd", "np_thru_hole", "connect"]:
                pad_type_enum = pad_type
            else:
                # Default to thru_hole for unknown types
                pad_type_enum = "thru_hole"

            # Map pad shape
            shape_map = {
                "circle": "circle",
                "rect": "rect",
                "oval": "oval",
                "roundrect": "roundrect",
            }
            pad_shape_enum = shape_map.get(pad_shape, "rect")

            # Create pad
            pad = Pad(
                number=pad_num,
                type=pad_type_enum,
                shape=pad_shape_enum,
                position=Point(x, y),
                size=(width, height),
                rotation=rotation,  # Add the parsed rotation
                layers=layers,
                uuid=str(uuid_module.uuid4()),
            )

            # Set drill info for through-hole pads (both plated and non-plated)
            if pad_type in ["thru_hole", "np_thru_hole"] and drill is not None:
                pad.drill = drill

            # Set net connection if present
            if net is not None:
                pad.net = net
                pad.net_name = net_name

            # Set pin metadata if present
            if pinfunction is not None:
                pad.pinfunction = pinfunction
            if pintype is not None:
                pad.pintype = pintype

            # Set roundrect ratio if present
            if roundrect_rratio is not None:
                pad.roundrect_rratio = roundrect_rratio

            # Set properties if present
            if properties:
                pad.properties = properties

            return pad

        except Exception as e:
            logger.error(f"Error parsing library pad: {e}")
            return None

    def _parse_library_line(self, line_data: List) -> Optional[Line]:
        """Parse line data from library format."""
        try:
            # Find start and end points
            start_x = start_y = end_x = end_y = 0.0
            layer = "F.SilkS"
            width = 0.1

            for item in line_data:
                if isinstance(item, list) and len(item) > 0:
                    cmd = str(item[0])
                    if cmd == "start" and len(item) >= 3:
                        start_x = float(item[1])
                        start_y = float(item[2])
                    elif cmd == "end" and len(item) >= 3:
                        end_x = float(item[1])
                        end_y = float(item[2])
                    elif cmd == "layer" and len(item) >= 2:
                        layer = str(item[1])
                    elif cmd == "stroke":
                        # Parse stroke info
                        for stroke_item in item[1:]:
                            if isinstance(stroke_item, list) and len(stroke_item) >= 2:
                                if str(stroke_item[0]) == "width":
                                    width = float(stroke_item[1])

            return Line(
                start=Point(start_x, start_y),
                end=Point(end_x, end_y),
                layer=layer,
                width=width,
                uuid=str(uuid_module.uuid4()),
            )

        except Exception as e:
            logger.error(f"Error parsing library line: {e}")
            return None

    def _parse_library_arc(self, arc_data: List) -> Optional[Arc]:
        """Parse arc data from library format."""
        try:
            # Find start, mid, and end points
            start_x = start_y = mid_x = mid_y = end_x = end_y = 0.0
            layer = "F.SilkS"
            width = 0.1

            for item in arc_data:
                if isinstance(item, list) and len(item) > 0:
                    cmd = str(item[0])
                    if cmd == "start" and len(item) >= 3:
                        start_x = float(item[1])
                        start_y = float(item[2])
                    elif cmd == "mid" and len(item) >= 3:
                        mid_x = float(item[1])
                        mid_y = float(item[2])
                    elif cmd == "end" and len(item) >= 3:
                        end_x = float(item[1])
                        end_y = float(item[2])
                    elif cmd == "layer" and len(item) >= 2:
                        layer = str(item[1])
                    elif cmd == "stroke":
                        # Parse stroke info
                        for stroke_item in item[1:]:
                            if isinstance(stroke_item, list) and len(stroke_item) >= 2:
                                if str(stroke_item[0]) == "width":
                                    width = float(stroke_item[1])

            return Arc(
                start=Point(start_x, start_y),
                mid=Point(mid_x, mid_y),
                end=Point(end_x, end_y),
                layer=layer,
                width=width,
                uuid=str(uuid_module.uuid4()),
            )

        except Exception as e:
            logger.error(f"Error parsing library arc: {e}")
            return None

    def _parse_library_text(self, text_data: List) -> Optional[Text]:
        """Parse text data from library format."""
        try:
            # text_data format: ['reference'/'value'/'user', 'text_content', ...]
            if len(text_data) < 2:
                return None

            text_type = str(text_data[0]) if text_data else "user"
            text_content = str(text_data[1]) if len(text_data) > 1 else ""

            # Default values
            x = y = 0.0
            layer = "F.SilkS"
            size_x = size_y = 1.0
            thickness = 0.15

            # Parse additional attributes
            for item in text_data[2:]:
                if isinstance(item, list) and len(item) > 0:
                    cmd = str(item[0])
                    if cmd == "at" and len(item) >= 3:
                        x = float(item[1])
                        y = float(item[2])
                    elif cmd == "layer" and len(item) >= 2:
                        layer = str(item[1])
                    elif cmd == "effects":
                        # Parse effects for font info
                        for effect_item in item[1:]:
                            if (
                                isinstance(effect_item, list)
                                and str(effect_item[0]) == "font"
                            ):
                                for font_item in effect_item[1:]:
                                    if (
                                        isinstance(font_item, list)
                                        and len(font_item) >= 2
                                    ):
                                        if (
                                            str(font_item[0]) == "size"
                                            and len(font_item) >= 3
                                        ):
                                            size_x = float(font_item[1])
                                            size_y = float(font_item[2])
                                        elif str(font_item[0]) == "thickness":
                                            thickness = float(font_item[1])

            return Text(
                text=text_content,
                position=Point(x, y),
                layer=layer,
                size=(size_x, size_y),
                thickness=thickness,
                uuid=str(uuid_module.uuid4()),
            )

        except Exception as e:
            logger.error(f"Error parsing library text: {e}")
            return None

    def _parse_library_rect(self, rect_data: List) -> Optional[Rectangle]:
        """Parse rectangle data from library format."""
        try:
            # rect_data is like [['start', x1, y1], ['end', x2, y2], ['layer', 'F.CrtYd'], ...]
            if not isinstance(rect_data, list):
                return None

            # Find start, end, layer, and stroke info
            start_x = start_y = end_x = end_y = 0
            layer = "F.CrtYd"
            width = 0.05
            fill = False

            for item in rect_data:
                if isinstance(item, list) and len(item) > 0:
                    cmd = str(item[0])
                    if cmd == "start" and len(item) >= 3:
                        start_x = float(item[1])
                        start_y = float(item[2])
                    elif cmd == "end" and len(item) >= 3:
                        end_x = float(item[1])
                        end_y = float(item[2])
                    elif cmd == "layer" and len(item) >= 2:
                        layer = str(item[1])
                    elif cmd == "stroke" and len(item) >= 2:
                        # Parse stroke properties
                        for stroke_item in item[1:]:
                            if isinstance(stroke_item, list) and len(stroke_item) >= 2:
                                if str(stroke_item[0]) == "width":
                                    width = float(stroke_item[1])
                    elif cmd == "fill" and len(item) >= 2:
                        fill_type = str(item[1])
                        fill = fill_type != "no" and fill_type != "none"

            return Rectangle(
                start=Point(start_x, start_y),
                end=Point(end_x, end_y),
                layer=layer,
                width=width,
                fill=fill,
                uuid=str(uuid_module.uuid4()),
            )

        except Exception as e:
            logger.error(f"Error parsing library rectangle: {e}")
            return None

    def list_available_libraries(self) -> List[str]:
        """
        Get list of all available footprint libraries.

        Returns:
            List of library names

        Example:
            libraries = pcb.list_available_libraries()
            for lib in libraries:
                print(f"Library: {lib}")
        """
        cache = get_footprint_cache()
        return cache.list_libraries()

    def refresh_footprint_cache(self):
        """
        Refresh the footprint library cache.

        This rescans all library paths and updates the cache.
        Useful after installing new libraries or modifying existing ones.
        """
        cache = get_footprint_cache()
        cache.refresh_cache()
        logger.debug("Footprint library cache refreshed")
