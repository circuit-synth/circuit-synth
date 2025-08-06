#!/usr/bin/env python3
"""
{project_name} - Circuit Design
Created with circuit-synth
"""

from circuit_synth import *


@circuit(name="{circuit_name}")
def main():
    """Main circuit - add your components here"""

    # Example: Create a simple LED circuit
    # led = Component(symbol="Device:LED", ref="D", footprint="LED_SMD:LED_0805_2012Metric")
    # resistor = Component(symbol="Device:R", ref="R", value="330", footprint="Resistor_SMD:R_0603_1608Metric")
    #
    # # Connect LED and resistor
    # gnd = Net("GND")
    # vcc = Net("VCC_3V3")
    # resistor[1] += vcc
    # resistor[2] += led["A"]
    # led["K"] += gnd

    pass


if __name__ == "__main__":
    circuit = main()
    circuit.generate_kicad_project(project_name="{circuit_name}")
