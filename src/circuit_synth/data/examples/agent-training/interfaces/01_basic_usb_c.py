#!/usr/bin/env python3
"""
CIRCUIT: Basic USB-C Power Interface
PURPOSE: USB-C connector with proper power delivery and protection
COMPONENTS: USB-C receptacle + CC pulldown + ESD protection + decoupling
COMPLEXITY: Beginner
DOMAIN: Interface Design
"""

from circuit_synth import Circuit, Component, Net, circuit


@circuit
def basic_usb_c_power():
    """
    USB-C power interface with protection and proper termination.

    Design Notes:
    - USB-C receptacle supports USB 2.0 data + power delivery
    - 5.1K CC pulldown identifies device as USB 2.0 sink
    - ESD protection on VBUS prevents damage from electrostatic discharge
    - 10µF decoupling capacitor filters power supply noise
    - Series resistors on data lines provide signal integrity

    USB-C Pin Functions:
    - A1/B1: GND (ground reference)
    - A4/B4: VBUS (5V power input, up to 3A)
    - A5: CC1 (configuration channel 1)
    - A6/A7: D+/D- (USB 2.0 data lines)
    """
    # Create interface nets
    vbus_5v = Net("VBUS_5V")  # 5V power from USB-C
    gnd = Net("GND")  # Ground reference
    usb_dp = Net("USB_DP")  # USB Data Plus (host side)
    usb_dm = Net("USB_DM")  # USB Data Minus (host side)

    # Internal nets between connector and protection
    usb_dp_raw = Net("USB_DP_RAW")  # Data+ before series resistor
    usb_dm_raw = Net("USB_DM_RAW")  # Data- before series resistor
    cc1 = Net("CC1")  # Configuration Channel 1

    # USB-C receptacle - horizontal mount for PCB edge
    usb_connector = Component(
        symbol="Connector:USB_C_Receptacle_USB2.0",
        ref="J1",
        footprint="Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal",
    )

    # CC pulldown resistor - 5.1K identifies device as USB 2.0 sink
    # This tells the host we can accept 5V power delivery
    r_cc_pulldown = Component(
        symbol="Device:R",
        ref="R1",
        value="5.1K",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # VBUS ESD protection diode - protects against electrostatic discharge
    esd_vbus = Component(
        symbol="Diode:ESD5Z5.0T1G",  # 5V clamping voltage
        ref="D1",
        footprint="Diode_SMD:D_SOD-523",
    )

    # USB data line series resistors - 22Ω for signal integrity
    r_dp_series = Component(
        symbol="Device:R",
        ref="R2",
        value="22R",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    r_dm_series = Component(
        symbol="Device:R",
        ref="R3",
        value="22R",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # USB data line ESD protection
    esd_dp = Component(
        symbol="Diode:ESD5Zxx", ref="D2", footprint="Diode_SMD:D_SOD-523"
    )

    esd_dm = Component(
        symbol="Diode:ESD5Zxx", ref="D3", footprint="Diode_SMD:D_SOD-523"
    )

    # Power supply decoupling capacitor
    cap_vbus = Component(
        symbol="Device:C",
        ref="C1",
        value="10uF",
        footprint="Capacitor_SMD:C_0805_2012Metric",
    )

    # USB-C connector pin connections (A-side pins, B-side identical)
    usb_connector["A1"] += gnd  # Ground
    usb_connector["A4"] += vbus_5v  # VBUS power
    usb_connector["A5"] += cc1  # Configuration Channel 1
    usb_connector["A6"] += usb_dp_raw  # Data Plus (raw from connector)
    usb_connector["A7"] += usb_dm_raw  # Data Minus (raw from connector)

    # B-side pins (mirror A-side for reversible connection)
    usb_connector["B1"] += gnd  # Ground
    usb_connector["B4"] += vbus_5v  # VBUS power
    usb_connector["B6"] += usb_dp_raw  # Data Plus
    usb_connector["B7"] += usb_dm_raw  # Data Minus

    # CC pulldown resistor (identifies device as sink)
    r_cc_pulldown[1] += cc1  # Connect to CC1 pin
    r_cc_pulldown[2] += gnd  # Pulldown to ground

    # VBUS ESD protection
    esd_vbus[1] += vbus_5v  # Cathode to VBUS
    esd_vbus[2] += gnd  # Anode to ground

    # USB data series resistors (for signal integrity)
    r_dp_series[1] += usb_dp_raw  # Input from connector
    r_dp_series[2] += usb_dp  # Output to system

    r_dm_series[1] += usb_dm_raw  # Input from connector
    r_dm_series[2] += usb_dm  # Output to system

    # USB data ESD protection
    esd_dp[1] += usb_dp  # Protect filtered data line
    esd_dp[2] += gnd  # Clamp to ground

    esd_dm[1] += usb_dm  # Protect filtered data line
    esd_dm[2] += gnd  # Clamp to ground

    # Power supply decoupling
    cap_vbus[1] += vbus_5v  # Filter VBUS power
    cap_vbus[2] += gnd  # Reference to ground
