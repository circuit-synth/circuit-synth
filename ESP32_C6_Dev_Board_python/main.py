#!/usr/bin/env python3
"""
Main circuit generated from KiCad
"""

from circuit_synth import *

# Import subcircuit functions
from USB_Port import USB_Port
from Power_Supply import Power_Supply
from ESP32_C6_MCU import ESP32_C6_MCU

@circuit(name='main')
def main():
    """
    Main circuit with hierarchical subcircuits
    """
    # Main circuit nets
    gnd = Net('GND')
    vbus = Net('VBUS')
    vcc_3v3 = Net('VCC_3V3')
    usb_dm = Net('USB_DM')
    usb_dp = Net('USB_DP')


    # Instantiate top-level subcircuits
    usb_port_circuit = usb_port(gnd, vbus, usb_dm, usb_dp)
    power_supply_circuit = power_supply(gnd, vbus, vcc_3v3)
    esp32_c6_mcu_circuit = esp32_c6_mcu(gnd, vcc_3v3, usb_dm, usb_dp)


# Generate the circuit
if __name__ == '__main__':
    circuit = main()
    # Generate KiCad netlist (required for ratsnest display)
    circuit.generate_kicad_netlist("ESP32_C6_Dev_Board_generated/ESP32_C6_Dev_Board_generated.net")
    circuit.generate_kicad_project(project_name="ESP32_C6_Dev_Board_generated")