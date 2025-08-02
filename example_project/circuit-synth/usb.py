#!/usr/bin/env python3
"""
USB-C Circuit - Proper USB-C implementation with protection
Includes CC resistors, ESD protection, and shield grounding
"""

from circuit_synth import *

@circuit(name="USB_Port")
def usb_port(vbus_out, gnd, usb_dp, usb_dm):
    """USB-C port with CC resistors, ESD protection, and proper grounding"""
    
    # USB-C connector
    usb_conn = Component(
        symbol="Connector:USB_C_Receptacle_USB2.0_16P",
        ref="J",
        footprint="Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal"
    )
    
    # CC pull-down resistors (5.1k for UFP device)
    cc1_resistor = Component(symbol="Device:R", ref="R", value="5.1k",
                            footprint="Resistor_SMD:R_0603_1608Metric")
    cc2_resistor = Component(symbol="Device:R", ref="R", value="5.1k", 
                            footprint="Resistor_SMD:R_0603_1608Metric")
    
    # ESD protection diodes for data lines
    esd_dp = Component(symbol="Diode:ESD5Zxx", ref="D",
                      footprint="Diode_SMD:D_SOD-523")
    esd_dm = Component(symbol="Diode:ESD5Zxx", ref="D",
                      footprint="Diode_SMD:D_SOD-523")
    
    # USB-C connections - explicitly connect both pins of each differential pair using pin numbers
    # VBUS pins (A4, A9, B4, B9) - connect together
    usb_conn["A4"] += vbus_out  # VBUS
    usb_conn["A9"] += vbus_out  # VBUS
    usb_conn["B4"] += vbus_out  # VBUS
    usb_conn["B9"] += vbus_out  # VBUS
    
    # GND pins (A1, A12, B1, B12) - connect together
    usb_conn["A1"] += gnd   # GND
    usb_conn["A12"] += gnd  # GND
    usb_conn["B1"] += gnd   # GND
    usb_conn["B12"] += gnd  # GND
    
    # Shield connection
    usb_conn["S1"] += gnd  # Ground the shield
    
    # D+ differential pair - connect both pins (A6, B6) to same net for cable flipping support
    usb_conn["A6"] += usb_dp  # D+ pin A6
    usb_conn["B6"] += usb_dp  # D+ pin B6
    
    # D- differential pair - connect both pins (A7, B7) to same net for cable flipping support
    usb_conn["A7"] += usb_dm  # D- pin A7
    usb_conn["B7"] += usb_dm  # D- pin B7
    
    # CC resistors to ground
    usb_conn["CC1"] += cc1_resistor[1]
    cc1_resistor[2] += gnd
    usb_conn["CC2"] += cc2_resistor[1] 
    cc2_resistor[2] += gnd
    
    # ESD protection
    esd_dp[1] += usb_dp
    esd_dp[2] += gnd
    esd_dm[1] += usb_dm
    esd_dm[2] += gnd
    
    # USB decoupling capacitor
    cap_usb = Component(symbol="Device:C", ref="C", value="10uF",
                       footprint="Capacitor_SMD:C_0805_2012Metric")
    cap_usb[1] += vbus_out
    cap_usb[2] += gnd

@circuit(name="USB_Test_Circuit")
def usb_test_circuit():
    """Top-level test circuit for USB port"""
    # Create hierarchical labels for the USB interface
    vbus_out = Net("VBUS_OUT")
    gnd = Net("GND")
    usb_dp = Net("USB_DP")
    usb_dm = Net("USB_DM")
    
    # Instantiate the USB port
    usb_port(vbus_out, gnd, usb_dp, usb_dm)

if __name__ == "__main__":
    circuit = usb_test_circuit()
    circuit.generate_kicad_project("usb_port")
    print("✅ USB-C circuit generated!")
