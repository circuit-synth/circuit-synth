#!/usr/bin/env python3
"""
Test 17: Delete Net - Sync Preservation Test

Validates that deleting a net (CLK) preserves all other schematic elements
and the DATA net.
"""

import pytest
import subprocess
import shutil
from pathlib import Path
from kicad_sch_api import Schematic


def test_17_delete_net(request):
    """Test deleting CLK net while preserving DATA and all components."""

    test_dir = Path(__file__).parent
    circuit_file = test_dir / "comprehensive_root.py"
    output_dir = test_dir / "comprehensive_root"
    schematic_file = output_dir / "comprehensive_root.kicad_sch"

    cleanup = not request.config.getoption("--keep-output", default=False)

    try:
        # STEP 1: Generate initial circuit with DATA and CLK nets
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

        # Store positions
        r1_before = next(c for c in regular_components if c.reference == "R1")
        r2_before = next(c for c in regular_components if c.reference == "R2")
        c1_before = next(c for c in regular_components if c.reference == "C1")

        r1_pos_before = r1_before.position
        r2_pos_before = r2_before.position
        c1_pos_before = c1_before.position

        # Check initial labels (should have both DATA and CLK)
        initial_labels = {label.text for label in sch.hierarchical_labels}
        assert "DATA" in initial_labels, "DATA label missing initially"
        assert "CLK" in initial_labels, "CLK label missing initially"

        # STEP 2: Modify circuit to delete CLK net
        original_code = circuit_file.read_text()
        modified_code = original_code.replace(
            '    clk = Net("CLK")  # Will be deleted in test',
            '    # clk = Net("CLK")  # Deleted in test'
        )
        modified_code = modified_code.replace(
            '    r2[1] += clk  # Will be disconnected when CLK deleted',
            '    # r2[1] += clk  # Disconnected (CLK deleted)'
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

        # Verify CLK deleted, DATA preserved
        final_labels = {label.text for label in sch_after.hierarchical_labels}
        assert "DATA" in final_labels, "DATA label missing after CLK deletion"
        assert "CLK" not in final_labels, "CLK label still exists after deletion"

        # Verify power symbols preserved
        power_symbols = [c for c in sch_after.components if c.reference.startswith("#PWR")]
        assert len(power_symbols) >= 2, "Power symbols missing"

        print("\n✅ Test 17 PASSED: Net deletion preserved all other elements")
        print(f"   - CLK net deleted ✓")
        print(f"   - DATA net preserved ✓")
        print(f"   - R1 position: preserved ✓")
        print(f"   - R2 position: preserved ✓")
        print(f"   - C1 position: preserved ✓")
        print(f"   - Power symbols: preserved ✓")

    finally:
        if 'original_code' in locals():
            circuit_file.write_text(original_code)

        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--keep-output"])
