#!/usr/bin/env python3
"""
main circuit with complex hierarchical structure

3-Level hierarchical circuit design:
  - main_circuit: System-level power and signal routing
  - resistor_divider: Voltage division + power conditioning (resistor_divider.kicad_sch)
  - capacitor_bank: Multi-stage filtering (capacitor_bank.kicad_sch)

This demonstrates deep hierarchical design patterns common in real circuits.
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
    Main circuit with 3-level hierarchical structure

    System-level circuit providing:
    - Power input (VIN: 5V or 3.3V)
    - Ground reference (GND)
    - Conditioned voltage output (MID: VIN/2)

    Delegates voltage division and filtering to resistor_divider subcircuit,
    which in turn uses capacitor_bank for power conditioning.
    """
    logger.info("Creating main circuit with deep hierarchical subcircuits")

    # Create system-level nets
    vin = Net("VIN")  # System power input (5V or 3.3V)
    gnd = Net("GND")  # System ground reference
    mid = Net("MID")  # Voltage divider output (VIN/2)

    # Instantiate the resistor divider subcircuit with power conditioning
    # This will internally instantiate the capacitor_bank for filtering
    resistor_divider_inst = resistor_divider(vin, gnd, mid)

    logger.info("Main circuit with 3-level hierarchy created")


if __name__ == "__main__":
    circuit = main_circuit()

    # Generate complete KiCad project with hierarchical structure
    circuit.generate_kicad_project(
        "complex_hierarchical_project", force_regenerate=True
    )

    # Also generate netlists for validation
    circuit.generate_kicad_netlist("complex_hierarchical.net")
    circuit.generate_json_netlist("complex_hierarchical.json")
