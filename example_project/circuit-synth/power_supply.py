#!/usr/bin/env python3
"""
Power Supply Subcircuit - 5V to 3.3V Regulation
===============================================

Linear voltage regulator circuit converting 5V USB power to stable 3.3V
for microcontroller operation with proper decoupling capacitors.
"""

from circuit_synth import Component, Net, circuit


@circuit(name="Power_Supply_3V3")
def power_supply_subcircuit(vin_net, vout_net, gnd_net):
    """
    5V to 3.3V linear regulator subcircuit
    
    Features:
    - AMS1117-3.3V linear regulator
    - Input/output decoupling capacitors
    - Power indicator LED
    - Clean 3.3V output with <1% regulation
    
    Args:
        vin_net: 5V input power net (from USB)
        vout_net: 3.3V regulated output net
        gnd_net: System ground net
    """
    
    # AMS1117-3.3V linear voltage regulator
    # Low dropout regulator with excellent line/load regulation
    voltage_regulator = Component(
        symbol="Regulator_Linear:AMS1117-3.3",
        ref="U",
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2"
    )
    
    # Input decoupling capacitor
    # Filters switching noise from USB supply
    input_cap = Component(
        symbol="Device:C",
        ref="C",
        value="10uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    
    # Output decoupling capacitor  
    # Provides local energy storage for load transients
    output_cap = Component(
        symbol="Device:C",
        ref="C",
        value="22uF", 
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    
    # Power indicator LED
    # Visual indication that 3.3V rail is active
    power_led = Component(
        symbol="Device:LED",
        ref="D",
        footprint="LED_SMD:LED_0603_1608Metric"
    )
    
    # Current limiting resistor for power LED
    # Limits LED current to ~2mA at 3.3V
    led_resistor = Component(
        symbol="Device:R",
        ref="R", 
        value="1k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    # Regulator connections
    # AMS1117 pinout: 1=GND/ADJ, 2=VOUT, 3=VIN, TAB=VOUT
    voltage_regulator["VIN"] += vin_net      # 5V input
    voltage_regulator["VOUT"] += vout_net    # 3.3V output
    voltage_regulator["GND"] += gnd_net      # Ground reference
    
    # Input decoupling
    # Place close to regulator input for best performance
    input_cap[1] += vin_net
    input_cap[2] += gnd_net
    
    # Output decoupling
    # Place close to regulator output and load
    output_cap[1] += vout_net
    output_cap[2] += gnd_net
    
    # Power indicator LED circuit
    # LED cathode connects through current limiting resistor
    vout_net += power_led["A"]           # LED anode to 3.3V
    power_led["K"] += led_resistor[1]    # LED cathode through resistor
    led_resistor[2] += gnd_net           # Resistor to ground
    
    return locals()


if __name__ == "__main__":
    print("⚡ Testing power supply subcircuit...")
    
    # Create test nets
    vin_5v = Net('VCC_5V')
    vout_3v3 = Net('VCC_3V3') 
    gnd = Net('GND')
    
    # Test the subcircuit
    circuit_obj = power_supply_subcircuit(vin_5v, vout_3v3, gnd)
    
    print("✅ Power supply subcircuit created successfully")
    print(f"📊 Components: {len(circuit_obj.to_dict()['components'])}")
    print("📋 Features: 5V→3.3V regulation, decoupling, power LED")