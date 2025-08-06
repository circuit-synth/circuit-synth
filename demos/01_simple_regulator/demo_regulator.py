#!/usr/bin/env python3
"""
Simple 3.3V Linear Regulator Circuit

This demonstrates the most basic circuit-synth workflow:
1. Write Python circuit code
2. Generate KiCad project files
3. Open in KiCad for PCB layout

Components: AMS1117-3.3 regulator + input/output capacitors
Input: 5V, Output: 3.3V @ 1A max

Run: python demo_regulator.py
"""

from circuit_synth import *

@circuit(name="Linear_Regulator")
def voltage_regulator():
    """3.3V linear regulator with input/output filtering"""
    
    # Power regulator - AMS1117-3.3 in SOT-223 package
    regulator = Component(
        symbol="Regulator_Linear:AMS1117-3.3",
        ref="U",
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2"
    )
    
    # Input filter capacitor - 10uF ceramic
    cap_in = Component(
        symbol="Device:C",
        ref="C",
        value="10uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    
    # Output filter capacitor - 22uF ceramic  
    cap_out = Component(
        symbol="Device:C", 
        ref="C",
        value="22uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    
    # Power input connector
    power_in = Component(
        symbol="Connector:Screw_Terminal_01x02",
        ref="J",
        footprint="TerminalBlock:TerminalBlock_bornier-2_P5.08mm"
    )
    
    # Regulated output connector
    power_out = Component(
        symbol="Connector:Screw_Terminal_01x02", 
        ref="J",
        footprint="TerminalBlock:TerminalBlock_bornier-2_P5.08mm"
    )
    
    # Create power nets
    vin = Net('VIN_5V')
    vout = Net('VOUT_3V3')
    gnd = Net('GND')
    
    # Connect regulator
    regulator["VI"] += vin     # Input pin
    regulator["VO"] += vout    # Output pin  
    regulator["GND"] += gnd    # Ground pin
    
    # Connect input capacitor
    cap_in[1] += vin
    cap_in[2] += gnd
    
    # Connect output capacitor
    cap_out[1] += vout
    cap_out[2] += gnd
    
    # Connect input terminal
    power_in[1] += vin
    power_in[2] += gnd
    
    # Connect output terminal
    power_out[1] += vout
    power_out[2] += gnd

if __name__ == "__main__":
    print("=== Circuit-Synth Demo: 3.3V Linear Regulator ===")
    print()
    print("Generating circuit...")
    
    # Create the circuit
    circuit = voltage_regulator()
    
    print("Creating KiCad project...")
    
    # Generate complete KiCad project
    circuit.generate_kicad_project(
        project_name="Linear_Regulator_Demo",
        generate_pcb=True,
        placement_algorithm="spiral"
    )
    
    print()
    print("✅ Demo complete! Generated files:")
    print("   • Linear_Regulator_Demo.kicad_pro")
    print("   • Linear_Regulator_Demo.kicad_sch") 
    print("   • Linear_Regulator_Demo.kicad_pcb")
    print("   • Linear_Regulator_Demo.net")
    print()
    print("📂 Open Linear_Regulator_Demo.kicad_pro in KiCad to see the schematic!")
    print("💡 The PCB will show component placements and ratsnest connections.")
    print()
    print("Circuit specifications:")
    print("   • Input: 5V DC")
    print("   • Output: 3.3V @ 1A max")  
    print("   • Dropout: 1.2V typical")
    print("   • Components: 5 total (regulator + caps + connectors)")