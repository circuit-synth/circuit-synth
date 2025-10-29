#!/usr/bin/env python3
"""
Circuit with intentional ERC violations for test 55.

This circuit demonstrates common ERC errors:
1. Output-to-output conflict (U1 output + U2 output on same net)
2. Undriven input (U3 input not connected to any driver)
3. Unconnected power pin (U4 VCC not connected)

For Step 4 of the test, violations will be fixed:
- Change U2 to input type (resolves conflict)
- Connect U3 input to valid driver
- Connect U4 VCC to power net

This validates KiCad ERC integration and circuit-synth's ability
to generate ERC-clean circuits after fixes.
"""

from circuit_synth import circuit, Component, Net


@circuit(name="erc_test_circuit")
def erc_test_circuit():
    """Create circuit with intentional ERC violations."""

    # Create components for ERC testing
    # Using 74HC04 inverters as they have defined pin types

    # U1: Output driver (will conflict with U2)
    u1 = Component(
        symbol="74xx:74HC04",
        ref="U1",
        value="74HC04",
        footprint="Package_SO:SOIC-14_3.9x8.7mm_P1.27mm",
        unit=1,
    )

    # U2: Another output driver (creates output-output conflict)
    # Note: For step 4, this will be changed to input type
    # Uncomment below to fix:
    # u2 = Component(
    #     symbol="74xx:74HC14",  # Schmitt trigger (input type)
    #     ref="U2",
    #     value="74HC14",
    #     footprint="Package_SO:SOIC-14_3.9x8.7mm_P1.27mm",
    #     unit=1,
    # )
    u2 = Component(
        symbol="74xx:74HC04",  # Inverter (output type, creates conflict)
        ref="U2",
        value="74HC04",
        footprint="Package_SO:SOIC-14_3.9x8.7mm_P1.27mm",
        unit=1,
    )

    # U3: Component with undriven input
    u3 = Component(
        symbol="74xx:74HC04",
        ref="U3",
        value="74HC04",
        footprint="Package_SO:SOIC-14_3.9x8.7mm_P1.27mm",
        unit=1,
    )

    # U4: Component with unconnected power pin
    u4 = Component(
        symbol="74xx:74HC04",
        ref="U4",
        value="74HC04",
        footprint="Package_SO:SOIC-14_3.9x8.7mm_P1.27mm",
        unit=1,
    )

    # Create ERC violation 1: Output-to-output conflict
    # Both U1 output (pin 2) and U2 output (pin 2) drive same net
    conflict_net = Net("CONFLICT_NET")
    u1[2] += conflict_net  # U1 output
    u2[2] += conflict_net  # U2 output (CONFLICT!)

    # ERC violation 2: Undriven input
    # U3 input (pin 1) is not connected to any driver
    # (intentionally left unconnected)

    # Note: For step 4, uncomment to fix:
    # driver_net = Net("DRIVEN_NET")
    # u1[4] += driver_net  # U1 has another output (pin 4)
    # u3[1] += driver_net  # Connect U3 input to driver

    # ERC violation 3: Unconnected power pin
    # U4 VCC (pin 14) is not connected to power
    # Other components will have power connected

    # Connect power to U1, U2, U3 (but NOT U4)
    vcc = Net("VCC")
    gnd = Net("GND")

    u1[14] += vcc  # U1 VCC
    u1[7] += gnd   # U1 GND

    u2[14] += vcc  # U2 VCC
    u2[7] += gnd   # U2 GND

    u3[14] += vcc  # U3 VCC
    u3[7] += gnd   # U3 GND

    # U4 VCC and GND intentionally NOT connected (ERC violation 3)
    # Note: For step 4, uncomment to fix:
    # u4[14] += vcc  # U4 VCC
    # u4[7] += gnd   # U4 GND


if __name__ == "__main__":
    circuit_obj = erc_test_circuit()
    circuit_obj.generate_kicad_project(project_name="circuit_with_erc_errors")
    print("Generated circuit with ERC violations")
    print("Run ERC to detect:")
    print("  1. Output-to-output conflict (U1 + U2 → CONFLICT_NET)")
    print("  2. Undriven input (U3 pin 1)")
    print("  3. Unconnected power pin (U4 VCC)")
