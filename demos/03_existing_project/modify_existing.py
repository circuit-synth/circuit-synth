#!/usr/bin/env python3
"""
Existing Project Integration Demo

This script demonstrates how to:
1. Import an existing KiCad project
2. Add new functionality in Python
3. Sync changes back to KiCad

The example adds an I2C temperature sensor to an existing LED blinker circuit.
"""

from circuit_synth import *
from circuit_synth.io import import_kicad_project


def demo_existing_project_integration():
    """Demonstrate bidirectional KiCad ↔ Python workflow"""

    print("=== Existing Project Integration Demo ===")
    print()

    # Step 1: Import existing KiCad project
    print("📂 Importing existing KiCad project...")
    try:
        # Import the simple LED circuit
        existing_circuit = import_kicad_project("before/simple_led.kicad_sch")
        print("✅ Successfully imported existing circuit")
        print(f"   Found {len(existing_circuit.components)} existing components")
    except FileNotFoundError:
        print("⚠️  Creating example circuit (existing project simulation)")
        existing_circuit = create_example_led_circuit()

    # Step 2: Add new functionality using circuit-synth
    print("🔧 Adding I2C temperature sensor functionality...")

    @circuit(name="Sensor_Interface")
    def add_temperature_sensor(vcc, gnd, sda, scl):
        """Add I2C temperature sensor to existing design"""

        # DS18B20 temperature sensor
        temp_sensor = Component(
            symbol="Sensor_Temperature:DS18B20",
            ref="U",
            footprint="Package_TO_SOT_THT:TO-92_Inline",
        )

        # I2C pull-up resistors (required for I2C bus)
        pullup_sda = Component(
            symbol="Device:R",
            ref="R",
            value="4.7k",
            footprint="Resistor_SMD:R_0603_1608Metric",
        )

        pullup_scl = Component(
            symbol="Device:R",
            ref="R",
            value="4.7k",
            footprint="Resistor_SMD:R_0603_1608Metric",
        )

        # Sensor connections
        temp_sensor["VDD"] += vcc
        temp_sensor["GND"] += gnd
        temp_sensor["DQ"] += sda  # One-wire data line

        # Pull-up resistor connections
        pullup_sda[1] += vcc
        pullup_sda[2] += sda
        pullup_scl[1] += vcc
        pullup_scl[2] += scl

        print("   ✅ Added DS18B20 temperature sensor")
        print("   ✅ Added I2C pull-up resistors")

        return temp_sensor

    # Get existing nets from the imported circuit
    vcc_net = existing_circuit.get_net("VCC_3V3")
    gnd_net = existing_circuit.get_net("GND")

    # Create new I2C nets
    i2c_sda = Net("I2C_SDA")
    i2c_scl = Net("I2C_SCL")

    # Add the sensor circuit to existing design
    sensor_circuit = add_temperature_sensor(vcc_net, gnd_net, i2c_sda, i2c_scl)
    existing_circuit.add_subcircuit(sensor_circuit)

    print("🔄 Integrated sensor with existing LED circuit")

    # Step 3: Generate updated KiCad files
    print("💾 Generating updated KiCad project...")

    existing_circuit.generate_kicad_project(
        project_name="enhanced_led_with_sensor",
        placement_algorithm="preserve_existing",  # Keep original placements
        generate_pcb=True,
    )

    print()
    print("✅ Project integration complete!")
    print()
    print("Generated files:")
    print("   📁 enhanced_led_with_sensor/")
    print("      ├── enhanced_led_with_sensor.kicad_pro")
    print("      ├── enhanced_led_with_sensor.kicad_sch")
    print("      ├── enhanced_led_with_sensor.kicad_pcb")
    print("      └── Sensor_Interface.kicad_sch")
    print()
    print("Changes made:")
    print("   ➕ Added DS18B20 temperature sensor")
    print("   ➕ Added I2C pull-up resistors")
    print("   ➕ Created new hierarchical sensor sheet")
    print("   ✅ Preserved existing LED circuit")
    print("   ✅ Maintained original component references")
    print()
    print("Open enhanced_led_with_sensor.kicad_pro to see the integrated design!")


def create_example_led_circuit():
    """Create a simple LED circuit to simulate existing project"""

    @circuit(name="Simple_LED")
    def led_circuit():
        # Simple LED + resistor circuit
        led = Component(
            symbol="Device:LED", ref="D", footprint="LED_SMD:LED_0805_2012Metric"
        )

        resistor = Component(
            symbol="Device:R",
            ref="R",
            value="330",
            footprint="Resistor_SMD:R_0603_1608Metric",
        )

        # Power nets
        vcc = Net("VCC_3V3")
        gnd = Net("GND")

        # Connections
        resistor[1] += vcc
        resistor[2] += led["A"]  # Anode
        led["K"] += gnd  # Cathode

        return led_circuit

    return led_circuit()


if __name__ == "__main__":
    demo_existing_project_integration()
