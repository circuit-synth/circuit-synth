#!/usr/bin/env python3
"""Test Issue #238: Text Class Parameters"""
import pytest, subprocess, shutil
from pathlib import Path

def test_issue_238(request):
    """Regression test: Verify Text class accepts parameters in correct order."""
    test_dir = Path(__file__).parent
    circuit_file = test_dir / "text_parameters_circuit.py"
    output_dir = test_dir / "text_test"
    cleanup = not request.config.getoption("--keep-output", default=False)

    try:
        # Generate circuit
        result = subprocess.run(["uv", "run", str(circuit_file)], cwd=test_dir, capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, f"Generation failed: {result.stderr}"

        # Verify schematic generated
        schematic_file = output_dir / "text_test.kicad_sch"
        assert schematic_file.exists(), "Schematic not generated"

        # Load and verify no errors with text/labels
        from kicad_sch_api import Schematic
        sch = Schematic.load(str(schematic_file))
        assert len(sch.components) > 0, "No components found"

        print(f"\n✅ Issue #238 PASSED: Text Class Parameters")
    finally:
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--keep-output"])
