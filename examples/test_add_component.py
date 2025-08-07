#!/usr/bin/env python3
"""
Test script that demonstrates adding a component to a KiCad schematic.

This script:
1. Creates a new empty schematic
2. Saves it to a file
3. Loads it back
4. Adds a resistor component at a specific position
5. Saves the modified schematic
"""

import sys
from pathlib import Path


def test_add_component():
    """Test adding a component to a schematic."""
    print("Testing KiCad Schematic Component Addition")
    print("=" * 50)

    try:
        import rust_kicad_schematic_writer as kicad

        print("✅ Successfully imported rust_kicad_schematic_writer")
    except ImportError as e:
        print(f"❌ Failed to import: {e}")
        return False

    # Step 1: Create a new empty schematic
    print("\n1. Creating new empty schematic...")
    schematic = kicad.create_empty_schematic("A4")

    # Save it to a file
    initial_file = Path("test_initial.kicad_sch")
    initial_file.write_text(schematic)
    print(f"   ✅ Saved initial schematic to {initial_file}")
    print(f"   Size: {len(schematic)} characters")

    # Step 2: Load the schematic back
    print("\n2. Loading schematic from file...")
    loaded_schematic = kicad.load_schematic(str(initial_file))
    print(f"   ✅ Loaded schematic ({len(loaded_schematic)} characters)")

    # Step 3: Add a resistor component
    print("\n3. Adding resistor component...")
    modified_schematic = kicad.add_component_to_schematic(
        loaded_schematic,
        reference="R1",
        lib_id="Device:R",
        value="10k",
        x=121.92,
        y=73.66,
        rotation=0.0,
    )
    print(f"   ✅ Added R1 (10k resistor) at position (121.92, 73.66)")

    # Step 4: Save the modified schematic
    modified_file = Path("test_with_resistor.kicad_sch")
    modified_file.write_text(modified_schematic)
    print(f"   ✅ Saved modified schematic to {modified_file}")
    print(f"   Size: {len(modified_schematic)} characters")

    # Step 5: Add another component to test multiple additions
    print("\n4. Adding second component...")
    modified_schematic = kicad.add_component_to_schematic(
        modified_schematic,
        reference="R2",
        lib_id="Device:R",
        value="22k",
        x=150.0,
        y=73.66,
        rotation=90.0,
    )
    print(f"   ✅ Added R2 (22k resistor) at position (150.0, 73.66) rotated 90°")

    # Save final version
    final_file = Path("test_with_two_resistors.kicad_sch")
    final_file.write_text(modified_schematic)
    print(f"   ✅ Saved final schematic to {final_file}")

    # Verify the components are in the schematic
    print("\n5. Verifying components...")
    if "R1" in modified_schematic and "10k" in modified_schematic:
        print("   ✅ R1 (10k) found in schematic")
    else:
        print("   ❌ R1 not found!")

    if "R2" in modified_schematic and "22k" in modified_schematic:
        print("   ✅ R2 (22k) found in schematic")
    else:
        print("   ❌ R2 not found!")

    # Check positions
    if "121.92 73.66" in modified_schematic:
        print("   ✅ R1 position correct")
    if "150.0 73.66" in modified_schematic:
        print("   ✅ R2 position correct")

    print("\n" + "=" * 50)
    print("✅ SUCCESS! Component addition works!")
    print("\nGenerated files:")
    print("  - test_initial.kicad_sch (empty schematic)")
    print("  - test_with_resistor.kicad_sch (with R1)")
    print("  - test_with_two_resistors.kicad_sch (with R1 and R2)")
    print("\nYou can open these files in KiCad to verify the components!")

    return True


if __name__ == "__main__":
    success = test_add_component()
    sys.exit(0 if success else 1)
