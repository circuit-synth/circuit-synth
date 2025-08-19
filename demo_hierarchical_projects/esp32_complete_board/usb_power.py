#!/usr/bin/env python3
"""
USB Power Input Circuit
USB-C connector with CC resistors for power negotiation
"""

from circuit_synth import *

@circuit(name="USB_Power_Input")
def usb_power():
    """USB-C power input subcircuit"""
    
    # Create output nets
    vbus = Net('VBUS')
    gnd = Net('GND')
    usb_dp = Net('USB_DP')
    usb_dm = Net('USB_DM')
    
    # USB-C connector
    usb_c = Component(
        symbol="Connector:USB_C_Receptacle_USB2.0_16P",
        ref="J",
        footprint="Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12"
    )
    
    # CC pull-down resistors (5.1k for default USB power)
    cc1_resistor = Component(
        symbol="Device:R",
        ref="R",
        value="5.1k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    cc2_resistor = Component(
        symbol="Device:R", 
        ref="R",
        value="5.1k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    # VBUS protection fuse
    vbus_fuse = Component(
        symbol="Device:Fuse",
        ref="F",
        value="2A",
        footprint="Fuse:Fuse_1206_3216Metric"
    )
    
    # USB-C connections
    usb_c["VBUS"] += vbus_fuse["1"]
    vbus_fuse["2"] += vbus
    usb_c["GND"] += gnd
    usb_c["D+"] += usb_dp
    usb_c["D-"] += usb_dm
    
    # CC resistors
    usb_c["CC1"] += cc1_resistor["1"]
    cc1_resistor["2"] += gnd
    usb_c["CC2"] += cc2_resistor["1"] 
    cc2_resistor["2"] += gnd
    
    return vbus, gnd, usb_dp, usb_dm
