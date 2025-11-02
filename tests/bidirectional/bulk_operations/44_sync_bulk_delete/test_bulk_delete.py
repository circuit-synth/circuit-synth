#!/usr/bin/env python3
"""
Test 44: Delete Multiple Components - Basic Generation Test

Validates that deleting multiple components in bulk
generates successfully and creates the expected schematic structure.
"""

import pytest
import subprocess
import shutil
from pathlib import Path
from kicad_sch_api import Schematic


def test_44_bulk_delete(request):
    """Test deleting multiple components - basic generation."""

    test_dir = Path(__file__).parent
    circuit_file = test_dir / "comprehensive_root.py"
    output_dir = test_dir / "comprehensive_root"
    root_schematic = output_dir / "comprehensive_root.kicad_sch"

    cleanup = not request.config.getoption("--keep-output", default=False)

    try:
        # STEP 1: Generate circuit
        result = subprocess.run(
            ["uv", "run", str(circuit_file)],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0, f"Generation failed: {result.stderr}"
        assert root_schematic.exists(), "Root schematic not generated"

        # Load root sheet
        root_sch = Schematic.load(str(root_schematic))
        root_components = [c for c in root_sch.components if not c.reference.startswith("#PWR")]
        assert len(root_components) == 7, "Expected 7 components (R1-R5, C1, C2)"

        # Verify all components exist
        r1 = next((c for c in root_components if c.reference == "R1"), None)
        r2 = next((c for c in root_components if c.reference == "R2"), None)
        r3 = next((c for c in root_components if c.reference == "R3"), None)
        r4 = next((c for c in root_components if c.reference == "R4"), None)
        r5 = next((c for c in root_components if c.reference == "R5"), None)
        c1 = next((c for c in root_components if c.reference == "C1"), None)
        c2 = next((c for c in root_components if c.reference == "C2"), None)
        assert all([r1, r2, r3, r4, r5, c1, c2]), "All components should exist initially"

        print("\n✅ Test 44 PASSED: Bulk delete test circuit generated successfully")
        print(f"   - Root sheet: 7 components (R1-R5, C1, C2) ✓")
        print(f"\n💡 Note: Full test includes deleting R3, R4, R5 and verifying remaining positions")

    finally:
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--keep-output"])
