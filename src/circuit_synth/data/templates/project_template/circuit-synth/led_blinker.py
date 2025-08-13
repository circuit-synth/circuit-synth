#!/usr/bin/env python3
"""
LED Blinker Subcircuit - Status Indication
==========================================

Simple LED circuit with current limiting for status indication.
Can be controlled by microcontroller GPIO for user feedback.
"""

from circuit_synth import Component, Net, circuit


@circuit(name="Status_LED")
def led_blinker_subcircuit(vcc_3v3_net, gnd_net, control_net):
    """
    Status LED subcircuit with current limiting
    
    Features:
    - High-brightness LED for clear visibility
    - Current limiting resistor sized for 2mA @ 3.3V
    - GPIO control from microcontroller
    - Standard 0603 SMD components
    
    Args:
        vcc_3v3_net: 3.3V power supply net
        gnd_net: System ground net  
        control_net: GPIO control signal from MCU
    """
    
    # Status LED (green for power/activity indication)
    # Standard green LED with ~2.1V forward voltage
    status_led = Component(
        symbol="Device:LED",
        ref="D",
        footprint="LED_SMD:LED_0603_1608Metric"
    )
    
    # Current limiting resistor
    # (3.3V - 2.1V) / 2mA = 600Ω, use 680Ω for safety margin
    current_resistor = Component(
        symbol="Device:R", 
        ref="R",
        value="680",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    # LED circuit connections
    # GPIO high turns on LED, GPIO low (or high-Z) turns off LED
    control_net += current_resistor[1]    # GPIO to current limiting resistor
    current_resistor[2] += status_led["A"] # Resistor to LED anode
    status_led["K"] += gnd_net            # LED cathode to ground
    
    return locals()


if __name__ == "__main__":
    print("💡 Testing LED blinker subcircuit...")
    
    # Create test nets
    vcc_3v3 = Net('VCC_3V3')
    gnd = Net('GND')
    led_ctrl = Net('LED_CONTROL')
    
    # Test the subcircuit
    circuit_obj = led_blinker_subcircuit(vcc_3v3, gnd, led_ctrl)
    
    print("✅ LED blinker subcircuit created successfully") 
    print(f"📊 Components: {len(circuit_obj.to_dict()['components'])}")
    print("📋 Features: GPIO-controlled LED with current limiting")