#!/usr/bin/env python3
"""
Step 5: Test KiCad Preservation During Python Regeneration

This Python file (from Step 4) will regenerate KiCad files back into Step 3's directory.
The test verifies that manual component positions from Step 3 are preserved
and not overwritten by circuit-synth generation.

Expected behavior:
- Circuit topology should be updated if needed
- Component positions should remain where manually placed in Step 3
- No loss of user's manual KiCad work
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
    # Step 5: Test KiCad preservation using UPDATE MODE
    # force_regenerate=False should trigger update mode that preserves manual work
    print("🔄 Testing KiCad update mode (should preserve manual component positions)")
    circuit.generate_kicad_project(
        project_name="initial_kicad_generated", 
        force_regenerate=False  # This should trigger update mode!
    )