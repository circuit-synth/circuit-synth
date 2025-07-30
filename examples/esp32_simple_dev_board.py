#!/usr/bin/env python3
"""
Simple ESP32 Development Board

A minimal ESP32 development board for testing purposes.
"""

import sys
import os
import json

# Add the src directory to the path so we can import circuit_synth
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from circuit_synth import Circuit, Component, Net, circuit
from circuit_synth.kicad.unified_kicad_integration import create_unified_kicad_integration

@circuit(name="Simple_ESP32_Dev_Board")
def create_simple_esp32_dev_board():
    """
    Simple ESP32 Development Board
    
    Features:
    - ESP32 module
    - Basic power supply
    - Status LED
    - Reset button
    """
    
    # Define basic nets
    VCC_3V3 = Net('VCC_3V3')
    GND = Net('GND')
    
    # ===== ESP32 MODULE =====
    # Use ESP32 module instead of bare chip for simplicity
    esp32_module = Component(
        symbol="RF_Module:ESP32-WROOM-32",
        ref="U",
        footprint="RF_Module:ESP32-WROOM-32",
        value="ESP32-WROOM-32"
    )
    
    # Basic power connections - use pin numbers
    esp32_module[2] += VCC_3V3  # 3V3
    esp32_module[1] += GND      # GND
    esp32_module[15] += GND     # GND
    esp32_module[38] += GND     # GND
    
    # ===== POWER INPUT =====
    # Simple power input connector
    power_conn = Component(
        symbol="Connector:Conn_01x02_Pin",
        ref="J",
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
        value="POWER"
    )
    
    power_conn[1] += VCC_3V3
    power_conn[2] += GND
    
    # ===== STATUS LED =====
    led = Component(
        symbol="Device:LED",
        ref="D",
        footprint="LED_SMD:LED_0603_1608Metric",
        value="LED"
    )
    
    led_resistor = Component(
        symbol="Device:R",
        ref="R",
        footprint="Resistor_SMD:R_0603_1608Metric",
        value="470"
    )
    
    # Connect LED to GPIO2
    esp32_module[24] += led_resistor[1]  # GPIO2
    led_resistor[2] += led["A"]
    led["K"] += GND
    
    # ===== RESET BUTTON =====
    reset_button = Component(
        symbol="Switch:SW_Push",
        ref="SW",
        footprint="Button_Switch_SMD:SW_SPST_CK_RS282G05A3",
        value="RESET"
    )
    
    # Connect reset button
    esp32_module[3] += reset_button[1]  # EN pin
    reset_button[2] += GND

def main():
    """Generate the simple ESP32 development board."""
    print("Generating Simple ESP32 Development Board...")
    
    # Create the circuit
    circuit = create_simple_esp32_dev_board()
    
    # Define project parameters
    project_name = "Simple_ESP32_Dev_Board"
    output_dir = os.path.join(os.path.dirname(__file__), "..", "generated_projects", project_name)
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate netlists
    print("\n=== Text Netlist ===")
    text_netlist = circuit.to_netlist()
    print(text_netlist)
    
    # Save text netlist
    with open(os.path.join(output_dir, f"{project_name}.net"), 'w') as f:
        f.write(text_netlist)
    
    print("\n=== JSON Netlist ===")
    json_netlist = circuit.to_json()
    print(json_netlist)
    
    # Save JSON netlist
    with open(os.path.join(output_dir, f"{project_name}.json"), 'w') as f:
        f.write(json_netlist)
    
    # Generate KiCad project
    print(f"\n=== Generating KiCad Project in {output_dir} ===")
    try:
        # Create unified KiCad integration
        kicad_integration = create_unified_kicad_integration(
            output_dir=output_dir,
            project_name=project_name
        )
        
        # Convert circuit to circuit data format
        circuit_data = json.loads(circuit.to_json())
        
        # Generate schematic
        schematic_generator = kicad_integration.get_schematic_generator()
        result = schematic_generator.generate_from_circuit_data(circuit_data)
        
        print("KiCad project generated successfully!")
        print(f"Generated files in: {output_dir}")
        
    except Exception as e:
        print(f"Error generating KiCad project: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print(f"\nProject files saved to: {output_dir}")
    return 0

if __name__ == "__main__":
    sys.exit(main())