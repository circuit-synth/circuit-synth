#!/usr/bin/env python3
"""
Automated Round-Trip Test (no user interaction)

This verifies the fix works programmatically without needing KiCad or user input.
Tests that component positions are preserved across updates.
"""

import sys
import tempfile
from pathlib import Path

from circuit_synth import Component, Net, circuit
import kicad_sch_api as ksa
from kicad_sch_api.core.types import Point


def test_roundtrip():
    """Test round-trip preservation automatically."""
    print("=" * 80)
    print("AUTOMATED ROUND-TRIP TEST")
    print("=" * 80)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "test_auto"
        output_dir.mkdir()

        # Step 1: Generate initial circuit
        print("\n[1] Generating initial circuit...")

        @circuit(name="test_auto")
        def simple_circuit():
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
            c.generate_kicad_project(str(output_dir), force_regenerate=True, generate_pcb=False)
            print("   ✓ Generated")
        except Exception as e:
            print(f"   ✗ Failed: {e}")
            return False

        # Find schematic - circuit-synth creates at parent level
        possible_paths = [
            output_dir / "test_auto.kicad_sch",
            Path(tmpdir) / "test_auto.kicad_sch",
        ]

        sch_path = None
        for path in possible_paths:
            if path.exists():
                sch_path = path
                break

        if not sch_path:
            print(f"   ✗ Schematic not found. Tried:")
            for p in possible_paths:
                print(f"     - {p}")
            return False
        print(f"   ✓ Found schematic at {sch_path}")

        # Step 2: Modify with kicad-sch-api
        print("\n[2] Modifying schematic (moving R1)...")

        try:
            sch = ksa.Schematic.load(str(sch_path))
            r1 = sch.components.get("R1")

            if not r1:
                print("   ✗ R1 not found")
                return False

            original_pos = r1.position
            print(f"   Original R1 position: ({original_pos.x:.2f}, {original_pos.y:.2f})")

            new_pos = Point(180.0, 120.0)
            r1.position = new_pos
            print(f"   Moving R1 to: ({new_pos.x:.2f}, {new_pos.y:.2f})")

            sch.save(str(sch_path), preserve_format=True)
            print("   ✓ Saved")

        except Exception as e:
            print(f"   ✗ Failed: {e}")
            import traceback
            traceback.print_exc()
            return False

        # Step 3: Re-run circuit-synth (UPDATE mode)
        print("\n[3] Re-running circuit-synth (force_regenerate=False)...")

        c2 = simple_circuit()

        try:
            c2.generate_kicad_project(str(output_dir), force_regenerate=False, generate_pcb=False)
            print("   ✓ Update completed")
        except Exception as e:
            print(f"   ✗ Update failed: {e}")
            import traceback
            traceback.print_exc()
            return False

        # Step 4: Verify position preserved
        print("\n[4] Verifying position preserved...")

        try:
            sch_after = ksa.Schematic.load(str(sch_path))
            r1_after = sch_after.components.get("R1")

            if not r1_after:
                print("   ✗ R1 not found after update")
                return False

            print(f"   R1 position after update: ({r1_after.position.x:.2f}, {r1_after.position.y:.2f})")

            pos_preserved = (
                abs(r1_after.position.x - new_pos.x) < 0.01 and
                abs(r1_after.position.y - new_pos.y) < 0.01
            )

            if pos_preserved:
                print(f"   ✅ SUCCESS: Position preserved!")
                print(f"      Expected: ({new_pos.x:.2f}, {new_pos.y:.2f})")
                print(f"      Got:      ({r1_after.position.x:.2f}, {r1_after.position.y:.2f})")
                return True
            else:
                print(f"   ❌ FAILURE: Position NOT preserved!")
                print(f"      Expected: ({new_pos.x:.2f}, {new_pos.y:.2f})")
                print(f"      Got:      ({r1_after.position.x:.2f}, {r1_after.position.y:.2f})")
                return False

        except Exception as e:
            print(f"   ✗ Verification failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    print("\n" + "=" * 80)
    return False  # Should not reach here


if __name__ == "__main__":
    success = test_roundtrip()
    print("\n" + "=" * 80)
    if success:
        print("AUTOMATED TEST PASSED ✅")
        print("The round-trip system is working!")
        print("\nYou can now run the manual test: uv run python test_manual_roundtrip.py")
    else:
        print("AUTOMATED TEST FAILED ❌")
        print("There are still issues to fix")
    print("=" * 80)
    sys.exit(0 if success else 1)
