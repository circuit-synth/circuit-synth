#!/usr/bin/env python3
"""
LED subcircuit test with hierarchical ports.

Demonstrates hierarchical pin connections:
- Parent circuit has VCC, GND power nets
- LED_Driver subcircuit requires VCC, GND via hierarchical ports
- Hierarchical labels in subcircuit connect to hierarchical pins on sheet symbol

This fixture is modified by the test to add/remove hierarchical ports dynamically.
"""

from circuit_synth import circuit, Component, Net, Circuit


@circuit(name="led_subcircuit")
def led_subcircuit():
    """Create LED subcircuit with hierarchical ports."""
    from circuit_synth.core.decorators import get_current_circuit

    root = get_current_circuit()

    # Create power nets in parent circuit context
    vcc = Net("VCC")
    gnd = Net("GND")

    # START_MARKER: Test will modify between these markers to add new signals
    # END_MARKER

    # Create LED_Driver subcircuit (child circuit)
    led_driver = Circuit("LED_Driver")

    # Add LED to subcircuit that requires power
    led = Component(
        symbol="Device:LED",
        ref="D1",
        value="Red",
        footprint="LED_SMD:LED_0603_1608Metric",
    )

    # Add current-limiting resistor in subcircuit
    resistor = Component(
        symbol="Device:R",
        ref="R1",
        value="330",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    led_driver.add_component(led)
    led_driver.add_component(resistor)

    # Create matching nets in subcircuit for hierarchical connection
    # Nets with same name in parent and child create hierarchical labels/pins
    vcc_child = Net("VCC")
    gnd_child = Net("GND")

    # Connect LED and resistor inside subcircuit to hierarchical port nets
    # These connections will create hierarchical labels in the subcircuit
    led[1] += vcc_child  # LED anode to VCC (hierarchical label)
    led[2] += resistor[1]  # LED cathode to resistor
    resistor[2] += gnd_child  # Resistor to GND (hierarchical label)

    # Add subcircuit to root circuit
    # This creates:
    # 1. Hierarchical labels (VCC, GND) in LED_Driver.kicad_sch
    # 2. Sheet symbol in parent with hierarchical pins (VCC, GND)
    # 3. Connections between parent nets and sheet pins
    root.add_subcircuit(led_driver)


def main():
    """Generate KiCad project from circuit."""
    # Create the circuit
    root = led_subcircuit()

    # Generate KiCad project
    print(f"Generating KiCad project: led_subcircuit")
    print(f"  Parent circuit: {root.name}")
    print(f"  Subcircuit: LED_Driver")
    print(f"  Hierarchical ports: VCC, GND")
    print(f"  Components in subcircuit: D1 (LED), R1 (resistor)")

    root.generate_kicad_project("led_subcircuit", force_regenerate=True)

    print(f"\n✅ Project generated successfully!")
    print(f"   Expected hierarchical structure:")
    print(f"   - Parent: led_subcircuit.kicad_sch (with sheet symbol)")
    print(f"   - Subcircuit: LED_Driver.kicad_sch (with hierarchical labels)")
    print(f"   - Sheet symbol should have pins: VCC, GND")
    print(f"   - Subcircuit should have hierarchical labels: VCC, GND")


if __name__ == "__main__":
    main()
