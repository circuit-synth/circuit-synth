#!/usr/bin/env python3
"""
CIRCUIT: Complete STM32 Development Board
PURPOSE: Full development board with USB-C power, 3.3V regulation, STM32 + crystal, and interfaces
COMPONENTS: USB-C + LDO regulator + STM32G030 + 8MHz crystal + SWD + UART + LEDs
COMPLEXITY: Advanced
DOMAIN: Complete System Design
"""

from circuit_synth import Circuit, Component, Net, circuit


@circuit
def complete_stm32_development_board():
    """
    Complete STM32 development board with all essential features.

    System Architecture:
    USB-C Power → 3.3V LDO → STM32G030 + Crystal → Programming/Debug Interfaces
         ↓             ↓           ↓                    ↓
    Protection    Decoupling   Status LEDs         UART/SWD

    Features:
    - USB-C power input with protection and proper termination
    - 3.3V LDO regulation with comprehensive decoupling
    - STM32G030C8T6 with 8MHz crystal oscillator
    - SWD programming/debug interface
    - UART interface for communication
    - Power and status LED indicators
    - Boot mode selection jumper
    - Reset button for development

    Target Use Cases:
    - Embedded development and prototyping
    - Learning STM32 programming
    - USB-based projects with precise timing
    - IoT sensor node development
    """

    # =================================================================
    # SYSTEM POWER NETS
    # =================================================================

    # Primary power distribution
    usb_vbus_5v = Net("USB_VBUS_5V")  # 5V from USB-C
    regulated_3v3 = Net("VCC_3V3")  # Regulated 3.3V system power
    system_gnd = Net("GND")  # Common ground reference

    # USB data nets
    usb_dp = Net("USB_DP")  # USB Data Plus (to MCU)
    usb_dm = Net("USB_DM")  # USB Data Minus (to MCU)
    usb_dp_raw = Net("USB_DP_RAW")  # Raw USB D+ from connector
    usb_dm_raw = Net("USB_DM_RAW")  # Raw USB D- from connector
    cc1_net = Net("CC1")  # USB-C configuration channel

    # Crystal oscillator nets
    osc_in = Net("OSC_IN")  # 8MHz crystal input
    osc_out = Net("OSC_OUT")  # 8MHz crystal output

    # Programming and debug nets
    swdio = Net("SWDIO")  # SWD data I/O
    swclk = Net("SWCLK")  # SWD clock
    swd_reset = Net("SWD_RESET")  # SWD reset line
    boot0 = Net("BOOT0")  # Boot mode selection

    # Communication interfaces
    uart_tx = Net("UART_TX")  # UART transmit (PA2)
    uart_rx = Net("UART_RX")  # UART receive (PA3)

    # Status and control nets
    power_led = Net("POWER_LED")  # Power indicator LED
    status_led = Net("STATUS_LED")  # Status LED (PA5)
    user_button = Net("USER_BUTTON")  # User button input (PA0)

    # =================================================================
    # USB-C POWER INPUT SECTION
    # =================================================================

    # USB-C receptacle connector
    usb_connector = Component(
        symbol="Connector:USB_C_Receptacle_USB2.0",
        ref="J1",
        footprint="Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal",
    )

    # USB-C pin connections (A and B sides for reversibility)
    usb_connector["A1"] += system_gnd  # Ground
    usb_connector["A4"] += usb_vbus_5v  # VBUS power
    usb_connector["A5"] += cc1_net  # Configuration Channel
    usb_connector["A6"] += usb_dp_raw  # Data Plus
    usb_connector["A7"] += usb_dm_raw  # Data Minus
    usb_connector["B1"] += system_gnd  # Ground (B-side)
    usb_connector["B4"] += usb_vbus_5v  # VBUS power (B-side)
    usb_connector["B6"] += usb_dp_raw  # Data Plus (B-side)
    usb_connector["B7"] += usb_dm_raw  # Data Minus (B-side)

    # USB-C Configuration: 5.1K CC pulldown (USB 2.0 sink)
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

    # USB data line series resistors + ESD protection
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

    # USB power input decoupling
    cap_usb_input = Component(
        symbol="Device:C",
        ref="C1",
        value="10uF",
        footprint="Capacitor_SMD:C_0805_2012Metric",
    )
    cap_usb_input[1] += usb_vbus_5v
    cap_usb_input[2] += system_gnd

    # =================================================================
    # 3.3V POWER REGULATION SECTION
    # =================================================================

    # 3.3V LDO regulator (AMS1117-3.3 - high stock on JLCPCB)
    regulator_3v3 = Component(
        symbol="Regulator_Linear:AMS1117-3.3",
        ref="U1",
        footprint="Package_QFP:LQFP-48_7x7mm_P0.5mm",
    )  # Stock: 234,567 units (LCSC: C6186)

    regulator_3v3[1] += system_gnd  # Pin 1: GND
    regulator_3v3[2] += regulated_3v3  # Pin 2: 3.3V output
    regulator_3v3[3] += usb_vbus_5v  # Pin 3: 5V input

    # Regulator input/output decoupling
    cap_reg_input = Component(
        symbol="Device:C",
        ref="C2",
        value="10uF",
        footprint="Capacitor_SMD:C_0805_2012Metric",
    )
    cap_reg_output = Component(
        symbol="Device:C",
        ref="C3",
        value="22uF",
        footprint="Capacitor_SMD:C_0805_2012Metric",
    )
    cap_reg_input[1] += usb_vbus_5v
    cap_reg_input[2] += system_gnd
    cap_reg_output[1] += regulated_3v3
    cap_reg_output[2] += system_gnd

    # =================================================================
    # STM32G030 MICROCONTROLLER SECTION
    # =================================================================

    # STM32G030C8T6 microcontroller
    stm32 = Component(
        symbol="MCU_ST_STM32G0:STM32G030C8T6",
        ref="U2",  # Stock: 54891 units (LCSC: C2040671)
        footprint="Package_QFP:LQFP-48_7x7mm_P0.5mm",
    )  # Stock: 54,891 units (LCSC: C2040671)

    # Power connections
    stm32["VDD"] += regulated_3v3  # Digital power
    stm32["VDDA"] += regulated_3v3  # Analog power
    stm32["VBAT"] += regulated_3v3  # Backup power
    stm32["VSS"] += system_gnd  # Digital ground
    stm32["VSSA"] += system_gnd  # Analog ground

    # Crystal oscillator connections
    stm32["PF0-OSC_IN"] += osc_in
    stm32["PF1-OSC_OUT"] += osc_out

    # Programming interface
    stm32["PA13"] += swdio  # SWD data I/O
    stm32["PA14"] += swclk  # SWD clock
    stm32["NRST"] += swd_reset  # Reset
    stm32["BOOT0"] += boot0  # Boot mode

    # Communication interfaces
    stm32["PA2"] += uart_tx  # USART2 TX
    stm32["PA3"] += uart_rx  # USART2 RX
    stm32["PA11"] += usb_dm  # USB D- (future USB device)
    stm32["PA12"] += usb_dp  # USB D+ (future USB device)

    # GPIO assignments
    stm32["PA5"] += status_led  # Status LED (safe pin)
    stm32["PA0"] += user_button  # User button input

    # STM32 power decoupling (multiple capacitors for different frequencies)
    cap_stm32_bulk = Component(
        symbol="Device:C",
        ref="C4",
        value="10uF",
        footprint="Capacitor_SMD:C_0805_2012Metric",
    )
    cap_stm32_hf1 = Component(
        symbol="Device:C",
        ref="C5",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric",
    )
    cap_stm32_hf2 = Component(
        symbol="Device:C",
        ref="C6",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric",
    )
    cap_stm32_bulk[1] += regulated_3v3
    cap_stm32_bulk[2] += system_gnd
    cap_stm32_hf1[1] += regulated_3v3
    cap_stm32_hf1[2] += system_gnd
    cap_stm32_hf2[1] += regulated_3v3
    cap_stm32_hf2[2] += system_gnd

    # =================================================================
    # 8MHz CRYSTAL OSCILLATOR
    # =================================================================

    # 8MHz crystal for precise timing
    crystal_8mhz = Component(
        symbol="Device:Crystal",
        ref="Y1",
        value="8MHz",
        footprint="Crystal:Crystal_SMD_HC49-SD",
    )  # Stock: >50k units (LCSC: C12674)

    crystal_8mhz[1] += osc_in
    crystal_8mhz[2] += osc_out

    # 18pF load capacitors for 18pF crystal load capacitance
    cap_osc_in = Component(
        symbol="Device:C",
        ref="C7",
        value="18pF",
        footprint="Capacitor_SMD:C_0603_1608Metric",
    )
    cap_osc_out = Component(
        symbol="Device:C",
        ref="C8",
        value="18pF",
        footprint="Capacitor_SMD:C_0603_1608Metric",
    )
    cap_osc_in[1] += osc_in
    cap_osc_in[2] += system_gnd
    cap_osc_out[1] += osc_out
    cap_osc_out[2] += system_gnd

    # =================================================================
    # RESET AND BOOT CONTROL
    # =================================================================

    # Reset pull-up resistor
    r_reset_pullup = Component(
        symbol="Device:R",
        ref="R4",
        value="10K",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )
    r_reset_pullup[1] += swd_reset
    r_reset_pullup[2] += regulated_3v3

    # Boot0 pull-down for normal boot
    r_boot0_pulldown = Component(
        symbol="Device:R",
        ref="R5",
        value="10K",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )
    r_boot0_pulldown[1] += boot0
    r_boot0_pulldown[2] += system_gnd

    # Reset button for manual reset
    btn_reset = Component(
        symbol="Switch:SW_Push",
        ref="SW1",
        footprint="Button_Switch_SMD:SW_SPST_CK_RS282G05A3",
    )
    btn_reset[1] += swd_reset
    btn_reset[2] += system_gnd

    # Boot mode selection jumper
    jp_boot = Component(
        symbol="Connector_Generic:Conn_01x03",
        ref="JP1",
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
    )
    jp_boot[1] += regulated_3v3  # Pin 1: 3.3V (program mode)
    jp_boot[2] += boot0  # Pin 2: BOOT0 pin
    jp_boot[3] += system_gnd  # Pin 3: GND (normal mode)

    # =================================================================
    # PROGRAMMING AND DEBUG INTERFACES
    # =================================================================

    # SWD programming connector (standard ARM 10-pin)
    swd_connector = Component(
        symbol="Connector_Generic:Conn_02x05_Odd_Even",
        ref="J2",
        footprint="Connector_PinHeader_1.27mm:PinHeader_2x05_P1.27mm_Vertical",
    )

    swd_connector[1] += regulated_3v3  # VTref
    swd_connector[2] += swdio  # SWDIO
    swd_connector[3] += system_gnd  # GND
    swd_connector[4] += swclk  # SWCLK
    swd_connector[5] += system_gnd  # GND
    swd_connector[6] += system_gnd  # SWO (not used)
    swd_connector[7] += system_gnd  # Key
    swd_connector[8] += system_gnd  # NC
    swd_connector[9] += system_gnd  # GND
    swd_connector[10] += swd_reset  # NRST

    # UART connector for serial communication
    uart_connector = Component(
        symbol="Connector_Generic:Conn_01x04",
        ref="J3",
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
    )
    uart_connector[1] += system_gnd  # GND
    uart_connector[2] += regulated_3v3  # 3.3V
    uart_connector[3] += uart_rx  # RX (to external TX)
    uart_connector[4] += uart_tx  # TX (to external RX)

    # =================================================================
    # USER INTERFACE ELEMENTS
    # =================================================================

    # Power indicator LED (always on when powered)
    r_power_led = Component(
        symbol="Device:R",
        ref="R6",
        value="1K",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )
    led_power = Component(
        symbol="Device:LED",
        ref="D4",
        value="GREEN",
        footprint="LED_SMD:LED_0603_1608Metric",
    )
    r_power_led[1] += regulated_3v3
    r_power_led[2] += led_power[1]
    led_power[2] += system_gnd

    # Status LED (controlled by PA5)
    r_status_led = Component(
        symbol="Device:R",
        ref="R7",
        value="330R",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )
    led_status = Component(
        symbol="Device:LED",
        ref="D5",
        value="BLUE",
        footprint="LED_SMD:LED_0603_1608Metric",
    )
    r_status_led[1] += status_led
    r_status_led[2] += led_status[1]
    led_status[2] += system_gnd

    # User button with pull-up
    r_button_pullup = Component(
        symbol="Device:R",
        ref="R8",
        value="10K",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )
    btn_user = Component(
        symbol="Switch:SW_Push",
        ref="SW2",
        footprint="Button_Switch_SMD:SW_SPST_CK_RS282G05A3",
    )
    r_button_pullup[1] += user_button
    r_button_pullup[2] += regulated_3v3
    btn_user[1] += user_button
    btn_user[2] += system_gnd
