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
    c_ = Component(symbol="Device:C", ref="C?", value="C", footprint="Capacitor_SMD:C_0603_1608Metric")
    u_ = Component(symbol="RF_Module:ESP32-C6-MINI-1", ref="U?", value="ESP32-C6-MINI-1", footprint="RF_Module:ESP32-C6-MINI-1")

    # Connections
    c_[1] += _3v3
    u_[3] += _3v3
    c_[2] += gnd
    u_[1] += gnd
    u_[11] += gnd
    u_[14] += gnd
    u_[2] += gnd
    u_[36] += gnd
    u_[37] += gnd
    u_[38] += gnd
    u_[39] += gnd
    u_[40] += gnd
    u_[41] += gnd
    u_[42] += gnd
    u_[43] += gnd
    u_[44] += gnd
    u_[45] += gnd
    u_[46] += gnd
    u_[47] += gnd
    u_[48] += gnd
    u_[49] += gnd
    u_[50] += gnd
    u_[51] += gnd
    u_[52] += gnd
    u_[53] += gnd

# Generate the circuit
if __name__ == '__main__':
    circuit = main()
    # Generate KiCad netlist (required for ratsnest display)
    circuit.generate_kicad_netlist("initial_kicad_generated_generated/initial_kicad_generated_generated.net")
    circuit.generate_kicad_project(project_name="initial_kicad_generated_generated")