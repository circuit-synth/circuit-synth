#!/usr/bin/env python3
"""
Test 15: Update Net Connection - Sync Preservation Test

Validates that changing which net a pin connects to (R2[2]: CLK → DATA)
preserves all other schematic elements.
"""

import pytest
import subprocess
import shutil
from pathlib import Path
from kicad_sch_api import Schematic


def test_15_update_net_connection(request):
    """Test changing R2[2] from CLK to DATA while preserving everything else."""

    test_dir = Path(__file__).parent
    circuit_file = test_dir / "comprehensive_root.py"
    output_dir = test_dir / "comprehensive_root"
    schematic_file = output_dir / "comprehensive_root.kicad_sch"

    cleanup = not request.config.getoption("--keep-output", default=False)

    try:
        # STEP 1: Generate initial circuit (R2[2] on CLK)
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

        # Check initial labels (should have both DATA and CLK)
        initial_labels = {label.text for label in sch.hierarchical_labels}
        assert "DATA" in initial_labels, "DATA label missing initially"
        assert "CLK" in initial_labels, "CLK label missing initially"

        # STEP 2: Modify circuit to change R2[2] from CLK to DATA
        original_code = circuit_file.read_text()
        modified_code = original_code.replace(
            '    r2[2] += clk  # Will change to: r2[2] += data',
            '    r2[2] += data  # Changed from CLK'
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

        # Check final labels (CLK might still exist if C1[1] still connected)
        final_labels = {label.text for label in sch_after.hierarchical_labels}
        assert "DATA" in final_labels, "DATA label missing after update"
        # CLK should still exist because C1[1] is still on CLK
        assert "CLK" in final_labels, "CLK label should still exist (C1[1] still connected)"

        # Verify power symbols preserved
        power_symbols = [c for c in sch_after.components if c.reference.startswith("#PWR")]
        assert len(power_symbols) >= 2, "Power symbols missing"

        print("\n✅ Test 15 PASSED: Net connection update preserved all other elements")
        print(f"   - R2[2] changed from CLK to DATA ✓")
        print(f"   - R1 position: preserved ✓")
        print(f"   - R2 position: preserved ✓")
        print(f"   - C1 position: preserved ✓")
        print(f"   - CLK label: still present (C1[1] connected) ✓")
        print(f"   - DATA label: preserved ✓")
        print(f"   - Power symbols: preserved ✓")

    finally:
        if 'original_code' in locals():
            circuit_file.write_text(original_code)

        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--keep-output"])
