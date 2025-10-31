#!/usr/bin/env python3
"""
Test 2: Nested resistor dividers - minimal hierarchical test

Creates a two-level hierarchy:
  Root Circuit
    └─ Divider_Level1 (subcircuit with resistor divider)
         └─ Divider_Level2 (nested subcircuit with another resistor divider)

This tests hierarchical label generation at multiple levels:
- Level 1 should have hierarchical labels for VIN, VOUT, GND
- Level 2 should have hierarchical labels for VIN2, VOUT2, GND
- Labels should be visible and connected in KiCad schematics
"""

from circuit_synth import Circuit, Component, Net, circuit


@circuit
def main():
    print("=" * 70)
    print("Test 2: Nested Resistor Divider Subcircuits")
    print("=" * 70)

    # =========================================================================
    # ROOT CIRCUIT
    # =========================================================================
    root = Circuit("nested_dividers")
    print(f"\n1. Created root circuit: {root.name}")

    # Create nets in root circuit
    vin_root = Net("VIN")
    gnd_root = Net("GND")
    vout_root = Net("VOUT_FROM_LEVEL1")

    print(f"   Root nets: VIN, GND, VOUT_FROM_LEVEL1")

    # =========================================================================
    # LEVEL 1 SUBCIRCUIT - First Resistor Divider
    # =========================================================================
    divider_level1 = Circuit("Divider_Level1")
    print(f"\n2. Created Level 1 subcircuit: {divider_level1.name}")

    # Add two resistors for voltage divider
    r1_level1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    r2_level1 = Component(
        symbol="Device:R",
        ref="R2",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    divider_level1.add_component(r1_level1)
    divider_level1.add_component(r2_level1)

    # Create local net for divider output
    vout_level1 = Net("VOUT1")

    # Connect resistor divider:
    # VIN ---[R1]--- VOUT1 ---[R2]--- GND
    r1_level1[1] += vin_root  # R1 pin 1 to VIN (from root)
    r1_level1[2] += vout_level1  # R1 pin 2 to VOUT1 (local)

    r2_level1[1] += vout_level1  # R2 pin 1 to VOUT1 (local)
    r2_level1[2] += gnd_root  # R2 pin 2 to GND (from root)

    print(f"   Level 1 components: R1 (10k), R2 (10k)")
    print(f"   Level 1 connections:")
    print(f"     - R1[1] → VIN (hierarchical from root)")
    print(f"     - R1[2] → VOUT1 (local)")
    print(f"     - R2[1] → VOUT1 (local)")
    print(f"     - R2[2] → GND (hierarchical from root)")

    # =========================================================================
    # LEVEL 2 SUBCIRCUIT - Nested Resistor Divider
    # =========================================================================
    divider_level2 = Circuit("Divider_Level2")
    print(f"\n3. Created Level 2 subcircuit: {divider_level2.name}")

    # Add two resistors for second voltage divider
    r3_level2 = Component(
        symbol="Device:R",
        ref="R3",
        value="5k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    r4_level2 = Component(
        symbol="Device:R",
        ref="R4",
        value="5k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    divider_level2.add_component(r3_level2)
    divider_level2.add_component(r4_level2)

    # Create local net for second divider output
    vout_level2 = Net("VOUT2")

    # Connect second resistor divider:
    # VOUT1 ---[R3]--- VOUT2 ---[R4]--- GND
    r3_level2[1] += vout_level1  # R3 pin 1 to VOUT1 (from Level 1)
    r3_level2[2] += vout_level2  # R3 pin 2 to VOUT2 (local)

    r4_level2[1] += vout_level2  # R4 pin 1 to VOUT2 (local)
    r4_level2[2] += gnd_root  # R4 pin 2 to GND (from root)

    print(f"   Level 2 components: R3 (5k), R4 (5k)")
    print(f"   Level 2 connections:")
    print(f"     - R3[1] → VOUT1 (hierarchical from Level 1)")
    print(f"     - R3[2] → VOUT2 (local)")
    print(f"     - R4[1] → VOUT2 (local)")
    print(f"     - R4[2] → GND (hierarchical from root)")

    # =========================================================================
    # NEST SUBCIRCUITS
    # =========================================================================

    # Add Level 2 into Level 1
    # Nets are already connected via component pins
    divider_level1.add_subcircuit(divider_level2)
    print(f"\n4. Nested Level 2 inside Level 1")
    print(f"   Hierarchical connections via nets: VOUT1, GND")

    # Add Level 1 into Root
    # Nets are already connected via component pins
    root.add_subcircuit(divider_level1)
    print(f"\n5. Added Level 1 to Root")
    print(f"   Hierarchical connections via nets: VIN, GND, VOUT1")

    # =========================================================================
    # GENERATE KICAD PROJECT
    # =========================================================================
    print(f"\n6. Generating KiCad project...")

    root.generate_kicad_project("test2_nested_output", force_regenerate=True)

    print(f"\n{'=' * 70}")
    print(f"✅ PROJECT GENERATED SUCCESSFULLY!")
    print(f"{'=' * 70}")
    print(f"\nExpected hierarchical structure:")
    print(f"  📁 Root: nested_dividers.kicad_sch")
    print(f"     └─ 📄 Sheet: Divider_Level1")
    print(f"         - Hierarchical pins: VIN, GND, VOUT1")
    print(f"         └─ 📁 Divider_Level1.kicad_sch")
    print(f"             - Hierarchical labels: VIN, GND (input)")
    print(f"             - Hierarchical labels: VOUT1 (output)")
    print(f"             - Components: R1, R2")
    print(f"             └─ 📄 Sheet: Divider_Level2")
    print(f"                 - Hierarchical pins: VOUT1, GND")
    print(f"                 └─ 📁 Divider_Level2.kicad_sch")
    print(f"                     - Hierarchical labels: VOUT1, GND (input)")
    print(f"                     - Components: R3, R4")
    print(f"\n🔍 TO VERIFY:")
    print(f"   1. Check Divider_Level1.kicad_sch for hierarchical labels")
    print(f"   2. Check Divider_Level2.kicad_sch for hierarchical labels")
    print(f"   3. Labels should be connected to resistor pins with wires")
    print(f"   4. Check JSON for 'nodes' arrays in nets")


if __name__ == "__main__":
    main()
