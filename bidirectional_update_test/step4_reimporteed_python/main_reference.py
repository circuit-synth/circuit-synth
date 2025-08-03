#!/usr/bin/env python3
"""
Circuit Generated from KiCad
"""

from circuit_synth import *

@circuit
def main():
    """Generated circuit from KiCad"""
    # Create nets
    _3v3 = Net('+3V3')
    gnd = Net('GND')

    # Create components
    c1 = Component(symbol="Device:C", ref="C1", value="C", footprint="Capacitor_SMD:C_0603_1608Metric")
    u1 = Component(symbol="RF_Module:ESP32-C6-MINI-1", ref="U1", value="ESP32-C6-MINI-1", footprint="RF_Module:ESP32-C6-MINI-1")

    # Connections
    c1[1] += _3v3
    u1[3] += _3v3
    c1[2] += gnd
    u1[1] += gnd
    u1[11] += gnd
    u1[14] += gnd
    u1[2] += gnd
    u1[36] += gnd
    u1[37] += gnd
    u1[38] += gnd
    u1[39] += gnd
    u1[40] += gnd
    u1[41] += gnd
    u1[42] += gnd
    u1[43] += gnd
    u1[44] += gnd
    u1[45] += gnd
    u1[46] += gnd
    u1[47] += gnd
    u1[48] += gnd
    u1[49] += gnd
    u1[50] += gnd
    u1[51] += gnd
    u1[52] += gnd
    u1[53] += gnd

# Generate the circuit
if __name__ == '__main__':
    circuit = main()
    # Generate KiCad netlist (required for ratsnest display)
    circuit.generate_kicad_netlist("initial_kicad_generated_generated/initial_kicad_generated_generated.net")
    circuit.generate_kicad_project(project_name="initial_kicad_generated_generated")