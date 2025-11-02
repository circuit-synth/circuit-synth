#!/usr/bin/env python3
"""
Test 19: Update Component Value in Subcircuit - Sync Preservation Test

Validates that changing R3 value in the amplifier subcircuit (1k → 47k)
preserves all root sheet components and R3's position.
"""

import pytest
import subprocess
import shutil
from pathlib import Path
from kicad_sch_api import Schematic


def test_19_update_value_hier(request):
    """Test updating R3 value in subcircuit while preserving positions."""

    test_dir = Path(__file__).parent
    circuit_file = test_dir / "comprehensive_root.py"
    output_dir = test_dir / "comprehensive_root"
    root_schematic = output_dir / "comprehensive_root.kicad_sch"
    sub_schematic = output_dir / "amplifier.kicad_sch"

    cleanup = not request.config.getoption("--keep-output", default=False)

    try:
        # STEP 1: Generate initial circuit (R3=1k)
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

        # Load subcircuit sheet and verify R3=1k
        sub_sch_before = Schematic.load(str(sub_schematic))
        sub_components_before = [c for c in sub_sch_before.components if not c.reference.startswith("#PWR")]

        r3_before = next((c for c in sub_components_before if c.reference == "R3"), None)
        assert r3_before is not None, "R3 should exist in subcircuit"
        assert r3_before.value == "1k", "R3 should initially be 1k"
        r3_pos_before = r3_before.position

        # STEP 2: Modify circuit to change R3 value: 1k → 47k
        original_code = circuit_file.read_text()
        modified_code = original_code.replace(
            '        value="1k",  # Will change to 47k',
            '        value="47k",  # Changed from 1k'
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

        # STEP 5: Verify R3 value changed but position preserved
        sub_sch_after = Schematic.load(str(sub_schematic))
        sub_components_after = [c for c in sub_sch_after.components if not c.reference.startswith("#PWR")]

        r3_after = next((c for c in sub_components_after if c.reference == "R3"), None)
        assert r3_after is not None, "R3 missing after value change"
        assert r3_after.value == "47k", "R3 value not updated to 47k"

        # Key bidirectional test: R3 position should be preserved
        assert r3_after.position.x == r3_pos_before.x, "R3 X position changed"
        assert r3_after.position.y == r3_pos_before.y, "R3 Y position changed"

        print("\n✅ Test 19 PASSED: Component value updated in subcircuit, positions preserved")
        print(f"   - R3 value: 1k → 47k ✓")
        print(f"   - R3 position: preserved ✓")
        print(f"   - Root R1 position: preserved ✓")
        print(f"   - Root R2 position: preserved ✓")
        print(f"   - Root values: preserved ✓")

    finally:
        if 'original_code' in locals():
            circuit_file.write_text(original_code)

        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--keep-output"])
