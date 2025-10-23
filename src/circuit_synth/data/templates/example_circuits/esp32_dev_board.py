"""ESP32-C6 Development Board - Simple Example

NOTE: This is a simplified single-file example.
For a complete hierarchical ESP32-C6 dev board with USB-C, power supply,
debug headers, and proper subcircuits, see the example_project template.

This example demonstrates:
- ESP32-C6-MINI-1 module integration
- Basic power connections
- Minimal working configuration

For production designs, add:
- USB-C interface with proper CC resistors
- 3.3V voltage regulator circuit
- Programming/debug header (USB-Serial or JTAG)
- Status LEDs
- Boot/reset buttons
"""
from circuit_synth import Component, Net, circuit


@circuit(name="ESP32_Simple")
def esp32_simple():
    """Simple ESP32-C6 minimal circuit

    This is a minimal example showing ESP32-C6-MINI-1 integration.
    For a complete development board, use the hierarchical template.

    Minimal requirements:
    - 3.3V power supply
    - Decoupling capacitors
    - Boot button for programming mode

    Missing from this simple example (add for production):
    - USB interface
    - Voltage regulator
    - Programming interface
    - Reset circuit
    """

    # ESP32-C6-MINI-1 module
    # This module includes flash, crystal, and RF components built-in
    esp32 = Component(
        symbol="RF_Module:ESP32-C6-MINI-1",
        ref="U",
        footprint="RF_Module:ESP32-C6-MINI-1"
    )

    # Decoupling capacitors for power pins
    # ESP32 modules need good decoupling for stable operation
    cap1 = Component(
        symbol="Device:C",
        ref="C",
        value="10uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )

    cap2 = Component(
        symbol="Device:C",
        ref="C",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )

    # Boot button (GPIO9 to GND) for entering programming mode
    boot_button = Component(
        symbol="Switch:SW_Push",
        ref="SW",
        footprint="Button_Switch_SMD:SW_SPST_CK_RS282G05A3"
    )

    # Define nets
    vcc_3v3 = Net('VCC_3V3')  # 3.3V power supply
    gnd = Net('GND')          # Ground
    gpio9 = Net('GPIO9')      # Boot pin

    # Connect ESP32 power pins
    # ESP32-C6-MINI-1 has VDD on pin 8
    esp32["VDD"] += vcc_3v3
    esp32["GND"] += gnd

    # Connect GPIO9 (boot pin)
    esp32["IO9"] += gpio9

    # Connect decoupling capacitors
    cap1[1] += vcc_3v3
    cap1[2] += gnd

    cap2[1] += vcc_3v3
    cap2[2] += gnd

    # Connect boot button (pull GPIO9 to GND when pressed)
    boot_button[1] += gpio9
    boot_button[2] += gnd


if __name__ == '__main__':
    # Generate KiCad project
    circuit_obj = esp32_simple()

    circuit_obj.generate_kicad_project(
        project_name="esp32_simple",
        placement_algorithm="hierarchical",
        generate_pcb=True
    )

    print("✅ ESP32-C6 simple circuit generated!")
    print("📁 Open in KiCad: esp32_simple/esp32_simple.kicad_pro")
    print()
    print("⚠️  WARNING: This is a minimal example!")
    print()
    print("📝 Missing components for a complete dev board:")
    print("   • USB-C connector with CC resistors")
    print("   • 3.3V voltage regulator (AMS1117-3.3 or similar)")
    print("   • Programming interface (USB-Serial bridge)")
    print("   • Reset button and circuit")
    print("   • Status LED")
    print("   • Additional GPIO connections")
    print()
    print("💡 For a complete hierarchical design, see:")
    print("   src/circuit_synth/data/templates/example_project/")
    print()
    print("🔧 To make this work:")
    print("   1. Add USB-C interface for power and programming")
    print("   2. Add voltage regulator for 5V→3.3V")
    print("   3. Add USB-to-Serial bridge (CH340, CP2102, etc.)")
    print("   4. Add reset button (GPIO9 + enable pin)")
