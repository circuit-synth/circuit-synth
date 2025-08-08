#!/usr/bin/env python3
"""
Simple circuit example that works immediately after pip install.

This example creates a basic voltage divider circuit and generates
KiCad project files. No directory setup or prerequisites required!

Usage:
    python simple_circuit.py
"""

from circuit_synth import circuit, Component, Net

@circuit(name="voltage_divider")
def create_voltage_divider():
    """Create a simple voltage divider circuit."""
    
    # Create components
    r1 = Component(
        symbol="Device:R",
        ref="R",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    r2 = Component(
        symbol="Device:R", 
        ref="R",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    # Create connectors for input/output
    input_conn = Component(
        symbol="Connector:Conn_01x02_Pin",
        ref="J",
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical"
    )
    
    output_conn = Component(
        symbol="Connector:Conn_01x02_Pin",
        ref="J",
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical"
    )
    
    # Create nets
    vin = Net("VIN")
    vout = Net("VOUT")
    gnd = Net("GND")
    
    # Connect components
    # Input connector
    input_conn[1] += vin
    input_conn[2] += gnd
    
    # Voltage divider
    r1[1] += vin
    r1[2] += vout
    r2[1] += vout
    r2[2] += gnd
    
    # Output connector
    output_conn[1] += vout
    output_conn[2] += gnd


if __name__ == "__main__":
    print("🚀 Circuit-Synth Simple Example")
    print("=" * 50)
    
    # Create the circuit
    print("📋 Creating voltage divider circuit...")
    circuit = create_voltage_divider()
    
    # Generate output files
    print("🔌 Generating KiCad project...")
    circuit.generate_kicad_project("voltage_divider")
    
    # Also generate standalone netlist for reference
    print("📝 Generating netlist...")
    circuit.generate_kicad_netlist("voltage_divider.net")
    
    # Generate JSON for debugging
    print("📊 Generating JSON representation...")
    circuit.generate_json_netlist("voltage_divider.json")
    
    print()
    print("✅ Success! Files generated:")
    print("   • voltage_divider/          - KiCad project directory")
    print("   • voltage_divider.net       - KiCad netlist")
    print("   • voltage_divider.json      - JSON representation")
    print()
    print("📖 Next steps:")
    print("   1. Open voltage_divider/voltage_divider.kicad_pro in KiCad")
    print("   2. View the schematic")
    print("   3. Open the PCB editor to see component placement")
    print()
    print("🎉 Example complete!")