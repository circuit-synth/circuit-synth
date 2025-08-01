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

# Import all subcircuits
from usb_subcircuit import usb_port_subcircuit
from power_supply_subcircuit import power_supply_subcircuit
from debug_header_subcircuit import debug_header_subcircuit
from led_blinker_subcircuit import led_blinker_subcircuit

@circuit(name="ESP32_C6_Dev_Board_Main")
def main_circuit():
    """Main hierarchical circuit - ESP32-C6 development board"""
    
    # Create all subcircuits
    usb_port = usb_port_subcircuit()
    power_supply = power_supply_subcircuit()
    debug_header = debug_header_subcircuit()
    led_blinker = led_blinker_subcircuit()
    
    # Add ESP32-C6 MCU
    esp32_c6 = Component(
        symbol="RF_Module:ESP32-C6-MINI-1",
        ref="U", 
        footprint="RF_Module:ESP32-C6-MINI-1"
    )
    
    # Create shared nets between subcircuits
    vbus = Net('VBUS')
    vcc_3v3 = Net('VCC_3V3')
    gnd = Net('GND')
    usb_dp = Net('USB_DP')
    usb_dm = Net('USB_DM')
    
    # Debug signals
    debug_tx = Net('DEBUG_TX')
    debug_rx = Net('DEBUG_RX')
    debug_en = Net('DEBUG_EN')
    debug_io0 = Net('DEBUG_IO0')
    
    # LED control
    led_control = Net('LED_CONTROL')
    
    # Power connections to ESP32-C6
    esp32_c6["3V3"] += vcc_3v3
    esp32_c6["GND"] += gnd
    
    # USB connections to ESP32-C6
    esp32_c6["IO18"] += usb_dp  # USB D+
    esp32_c6["IO19"] += usb_dm  # USB D-
    
    # Debug connections
    esp32_c6["EN"] += debug_en    # Reset/Enable
    esp32_c6["TXD0"] += debug_tx  # UART TX
    esp32_c6["RXD0"] += debug_rx  # UART RX
    esp32_c6["IO0"] += debug_io0  # Boot mode control
    
    # LED control GPIO
    esp32_c6["IO8"] += led_control  # GPIO for LED control
    
    # ESP32-C6 decoupling capacitor
    cap_esp = Component(symbol="Device:C", ref="C", value="100nF",
                       footprint="Capacitor_SMD:C_0603_1608Metric")
    cap_esp[1] += vcc_3v3
    cap_esp[2] += gnd


if __name__ == "__main__":
    import os
    
    print("🚀 Starting ESP32-C6 development board generation...")
    
    # Generate the complete hierarchical circuit
    print("📋 Creating circuit...")
    circuit = main_circuit()
    
    # Create KiCad project with hierarchical sheets (this creates the directory)
    print("🏗️  Generating KiCad project...")
    circuit.generate_kicad_project(
        project_name="ESP32_C6_Dev_Board",
        placement_algorithm="hierarchical",
        generate_pcb=True
    )
    
    # Now generate netlist files into the KiCad project directory
    kicad_dir = "ESP32_C6_Dev_Board"  # Circuit-synth creates this directory
    
    # Generate KiCad netlist (required for ratsnest display) - save to KiCad project folder
    print("🔌 Generating KiCad netlist...")
    netlist_path = os.path.join(kicad_dir, "ESP32_C6_Dev_Board.net")
    circuit.generate_kicad_netlist(netlist_path)
    
    # Generate JSON netlist (for debugging and analysis) - save to KiCad project folder
    print("📄 Generating JSON netlist...")
    json_path = os.path.join(kicad_dir, "ESP32_C6_Dev_Board.json")
    circuit.generate_json_netlist(json_path)
    
    print("")
    print(f"✅ ESP32-C6 Development Board project generated!")
    print(f"📁 Files saved to: {kicad_dir}")
    print("")
    print("🏗️ Generated subcircuits:")
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
    print("💡 Open the .kicad_pro file in KiCad to see the ratsnest!")
