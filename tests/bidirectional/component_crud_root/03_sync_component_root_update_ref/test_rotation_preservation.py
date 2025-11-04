#!/usr/bin/env python3
"""
Test: Component Rotation Preservation During Sync

Validates that component rotations are preserved when synchronizing
changes (value updates, footprint changes, etc.)
"""

import pytest
import subprocess
import shutil
from pathlib import Path
import kicad_sch_api as ksa


def test_rotation_preservation_on_value_change(request):
    """Test that rotation is preserved when only value changes."""

    test_dir = Path(__file__).parent
    circuit_file = test_dir / "comprehensive_root.py"
    output_dir = test_dir / "comprehensive_root"
    schematic_file = output_dir / "comprehensive_root.kicad_sch"

    cleanup = not request.config.getoption("--keep-output", default=False)

    try:
        # STEP 1: Generate initial circuit
        result = subprocess.run(
            ["uv", "run", str(circuit_file)],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0, f"Initial generation failed: {result.stderr}"
        assert schematic_file.exists(), "Schematic not generated"

        # STEP 2: Load schematic and set rotations
        sch = ksa.Schematic.load(str(schematic_file))

        # Set specific rotations for each component
        rotations = {'R1': 90.0, 'R2': 180.0, 'C1': 270.0}
        for comp in sch.components:
            if comp.reference in rotations:
                comp.rotation = rotations[comp.reference]
                print(f"Set {comp.reference} rotation to {comp.rotation}°")

        # Save with rotations
        sch.save(str(schematic_file))

        # Verify rotations were saved
        sch = ksa.Schematic.load(str(schematic_file))
        for comp in sch.components:
            if comp.reference in rotations:
                assert comp.rotation == rotations[comp.reference], \
                    f"{comp.reference} rotation not saved correctly"

        print("\n✅ Initial rotations set:")
        print(f"   R1: 90°, R2: 180°, C1: 270°")

        # STEP 3: Modify circuit to change R1 value
        original_code = circuit_file.read_text()
        modified_code = original_code.replace('value="10k"', 'value="47k"', 1)  # Only first occurrence (R1)
        circuit_file.write_text(modified_code)

        # STEP 4: Sync/regenerate
        result = subprocess.run(
            ["uv", "run", str(circuit_file)],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0, f"Sync failed: {result.stderr}"

        # STEP 5: Verify rotations preserved after sync
        sch_after = ksa.Schematic.load(str(schematic_file))

        print("\n🔍 Checking rotations after sync...")
        for comp in sch_after.components:
            if comp.reference in rotations:
                expected_rotation = rotations[comp.reference]
                actual_rotation = comp.rotation
                print(f"   {comp.reference}: expected={expected_rotation}°, actual={actual_rotation}°")

                assert actual_rotation == expected_rotation, \
                    f"{comp.reference} rotation changed! Expected {expected_rotation}°, got {actual_rotation}°"

        # Verify the value actually changed
        r1 = next((c for c in sch_after.components if c.reference == "R1"), None)
        assert r1 is not None, "R1 not found after sync"
        assert r1.value == "47k", f"R1 value not updated! Expected 47k, got {r1.value}"

        print("\n✅ Test PASSED:")
        print("   - R1 value updated: 10k → 47k ✓")
        print("   - R1 rotation preserved: 90° ✓")
        print("   - R2 rotation preserved: 180° ✓")
        print("   - C1 rotation preserved: 270° ✓")

    finally:
        # Restore original code
        if 'original_code' in locals():
            circuit_file.write_text(original_code)

        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)


def test_rotation_preservation_all_angles(request):
    """Test all standard rotation angles (0°, 90°, 180°, 270°) are preserved."""

    test_dir = Path(__file__).parent
    circuit_file = test_dir / "comprehensive_root.py"
    output_dir = test_dir / "comprehensive_root"
    schematic_file = output_dir / "comprehensive_root.kicad_sch"

    cleanup = not request.config.getoption("--keep-output", default=False)

    # Test each angle
    angles_to_test = [0.0, 90.0, 180.0, 270.0]

    try:
        for angle in angles_to_test:
            print(f"\n🔄 Testing rotation angle: {angle}°")

            # Generate initial circuit
            result = subprocess.run(
                ["uv", "run", str(circuit_file)],
                cwd=test_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            assert result.returncode == 0, f"Generation failed for angle {angle}°"

            # Set R1 to test angle
            sch = ksa.Schematic.load(str(schematic_file))
            for comp in sch.components:
                if comp.reference == "R1":
                    comp.rotation = angle
            sch.save(str(schematic_file))

            # Change value
            original_code = circuit_file.read_text()
            modified_code = original_code.replace('value="10k"', 'value="47k"', 1)
            circuit_file.write_text(modified_code)

            # Sync
            result = subprocess.run(
                ["uv", "run", str(circuit_file)],
                cwd=test_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            assert result.returncode == 0, f"Sync failed for angle {angle}°"

            # Verify rotation preserved
            sch_after = ksa.Schematic.load(str(schematic_file))
            r1 = next((c for c in sch_after.components if c.reference == "R1"), None)
            assert r1 is not None, f"R1 not found after sync (angle {angle}°)"
            assert r1.rotation == angle, \
                f"R1 rotation changed for angle {angle}°! Expected {angle}°, got {r1.rotation}°"

            print(f"   ✅ {angle}° preserved correctly")

            # Restore original code
            circuit_file.write_text(original_code)

            # Clean up for next iteration
            if output_dir.exists():
                shutil.rmtree(output_dir)

        print("\n✅ All rotation angles preserved correctly!")

    finally:
        if 'original_code' in locals():
            circuit_file.write_text(original_code)

        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--keep-output"])
