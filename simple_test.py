#!/usr/bin/env python3
"""
Simple Circuit-Synth Test
========================

Basic test to verify circuit-synth is working correctly.
"""

from circuit_synth import *

@circuit(name="simple_test")
def simple_led_circuit():
    """Simple LED circuit with current limiting resistor."""
    
    # Components
    led = Component("Device:LED", ref="D", value="Red LED")
    resistor = Component("Device:R", ref="R", value="220R")
    
    # Nets
    VCC = Net('VCC_5V')
    GND = Net('GND')
    led_anode = Net('LED_ANODE')
    
    # Connections
    led["A"] += led_anode
    led["K"] += GND
    resistor[1] += VCC
    resistor[2] += led_anode
    
    return led, resistor

if __name__ == "__main__":
    print("🔧 Testing Circuit-Synth...")
    
    # Create the circuit
    circuit = simple_led_circuit()
    print("✅ Circuit created successfully!")
    
    # Check components
    components = circuit._components
    print(f"📦 Components: {len(components)} total")
    for ref, comp in components.items():
        print(f"   - {ref}: {comp.symbol}")
    
    # Check nets  
    nets = circuit._nets
    print(f"🔗 Nets: {len(nets)} total")
    for name, net in nets.items():
        print(f"   - {name}: {len(net.pins)} pins")
    
    print("🎉 Circuit-Synth test completed successfully!")