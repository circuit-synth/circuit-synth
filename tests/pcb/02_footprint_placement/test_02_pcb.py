#!/usr/bin/env python3
"""Test 02: Footprint Placement"""
import pytest, subprocess, shutil
from pathlib import Path

def test_02_pcb(request):
    """Test Verify footprints placed in PCB."""
    test_dir = Path(__file__).parent
    circuit_file = test_dir / "footprint_test.py"
    output_dir = test_dir / "footprint_test"
    schematic_file = output_dir / "footprint_test.kicad_sch"
    cleanup = not request.config.getoption("--keep-output", default=False)

    try:
        # Generate circuit
        result = subprocess.run(["uv", "run", str(circuit_file)], cwd=test_dir, capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, f"Generation failed: {result.stderr}"
        assert schematic_file.exists(), "Schematic not generated"

        # Verify PCB file has footprints
        pcb_file = output_dir / "footprint_test.kicad_pcb"
        assert pcb_file.exists(), "PCB file not generated"

        pcb_content = pcb_file.read_text()
        assert "footprint" in pcb_content.lower(), "No footprints found in PCB"

        # Count footprints
        footprint_count = pcb_content.lower().count("(footprint")
        assert footprint_count >= 3, f"Expected >= 3 footprints, found {footprint_count}"

        print(f"\n✅ Test 02 PASSED: Footprint Placement")
        print(f"   Footprints in PCB: {footprint_count}")
    finally:
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--keep-output"])
