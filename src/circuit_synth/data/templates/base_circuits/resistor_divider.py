"""Resistor Divider - 5V to 3.3V Logic Level Shifter

This example demonstrates:
- Creating components with Device library
- Defining nets for electrical connections
- Connecting components to nets
- Calculating resistor values for voltage division

Voltage divider formula: Vout = Vin * (R2 / (R1 + R2))
For 5V → 3.3V: R1=1kΩ, R2=2kΩ
Actual output: 5V * (2kΩ / 3kΩ) = 3.33V ✓
"""
from circuit_synth import Component, Net, circuit


@circuit(name="Resistor_Divider")
def resistor_divider():
    """5V to 3.3V voltage divider for logic level shifting

    This circuit converts 5V signals to 3.3V levels, commonly used for:
    - Arduino (5V) to ESP32 (3.3V) communication
    - Level shifting I2C, SPI, UART signals
    - Interfacing 5V sensors with 3.3V microcontrollers

    Circuit topology:
           VIN_5V
             │
            ┌┴┐ R1 (1kΩ)
            └┬┘
             ├─── VOUT_3V3 (3.33V output)
            ┌┴┐ R2 (2kΩ)
            └┬┘
             │
            GND
    """

    # Create resistors from KiCad Device library
    # The Device library provides generic passive components

    # R1 = 1kΩ (upper resistor)
    # This resistor connects between VIN and VOUT
    r1 = Component(
        symbol="Device:R",  # Generic resistor symbol
        ref="R",  # Reference prefix (will become R1, R2, etc.)
        value="1k",  # Resistance value in ohms
        footprint="Resistor_SMD:R_0603_1608Metric"  # 0603 SMD package
    )

    # R2 = 2kΩ (lower resistor)
    # This resistor connects between VOUT and GND
    r2 = Component(
        symbol="Device:R",
        ref="R",
        value="2k",  # 2000 ohms
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    # Define electrical nets (connections)
    # Nets represent wires/traces that connect component pins
    vin_5v = Net('VIN_5V')      # Input: 5V from source
    vout_3v3 = Net('VOUT_3V3')  # Output: 3.3V to destination
    gnd = Net('GND')            # Ground reference (0V)

    # Connect resistors to form voltage divider
    # The += operator connects a component pin to a net
    # For resistors, pins are numbered 1 and 2

    r1[1] += vin_5v    # R1 pin 1 connects to 5V input
    r1[2] += vout_3v3  # R1 pin 2 connects to output (junction point)
    r2[1] += vout_3v3  # R2 pin 1 connects to output (junction point)
    r2[2] += gnd       # R2 pin 2 connects to ground

    # Note: R1[2] and R2[1] both connect to VOUT_3V3
    # This creates the junction between the two resistors


if __name__ == '__main__':
    # This code runs when you execute: uv run python circuit-synth/main.py

    # Generate the circuit
    circuit_obj = resistor_divider()

    # Export to KiCad project files
    circuit_obj.generate_kicad_project(
        project_name="resistor_divider",  # Name for KiCad project files
        placement_algorithm="hierarchical",  # Simple placement for small circuits
        generate_pcb=True  # Also create PCB file (.kicad_pcb)
    )

    print("✅ Resistor divider circuit generated!")
    print("📁 Open in KiCad: resistor_divider/resistor_divider.kicad_pro")
    print()
    print("📊 Circuit Analysis:")
    print("   Input voltage:  5.0V (VIN_5V)")
    print("   Output voltage: 3.33V (VOUT_3V3)")
    print("   Current draw:   1.67mA (when loaded)")
    print()
    print("💡 Next Steps:")
    print("   1. Open the .kicad_pro file in KiCad")
    print("   2. View the schematic (F5)")
    print("   3. Inspect component values and connections")
    print("   4. Try modifying resistor values to get different output voltages")
