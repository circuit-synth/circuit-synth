#!/usr/bin/env python3
import logging
import os

from circuit_synth import *

# Configure logging so you see debug output in the console
logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


@circuit
def resistor_divider2():
    """
    A simple resistor divider to generate 3.3V from 5V.
    Uses two 10K resistors.
    """

    # Create main nets
    _5v = Net("5V")
    out = Net("out")
    GND = Net("GND")

    r1 = Component(
        symbol="Device:R",
        ref="R",
        value="4.7k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    r2 = Component(
        symbol="Device:R",
        ref="R",
        value="1k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    c1 = Component(
        symbol="Device:C",
        ref="C",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric",
    )
    r1["1"] += _5v
    r1["2"] += out
    r2["1"] += out
    r2["2"] += GND
    c1["1"] += out
    c1["2"] += GND


@circuit
def resistor_divider():
    """
    A simple resistor divider to generate 3.3V from 5V.
    Uses two 10K resistors.
    """

    # Create main nets
    _5v = Net("5V")
    out = Net("out")
    GND = Net("GND")

    r1 = Component(
        symbol="Device:R",
        ref="R",
        value="4.7k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    r2 = Component(
        symbol="Device:R",
        ref="R",
        value="1k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    c1 = Component(
        symbol="Device:C",
        ref="C",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric",
    )
    r1["1"] += _5v
    r1["2"] += out
    r2["1"] += out
    r2["2"] += GND
    c1["1"] += out
    c1["2"] += GND

    resistor_divider2()


if __name__ == "__main__":
    # Create the circuit instance
    c = resistor_divider()

    # Generate netlists (required before schematic generation)
    netlist_text = c.generate_text_netlist()
    print(netlist_text)

    # Generate JSON netlist with matching filename
    json_filename = "python_generated_reference_design.json"
    c.generate_json_netlist(json_filename)

    # Create output directory for KiCad project
    output_dir = "python_generated_reference_design"
    os.makedirs(output_dir, exist_ok=True)

    # Generate KiCad project with schematic
    project_name = "python_generated_reference_design"
    logger.info(f"Generating KiCad project in {output_dir}")
    logger.info(f"Using JSON file: {json_filename}")
    gen = SchematicGenerator(output_dir, project_name)
    gen.generate_project(json_filename)
    logger.info(f"KiCad project generated successfully in {output_dir}")
