#!/usr/bin/env python3
"""
08_reference: Microcontroller circuit (ESP32 + power + USB)

This design demonstrates a more complex real-world circuit with
an ESP32 microcontroller and supporting components in hierarchical sheets.
"""

from circuit_synth import *
from power_section import power_circuit
from mcu_section import mcu_circuit

@circuit(name="08_reference")
def main_circuit():
    """Main circuit with ESP32 and power management"""
    
    # Create global nets
    VCC_5V = Net('VCC_5V')
    VCC_3V3 = Net('VCC_3V3')
    GND = Net('GND')
    USB_DP = Net('USB_DP')
    USB_DM = Net('USB_DM')
    
    # Instantiate power and MCU subcircuits
    power_sub = power_circuit(VCC_5V, VCC_3V3, GND)
    mcu_sub = mcu_circuit(VCC_3V3, GND, USB_DP, USB_DM)


if __name__ == "__main__":
    print("🚀 Starting 08_reference generation...")
    
    # Generate the complete hierarchical circuit
    circuit = main_circuit()
    
    # Generate KiCad project
    circuit.generate_kicad_project(project_name="08_reference")
    
    print("✅ 08_reference project generated!")