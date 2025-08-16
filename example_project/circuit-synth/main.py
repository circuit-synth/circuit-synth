#!/usr/bin/env python3
"""
Main Circuit - ESP32-C6 Development Board
Professional hierarchical circuit design with modular subcircuits

This is the main entry point that orchestrates all subcircuits:
- USB-C power input with proper CC resistors and protection
- 5V to 3.3V power regulation  
- ESP32-C6 microcontroller with USB and debug interfaces
- Status LED with current limiting
- Debug header for programming and development
"""

from circuit_synth import *

# Import all circuits
from usb import usb_port
from power_supply import power_supply
from esp32c6 import esp32c6

@circuit(name="ESP32_C6_Dev_Board_Main")
def main_circuit():
    """Main hierarchical circuit - ESP32-C6 development board"""
    
    # Create shared nets between subcircuits (ONLY nets - no components here)
    vbus = Net('VBUS')
    vcc_3v3 = Net('VCC_3V3')
    gnd = Net('GND')
    usb_dp = Net('USB_DP')
    usb_dm = Net('USB_DM')

    
    # Create all circuits with shared nets
    usb_port_circuit = usb_port(vbus, gnd, usb_dp, usb_dm)
    power_supply_circuit = power_supply(vbus, vcc_3v3, gnd)
    esp32_circuit = esp32c6(vcc_3v3, gnd, usb_dp, usb_dm)


if __name__ == "__main__":
    print("🚀 Starting ESP32-C6 development board generation...")
    
    # Generate the complete hierarchical circuit
    print("📋 Creating circuit...")
    circuit = main_circuit()
    
    # Generate KiCad netlist (required for ratsnest display)
    print("🔌 Generating KiCad netlist...")
    circuit.generate_kicad_netlist("ESP32_C6_Dev_Board.net")
    
    # Generate JSON netlist (for debugging and analysis)
    print("📄 Generating JSON netlist...")
    circuit.generate_json_netlist("ESP32_C6_Dev_Board.json")
    
    # Create KiCad project with hierarchical sheets
    print("🏗️  Generating KiCad project...")
    circuit.generate_kicad_project(
        project_name="ESP32_C6_Dev_Board",
        placement_algorithm="hierarchical",
        generate_pcb=True
    )
    
    print("")
    print("✅ ESP32-C6 Development Board project generated!")
    print("📁 Check the ESP32_C6_Dev_Board/ directory for KiCad files")
    print("")
    print("🏗️ Generated circuits:")
    print("   • USB-C port with CC resistors and ESD protection")
    print("   • 5V to 3.3V power regulation")
    print("   • ESP32-C6 microcontroller with support circuits")
    print("   • Debug header for programming")  
    print("   • Status LED with current limiting")
    print("")
    print("📋 Generated files:")
    print("   • ESP32_C6_Dev_Board.kicad_pro - KiCad project file")
    print("   • ESP32_C6_Dev_Board.kicad_sch - Hierarchical schematic")
    print("   • ESP32_C6_Dev_Board.kicad_pcb - PCB layout")
    print("   • ESP32_C6_Dev_Board.net - Netlist (enables ratsnest)")
    print("   • ESP32_C6_Dev_Board.json - JSON netlist (for analysis)")
    print("")
    print("🎯 Ready for professional PCB manufacturing!")
    print("💡 Open ESP32_C6_Dev_Board.kicad_pcb in KiCad to see the ratsnest!")
