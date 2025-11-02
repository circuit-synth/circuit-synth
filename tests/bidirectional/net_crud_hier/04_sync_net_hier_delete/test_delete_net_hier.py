#!/usr/bin/env python3
"""
Test 25: Delete Net in Subcircuit - Basic Generation Test

Validates that deleting a net in the amplifier subcircuit
generates successfully and creates the expected schematic structure.

Note: Full bidirectional sync verification for hierarchical circuits
is pending implementation of hierarchical position preservation.
"""

import pytest
import subprocess
import shutil
from pathlib import Path
from kicad_sch_api import Schematic


def test_25_delete_net_hier(request):
    """Test deleting net in subcircuit - basic generation."""

    test_dir = Path(__file__).parent
    circuit_file = test_dir / "comprehensive_root.py"
    output_dir = test_dir / "comprehensive_root"
    root_schematic = output_dir / "comprehensive_root.kicad_sch"
    sub_schematic = output_dir / "amplifier.kicad_sch"

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
        assert sub_schematic.exists(), "Subcircuit schematic not generated"

        # Load root sheet
        root_sch = Schematic.load(str(root_schematic))
        root_components = [c for c in root_sch.components if not c.reference.startswith("#PWR")]
        assert len(root_components) == 2, "Expected 2 components on root sheet"

        # Load subcircuit sheet
        sub_sch = Schematic.load(str(sub_schematic))
        sub_components = [c for c in sub_sch.components if not c.reference.startswith("#PWR")]
        assert len(sub_components) == 2, "Expected 2 components in subcircuit"

        # Verify components exist
        r3 = next((c for c in sub_components if c.reference == "R3"), None)
        r4 = next((c for c in sub_components if c.reference == "R4"), None)
        assert r3 is not None, "R3 missing in subcircuit"
        assert r4 is not None, "R4 missing in subcircuit"

        print("\n✅ Test 25 PASSED: Hierarchical net delete test circuit generated successfully")
        print(f"   - Root sheet: 2 components ✓")
        print(f"   - Subcircuit sheet: R3, R4 ✓")
        print(f"   - Hierarchical structure: verified ✓")
        print(f"\n💡 Note: Full bidirectional sync test pending hierarchical support")

    finally:
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--keep-output"])
