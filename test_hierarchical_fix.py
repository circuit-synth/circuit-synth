#!/usr/bin/env python3
"""
Test hierarchical circuit generation with fixed Rust backend.
"""

from circuit_synth import *
from pathlib import Path

# Define subcircuits
@circuit(name="USB_Port")
def usb_port(gnd, vbus, usb_dm, usb_dp):
    """USB Type-C port with ESD protection"""
    j1 = Component(
        symbol="Connector:USB_C_Receptacle_USB2.0",
        ref="J1",
        footprint="Connector_USB:USB_C_Receptacle_Amphenol_10103011-0001LF"
    )
    
    # Connections
    j1["GND"] += gnd
    j1["VBUS"] += vbus
    j1["D-"] += usb_dm
    j1["D+"] += usb_dp
    
    return None

@circuit(name="Power_Supply")
def power_supply(gnd, vbus, vcc_3v3):
    """3.3V LDO power supply"""
    u1 = Component(
        symbol="Regulator_Linear:AMS1117-3.3",
        ref="U1",
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2"
    )
    c2 = Component(
        symbol="Device:C",
        ref="C2",
        value="10uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    c3 = Component(
        symbol="Device:C",
        ref="C3",
        value="22uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    
    # Connections
    u1["VI"] += vbus
    u1["VO"] += vcc_3v3
    u1["GND"] += gnd
    c2[1] += vbus
    c2[2] += gnd
    c3[1] += vcc_3v3
    c3[2] += gnd
    
    return None

@circuit(name="Debug_Header")
def debug_header(gnd, vcc_3v3, debug_en, debug_tx, debug_rx, debug_io0):
    """Debug header for programming"""
    j2 = Component(
        symbol="Connector_Generic:Conn_02x03_Odd_Even",
        ref="J2",
        footprint="Connector_IDC:IDC-Header_2x03_P2.54mm_Vertical"
    )
    
    # Connections
    j2[1] += debug_en
    j2[2] += vcc_3v3
    j2[3] += debug_tx
    j2[4] += gnd
    j2[5] += debug_rx
    j2[6] += debug_io0
    
    return None

@circuit(name="LED_Blinker")
def led_blinker(gnd, led_control):
    """LED with current limiting resistor"""
    # Internal net
    n3 = Net("N$3")
    
    d3 = Component(
        symbol="Device:LED",
        ref="D3",
        footprint="LED_SMD:LED_0805_2012Metric"
    )
    r3 = Component(
        symbol="Device:R",
        ref="R3",
        value="330",
        footprint="Resistor_SMD:R_0805_2012Metric"
    )
    
    # Connections
    d3[1] += gnd
    d3[2] += n3
    r3[1] += led_control
    r3[2] += n3
    
    return None

@circuit(name="ESP32_C6_MCU")
def esp32_c6_mcu(gnd, vcc_3v3, usb_dm, usb_dp, debug_en, debug_tx, debug_rx, debug_io0, led_control):
    """ESP32-C6 microcontroller with nested subcircuits"""
    u2 = Component(
        symbol="RF_Module:ESP32-S3-MINI-1",
        ref="U2",
        footprint="RF_Module:ESP32-S3-MINI-1"
    )
    
    # Bypass capacitors
    c4 = Component(
        symbol="Device:C",
        ref="C4",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    
    # MCU connections
    u2["GND"] += gnd
    u2["3V3"] += vcc_3v3
    u2["IO19"] += usb_dm
    u2["IO20"] += usb_dp
    u2["EN"] += debug_en
    u2["TXD0"] += debug_tx
    u2["RXD0"] += debug_rx
    u2["IO0"] += debug_io0
    u2["IO8"] += led_control
    
    # Bypass cap
    c4[1] += vcc_3v3
    c4[2] += gnd
    
    # Add nested subcircuits
    debug = debug_header(gnd, vcc_3v3, debug_en, debug_tx, debug_rx, debug_io0)
    led = led_blinker(gnd, led_control)
    
    return None

@circuit(name="ESP32_C6_Dev_Board")
def main():
    """Main ESP32-C6 development board"""
    # Main nets
    gnd = Net("GND")
    vbus = Net("VBUS")
    vcc_3v3 = Net("VCC_3V3")
    usb_dm = Net("USB_DM")
    usb_dp = Net("USB_DP")
    debug_en = Net("DEBUG_EN")
    debug_tx = Net("DEBUG_TX")
    debug_rx = Net("DEBUG_RX")
    debug_io0 = Net("DEBUG_IO0")
    led_control = Net("LED_CONTROL")
    
    # Instantiate subcircuits
    usb = usb_port(gnd, vbus, usb_dm, usb_dp)
    power = power_supply(gnd, vbus, vcc_3v3)
    mcu = esp32_c6_mcu(gnd, vcc_3v3, usb_dm, usb_dp, debug_en, debug_tx, debug_rx, debug_io0, led_control)
    
    return None

# Generate the circuit
if __name__ == "__main__":
    import shutil
    
    # Clean previous output
    if Path("ESP32_C6_Dev_Board").exists():
        shutil.rmtree("ESP32_C6_Dev_Board")
    
    circuit = main()
    circuit.generate_kicad_project(project_name="ESP32_C6_Dev_Board")
    print("\n✅ Hierarchical circuit generation complete!")
    print("Generated files in ESP32_C6_Dev_Board/")