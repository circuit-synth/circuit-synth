#!/usr/bin/env python3
import logging
import os

from circuit_synth import *

# Configure logging so you see debug output in the console
logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)


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


if __name__ == "__main__":
    # Create the circuit instance
    c = resistor_divider()

    # Generate KiCad project directly (no intermediate files needed)
    c.generate_kicad_project(
        "python_generated_design",
        force_regenerate=False,
        draw_bounding_boxes=True,
    )

    # Generate KiCad netlist file
    logger.info("Generating KiCad netlist...")
    netlist_path = os.path.join(
        "python_generated_design", "python_generated_design.net"
    )
    c.generate_kicad_netlist(netlist_path)
    logger.info(f"KiCad netlist generated: {netlist_path}")
