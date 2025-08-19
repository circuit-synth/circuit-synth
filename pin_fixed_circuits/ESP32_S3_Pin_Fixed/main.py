#!/usr/bin/env python3
"""
Main Circuit - ESP32-S3 Complete Development Board
Professional hierarchical circuit design with modular subcircuits

This is the main entry point that orchestrates all subcircuits:
- USB-C power input with proper CC resistors and protection
- 5V to 3.3V power regulation
- ESP32-S3 microcontroller with USB and debug interfaces  
- Debug header for programming and development
- Status LED with current limiting
"""

from circuit_synth import *

# Import all subcircuits
from usb_power import usb_power
from power_supply import power_supply  
from esp32_mcu import esp32_mcu
from debug_header import debug_header
from led_status import led_status

@circuit(name="ESP32_Complete_Board")
def main_circuit():
    """Main hierarchical circuit - ESP32-S3 complete development board"""
    
    # Create USB power input
    vbus, gnd, usb_dp, usb_dm = usb_power()
    
    # Create power supply (5V to 3.3V)
    vcc_3v3, gnd = power_supply(vbus, gnd)
    
    # Create ESP32 MCU with support circuits
    vcc_3v3, gnd, debug_tx, debug_rx, led_control = esp32_mcu(vcc_3v3, gnd, usb_dp, usb_dm)
    
    # Create debug interface
    debug_header(vcc_3v3, gnd, debug_tx, debug_rx)
    
    # Create status LED
    led_status(vcc_3v3, gnd, led_control)


if __name__ == "__main__":
    print("🚀 Starting ESP32 Complete Board generation...")
    
    circuit = main_circuit()
    
    print("🔌 Generating KiCad netlist...")
    circuit.generate_kicad_netlist("ESP32_Complete_Board.net")
    
    print("📄 Generating JSON netlist...")  
    circuit.generate_json_netlist("ESP32_Complete_Board.json")
    
    print("🏗️  Generating KiCad project...")
    circuit.generate_kicad_project(
        project_name="ESP32_Complete_Board",
        placement_algorithm="hierarchical",
        generate_pcb=True
    )
    
    print("✅ ESP32 Complete Board project generated!")
    print("📁 Check the ESP32_Complete_Board/ directory for KiCad files")
