#!/usr/bin/env python3
"""
LED Blinker Subcircuit - Status LED with current limiting
Simple LED indicator with proper current limiting resistor
"""

from circuit_synth import *

@circuit(name="LED_Blinker")  
def led_blinker_subcircuit(vcc_3v3=None, gnd=None, led_control=None):
    """LED with current limiting resistor"""
    
    # Interface nets - use provided nets or create defaults for standalone operation
    vcc_3v3 = vcc_3v3 or Net('VCC_3V3')
    gnd = gnd or Net('GND')
    led_control = led_control or Net('LED_CONTROL')
    
    # LED and resistor
    led = Component(symbol="Device:LED", ref="D", 
                   footprint="LED_SMD:LED_0805_2012Metric")
    resistor = Component(symbol="Device:R", ref="R", value="330",
                        footprint="Resistor_SMD:R_0805_2012Metric")
    
    # Connections  
    resistor[1] += vcc_3v3
    resistor[2] += led["A"]  # Anode
    led["K"] += led_control  # Cathode (controlled by MCU)

if __name__ == "__main__":
    circuit = led_blinker_subcircuit()
    circuit.generate_kicad_project("led_blinker")
    print("✅ LED blinker subcircuit generated!")
