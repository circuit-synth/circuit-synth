#!/usr/bin/env python3
"""
LED Indicator Circuit

A reusable LED indicator with current limiting resistor.
Demonstrates component composition and parameter configuration.
"""

from circuit_synth import Circuit, Component, Net, circuit
from .components import R_330, LED_RED, LED_GREEN


@circuit(name="status_led")
def status_led(vcc, gnd, control_signal, led_color="red"):
    """
    LED indicator with current limiting resistor.
    
    Features:
    - Current limiting resistor (330Ω for ~10mA at 3.3V)
    - Choice of LED colors (red or green)
    - Direct GPIO control
    
    Args:
        vcc: Power supply net (3.3V typical)
        gnd: Ground net  
        control_signal: GPIO control net
        led_color: "red" or "green" LED selection
    """
    
    # Select LED based on color parameter
    if led_color.lower() == "green":
        led = LED_GREEN()
    else: 
        led = LED_RED()
        
    led.ref = "D"  # Auto-numbered by circuit-synth
    
    # Current limiting resistor
    resistor = R_330()
    resistor.ref = "R"  # Auto-numbered by circuit-synth
    
    # Connect the circuit
    # GPIO -> Resistor -> LED anode, LED cathode -> GND
    control_signal += resistor[1]   # GPIO to resistor
    resistor[2] += led[1]           # Resistor to LED anode  
    led[2] += gnd                   # LED cathode to ground


@circuit(name="dual_status_leds") 
def dual_status_leds(vcc, gnd, status1, status2):
    """
    Dual LED status indicators (red + green).
    
    Demonstrates circuit composition - building complex circuits
    from simpler building blocks.
    
    Args:
        vcc: Power supply net
        gnd: Ground net
        status1: First status signal (red LED)
        status2: Second status signal (green LED)
    """
    
    # Create two independent LED circuits
    status_led(vcc, gnd, status1, led_color="red")
    status_led(vcc, gnd, status2, led_color="green")


if __name__ == "__main__":
    """
    Test the LED indicator circuits independently.
    """
    # Create test nets
    VCC_3V3 = Net('VCC_3V3')
    GND = Net('GND')
    GPIO1 = Net('GPIO1')
    GPIO2 = Net('GPIO2')
    
    # Test single LED
    print("Testing single LED circuit...")
    circuit1 = status_led(VCC_3V3, GND, GPIO1, led_color="red")
    circuit1.generate_kicad_project("single_led_test")
    
    # Test dual LEDs
    print("Testing dual LED circuit...")
    circuit2 = dual_status_leds(VCC_3V3, GND, GPIO1, GPIO2)
    circuit2.generate_kicad_project("dual_led_test")
    
    print("✅ LED indicator circuits generated successfully!")