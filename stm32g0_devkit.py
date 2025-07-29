#!/usr/bin/env python3
"""
STM32G0 Development Kit
A complete development board based on STM32G050C8T6 with USB-C power, 
programming interface, and user I/O.
"""

from src.circuit_synth import *

@circuit(name="STM32G0_DevKit")
def stm32g0_devkit():
    """
    STM32G0 Development Kit with USB-C power, SWD programming, and user I/O.
    
    Features:
    - STM32G050C8T6 MCU (64KB Flash, 8KB RAM, ARM Cortex-M0+)
    - USB-C connector for power (5V to 3.3V LDO regulation)
    - SWD programming header compatible with ST-Link
    - User LED, power LED, and reset button
    - GPIO headers for expansion
    - Crystal oscillator for precise timing
    - Comprehensive decoupling capacitors
    """
    
    # Power rails
    VCC_5V = Net('VCC_5V')      # USB-C input power
    VCC_3V3 = Net('VCC_3V3')    # Regulated 3.3V for MCU
    GND = Net('GND')            # Ground
    
    # ===== USB-C Power Input =====
    usb_c = Component(
        symbol="Connector:USB_C_Receptacle_USB2.0_16P", 
        ref="J",
        footprint="Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12"
    )
    
    # Connect USB-C power
    usb_c["VBUS"] += VCC_5V
    usb_c["GND"] += GND
    usb_c["SHIELD"] += GND
    
    # ===== 3.3V Power Supply =====
    # LDO voltage regulator: 5V -> 3.3V
    vreg = Component(
        symbol="Regulator_Linear:AMS1117-3.3", 
        ref="U",
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2"
    )
    
    vreg["VI"] += VCC_5V
    vreg["VO"] += VCC_3V3
    vreg["GND"] += GND
    
    # Input decoupling capacitor
    cap_vin = Component(
        symbol="Device:C", 
        ref="C", 
        value="10uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    cap_vin[1] += VCC_5V
    cap_vin[2] += GND
    
    # Output decoupling capacitor
    cap_vout = Component(
        symbol="Device:C", 
        ref="C", 
        value="22uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    cap_vout[1] += VCC_3V3
    cap_vout[2] += GND
    
    # Power LED
    led_power = Component(
        symbol="Device:LED", 
        ref="D",
        footprint="LED_SMD:LED_0603_1608Metric"
    )
    r_power = Component(
        symbol="Device:R", 
        ref="R", 
        value="1k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    led_power["A"] += VCC_3V3
    led_power["K"] += r_power[1]
    r_power[2] += GND
    
    # ===== STM32G0 Microcontroller =====
    mcu = Component(
        symbol="MCU_ST_STM32G0:STM32G050C8Tx", 
        ref="U",
        footprint="Package_QFP:LQFP-48_7x7mm_P0.5mm"
    )
    
    # Power connections
    mcu["VDD"] += VCC_3V3
    mcu["VREF+"] += VCC_3V3  # Analog power
    mcu["VSS"] += GND
    
    # ===== Crystal Oscillator (8MHz) =====
    crystal = Component(
        symbol="Device:Crystal", 
        ref="Y",
        value="8MHz",
        footprint="Crystal:Crystal_SMD_HC49-SD"
    )
    
    # Crystal load capacitors
    cap_c1 = Component(
        symbol="Device:C", 
        ref="C", 
        value="22pF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    cap_c2 = Component(
        symbol="Device:C", 
        ref="C", 
        value="22pF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    
    crystal[1] += mcu["PF0"]  # OSC_IN
    crystal[2] += mcu["PF1"]  # OSC_OUT
    cap_c1[1] += mcu["PF0"]
    cap_c1[2] += GND
    cap_c2[1] += mcu["PF1"]
    cap_c2[2] += GND
    
    # ===== MCU Decoupling Capacitors =====
    # Multiple small decoupling caps for clean power
    for i in range(4):
        cap_decouple = Component(
            symbol="Device:C", 
            ref="C", 
            value="100nF",
            footprint="Capacitor_SMD:C_0603_1608Metric"
        )
        cap_decouple[1] += VCC_3V3
        cap_decouple[2] += GND
    
    # Larger decoupling capacitor
    cap_bulk = Component(
        symbol="Device:C", 
        ref="C", 
        value="10uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    cap_bulk[1] += VCC_3V3
    cap_bulk[2] += GND
    
    # ===== Reset Circuit =====
    # Reset button
    btn_reset = Component(
        symbol="Switch:SW_Push", 
        ref="SW",
        footprint="Button_Switch_SMD:SW_SPST_CK_RS282G05A3"
    )
    
    # Reset pullup resistor
    r_reset = Component(
        symbol="Device:R", 
        ref="R", 
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    # Reset connections (pin 7 is typically NRST on STM32)
    mcu[7] += r_reset[1]
    r_reset[2] += VCC_3V3
    mcu[7] += btn_reset[1]
    btn_reset[2] += GND
    
    # ===== SWD Programming Interface =====
    swd_header = Component(
        symbol="Connector_Generic:Conn_02x05_Odd_Even", 
        ref="J",
        footprint="Connector_PinHeader_2.54mm:PinHeader_2x05_P2.54mm_Vertical"
    )
    
    # SWD connections (standard 10-pin layout)
    swd_header[1] += VCC_3V3      # VCC
    swd_header[2] += mcu["PA14"]  # SWCLK
    swd_header[3] += GND          # GND
    swd_header[4] += mcu["PA13"]  # SWDIO
    swd_header[5] += GND          # GND
    swd_header[6] += mcu["PB4"]   # SWO (optional)
    swd_header[7] += GND          # KEY (no connection)
    swd_header[8] += GND          # NC
    swd_header[9] += GND          # GND
    swd_header[10] += mcu[7] # RESET
    
    # ===== User Interface =====
    # User LED
    led_user = Component(
        symbol="Device:LED", 
        ref="D",
        footprint="LED_SMD:LED_0603_1608Metric"
    )
    r_user = Component(
        symbol="Device:R", 
        ref="R", 
        value="330",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    mcu["PA5"] += r_user[1]
    r_user[2] += led_user["A"]
    led_user["K"] += GND
    
    # User button
    btn_user = Component(
        symbol="Switch:SW_Push", 
        ref="SW",
        footprint="Button_Switch_SMD:SW_SPST_CK_RS282G05A3"
    )
    
    # Button pullup resistor
    r_button = Component(
        symbol="Device:R", 
        ref="R", 
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    mcu["PA0"] += r_button[1]
    r_button[2] += VCC_3V3
    mcu["PA0"] += btn_user[1]
    btn_user[2] += GND
    
    # ===== GPIO Expansion Headers =====
    # Port A header
    header_porta = Component(
        symbol="Connector_Generic:Conn_01x08", 
        ref="J",
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical"
    )
    
    # Connect Port A pins
    header_porta[1] += mcu["PA1"]
    header_porta[2] += mcu["PA2"]
    header_porta[3] += mcu["PA3"]
    header_porta[4] += mcu["PA4"]
    header_porta[5] += mcu["PA6"]
    header_porta[6] += mcu["PA7"]
    header_porta[7] += mcu["PA8"]
    header_porta[8] += mcu["PA15"]
    
    # Port B header
    header_portb = Component(
        symbol="Connector_Generic:Conn_01x08", 
        ref="J",
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical"
    )
    
    # Connect Port B pins
    header_portb[1] += mcu["PB0"]
    header_portb[2] += mcu["PB1"]
    header_portb[3] += mcu["PB2"]
    header_portb[4] += mcu["PB3"]
    header_portb[5] += mcu["PB5"]
    header_portb[6] += mcu["PB6"]
    header_portb[7] += mcu["PB7"]
    header_portb[8] += mcu["PB8"]
    
    # Power header for expansion
    header_power = Component(
        symbol="Connector_Generic:Conn_01x04", 
        ref="J",
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical"
    )
    
    header_power[1] += VCC_3V3
    header_power[2] += VCC_5V
    header_power[3] += GND
    header_power[4] += GND


if __name__ == "__main__":
    # Generate the development kit
    devkit = stm32g0_devkit()
    
    print("STM32G0 Development Kit Generated!")
    print(f"Components: {len(devkit.components)}")
    print(f"Nets: {len(devkit.nets)}")
    
    # Export to KiCad (using correct method)
    try:
        devkit.generate_kicad_files("stm32g0_devkit")
        print("KiCad files exported to stm32g0_devkit/")
    except AttributeError:
        print("Note: KiCad export method needs to be implemented")
        print("Circuit structure is ready for KiCad export")