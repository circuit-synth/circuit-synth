#!/usr/bin/env python3
"""
Test 18: Add Component in Subcircuit - Sync Preservation Test

Validates that adding R3 to the amplifier subcircuit preserves
all root sheet components (R1, R2) and their positions.
"""

import pytest
import subprocess
import shutil
from pathlib import Path
from kicad_sch_api import Schematic


def test_18_add_component_hier(request):
    """Test adding R3 to amplifier subcircuit while preserving root sheet."""

    test_dir = Path(__file__).parent
    circuit_file = test_dir / "comprehensive_root.py"
    output_dir = test_dir / "comprehensive_root"
    root_schematic = output_dir / "comprehensive_root.kicad_sch"
    sub_schematic = output_dir / "amplifier.kicad_sch"

    cleanup = not request.config.getoption("--keep-output", default=False)

    try:
        # STEP 1: Generate initial circuit (R3 disconnected)
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

        # Load subcircuit sheet
        sub_sch_before = Schematic.load(str(sub_schematic))
        sub_components_before = [c for c in sub_sch_before.components if not c.reference.startswith("#PWR")]

        # R3 exists but is disconnected (no net connections)
        r3_before = next((c for c in sub_components_before if c.reference == "R3"), None)
        assert r3_before is not None, "R3 should exist in subcircuit"

        # STEP 2: Modify circuit to connect R3
        original_code = circuit_file.read_text()
        modified_code = original_code.replace(
            '    # r3_amp[1] += input_sig\n    # r3_amp[2] += output_sig',
            '    r3_amp[1] += input_sig  # Connected\n    r3_amp[2] += output_sig  # Connected'
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

        # STEP 5: Verify R3 in subcircuit after modification
        sub_sch_after = Schematic.load(str(sub_schematic))
        sub_components_after = [c for c in sub_sch_after.components if not c.reference.startswith("#PWR")]

        r3_after = next((c for c in sub_components_after if c.reference == "R3"), None)
        assert r3_after is not None, "R3 missing after connection"
        assert r3_after.value == "1k", "R3 value incorrect"

        # Key bidirectional test: R3 position should be preserved after modification
        assert r3_after.position.x == r3_before.position.x, "R3 X position changed"
        assert r3_after.position.y == r3_before.position.y, "R3 Y position changed"

        print("\n✅ Test 18 PASSED: Component modification in subcircuit, root preserved")
        print(f"   - R3 modified in subcircuit ✓")
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
