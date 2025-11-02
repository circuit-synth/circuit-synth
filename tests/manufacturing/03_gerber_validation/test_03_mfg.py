#!/usr/bin/env python3
"""Test 03: PCB File Generation"""
import pytest, subprocess, shutil
from pathlib import Path

def test_03_manufacturing(request):
    """Test Verify PCB file generated and valid."""
    test_dir = Path(__file__).parent
    circuit_file = test_dir / "gerber_circuit.py"
    output_dir = test_dir / "gerber_circuit"
    schematic_file = output_dir / "gerber_circuit.kicad_sch"
    cleanup = not request.config.getoption("--keep-output", default=False)

    try:
        # Generate circuit
        result = subprocess.run(["uv", "run", str(circuit_file)], cwd=test_dir, capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, f"Generation failed: {result.stderr}"
        assert schematic_file.exists(), "Schematic not generated"

        # Verify PCB file generated
        pcb_file = output_dir / "gerber_circuit.kicad_pcb"
        assert pcb_file.exists(), "PCB file not generated"

        # Basic validation: file not empty and contains expected content
        pcb_content = pcb_file.read_text()
        assert len(pcb_content) > 0, "PCB file is empty"
        assert "kicad_pcb" in pcb_content, "PCB file doesn't appear to be valid KiCad PCB"
        assert "footprint" in pcb_content.lower(), "PCB file missing footprints"

        print(f"\n✅ Test 03 PASSED: PCB File Validation")
        print(f"   PCB file size: {len(pcb_content)} bytes")
    finally:
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--keep-output"])
