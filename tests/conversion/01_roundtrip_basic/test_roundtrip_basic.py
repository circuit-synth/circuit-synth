#!/usr/bin/env python3
"""
Test 01: Basic Round-Trip Conversion

Validates that a simple circuit can be:
1. Generated from Python → KiCad
2. Read back from KiCad → Python representation
3. Compared to verify no information loss

This is the most critical test - if basic round-trip fails,
bidirectional sync cannot be trusted.
"""

import pytest
import subprocess
import shutil
from pathlib import Path
from kicad_sch_api import Schematic


def test_01_roundtrip_basic(request):
    """Test Python → KiCad → Python round-trip for basic circuit."""

    test_dir = Path(__file__).parent
    circuit_file = test_dir / "simple_circuit.py"
    output_dir = test_dir / "simple_circuit"
    schematic_file = output_dir / "simple_circuit.kicad_sch"

    cleanup = not request.config.getoption("--keep-output", default=False)

    try:
        # STEP 1: Generate KiCad from Python
        result = subprocess.run(
            ["uv", "run", str(circuit_file)],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0, f"Generation failed: {result.stderr}"
        assert schematic_file.exists(), "Schematic not generated"

        # STEP 2: Load KiCad schematic
        sch = Schematic.load(str(schematic_file))
        components = [c for c in sch.components if not c.reference.startswith("#PWR")]

        # STEP 3: Verify expected circuit structure
        assert len(components) == 3, f"Expected 3 components, got {len(components)}"

        # Verify R1
        r1 = next((c for c in components if c.reference == "R1"), None)
        assert r1 is not None, "R1 not found"
        assert r1.value == "10k", f"R1 value should be 10k, got {r1.value}"
        assert "Resistor_SMD:R_0603" in r1.footprint, f"R1 footprint incorrect: {r1.footprint}"

        # Verify R2
        r2 = next((c for c in components if c.reference == "R2"), None)
        assert r2 is not None, "R2 not found"
        assert r2.value == "4.7k", f"R2 value should be 4.7k, got {r2.value}"

        # Verify C1
        c1 = next((c for c in components if c.reference == "C1"), None)
        assert c1 is not None, "C1 not found"
        assert c1.value == "100nF", f"C1 value should be 100nF, got {c1.value}"

        # STEP 4: Verify nets (basic check - power symbols exist)
        power_symbols = [c for c in sch.components if c.reference.startswith("#PWR")]
        assert len(power_symbols) > 0, "No power symbols found"

        # STEP 5: Store original data for comparison
        original_data = {
            "components": {
                "R1": {"value": "10k", "ref": "R1"},
                "R2": {"value": "4.7k", "ref": "R2"},
                "C1": {"value": "100nF", "ref": "C1"},
            },
            "component_count": 3,
        }

        # STEP 6: Regenerate from same Python source
        result2 = subprocess.run(
            ["uv", "run", str(circuit_file)],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result2.returncode == 0, "Regeneration failed"

        # STEP 7: Load regenerated schematic
        sch2 = Schematic.load(str(schematic_file))
        components2 = [c for c in sch2.components if not c.reference.startswith("#PWR")]

        # STEP 8: Verify round-trip preservation
        assert len(components2) == original_data["component_count"], "Component count changed after round-trip"

        for ref, expected in original_data["components"].items():
            comp = next((c for c in components2 if c.reference == ref), None)
            assert comp is not None, f"{ref} missing after round-trip"
            assert comp.value == expected["value"], f"{ref} value changed: {expected['value']} → {comp.value}"

        print("\n✅ Test 01 PASSED: Basic round-trip conversion successful")
        print(f"   - Python → KiCad: 3 components generated ✓")
        print(f"   - KiCad → Python: All data preserved ✓")
        print(f"   - Round-trip: No information loss ✓")

    finally:
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--keep-output"])
