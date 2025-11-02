#!/usr/bin/env python3
"""Test 48: Invalid Component Values"""

import pytest
import subprocess
import shutil
from pathlib import Path
from kicad_sch_api import Schematic


def test_48_invalid_values(request):
    """Test invalid value handling."""
    test_dir = Path(__file__).parent
    circuit_file = test_dir / "comprehensive_root.py"
    output_dir = test_dir / "comprehensive_root"
    root_schematic = output_dir / "comprehensive_root.kicad_sch"
    cleanup = not request.config.getoption("--keep-output", default=False)

    try:
        result = subprocess.run(["uv", "run", str(circuit_file)], cwd=test_dir, capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, f"Generation failed: {result.stderr}"
        assert root_schematic.exists()

        root_sch = Schematic.load(str(root_schematic))
        components = [c for c in root_sch.components if not c.reference.startswith("#PWR")]
        assert len(components) == 3
        print("\n✅ Test 48 PASSED: Invalid values handled gracefully")
    finally:
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--keep-output"])
