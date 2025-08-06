#!/usr/bin/env python3
"""
USB_Port subcircuit generated from KiCad
"""

from circuit_synth import *


@circuit(name="USB_Port")
def usb_port(gnd, vbus, usb_dm, usb_dp):
    """
    USB_Port subcircuit
    Parameters: GND, VBUS, USB_DM, USB_DP
    """
    # Create local nets
    n_1 = Net("N$1")
    n_2 = Net("N$2")

    # Create components
    c1 = Component(
        symbol="Device:C",
        ref="C1",
        value="10uF",
        footprint="Capacitor_SMD:C_0805_2012Metric",
    )
    d1 = Component(
        symbol="Diode:ESD5Zxx", ref="D1", value="~", footprint="Diode_SMD:D_SOD-523"
    )
    d2 = Component(
        symbol="Diode:ESD5Zxx", ref="D2", value="~", footprint="Diode_SMD:D_SOD-523"
    )
    j1 = Component(
        symbol="Connector:USB_C_Receptacle_USB2.0_16P",
        ref="J1",
        value="~",
        footprint="Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal",
    )
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="5.1k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )
    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="5.1k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # Connections
    c1[2] += gnd
    d1[2] += gnd
    d2[2] += gnd
    j1["A1"] += gnd
    j1["A12"] += gnd
    j1["B1"] += gnd
    j1["B12"] += gnd
    j1["S1"] += gnd
    r1[2] += gnd
    r2[2] += gnd
    j1["A5"] += n_1
    r1[1] += n_1
    j1["B5"] += n_2
    r2[1] += n_2
    d2[1] += usb_dm
    j1["A7"] += usb_dm
    d1[1] += usb_dp
    j1["A6"] += usb_dp
    c1[1] += vbus
    j1["A4"] += vbus
    j1["A9"] += vbus
    j1["B4"] += vbus
    j1["B9"] += vbus
