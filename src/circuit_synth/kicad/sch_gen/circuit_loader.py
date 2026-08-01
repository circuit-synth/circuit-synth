# -*- coding: utf-8 -*-
#
# circuit_loader.py
#
# Parses the hierarchical circuit JSON into Circuit objects.
# Also provides assign_subcircuit_instance_labels() to rename repeated subcircuit instances.
#
# Updated to use SchematicSymbol directly instead of legacy Component class

import json
import logging
import uuid as uuid_module
from pathlib import Path
from typing import Any, Dict

from kicad_sch_api.core.types import Point, SchematicPin, SchematicSymbol

from ...core.hierarchy import Port as HierarchyPort

logger = logging.getLogger(__name__)


class Pin:
    """
    Represents a single pin on a component (including location, orientation, etc.).
    """

    def __init__(
        self,
        number: str,
        name: str,
        function: str,
        orientation: float,
        x: float,
        y: float,
        length: float,
    ):
        self.number = number  # e.g. "1"
        self.name = name  # e.g. "GND"
        self.function = function  # e.g. "power_in"
        self.orientation = orientation
        self.x = x
        self.y = y
        self.length = length

    def __repr__(self):
        return (
            f"Pin(number='{self.number}', name='{self.name}', function='{self.function}', "
            f"orientation={self.orientation}, x={self.x}, y={self.y}, length={self.length})"
        )


class Net:
    """
    Represents an electrical net (by name) and the pin connections (component ref, pin_number).
    """

    def __init__(self, name: str):
        self.name = name
        # Each connection is a tuple (comp_ref, pin_number).
        self.connections: List[tuple] = []
        # Power net properties
        self.is_power = False
        self.power_symbol = None
        self.trace_current = None
        self.impedance = None
        self.properties = {}

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Net":
        """Create Net from dictionary representation."""
        net = Net(data.get("name", ""))
        net.is_power = data.get("is_power", False)
        net.power_symbol = data.get("power_symbol")
        net.trace_current = data.get("trace_current")
        net.impedance = data.get("impedance")
        net.properties = data.get("properties", {})
        return net

    def __repr__(self):
        flags = []
        if self.is_power:
            flags.append("power")
        if self.impedance:
            flags.append(f"{self.impedance}Ω")
        flag_str = f" [{', '.join(flags)}]" if flags else ""
        return f"Net(name='{self.name}'{flag_str}, connections={self.connections})"


class Circuit:
    """
    Holds all components (as SchematicSymbols), nets, and child subcircuits (instances).
    """

    def __init__(self, name: str):
        self.name = name
        self.components: List[SchematicSymbol] = []
        self.nets: List[Net] = []
        # child_instances: each item is { "sub_name": <str>, "instance_label": <str>, "x": float, "y": float, "width": float, "height": float }
        # We'll store subcircuit usage references here for building hierarchical sheets.
        # x, y, width, height are added during collision placement
        self.child_instances = []
        # Annotations for text elements
        self._annotations = []
        # Declared hierarchical ports (core.hierarchy.Port). Empty when the
        # circuit does not declare an interface.
        self.ports: List[HierarchyPort] = []

    @property
    def port_net_names(self) -> Dict[str, str]:
        """Map each declared port name to the net bound to it.

        Returns:
            ``{port_name: net_name}`` for every declared port.
        """
        return {port.name: port.net_name for port in self.ports}

    @property
    def net_port_names(self) -> Dict[str, str]:
        """Map each net that is exported to the port name exporting it.

        Returns:
            ``{net_name: port_name}``. If several ports bind the same net, the
            first declaration wins, since that is the name KiCad will show.
        """
        mapping: Dict[str, str] = {}
        for port in self.ports:
            mapping.setdefault(port.net_name, port.name)
        return mapping

    def add_component(self, comp: SchematicSymbol):
        logger.debug(
            f"Adding component {comp.reference} ({comp.lib_id}) to circuit '{self.name}'"
        )
        self.components.append(comp)

    def add_net(self, net: Net):
        logger.debug(
            f"Adding net {net.name} with {len(net.connections)} connections to circuit '{self.name}'"
        )
        self.nets.append(net)

    def __repr__(self):
        return (
            f"Circuit(name='{self.name}', "
            f"components=[{', '.join(str(c) for c in self.components)}], "
            f"nets=[{', '.join(str(n) for n in self.nets)}], "
            f"child_instances={self.child_instances})"
        )


def load_circuit_hierarchy(json_file: str) -> (Circuit, Dict[str, Circuit]):
    """
    Load the top-level circuit from JSON, plus recursively parse its subcircuits.
    Return (top_circuit, subcircuit_dict).

    subcircuit_dict: dict[subcircuit_name, Circuit]
                     includes the top circuit as well, keyed by top_circuit.name
    """
    logger.info(f"Loading circuit JSON from {json_file}")
    path_obj = Path(json_file)
    if not path_obj.exists():
        raise FileNotFoundError(f"Could not find circuit JSON: {json_file}")

    with open(path_obj, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Create a dictionary for all subcircuits
    all_subcircuits: Dict[str, Circuit] = {}

    # Parse the top circuit from the JSON root
    top_circuit = _parse_circuit(data, all_subcircuits)

    # Save the original name for later use as project name
    original_name = top_circuit.name

    # Rename the original circuit to match project name in circuit dictionary
    # but keep it as the top circuit (will be referenced by the top_sheet)
    if original_name in all_subcircuits:
        del all_subcircuits[original_name]

    # We'll use the original name instead of "Root" for the main schematic
    all_subcircuits[original_name] = top_circuit

    logger.info(
        f"Finished building circuit hierarchy. Found {len(all_subcircuits)} unique subcircuit(s)."
    )
    return top_circuit, all_subcircuits


def _parse_circuit(circ_data: dict, sub_dict: Dict[str, Circuit]) -> Circuit:
    """
    Parse a single circuit from circ_data. Also parse its subcircuits recursively.
    If circ_data["name"] is already in sub_dict, check whether it's truly the same circuit:
      - If identical, reuse it.
      - If different, raise an error (naming collision).
    Otherwise, create a new Circuit, parse components, nets, subcircuits,
    then store it in sub_dict.
    """
    c_name = circ_data.get("name", "UnnamedCircuit")

    # Strip "build_" prefix if present
    if c_name.startswith("build_"):
        c_name = c_name[6:]  # Remove first 6 characters ("build_")
        # Also capitalize words properly (e.g., "root_circuit" -> "Root Circuit")
        c_name = " ".join(word.capitalize() for word in c_name.split("_"))

    logger.debug(f"Parsing circuit named '{c_name}'...")

    # Every entry in the JSON is a distinct instance, even when two instances
    # come from the same @circuit function and therefore share a name. Each one
    # has its own component references and its own nets connected to its ports,
    # so each needs its own Circuit and its own .kicad_sch file.
    if c_name in sub_dict:
        c_name = _unique_circuit_name(c_name, sub_dict)
        logger.debug(f"Renamed duplicate subcircuit instance to '{c_name}'")

    # Otherwise, create a new Circuit
    circuit = Circuit(name=c_name)
    sub_dict[c_name] = circuit

    # Parse components
    comps_data = circ_data.get("components", {})
    # Handle both list and dict formats
    if isinstance(comps_data, dict):
        comps_data = [
            {"ref": ref, **comp_info} for ref, comp_info in comps_data.items()
        ]

    for comp_dict in comps_data:
        ref = comp_dict["ref"]
        symbol_id = comp_dict["symbol"]
        value = comp_dict.get("value", symbol_id.split(":")[-1])
        footprint = comp_dict.get("footprint", "")

        # Extract ALL properties (system + user) using property_utils
        from ..property_utils import extract_component_properties, extract_dnp_value

        properties = extract_component_properties(comp_dict, default_hierarchy_path="/"  if not hasattr(circuit, 'hierarchical_path') else circuit.hierarchical_path)

        # Handle DNP special case: KiCad has built-in dnp attribute
        dnp_value = extract_dnp_value(comp_dict)

        # Create SchematicSymbol with properties
        # NOTE: kicad-sch-api SchematicSymbol doesn't support dnp parameter yet
        # DNP is written as a property for now. in_bom/on_board flags can be set based on DNP.
        comp = SchematicSymbol(
            reference=ref,
            value=value,
            lib_id=symbol_id,
            position=Point(0.0, 0.0),  # Will be set during placement
            rotation=0.0,
            footprint=footprint,
            properties=properties,  # FIXED: Use extracted properties instead of hardcoded
            pins=[],
            uuid=str(uuid_module.uuid4()),
            in_bom=not dnp_value,  # If DNP, exclude from BOM
            on_board=not dnp_value,  # If DNP, exclude from board
        )

        # Parse pins and convert to SchematicPin
        pin_list = comp_dict.get("pins", [])
        for p in pin_list:
            pin_obj = SchematicPin(
                number=str(p.get("num", "")),
                name=p.get("name", ""),
                pin_type=p.get("func", "passive"),  # Changed from 'type' to 'pin_type'
                position=Point(float(p.get("x", 0)), float(p.get("y", 0))),
                rotation=float(
                    p.get("orientation", 0)
                ),  # Changed from 'orientation' to 'rotation'
            )
            comp.pins.append(pin_obj)

        circuit.add_component(comp)

    # Parse nets
    nets_data = circ_data.get("nets", {})
    for net_name, net_info in nets_data.items():
        # Handle both old format (list of connections) and new format (dict with metadata)
        if isinstance(net_info, list):
            # Old format: just connections
            connections = net_info
            net_obj = Net.from_dict({"name": net_name})  # Use from_dict for consistency
        else:
            # New format: dict with connections and metadata
            # Fixed for Issue #385: Use "nodes" key instead of "connections" key
            # The NetlistExporter uses "nodes" for KiCad compatibility
            connections = net_info.get("nodes", net_info.get("connections", []))
            # Create Net with metadata using from_dict
            net_dict = {
                "name": net_name,
                "is_power": net_info.get("is_power", False),
                "power_symbol": net_info.get("power_symbol"),
                "trace_current": net_info.get("trace_current"),
                "impedance": net_info.get("impedance"),
                "properties": net_info.get("properties", {}),
            }
            net_obj = Net.from_dict(net_dict)

        # Parse connections and add them to the net
        for conn in connections:
            comp_ref = conn["component"]
            pin_data = conn["pin"]

            # Pin identification. The pin number is preferred because it is the
            # only identifier guaranteed to be unique within a symbol: passive
            # parts such as Device:R leave every pin name empty, and larger
            # parts repeat names (an STM32 has three pins called VDD), both of
            # which collapse every connection onto one pin when matched by name.
            pin_identifier = None

            if pin_data.get("number") not in (None, ""):
                pin_identifier = str(pin_data["number"])
                logger.debug(
                    f"Using pin number '{pin_identifier}' for {comp_ref} in net {net_name}"
                )
            elif pin_data.get("name") and pin_data["name"] != "~":
                pin_identifier = pin_data["name"]
                logger.debug(
                    f"Using pin name '{pin_identifier}' for {comp_ref} in net {net_name}"
                )
            else:
                pin_identifier = str(pin_data.get("pin_id", ""))
                logger.debug(
                    f"Using pin ID '{pin_identifier}' for {comp_ref} in net {net_name}"
                )

            net_obj.connections.append((comp_ref, pin_identifier))
            logger.debug(
                f"Added connection: {comp_ref}.{pin_identifier} to net {net_name}"
            )

        circuit.add_net(net_obj)

    # Parse declared hierarchical ports
    for port_data in circ_data.get("ports", []) or []:
        circuit.ports.append(HierarchyPort.from_dict(port_data))
    if circuit.ports:
        logger.debug(
            f"Circuit '{c_name}' declares {len(circuit.ports)} hierarchical port(s): "
            f"{[p.name for p in circuit.ports]}"
        )

    # Parse subcircuits
    sub_list = circ_data.get("subcircuits", [])
    for sub_info in sub_list:
        child_circ = _parse_circuit(sub_info, sub_dict)
        circuit.child_instances.append(
            {"sub_name": child_circ.name, "instance_label": ""}  # assigned later
        )

    # Parse annotations
    annotations_data = circ_data.get("annotations", [])
    for annotation_dict in annotations_data:
        # Convert JSON annotation back to annotation object
        # For now, just store the dictionary data
        circuit._annotations.append(annotation_dict)

    return circuit


def _unique_circuit_name(base_name: str, sub_dict: Dict[str, Circuit]) -> str:
    """Derive an unused circuit name for a repeated subcircuit instance.

    The first instance keeps the plain name, so a design that instantiates a
    block once is unaffected. Later instances get a numeric suffix, which also
    becomes their .kicad_sch filename and their sheet name.

    Args:
        base_name: The name the instance would like to use.
        sub_dict: All circuits parsed so far, keyed by name.

    Returns:
        A name that is not yet present in ``sub_dict``.
    """
    index = 2
    while f"{base_name}{index}" in sub_dict:
        index += 1
    return f"{base_name}{index}"


def assign_subcircuit_instance_labels(
    top_circuit: Circuit, sub_dict: Dict[str, Circuit]
):
    """
    For each child circuit usage, generate instance_label like sub_name, sub_name1, sub_name2, etc.
    If a sub_name is used only once, we keep it as sub_name (no trailing number).
    If used multiple times, we number them sub_name1, sub_name2, ...
    Then recurse for each child.
    """
    logger.debug(
        f"Assigning subcircuit instance labels in circuit '{top_circuit.name}'"
    )
    usage_counts = {}

    # Count usage frequency of each sub_name
    for child in top_circuit.child_instances:
        sn = child["sub_name"]
        usage_counts[sn] = usage_counts.get(sn, 0) + 1

    # Assign labels
    label_indices = {}
    for child in top_circuit.child_instances:
        sn = child["sub_name"]
        if usage_counts[sn] == 1:
            # single usage => label is sub_name
            child["instance_label"] = sn
        else:
            # multiple usage => sub_name + index
            idx = label_indices.get(sn, 0) + 1
            label_indices[sn] = idx
            child["instance_label"] = f"{sn}{idx}"

    # Recurse
    for child in top_circuit.child_instances:
        sub_name = child["sub_name"]
        sub_circ = sub_dict[sub_name]
        assign_subcircuit_instance_labels(sub_circ, sub_dict)
