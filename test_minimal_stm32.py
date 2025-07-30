#!/usr/bin/env python3
"""
Minimal STM32 test to verify basic functionality
"""

from src.circuit_synth import *

@circuit(name="Minimal_STM32_Test")
def minimal_stm32_test():
    """Simple STM32 circuit to verify symbols work"""
    
    # Power nets
    VCC_3V3 = Net('VCC_3V3')
    GND = Net('GND')
    
    # Test with a simple voltage regulator first
    vreg = Component(
        symbol="Regulator_Linear:AMS1117-3.3", 
        ref="U1",
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2"
    )
    
    vreg["GND"] += GND
    vreg["VO"] += VCC_3V3
    vreg["VI"] += Net('VCC_5V')
    
    # Test with an LED
    led = Component(
        symbol="Device:LED", 
        ref="D1",
        footprint="LED_SMD:LED_0603_1608Metric"
    )
    
    resistor = Component(
        symbol="Device:R", 
        ref="R1", 
        value="330",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    led["A"] += VCC_3V3
    led["K"] += resistor[1]
    resistor[2] += GND

if __name__ == "__main__":
    print("Testing minimal STM32 circuit...")
    circuit = minimal_stm32_test()
    print(f"✅ Success! Components: {len(circuit.components)}, Nets: {len(circuit.nets)}")