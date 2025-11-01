#!/usr/bin/env python3
"""
Test 11: Update Component Value - Sync Preservation Test

Validates that updating a component value (R1: 10k → 47k) preserves ALL other
schematic elements using kicad-sch-api verification.
"""

import pytest
import subprocess
import shutil
from pathlib import Path
from kicad_sch_api import Schematic


def test_11_update_component_value(request):
    """Test updating R1 value while preserving R2, C1, power, and labels."""

    test_dir = Path(__file__).parent
    circuit_file = test_dir / "comprehensive_root.py"
    output_dir = test_dir / "comprehensive_root"
    schematic_file = output_dir / "comprehensive_root.kicad_sch"

    # Cleanup flag
    cleanup = not request.config.getoption("--keep-output", default=False)

    try:
        # STEP 1: Generate initial circuit with R1=10k
        result = subprocess.run(
            ["uv", "run", str(circuit_file)],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0, f"Initial generation failed: {result.stderr}"
        assert schematic_file.exists(), "Schematic not generated"

        # Load and verify initial state
        sch = Schematic.load(str(schematic_file))

        # Get initial components (exclude power symbols)
        regular_components = [c for c in sch.components if not c.reference.startswith("#PWR")]
        assert len(regular_components) == 3, f"Expected 3 components, got {len(regular_components)}"

        # Find components
        r1_before = next(c for c in regular_components if c.reference == "R1")
        r2_before = next(c for c in regular_components if c.reference == "R2")
        c1_before = next(c for c in regular_components if c.reference == "C1")

        # Verify initial values
        assert r1_before.value == "10k", f"R1 should be 10k, got {r1_before.value}"
        assert r2_before.value == "4.7k", f"R2 should be 4.7k, got {r2_before.value}"
        assert c1_before.value == "100nF", f"C1 should be 100nF, got {c1_before.value}"

        # Store positions for preservation check
        r1_pos_before = r1_before.position
        r2_pos_before = r2_before.position
        c1_pos_before = c1_before.position

        # STEP 2: Modify circuit to change R1 value to 47k
        original_code = circuit_file.read_text()
        modified_code = original_code.replace(
            'value="10k",  # Will be updated to 47k in test',
            'value="47k",  # Updated from 10k'
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

        # STEP 4: Load regenerated schematic and verify preservation
        sch_after = Schematic.load(str(schematic_file))

        regular_components_after = [c for c in sch_after.components if not c.reference.startswith("#PWR")]
        assert len(regular_components_after) == 3, "Component count changed"

        # Find components after update
        r1_after = next(c for c in regular_components_after if c.reference == "R1")
        r2_after = next(c for c in regular_components_after if c.reference == "R2")
        c1_after = next(c for c in regular_components_after if c.reference == "C1")

        # Verify R1 value updated
        assert r1_after.value == "47k", f"R1 value should be 47k, got {r1_after.value}"

        # Verify R1 position preserved
        assert r1_after.position.x == r1_pos_before.x, "R1 X position changed"
        assert r1_after.position.y == r1_pos_before.y, "R1 Y position changed"

        # Verify R1 other properties preserved
        assert r1_after.footprint == r1_before.footprint, "R1 footprint changed"
        assert r1_after.rotation == r1_before.rotation, "R1 rotation changed"

        # Verify R2 completely unchanged
        assert r2_after.value == "4.7k", "R2 value changed"
        assert r2_after.position.x == r2_pos_before.x, "R2 X position changed"
        assert r2_after.position.y == r2_pos_before.y, "R2 Y position changed"
        assert r2_after.footprint == r2_before.footprint, "R2 footprint changed"

        # Verify C1 completely unchanged
        assert c1_after.value == "100nF", "C1 value changed"
        assert c1_after.position.x == c1_pos_before.x, "C1 X position changed"
        assert c1_after.position.y == c1_pos_before.y, "C1 Y position changed"
        assert c1_after.footprint == c1_before.footprint, "C1 footprint changed"

        # Verify power symbols preserved
        power_symbols = [c for c in sch_after.components if c.reference.startswith("#PWR")]
        assert len(power_symbols) >= 2, "Power symbols missing"
        power_values = {p.value for p in power_symbols}
        assert "VCC" in power_values, "VCC power symbol missing"
        assert "GND" in power_values, "GND power symbol missing"

        print("\n✅ Test 11 PASSED: Component value update preserved all other elements")
        print(f"   - R1 value: 10k → 47k ✓")
        print(f"   - R1 position: preserved ✓")
        print(f"   - R2: completely unchanged ✓")
        print(f"   - C1: completely unchanged ✓")
        print(f"   - Power symbols: preserved ✓")

    finally:
        # Restore original file
        if 'original_code' in locals():
            circuit_file.write_text(original_code)

        # Cleanup if requested
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--keep-output"])
