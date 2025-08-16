#!/usr/bin/env python3
"""
USB-C Circuit - Professional USB-C implementation with ESD protection
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
    
    # USB decoupling capacitor
    cap_usb = Component(symbol="Device:C", ref="C", value="10uF",
                       footprint="Capacitor_SMD:C_0805_2012Metric")
    
    # USB-C connections
    usb_conn["VBUS"] += vbus_out
    usb_conn["GND"] += gnd
    usb_conn["SHIELD"] += gnd  # Ground the shield
    usb_conn["D+"] += usb_dp
    usb_conn["D-"] += usb_dm
    
    # CC resistors to ground
    usb_conn["CC1"] += cc1_resistor[1]
    cc1_resistor[2] += gnd
    usb_conn["CC2"] += cc2_resistor[1] 
    cc2_resistor[2] += gnd
    
    # ESD protection (connector side)
    esd_dp[1] += usb_dp
    esd_dp[2] += gnd
    esd_dm[1] += usb_dm
    esd_dm[2] += gnd
    
    # USB decoupling capacitor connections
    cap_usb[1] += vbus_out
    cap_usb[2] += gnd

