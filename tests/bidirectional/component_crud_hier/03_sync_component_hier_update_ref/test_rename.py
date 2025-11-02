#!/usr/bin/env python3
"""
Test 20: Rename Component in Subcircuit - Sync Preservation Test

Validates that renaming R3 → R100 in the amplifier subcircuit
preserves all root sheet components and the renamed component's properties.
"""

import pytest
import subprocess
import shutil
from pathlib import Path
from kicad_sch_api import Schematic


def test_20_rename_component_hier(request):
    """Test renaming R3 → R100 in subcircuit while preserving positions."""

    test_dir = Path(__file__).parent
    circuit_file = test_dir / "comprehensive_root.py"
    output_dir = test_dir / "comprehensive_root"
    root_schematic = output_dir / "comprehensive_root.kicad_sch"
    sub_schematic = output_dir / "amplifier.kicad_sch"

    cleanup = not request.config.getoption("--keep-output", default=False)

    try:
        # STEP 1: Generate initial circuit (R3)
        result = subprocess.run(
            ["uv", "run", str(circuit_file)],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0, f"Initial generation failed: {result.stderr}"
        assert root_schematic.exists(), "Root schematic not generated"
        assert sub_schematic.exists(), "Subcircuit schematic not generated"

        # Load root sheet
        root_sch = Schematic.load(str(root_schematic))
        root_components = [c for c in root_sch.components if not c.reference.startswith("#PWR")]
        assert len(root_components) == 2, "Expected 2 components on root sheet"

        # Store root component positions
        r1_before = next(c for c in root_components if c.reference == "R1")
        r2_before = next(c for c in root_components if c.reference == "R2")
        r1_pos_before = r1_before.position
        r2_pos_before = r2_before.position

        # Load subcircuit sheet and verify R3 exists
        sub_sch_before = Schematic.load(str(sub_schematic))
        sub_components_before = [c for c in sub_sch_before.components if not c.reference.startswith("#PWR")]

        r3_before = next((c for c in sub_components_before if c.reference == "R3"), None)
        assert r3_before is not None, "R3 should exist in subcircuit"
        r3_pos_before = r3_before.position
        r3_value_before = r3_before.value

        # STEP 2: Modify circuit to rename R3 → R100
        original_code = circuit_file.read_text()
        modified_code = original_code.replace(
            '        ref="R3",  # Will change to R100',
            '        ref="R100",  # Renamed from R3'
        )
        circuit_file.write_text(modified_code)

        # STEP 3: Regenerate circuit
        result = subprocess.run(
            ["uv", "run", str(circuit_file)],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0, f"Regeneration failed: {result.stderr}"

        # STEP 4: Verify root sheet unchanged
        root_sch_after = Schematic.load(str(root_schematic))
        root_components_after = [c for c in root_sch_after.components if not c.reference.startswith("#PWR")]
        assert len(root_components_after) == 2, "Root component count changed"

        r1_after = next(c for c in root_components_after if c.reference == "R1")
        r2_after = next(c for c in root_components_after if c.reference == "R2")

        # Verify root positions preserved
        assert r1_after.position.x == r1_pos_before.x, "R1 X position changed"
        assert r1_after.position.y == r1_pos_before.y, "R1 Y position changed"
        assert r2_after.position.x == r2_pos_before.x, "R2 X position changed"
        assert r2_after.position.y == r2_pos_before.y, "R2 Y position changed"

        # Verify root values preserved
        assert r1_after.value == "10k", "R1 value changed"
        assert r2_after.value == "4.7k", "R2 value changed"

        # STEP 5: Verify R3 renamed to R100 with same value and position
        sub_sch_after = Schematic.load(str(sub_schematic))
        sub_components_after = [c for c in sub_sch_after.components if not c.reference.startswith("#PWR")]

        # R3 should be gone
        r3_after = next((c for c in sub_components_after if c.reference == "R3"), None)
        assert r3_after is None, "R3 still exists after rename"

        # R100 should exist with same value and position
        r100_after = next((c for c in sub_components_after if c.reference == "R100"), None)
        assert r100_after is not None, "R100 not found after rename"
        assert r100_after.value == r3_value_before, "R100 value doesn't match old R3 value"

        # Key bidirectional test: R100 position should match old R3 position
        assert r100_after.position.x == r3_pos_before.x, "R100 X position doesn't match old R3"
        assert r100_after.position.y == r3_pos_before.y, "R100 Y position doesn't match old R3"

        print("\n✅ Test 20 PASSED: Component renamed in subcircuit, positions preserved")
        print(f"   - R3 → R100 ✓")
        print(f"   - R100 value: preserved ✓")
        print(f"   - R100 position: preserved ✓")
        print(f"   - Root R1 position: preserved ✓")
        print(f"   - Root R2 position: preserved ✓")

    finally:
        if 'original_code' in locals():
            circuit_file.write_text(original_code)

        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--keep-output"])
