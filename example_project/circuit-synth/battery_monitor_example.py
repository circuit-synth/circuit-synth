#!/usr/bin/env python3
"""
Battery-Powered Monitoring System Example
Demonstrates using multiple circuit patterns together in a real application

Features:
- USB-C charging with LiPo battery charger
- Battery voltage monitoring via resistor divider
- Temperature sensing with thermistor
- Op-amp buffered analog sensors
- RS-485 industrial communication
"""

from circuit_synth import *

# Import circuit patterns
from lipo_charger import lipo_charger
from resistor_divider import resistor_divider
from thermistor import thermistor_sensor
from opamp_follower import opamp_voltage_follower
from rs485 import rs485_transceiver

@circuit(name="Battery_Monitor_System")
def battery_monitor_system():
    """
    Complete battery-powered monitoring system

    System overview:
    - Charges LiPo battery from USB-C
    - Monitors battery voltage and temperature
    - Buffers sensor outputs with op-amps
    - Communicates via RS-485 to master controller
    """

    # Create shared power nets
    usb_vbus = Net('USB_VBUS')         # 5V from USB-C
    battery_plus = Net('VBAT+')        # 3.7V nominal (3.0-4.2V range)
    system_3v3 = Net('VCC_3V3')        # 3.3V regulated for logic
    gnd = Net('GND')

    # Communication nets
    uart_tx = Net('UART_TX')           # From MCU
    uart_rx = Net('UART_RX')           # To MCU
    rs485_de = Net('RS485_DE')         # Driver enable
    rs485_a = Net('RS485_A')           # Differential A
    rs485_b = Net('RS485_B')           # Differential B

    # Analog sensing nets
    adc_battery_voltage = Net('ADC_VBAT')
    adc_temperature = Net('ADC_TEMP')
    sensor_raw = Net('SENSOR_RAW')     # High impedance sensor
    sensor_buffered = Net('SENSOR_BUF') # Buffered for ADC

    # Status indication
    charge_led = Net('CHARGE_LED')

    # === Power Management ===

    # LiPo battery charger (USB-C to battery)
    lipo_charger(usb_vbus, gnd, battery_plus, gnd, charge_led)

    # Charge status LED
    led_charge = Component(
        symbol="Device:LED",
        ref="D",
        footprint="LED_SMD:LED_0603_1608Metric"
    )
    led_charge["A"] += system_3v3
    led_charge["K"] += charge_led

    # 3.3V regulator for system (simplified - could use from power_supply.py)
    vreg_3v3 = Component(
        symbol="Regulator_Linear:AMS1117-3.3",
        ref="U",
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2"
    )
    cap_in = Component(symbol="Device:C", ref="C", value="10uF",
                      footprint="Capacitor_SMD:C_0805_2012Metric")
    cap_out = Component(symbol="Device:C", ref="C", value="22uF",
                       footprint="Capacitor_SMD:C_0805_2012Metric")

    vreg_3v3["VI"] += battery_plus
    vreg_3v3["VO"] += system_3v3
    vreg_3v3["GND"] += gnd
    cap_in[1] += battery_plus
    cap_in[2] += gnd
    cap_out[1] += system_3v3
    cap_out[2] += gnd

    # === Battery Voltage Monitoring ===

    # Monitor battery voltage (4.2V max) with ADC (3.3V max)
    # Use 2:1 divider -> 4.2V becomes 2.1V (safe for 3.3V ADC)
    resistor_divider(battery_plus, adc_battery_voltage, gnd, ratio="2:1")

    # === Temperature Monitoring ===

    # Monitor battery temperature with NTC thermistor
    thermistor_sensor(system_3v3, adc_temperature, gnd, thermistor_type="NTC_10k")

    # === Analog Sensor Buffering ===

    # Buffer high-impedance sensor output before ADC
    # Example: pH sensor, glass electrode, or other high-Z sensor
    opamp_voltage_follower(system_3v3, gnd, sensor_raw, sensor_buffered)

    # Simulated high-impedance sensor (placeholder)
    # In real design, this would be an actual sensor connector
    sensor_input = Component(
        symbol="Connector:TestPoint",
        ref="TP",
        footprint="TestPoint:TestPoint_Pad_D2.0mm"
    )
    sensor_input[1] += sensor_raw

    # === RS-485 Communication ===

    # Industrial communication interface
    rs485_transceiver(system_3v3, gnd, uart_tx, uart_rx, rs485_de,
                     rs485_a, rs485_b)

    # RS-485 terminal block
    conn_rs485 = Component(
        symbol="Connector:Screw_Terminal_01x03",
        ref="J",
        footprint="TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-3_1x03_P5.00mm_Horizontal"
    )
    conn_rs485[1] += rs485_a
    conn_rs485[2] += rs485_b
    conn_rs485[3] += gnd

    # === Test Points for Debugging ===

    tp_vbat = Component(symbol="Connector:TestPoint", ref="TP",
                       footprint="TestPoint:TestPoint_Pad_D2.0mm")
    tp_3v3 = Component(symbol="Connector:TestPoint", ref="TP",
                      footprint="TestPoint:TestPoint_Pad_D2.0mm")
    tp_usb = Component(symbol="Connector:TestPoint", ref="TP",
                      footprint="TestPoint:TestPoint_Pad_D2.0mm")

    tp_vbat[1] += battery_plus
    tp_3v3[1] += system_3v3
    tp_usb[1] += usb_vbus


if __name__ == "__main__":
    print("🔋 Starting Battery Monitoring System generation...")
    print("")

    # Generate the circuit
    print("📋 Creating circuit with integrated patterns:")
    print("   ✓ LiPo battery charger (USB-C input)")
    print("   ✓ Battery voltage monitoring (resistor divider)")
    print("   ✓ Temperature sensing (NTC thermistor)")
    print("   ✓ Sensor buffering (op-amp follower)")
    print("   ✓ RS-485 communication interface")
    print("")

    circuit = battery_monitor_system()

    # Generate outputs
    print("🔌 Generating netlists...")
    circuit.generate_kicad_netlist("Battery_Monitor_System.net")
    circuit.generate_json_netlist("Battery_Monitor_System.json")

    print("🏗️  Generating KiCad project...")
    circuit.generate_kicad_project(
        project_name="Battery_Monitor_System",
        placement_algorithm="hierarchical",
        generate_pcb=True
    )

    print("")
    print("✅ Battery Monitoring System generated!")
    print("")
    print("📊 System Specifications:")
    print("   • Input: USB-C 5V for charging")
    print("   • Battery: Single-cell Li-ion/LiPo (3.7V nominal)")
    print("   • Charge current: 500mA (configurable)")
    print("   • System voltage: 3.3V regulated")
    print("   • Battery voltage range: 3.0V-4.2V")
    print("   • ADC monitoring: Battery voltage (2.1V max), Temperature")
    print("   • Communication: RS-485 half-duplex")
    print("")
    print("🔬 Monitored Parameters:")
    print("   • Battery voltage (via 2:1 divider)")
    print("   • Battery temperature (NTC thermistor)")
    print("   • Sensor input (buffered high-Z)")
    print("   • Charge status (LED indicator)")
    print("")
    print("📁 Generated files in Battery_Monitor_System/:")
    print("   • Battery_Monitor_System.kicad_pro")
    print("   • Battery_Monitor_System.kicad_sch")
    print("   • Battery_Monitor_System.kicad_pcb")
    print("   • Battery_Monitor_System.net")
    print("   • Battery_Monitor_System.json")
    print("")
    print("🎯 Ready for PCB manufacturing!")
