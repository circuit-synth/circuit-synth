"""
Helper utilities for Phase 0 integration tests.

These helpers create test circuits, validate JSON schemas, and perform
semantic comparisons for Phase 0 integration testing.
"""

import json
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from circuit_synth import Component, Net, circuit
from circuit_synth.core.circuit import Circuit


def create_simple_circuit() -> Circuit:
    """
    Create a simple voltage divider circuit for basic testing.

    Returns:
        Circuit: Simple circuit with 2 resistors and 3 nets
    """
    @circuit(name="voltage_divider")
    def voltage_divider():
        r1 = Component(
            "Device:R",
            ref="R1",
            value="10k",
            footprint="Resistor_SMD:R_0603_1608Metric",
        )
        r2 = Component(
            "Device:R",
            ref="R2",
            value="10k",
            footprint="Resistor_SMD:R_0603_1608Metric",
        )
        vin = Net("VIN")
        vout = Net("VOUT")
        gnd = Net("GND")

        r1[1] += vin
        r1[2] += vout
        r2[1] += vout
        r2[2] += gnd

        return r1, r2

    return voltage_divider()


def create_medium_circuit() -> Circuit:
    """
    Create a medium-complexity decoupling network for testing.

    Returns:
        Circuit: Circuit with MCU and decoupling capacitors (5+ components)
    """
    @circuit(name="decoupling_network")
    def decoupling_network():
        # MCU
        u1 = Component(
            "MCU_Module:Arduino_Nano",
            ref="U1",
            footprint="Module:Arduino_Nano",
        )

        # Decoupling capacitors
        c1 = Component(
            "Device:C",
            ref="C1",
            value="100nF",
            footprint="Capacitor_SMD:C_0603_1608Metric",
        )
        c2 = Component(
            "Device:C",
            ref="C2",
            value="10uF",
            footprint="Capacitor_SMD:C_0805_2012Metric",
        )
        c3 = Component(
            "Device:C",
            ref="C3",
            value="100nF",
            footprint="Capacitor_SMD:C_0603_1608Metric",
        )

        # Power resistor
        r1 = Component(
            "Device:R",
            ref="R1",
            value="10k",
            footprint="Resistor_SMD:R_0603_1608Metric",
        )

        # Nets
        vcc = Net("VCC_3V3")
        gnd = Net("GND")
        reset = Net("RESET")

        # Connections - VCC decoupling
        u1["VCC"] += vcc
        c1[1] += vcc
        c1[2] += gnd
        c2[1] += vcc
        c2[2] += gnd

        # Additional decoupling
        c3[1] += vcc
        c3[2] += gnd

        # Reset pull-up
        r1[1] += vcc
        r1[2] += reset
        u1["RESET"] += reset

        # Ground connections
        u1["GND"] += gnd

        return u1, c1, c2, c3, r1

    return decoupling_network()


def create_hierarchical_circuit() -> Circuit:
    """
    Create a hierarchical circuit with subcircuits for testing.

    Returns:
        Circuit: Main circuit with power supply and sensor subcircuits
    """
    # Power supply subcircuit
    @circuit(name="power_supply")
    def power_supply():
        u1 = Component(
            "Regulator_Linear:AMS1117-3.3",
            ref="U1",
            footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2",
        )
        c1 = Component(
            "Device:C",
            ref="C1",
            value="10uF",
            footprint="Capacitor_SMD:C_0805_2012Metric",
        )
        c2 = Component(
            "Device:C",
            ref="C2",
            value="22uF",
            footprint="Capacitor_SMD:C_0805_2012Metric",
        )

        vin = Net("VIN")
        vout = Net("VOUT")
        gnd = Net("GND")

        u1["VIN"] += vin
        u1["VOUT"] += vout
        u1["GND"] += gnd

        c1[1] += vin
        c1[2] += gnd

        c2[1] += vout
        c2[2] += gnd

        return u1, c1, c2

    # Main circuit
    @circuit(name="main_hierarchical")
    def main_hierarchical():
        # Use power supply subcircuit
        ps = power_supply()

        # Main circuit components
        r1 = Component(
            "Device:R",
            ref="R1",
            value="10k",
            footprint="Resistor_SMD:R_0603_1608Metric",
        )
        led1 = Component(
            "Device:LED",
            ref="LED1",
            footprint="LED_SMD:LED_0603_1608Metric",
        )

        vcc = Net("VCC_3V3")
        led_net = Net("LED")
        gnd = Net("GND")

        r1[1] += vcc
        r1[2] += led_net
        led1[1] += led_net
        led1[2] += gnd

        return ps, r1, led1

    return main_hierarchical()


def create_large_circuit(num_components: int = 100) -> Circuit:
    """
    Create a large circuit with many components for performance testing.

    Args:
        num_components: Number of components to create (default: 100)

    Returns:
        Circuit: Large circuit with specified number of components
    """
    @circuit(name=f"large_circuit_{num_components}")
    def large_circuit():
        components = []
        vcc = Net("VCC")
        gnd = Net("GND")

        # Create resistors
        num_resistors = num_components // 2
        for i in range(num_resistors):
            r = Component(
                "Device:R",
                ref=f"R{i+1}",
                value=f"{(i % 10 + 1) * 10}k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )
            # Connect to power rail
            r[1] += vcc
            r[2] += gnd
            components.append(r)

        # Create capacitors
        num_caps = num_components - num_resistors
        for i in range(num_caps):
            c = Component(
                "Device:C",
                ref=f"C{i+1}",
                value=f"{(i % 10 + 1) * 10}nF",
                footprint="Capacitor_SMD:C_0603_1608Metric",
            )
            # Connect to power rail
            c[1] += vcc
            c[2] += gnd
            components.append(c)

        return tuple(components)

    return large_circuit()


def validate_json_schema(json_path: Path) -> bool:
    """
    Validate that a JSON file matches the circuit-synth schema.

    Args:
        json_path: Path to JSON file to validate

    Returns:
        bool: True if JSON is valid, False otherwise
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Check required top-level fields
        required_fields = ["name", "components", "nets"]
        for field in required_fields:
            if field not in data:
                print(f"Missing required field: {field}")
                return False

        # Verify components is a dict (not list)
        if not isinstance(data["components"], dict):
            print("Components should be a dict, not a list")
            return False

        # Verify nets is a dict (not list)
        if not isinstance(data["nets"], dict):
            print("Nets should be a dict, not a list")
            return False

        # Validate component structure
        for ref, comp in data["components"].items():
            required_comp_fields = ["symbol", "ref"]
            for field in required_comp_fields:
                if field not in comp:
                    print(f"Component {ref} missing required field: {field}")
                    return False

        # Validate net structure
        for net_name, connections in data["nets"].items():
            if not isinstance(connections, list):
                print(f"Net {net_name} connections should be a list")
                return False

            for conn in connections:
                if "component" not in conn:
                    print(f"Net {net_name} connection missing 'component' field")
                    return False

        return True

    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}")
        return False
    except Exception as e:
        print(f"Validation error: {e}")
        return False


def compare_circuits_semantic(circuit1: Circuit, circuit2: Circuit) -> Tuple[bool, List[str]]:
    """
    Compare two circuits for semantic equivalence.

    This checks that the circuits have the same components, nets, and
    connections, even if the internal representation differs.

    Args:
        circuit1: First circuit to compare
        circuit2: Second circuit to compare

    Returns:
        Tuple of (is_equivalent: bool, differences: List[str])
    """
    differences = []

    # Compare component counts
    if len(circuit1.components) != len(circuit2.components):
        differences.append(
            f"Component count mismatch: "
            f"{len(circuit1.components)} vs {len(circuit2.components)}"
        )

    # Compare component references
    refs1 = {comp.reference for comp in circuit1.components}
    refs2 = {comp.reference for comp in circuit2.components}

    missing_refs = refs1 - refs2
    extra_refs = refs2 - refs1

    if missing_refs:
        differences.append(f"Missing component refs: {missing_refs}")
    if extra_refs:
        differences.append(f"Extra component refs: {extra_refs}")

    # Compare component properties for matching refs
    common_refs = refs1 & refs2
    for ref in common_refs:
        comp1 = next(c for c in circuit1.components if c.reference == ref)
        comp2 = next(c for c in circuit2.components if c.reference == ref)

        if comp1.value != comp2.value:
            differences.append(
                f"Component {ref} value mismatch: "
                f"{comp1.value} vs {comp2.value}"
            )

        if comp1.lib_id != comp2.lib_id:
            differences.append(
                f"Component {ref} lib_id mismatch: "
                f"{comp1.lib_id} vs {comp2.lib_id}"
            )

    # Compare net counts
    if len(circuit1.nets) != len(circuit2.nets):
        differences.append(
            f"Net count mismatch: "
            f"{len(circuit1.nets)} vs {len(circuit2.nets)}"
        )

    # Compare net names
    net_names1 = {net.name for net in circuit1.nets}
    net_names2 = {net.name for net in circuit2.nets}

    missing_nets = net_names1 - net_names2
    extra_nets = net_names2 - net_names1

    if missing_nets:
        differences.append(f"Missing nets: {missing_nets}")
    if extra_nets:
        differences.append(f"Extra nets: {extra_nets}")

    # Semantic equivalence check
    is_equivalent = len(differences) == 0

    return is_equivalent, differences


def measure_performance(func: Callable, *args, **kwargs) -> Tuple[Any, float]:
    """
    Measure the execution time of a function.

    Args:
        func: Function to measure
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function

    Returns:
        Tuple of (result, elapsed_time_seconds)
    """
    start_time = time.time()
    result = func(*args, **kwargs)
    elapsed_time = time.time() - start_time

    return result, elapsed_time


def load_json_netlist(json_path: Path) -> Dict[str, Any]:
    """
    Load and parse a JSON netlist file.

    Args:
        json_path: Path to JSON file

    Returns:
        Dict containing parsed JSON data

    Raises:
        FileNotFoundError: If JSON file doesn't exist
        json.JSONDecodeError: If JSON is malformed
    """
    if not json_path.exists():
        raise FileNotFoundError(f"JSON file not found: {json_path}")

    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def verify_json_path_in_result(result: Dict[str, Any]) -> bool:
    """
    Verify that a generation result contains a valid JSON path.

    Args:
        result: Result dict from generate_kicad_project()

    Returns:
        bool: True if JSON path is present and valid
    """
    if "json_path" not in result:
        print("Result missing 'json_path' field")
        return False

    json_path = Path(result["json_path"])

    if not json_path.exists():
        print(f"JSON path doesn't exist: {json_path}")
        return False

    if not json_path.is_file():
        print(f"JSON path is not a file: {json_path}")
        return False

    if json_path.suffix != ".json":
        print(f"JSON path doesn't have .json extension: {json_path}")
        return False

    return True


def extract_connectivity_graph(circuit: Circuit) -> Dict[str, set]:
    """
    Extract a connectivity graph from a circuit for semantic comparison.

    Args:
        circuit: Circuit to analyze

    Returns:
        Dict mapping net names to sets of (component_ref, pin) tuples
    """
    graph = {}

    for net in circuit.nets:
        connections = set()

        for conn in net.connections:
            if isinstance(conn, tuple) and len(conn) == 2:
                component_ref, pin = conn
                connections.add((component_ref, str(pin)))

        graph[net.name] = connections

    return graph
