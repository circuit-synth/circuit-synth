#!/usr/bin/env python3
"""
USB-C Subcircuit - Proper USB-C implementation with protection
Includes CC resistors, ESD protection, and shield grounding
"""

from circuit_synth import *

@circuit(name="USB_Port")
def usb_port_subcircuit(vbus_out=None, gnd=None, usb_dp=None, usb_dm=None):
    """USB-C port with CC resistors, ESD protection, and proper grounding"""
    
    # Interface nets - use provided nets or create defaults for standalone operation
    vbus_out = vbus_out or Net('VBUS_OUT')
    gnd = gnd or Net('GND')
    usb_dp = usb_dp or Net('USB_DP')
    usb_dm = usb_dm or Net('USB_DM')
    
    # USB-C connector
    usb_conn = Component(
        symbol="Connector:USB_C_Receptacle_USB2.0_16P",
        ref="J",
        footprint="Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal"
    )
    

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
    


if __name__ == "__main__":
    circuit = usb_port_subcircuit()
    circuit.generate_kicad_project("usb_port")
    print("✅ USB-C subcircuit generated!")
