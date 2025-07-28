import json
import logging
from pathlib import Path

from ..core.circuit import Circuit
from ..core.component import Component
from ..core.decorators import get_current_circuit, set_current_circuit
from ..core.exception import CircuitSynthError
from ..core.net import Net
from ..core.pin import Pin

logger = logging.getLogger(__name__)


def load_circuit_from_json_file(json_path) -> Circuit:
    """
    Reads JSON from the given file path, and returns a newly constructed
    Circuit object (with nested subcircuits) that matches the saved data.
    """
    json_path = Path(json_path)
    if not json_path.exists():
        raise FileNotFoundError(f"JSON file not found: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return load_circuit_from_dict(data)


def load_circuit_from_dict(data: dict, parent: Circuit = None) -> Circuit:
    """
    Reconstruct a Circuit from a dictionary produced by `Circuit.to_dict()`.
    """
    circuit_name = data.get("name", "UnnamedCircuit")
    circuit_desc = data.get("description", "")

    new_circ = Circuit(name=circuit_name, description=circuit_desc)
    logger.debug("load_circuit_from_dict: created circuit '%s'", circuit_name)

    # Link parent->child relationship so the new circuit knows its parent:
    if parent:
        new_circ._parent = parent

    old_circ = get_current_circuit()
    set_current_circuit(new_circ)
    try:
        # Create Net objects first
        net_map = {}
        nets_data = data.get("nets", {})
        for net_name in nets_data.keys():
            net_obj = Net(name=net_name)
            new_circ.add_net(net_obj)
            net_map[net_name] = net_obj
            logger.debug("  net created: '%s'", net_name)

        # Create Components
        components_data = data.get("components", {})
        component_map = {}

        # Handle both dictionary and list formats for components
        if isinstance(components_data, dict):
            # Dictionary format: {"C1": {...}, "R1": {...}}
            comp_items = components_data.items()
        else:
            # List format: [{"ref": "C1", ...}, {"ref": "R1", ...}]
            comp_items = [
                (comp.get("ref", "UNKNOWN"), comp) for comp in components_data
            ]

        for comp_ref, comp_info in comp_items:
            symbol = comp_info.get("symbol", "Device:???")
            # Handle empty symbols by providing a default based on component type
            if not symbol or symbol.strip() == "":
                # Try to infer symbol from component reference or description
                description = comp_info.get("description", "").lower()
                if comp_ref.startswith("R") or "resistor" in description:
                    symbol = "Device:R"
                elif comp_ref.startswith("C") or "capacitor" in description:
                    symbol = "Device:C"
                elif comp_ref.startswith("L") or "inductor" in description:
                    symbol = "Device:L"
                elif comp_ref.startswith("D") or "diode" in description:
                    symbol = "Device:D"
                else:
                    symbol = "Device:R"  # Default to resistor as it's most common
            ref = comp_info.get("reference", comp_info.get("ref", comp_ref))
            value = comp_info.get("value")
            footprint = comp_info.get("footprint")
            datasheet = comp_info.get("datasheet")
            descr = comp_info.get("description")

            comp_obj = Component(
                symbol=symbol,
                ref=ref,
                value=value,
                footprint=footprint,
                datasheet=datasheet,
                description=descr,
            )
            # Clear pins since they'll be loaded from JSON data
            comp_obj._pins = {}
            comp_obj._user_reference = ref

            pins_data = comp_info.get("pins", [])
            for pin_data in pins_data:
                pid = pin_data.get("pin_id", 0)
                pin_name = pin_data.get("name", "")
                pin_num = pin_data.get("num", "")
                pin_func = pin_data.get("func", "passive")
                pin_unit = pin_data.get("unit", 1)
                pin_x = pin_data.get("x", 0)
                pin_y = pin_data.get("y", 0)
                pin_len = pin_data.get("length", 0)
                pin_ori = pin_data.get("orientation", 0)

                new_pin = Pin(
                    name=pin_name,
                    num=pin_num,
                    func=pin_func,
                    unit=pin_unit,
                    x=pin_x,
                    y=pin_y,
                    length=pin_len,
                    orientation=pin_ori,
                )
                new_pin._component_pin_id = pid
                new_pin._component = comp_obj
                comp_obj._pins[pid] = new_pin

            new_circ.add_component(comp_obj)
            component_map[ref] = comp_obj
            logger.debug(
                "  component '%s' (symbol=%s) created with %d pins",
                ref,
                symbol,
                len(pins_data),
            )

        # Connect pins to nets
        for net_name, pin_connection_list in nets_data.items():
            net_obj = net_map[net_name]
            for pin_conn in pin_connection_list:
                comp_ref = pin_conn["component"]

                # Handle different pin reference formats
                if "pin_id" in pin_conn:
                    # Old format: direct pin_id
                    pin_id = pin_conn["pin_id"]
                elif "pin" in pin_conn and isinstance(pin_conn["pin"], dict):
                    # New format: pin object with number
                    pin_number = pin_conn["pin"].get("number", "")
                    pin_name = pin_conn["pin"].get("name", "")
                    pin_type = pin_conn["pin"].get("type", "passive")

                    # Create a pin if it doesn't exist
                    comp_obj = component_map.get(comp_ref)
                    if comp_obj is None:
                        raise ValueError(
                            f"JSON references unknown component '{comp_ref}'"
                        )

                    # Find or create pin by number
                    pin_obj = None
                    for existing_pin in comp_obj._pins.values():
                        if existing_pin.num == pin_number:
                            pin_obj = existing_pin
                            break

                    if pin_obj is None:
                        # Create new pin
                        pin_obj = Pin(
                            name=pin_name,
                            num=pin_number,
                            func=pin_type,
                            unit=1,
                            x=0,
                            y=0,
                            length=0,
                            orientation=0,
                        )
                        pin_obj._component = comp_obj
                        # Use pin number as key if no existing pins, otherwise use next available ID
                        pin_id = len(comp_obj._pins)
                        pin_obj._component_pin_id = pin_id
                        comp_obj._pins[pin_id] = pin_obj

                    pin_obj.connect_to_net(net_obj)
                    continue
                else:
                    raise ValueError(
                        f"Pin connection format not recognized: {pin_conn}"
                    )

                comp_obj = component_map.get(comp_ref)
                if comp_obj is None:
                    raise ValueError(f"JSON references unknown component '{comp_ref}'")

                pin_obj = comp_obj._pins.get(pin_id)
                if pin_obj is None:
                    raise ValueError(
                        f"Component '{comp_ref}' has no pin with pin_id={pin_id}"
                    )

                pin_obj.connect_to_net(net_obj)
                logger.debug(
                    "  connected %s pin_id=%s to net '%s'", comp_ref, pin_id, net_name
                )

        # Recursively load subcircuits
        for child_data in data.get("subcircuits", []):
            child_circ = load_circuit_from_dict(child_data, parent=new_circ)
            new_circ.add_subcircuit(child_circ)

        # Note: Removed duplicate detection loading as it depends on private modules
        # This functionality can be added back if needed with proper interfaces

    finally:
        set_current_circuit(old_circ)

    return new_circ
