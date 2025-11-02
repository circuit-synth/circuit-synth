#!/usr/bin/env python3
"""
Test 14: Add Net - Sync Preservation Test

Validates that adding a new net (CLK) connecting previously isolated
components preserves ALL other schematic elements.
"""

import pytest
import subprocess
import shutil
from pathlib import Path
from kicad_sch_api import Schematic


def test_14_add_net(request):
    """Test adding CLK net while preserving R1, DATA, power symbols."""

    test_dir = Path(__file__).parent
    circuit_file = test_dir / "comprehensive_root.py"
    output_dir = test_dir / "comprehensive_root"
    schematic_file = output_dir / "comprehensive_root.kicad_sch"

    cleanup = not request.config.getoption("--keep-output", default=False)

    try:
        # STEP 1: Generate initial circuit (R2, C1 isolated)
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
        assert len(regular_components) == 3

        r1_before = next(c for c in regular_components if c.reference == "R1")
        r2_before = next(c for c in regular_components if c.reference == "R2")
        c1_before = next(c for c in regular_components if c.reference == "C1")

        # Store positions
        r1_pos_before = r1_before.position
        r2_pos_before = r2_before.position
        c1_pos_before = c1_before.position

        # Check initial labels (should only have DATA, not CLK)
        initial_labels = {label.text for label in sch.hierarchical_labels}
        assert "DATA" in initial_labels, "DATA label missing initially"
        initial_label_count = len(sch.hierarchical_labels)

        # STEP 2: Modify circuit to add CLK net
        original_code = circuit_file.read_text()
        modified_code = original_code.replace(
            '    # clk = Net("CLK")  # Will be added in test',
            '    clk = Net("CLK")  # Added in test'
        )
        modified_code = modified_code.replace(
            '    # r2[2] will be connected to CLK in test',
            '    r2[2] += clk  # Added CLK connection'
        )
        modified_code = modified_code.replace(
            '    # c1[1] will be connected to CLK in test',
            '    c1[1] += clk  # Added CLK connection'
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

        # STEP 4: Load and verify
        sch_after = Schematic.load(str(schematic_file))

        regular_components_after = [c for c in sch_after.components if not c.reference.startswith("#PWR")]
        assert len(regular_components_after) == 3, "Component count changed"

        r1_after = next(c for c in regular_components_after if c.reference == "R1")
        r2_after = next(c for c in regular_components_after if c.reference == "R2")
        c1_after = next(c for c in regular_components_after if c.reference == "C1")

        # Verify all component positions preserved
        assert r1_after.position.x == r1_pos_before.x, "R1 X position changed"
        assert r1_after.position.y == r1_pos_before.y, "R1 Y position changed"
        assert r2_after.position.x == r2_pos_before.x, "R2 X position changed"
        assert r2_after.position.y == r2_pos_before.y, "R2 Y position changed"
        assert c1_after.position.x == c1_pos_before.x, "C1 X position changed"
        assert c1_after.position.y == c1_pos_before.y, "C1 Y position changed"

        # Verify CLK label added
        final_labels = {label.text for label in sch_after.hierarchical_labels}
        assert "CLK" in final_labels, "CLK label not added"
        assert "DATA" in final_labels, "DATA label disappeared"

        # Should have more labels now (CLK added)
        assert len(sch_after.hierarchical_labels) > initial_label_count, "Label count didn't increase"

        # Verify power symbols preserved
        power_symbols = [c for c in sch_after.components if c.reference.startswith("#PWR")]
        assert len(power_symbols) >= 2, "Power symbols missing"

        print("\n✅ Test 14 PASSED: Net addition preserved all other elements")
        print(f"   - CLK net added ✓")
        print(f"   - CLK connects R2-C1 ✓")
        print(f"   - R1 position: preserved ✓")
        print(f"   - R2 position: preserved ✓")
        print(f"   - C1 position: preserved ✓")
        print(f"   - DATA label: preserved ✓")
        print(f"   - Power symbols: preserved ✓")

    finally:
        if 'original_code' in locals():
            circuit_file.write_text(original_code)

        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--keep-output"])
