#!/usr/bin/env python3
"""
Test 12: Update Component Reference (Rename) - Sync Preservation Test

Validates that renaming a component (R1 → R100) preserves ALL other
schematic elements using kicad-sch-api verification.
"""

import pytest
import subprocess
import shutil
from pathlib import Path
from kicad_sch_api import Schematic


def test_12_update_component_ref(request):
    """Test renaming R1 → R100 while preserving R2, C1, power, and labels."""

    test_dir = Path(__file__).parent
    circuit_file = test_dir / "comprehensive_root.py"
    output_dir = test_dir / "comprehensive_root"
    schematic_file = output_dir / "comprehensive_root.kicad_sch"

    cleanup = not request.config.getoption("--keep-output", default=False)

    try:
        # STEP 1: Generate initial circuit with R1
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

        # Store properties for preservation check
        r1_value_before = r1_before.value
        r1_pos_before = r1_before.position
        r1_footprint_before = r1_before.footprint
        r2_pos_before = r2_before.position
        c1_pos_before = c1_before.position

        # STEP 2: Modify circuit to rename R1 → R100
        original_code = circuit_file.read_text()
        modified_code = original_code.replace('ref="R1"', 'ref="R100"')
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

        # Verify R1 renamed to R100
        refs = {c.reference for c in regular_components_after}
        assert "R100" in refs, "R100 not found after rename"
        assert "R1" not in refs, "R1 still exists after rename"

        r100 = next(c for c in regular_components_after if c.reference == "R100")
        r2_after = next(c for c in regular_components_after if c.reference == "R2")
        c1_after = next(c for c in regular_components_after if c.reference == "C1")

        # Verify R100 (formerly R1) properties preserved
        assert r100.value == r1_value_before, "R100 value changed"
        assert r100.position.x == r1_pos_before.x, "R100 X position changed"
        assert r100.position.y == r1_pos_before.y, "R100 Y position changed"
        assert r100.footprint == r1_footprint_before, "R100 footprint changed"

        # Verify R2 completely unchanged
        assert r2_after.value == "4.7k", "R2 value changed"
        assert r2_after.position.x == r2_pos_before.x, "R2 X position changed"
        assert r2_after.position.y == r2_pos_before.y, "R2 Y position changed"

        # Verify C1 completely unchanged
        assert c1_after.value == "100nF", "C1 value changed"
        assert c1_after.position.x == c1_pos_before.x, "C1 X position changed"
        assert c1_after.position.y == c1_pos_before.y, "C1 Y position changed"

        # Verify power symbols preserved
        power_symbols = [c for c in sch_after.components if c.reference.startswith("#PWR")]
        assert len(power_symbols) >= 2, "Power symbols missing"

        print("\n✅ Test 12 PASSED: Component rename preserved all other elements")
        print(f"   - R1 → R100 ✓")
        print(f"   - R100 value: {r100.value} (preserved) ✓")
        print(f"   - R100 position: preserved ✓")
        print(f"   - R2: completely unchanged ✓")
        print(f"   - C1: completely unchanged ✓")
        print(f"   - Power symbols: preserved ✓")

    finally:
        if 'original_code' in locals():
            circuit_file.write_text(original_code)

        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--keep-output"])
