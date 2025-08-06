#!/usr/bin/env python3
"""
resistor_divider subcircuit

Generated from KiCad schematic: resistor_divider.kicad_sch
Components: 2
Nets: 3
"""

from circuit_synth import *


@circuit
def resistor_divider(vin, gnd, mid, _3v3):
    """
    resistor_divider subcircuit from KiCad
    """

    # Create resistors with proper references and values
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="1k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="1k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # Connect resistors in voltage divider configuration
    r1["1"] += vin  # Connect R1 pin 1 to VIN
    r1["2"] += mid  # Connect R1 pin 2 to MID (voltage divider output)
    r2["1"] += mid  # Connect R2 pin 1 to MID
    r2["2"] += gnd  # Connect R2 pin 2 to GND
