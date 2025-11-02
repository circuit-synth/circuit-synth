#!/usr/bin/env python3
"""Test 03: PCB Net Definitions"""
import pytest, subprocess, shutil
from pathlib import Path

def test_03_pcb(request):
    """Test Verify nets defined in PCB."""
    test_dir = Path(__file__).parent
    circuit_file = test_dir / "pcb_nets.py"
    output_dir = test_dir / "pcb_nets"
    schematic_file = output_dir / "pcb_nets.kicad_sch"
    cleanup = not request.config.getoption("--keep-output", default=False)

    try:
        # Generate circuit
        result = subprocess.run(["uv", "run", str(circuit_file)], cwd=test_dir, capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, f"Generation failed: {result.stderr}"
        assert schematic_file.exists(), "Schematic not generated"

        # Verify PCB has net definitions
        pcb_file = output_dir / "pcb_nets.kicad_pcb"
        assert pcb_file.exists(), "PCB file not generated"

        pcb_content = pcb_file.read_text()
        assert "(net " in pcb_content, "No net definitions found"

        # Check for specific nets
        assert "VCC" in pcb_content or "Net-" in pcb_content, "No nets found in PCB"

        # Count nets
        net_count = pcb_content.count("(net ")
        print(f"\n✅ Test 03 PASSED: PCB Net Definitions")
        print(f"   Nets in PCB: {net_count}")
    finally:
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--keep-output"])
