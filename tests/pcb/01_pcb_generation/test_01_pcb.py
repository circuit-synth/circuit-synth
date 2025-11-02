#!/usr/bin/env python3
"""Test 01: PCB File Generation"""
import pytest, subprocess, shutil
from pathlib import Path

def test_01_pcb(request):
    """Test Verify PCB file generated with basic structure."""
    test_dir = Path(__file__).parent
    circuit_file = test_dir / "pcb_gen.py"
    output_dir = test_dir / "pcb_gen"
    schematic_file = output_dir / "pcb_gen.kicad_sch"
    cleanup = not request.config.getoption("--keep-output", default=False)

    try:
        # Generate circuit
        result = subprocess.run(["uv", "run", str(circuit_file)], cwd=test_dir, capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, f"Generation failed: {result.stderr}"
        assert schematic_file.exists(), "Schematic not generated"

        # Verify PCB file exists
        pcb_file = output_dir / "pcb_gen.kicad_pcb"
        assert pcb_file.exists(), "PCB file not generated"

        # Validate PCB content
        pcb_content = pcb_file.read_text()
        assert len(pcb_content) > 100, "PCB file too small to be valid"
        assert "kicad_pcb" in pcb_content, "Missing kicad_pcb header"
        assert "version" in pcb_content, "Missing version info"

        print(f"\n✅ Test 01 PASSED: PCB File Generation")
        print(f"   PCB file size: {len(pcb_content)} bytes")
    finally:
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--keep-output"])
