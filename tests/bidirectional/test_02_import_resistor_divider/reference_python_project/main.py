#!/usr/bin/env python3
"""
main main circuit

Generated from KiCad project with hierarchical structure:
  - resistor_divider: 2 components (resistor_divider.kicad_sch)
  - main: 0 components (reference_resistor_divider.kicad_sch)
"""

import logging

from resistor_divider import resistor_divider

from circuit_synth import *

# Configure logging to reduce noise - only show warnings and errors
logging.basicConfig(level=logging.WARNING)

logger = logging.getLogger(__name__)


@circuit
def main_circuit():
    """
    Main circuit with hierarchical subcircuits
    """
    logger.info("Creating main circuit with subcircuits")

    # Create main nets
    gnd = Net("GND")
    mid = Net("MID")
    vin = Net("VIN")

    # Instantiate subcircuits
    resistor_divider_instance = resistor_divider(vin, gnd, mid, vin)


if __name__ == "__main__":
    circuit = main_circuit()

    # Generate KiCad project (following example pattern)
    circuit.generate_kicad_project("resistor_divider_project", force_regenerate=True)
