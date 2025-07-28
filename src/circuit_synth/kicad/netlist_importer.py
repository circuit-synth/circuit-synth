"""
kicad_netlist_importer.py

Core logic to parse a KiCad netlist (.net) file and convert it into a
hierarchical Circuit-Synth JSON, adhering to the standardized format where
the 'nets' dictionary maps net names directly to a list of node connection
details (Structure A). Includes extensive debug logging to trace each step
of the conversion.

The parser first builds the complete subcircuit hierarchy from the design section,
then fills in components and nets, ensuring all subcircuits are correctly discovered
and organized, even with multiple top-level circuits.
"""

import hashlib
import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------------------
# PinType Enum
# ------------------------------------------------------------------------------
class PinType(Enum):
    """
    Enumeration of pin types used in Circuit-Synth.
    Maps between KiCad pin types and Circuit-Synth pin types.
    """

    INPUT = "input"
    OUTPUT = "output"
    BIDIRECTIONAL = "bidirectional"
    POWER_IN = "power_in"
    POWER_OUT = "power_out"
    PASSIVE = "passive"
    UNSPECIFIED = "unspecified"

    @classmethod
    def from_kicad(cls, kicad_type: str) -> "PinType":
        """
        Convert a KiCad pin type to Circuit-Synth PinType.

        Args:
            kicad_type: The KiCad pin type string

        Returns:
            Corresponding PinType enum value
        """
        type_map = {
            "input": cls.INPUT,
            "output": cls.OUTPUT,
            "bidirectional": cls.BIDIRECTIONAL,
            "power_in": cls.POWER_IN,
            "power_out": cls.POWER_OUT,
            "passive": cls.PASSIVE,
        }
        return type_map.get((kicad_type or "").lower(), cls.UNSPECIFIED)


# ------------------------------------------------------------------------------
# Dataclasses for Circuit-Synth objects
# ------------------------------------------------------------------------------
@dataclass
class Pin:
    """
    Represents a pin on a component.
    """

    number: str
    name: str = ""  # Add default value
    pin_type: PinType = PinType.UNSPECIFIED

    def to_dict(self) -> dict:
        """
        Convert Pin object to dictionary representation for JSON output.
        """
        return {"number": self.number, "name": self.name, "type": self.pin_type.value}


@dataclass
class Component:
    """
    Represents a component in a circuit with its properties and pins.
    """

    reference: str
    value: str
    symbol: str = ""
    footprint: str = ""
    description: str = ""
    pins: Dict[str, Pin] = field(default_factory=dict)
    properties: Dict[str, str] = field(default_factory=dict)
    sheetpath: str = "/"  # default to root

    def add_pin(self, pin: Pin) -> None:
        """
        Add a pin to this component.

        Args:
            pin: The Pin object to add
        """
        self.pins[pin.number] = pin

    def to_dict(self) -> dict:
        """
        Convert Component object to dictionary representation for JSON output.
        """
        return {
            "reference": self.reference,
            "value": self.value,
            "symbol": self.symbol,
            "footprint": self.footprint,
            "description": self.description,
            # Convert the pins dictionary to a list of dictionaries,
            # adding 'pin_id' based on the pin number (key).
            "pins": [
                {"pin_id": num, **pin.to_dict()}  # Use pin number as pin_id
                for num, pin in self.pins.items()
            ],
            "properties": self.properties,
        }


@dataclass
class Node:
    """
    Represents a node in a net (a connection point between a component and a net).
    """

    component_ref: str
    pin_number: str
    pin_name: str = ""
    pin_type: PinType = PinType.UNSPECIFIED

    def to_dict(self) -> dict:
        """
        Convert Node object to dictionary representation for JSON output.
        """
        return {
            "component": self.component_ref,
            "pin": {
                "number": self.pin_number,
                "name": self.pin_name,
                "type": self.pin_type.value,
            },
        }


@dataclass
class Net:
    """
    Represents a net (electrical connection) in a circuit.
    """

    name: str  # Local name (for backward compatibility)
    code: str
    nodes: List[Node] = field(default_factory=list)
    sheetpath: str = "/"
    is_hierarchical: bool = False  # Whether this is a hierarchical net
    hierarchical_name: str = ""  # Full hierarchical name (if applicable)
    attributes: Dict[str, Any] = field(default_factory=dict)  # Added for net attributes

    def add_node(self, node: Node) -> None:
        """Add a node to this net."""
        self.nodes.append(node)

    def to_dict(self) -> dict:
        """
        Convert Net object to dictionary representation for JSON output.
        Returns a dictionary with just the nodes list to comply with Structure A format.
        Other properties like attributes are handled separately by the parent object.
        """
        return {"nodes": [n.to_dict() for n in self.nodes]}


@dataclass
class Subcircuit:
    """
    Represents a subcircuit in the hierarchical circuit structure.
    Can contain components, nets, and other subcircuits (children).
    """

    name: str
    components: Dict[str, Component] = field(default_factory=dict)
    nets: Dict[str, Net] = field(default_factory=dict)
    children: Dict[str, "Subcircuit"] = field(default_factory=dict)
    uuid: str = ""  # Store the KiCad tstamp UUID

    def to_dict(self) -> dict:
        """
        Convert Subcircuit object to dictionary representation for JSON output.
        Specifically formats the 'nets' dictionary according to Structure A:
        `Net Name -> List of Node Dictionaries`.
        """
        # First collect any net attributes that might be needed elsewhere
        net_attributes = {}
        for nname, net in self.nets.items():
            if net.attributes:
                net_attributes[nname] = net.attributes

        result = {
            "name": self.name,
            "components": {
                ref: comp.to_dict() for ref, comp in self.components.items()
            },
            # Structure A format: Map net name directly to list of nodes
            "nets": {nname: net.to_dict()["nodes"] for nname, net in self.nets.items()},
            "subcircuits": [child.to_dict() for child in self.children.values()],
        }

        # Only include net_attributes if there are any
        if net_attributes:
            result["net_attributes"] = net_attributes

        return result


@dataclass
class CircuitTemplate:
    """Represents a reusable circuit template with multiple instances."""

    source_file: str  # e.g., "half_bridge.kicad_sch"
    component_signature: str  # Hash of component types/values/timestamps
    instances: List[str]  # ["Half Bridge", "Half Bridge1", "Half Bridge2"]
    canonical_name: str  # "Half_Bridge"
    representative_circuit: Optional[Subcircuit] = (
        None  # One instance to use as template
    )

    def to_dict(self) -> dict:
        """Convert CircuitTemplate to dictionary representation."""
        return {
            "source_file": self.source_file,
            "component_signature": self.component_signature,
            "instances": self.instances,
            "canonical_name": self.canonical_name,
            "representative_circuit_name": (
                self.representative_circuit.name
                if self.representative_circuit
                else None
            ),
        }


@dataclass
class DuplicateDetectionResult:
    """Results of duplicate detection analysis."""

    templates: Dict[str, CircuitTemplate] = field(
        default_factory=dict
    )  # template_id -> CircuitTemplate
    unique_circuits: List[str] = field(
        default_factory=list
    )  # Circuit names that are unique
    duplicate_groups: Dict[str, str] = field(
        default_factory=dict
    )  # circuit_name -> template_id

    def to_dict(self) -> dict:
        """Convert DuplicateDetectionResult to dictionary representation."""
        return {
            "templates": {k: v.to_dict() for k, v in self.templates.items()},
            "unique_circuits": self.unique_circuits,
            "duplicate_groups": self.duplicate_groups,
        }


@dataclass
class Circuit:
    """
    Top-level representation of a circuit, containing the root subcircuit and properties.
    """

    name: str
    properties: Dict[str, Any] = field(default_factory=dict)
    root: Subcircuit = field(default_factory=lambda: Subcircuit(name="Root"))

    def to_dict(self) -> dict:
        """
        Convert Circuit object to dictionary representation for JSON output.
        Ensures the final JSON adheres to the standardized format, including
        Structure A for the 'nets' dictionary within the root and subcircuits.
        Filters out artifact subcircuits while preserving structural elements.
        """
        logger.info(f"Converting circuit '{self.name}' to dictionary")

        # Clean up artifact subcircuits (not structural elements)
        self._clean_artifact_subcircuits(self.root)

        root_dict = self.root.to_dict()

        # Verify the subcircuits made it into the dictionary
        if "subcircuits" in root_dict:
            pass  # No action needed if subcircuits are present
        else:
            logger.error("Root dict is missing 'subcircuits' key!")

        # Use the root subcircuit's dict but override the name
        result = {
            "name": self.name,
            "components": root_dict["components"],
            "nets": root_dict[
                "nets"
            ],  # Uses the 'nets' from root_dict, which is already in Structure A (Net Name -> List of Nodes).
            "subcircuits": root_dict["subcircuits"],
            "properties": self.properties,
        }

        # Add duplicate detection results if available
        if hasattr(self, "duplicate_detection_result"):
            result["duplicate_detection"] = self.duplicate_detection_result.to_dict()

        logger.info(f"Final JSON output has {len(result['subcircuits'])} subcircuits")
        return result

    def _clean_artifact_subcircuits(self, subcircuit: Subcircuit) -> bool:
        """
        Recursively clean up artifact subcircuits while preserving meaningful structure.

        Args:
            subcircuit: The subcircuit to evaluate

        Returns:
            True if the subcircuit is meaningful, False if it's an artifact
        """
        # First recursively process children
        meaningful_children = {}
        for name, child in subcircuit.children.items():
            # Check if this child is meaningful
            is_meaningful = self._clean_artifact_subcircuits(child)

            # If it's meaningful or has a human-readable name, keep it
            if is_meaningful or self._is_human_readable_name(name):
                meaningful_children[name] = child

        # Replace children with cleaned list
        subcircuit.children = meaningful_children

        # A subcircuit is meaningful if:
        # 1. It has components, or
        # 2. It has nets, or
        # 3. It has meaningful children
        # 4. It has a human-readable name (not a UUID)
        return (
            bool(subcircuit.components)
            or bool(subcircuit.nets)
            or bool(subcircuit.children)
            or self._is_human_readable_name(subcircuit.name)
        )

    def _is_human_readable_name(self, name: str) -> bool:
        """
        Determine if a name is likely a human-readable identifier vs. a UUID or auto-generated ID.

        Args:
            name: The name to check

        Returns:
            True if the name is likely human-readable, False otherwise
        """
        # UUIDs and auto-generated IDs are often:
        # 1. Long (> 30 chars)
        # 2. Mostly hex characters or contain many dashes
        # 3. No spaces or common words

        # Check for UUID-like pattern
        if len(name) > 30 and all(c.isalnum() or c == "-" for c in name):
            return False

        # Check for common words or short names (likely human-chosen)
        common_words = [
            "usb",
            "power",
            "cpu",
            "interface",
            "sensor",
            "led",
            "filter",
            "card",
            "memory",
            "output",
            "input",
        ]
        if any(word in name.lower() for word in common_words) or len(name) < 15:
            return True

        # Default to treating it as human-readable
        return True


# ------------------------------------------------------------------------------
# KiCadNetlistParser - S-expression Parser
# ------------------------------------------------------------------------------
class KiCadNetlistParser:
    """
    Parser for KiCad netlist files in S-expression format.
    Converts the S-expression text to a nested list structure.
    """

    def __init__(self):
        self.tokens = []
        self.pos = 0

    def parse_file(self, filepath: Path) -> Any:
        """
        Parse a KiCad netlist file from the given filepath.

        Args:
            filepath: Path to the KiCad netlist file

        Returns:
            Parsed netlist data as nested lists
        """
        logger.info(f"Parsing KiCad netlist file: {filepath}")
        try:
            content = filepath.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"Error reading {filepath}: {e}")
            raise

        return self.parse(content)

    def parse(self, content: str) -> Any:
        """
        Parse the KiCad netlist content string.

        Args:
            content: The KiCad netlist file content as a string

        Returns:
            Parsed netlist data as nested lists
        """
        logger.info("Tokenizing netlist content...")
        self.tokens = self._tokenize(content)
        self.pos = 0
        logger.info("Parsing S-expression structure into nested lists...")
        data = self._parse_expr()
        return data

    def _tokenize(self, content: str) -> List[str]:
        """
        Tokenize the netlist content into a list of tokens.
        Handles strings, comments, and parentheses according to S-expression rules.

        Args:
            content: The KiCad netlist file content

        Returns:
            List of tokens
        """
        tokens = []
        current = []
        in_string = False
        in_comment = False
        i = 0
        line_num = 1

        while i < len(content):
            c = content[i]

            if c == "\n":
                line_num += 1

            # Skip comments
            if c == ";" and not in_string:
                in_comment = True
                i += 1
                continue
            if in_comment:
                if c == "\n":
                    in_comment = False
                i += 1
                continue

            # Handle quoted strings
            if c == '"':
                if not in_string or (in_string and i > 0 and content[i - 1] != "\\"):
                    in_string = not in_string
                    current.append(c)
                    i += 1
                    continue

            if in_string:
                if c == "\\" and (i + 1) < len(content):
                    current.append(c)
                    i += 1
                    c = content[i]
                    current.append(c)
                    i += 1
                else:
                    current.append(c)
                    i += 1
                continue

            # whitespace & parentheses
            if c.isspace():
                if current:
                    tokens.append("".join(current))
                    current = []
                i += 1
                continue

            if c in "()":
                if current:
                    tokens.append("".join(current))
                    current = []
                tokens.append(c)
                i += 1
                continue

            current.append(c)
            i += 1

        if current:
            tokens.append("".join(current))

        return tokens

    def _parse_expr(self) -> Any:
        """
        Parse an S-expression from the token stream.
        Recursively builds the nested list structure.

        Returns:
            A parsed S-expression as a nested list, string, or number
        """
        if self.pos >= len(self.tokens):
            return None

        token = self.tokens[self.pos]
        self.pos += 1

        if token == "(":
            expr = []
            while self.pos < len(self.tokens) and self.tokens[self.pos] != ")":
                sub_expr = self._parse_expr()
                if sub_expr is not None:
                    expr.append(sub_expr)
            if self.pos >= len(self.tokens):
                raise ValueError("Unclosed parenthesis in netlist!")
            self.pos += 1  # skip ')'
            return expr
        else:
            # Check for quoted string
            if token.startswith('"') and token.endswith('"'):
                return token[1:-1]
            # Try numeric
            try:
                return int(token)
            except ValueError:
                try:
                    return float(token)
                except ValueError:
                    return token


# ------------------------------------------------------------------------------
# ParsedNetlist Helper
# ------------------------------------------------------------------------------
class ParsedNetlist:
    """
    Helper class to navigate the parsed netlist data structure.
    Provides methods to access specific sections of the netlist.
    """

    def __init__(self, data: Any):
        self.data = data
        self.export_content = None
        if isinstance(data, list) and data and data[0] == "export":
            self.export_content = data[1:]

    def _find_section(self, section_name: str) -> List[Any]:
        """
        Find a specific section in the netlist export data.

        Args:
            section_name: Name of the section to find

        Returns:
            List of items in the section, or empty list if not found
        """
        if not self.export_content:
            return []
        for expr in self.export_content:
            if isinstance(expr, list) and expr and expr[0] == section_name:
                return expr[1:]
        return []

    def design(self) -> List[Any]:
        """
        Get the design section of the netlist.

        Returns:
            List of design items, or empty list if not found
        """
        if not self.export_content:
            return []
        for expr in self.export_content:
            if isinstance(expr, list) and expr and expr[0] == "design":
                return expr  # Return the whole expression including 'design'
        return []

    def sheets(self) -> List[List[Any]]:
        """
        Get all sheet definitions from the design section.

        Returns:
            List of sheet definitions
        """
        des = self.design()
        sheets_found = []

        # First-pass: Process all sheet entries in the design section
        for item in des:
            if isinstance(item, list) and item and item[0] == "sheet":
                sheets_found.append(item[1:])

        # Log the design structure if no sheets were found in first pass
        if not sheets_found:
            logger.debug(
                "No direct sheet entries found in design section. Design structure:"
            )
            for item in des:
                if isinstance(item, list) and len(item) > 0:
                    logger.debug(f" - Design item: {item[0]}")

        # Second-pass: Look for sheet entries in nested structures
        for item in des:
            if isinstance(item, list) and len(item) > 1:
                for subitem in item[1:]:
                    if isinstance(subitem, list) and subitem and subitem[0] == "sheet":
                        sheets_found.append(subitem[1:])

        # Final check - manually examine the design data for sheet number entries
        # This helps with KiCad 6+ format
        if not sheets_found:
            logger.debug("Searching for sheets by number entries")
            for item in des:
                if isinstance(item, list) and len(item) >= 2 and item[0] == "sheet":
                    # Get sheet name and tstamps from sheet entry
                    sheet_data = {}
                    for subitem in item[1:]:
                        if isinstance(subitem, list) and len(subitem) >= 2:
                            if subitem[0] == "number":
                                sheet_data["number"] = subitem[1]
                            elif subitem[0] == "name":
                                sheet_data["name"] = subitem[1]
                            elif subitem[0] == "tstamps":
                                sheet_data["tstamps"] = subitem[1]

                    if sheet_data:
                        logger.debug(f"Found sheet: {sheet_data}")
                        sheets_found.append([["name", sheet_data.get("name", "/")]])

        logger.debug(f"Found {len(sheets_found)} sheets in total")
        return sheets_found

    def components(self) -> List[List[Any]]:
        """
        Get all component definitions from the components section.

        Returns:
            List of component definitions
        """
        comps_section = self._find_section("components")
        comps = []
        for c in comps_section:
            if isinstance(c, list) and c and c[0] == "comp":
                comps.append(c[1:])
        return comps

    def nets(self) -> List[List[Any]]:
        """
        Get all net definitions from the nets section.

        Returns:
            List of net definitions
        """
        nets_section = self._find_section("nets")
        netlist = []
        for n in nets_section:
            if isinstance(n, list) and n and n[0] == "net":
                netlist.append(n[1:])
        return netlist

    def libparts(self) -> List[List[Any]]:
        """
        Get all libpart definitions from the libparts section.

        Returns:
            List of libpart definitions
        """
        libparts_section = self._find_section("libparts")
        parts = []
        for p in libparts_section:
            if isinstance(p, list) and p and p[0] == "libpart":
                parts.append(p)  # Keep the 'libpart' keyword for parsing
        return parts


# ------------------------------------------------------------------------------
# Main Converter Class
# ------------------------------------------------------------------------------
class CircuitSynthParser:
    """
    Main class for converting KiCad netlist to Circuit-Synth JSON.
    Uses hierarchy-first approach to handle complex hierarchies with multiple
    top-level circuits correctly.
    """

    def __init__(self):
        self.circuit: Optional[Circuit] = None
        self.subcircuits: Dict[str, Subcircuit] = (
            {}
        )  # Map path string to Subcircuit object
        # Component reference to sheetpath lookup for faster access
        self.component_sheetpaths: Dict[str, str] = (
            {}
        )  # Map component ref to its sheetpath string
        # Keep track of all sheetpaths found during parsing
        self.all_discovered_paths: Set[str] = set()
        # Track parent-child relationships
        self.path_parents: Dict[str, str] = {}  # Map sheet path to parent path
        # Net name standardization map
        self.net_name_map: Dict[str, str] = (
            {}
        )  # Map original net name to standardized name
        # Store parsed libpart data (lib, part) -> {pin_num: Pin}
        self._libparts_data: Dict[Tuple[str, str], Dict[str, Pin]] = {}
        # ADDED: Store all components for easy lookup by ref
        self.all_components: Dict[str, Component] = (
            {}
        )  # Map component ref to Component object

    def parse_kicad_netlist(self, netlist_path: Path) -> Circuit:
        """
        Parse a KiCad netlist file and convert it to a Circuit-Synth Circuit object.
        Uses hierarchy-first approach to ensure all subcircuits are captured.

        Args:
            netlist_path: Path to the KiCad netlist file

        Returns:
            Circuit object representing the parsed netlist
        """
        # Initialize new Circuit with the stem of the netlist file as the name
        self.circuit = Circuit(name=netlist_path.stem)
        # Initialize the root subcircuit
        self.subcircuits["/"] = self.circuit.root
        self.all_discovered_paths.add("/")

        logger.info(f"Reading netlist from {netlist_path}...")
        parser = KiCadNetlistParser()
        raw_data = parser.parse_file(netlist_path)
        if not isinstance(raw_data, list) or not raw_data:
            raise ValueError("Parsed netlist not recognized as KiCad 'export' list")

        netlist = ParsedNetlist(raw_data)

        # PHASE 1: Build the complete hierarchy from design section first
        logger.info("PHASE 1: Building complete circuit hierarchy from design section")
        self._build_hierarchy_from_design(netlist)

        # PHASE 1.5: Parse libparts to get pin details needed for components
        logger.info("PHASE 1.5: Parsing libparts section")
        libpart_blocks = (
            netlist.libparts()
        )  # Assuming ParsedNetlist has libparts() method
        self._parse_libparts(libpart_blocks)

        # PHASE 2: Parse components and add them to the appropriate subcircuits
        logger.info("PHASE 2: Parsing components and assigning to subcircuits")
        comp_blocks = netlist.components()
        self._parse_components(comp_blocks)  # This will now use self._libparts_data

        # PHASE 2.5: Detect duplicate circuits
        logger.info("PHASE 2.5: Detecting duplicate circuits")
        duplicate_result = self.detect_duplicate_circuits()
        self.circuit.duplicate_detection_result = duplicate_result

        # PHASE 3: Parse nets and assign to subcircuits
        logger.info("PHASE 3: Parsing nets and assigning to appropriate subcircuits")
        net_blocks = netlist.nets()
        self._parse_nets(net_blocks)

        # PHASE 4: Parse design properties
        logger.info("PHASE 4: Parsing design properties")
        self._parse_design_properties(netlist.design())

        # PHASE 5: Final verification and logging
        logger.info("PHASE 5: Final verification and logging")
        self._verify_and_log_hierarchy()

        return self.circuit

    def _parse_libparts(self, libpart_blocks: List[List[Any]]) -> None:
        """
        Parse the (libparts ...) section and store pin information.
        Populates self._libparts_data with detailed pin information including types.
        """
        logger.info(f"Parsing {len(libpart_blocks)} libpart blocks.")
        for block in libpart_blocks:
            if not isinstance(block, list) or block[0] != "libpart":
                continue

            lib_name = ""
            part_name = ""
            pins_dict: Dict[str, Pin] = {}
            description = ""

            # First pass - get basic libpart info
            for item in block[1:]:
                if not isinstance(item, list) or not item:
                    continue
                key = item[0]
                if key == "lib" and len(item) > 1:
                    lib_name = item[1]
                elif key == "part" and len(item) > 1:
                    part_name = item[1]
                elif key == "description" and len(item) > 1:
                    description = item[1]

            if not lib_name or not part_name:
                logger.warning(
                    f"Skipping libpart block due to missing lib or part name: {block}"
                )
                continue

            libpart_key = (lib_name, part_name)
            logger.debug(f"Processing libpart {libpart_key} - {description}")

            # Second pass - process pins with detailed type mapping
            for item in block[1:]:
                if not isinstance(item, list) or not item or item[0] != "pins":
                    continue

                for pin_item in item[1:]:
                    if not isinstance(pin_item, list) or pin_item[0] != "pin":
                        continue

                    pin_data = {
                        "num": "",
                        "name": "",
                        "type": "unspecified",
                        "direction": "",  # Additional field for direction
                        "electrical_type": "",  # Additional field for electrical type
                    }

                    # Extract all pin details
                    for pin_detail in pin_item[1:]:
                        if not isinstance(pin_detail, list) or len(pin_detail) < 2:
                            continue
                        detail_key = pin_detail[0]
                        detail_value = pin_detail[1]
                        if detail_key in pin_data:
                            pin_data[detail_key] = str(detail_value)

                    if not pin_data["num"]:
                        logger.warning(
                            f"Skipping pin with missing number in {libpart_key}: {pin_item}"
                        )
                        continue

                    # Enhanced pin type determination
                    pin_type = self._determine_pin_type(
                        type_str=pin_data["type"],
                        direction=pin_data["direction"],
                        electrical_type=pin_data["electrical_type"],
                        pin_name=pin_data["name"],
                    )

                    pin_obj = Pin(
                        number=pin_data["num"], name=pin_data["name"], pin_type=pin_type
                    )
                    pins_dict[pin_data["num"]] = pin_obj
                    logger.debug(
                        f"Added pin {pin_data['num']} ({pin_data['name']}) of type {pin_type.value} to {libpart_key}"
                    )

            # Store the complete pin dictionary for this libpart
            self._libparts_data[libpart_key] = pins_dict
            logger.info(f"Stored libpart {libpart_key} with {len(pins_dict)} pins")

    def _determine_pin_type(
        self, type_str: str, direction: str, electrical_type: str, pin_name: str
    ) -> PinType:
        """
        Determine the Circuit-Synth pin type based on multiple KiCad pin attributes.

        Args:
            type_str: The KiCad pin type string
            direction: The pin direction (input/output/bidirectional)
            electrical_type: The electrical characteristics
            pin_name: The pin name (useful for power pins)

        Returns:
            Corresponding PinType enum value
        """
        # Convert everything to lowercase for consistent matching
        type_str = (type_str or "").lower()
        direction = (direction or "").lower()
        electrical_type = (electrical_type or "").lower()
        pin_name = (pin_name or "").lower()

        # Check for power pins first
        if any(
            power_term in pin_name
            for power_term in ["vcc", "vdd", "v+", "pwr", "power"]
        ):
            return PinType.POWER_IN
        if any(gnd_term in pin_name for gnd_term in ["gnd", "vss", "v-"]):
            return PinType.POWER_IN

        # Map based on type and direction
        if type_str == "power_in" or type_str == "power":
            return PinType.POWER_IN
        if type_str == "power_out":
            return PinType.POWER_OUT
        if direction == "input" or type_str == "input":
            return PinType.INPUT
        if direction == "output" or type_str == "output":
            return PinType.OUTPUT
        if direction == "bidirectional" or type_str == "bidirectional":
            return PinType.BIDIRECTIONAL
        if type_str == "passive":
            return PinType.PASSIVE

        # Default to unspecified if no clear mapping
        logger.debug(
            f"Could not determine specific pin type for: type={type_str}, direction={direction}, name={pin_name}"
        )
        return PinType.UNSPECIFIED

        logger.info("Netlist conversion finished successfully.")
        return self.circuit

    def _build_hierarchy_from_design(self, netlist: ParsedNetlist) -> None:
        """
        Build the complete subcircuit hierarchy from the design section.
        This is the first phase that establishes all subcircuits even if they have no components.

        Args:
            netlist: ParsedNetlist object
        """
        # Extract all sheet definitions
        sheet_blocks = netlist.sheets()
        logger.info(f"Found {len(sheet_blocks)} sheet definitions in design section")

        # Initialize collections for processing
        sheet_paths = set(["/"])  # Start with root path
        sheet_data = {}  # Map of path to sheet metadata

        # Process sheet blocks in a single pass
        for sb in sheet_blocks:
            sheet_info = self._extract_sheet_info(sb)
            normalized_path = self._normalize_sheet_path(sheet_info["name"])
            sheet_paths.add(normalized_path)
            sheet_data[normalized_path] = sheet_info

        # Process parent-child relationships
        self._process_sheet_hierarchies(sheet_paths, sheet_data)

        # Create subcircuits for all paths
        self._create_subcircuit_hierarchy(sheet_paths, sheet_data)

    def _extract_sheet_info(self, sheet_block):
        """
        Extract essential information from a sheet block.

        Args:
            sheet_block: A parsed sheet block from the netlist

        Returns:
            Dictionary containing sheet name, number, and tstamps
        """
        info = {"name": "/", "number": "1", "tstamps": ""}

        for item in sheet_block:
            if isinstance(item, list) and len(item) == 2:
                key, val = item
                if key in ["name", "number", "tstamps"]:
                    info[key] = val

        return info

    def _process_sheet_hierarchies(self, sheet_paths, sheet_data):
        """
        Process parent-child relationships between sheets based on path nesting.

        Args:
            sheet_paths: Set of all sheet paths
            sheet_data: Dictionary mapping paths to sheet information
        """
        # Determine parent-child relationships based on path nesting
        for path in sorted(sheet_paths, key=lambda p: p.count("/")):
            if path == "/":
                continue  # Skip root

            # Determine parent path
            parent_path = self._get_parent_path(path)
            if parent_path:
                self.path_parents[path] = parent_path
                logger.debug(f"Set parent relationship: {path} -> {parent_path}")

            # Ensure all paths are in our tracking set
            self.all_discovered_paths.add(path)

    def _create_subcircuit_hierarchy(self, sheet_paths, sheet_data):
        """
        Create subcircuits for all paths and build the hierarchy tree.

        Args:
            sheet_paths: Set of all sheet paths
            sheet_data: Dictionary mapping paths to sheet information
        """
        # Create subcircuits for all paths
        for path in sorted(sheet_paths, key=lambda p: p.count("/")):
            if path not in self.subcircuits:
                subcircuit_name = self._get_subcircuit_name_from_path(path)
                self.subcircuits[path] = Subcircuit(name=subcircuit_name)
                logger.info(
                    f"Created subcircuit for path: {path} with name: {subcircuit_name}"
                )

        # Build the hierarchy tree
        logger.info("Building subcircuit hierarchy tree from design")
        root = self.subcircuits["/"]

        # First process top-level subcircuits (direct children of root)
        for path in sorted(sheet_paths):
            if path == "/":
                continue  # Skip root

            parent_path = self.path_parents.get(path, "/")
            if parent_path == "/" and path.count("/") <= 2:
                # This is a top-level subcircuit
                child = self.subcircuits[path]
                child_name = child.name

                if child_name not in root.children:
                    root.children[child_name] = child
                    logger.info(f"Added top-level subcircuit '{child_name}' to root")

        # Then process deeper levels
        for path in sorted(sheet_paths, key=lambda p: p.count("/")):
            if path == "/" or path.count("/") <= 2:
                continue  # Skip root and top-level

            parent_path = self.path_parents.get(path, "/")
            if parent_path in self.subcircuits:
                parent = self.subcircuits[parent_path]
                child = self.subcircuits[path]
                child_name = child.name

                if child_name not in parent.children:
                    parent.children[child_name] = child
                    logger.info(
                        f"Added subcircuit '{child_name}' to parent '{parent_path}'"
                    )
            else:
                logger.warning(
                    f"Parent path '{parent_path}' not found for subcircuit '{path}', attaching to root"
                )
                # Fallback: attach to root
                root.children[self.subcircuits[path].name] = self.subcircuits[path]

    def _register_component(self, component: Component, sheet_path: str) -> None:
        """
        Register a component in its subcircuit and the global lookup.

        Args:
            component: The Component object to register
            sheet_path: The sheet path where this component belongs
        """
        # Ensure subcircuit exists
        if sheet_path not in self.subcircuits:
            self._find_or_create_subcircuit(sheet_path)

        # Register in subcircuit
        self.subcircuits[sheet_path].components[component.reference] = component

        # Register in global lookup without duplicating the object
        self.all_components[component.reference] = component

        # Register sheetpath for quick access during net processing
        self.component_sheetpaths[component.reference] = sheet_path

        logger.debug(
            f"Registered component '{component.reference}' in subcircuit '{sheet_path}'"
        )

    def _parse_components(self, comp_blocks: List[List[Any]]) -> None:
        """
        Parse component blocks and assign components to their respective subcircuits.
        This phase assumes the hierarchy is already established.

        Args:
            comp_blocks: List of component blocks from the netlist
        """
        logger.info(f"Parsing {len(comp_blocks)} components...")

        # Track components by sheet for logging
        components_by_sheet = {}

        for comp_block in comp_blocks:
            comp_info = {
                "ref": "",
                "value": "",
                "footprint": "",
                "description": "",
                "sheetpath": "/",
                "properties": {},
            }

            lib_name = ""
            part_name = ""

            # Track found fields for validation
            found_fields = set()
            found_properties = set()

            # Extract component info from block
            for item in comp_block:
                if isinstance(item, list) and len(item) >= 2:
                    key = item[0]
                    val = item[1] if len(item) == 2 else item[1:]
                    if key == "ref":
                        comp_info["ref"] = val
                    elif key == "value":
                        comp_info["value"] = val
                    elif key == "footprint":
                        comp_info["footprint"] = val
                    elif key == "description":
                        comp_info["description"] = val
                    elif key == "libsource":
                        for sub_item in val:
                            if isinstance(sub_item, list) and len(sub_item) == 2:
                                sub_key, sub_val = sub_item
                                if sub_key == "lib":
                                    lib_name = sub_val
                                if sub_key == "part":
                                    part_name = sub_val
                    elif key == "sheetpath":
                        spath = self._extract_sheetpath(item)
                        comp_info["sheetpath"] = spath
                    elif key == "fields":
                        # Process fields section for custom fields
                        for field_item in val:
                            if (
                                isinstance(field_item, list)
                                and field_item[0] == "field"
                                and len(field_item) >= 3
                            ):
                                field_parts = field_item[1:]
                                field_name = ""
                                field_value = ""
                                # Extract field name and value
                                if (
                                    isinstance(field_parts[0], list)
                                    and field_parts[0][0] == "name"
                                ):
                                    field_name = field_parts[0][1]
                                if len(field_parts) >= 2 and isinstance(
                                    field_parts[1], str
                                ):
                                    field_value = field_parts[1]

                                if field_name:
                                    found_fields.add(field_name)
                                    comp_info["properties"][field_name] = field_value
                                    logger.debug(
                                        f"Added field '{field_name}' = '{field_value}' to component {comp_info['ref']}"
                                    )
                    elif key == "property":
                        p_name, p_val = "", ""
                        if isinstance(val, list):
                            for sub2 in val:
                                if isinstance(sub2, list) and len(sub2) == 2:
                                    sub2key, sub2val = sub2
                                    if sub2key == "name":
                                        p_name = sub2val
                                    elif sub2key == "value":
                                        p_val = sub2val
                        if p_name:
                            found_properties.add(p_name)
                            comp_info["properties"][p_name] = p_val
                            logger.debug(
                                f"Added property '{p_name}' = '{p_val}' to component {comp_info['ref']}"
                            )

            # Create component object
            c = Component(
                reference=comp_info["ref"],
                value=comp_info["value"],
                symbol=f"{lib_name}:{part_name}" if lib_name and part_name else "",
                footprint=comp_info["footprint"],
                description=comp_info["description"],
                properties=comp_info["properties"],
            )

            # Look up and add pins from parsed libparts data
            libpart_key = (lib_name, part_name)
            if libpart_key in self._libparts_data:
                c.pins = self._libparts_data[libpart_key].copy()
                logger.debug(
                    f"  Added {len(c.pins)} pins to {c.reference} from libpart {libpart_key}"
                )
            else:
                logger.warning(
                    f"  Libpart key {libpart_key} not found for component {c.reference}. Pins will be empty."
                )

            # Normalize sheet path
            sheet_path = self._normalize_sheet_path(comp_info["sheetpath"])
            c.sheetpath = sheet_path

            # Register the component in subcircuit and global lookup
            self._register_component(c, sheet_path)

            # Track components by sheet for logging
            if sheet_path not in components_by_sheet:
                components_by_sheet[sheet_path] = []
            components_by_sheet[sheet_path].append(c.reference)

        # Log component distribution
        for sheet_path, components in components_by_sheet.items():
            logger.info(
                f"Subcircuit '{sheet_path}' has {len(components)} components: {components}"
            )

    def _get_pin_details(
        self, component_ref: str, pin_number: str, net_name: str, node_index: int
    ) -> Tuple[str, PinType]:
        """
        Get pin name and type for a given component and pin number.

        Args:
            component_ref: Component reference designator
            pin_number: Pin number as a string
            net_name: Net name for context in logs
            node_index: Node index for context in logs

        Returns:
            Tuple containing pin name and pin type
        """
        # Default values for when pin information can't be found
        pin_name = "~"  # Default KiCad name for unnamed pins
        pin_type = PinType.UNSPECIFIED

        # Try to find the component
        component = self.all_components.get(component_ref)
        if not component:
            logger.warning(
                f"Node {node_index}: Component '{component_ref}' not found for net '{net_name}'"
            )
            return pin_name, pin_type

        # Try to find the pin in this component
        pin = component.pins.get(pin_number)
        if not pin:
            logger.warning(
                f"Node {node_index}: Pin '{pin_number}' not found in component '{component_ref}' for net '{net_name}'"
            )
            return pin_name, pin_type

        # Found both component and pin
        pin_name = pin.name or "~"  # Use ~ if name is empty
        pin_type = pin.pin_type
        logger.debug(
            f"Node {node_index}: Found pin '{pin_name}' of type '{pin_type.value}'"
        )

        return pin_name, pin_type

    def _parse_nets(self, net_blocks: List[List[Any]]) -> None:
        """
        Parse net blocks from the netlist and populate the internal `Net` objects
        within the circuit hierarchy. Ensures no duplicate nodes and proper net naming.

        Args:
            net_blocks: List of net blocks from the netlist
        """
        logger.info(f"Parsing {len(net_blocks)} net blocks...")

        # First pass: Build complete net mapping and collect all nodes
        self._build_net_mapping(net_blocks)
        logger.debug(f"Built net name mapping with {len(self.net_name_map)} entries")

        # Track processed nodes to prevent duplicates
        processed_nodes = set()  # (net_name, component_ref, pin_number)

        # Process each net block
        for i, net_block in enumerate(net_blocks):
            if not isinstance(net_block, list) or len(net_block) < 3:
                logger.warning(f"Skipping malformed net block: {net_block}")
                continue

            # Extract net information
            net_info = self._extract_net_info(net_block)
            if not net_info:
                continue

            net_name = net_info["name"]
            net_code = net_info["code"]
            net_attributes = net_info["attributes"]
            nodes_data = net_info["nodes"]

            # Skip empty nets
            if not nodes_data:
                logger.warning(
                    f"Net '{net_name}' (code {net_code}) has no nodes. Skipping."
                )
                continue

            # Get standardized name once for the entire net
            standardized_name = self._standardize_net_name(net_name)
            logger.debug(
                f"Processing net '{net_name}' -> '{standardized_name}' with {len(nodes_data)} nodes"
            )

            # Process each node
            for node_data in nodes_data:
                node_info = self._extract_node_info(node_data, net_name)
                if not node_info:
                    continue

                component_ref = node_info["component_ref"]
                pin_number = node_info["pin_number"]

                # Check for duplicate nodes
                node_key = (standardized_name, component_ref, pin_number)
                if node_key in processed_nodes:
                    logger.debug(f"Skipping duplicate node: {node_key}")
                    continue
                processed_nodes.add(node_key)

                # Get component's sheet path
                node_sheetpath = self._get_component_sheet_path(component_ref, net_name)

                # Find target subcircuit and create/update net
                self._add_node_to_subcircuit(
                    component_ref=component_ref,
                    pin_number=pin_number,
                    net_name=standardized_name,
                    net_code=net_code,
                    sheet_path=node_sheetpath,
                    net_attributes=net_attributes,
                )

        logger.info(
            f"Finished parsing nets. Processed {len(processed_nodes)} unique nodes."
        )

    def _extract_net_info(self, net_block: List[Any]) -> Optional[Dict[str, Any]]:
        """Extract basic information from a net block."""
        try:
            net_info = {
                "name": "UnnamedNet",
                "code": "0",
                "attributes": {},
                "nodes": [],
            }

            for item in net_block:
                if not isinstance(item, list) or len(item) < 2:
                    continue
                key, value = item[0], item[1]

                if key == "name":
                    net_info["name"] = value
                elif key == "code":
                    net_info["code"] = str(value)
                elif key == "node":
                    net_info["nodes"].append(item)
                elif key == "class":
                    net_info["attributes"]["class"] = value
                elif key not in ["name", "code", "node", "class"]:
                    net_info["attributes"][key] = value

            return net_info
        except Exception as e:
            logger.error(f"Error extracting net info: {e}", exc_info=True)
            return None

    def _extract_node_info(
        self, node_data: List[Any], net_name: str
    ) -> Optional[Dict[str, str]]:
        """Extract component reference and pin number from node data."""
        try:
            if not isinstance(node_data, list) or len(node_data) < 3:
                return None

            component_ref = "UnknownRef"
            pin_number = "UnknownPin"

            for item in node_data[1:]:
                if isinstance(item, list) and len(item) >= 2:
                    if item[0] == "ref":
                        component_ref = item[1]
                    elif item[0] == "pin":
                        pin_number = str(item[1])

            return {"component_ref": component_ref, "pin_number": pin_number}
        except Exception as e:
            logger.error(
                f"Error extracting node info for net '{net_name}': {e}", exc_info=True
            )
            return None

    def _get_component_sheet_path(self, component_ref: str, net_name: str) -> str:
        """Get the sheet path for a component, with proper error handling."""
        sheet_path = self.component_sheetpaths.get(component_ref)

        if not sheet_path:
            logger.warning(
                f"Component '{component_ref}' not found in sheetpaths for net '{net_name}'. Using root."
            )
            sheet_path = "/"

        return self._normalize_sheet_path(sheet_path)

    def _add_node_to_subcircuit(
        self,
        component_ref: str,
        pin_number: str,
        net_name: str,
        net_code: str,
        sheet_path: str,
        net_attributes: Dict[str, Any],
    ) -> None:
        """Add a node to the appropriate subcircuit's net."""
        try:
            # Find target subcircuit
            target_subcircuit = self._find_or_create_subcircuit(sheet_path)
            if not target_subcircuit:
                logger.error(
                    f"Could not find/create subcircuit for '{sheet_path}'. Skipping node."
                )
                return

            # Get local net name
            local_name, hierarchical_name, is_hierarchical = self._get_local_net_name(
                net_name, sheet_path
            )

            # Find or create net
            if local_name in target_subcircuit.nets:
                net = target_subcircuit.nets[local_name]
            else:
                net = Net(
                    name=local_name,
                    code=net_code,
                    sheetpath=sheet_path,
                    is_hierarchical=is_hierarchical,
                    hierarchical_name=hierarchical_name,
                    attributes=net_attributes.copy(),
                )
                target_subcircuit.nets[local_name] = net

            # Get pin details and create node
            pin_name, pin_type = self._get_pin_details(
                component_ref, pin_number, net_name, 0
            )
            node = Node(
                component_ref=component_ref,
                pin_number=pin_number,
                pin_name=pin_name,
                pin_type=pin_type,
            )

            # Add node to net
            net.add_node(node)
            logger.debug(
                f"Added node {component_ref}:{pin_number} to net '{local_name}' in '{sheet_path}'"
            )

        except Exception as e:
            logger.error(f"Error adding node to subcircuit: {e}", exc_info=True)

    # --------------------------------------------------------------------------
    # Helper methods for net parsing
    # --------------------------------------------------------------------------
    def _build_net_mapping(self, net_blocks: List[List[Any]]) -> None:
        """
        Build a mapping from potentially non-standard net names (like those starting
        with '/') to their standardized root name. This helps resolve connections
        across hierarchical boundaries where KiCad might use different naming conventions.
        Stores the result in self.net_name_map.

        Example: /Net(R1-Pad1) might map to Net-(R1-Pad1)
        """
        self.net_name_map = {}  # Initialize the map
        for i, net_block in enumerate(net_blocks):
            net_name = None
            try:
                # Find the name item: (name "NetName")
                for item in net_block:
                    if isinstance(item, list) and len(item) == 2 and item[0] == "name":
                        net_name = item[1]
                        break
                if net_name is None:
                    logger.warning(
                        f"  Net Block {i+1}: Could not find name in block: {net_block}"
                    )
                    continue

                standardized = net_name  # Default to original
                if net_name.startswith("/"):
                    standardized = net_name[1:]
                    logger.debug(
                        f"  Net Block {i+1}: Standardizing '{net_name}' -> '{standardized}'"
                    )

                # Store the mapping from original to standardized
                # If multiple originals map to the same standard, that's okay.
                self.net_name_map[net_name] = standardized
                # Also ensure the standardized name maps to itself if it wasn't already mapped
                if standardized not in self.net_name_map:
                    self.net_name_map[standardized] = standardized

            except (IndexError, TypeError) as e:
                logger.warning(
                    f"  Net Block {i+1}: Error processing block for mapping: {net_block}. Error: {e}"
                )

        # Log the final mapping only if debug logging is enabled
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Final Net Name Mapping:")
            for k, v in self.net_name_map.items():
                logger.debug(f"  '{k}' -> '{v}'")

    def _standardize_net_name(self, net_name: str) -> str:
        """
        Standardize net names by removing leading '/' and using map for known equivalents.

        Args:
            net_name: The original net name from the netlist

        Returns:
            Standardized net name
        """
        # First check the pre-built map for known equivalents
        if net_name in self.net_name_map:
            standardized = self.net_name_map[net_name]
            if standardized != net_name:
                logger.debug(
                    f"Standardizing net name via map: '{net_name}' -> '{standardized}'"
                )
            return standardized

        # If not in map but has leading slash, remove it
        if net_name.startswith("/"):
            standardized = net_name[1:]
            logger.debug(
                f"Standardizing net name (removing leading '/'): '{net_name}' -> '{standardized}'"
            )
            return standardized

        # No standardization needed
        logger.debug(f"No standardization needed for net name: '{net_name}'")
        return net_name

    def _get_local_net_name(
        self, full_net_name: str, sheet_path: str
    ) -> Tuple[str, str, bool]:
        """
        Determines the local net name within a sheet and the full hierarchical name.

        Args:
            full_net_name: The standardized potentially hierarchical net name
                (e.g., Sheet1/NetLabel or NetLabel).
            sheet_path: The sheet path where this net is defined or referenced
                (e.g., /Sheet1/).

        Returns:
            Tuple containing:
                - local_name: The net name within the local sheet context
                - hierarchical_name: The full hierarchical path of the net
                - is_hierarchical: Whether the net is hierarchical
        """
        normalized_sheet_path = self._normalize_sheet_path(sheet_path)
        logger.debug(f"Normalized sheet path: '{normalized_sheet_path}'")

        # The input `full_net_name` is assumed to be standardized already (e.g., no leading '/')
        # Determine if the original KiCad name implied hierarchy
        is_hierarchical = (
            full_net_name != self.net_name_map.get(f"/{full_net_name}", full_net_name)
            or "/" in full_net_name
        )  # Check if original started with / or contains /

        if "/" in full_net_name and not full_net_name.startswith(
            "/"
        ):  # Handles names like "Sheet1/NetLabel"
            # This implies a hierarchical structure relative to the current sheet_path context
            parts = full_net_name.split("/")
            local_name = parts[-1]
            # Construct the full path based on the sheet_path context
            hierarchical_name = f"{normalized_sheet_path}{full_net_name}"  # This might need refinement based on KiCad's exact naming
            is_hierarchical = True  # Mark as hierarchical based on structure
            logger.debug(
                f"Relative hierarchical net detected. Local: '{local_name}', Constructed Hierarchical: '{hierarchical_name}'"
            )

        elif is_hierarchical:
            # Original name likely started with '/', but standardized name doesn't.
            # The standardized name IS the local name in this case.
            local_name = full_net_name
            hierarchical_name = f"/{full_net_name}"  # Reconstruct the absolute path
            logger.debug(
                f"Absolute hierarchical net detected. Hierarchical: '{hierarchical_name}', Local: '{local_name}'"
            )
        else:
            # Local net: name does not include path, construct hierarchical name based on context
            local_name = full_net_name
            if normalized_sheet_path == "/":
                hierarchical_name = f"/{local_name}"  # Root level nets start with /
            else:
                # Ensure sheet path ends with / before appending local name
                hierarchical_name = f"{normalized_sheet_path}{local_name}"

        # Final check for consistency
        if not hierarchical_name.startswith("/"):
            logger.warning(
                f"Generated hierarchical name '{hierarchical_name}' does not start with '/'. Forcing."
            )
            hierarchical_name = f"/{hierarchical_name.lstrip('/')}"

        return local_name, hierarchical_name, is_hierarchical

    def _normalize_sheet_path(self, sheet_path: str) -> str:
        """Ensure sheet path starts and ends with '/', and removes double slashes."""
        original_path = sheet_path
        if not sheet_path:
            path = "/"
        else:
            path = sheet_path
        if not path.startswith("/"):
            path = "/" + path
        if not path.endswith("/"):
            path += "/"
        while "//" in path:
            path = path.replace("//", "/")
        if path != "/" and path.endswith(
            "//"
        ):  # Handle potential trailing double slash after replace
            path = path[:-1]
        if path != original_path:
            logger.debug(f"Normalizing sheet path: '{original_path}' -> '{path}'")
        return path

    def _find_or_create_subcircuit(self, path: str) -> Optional[Subcircuit]:
        """
        Find an existing subcircuit by path or create it if it doesn't exist.

        Args:
            path: Path string to find or create

        Returns:
            Found or created Subcircuit object, or None if creation failed
        """
        normalized_path = self._normalize_sheet_path(path)

        if normalized_path in self.subcircuits:
            return self.subcircuits[normalized_path]

        # If not in lookup, traverse or create
        if normalized_path == "/":
            logger.debug("Path is root, returning root subcircuit.")
            if "/" not in self.subcircuits:
                self.subcircuits["/"] = self.circuit.root
            return self.circuit.root

        parts = normalized_path.strip("/").split("/")
        current_subcircuit = self.circuit.root
        current_path_so_far = "/"

        for part in parts:
            if not part:
                continue  # Skip empty parts resulting from slashes

            # Use Path object for safer path joining
            path_obj = Path(current_path_so_far)
            child_path = self._normalize_sheet_path(str(path_obj / part))
            logger.debug(
                f"Processing path part: '{part}', Target child path: '{child_path}'"
            )

            # Check if child exists by path in the global lookup first
            if child_path in self.subcircuits:
                logger.debug(
                    f"Found existing child subcircuit for path '{child_path}' in global lookup."
                )
                current_subcircuit = self.subcircuits[child_path]
            # If not in global lookup, check the current parent's children by name
            elif part in current_subcircuit.children:
                logger.debug(
                    f"Found existing child subcircuit by name '{part}' under parent '{current_subcircuit.name}'. Adding to global lookup."
                )
                current_subcircuit = current_subcircuit.children[part]
                self.subcircuits[child_path] = current_subcircuit
            else:
                # If truly not found, create it
                logger.warning(
                    f"Subcircuit for path '{child_path}' (name '{part}') not found under parent '{current_subcircuit.name}'. Creating it."
                )
                # Use the part name for the new subcircuit's name
                new_subcircuit = Subcircuit(name=part)
                current_subcircuit.children[part] = (
                    new_subcircuit  # Add to parent's children dict
                )
                current_subcircuit = new_subcircuit
                # Add to the global lookup as well
                self.subcircuits[child_path] = new_subcircuit
                logger.debug(f"Created new subcircuit '{part}' at path '{child_path}'")

            current_path_so_far = child_path  # Update path for next iteration

        logger.debug(
            f"Returning subcircuit '{current_subcircuit.name}' for path '{path}'"
        )
        return current_subcircuit

    def _get_subcircuit_name_from_path(self, path: str) -> str:
        """Extract the last part of a sheet path as the subcircuit name."""
        normalized = self._normalize_sheet_path(path)
        if normalized == "/":
            return "Root"
        return normalized.strip("/").split("/")[-1]

    def _get_parent_path(self, path: str) -> str:
        """
        Determine the parent path for a given path.

        Args:
            path: The path to find the parent for

        Returns:
            The parent path or empty string if it's a top-level path
        """
        if path == "/" or path == "":
            return ""  # Root has no parent

        # Normalize path for consistent handling
        normalized = self._normalize_sheet_path(path)

        # Remove trailing slash for processing
        if normalized.endswith("/"):
            normalized = normalized[:-1]

        # Find last slash to get parent path
        last_slash = normalized.rfind("/")
        if last_slash <= 0:  # Path is top-level or malformed
            return "/"  # Return root as parent

        parent = normalized[: last_slash + 1]  # Include trailing slash
        return parent

    def _extract_sheetpath(self, sheetpath_item: List[Any]) -> str:
        """Extract the sheetpath string from a (sheetpath names /...) item."""
        # Expected format: (sheetpath (names "/Sheet1/") (tstamps "/UUID1/"))
        if (
            not isinstance(sheetpath_item, list)
            or len(sheetpath_item) < 3
            or sheetpath_item[0] != "sheetpath"
        ):
            logger.warning(
                f"Invalid sheetpath item format: {sheetpath_item}. Defaulting to '/'"
            )
            return "/"
        try:
            # Find the 'names' sub-list
            for sub_item in sheetpath_item[1:]:
                if (
                    isinstance(sub_item, list)
                    and len(sub_item) == 2
                    and sub_item[0] == "names"
                ):
                    path = sub_item[1]
                    normalized_path = self._normalize_sheet_path(path)
                    logger.debug(
                        f"Extracted sheetpath: '{path}' -> Normalized: '{normalized_path}' from item: {sheetpath_item}"
                    )
                    return normalized_path
            logger.warning(
                f"Could not find 'names' in sheetpath item: {sheetpath_item}. Defaulting to '/'"
            )
            return "/"
        except (IndexError, TypeError):
            logger.warning(
                f"Error parsing sheetpath item: {sheetpath_item}. Defaulting to '/'"
            )
            return "/"

    def _parse_design_properties(self, design_expr: List[Any]) -> None:
        """Parse top-level design properties."""
        logger.debug("Parsing design properties...")
        # Example: (design (source "/path/to/project.kicad_sch") (date "...") (tool "...") ...)
        if not isinstance(design_expr, list) or design_expr[0] != "design":
            logger.warning(f"Expected 'design' expression, got: {design_expr}")
            return

        for item in design_expr[1:]:  # Skip the 'design' keyword
            if isinstance(item, list) and len(item) == 2:
                key = item[0]
                value = item[1]
                # Examples: (source example.sch), (date "...") , (tool "...")
                if key in ["source", "date", "tool", "version"]:
                    self.circuit.properties[key] = value
                elif key == "sheet":  # Handle top-level sheet info if needed
                    # Example: (sheet (number 1) (name /) (tstamps /) (title_block ...))
                    # Could extract top-level sheet name/title here if necessary
                    pass
        logger.debug("Finished parsing design properties.")

    def _verify_and_log_hierarchy(self) -> None:
        """Verify the constructed hierarchy and log it for debugging."""
        logger.info("Verifying and logging constructed circuit hierarchy...")
        if not self.circuit or not self.circuit.root:
            logger.error("Circuit or root subcircuit is not initialized.")
            return

        # Log the global path lookup table
        for path, subcircuit in self.subcircuits.items():  # Use self.subcircuits
            pass  # Removed logger.debug call, add pass to avoid indentation error
        # Log the actual hierarchy tree structure
        self._log_subcircuit_hierarchy(self.circuit.root)

        # Verify all subcircuits in the lookup table are actually in the tree
        all_paths_in_lookup = set(self.subcircuits.keys())  # Use self.subcircuits
        all_paths_in_tree = set()
        nodes_to_visit = [("/", self.circuit.root)]  # Tuple: (path, subcircuit_obj)
        visited_objs = set()

        while nodes_to_visit:
            current_path, current_node = nodes_to_visit.pop(0)
            current_node_id = id(current_node)
            if current_node_id in visited_objs:
                continue  # Avoid cycles if any exist
            visited_objs.add(current_node_id)
            all_paths_in_tree.add(current_path)

            for child_name, child_node in current_node.children.items():
                # Construct child path carefully
                child_full_path = self._normalize_sheet_path(current_path + child_name)
                nodes_to_visit.append((child_full_path, child_node))

        # Compare sets
        paths_only_in_lookup = all_paths_in_lookup - all_paths_in_tree
        paths_only_in_tree = (
            all_paths_in_tree - all_paths_in_lookup
        )  # Should be empty if lookup is correct

        if paths_only_in_lookup:
            logger.warning(
                f"Found {len(paths_only_in_lookup)} paths in lookup table but not reachable in the final tree: {paths_only_in_lookup}"
            )
        if paths_only_in_tree:
            logger.error(
                f"Found {len(paths_only_in_tree)} paths in the final tree but missing from the lookup table: {paths_only_in_tree}"
            )  # This indicates a bug

        logger.info("Hierarchy verification and logging complete.")

    def detect_duplicate_circuits(self) -> DuplicateDetectionResult:
        """
        Analyze all subcircuits to find duplicates based on:
        - Same source schematic file (from Sheetfile property)
        - Identical component topology (same components, values, timestamps)

        Returns:
            DuplicateDetectionResult containing templates and groupings
        """
        logger.info("Starting duplicate circuit detection analysis...")

        # Step 1: Extract schematic sources and signatures for all subcircuits
        circuit_analysis = (
            {}
        )  # subcircuit_name -> (source_file, signature, subcircuit_obj)

        for path, subcircuit in self.subcircuits.items():
            if path == "/" or not subcircuit.components:
                continue  # Skip root and empty subcircuits

            source_file = self._extract_schematic_source(subcircuit)
            if not source_file:
                logger.debug(f"No source file found for '{subcircuit.name}' - skipping")
                continue  # Skip if no source file found

            signature = self._generate_component_signature(subcircuit)
            circuit_analysis[subcircuit.name] = (source_file, signature, subcircuit)

            logger.info(
                f"Circuit '{subcircuit.name}': source='{source_file}', signature='{signature[:16]}...'"
            )

        # Step 2: Group circuits by source file and signature
        source_groups = defaultdict(
            list
        )  # source_file -> [(name, signature, subcircuit)]

        for name, (source_file, signature, subcircuit) in circuit_analysis.items():
            source_groups[source_file].append((name, signature, subcircuit))

        # Step 3: Identify duplicates and create templates
        templates = {}
        duplicate_groups = {}
        unique_circuits = []

        for source_file, circuits in source_groups.items():
            if len(circuits) == 1:
                # Single circuit using this source file
                unique_circuits.append(circuits[0][0])
                logger.debug(
                    f"Unique circuit: '{circuits[0][0]}' (source: {source_file})"
                )
            else:
                # Multiple circuits using same source file - check signatures
                signature_groups = defaultdict(list)
                for name, signature, subcircuit in circuits:
                    signature_groups[signature].append((name, subcircuit))

                for signature, circuit_group in signature_groups.items():
                    if len(circuit_group) == 1:
                        # Unique signature within this source file
                        unique_circuits.append(circuit_group[0][0])
                        logger.debug(
                            f"Unique circuit: '{circuit_group[0][0]}' (unique signature)"
                        )
                    else:
                        # True duplicates found!
                        template_id = self._generate_template_id(source_file)
                        instance_names = [name for name, _ in circuit_group]
                        representative = circuit_group[0][
                            1
                        ]  # Use first as representative

                        template = CircuitTemplate(
                            source_file=source_file,
                            component_signature=signature,
                            instances=instance_names,
                            canonical_name=self._generate_canonical_name(source_file),
                            representative_circuit=representative,
                        )

                        templates[template_id] = template

                        # Map each instance to this template
                        for name, _ in circuit_group:
                            duplicate_groups[name] = template_id

                        logger.info(
                            f"Detected duplicate template '{template_id}': {len(instance_names)} instances of '{source_file}'"
                        )
                        logger.info(f"  Instances: {instance_names}")

        result = DuplicateDetectionResult(
            templates=templates,
            unique_circuits=unique_circuits,
            duplicate_groups=duplicate_groups,
        )

        logger.info(
            f"Duplicate detection complete: {len(templates)} templates, {len(unique_circuits)} unique circuits"
        )
        return result

    def _extract_schematic_source(self, subcircuit: Subcircuit) -> Optional[str]:
        """
        Extract the source .kicad_sch file from component properties.

        Args:
            subcircuit: The subcircuit to analyze

        Returns:
            The source schematic filename or None if not found
        """
        # Look for Sheetfile property in any component
        for component in subcircuit.components.values():
            if "Sheetfile" in component.properties:
                source_file = component.properties["Sheetfile"]
                logger.debug(
                    f"Found source file '{source_file}' in component '{component.reference}'"
                )
                return source_file

        logger.debug(f"No source file found for subcircuit '{subcircuit.name}'")
        return None

    def _generate_component_signature(self, subcircuit: Subcircuit) -> str:
        """
        Create a hash based on:
        - Component types and values (not references)
        - Component timestamps (identical for copies)
        - Connection topology (normalized)

        Args:
            subcircuit: The subcircuit to analyze

        Returns:
            A hash string representing the circuit topology
        """
        signature_parts = []

        # Sort components by timestamp for consistent ordering (timestamps are identical for copies)
        components_by_timestamp = []
        for ref, component in subcircuit.components.items():
            timestamp = component.properties.get("tstamps", "no_timestamp")
            components_by_timestamp.append(
                (timestamp, component.value, component.symbol)
            )

        components_by_timestamp.sort()

        for timestamp, value, symbol in components_by_timestamp:
            # Component signature: value:symbol:timestamp (no reference to avoid differences)
            comp_sig = f"{value}:{symbol}:{timestamp}"
            signature_parts.append(comp_sig)

        # Add net topology (normalized by removing specific component references)
        sorted_nets = sorted(subcircuit.nets.items())
        for net_name, net in sorted_nets:
            # Normalize net signature by counting connections by component type rather than reference
            connection_types = []
            for node in net.nodes:
                # Find component by reference and use its type/value instead
                if node.component_ref in subcircuit.components:
                    comp = subcircuit.components[node.component_ref]
                    connection_types.append(
                        f"{comp.value}:{comp.symbol}:{node.pin_number}"
                    )
                else:
                    connection_types.append(f"unknown:{node.pin_number}")
            connection_types.sort()

            # Use a normalized net name pattern (remove specific net names that might differ)
            normalized_net_name = (
                "net" if not net_name.startswith("unconnected-") else "unconnected"
            )
            net_sig = (
                f"{normalized_net_name}:{len(net.nodes)}:{':'.join(connection_types)}"
            )
            signature_parts.append(net_sig)

        # Create hash of all signature parts
        full_signature = "|".join(signature_parts)
        hash_obj = hashlib.sha256(full_signature.encode("utf-8"))
        signature_hash = hash_obj.hexdigest()

        logger.debug(
            f"Generated signature for '{subcircuit.name}': {signature_hash[:16]}... (from {len(signature_parts)} parts)"
        )
        return signature_hash

    def _generate_template_id(self, source_file: str) -> str:
        """
        Generate a template ID from the source file name.

        Args:
            source_file: The .kicad_sch filename

        Returns:
            A clean template identifier
        """
        # Remove .kicad_sch extension and clean up
        template_id = source_file.replace(".kicad_sch", "").lower()
        # Replace non-alphanumeric with underscores
        import re

        template_id = re.sub(r"[^a-z0-9_]", "_", template_id)
        return template_id

    def _generate_canonical_name(self, source_file: str) -> str:
        """
        Generate a canonical Python class name from the source file.

        Args:
            source_file: The .kicad_sch filename

        Returns:
            A Python-friendly class name
        """
        # Remove extension and convert to PascalCase
        base_name = source_file.replace(".kicad_sch", "")

        # Split on underscores and capitalize each part
        parts = base_name.split("_")
        canonical = "".join(word.capitalize() for word in parts if word)

        # Ensure it starts with a letter
        if canonical and canonical[0].isdigit():
            canonical = "Circuit" + canonical

        return canonical or "Circuit"

    def _collect_attached_subcircuits(
        self, subcircuit: Subcircuit, attached: Set[str]
    ) -> None:
        """Recursively collect the names of all subcircuits attached to the hierarchy."""
        # This method seems less reliable than traversing the tree directly.
        # Relying on the verification logic in _verify_and_log_hierarchy instead.
        # Keeping the method signature for now if needed later.
        pass  # See _verify_and_log_hierarchy for tree traversal logic

    def _log_subcircuit_hierarchy(self, subcircuit: Subcircuit, level: int = 0) -> None:
        """Recursively log the subcircuit hierarchy structure."""
        indent = "  " * level
        details = f"Comps: {len(subcircuit.components)}, Nets: {len(subcircuit.nets)}, Children: {len(subcircuit.children)}"
        # Find the path for this subcircuit from the lookup table for better context
        path_str = "[Unknown Path]"
        for p, s in self.subcircuits.items():  # Use self.subcircuits
            if s is subcircuit:
                path_str = f"Path: '{p}'"
                break
        logger.debug(
            f"{indent}- Subcircuit: '{subcircuit.name}' ({path_str}, {details})"
        )
        # Log component refs for context
        if subcircuit.components:
            pass  # Removed logger.debug for components
        # Log net names for context (local names)
        if subcircuit.nets:
            # Log local name and hierarchical name for clarity
            net_info = [
                f"'{n.name}' (Hier: '{n.hierarchical_name}')"
                for n in subcircuit.nets.values()
            ]
            pass  # Removed logger.debug for nets

        for child_key, child_obj in subcircuit.children.items():
            # Log the key used in the children dict vs the child's actual name
            # Keep logging child traversal for structure understanding if needed at INFO level
            # logger.info(f"{indent}  Child Key: '{child_key}' -> Child Name: '{child_obj.name}'")
            self._log_subcircuit_hierarchy(child_obj, level + 1)


# ------------------------------------------------------------------------------
# Top-level convert function
# ------------------------------------------------------------------------------
def convert_netlist(input_path: Path, output_path: Path) -> None:
    """
    Convert a KiCad netlist file to Circuit-Synth JSON format.

    Args:
        input_path: Path to the input KiCad netlist file (.net).
        output_path: Path to save the output JSON file.
    """
    # Setup basic logging if not already configured (but don't force DEBUG level)
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        )
    logger.debug(f"Starting conversion: {input_path} -> {output_path}")

    parser = CircuitSynthParser()
    try:
        circuit = parser.parse_kicad_netlist(input_path)
        # Call the hierarchy verification *before* converting to dict
        parser._verify_and_log_hierarchy()
        circuit_dict = circuit.to_dict()

        logger.debug(f"Conversion successful. Writing JSON to {output_path}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(circuit_dict, f, indent=2)
        logger.debug("JSON file written successfully.")

    except Exception as e:
        logger.error(f"Error during netlist conversion: {e}")
        raise


def main():
    """CLI entry point for netlist import."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Convert KiCad netlist to Circuit-Synth JSON"
    )
    parser.add_argument(
        "input_netlist", type=Path, help="Input KiCad netlist file (.net)"
    )
    parser.add_argument("output_json", type=Path, help="Output JSON file")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    # Configure logging
    level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=level, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )

    try:
        convert_netlist(args.input_netlist, args.output_json)
        print(f"✓ Successfully converted {args.input_netlist} to {args.output_json}")
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    return 0


# Example usage (if run as script)
if __name__ == "__main__":
    import sys

    sys.exit(main())
