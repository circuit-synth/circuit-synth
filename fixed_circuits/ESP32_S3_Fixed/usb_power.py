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
    
    # ESD protection for USB data lines
    esd_protection = Component(
        symbol="Power_Protection:USBLC6-2P6",
        ref="D",
        footprint="Package_TO_SOT_SMD:SOT-23-6"
    )
    
    # VBUS protection fuse
    vbus_fuse = Component(
        symbol="Device:Fuse",
        ref="F",
        value="2A",
        footprint="Fuse:Fuse_1206_3216Metric"
    )
    
    # USB-C power connections
    usb_c["A4"] += vbus_fuse["1"]  # VBUS (A-side)
    usb_c["A9"] += vbus_fuse["1"]  # VBUS (A-side)
    usb_c["B4"] += vbus_fuse["1"]  # VBUS (B-side)  
    usb_c["B9"] += vbus_fuse["1"]  # VBUS (B-side)
    vbus_fuse["2"] += vbus
    usb_c["A1"] += gnd   # GND (A-side)
    usb_c["A12"] += gnd  # GND (A-side)
    usb_c["B1"] += gnd   # GND (B-side)
    usb_c["B12"] += gnd  # GND (B-side)
    
    # USB-C data connections through ESD protection
    usb_c["A6"] += esd_protection["I/O1"]  # D+ (A-side)
    usb_c["A7"] += esd_protection["I/O2"]  # D- (A-side)
    usb_c["B6"] += esd_protection["I/O1"]  # D+ (B-side)  
    usb_c["B7"] += esd_protection["I/O2"]  # D- (B-side)
    esd_protection["I/O1"] += usb_dp  # Protected D+ to output
    esd_protection["I/O2"] += usb_dm  # Protected D- to output
    esd_protection["VBUS"] += vbus    # ESD protection power
    esd_protection["GND"] += gnd      # ESD protection ground
    
    # CC pull-down resistors for power negotiation
    usb_c["A5"] += cc1_resistor["1"]  # CC1
    cc1_resistor["2"] += gnd
    usb_c["B5"] += cc2_resistor["1"]  # CC2
    cc2_resistor["2"] += gnd
    
    return vbus, gnd, usb_dp, usb_dm
