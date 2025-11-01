#!/usr/bin/env python3
"""
Initial voltage regulator circuit for test 64.

Step 1: Simple voltage regulator with input/output capacitors.
This is the starting point for the iterative design process.
"""

from circuit_synth import circuit, Component


@circuit(name="voltage_regulator")
def voltage_regulator():
    """Create initial voltage regulator circuit.

    Simple design:
    - C1: Input capacitor (100uF)
    - U1: Voltage regulator (using resistor as placeholder)
    - C2: Output capacitor (10uF)

    Additional components (commented out for iterative testing):
    - D1: Protection diode (added in Step 3)
    - D2: LED indicator (added in Step 5)
    - R1: LED resistor (added in Step 5)
    """
    # Input capacitor
    c1 = Component(
        symbol="Device:C",
        ref="C1",
        value="100uF",
        footprint="Capacitor_SMD:C_0805_2012Metric",
    )

    # Voltage regulator (using resistor as placeholder)
    u1 = Component(
        symbol="Device:R",
        ref="U1",
        value="100",
        footprint="Resistor_SMD:R_0805_2012Metric",
    )

    # Output capacitor
    c2 = Component(
        symbol="Device:C",
        ref="C2",
        value="10uF",
        footprint="Capacitor_SMD:C_0603_1608Metric",
    )

    # STEP 3: Protection diode (uncommented by test)
    # d1 = Component(
    #     symbol="Device:D",
    #     ref="D1",
    #     value="1N4007",
    #     footprint="Diode_SMD:D_SOD-123",
    # )

    # STEP 5: LED indicator and resistor (uncommented by test)
    # d2 = Component(
    #     symbol="Device:LED",
    #     ref="D2",
    #     value="RED",
    #     footprint="LED_SMD:LED_0603_1608Metric",
    # )
    #
    # r1 = Component(
    #     symbol="Device:R",
    #     ref="R1",
    #     value="1k",
    #     footprint="Resistor_SMD:R_0603_1608Metric",
    # )


if __name__ == "__main__":
    # Generate KiCad project when run directly
    circuit_obj = voltage_regulator()

    circuit_obj.generate_kicad_project(
        project_name="voltage_regulator",
        placement_algorithm="simple",
        generate_pcb=True,
    )

    print("✅ Voltage regulator circuit generated successfully!")
    print(f"📁 Open in KiCad: voltage_regulator/voltage_regulator.kicad_pro")
    print(f"Components: {len(circuit_obj.components)}")
    print(f"Nets: {len(circuit_obj.nets)}")
