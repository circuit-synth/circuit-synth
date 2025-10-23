"""STM32 Minimal Board - Simple Example

This example demonstrates:
- STM32F411CEU6 microcontroller integration
- Minimum viable circuit for STM32
- External crystal oscillator
- Basic power and programming connections

STM32F411CEU6 Features:
- ARM Cortex-M4 @ 100MHz
- 512KB Flash, 128KB RAM
- USB OTG Full Speed
- LQFP-48 package
- Good availability on JLCPCB

Minimal STM32 circuit requirements:
- 3.3V power with decoupling
- Boot0 pull-down resistor
- Reset pull-up resistor
- SWD programming header
- External crystal (8MHz) for accurate timing
"""
from circuit_synth import Component, Net, circuit


@circuit(name="STM32_Minimal")
def stm32_minimal():
    """Minimal STM32F411 circuit with crystal and programming interface

    This circuit provides:
    - STM32F411CEU6 microcontroller
    - 8MHz external crystal oscillator
    - SWD programming header
    - Proper power decoupling
    - Boot and reset configuration

    For a complete development board, add:
    - USB connector
    - Voltage regulator
    - User LED
    - Reset button
    """

    # STM32F411CEU6 microcontroller (LQFP-48)
    mcu = Component(
        symbol="MCU_ST_STM32F4:STM32F411CEUx",
        ref="U",
        footprint="Package_QFP:LQFP-48_7x7mm_P0.5mm"
    )

    # 8MHz crystal oscillator for HSE (High Speed External)
    # STM32 uses PLL to multiply this to 100MHz system clock
    crystal = Component(
        symbol="Device:Crystal",
        ref="Y",
        value="8MHz",
        footprint="Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm"
    )

    # Crystal load capacitors (typically 10-20pF for 8MHz)
    # Check crystal datasheet for exact value
    cap_xtal1 = Component(
        symbol="Device:C",
        ref="C",
        value="18pF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )

    cap_xtal2 = Component(
        symbol="Device:C",
        ref="C",
        value="18pF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )

    # Power decoupling capacitors
    # STM32 requires decoupling on each VDD pin
    cap_vdd1 = Component(
        symbol="Device:C",
        ref="C",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )

    cap_vdd2 = Component(
        symbol="Device:C",
        ref="C",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )

    # Bulk capacitor
    cap_bulk = Component(
        symbol="Device:C",
        ref="C",
        value="10uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )

    # Boot0 pull-down resistor (boot from flash)
    r_boot0 = Component(
        symbol="Device:R",
        ref="R",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    # Reset pull-up resistor
    r_reset = Component(
        symbol="Device:R",
        ref="R",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    # SWD programming header (4-pin: VCC, GND, SWDIO, SWCLK)
    swd_header = Component(
        symbol="Connector_Generic:Conn_01x04",
        ref="J",
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical"
    )

    # Define nets
    vcc_3v3 = Net('VCC_3V3')  # 3.3V power
    gnd = Net('GND')          # Ground
    osc_in = Net('OSC_IN')    # Crystal input
    osc_out = Net('OSC_OUT')  # Crystal output
    swdio = Net('SWDIO')      # SWD data
    swclk = Net('SWCLK')      # SWD clock
    nrst = Net('NRST')        # Reset (active low)
    boot0 = Net('BOOT0')      # Boot configuration

    # Connect MCU power pins
    mcu["VDD"] += vcc_3v3
    mcu["VDDA"] += vcc_3v3  # Analog power
    mcu["VSS"] += gnd
    mcu["VSSA"] += gnd      # Analog ground

    # Connect crystal oscillator
    mcu["PH0"] += osc_in   # OSC_IN pin
    mcu["PH1"] += osc_out  # OSC_OUT pin

    crystal[1] += osc_in
    crystal[2] += osc_out

    # Crystal load capacitors
    cap_xtal1[1] += osc_in
    cap_xtal1[2] += gnd

    cap_xtal2[1] += osc_out
    cap_xtal2[2] += gnd

    # Connect decoupling capacitors
    cap_vdd1[1] += vcc_3v3
    cap_vdd1[2] += gnd

    cap_vdd2[1] += vcc_3v3
    cap_vdd2[2] += gnd

    cap_bulk[1] += vcc_3v3
    cap_bulk[2] += gnd

    # Connect Boot0 pin (pull-down to boot from flash)
    mcu["BOOT0"] += boot0
    r_boot0[1] += boot0
    r_boot0[2] += gnd

    # Connect reset pin (pull-up, active low)
    mcu["NRST"] += nrst
    r_reset[1] += nrst
    r_reset[2] += vcc_3v3

    # Connect SWD programming interface
    mcu["PA13"] += swdio  # SWDIO
    mcu["PA14"] += swclk  # SWCLK

    # Connect SWD header
    swd_header[1] += vcc_3v3  # VCC
    swd_header[2] += gnd      # GND
    swd_header[3] += swdio    # SWDIO
    swd_header[4] += swclk    # SWCLK


if __name__ == '__main__':
    # Generate KiCad project
    circuit_obj = stm32_minimal()

    circuit_obj.generate_kicad_project(
        project_name="stm32_minimal",
        placement_algorithm="hierarchical",
        generate_pcb=True
    )

    print("✅ STM32F411 minimal circuit generated!")
    print("📁 Open in KiCad: stm32_minimal/stm32_minimal.kicad_pro")
    print()
    print("📊 Circuit Features:")
    print("   • STM32F411CEU6 (100MHz Cortex-M4)")
    print("   • 8MHz external crystal")
    print("   • SWD programming interface")
    print("   • Boot from flash configuration")
    print()
    print("🔧 Programming:")
    print("   Use ST-Link V2 or similar SWD programmer")
    print("   Connect: VCC, GND, SWDIO, SWCLK")
    print()
    print("💡 Next Steps:")
    print("   • Add USB connector for USB programming/communication")
    print("   • Add voltage regulator for 5V→3.3V")
    print("   • Add reset button")
    print("   • Add user LED (e.g., on PC13)")
    print("   • Add USB data line protection (if using USB)")
