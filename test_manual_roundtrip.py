#!/usr/bin/env python3
"""
Interactive Manual Round-Trip Test

This script guides you through manually verifying the round-trip update system:
1. Generate initial KiCad project with circuit-synth
2. Opens KiCad for you to inspect
3. Programmatically modifies schematic with kicad-sch-api (moves component)
4. Re-runs circuit-synth (should preserve the modification)
5. Opens KiCad again for you to verify the change was preserved
"""

import subprocess
import sys
import time
from pathlib import Path

from circuit_synth import Component, Net, circuit
import kicad_sch_api as ksa
from kicad_sch_api.core.types import Point


def open_kicad(project_path: Path, project_name: str):
    """Open KiCad project."""
    # Look for the .kicad_pro file - try both project_path and parent
    kicad_pro_locations = [
        project_path / f"{project_name}.kicad_pro",
        project_path.parent / f"{project_name}.kicad_pro",
        Path.cwd() / f"{project_name}.kicad_pro",
    ]

    kicad_pro = None
    for loc in kicad_pro_locations:
        if loc.exists():
            kicad_pro = loc
            break

    if not kicad_pro:
        print(f"✗ Project file not found. Tried:")
        for loc in kicad_pro_locations:
            print(f"  - {loc}")
        return False

    print(f"\n📂 Opening KiCad project: {kicad_pro}")
    try:
        subprocess.Popen(['open', str(kicad_pro)])
        return True
    except Exception as e:
        print(f"✗ Failed to open KiCad: {e}")
        return False


def wait_for_user(message: str):
    """Wait for user to press Enter."""
    input(f"\n⏸️  {message}\nPress Enter when ready to continue...")


def main():
    print("=" * 80)
    print("INTERACTIVE MANUAL ROUND-TRIP TEST")
    print("=" * 80)
    print("\nThis test will:")
    print("  1. Generate a simple circuit with circuit-synth")
    print("  2. Open it in KiCad for you to inspect")
    print("  3. Programmatically move R1 using kicad-sch-api")
    print("  4. Re-run circuit-synth (should preserve the move)")
    print("  5. Open KiCad again for you to verify")

    wait_for_user("Ready to start?")

    # Setup output directory - use current directory to match circuit-synth behavior
    project_name = "test_manual_roundtrip"
    output_dir = Path.cwd() / project_name

    # =================================================================
    # STEP 1: Generate initial circuit
    # =================================================================
    print("\n" + "=" * 80)
    print("STEP 1: Generating initial circuit with circuit-synth")
    print("=" * 80)

    @circuit(name="test_manual_roundtrip")
    def simple_circuit():
        """A simple resistor divider for testing"""
        r1 = Component("Device:R", ref="R1", value="10k",
                      footprint="Resistor_SMD:R_0603_1608Metric")
        r2 = Component("Device:R", ref="R2", value="10k",
                      footprint="Resistor_SMD:R_0603_1608Metric")
        vcc = Net('VCC')
        gnd = Net('GND')
        mid = Net('MID')

        r1[1] += vcc
        r1[2] += mid
        r2[1] += mid
        r2[2] += gnd

        return r1, r2

    c = simple_circuit()

    try:
        # Disable PCB generation to avoid errors
        c.generate_kicad_project(str(output_dir), force_regenerate=True, generate_pcb=False)
        print("✓ Initial generation completed")
    except Exception as e:
        print(f"✗ Generation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # List what was actually created
    print(f"\n📁 Contents of {output_dir}:")
    if output_dir.exists():
        for item in sorted(output_dir.iterdir()):
            print(f"   - {item.name}")

    # Try to find the schematic file - circuit-synth creates it at project_name level
    possible_sch_paths = [
        output_dir / f"{project_name}.kicad_sch",
        Path.cwd() / f"{project_name}.kicad_sch",
        output_dir.parent / f"{project_name}.kicad_sch",
    ]

    sch_path = None
    for path in possible_sch_paths:
        if path.exists():
            sch_path = path
            print(f"✓ Found schematic at: {sch_path}")
            break

    if not sch_path:
        print(f"\n✗ Schematic not found. Tried:")
        for path in possible_sch_paths:
            print(f"   - {path}")
        return 1

    # =================================================================
    # STEP 2: Open in KiCad for inspection
    # =================================================================
    print("\n" + "=" * 80)
    print("STEP 2: Opening KiCad for initial inspection")
    print("=" * 80)
    print("\nLook at the schematic layout, especially:")
    print("  - Position of R1 and R2")
    print("  - Net connections")

    if not open_kicad(output_dir, project_name):
        return 1

    wait_for_user("Inspect the schematic, then CLOSE KiCad")

    # =================================================================
    # STEP 3: Programmatically modify with kicad-sch-api
    # =================================================================
    print("\n" + "=" * 80)
    print("STEP 3: Modifying schematic with kicad-sch-api")
    print("=" * 80)

    try:
        # Load schematic
        sch = ksa.Schematic.load(str(sch_path))
        print(f"✓ Loaded schematic with {len(sch.components)} components")

        # Find R1 - components is a ComponentCollection with .get() method
        r1 = sch.components.get("R1")
        if not r1:
            print("✗ R1 not found")
            return 1

        original_pos = r1.position
        print(f"\n📍 R1 original position: ({original_pos.x:.2f}, {original_pos.y:.2f})")

        # Move R1 to a very obvious new position
        new_pos = Point(180.0, 120.0)
        r1.position = new_pos
        print(f"📍 Moving R1 to: ({new_pos.x:.2f}, {new_pos.y:.2f})")
        print(f"   Δx = {new_pos.x - original_pos.x:.2f}mm, Δy = {new_pos.y - original_pos.y:.2f}mm")

        # Save with format preservation
        sch.save(str(sch_path), preserve_format=True)
        print("✓ Saved modified schematic")

    except Exception as e:
        print(f"✗ Failed to modify schematic: {e}")
        import traceback
        traceback.print_exc()
        return 1

    print("\n⚠️  IMPORTANT: R1 has been moved to a new position programmatically")
    print("   The next step will test if circuit-synth preserves this change")

    wait_for_user("Ready to re-run circuit-synth?")

    # =================================================================
    # STEP 4: Re-run circuit-synth (should preserve modification)
    # =================================================================
    print("\n" + "=" * 80)
    print("STEP 4: Re-running circuit-synth (UPDATE MODE)")
    print("=" * 80)
    print("\n⚙️  Re-generating with force_regenerate=False")
    print("   This should trigger the UPDATE path, preserving R1's new position")

    # Same circuit, but we'll verify the value stays at 10k
    c2 = simple_circuit()

    try:
        c2.generate_kicad_project(str(output_dir), force_regenerate=False, generate_pcb=False)
        print("✓ Update completed")
    except Exception as e:
        print(f"✗ Update failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # =================================================================
    # STEP 5: Verify programmatically
    # =================================================================
    print("\n" + "=" * 80)
    print("STEP 5: Verifying preservation programmatically")
    print("=" * 80)

    try:
        sch_after = ksa.Schematic.load(str(sch_path))
        r1_after = sch_after.components.get("R1")

        if not r1_after:
            print("✗ R1 not found after update")
            return 1

        print(f"\n📍 R1 position after update: ({r1_after.position.x:.2f}, {r1_after.position.y:.2f})")

        # Check if position was preserved (allow small floating point difference)
        pos_preserved = (
            abs(r1_after.position.x - new_pos.x) < 0.01 and
            abs(r1_after.position.y - new_pos.y) < 0.01
        )

        if pos_preserved:
            print("✅ SUCCESS: R1 position was PRESERVED!")
            print(f"   Expected: ({new_pos.x:.2f}, {new_pos.y:.2f})")
            print(f"   Got:      ({r1_after.position.x:.2f}, {r1_after.position.y:.2f})")
        else:
            print("❌ FAILURE: R1 position was NOT preserved!")
            print(f"   Expected: ({new_pos.x:.2f}, {new_pos.y:.2f})")
            print(f"   Got:      ({r1_after.position.x:.2f}, {r1_after.position.y:.2f})")
            print("\n⚠️  The update system is broken!")

    except Exception as e:
        print(f"✗ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # =================================================================
    # STEP 6: Open in KiCad for visual verification
    # =================================================================
    print("\n" + "=" * 80)
    print("STEP 6: Opening KiCad for VISUAL VERIFICATION")
    print("=" * 80)
    print("\n👀 Visual Check:")
    print("   - Is R1 at the NEW position (180, 120)?")
    print("   - Or did it reset to the original position?")

    if not open_kicad(output_dir, project_name):
        return 1

    wait_for_user("Visually verify R1's position, then close KiCad")

    # =================================================================
    # Summary
    # =================================================================
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

    if pos_preserved:
        print("\n✅ Programmatic check PASSED: Position was preserved")
        print("\n❓ Did the VISUAL check also confirm R1 is at the new position?")
        response = input("   Type 'yes' if R1 was visibly at the moved position: ").strip().lower()

        if response == 'yes':
            print("\n🎉 COMPLETE SUCCESS! Round-trip preservation works!")
            print("\n✓ Position preservation verified programmatically")
            print("✓ Position preservation verified visually")
            print("\nThe update system is working correctly!")
        else:
            print("\n⚠️  Discrepancy: Programmatic check passed but visual check failed")
            print("   This could indicate a display issue or the file wasn't reloaded")
    else:
        print("\n❌ TEST FAILED: Position was not preserved")
        print("\nThe update system needs debugging!")

    print("\n" + "=" * 80)
    print(f"\nTest files saved in: {output_dir}")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
