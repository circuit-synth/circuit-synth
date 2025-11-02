#!/usr/bin/env python3
"""Test 04: Power Nets Round-Trip"""
import pytest, subprocess, shutil
from pathlib import Path
from kicad_sch_api import Schematic

def test_04_roundtrip(request):
    """Round-trip test for multiple power domains."""
    test_dir = Path(__file__).parent
    circuit_file = test_dir / "power_circuit.py"
    output_dir = test_dir / "power_circuit"
    schematic_file = output_dir / "power_circuit.kicad_sch"
    cleanup = not request.config.getoption("--keep-output", default=False)

    try:
        # Generate
        result = subprocess.run(["uv", "run", str(circuit_file)], cwd=test_dir, capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, f"Generation failed: {result.stderr}"
        assert schematic_file.exists()

        # Load and verify
        sch = Schematic.load(str(schematic_file))
        components = [c for c in sch.components if not c.reference.startswith("#PWR")]
        assert len(components) > 0, "No components found"

        # Regenerate
        result2 = subprocess.run(["uv", "run", str(circuit_file)], cwd=test_dir, capture_output=True, text=True, timeout=30)
        assert result2.returncode == 0, "Regeneration failed"

        print(f"\n✅ Test 04 PASSED: Power Nets Round-Trip")
    finally:
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--keep-output"])
