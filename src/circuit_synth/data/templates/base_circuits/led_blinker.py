"""LED Blinker - Basic LED Circuit with Current Limiting

This example demonstrates:
- Using LED components from Device library
- Calculating current limiting resistor values
- Working with different footprints
- Component value specification
- Named pin connections (anode/cathode)

LED specifications:
- Forward voltage (Vf): 2.0V (typical for red LED)
- Forward current (If): 20mA (maximum safe continuous current)
- Supply voltage (Vcc): 3.3V

Resistor calculation: R = (Vcc - Vf) / If
R = (3.3V - 2.0V) / 20mA = 1.3V / 0.02A = 65Ω

Standard value: 68Ω (closest standard value, allows ~19mA - safe for LED)
"""
from circuit_synth import Component, Net, circuit


@circuit(name="LED_Blinker")
def led_blinker():
    """Simple LED circuit with current limiting resistor

    This is one of the most basic circuits in electronics, often used for:
    - Power indicators
    - Status lights
    - Debug signals
    - Learning electronics fundamentals

    Circuit topology:
           VCC_3V3
             │
            ┌┴┐ R (68Ω) - Current limiter
            └┬┘
             ├─── LED_ANODE
            ╱│╲  LED (Red)
             ├───
             │
            GND

    Current flow: VCC → Resistor → LED → GND
    """

    # Create LED (red, common 0603 SMD package)
    # LEDs are polarized: anode (+) connects to higher voltage
    led = Component(
        symbol="Device:LED",  # Generic LED symbol from Device library
        ref="D",  # Reference prefix for diodes (D1, D2, etc.)
        value="Red",  # LED color - helps identify in schematic
        footprint="LED_SMD:LED_0603_1608Metric"  # Standard 0603 SMD LED
    )

    # Create current limiting resistor
    # Without this resistor, the LED would draw too much current and burn out!
    # 68Ω limits current to ~19mA (safe for most LEDs)
    resistor = Component(
        symbol="Device:R",  # Generic resistor symbol
        ref="R",  # Reference prefix for resistors
        value="68",  # 68 Ohms - standard E24 series value
        footprint="Resistor_SMD:R_0603_1608Metric"  # Standard 0603 SMD resistor
    )

    # Define nets (electrical connections)
    vcc_3v3 = Net('VCC_3V3')     # Power supply: 3.3V
    led_anode = Net('LED_ANODE')  # Connection between resistor and LED
    gnd = Net('GND')             # Ground reference

    # Connect components
    # Current flow: VCC_3V3 → R → LED → GND

    # Resistor connections (numbered pins 1 and 2)
    resistor[1] += vcc_3v3     # R pin 1 to 3.3V power supply
    resistor[2] += led_anode   # R pin 2 to LED anode (junction point)

    # LED connections (named pins: A=anode, K=cathode)
    # Note: LEDs use named pins instead of numbers
    led["A"] += led_anode      # LED anode (positive terminal, longer leg)
    led["K"] += gnd            # LED cathode (negative terminal, shorter leg, flat edge)

    # Important: LEDs are polarized! Connecting backwards won't work (and may damage it)
    # Always connect: Higher voltage → Anode (A), Cathode (K) → Lower voltage


if __name__ == '__main__':
    # This code runs when you execute: uv run python circuit-synth/main.py

    # Generate the circuit
    circuit_obj = led_blinker()

    # Export to KiCad project files
    circuit_obj.generate_kicad_project(
        project_name="led_blinker",
        placement_algorithm="hierarchical",
        generate_pcb=True
    )

    print("✅ LED blinker circuit generated!")
    print("📁 Open in KiCad: led_blinker/led_blinker.kicad_pro")
    print()
    print("📊 Circuit Analysis:")
    print("   Supply voltage:    3.3V")
    print("   LED forward voltage: 2.0V (red)")
    print("   Resistor voltage:  1.3V")
    print("   Current draw:      ~19mA")
    print("   Power dissipation: ~25mW (resistor), ~38mW (LED)")
    print()
    print("💡 LED Color Guide:")
    print("   Red:    Vf = 1.8-2.2V")
    print("   Green:  Vf = 2.0-3.0V")
    print("   Blue:   Vf = 2.8-3.6V")
    print("   White:  Vf = 3.0-3.6V")
    print()
    print("🔧 Next Steps:")
    print("   1. Open the KiCad project")
    print("   2. Try changing the resistor value")
    print("   3. Calculate new current: I = (Vcc - Vf) / R")
    print("   4. Experiment with different LED colors")
