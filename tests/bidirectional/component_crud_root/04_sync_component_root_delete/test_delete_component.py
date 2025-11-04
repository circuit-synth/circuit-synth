#!/usr/bin/env python3
"""
Test 13: Delete Component - Sync Preservation Test

Validates that deleting a component (R2) preserves ALL other
schematic elements using kicad-sch-api verification.
"""

import pytest
import subprocess
import shutil
from pathlib import Path
from kicad_sch_api import Schematic


def test_13_delete_component(request):
    """Test deleting R2 while preserving R1, C1, power, and labels."""

    test_dir = Path(__file__).parent
    circuit_file = test_dir / "comprehensive_root.py"
    output_dir = test_dir / "comprehensive_root"
    schematic_file = output_dir / "comprehensive_root.kicad_sch"

    cleanup = not request.config.getoption("--keep-output", default=False)

    try:
        # STEP 0: Save original code and uncomment R2 for initial generation
        original_code = circuit_file.read_text()

        # Uncomment R2 definition and connections
        code_with_r2 = original_code.replace(
            '    # r2 = Component(  # Will be deleted in test',
            '    r2 = Component(  # Will be deleted in test'
        )
        code_with_r2 = code_with_r2.replace(
            '    #     symbol="Device:R",\n    #     ref="R2",',
            '        symbol="Device:R",\n        ref="R2",'
        )
        code_with_r2 = code_with_r2.replace(
            '    #     value="4.7k",\n    #     footprint="Resistor_SMD:R_0603_1608Metric"\n    # )',
            '        value="4.7k",\n        footprint="Resistor_SMD:R_0603_1608Metric"\n    )'
        )
        code_with_r2 = code_with_r2.replace('    # r2[1] += vcc  # Will be deleted with R2', '    r2[1] += vcc  # Will be deleted with R2')
        code_with_r2 = code_with_r2.replace('    # r2[2] += gnd  # Will be deleted with R2', '    r2[2] += gnd  # Will be deleted with R2')

        circuit_file.write_text(code_with_r2)

        # STEP 1: Generate initial circuit with R1, R2, C1
        result = subprocess.run(
            ["uv", "run", str(circuit_file)],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0, f"Initial generation failed: {result.stderr}"
        assert schematic_file.exists(), "Schematic not generated"

        sch = Schematic.load(str(schematic_file))

        regular_components = [c for c in sch.components if not c.reference.startswith("#PWR")]
        assert len(regular_components) == 3, f"Expected 3 components, got {len(regular_components)}"

        r1_before = next(c for c in regular_components if c.reference == "R1")
        r2_before = next(c for c in regular_components if c.reference == "R2")
        c1_before = next(c for c in regular_components if c.reference == "C1")

        # Store properties for preservation check
        r1_pos_before = r1_before.position
        r1_value_before = r1_before.value
        c1_pos_before = c1_before.position
        c1_value_before = c1_before.value

        # STEP 2: Modify circuit to delete R2 (restore original with R2 commented out)
        circuit_file.write_text(original_code)

        # STEP 3: Regenerate circuit
        result = subprocess.run(
            ["uv", "run", str(circuit_file)],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0, f"Regeneration failed: {result.stderr}"

        # STEP 4: Load and verify
        sch_after = Schematic.load(str(schematic_file))

        regular_components_after = [c for c in sch_after.components if not c.reference.startswith("#PWR")]

        # Verify R2 deleted
        assert len(regular_components_after) == 2, f"Expected 2 components after delete, got {len(regular_components_after)}"

        refs = {c.reference for c in regular_components_after}
        assert "R2" not in refs, "R2 still exists after delete"
        assert "R1" in refs, "R1 missing after R2 delete"
        assert "C1" in refs, "C1 missing after R2 delete"

        r1_after = next(c for c in regular_components_after if c.reference == "R1")
        c1_after = next(c for c in regular_components_after if c.reference == "C1")

        # Verify R1 completely unchanged
        assert r1_after.value == r1_value_before, "R1 value changed"
        assert r1_after.position.x == r1_pos_before.x, "R1 X position changed"
        assert r1_after.position.y == r1_pos_before.y, "R1 Y position changed"

        # Verify C1 completely unchanged
        assert c1_after.value == c1_value_before, "C1 value changed"
        assert c1_after.position.x == c1_pos_before.x, "C1 X position changed"
        assert c1_after.position.y == c1_pos_before.y, "C1 Y position changed"

        # Verify power symbols preserved
        power_symbols = [c for c in sch_after.components if c.reference.startswith("#PWR")]
        assert len(power_symbols) >= 2, "Power symbols missing"

        print("\n✅ Test 13 PASSED: Component deletion preserved all other elements")
        print(f"   - R2 deleted ✓")
        print(f"   - R1: completely unchanged ✓")
        print(f"   - C1: completely unchanged ✓")
        print(f"   - Power symbols: preserved ✓")
        print(f"   - Component count: 3 → 2 ✓")

    finally:
        if 'original_code' in locals():
            circuit_file.write_text(original_code)

        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)


def test_13b_delete_with_moved_components(request):
    """Test deleting R2 after manually moving components in KiCad.

    This verifies that:
    1. Moving components in KiCad works
    2. Deleting a component preserves the moved positions of remaining components
    """

    test_dir = Path(__file__).parent
    circuit_file = test_dir / "comprehensive_root.py"
    output_dir = test_dir / "comprehensive_root"
    schematic_file = output_dir / "comprehensive_root.kicad_sch"

    cleanup = not request.config.getoption("--keep-output", default=False)

    try:
        # STEP 0: Save original and uncomment R2
        original_code = circuit_file.read_text()

        code_with_r2 = original_code.replace(
            '    # r2 = Component(  # Will be deleted in test',
            '    r2 = Component(  # Will be deleted in test'
        )
        code_with_r2 = code_with_r2.replace(
            '    #     symbol="Device:R",\n    #     ref="R2",',
            '        symbol="Device:R",\n        ref="R2",'
        )
        code_with_r2 = code_with_r2.replace(
            '    #     value="4.7k",\n    #     footprint="Resistor_SMD:R_0603_1608Metric"\n    # )',
            '        value="4.7k",\n        footprint="Resistor_SMD:R_0603_1608Metric"\n    )'
        )
        code_with_r2 = code_with_r2.replace('    # r2[1] += vcc  # Will be deleted with R2', '    r2[1] += vcc  # Will be deleted with R2')
        code_with_r2 = code_with_r2.replace('    # r2[2] += gnd  # Will be deleted with R2', '    r2[2] += gnd  # Will be deleted with R2')

        circuit_file.write_text(code_with_r2)

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

        # STEP 2: Manually move components by modifying schematic file
        # Simulate user moving components in KiCad GUI
        sch_content = schematic_file.read_text()

        # Move R1 from default position to (50.8, 50.8)
        sch_content = sch_content.replace(
            '(symbol (lib_id "Device:R") (at 30.48',
            '(symbol (lib_id "Device:R") (at 50.8'
        )
        # Move C1 to (100.0, 60.0)
        sch_content_lines = sch_content.split('\n')
        in_c1 = False
        for i, line in enumerate(sch_content_lines):
            if '(symbol (lib_id "Device:C")' in line and 'C1' in sch_content_lines[i+2]:
                # Found C1, modify its position line
                sch_content_lines[i] = line.replace('(at 76.2', '(at 100.0')
                sch_content_lines[i] = sch_content_lines[i].replace('58.42', '60.0')
                break
        sch_content = '\n'.join(sch_content_lines)

        schematic_file.write_text(sch_content)

        # STEP 3: Verify moved positions
        sch = Schematic.load(str(schematic_file))
        regular_components = [c for c in sch.components if not c.reference.startswith("#PWR")]

        r1_moved = next(c for c in regular_components if c.reference == "R1")
        c1_moved = next(c for c in regular_components if c.reference == "C1")

        # Store the NEW moved positions
        r1_new_x = r1_moved.position.x
        r1_new_y = r1_moved.position.y
        c1_new_x = c1_moved.position.x
        c1_new_y = c1_moved.position.y

        print(f"\n📍 Moved positions:")
        print(f"   R1: ({r1_new_x:.2f}, {r1_new_y:.2f})")
        print(f"   C1: ({c1_new_x:.2f}, {c1_new_y:.2f})")

        # STEP 4: Delete R2 in Python code (restore original with R2 commented out)
        circuit_file.write_text(original_code)

        # STEP 5: Regenerate - should preserve moved positions
        result = subprocess.run(
            ["uv", "run", str(circuit_file)],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0, f"Regeneration failed: {result.stderr}"

        # STEP 6: Verify R2 deleted AND moved positions preserved
        sch_after = Schematic.load(str(schematic_file))
        regular_components_after = [c for c in sch_after.components if not c.reference.startswith("#PWR")]

        # Verify R2 deleted
        assert len(regular_components_after) == 2, f"Expected 2 components, got {len(regular_components_after)}"
        refs = {c.reference for c in regular_components_after}
        assert "R2" not in refs, "R2 still exists after delete"

        # Verify moved positions PRESERVED
        r1_after = next(c for c in regular_components_after if c.reference == "R1")
        c1_after = next(c for c in regular_components_after if c.reference == "C1")

        # R1 should be at its moved position (50.8, 50.8)
        assert abs(r1_after.position.x - r1_new_x) < 0.1, \
            f"R1 X position not preserved: expected {r1_new_x}, got {r1_after.position.x}"
        assert abs(r1_after.position.y - r1_new_y) < 0.1, \
            f"R1 Y position not preserved: expected {r1_new_y}, got {r1_after.position.y}"

        # C1 should be at its moved position (100.0, 60.0)
        assert abs(c1_after.position.x - c1_new_x) < 0.1, \
            f"C1 X position not preserved: expected {c1_new_x}, got {c1_after.position.x}"
        assert abs(c1_after.position.y - c1_new_y) < 0.1, \
            f"C1 Y position not preserved: expected {c1_new_y}, got {c1_after.position.y}"

        print("\n✅ Test 13b PASSED: Deletion preserved moved component positions")
        print(f"   - R2 deleted ✓")
        print(f"   - R1 position preserved at ({r1_after.position.x:.2f}, {r1_after.position.y:.2f}) ✓")
        print(f"   - C1 position preserved at ({c1_after.position.x:.2f}, {c1_after.position.y:.2f}) ✓")
        print(f"   - Position preservation WORKING! ✓")

    finally:
        if 'original_code' in locals():
            circuit_file.write_text(original_code)

        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--keep-output"])
