#!/usr/bin/env python3
"""
CIRCUIT: USB-C Powered ESP32-S3 System
PURPOSE: Complete system with USB-C power input, 3.3V regulation, and ESP32-S3
COMPONENTS: USB-C connector + 3.3V LDO + ESP32-S3 + protection + indicators
COMPLEXITY: Intermediate
DOMAIN: Complete System Design
"""

from circuit_synth import Circuit, Component, Net, circuit


@circuit
def usb_powered_esp32():
    """
    Complete USB-C powered ESP32-S3 system.

    System Architecture:
    USB-C Connector → 3.3V LDO Regulator → ESP32-S3 Module
         ↓                    ↓                 ↓
    ESD Protection    Input/Output Caps    Status LED + Reset

    Design Notes:
    - USB-C provides 5V power input with proper protection
    - 3.3V LDO regulator converts 5V to stable 3.3V for ESP32
    - ESP32-S3 configured for normal operation with status LED
    - All components use appropriate decoupling and protection
    """

    # System power nets
    usb_vbus_5v = Net("USB_VBUS_5V")  # 5V from USB-C connector
    regulated_3v3 = Net("VCC_3V3")  # Regulated 3.3V for system
    system_gnd = Net("GND")  # Common ground reference

    # USB data nets (for future expansion)
    usb_dp = Net("USB_DP")  # USB Data Plus
    usb_dm = Net("USB_DM")  # USB Data Minus
    usb_dp_raw = Net("USB_DP_RAW")  # Raw data from connector
    usb_dm_raw = Net("USB_DM_RAW")  # Raw data from connector

    # Control and status nets
    esp32_en = Net("ESP32_EN")  # ESP32 enable/reset
    esp32_io0 = Net("ESP32_IO0")  # ESP32 boot control
    esp32_io2 = Net("ESP32_IO2")  # ESP32 GPIO for LED
    cc1_net = Net("CC1")  # USB-C configuration channel

    # =================================================================
    # USB-C POWER INPUT SECTION
    # =================================================================

    # USB-C receptacle connector
    usb_connector = Component(
        symbol="Connector:USB_C_Receptacle_USB2.0",
        ref="J1",
        footprint="Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal",
    )

    # USB-C pin connections (A-side, B-side mirrors for reversibility)
    usb_connector["A1"] += system_gnd  # Ground
    usb_connector["A4"] += usb_vbus_5v  # VBUS power
    usb_connector["A5"] += cc1_net  # Configuration Channel 1
    usb_connector["A6"] += usb_dp_raw  # Data Plus
    usb_connector["A7"] += usb_dm_raw  # Data Minus
    usb_connector["B1"] += system_gnd  # Ground (B-side)
    usb_connector["B4"] += usb_vbus_5v  # VBUS power (B-side)
    usb_connector["B6"] += usb_dp_raw  # Data Plus (B-side)
    usb_connector["B7"] += usb_dm_raw  # Data Minus (B-side)

    # USB-C configuration: 5.1K CC pulldown (identifies as USB 2.0 sink)
    r_cc_pulldown = Component(
        symbol="Device:R",
        ref="R1",
        value="5.1K",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )
    r_cc_pulldown[1] += cc1_net
    r_cc_pulldown[2] += system_gnd

    # VBUS ESD protection
    esd_vbus = Component(
        symbol="Diode:ESD5Z5.0T1G", ref="D1", footprint="Diode_SMD:D_SOD-523"
    )
    esd_vbus[1] += usb_vbus_5v
    esd_vbus[2] += system_gnd

    # USB data line series resistors (22Ω for signal integrity)
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
    r_dp_series[1] += usb_dp_raw
    r_dp_series[2] += usb_dp
    r_dm_series[1] += usb_dm_raw
    r_dm_series[2] += usb_dm

    # USB data line ESD protection
    esd_dp = Component(
        symbol="Diode:ESD5Zxx", ref="D2", footprint="Diode_SMD:D_SOD-523"
    )
    esd_dm = Component(
        symbol="Diode:ESD5Zxx", ref="D3", footprint="Diode_SMD:D_SOD-523"
    )
    esd_dp[1] += usb_dp
    esd_dp[2] += system_gnd
    esd_dm[1] += usb_dm
    esd_dm[2] += system_gnd

    # USB power decoupling capacitor
    cap_usb = Component(
        symbol="Device:C",
        ref="C1",
        value="10uF",
        footprint="Capacitor_SMD:C_0805_2012Metric",
    )
    cap_usb[1] += usb_vbus_5v
    cap_usb[2] += system_gnd

    # =================================================================
    # 3.3V POWER REGULATION SECTION
    # =================================================================

    # 3.3V LDO regulator (5V → 3.3V conversion)
    regulator_3v3 = Component(
        symbol="Regulator_Linear:NCP1117-3.3_SOT223",
        ref="U1",
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2",
    )

    # LDO pin connections
    regulator_3v3[1] += system_gnd  # Pin 1: GND
    regulator_3v3[2] += regulated_3v3  # Pin 2: VOUT (3.3V)
    regulator_3v3[3] += usb_vbus_5v  # Pin 3: VIN (5V)

    # LDO input decoupling capacitor
    cap_reg_input = Component(
        symbol="Device:C",
        ref="C2",
        value="10uF",
        footprint="Capacitor_SMD:C_0805_2012Metric",
    )
    cap_reg_input[1] += usb_vbus_5v
    cap_reg_input[2] += system_gnd

    # LDO output decoupling capacitor
    cap_reg_output = Component(
        symbol="Device:C",
        ref="C3",
        value="22uF",
        footprint="Capacitor_SMD:C_0805_2012Metric",
    )
    cap_reg_output[1] += regulated_3v3
    cap_reg_output[2] += system_gnd

    # =================================================================
    # ESP32-S3 MICROCONTROLLER SECTION
    # =================================================================

    # ESP32-S3-MINI-1 module
    esp32 = Component(
        symbol="RF_Module:ESP32-S3-MINI-1",
        ref="U2",
        footprint="RF_Module:ESP32-S3-MINI-1",
    )

    # ESP32 power connections
    esp32[1] += system_gnd  # Pin 1: GND
    esp32[2] += regulated_3v3  # Pin 2: 3V3 power
    esp32[3] += esp32_en  # Pin 3: EN (enable/reset)
    esp32[41] += esp32_io0  # Pin 41: IO0 (boot mode)
    esp32[42] += esp32_io2  # Pin 42: IO2 (status LED)

    # ESP32 power decoupling
    cap_esp32 = Component(
        symbol="Device:C",
        ref="C4",
        value="10uF",
        footprint="Capacitor_SMD:C_0805_2012Metric",
    )
    cap_esp32[1] += regulated_3v3
    cap_esp32[2] += system_gnd

    # ESP32 EN pin pull-up (for normal operation)
    r_en_pullup = Component(
        symbol="Device:R",
        ref="R4",
        value="10K",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )
    r_en_pullup[1] += esp32_en
    r_en_pullup[2] += regulated_3v3

    # ESP32 IO0 pin pull-up (for normal boot mode)
    r_io0_pullup = Component(
        symbol="Device:R",
        ref="R5",
        value="10K",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )
    r_io0_pullup[1] += esp32_io0
    r_io0_pullup[2] += regulated_3v3

    # =================================================================
    # STATUS INDICATION SECTION
    # =================================================================

    # Status LED with current limiting resistor
    r_status_led = Component(
        symbol="Device:R",
        ref="R6",
        value="330R",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )
    led_status = Component(
        symbol="Device:LED",
        ref="D4",
        value="LED",
        footprint="LED_SMD:LED_0603_1608Metric",
    )

    # LED circuit connections
    r_status_led[1] += esp32_io2  # GPIO2 to current limiting resistor
    r_status_led[2] += led_status[1]  # Resistor to LED anode
    led_status[2] += system_gnd  # LED cathode to ground
