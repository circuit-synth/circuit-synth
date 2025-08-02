#!/usr/bin/env python3
"""
Main Circuit - ESP32_C6_Dev_Board
Hierarchical circuit design with modular subcircuits

This is the main entry point that orchestrates all subcircuits.
Converted from KiCad hierarchical design.
"""

from circuit_synth import *

# Import all subcircuits
from usb_port import usb_port
from power_supply import power_supply
from esp32_c6_mcu import esp32_c6_mcu

@circuit(name="ESP32_C6_Dev_Board_Main")
def main_circuit():
    """Main hierarchical circuit - ESP32_C6_Dev_Board"""
    
    # Create shared nets between subcircuits (ONLY nets - no components here)
    vbus = Net('VBUS')
    vcc_3v3 = Net('VCC_3V3')
    gnd = Net('GND')
    usb_dp = Net('USB_DP')
    usb_dm = Net('USB_DM')

    
    # Create all circuits with shared nets
    usb_port_circuit = usb_port(vbus, gnd, usb_dp, usb_dm)
    power_supply_circuit = power_supply(vbus, vcc_3v3, gnd)
    esp32_circuit = esp32_c6_mcu(vcc_3v3, gnd, usb_dp, usb_dm)


if __name__ == "__main__":
    print("🚀 Generating KiCad project from circuit-synth...")
    circuit = main_circuit()
    
    # Generate KiCad project
    circuit.generate_kicad_project(
        project_name="ESP32_C6_Dev_Board",
        placement_algorithm="hierarchical",
        generate_pcb=True
    )
    
    print("✅ KiCad project generated successfully!")
    print("📁 Check the generated KiCad files for your circuit")
