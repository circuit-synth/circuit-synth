#!/usr/bin/env python3
"""Test 04: PCB Layer Structure"""
import pytest, subprocess, shutil
from pathlib import Path

def test_04_pcb(request):
    """Test Verify PCB has proper layer definitions."""
    test_dir = Path(__file__).parent
    circuit_file = test_dir / "pcb_layers.py"
    output_dir = test_dir / "pcb_layers"
    schematic_file = output_dir / "pcb_layers.kicad_sch"
    cleanup = not request.config.getoption("--keep-output", default=False)

    try:
        # Generate circuit
        result = subprocess.run(["uv", "run", str(circuit_file)], cwd=test_dir, capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, f"Generation failed: {result.stderr}"
        assert schematic_file.exists(), "Schematic not generated"

        # Verify PCB has layer definitions
        pcb_file = output_dir / "pcb_layers.kicad_pcb"
        assert pcb_file.exists(), "PCB file not generated"

        pcb_content = pcb_file.read_text()
        assert "(layers" in pcb_content, "No layer definitions found"

        # Check for standard layers
        assert "F.Cu" in pcb_content or '0 "F.Cu"' in pcb_content, "Front copper layer missing"
        assert "B.Cu" in pcb_content or '31 "B.Cu"' in pcb_content, "Back copper layer missing"

        print(f"\n✅ Test 04 PASSED: PCB Layer Structure")
    finally:
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--keep-output"])
