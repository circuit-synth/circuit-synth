#!/usr/bin/env python3
"""
Circuit with intentional ERC violations for test 54.

This circuit demonstrates 2 common ERC violations:
1. Unconnected input pin (floating op-amp input)
2. Missing footprint (resistor without PCB footprint)

Usage:
    uv run circuit_with_violations.py

To fix violations, set FIX_VIOLATIONS = True
"""
from circuit_synth import *

# Toggle to generate circuit with violations fixed
FIX_VIOLATIONS = False


@circuit(name="circuit_with_violations")
def circuit_with_violations():
    """Circuit with intentional ERC violations."""

    # =========================================================================
    # VIOLATION 1: Unconnected pin (floating input on logic gate)
    # =========================================================================
    # Use a simple logic gate with unconnected input
    # 74HC00 NAND gate - 4 gates in one package
    gate = Component(
        symbol="74xx:74HC00",
        ref="U1",
        value="74HC00",
        footprint="Package_SO:SOIC-14_3.9x8.7mm_P1.27mm"  # Has footprint
    )

    # Connect one input of first NAND gate (pin 1)
    input_a = Net("INPUT_A")
    gate[1] += input_a

    # Pin 2 (second input) intentionally left UNCONNECTED
    # This creates VIOLATION 1: Unconnected input pin

    # Connect output (pin 3)
    gate_out = Net("GATE_OUT")
    gate[3] += gate_out

    if FIX_VIOLATIONS:
        # FIX: Connect floating input to something (e.g., tie to input_a or GND)
        gate[2] += input_a  # Tie both inputs together

    # =========================================================================
    # Power and Ground connections
    # =========================================================================
    # Connect power (VCC is pin 14 on 74HC00)
    vcc = Net("VCC")
    gate[14] += vcc

    # Connect GND (GND is pin 7 on 74HC00)
    gnd = Net("GND")
    gate[7] += gnd

    # =========================================================================
    # VIOLATION 2: Missing footprint (resistor without PCB footprint)
    # =========================================================================
    # Resistor with NO footprint assigned
    if FIX_VIOLATIONS:
        # With footprint
        resistor = Component(
            symbol="Device:R",
            ref="R1",
            value="10k",
            footprint="Resistor_SMD:R_0603_1608Metric"
        )
    else:
        # Without footprint - VIOLATION 2
        resistor = Component(
            symbol="Device:R",
            ref="R1",
            value="10k"
            # footprint intentionally NOT set
        )

    # Connect resistor to gate output
    resistor[1] += gate_out
    resistor[2] += gnd


if __name__ == "__main__":
    circuit_obj = circuit_with_violations()
    circuit_obj.generate_kicad_project(
        project_name="circuit_with_violations",
        placement_algorithm="simple",
        generate_pcb=True
    )

    violation_status = "FIXED" if FIX_VIOLATIONS else "WITH VIOLATIONS"
    print(f"\n✅ Circuit generated ({violation_status})")
    print(f"   Output: circuit_with_violations/circuit_with_violations.kicad_sch")

    if not FIX_VIOLATIONS:
        print(f"\n⚠️  Expected ERC Violations:")
        print(f"   1. Unconnected pin: U1 pin 2 (floating NAND input)")
        print(f"   2. Missing footprint: R1 (warning)")
        print(f"\nTo fix violations, set FIX_VIOLATIONS = True")
    else:
        print(f"\n✅ All violations fixed!")
        print(f"   - U1 pin 2 connected to INPUT_A net")
        print(f"   - R1 has footprint assigned")
