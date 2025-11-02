#!/usr/bin/env python3
"""
Test 21: Delete Component in Subcircuit - Sync Preservation Test

Validates that deleting R4 from the amplifier subcircuit preserves
all root sheet components and remaining subcircuit components (R3).
"""

import pytest
import subprocess
import shutil
from pathlib import Path
from kicad_sch_api import Schematic


def test_21_delete_component_hier(request):
    """Test deleting R4 from subcircuit while preserving R3 and root components."""

    test_dir = Path(__file__).parent
    circuit_file = test_dir / "comprehensive_root.py"
    output_dir = test_dir / "comprehensive_root"
    root_schematic = output_dir / "comprehensive_root.kicad_sch"
    sub_schematic = output_dir / "amplifier.kicad_sch"

    cleanup = not request.config.getoption("--keep-output", default=False)

    try:
        # STEP 1: Generate initial circuit (R3, R4 in subcircuit)
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
        assert len(root_components) == 3, "Expected 3 components on root sheet"

        # Store root component positions
        r1_before = next(c for c in root_components if c.reference == "R1")
        r2_before = next(c for c in root_components if c.reference == "R2")
        c1_before = next(c for c in root_components if c.reference == "C1")
        r1_pos_before = r1_before.position
        r2_pos_before = r2_before.position
        c1_pos_before = c1_before.position

        # Load subcircuit sheet and verify R3, R4 exist
        sub_sch_before = Schematic.load(str(sub_schematic))
        sub_components_before = [c for c in sub_sch_before.components if not c.reference.startswith("#PWR")]
        assert len(sub_components_before) == 2, "Expected 2 components in subcircuit (R3, R4)"

        r3_before = next((c for c in sub_components_before if c.reference == "R3"), None)
        r4_before = next((c for c in sub_components_before if c.reference == "R4"), None)
        assert r3_before is not None, "R3 should exist in subcircuit"
        assert r4_before is not None, "R4 should exist in subcircuit"
        r3_pos_before = r3_before.position

        # STEP 2: Modify circuit to delete R4
        original_code = circuit_file.read_text()
        modified_code = original_code.replace(
            """    r4_amp = Component(
        symbol="Device:R",
        ref="R4",  # Will be deleted
        value="2.2k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )""",
            """    # r4_amp = Component(
    #     symbol="Device:R",
    #     ref="R4",  # Deleted
    #     value="2.2k",
    #     footprint="Resistor_SMD:R_0603_1608Metric"
    # )"""
        )
        modified_code = modified_code.replace(
            """    r4_amp[1] += output_sig
    r4_amp[2] += gnd""",
            """    # r4_amp[1] += output_sig  # Deleted
    # r4_amp[2] += gnd  # Deleted"""
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
        assert len(root_components_after) == 3, "Root component count changed"

        r1_after = next(c for c in root_components_after if c.reference == "R1")
        r2_after = next(c for c in root_components_after if c.reference == "R2")
        c1_after = next(c for c in root_components_after if c.reference == "C1")

        # Verify root positions preserved
        assert r1_after.position.x == r1_pos_before.x, "R1 X position changed"
        assert r1_after.position.y == r1_pos_before.y, "R1 Y position changed"
        assert r2_after.position.x == r2_pos_before.x, "R2 X position changed"
        assert r2_after.position.y == r2_pos_before.y, "R2 Y position changed"
        assert c1_after.position.x == c1_pos_before.x, "C1 X position changed"
        assert c1_after.position.y == c1_pos_before.y, "C1 Y position changed"

        # Verify root values preserved
        assert r1_after.value == "10k", "R1 value changed"
        assert r2_after.value == "4.7k", "R2 value changed"
        assert c1_after.value == "100nF", "C1 value changed"

        # STEP 5: Verify R4 deleted, R3 preserved
        sub_sch_after = Schematic.load(str(sub_schematic))
        sub_components_after = [c for c in sub_sch_after.components if not c.reference.startswith("#PWR")]
        assert len(sub_components_after) == 1, "Expected 1 component in subcircuit after deletion"

        # R4 should be gone
        r4_after = next((c for c in sub_components_after if c.reference == "R4"), None)
        assert r4_after is None, "R4 still exists after deletion"

        # R3 should still exist with preserved position
        r3_after = next((c for c in sub_components_after if c.reference == "R3"), None)
        assert r3_after is not None, "R3 missing after R4 deletion"
        assert r3_after.value == "1k", "R3 value changed"

        # Key bidirectional test: R3 position should be preserved
        assert r3_after.position.x == r3_pos_before.x, "R3 X position changed"
        assert r3_after.position.y == r3_pos_before.y, "R3 Y position changed"

        print("\n✅ Test 21 PASSED: Component deleted from subcircuit, other components preserved")
        print(f"   - R4 deleted ✓")
        print(f"   - R3 preserved ✓")
        print(f"   - R3 position: preserved ✓")
        print(f"   - Root R1, R2, C1 positions: preserved ✓")
        print(f"   - Root values: preserved ✓")

    finally:
        if 'original_code' in locals():
            circuit_file.write_text(original_code)

        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--keep-output"])
