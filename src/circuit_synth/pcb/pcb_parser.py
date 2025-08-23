"""
Parser for KiCad PCB files using S-expressions.
"""

import logging
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import sexpdata

from .pcb_formatter import PCBFormatter
from .types import (
    Arc,
    Footprint,
    Layer,
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

logger = logging.getLogger(__name__)


class PCBParser:
    """
    Parser for KiCad PCB files.

    Handles reading and writing .kicad_pcb files using S-expressions.
    """

    def __init__(self):
        """Initialize the parser."""
        self.version = 20241229  # KiCad 9 version
        self.generator = "pcbnew"
        self.generator_version = "9.0"

    def parse_file(self, filepath: Union[str, Path]) -> Dict[str, Any]:
        """
        Parse a KiCad PCB file.

        Args:
            filepath: Path to the .kicad_pcb file

        Returns:
            Dictionary containing parsed PCB data
        """
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            return self.parse_string(content)
        except Exception as e:
            logger.error(f"Error parsing {filepath}: {e}")
            raise

    def parse_string(self, content: str) -> Dict[str, Any]:
        """
        Parse PCB content from a string.

        Args:
            content: S-expression string content

        Returns:
            Dictionary containing parsed PCB data
        """
        sexp = sexpdata.loads(content)

        if (
            not self._is_sexp_list(sexp)
            or self._get_symbol_name(sexp[0]) != "kicad_pcb"
        ):
            raise ValueError("Invalid KiCad PCB format")

        pcb_data = {
            "version": None,
            "generator": None,
            "general": {},
            "paper": "A4",
            "layers": [],
            "setup": {},
            "nets": [],
            "footprints": [],
            "vias": [],
            "tracks": [],
            "zones": [],
            "groups": [],
            "embedded_fonts": False,
        }

        # Parse PCB elements
        for element in sexp[1:]:
            if not self._is_sexp_list(element):
                continue

            element_type = self._get_symbol_name(element[0])

            if element_type == "version":
                pcb_data["version"] = element[1]
            elif element_type == "generator":
                pcb_data["generator"] = element[1]
                if len(element) > 2:
                    gen_version = self._find_element(element, "generator_version")
                    if gen_version:
                        pcb_data["generator_version"] = gen_version[1]
            elif element_type == "general":
                pcb_data["general"] = self._parse_general(element)
            elif element_type == "paper":
                pcb_data["paper"] = element[1]
            elif element_type == "layers":
                pcb_data["layers"] = self._parse_layers(element)
            elif element_type == "setup":
                pcb_data["setup"] = element  # Store raw for now
            elif element_type == "net":
                net = self._parse_net(element)
                if net:
                    pcb_data["nets"].append(net)
            elif element_type == "footprint":
                footprint = self._parse_footprint(element)
                if footprint:
                    pcb_data["footprints"].append(footprint)
            elif element_type == "via":
                via = self._parse_via(element)
                if via:
                    pcb_data["vias"].append(via)
            elif element_type == "segment":
                track = self._parse_track(element)
                if track:
                    pcb_data["tracks"].append(track)
            elif element_type == "gr_line":
                line = self._parse_line(element)
                if line:
                    if "graphics" not in pcb_data:
                        pcb_data["graphics"] = []
                    pcb_data["graphics"].append(line)
            elif element_type == "gr_rect":
                rect = self._parse_rectangle(element)
                if rect:
                    if "graphics" not in pcb_data:
                        pcb_data["graphics"] = []
                    pcb_data["graphics"].append(rect)
            elif element_type == "zone":
                zone = self._parse_zone(element)
                if zone:
                    pcb_data["zones"].append(zone)
            elif element_type == "embedded_fonts":
                pcb_data["embedded_fonts"] = element[1] == "yes"

        return pcb_data

    def write_file(self, pcb_data: Dict[str, Any], filepath: Union[str, Path]):
        """
        Write PCB data to a file.

        Args:
            pcb_data: PCB data dictionary
            filepath: Path to write to
        """
        filepath = Path(filepath)
        content = self.dumps(pcb_data)

        # Ensure directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

    def dumps(self, pcb_data: Dict[str, Any]) -> str:
        """
        Convert PCB data to S-expression string.

        Args:
            pcb_data: PCB data dictionary

        Returns:
            S-expression string
        """
        sexp = self._pcb_to_sexp(pcb_data)

        # Use our custom formatter that handles symbols correctly
        formatter = PCBFormatter()
        return formatter.format_pcb(sexp)

    # Helper methods for parsing

    def _is_sexp_list(self, obj: Any) -> bool:
        """Check if object is a list (S-expression)."""
        return isinstance(obj, list)

    def _get_symbol_name(self, obj: Any) -> Optional[str]:
        """Get the name of a symbol if it is one."""
        if isinstance(obj, sexpdata.Symbol):
            return str(obj)
        return None

    def _find_element(self, sexp: List, name: str) -> Optional[Any]:
        """Find an element by name in an S-expression."""
        for item in sexp:
            if self._is_sexp_list(item) and self._get_symbol_name(item[0]) == name:
                return item
        return None

    def _find_all_elements(self, sexp: List, name: str) -> List[Any]:
        """Find all elements by name in an S-expression."""
        results = []
        for item in sexp:
            if self._is_sexp_list(item) and self._get_symbol_name(item[0]) == name:
                results.append(item)
        return results

    def _get_value(self, sexp: List, name: str, default: Any = None) -> Any:
        """Get the value of a named element."""
        element = self._find_element(sexp, name)
        if element and len(element) > 1:
            return element[1]
        return default

    def _parse_general(self, sexp: List) -> Dict[str, Any]:
        """Parse general section."""
        general = {}
        general["thickness"] = self._get_value(sexp, "thickness", 1.6)
        general["legacy_teardrops"] = (
            self._get_value(sexp, "legacy_teardrops", "no") == "yes"
        )
        return general

    def _parse_layers(self, sexp: List) -> List[Dict[str, Any]]:
        """Parse layers section."""
        layers = []
        for item in sexp[1:]:
            if self._is_sexp_list(item) and len(item) >= 3:
                layer = {"number": item[0], "canonical_name": item[1], "type": item[2]}
                if len(item) > 3:
                    layer["user_name"] = item[3]
                layers.append(layer)
        return layers

    def _parse_net(self, sexp: List) -> Optional[Net]:
        """Parse a net definition."""
        if len(sexp) < 3:
            return None
        return Net(number=sexp[1], name=sexp[2])

    def _parse_footprint(self, sexp: List) -> Optional[Footprint]:
        """Parse a footprint from S-expression."""
        try:
            # Get library ID (e.g., "Resistor_SMD:R_0603_1608Metric")
            lib_id = sexp[1]
            if ":" in lib_id:
                library, name = lib_id.split(":", 1)
            else:
                library = ""
                name = lib_id

            # Get layer
            layer_elem = self._find_element(sexp, "layer")
            layer = layer_elem[1] if layer_elem else "F.Cu"

            # Get UUID
            uuid_elem = self._find_element(sexp, "uuid")
            fp_uuid = uuid_elem[1] if uuid_elem else str(uuid.uuid4())

            # Get position
            at_elem = self._find_element(sexp, "at")
            if not at_elem or len(at_elem) < 3:
                return None

            position = Point(float(at_elem[1]), float(at_elem[2]))
            rotation = float(at_elem[3]) if len(at_elem) > 3 else 0.0

            # Create footprint
            footprint = Footprint(
                library=library,
                name=name,
                position=position,
                rotation=rotation,
                layer=layer,
                uuid=fp_uuid,
            )

            # Parse description and tags
            footprint.descr = self._get_value(sexp, "descr", "")
            footprint.tags = self._get_value(sexp, "tags", "")

            # Parse attributes
            attr_elem = self._find_element(sexp, "attr")
            if attr_elem:
                footprint.attr = " ".join(str(a) for a in attr_elem[1:])

            # Parse properties
            for prop_elem in self._find_all_elements(sexp, "property"):
                prop = self._parse_property(prop_elem)
                if prop:
                    footprint.properties.append(prop)
                    # Set reference and value
                    if prop.name == "Reference":
                        footprint.reference = prop.value
                    elif prop.name == "Value":
                        footprint.value = prop.value

            # Parse path info
            path_elem = self._find_element(sexp, "path")
            if path_elem:
                footprint.path = path_elem[1]
            sheetname_elem = self._find_element(sexp, "sheetname")
            if sheetname_elem:
                footprint.sheetname = sheetname_elem[1]
            sheetfile_elem = self._find_element(sexp, "sheetfile")
            if sheetfile_elem:
                footprint.sheetfile = sheetfile_elem[1]

            # Parse graphical elements
            for line_elem in self._find_all_elements(sexp, "fp_line"):
                line = self._parse_line(line_elem)
                if line:
                    footprint.lines.append(line)

            for arc_elem in self._find_all_elements(sexp, "fp_arc"):
                arc = self._parse_arc(arc_elem)
                if arc:
                    footprint.arcs.append(arc)

            for text_elem in self._find_all_elements(sexp, "fp_text"):
                text = self._parse_text(text_elem)
                if text:
                    footprint.texts.append(text)

            # Parse pads
            for pad_elem in self._find_all_elements(sexp, "pad"):
                pad = self._parse_pad(pad_elem)
                if pad:
                    footprint.pads.append(pad)

            # Parse 3D model
            model_elem = self._find_element(sexp, "model")
            if model_elem:
                footprint.model_path = model_elem[1]
                # Parse offset, scale, rotate if present

            return footprint

        except Exception as e:
            logger.error(f"Error parsing footprint: {e}")
            return None

    def _parse_property(self, sexp: List) -> Optional[Property]:
        """Parse a property element."""
        if len(sexp) < 3:
            return None

        name = sexp[1]
        value = sexp[2]

        # Get position
        at_elem = self._find_element(sexp, "at")
        if at_elem and len(at_elem) >= 3:
            position = Point(float(at_elem[1]), float(at_elem[2]))
        else:
            position = Point(0, 0)

        # Get layer
        layer_elem = self._find_element(sexp, "layer")
        layer = layer_elem[1] if layer_elem else "F.SilkS"

        # Get UUID
        uuid_elem = self._find_element(sexp, "uuid")
        prop_uuid = uuid_elem[1] if uuid_elem else str(uuid.uuid4())

        prop = Property(
            name=name, value=value, position=position, layer=layer, uuid=prop_uuid
        )

        # Parse effects
        effects_elem = self._find_element(sexp, "effects")
        if effects_elem:
            font_elem = self._find_element(effects_elem, "font")
            if font_elem:
                size_elem = self._find_element(font_elem, "size")
                if size_elem and len(size_elem) >= 3:
                    prop.size = (float(size_elem[1]), float(size_elem[2]))
                thickness_elem = self._find_element(font_elem, "thickness")
                if thickness_elem:
                    prop.thickness = float(thickness_elem[1])

        return prop

    def _parse_pad(self, sexp: List) -> Optional[Pad]:
        """Parse a pad element."""
        if len(sexp) < 4:
            return None

        number = str(sexp[1])
        pad_type = sexp[2]
        shape = sexp[3]

        # Get position
        at_elem = self._find_element(sexp, "at")
        if at_elem and len(at_elem) >= 3:
            position = Point(float(at_elem[1]), float(at_elem[2]))
        else:
            position = Point(0, 0)

        # Get size
        size_elem = self._find_element(sexp, "size")
        if size_elem and len(size_elem) >= 3:
            size = (float(size_elem[1]), float(size_elem[2]))
        else:
            size = (1.0, 1.0)

        # Get layers
        layers_elem = self._find_element(sexp, "layers")
        if layers_elem:
            layers = [str(l) for l in layers_elem[1:]]
        else:
            layers = []

        pad = Pad(
            number=number,
            type=pad_type,
            shape=shape,
            position=position,
            size=size,
            layers=layers,
        )

        # Get drill if present
        drill_elem = self._find_element(sexp, "drill")
        if drill_elem:
            if len(drill_elem) >= 4 and str(drill_elem[1]) == "oval":
                # Oval drill
                pad.drill = {
                    "shape": "oval",
                    "width": float(drill_elem[2]),
                    "height": float(drill_elem[3]),
                }
            else:
                # Circular drill
                pad.drill = float(drill_elem[1])

        # Get net
        net_elem = self._find_element(sexp, "net")
        if net_elem and len(net_elem) >= 3:
            pad.net = net_elem[1]
            pad.net_name = net_elem[2]

        # Get roundrect ratio
        rratio_elem = self._find_element(sexp, "roundrect_rratio")
        if rratio_elem:
            pad.roundrect_rratio = float(rratio_elem[1])

        # Get UUID
        uuid_elem = self._find_element(sexp, "uuid")
        pad.uuid = uuid_elem[1] if uuid_elem else str(uuid.uuid4())

        return pad

    def _parse_line(self, sexp: List) -> Optional[Line]:
        """Parse a line element."""
        start_elem = self._find_element(sexp, "start")
        end_elem = self._find_element(sexp, "end")

        if not start_elem or not end_elem:
            return None

        start = Point(float(start_elem[1]), float(start_elem[2]))
        end = Point(float(end_elem[1]), float(end_elem[2]))

        layer_elem = self._find_element(sexp, "layer")
        layer = layer_elem[1] if layer_elem else "F.SilkS"

        line = Line(start=start, end=end, layer=layer)

        # Parse stroke
        stroke_elem = self._find_element(sexp, "stroke")
        if stroke_elem:
            width_elem = self._find_element(stroke_elem, "width")
            if width_elem:
                line.width = float(width_elem[1])
            type_elem = self._find_element(stroke_elem, "type")
            if type_elem:
                line.type = type_elem[1]

        # Get UUID
        uuid_elem = self._find_element(sexp, "uuid")
        line.uuid = uuid_elem[1] if uuid_elem else str(uuid.uuid4())

        return line

    def _parse_arc(self, sexp: List) -> Optional[Arc]:
        """Parse an arc element."""
        start_elem = self._find_element(sexp, "start")
        mid_elem = self._find_element(sexp, "mid")
        end_elem = self._find_element(sexp, "end")

        if not start_elem or not mid_elem or not end_elem:
            return None

        start = Point(float(start_elem[1]), float(start_elem[2]))
        mid = Point(float(mid_elem[1]), float(mid_elem[2]))
        end = Point(float(end_elem[1]), float(end_elem[2]))

        layer_elem = self._find_element(sexp, "layer")
        layer = layer_elem[1] if layer_elem else "F.SilkS"

        arc = Arc(start=start, mid=mid, end=end, layer=layer)

        # Parse stroke
        stroke_elem = self._find_element(sexp, "stroke")
        if stroke_elem:
            width_elem = self._find_element(stroke_elem, "width")
            if width_elem:
                arc.width = float(width_elem[1])
            type_elem = self._find_element(stroke_elem, "type")
            if type_elem:
                arc.type = type_elem[1]

        # Get UUID
        uuid_elem = self._find_element(sexp, "uuid")
        arc.uuid = uuid_elem[1] if uuid_elem else str(uuid.uuid4())

        return arc

    def _parse_rectangle(self, sexp: List) -> Optional[Rectangle]:
        """Parse a rectangle element."""
        start_elem = self._find_element(sexp, "start")
        end_elem = self._find_element(sexp, "end")

        if not start_elem or not end_elem:
            return None

        start = Point(float(start_elem[1]), float(start_elem[2]))
        end = Point(float(end_elem[1]), float(end_elem[2]))

        layer_elem = self._find_element(sexp, "layer")
        layer = layer_elem[1] if layer_elem else "F.SilkS"

        rect = Rectangle(start=start, end=end, layer=layer)

        # Parse stroke
        stroke_elem = self._find_element(sexp, "stroke")
        if stroke_elem:
            width_elem = self._find_element(stroke_elem, "width")
            if width_elem:
                rect.width = float(width_elem[1])

        # Parse fill
        fill_elem = self._find_element(sexp, "fill")
        if fill_elem and len(fill_elem) > 1:
            # Handle both "no" and "none" as False
            # Convert to string in case it's a Symbol object
            fill_value = str(fill_elem[1])
            rect.fill = fill_value not in ["no", "none"]

        # Get UUID
        uuid_elem = self._find_element(sexp, "uuid")
        rect.uuid = uuid_elem[1] if uuid_elem else str(uuid.uuid4())

        return rect

    def _parse_text(self, sexp: List) -> Optional[Text]:
        """Parse a text element."""
        if len(sexp) < 3:
            return None

        text_type = sexp[1]  # "reference", "value", "user"
        text_value = sexp[2]

        at_elem = self._find_element(sexp, "at")
        if at_elem and len(at_elem) >= 3:
            position = Point(float(at_elem[1]), float(at_elem[2]))
        else:
            position = Point(0, 0)

        layer_elem = self._find_element(sexp, "layer")
        layer = layer_elem[1] if layer_elem else "F.SilkS"

        text = Text(text=text_value, position=position, layer=layer)

        # Parse effects
        effects_elem = self._find_element(sexp, "effects")
        if effects_elem:
            font_elem = self._find_element(effects_elem, "font")
            if font_elem:
                size_elem = self._find_element(font_elem, "size")
                if size_elem and len(size_elem) >= 3:
                    text.size = (float(size_elem[1]), float(size_elem[2]))
                thickness_elem = self._find_element(font_elem, "thickness")
                if thickness_elem:
                    text.thickness = float(thickness_elem[1])

        # Get UUID
        uuid_elem = self._find_element(sexp, "uuid")
        text.uuid = uuid_elem[1] if uuid_elem else str(uuid.uuid4())

        return text

    def _parse_via(self, sexp: List) -> Optional[Via]:
        """Parse a via element."""
        at_elem = self._find_element(sexp, "at")
        if not at_elem or len(at_elem) < 3:
            return None

        position = Point(float(at_elem[1]), float(at_elem[2]))

        size_elem = self._find_element(sexp, "size")
        size = float(size_elem[1]) if size_elem else 0.8

        drill_elem = self._find_element(sexp, "drill")
        drill = float(drill_elem[1]) if drill_elem else 0.4

        layers_elem = self._find_element(sexp, "layers")
        layers = [str(l) for l in layers_elem[1:]] if layers_elem else ["F.Cu", "B.Cu"]

        via = Via(position=position, size=size, drill=drill, layers=layers)

        net_elem = self._find_element(sexp, "net")
        if net_elem:
            via.net = net_elem[1]

        uuid_elem = self._find_element(sexp, "uuid")
        via.uuid = uuid_elem[1] if uuid_elem else str(uuid.uuid4())

        return via

    def _parse_track(self, sexp: List) -> Optional[Track]:
        """Parse a track (segment) element."""
        start_elem = self._find_element(sexp, "start")
        end_elem = self._find_element(sexp, "end")

        if not start_elem or not end_elem:
            return None

        start = Point(float(start_elem[1]), float(start_elem[2]))
        end = Point(float(end_elem[1]), float(end_elem[2]))

        width_elem = self._find_element(sexp, "width")
        width = float(width_elem[1]) if width_elem else 0.25

        layer_elem = self._find_element(sexp, "layer")
        layer = layer_elem[1] if layer_elem else "F.Cu"

        track = Track(start=start, end=end, width=width, layer=layer)

        net_elem = self._find_element(sexp, "net")
        if net_elem:
            track.net = net_elem[1]

        uuid_elem = self._find_element(sexp, "uuid")
        track.uuid = uuid_elem[1] if uuid_elem else str(uuid.uuid4())

        return track

    # Helper methods for writing

    def _pcb_to_sexp(self, pcb_data: Dict[str, Any]) -> List:
        """Convert PCB data to S-expression."""
        # Build the header on one line like KiCad expects
        sexp = [
            sexpdata.Symbol("kicad_pcb"),
            [sexpdata.Symbol("version"), pcb_data.get("version", self.version)],
            [sexpdata.Symbol("generator"), pcb_data.get("generator", self.generator)],
            [
                sexpdata.Symbol("generator_version"),
                pcb_data.get("generator_version", self.generator_version),
            ],
        ]

        # Add general section
        if "general" in pcb_data:
            general = [sexpdata.Symbol("general")]
            if "thickness" in pcb_data["general"]:
                general.append(
                    [sexpdata.Symbol("thickness"), pcb_data["general"]["thickness"]]
                )
            if "legacy_teardrops" in pcb_data["general"]:
                val = (
                    sexpdata.Symbol("yes")
                    if pcb_data["general"]["legacy_teardrops"]
                    else sexpdata.Symbol("no")
                )
                general.append([sexpdata.Symbol("legacy_teardrops"), val])
            sexp.append(general)

        # Add paper
        if "paper" in pcb_data:
            sexp.append([sexpdata.Symbol("paper"), pcb_data["paper"]])

        # Add layers
        if "layers" in pcb_data:
            layers = [sexpdata.Symbol("layers")]
            for layer in pcb_data["layers"]:
                layer_elem = [
                    layer["number"],
                    layer["canonical_name"],
                    sexpdata.Symbol(layer["type"]),
                ]
                if "user_name" in layer:
                    layer_elem.append(layer["user_name"])
                layers.append(layer_elem)
            sexp.append(layers)

        # Add setup (raw for now)
        if "setup" in pcb_data and pcb_data["setup"]:
            sexp.append(pcb_data["setup"])

        # Add nets
        for net in pcb_data.get("nets", []):
            sexp.append([sexpdata.Symbol("net"), net.number, net.name])

        # Add footprints
        for footprint in pcb_data.get("footprints", []):
            sexp.append(self._footprint_to_sexp(footprint))

        # Add vias
        for via in pcb_data.get("vias", []):
            sexp.append(self._via_to_sexp(via))

        # Add tracks
        for track in pcb_data.get("tracks", []):
            sexp.append(self._track_to_sexp(track))

        # Add graphics items
        for graphic in pcb_data.get("graphics", []):
            if isinstance(graphic, Line):
                sexp.append(self._gr_line_to_sexp(graphic))
            elif isinstance(graphic, Rectangle):
                sexp.append(self._gr_rect_to_sexp(graphic))

        # Add zones
        for zone in pcb_data.get("zones", []):
            sexp.append(self._zone_to_sexp(zone))

        # Add embedded fonts
        if "embedded_fonts" in pcb_data:
            val = (
                sexpdata.Symbol("yes")
                if pcb_data["embedded_fonts"]
                else sexpdata.Symbol("no")
            )
            sexp.append([sexpdata.Symbol("embedded_fonts"), val])

        return sexp

    def _zone_to_sexp(self, zone: Zone) -> List:
        """Convert a zone to S-expression."""
        sexp = [sexpdata.Symbol("zone")]

        # Add net info
        if zone.net is not None:
            sexp.append([sexpdata.Symbol("net"), zone.net])
        if zone.net_name:
            sexp.append([sexpdata.Symbol("net_name"), zone.net_name])

        # Add layers
        if " " in zone.layer:
            # Multiple layers
            layers = zone.layer.split()
            layers_elem = [sexpdata.Symbol("layers")]
            layers_elem.extend(layers)
            sexp.append(layers_elem)
        else:
            # Single layer
            sexp.append([sexpdata.Symbol("layer"), zone.layer])

        # Add UUID
        if zone.uuid:
            sexp.append([sexpdata.Symbol("uuid"), zone.uuid])

        # Add hatch
        sexp.append([sexpdata.Symbol("hatch"), sexpdata.Symbol("edge"), 0.5])

        # Add connect_pads
        connect_pads = [sexpdata.Symbol("connect_pads")]
        connect_pads.append([sexpdata.Symbol("clearance"), zone.thermal_relief_gap])
        sexp.append(connect_pads)

        # Add min_thickness
        sexp.append([sexpdata.Symbol("min_thickness"), zone.min_thickness])

        # Add filled_areas_thickness
        val = sexpdata.Symbol("yes") if zone.filled else sexpdata.Symbol("no")
        sexp.append([sexpdata.Symbol("filled_areas_thickness"), val])

        # Add fill
        fill = [sexpdata.Symbol("fill")]
        fill.append([sexpdata.Symbol("thermal_gap"), zone.thermal_relief_gap])
        fill.append(
            [sexpdata.Symbol("thermal_bridge_width"), zone.thermal_relief_bridge]
        )
        sexp.append(fill)

        # Add polygon
        if zone.polygon:
            polygon = [sexpdata.Symbol("polygon")]
            pts = [sexpdata.Symbol("pts")]
            for point in zone.polygon:
                pts.append([sexpdata.Symbol("xy"), point.x, point.y])
            polygon.append(pts)
            sexp.append(polygon)

        return sexp

    def _parse_zone(self, sexp: List) -> Optional[Zone]:
        """Parse a zone element."""
        zone = Zone(layer="F.Cu")  # Default layer

        # Parse attributes
        for item in sexp[1:]:
            if not self._is_sexp_list(item):
                continue

            item_type = self._get_symbol_name(item[0])

            if item_type == "net":
                if len(item) >= 2:
                    zone.net = item[1]
                if len(item) >= 3:
                    zone.net_name = item[2]
            elif item_type == "net_name":
                zone.net_name = item[1]
            elif item_type == "layers":
                # Can be multiple layers
                zone.layer = " ".join(str(l) for l in item[1:])
            elif item_type == "uuid":
                zone.uuid = item[1]
            elif item_type == "hatch":
                if len(item) >= 3:
                    zone.hatch_thickness = float(item[2])
                if len(item) >= 4:
                    zone.hatch_gap = float(item[3])
            elif item_type == "connect_pads":
                connect_elem = self._find_element(item, "clearance")
                if connect_elem:
                    zone.thermal_relief_gap = float(connect_elem[1])
            elif item_type == "min_thickness":
                zone.min_thickness = float(item[1])
            elif item_type == "filled_areas_thickness":
                zone.filled = item[1] != "no"
            elif item_type == "fill":
                thermal_gap = self._find_element(item, "thermal_gap")
                if thermal_gap:
                    zone.thermal_relief_gap = float(thermal_gap[1])
                thermal_bridge = self._find_element(item, "thermal_bridge_width")
                if thermal_bridge:
                    zone.thermal_relief_bridge = float(thermal_bridge[1])
            elif item_type == "polygon":
                pts_elem = self._find_element(item, "pts")
                if pts_elem:
                    for pt in pts_elem[1:]:
                        if (
                            self._is_sexp_list(pt)
                            and self._get_symbol_name(pt[0]) == "xy"
                        ):
                            zone.polygon.append(Point(float(pt[1]), float(pt[2])))

        return zone

    def _gr_rect_to_sexp(self, rect: Rectangle) -> List:
        """Convert a graphics rectangle to S-expression."""
        sexp = [sexpdata.Symbol("gr_rect")]

        # Add start and end
        sexp.append([sexpdata.Symbol("start"), rect.start.x, rect.start.y])
        sexp.append([sexpdata.Symbol("end"), rect.end.x, rect.end.y])

        # Add stroke
        stroke = [sexpdata.Symbol("stroke")]
        stroke.append([sexpdata.Symbol("width"), rect.width])
        stroke.append([sexpdata.Symbol("type"), sexpdata.Symbol("default")])
        sexp.append(stroke)

        # Add fill
        fill_value = sexpdata.Symbol("yes") if rect.fill else sexpdata.Symbol("no")
        sexp.append([sexpdata.Symbol("fill"), fill_value])

        # Add layer
        sexp.append([sexpdata.Symbol("layer"), rect.layer])

        # Add UUID
        if rect.uuid:
            sexp.append([sexpdata.Symbol("uuid"), rect.uuid])

        return sexp

    def _footprint_to_sexp(self, footprint: Footprint) -> List:
        """Convert a footprint to S-expression."""
        lib_id = footprint.get_library_id()
        sexp = [sexpdata.Symbol("footprint"), lib_id]

        # Add layer
        sexp.append([sexpdata.Symbol("layer"), footprint.layer])

        # Add UUID
        sexp.append([sexpdata.Symbol("uuid"), footprint.uuid])

        # Add position
        at_expr = [sexpdata.Symbol("at"), footprint.position.x, footprint.position.y]
        if footprint.rotation != 0:
            at_expr.append(footprint.rotation)
        sexp.append(at_expr)

        # Add description and tags
        if footprint.descr:
            sexp.append([sexpdata.Symbol("descr"), footprint.descr])
        if footprint.tags:
            sexp.append([sexpdata.Symbol("tags"), footprint.tags])

        # Add properties
        for prop in footprint.properties:
            sexp.append(self._property_to_sexp(prop))

        # Add path info
        if footprint.path:
            sexp.append([sexpdata.Symbol("path"), footprint.path])
        if footprint.sheetname:
            sexp.append([sexpdata.Symbol("sheetname"), footprint.sheetname])
        if footprint.sheetfile:
            sexp.append([sexpdata.Symbol("sheetfile"), footprint.sheetfile])

        # Add attributes
        if footprint.attr:
            attr_parts = footprint.attr.split()
            attr_elem = [sexpdata.Symbol("attr")]
            for part in attr_parts:
                attr_elem.append(sexpdata.Symbol(part))
            sexp.append(attr_elem)

        # Add graphical elements
        for line in footprint.lines:
            sexp.append(self._line_to_sexp(line))
        for arc in footprint.arcs:
            sexp.append(self._arc_to_sexp(arc))
        for text in footprint.texts:
            sexp.append(self._text_to_sexp(text))
        for rect in footprint.rectangles:
            sexp.append(self._rect_to_sexp(rect))

        # Add pads
        for pad in footprint.pads:
            sexp.append(self._pad_to_sexp(pad))

        # Add 3D model if present
        if footprint.model_path:
            model = [sexpdata.Symbol("model"), footprint.model_path]
            if footprint.model_offset:
                model.append(
                    [
                        sexpdata.Symbol("offset"),
                        [sexpdata.Symbol("xyz")] + list(footprint.model_offset),
                    ]
                )
            if footprint.model_scale:
                model.append(
                    [
                        sexpdata.Symbol("scale"),
                        [sexpdata.Symbol("xyz")] + list(footprint.model_scale),
                    ]
                )
            if footprint.model_rotate:
                model.append(
                    [
                        sexpdata.Symbol("rotate"),
                        [sexpdata.Symbol("xyz")] + list(footprint.model_rotate),
                    ]
                )
            sexp.append(model)

        # Add embedded fonts
        sexp.append([sexpdata.Symbol("embedded_fonts"), sexpdata.Symbol("no")])

        return sexp

    def _property_to_sexp(self, prop: Property) -> List:
        """Convert a property to S-expression."""
        sexp = [sexpdata.Symbol("property"), prop.name, prop.value]

        # Add position
        at_expr = [sexpdata.Symbol("at"), prop.position.x, prop.position.y, 0]
        sexp.append(at_expr)

        # Add layer
        sexp.append([sexpdata.Symbol("layer"), prop.layer])

        # Add UUID
        if prop.uuid:
            sexp.append([sexpdata.Symbol("uuid"), prop.uuid])

        # Add effects
        effects = [sexpdata.Symbol("effects")]
        font = [sexpdata.Symbol("font")]
        font.append([sexpdata.Symbol("size")] + list(prop.size))
        font.append([sexpdata.Symbol("thickness"), prop.thickness])
        effects.append(font)

        sexp.append(effects)

        return sexp

    def _pad_to_sexp(self, pad: Pad) -> List:
        """Convert a pad to S-expression."""
        sexp = [
            sexpdata.Symbol("pad"),
            pad.number,
            sexpdata.Symbol(pad.type),
            sexpdata.Symbol(pad.shape),
        ]

        # Add position with rotation
        at_expr = [sexpdata.Symbol("at"), pad.position.x, pad.position.y]
        if hasattr(pad, 'rotation') and pad.rotation != 0:
            at_expr.append(pad.rotation)
        sexp.append(at_expr)

        # Add size
        sexp.append([sexpdata.Symbol("size")] + list(pad.size))

        # Add layers
        layers_elem = [sexpdata.Symbol("layers")]
        for layer in pad.layers:
            layers_elem.append(layer)
        sexp.append(layers_elem)

        # Add drill if present
        if pad.drill is not None:
            if isinstance(pad.drill, dict) and pad.drill.get("shape") == "oval":
                # Oval drill
                sexp.append(
                    [
                        sexpdata.Symbol("drill"),
                        sexpdata.Symbol("oval"),
                        pad.drill["width"],
                        pad.drill["height"],
                    ]
                )
            else:
                # Circular drill
                sexp.append([sexpdata.Symbol("drill"), pad.drill])

        # Add roundrect ratio if present
        if pad.roundrect_rratio is not None:
            sexp.append([sexpdata.Symbol("roundrect_rratio"), pad.roundrect_rratio])

        # Add net if present
        if pad.net is not None:
            sexp.append([sexpdata.Symbol("net"), pad.net, pad.net_name or ""])

        # Add pinfunction if present
        if pad.pinfunction is not None:
            sexp.append([sexpdata.Symbol("pinfunction"), pad.pinfunction])

        # Add pintype if present
        if pad.pintype is not None:
            sexp.append([sexpdata.Symbol("pintype"), pad.pintype])

        # Add properties if present
        for prop_name, prop_value in pad.properties.items():
            if prop_value:  # Only add if True
                sexp.append([sexpdata.Symbol("property"), sexpdata.Symbol(prop_name)])

        # Add UUID
        if pad.uuid:
            sexp.append([sexpdata.Symbol("uuid"), pad.uuid])

        return sexp

    def _line_to_sexp(self, line: Line) -> List:
        """Convert a line to S-expression."""
        sexp = [sexpdata.Symbol("fp_line")]

        # Add start and end
        sexp.append([sexpdata.Symbol("start"), line.start.x, line.start.y])
        sexp.append([sexpdata.Symbol("end"), line.end.x, line.end.y])

        # Add stroke
        stroke = [sexpdata.Symbol("stroke")]
        stroke.append([sexpdata.Symbol("width"), line.width])
        stroke.append([sexpdata.Symbol("type"), sexpdata.Symbol(line.type)])
        sexp.append(stroke)

        # Add layer
        sexp.append([sexpdata.Symbol("layer"), line.layer])

        # Add UUID
        if line.uuid:
            sexp.append([sexpdata.Symbol("uuid"), line.uuid])

        return sexp

    def _arc_to_sexp(self, arc: Arc) -> List:
        """Convert an arc to S-expression."""
        sexp = [sexpdata.Symbol("fp_arc")]

        # Add start, mid, end
        sexp.append([sexpdata.Symbol("start"), arc.start.x, arc.start.y])
        sexp.append([sexpdata.Symbol("mid"), arc.mid.x, arc.mid.y])
        sexp.append([sexpdata.Symbol("end"), arc.end.x, arc.end.y])

        # Add stroke
        stroke = [sexpdata.Symbol("stroke")]
        stroke.append([sexpdata.Symbol("width"), arc.width])
        stroke.append([sexpdata.Symbol("type"), sexpdata.Symbol(arc.type)])
        sexp.append(stroke)

        # Add layer
        sexp.append([sexpdata.Symbol("layer"), arc.layer])

        # Add UUID
        if arc.uuid:
            sexp.append([sexpdata.Symbol("uuid"), arc.uuid])

        return sexp

    def _text_to_sexp(self, text: Text) -> List:
        """Convert a text to S-expression."""
        # Determine text type based on content
        if text.text == "${REFERENCE}":
            text_type = "reference"
        elif text.text == "${VALUE}":
            text_type = "value"
        else:
            text_type = "user"

        sexp = [sexpdata.Symbol("fp_text"), sexpdata.Symbol(text_type), text.text]

        # Add position
        at_expr = [sexpdata.Symbol("at"), text.position.x, text.position.y, 0]
        sexp.append(at_expr)

        # Add layer
        sexp.append([sexpdata.Symbol("layer"), text.layer])

        # Add UUID
        if text.uuid:
            sexp.append([sexpdata.Symbol("uuid"), text.uuid])

        # Add effects
        effects = [sexpdata.Symbol("effects")]
        font = [sexpdata.Symbol("font")]
        font.append([sexpdata.Symbol("size")] + list(text.size))
        font.append([sexpdata.Symbol("thickness"), text.thickness])
        effects.append(font)
        sexp.append(effects)

        return sexp

    def _rect_to_sexp(self, rect: Rectangle) -> List:
        """Convert a rectangle to S-expression."""
        sexp = [sexpdata.Symbol("fp_rect")]

        # Add start and end points
        sexp.append([sexpdata.Symbol("start"), rect.start.x, rect.start.y])
        sexp.append([sexpdata.Symbol("end"), rect.end.x, rect.end.y])

        # Add stroke
        stroke = [sexpdata.Symbol("stroke")]
        stroke.append([sexpdata.Symbol("width"), rect.width])
        stroke.append([sexpdata.Symbol("type"), sexpdata.Symbol("solid")])
        sexp.append(stroke)

        # Add layer
        sexp.append([sexpdata.Symbol("layer"), rect.layer])

        # Add fill - KiCad 9 uses yes/no format
        if rect.fill:
            sexp.append([sexpdata.Symbol("fill"), sexpdata.Symbol("yes")])
        else:
            sexp.append([sexpdata.Symbol("fill"), sexpdata.Symbol("no")])

        # Add UUID if present
        if rect.uuid:
            sexp.append([sexpdata.Symbol("uuid"), rect.uuid])

        return sexp

    def _via_to_sexp(self, via: Via) -> List:
        """Convert a via to S-expression."""
        sexp = [sexpdata.Symbol("via")]

        # Add position
        sexp.append([sexpdata.Symbol("at"), via.position.x, via.position.y])

        # Add size
        sexp.append([sexpdata.Symbol("size"), via.size])

        # Add drill
        sexp.append([sexpdata.Symbol("drill"), via.drill])

        # Add layers
        layers_elem = [sexpdata.Symbol("layers")]
        for layer in via.layers:
            layers_elem.append(layer)
        sexp.append(layers_elem)

        # Add net if present
        if via.net is not None:
            sexp.append([sexpdata.Symbol("net"), via.net])

        # Add UUID
        if via.uuid:
            sexp.append([sexpdata.Symbol("uuid"), via.uuid])

        return sexp

    def _track_to_sexp(self, track: Track) -> List:
        """Convert a track to S-expression."""
        sexp = [sexpdata.Symbol("segment")]

        # Add start and end
        sexp.append([sexpdata.Symbol("start"), track.start.x, track.start.y])
        sexp.append([sexpdata.Symbol("end"), track.end.x, track.end.y])

        # Add width
        sexp.append([sexpdata.Symbol("width"), track.width])

        # Add layer
        sexp.append([sexpdata.Symbol("layer"), track.layer])

        # Add net if present
        if track.net is not None:
            sexp.append([sexpdata.Symbol("net"), track.net])

        # Add UUID
        if track.uuid:
            sexp.append([sexpdata.Symbol("uuid"), track.uuid])

        return sexp

    def _gr_line_to_sexp(self, line: Line) -> List:
        """Convert a graphics line to S-expression."""
        sexp = [sexpdata.Symbol("gr_line")]

        # Add start and end
        sexp.append([sexpdata.Symbol("start"), line.start.x, line.start.y])
        sexp.append([sexpdata.Symbol("end"), line.end.x, line.end.y])

        # Add stroke
        stroke = [sexpdata.Symbol("stroke")]
        stroke.append([sexpdata.Symbol("width"), line.width])
        stroke.append([sexpdata.Symbol("type"), sexpdata.Symbol(line.type)])
        sexp.append(stroke)

        # Add layer
        sexp.append([sexpdata.Symbol("layer"), line.layer])

        # Add UUID
        if line.uuid:
            sexp.append([sexpdata.Symbol("uuid"), line.uuid])

        return sexp
