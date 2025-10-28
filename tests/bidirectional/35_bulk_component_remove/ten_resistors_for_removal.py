#!/usr/bin/env python3
"""Ten resistor circuit - starting point for test 35 (bulk component removal)"""

from circuit_synth import *


@circuit(name="ten_resistors_for_removal")
def ten_resistors_for_removal():
    """Circuit with ten resistors for testing bulk component deletion"""

    # Create 10 resistors with different values
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="4.7k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    r3 = Component(
        symbol="Device:R",
        ref="R3",
        value="2.2k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    r4 = Component(
        symbol="Device:R",
        ref="R4",
        value="1k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    r5 = Component(
        symbol="Device:R",
        ref="R5",
        value="100",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    r6 = Component(
        symbol="Device:R",
        ref="R6",
        value="220",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    r7 = Component(
        symbol="Device:R",
        ref="R7",
        value="470",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    r8 = Component(
        symbol="Device:R",
        ref="R8",
        value="680",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    r9 = Component(
        symbol="Device:R",
        ref="R9",
        value="1.5k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    r10 = Component(
        symbol="Device:R",
        ref="R10",
        value="3.3k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )


# Generate the circuit
if __name__ == "__main__":
    circuit = ten_resistors_for_removal()
    # Generate KiCad project (creates directory)
    circuit.generate_kicad_project(project_name="ten_resistors_for_removal")
    # Generate KiCad netlist (required for ratsnest display)
    circuit.generate_kicad_netlist("ten_resistors_for_removal/ten_resistors_for_removal.net")
