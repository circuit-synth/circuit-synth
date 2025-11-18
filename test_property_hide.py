from circuit_synth import circuit, Component, Net

@circuit(name="Property_Hide_Test")
def test_circuit():
    """
    Simple test circuit to verify property hiding.
    Should only show Reference and Value in KiCad.
    """

    # Resistor with value and footprint
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    # Another resistor
    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="1k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    # Capacitor
    c1 = Component(
        symbol="Device:C",
        ref="C1",
        value="10uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )

    # Create nets
    vcc = Net('VCC')
    gnd = Net('GND')
    output = Net('OUT')

    # Connect components (simple voltage divider)
    r1[1] += vcc
    r1[2] += output

    r2[1] += output
    r2[2] += gnd

    c1[1] += output
    c1[2] += gnd


if __name__ == "__main__":
    # Generate the circuit
    result = test_circuit()

    # Generate KiCad project files
    result.generate_kicad_project(
        project_name="Property_Hide_Test",
        placement_algorithm="hierarchical",
        generate_pcb=False
    )

    print("✓ Test circuit generated successfully!")
    print(f"  Project: Property_Hide_Test/Property_Hide_Test.kicad_pro")
    print(f"\nInspect the schematic to verify only Reference and Value are visible.")
