#!/usr/bin/env python3
"""
CIRCUIT: STM32G030 Reference Design with Crystal Oscillator
PURPOSE: Complete STM32 setup with external crystal, power regulation, and programming interface
COMPONENTS: STM32G030C8T6 + 8MHz crystal + load capacitors + decoupling + SWD header
COMPLEXITY: Intermediate
DOMAIN: Microcontroller Design
"""

from circuit_synth import Circuit, Component, Net, circuit


@circuit
def stm32_reference_design():
    """
    Complete STM32G030 reference design with crystal oscillator.

    Design Notes:
    - STM32G030C8T6: ARM Cortex-M0+, 64KB Flash, 8KB RAM, LQFP-48
    - 8MHz external crystal for precise timing (USB, UART, timers)
    - 18pF load capacitors matched to crystal specification
    - Comprehensive decoupling: 100nF + 10µF for stable power
    - SWD programming/debug interface with proper pull-ups
    - Boot0 pin configuration for normal/programming modes
    - Status LED on safe GPIO pin (PA5)

    Crystal Oscillator Design:
    - 8MHz fundamental mode crystal (32MHz max for STM32G0)
    - Load capacitance: CL = (C1 × C2)/(C1 + C2) + Cstray ≈ 18pF
    - PCB trace length <10mm between crystal and MCU pins
    - Ground plane under crystal for EMI reduction
    """

    # System power nets
    vcc_3v3 = Net("VCC_3V3")  # 3.3V power supply
    gnd = Net("GND")  # Ground reference

    # Crystal oscillator nets
    osc_in = Net("OSC_IN")  # Crystal input to MCU
    osc_out = Net("OSC_OUT")  # Crystal output from MCU

    # Programming and control nets
    swdio = Net("SWDIO")  # SWD data I/O
    swclk = Net("SWCLK")  # SWD clock
    swd_reset = Net("SWD_RESET")  # SWD reset (NRST)
    boot0 = Net("BOOT0")  # Boot mode selection

    # GPIO nets
    status_led = Net("STATUS_LED")  # Status LED control (PA5)

    # =================================================================
    # STM32G030C8T6 MICROCONTROLLER
    # =================================================================

    # STM32G030C8T6 in LQFP-48 package
    # Pin 1: VBAT, Pin 8: VSSA, Pin 9: VDDA, Pin 24: VDD, Pin 37: VSS
    # Pin 2: PC13, Pin 3: PC14/OSC32_IN, Pin 4: PC15/OSC32_OUT
    # Pin 5: PF0/OSC_IN, Pin 6: PF1/OSC_OUT, Pin 7: NRST
    stm32 = Component(
        symbol="MCU_ST_STM32G0:STM32G030C8T6",  # Stock: 54891 units (LCSC: C2040671)# Updated with in-stock part
        ref="U1",
        footprint="Package_QFP:LQFP-48_7x7mm_P0.5mm",
    )  # Stock: 54,891 units (LCSC: C2040671)

    # Power connections
    stm32["VDD"] += vcc_3v3  # Digital power supply
    stm32["VDDA"] += vcc_3v3  # Analog power supply
    stm32["VBAT"] += vcc_3v3  # Backup power (tied to VDD)
    stm32["VSS"] += gnd  # Digital ground
    stm32["VSSA"] += gnd  # Analog ground

    # Crystal oscillator connections
    stm32["PF0-OSC_IN"] += osc_in  # Crystal input
    stm32["PF1-OSC_OUT"] += osc_out  # Crystal output

    # Programming interface (SWD)
    stm32["PA13"] += swdio  # SWD data I/O
    stm32["PA14"] += swclk  # SWD clock
    stm32["NRST"] += swd_reset  # Reset pin

    # Boot mode control
    stm32["BOOT0"] += boot0  # Boot mode selection

    # Status LED (PA5 is safe, no alternate functions)
    stm32["PA5"] += status_led  # GPIO output for LED

    # =================================================================
    # CRYSTAL OSCILLATOR CIRCUIT
    # =================================================================

    # 8MHz crystal oscillator
    # Fundamental mode crystal for precise timing
    crystal_8mhz = Component(
        symbol="Device:Crystal",
        ref="Y1",
        value="8MHz",
        footprint="Crystal:Crystal_SMD_HC49-SD",
    )

    # Crystal connections
    crystal_8mhz[1] += osc_in  # Crystal pin 1 to OSC_IN
    crystal_8mhz[2] += osc_out  # Crystal pin 2 to OSC_OUT

    # Crystal load capacitors (18pF each for 18pF load capacitance)
    # CL = (C1 × C2)/(C1 + C2) + Cstray where Cstray ≈ 2-5pF
    cap_osc_in = Component(
        symbol="Device:C",
        ref="C1",
        value="18pF",
        footprint="Capacitor_SMD:C_0603_1608Metric",
    )

    cap_osc_out = Component(
        symbol="Device:C",
        ref="C2",
        value="18pF",
        footprint="Capacitor_SMD:C_0603_1608Metric",
    )

    # Load capacitor connections
    cap_osc_in[1] += osc_in  # OSC_IN to ground
    cap_osc_in[2] += gnd

    cap_osc_out[1] += osc_out  # OSC_OUT to ground
    cap_osc_out[2] += gnd

    # =================================================================
    # POWER SUPPLY DECOUPLING
    # =================================================================

    # Primary decoupling capacitor (close to VDD pin)
    cap_vdd_bulk = Component(
        symbol="Device:C",
        ref="C3",
        value="10uF",
        footprint="Capacitor_SMD:C_0805_2012Metric",
    )
    cap_vdd_bulk[1] += vcc_3v3
    cap_vdd_bulk[2] += gnd

    # High frequency decoupling (close to VDD pin)
    cap_vdd_hf = Component(
        symbol="Device:C",
        ref="C4",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric",
    )
    cap_vdd_hf[1] += vcc_3v3
    cap_vdd_hf[2] += gnd

    # Analog supply decoupling (close to VDDA pin)
    cap_vdda = Component(
        symbol="Device:C",
        ref="C5",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric",
    )
    cap_vdda[1] += vcc_3v3  # VDDA connected to VDD
    cap_vdda[2] += gnd

    # =================================================================
    # RESET AND BOOT CONTROL
    # =================================================================

    # Reset pull-up resistor (10K for proper reset operation)
    r_reset_pullup = Component(
        symbol="Device:R",
        ref="R1",
        value="10K",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )
    r_reset_pullup[1] += swd_reset
    r_reset_pullup[2] += vcc_3v3

    # Boot0 pull-down resistor (ensures normal boot mode)
    r_boot0_pulldown = Component(
        symbol="Device:R",
        ref="R2",
        value="10K",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )
    r_boot0_pulldown[1] += boot0
    r_boot0_pulldown[2] += gnd

    # =================================================================
    # SWD PROGRAMMING INTERFACE
    # =================================================================

    # SWD connector (2x5 pin header, 1.27mm pitch)
    swd_connector = Component(
        symbol="Connector_Generic:Conn_02x05_Odd_Even",
        ref="J1",
        footprint="Connector_PinHeader_1.27mm:PinHeader_2x05_P1.27mm_Vertical_SMD",
    )

    # SWD pin connections (standard ARM 10-pin layout)
    swd_connector[1] += vcc_3v3  # Pin 1: VTref (3.3V)
    swd_connector[2] += swdio  # Pin 2: SWDIO
    swd_connector[3] += gnd  # Pin 3: GND
    swd_connector[4] += swclk  # Pin 4: SWCLK
    swd_connector[5] += gnd  # Pin 5: GND
    swd_connector[6] += gnd  # Pin 6: SWO (not used, tie to GND)
    swd_connector[7] += gnd  # Pin 7: Key (no connection)
    swd_connector[8] += gnd  # Pin 8: NC (not connected)
    swd_connector[9] += gnd  # Pin 9: GND
    swd_connector[10] += swd_reset  # Pin 10: NRST

    # =================================================================
    # STATUS LED INDICATOR
    # =================================================================

    # Status LED with current limiting resistor
    r_led = Component(
        symbol="Device:R",
        ref="R3",
        value="330R",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    led_status = Component(
        symbol="Device:LED",
        ref="D1",
        value="LED",
        footprint="LED_SMD:LED_0603_1608Metric",
    )

    # LED circuit connections
    r_led[1] += status_led  # PA5 to current limiting resistor
    r_led[2] += led_status[1]  # Resistor to LED anode
    led_status[2] += gnd  # LED cathode to ground

    # Current calculation: I = (3.3V - 2.1V) / 330Ω = 3.6mA
