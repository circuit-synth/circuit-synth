#!/usr/bin/env python3
"""
Simple LED Circuit - Hello World of Electronics
Basic LED with current limiting resistor
"""

from circuit_synth import *

@circuit
def hello_led():
    """Simple LED circuit with current limiting resistor"""
    
    # Components
    led = Component(
        symbol="Device:LED", 
        ref="D",
        footprint="LED_THT:LED_D5.0mm"
    )
    
    resistor = Component(
        symbol="Device:R",
        ref="R", 
        value="330",
        footprint="Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal"
    )
    
    # Nets
    vcc = Net("VCC")
    gnd = Net("GND")
    led_anode = Net("LED_ANODE")
    
    # Connections
    resistor[1] += vcc
    resistor[2] += led_anode
    led["A"] += led_anode  # Anode
    led["K"] += gnd        # Cathode

if __name__ == "__main__":
    circuit = hello_led()
    circuit.generate_kicad_project("hello_led")
    print("✅ Hello LED circuit generated!")
