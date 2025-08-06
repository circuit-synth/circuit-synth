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

from circuit_synth.kicad.core.types import Point, SchematicPin, SchematicSymbol

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

    def __repr__(self):
        return f"Net(name='{self.name}', connections={self.connections})"


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

    # If we have a collision in name, compare content
    if c_name in sub_dict:
        existing_circuit = sub_dict[c_name]
        if not _circuits_match(existing_circuit, circ_data):
            raise ValueError(
                f"Error: Subcircuit name '{c_name}' is used more than once with different definitions.\n"
                f"Please rename one of them or unify the definitions."
            )
        # If it matches, reuse the existing circuit
        return existing_circuit

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

        # Create SchematicSymbol directly
        comp = SchematicSymbol(
            reference=ref,
            value=value,
            lib_id=symbol_id,
            position=Point(0.0, 0.0),  # Will be set during placement
            rotation=0.0,
            footprint=footprint,
            properties={"hierarchy_path": "/"},  # default top-level
            pins=[],
            uuid=str(uuid_module.uuid4()),
        )

        # Parse pins and convert to SchematicPin
        pin_list = comp_dict.get("pins", [])
        for p in pin_list:
            pin_obj = SchematicPin(
                number=str(p.get("num", "")),
                name=p.get("name", ""),
                type=p.get("func", "passive"),  # function -> type
                position=Point(float(p.get("x", 0)), float(p.get("y", 0))),
                orientation=int(float(p.get("orientation", 0))),
            )
            comp.pins.append(pin_obj)

        circuit.add_component(comp)

    # Parse nets
    nets_data = circ_data.get("nets", {})
    for net_name, connections in nets_data.items():
        net_obj = Net(net_name)
        for conn in connections:
            comp_ref = conn["component"]
            pin_data = conn["pin"]

            # Enhanced pin identification - store the most specific identifier available
            pin_identifier = None

            # First check if name is available (most specific)
            if "name" in pin_data and pin_data["name"] != "~":
                pin_identifier = pin_data["name"]
                logger.debug(
                    f"Using pin name '{pin_identifier}' for {comp_ref} in net {net_name}"
                )
            # Then check for number
            elif "number" in pin_data:
                pin_identifier = str(pin_data["number"])
                logger.debug(
                    f"Using pin number '{pin_identifier}' for {comp_ref} in net {net_name}"
                )
            # Finally fall back to pin_id
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


def _circuits_match(existing_circuit: Circuit, new_data: dict) -> bool:
    """Check if existing_circuit matches the new subcircuit data enough to reuse the same name."""
    existing_refs = sorted([c.reference for c in existing_circuit.components])
    new_comps_data = new_data.get("components", {})
    # Handle components as a dictionary
    if isinstance(new_comps_data, dict):
        new_refs = sorted(new_comps_data.keys())
    else:
        # Fallback for list format
        new_refs = sorted([c["ref"] for c in new_comps_data])
    if existing_refs != new_refs:
        return False

    existing_net_names = sorted([n.name for n in existing_circuit.nets])
    new_nets_data = new_data.get("nets", {})
    new_net_names = sorted(new_nets_data.keys())
    if existing_net_names != new_net_names:
        return False

    return True


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
