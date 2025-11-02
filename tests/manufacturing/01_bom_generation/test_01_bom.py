#!/usr/bin/env python3
"""Test 01: BOM Generation"""
import pytest, subprocess, shutil, csv
from pathlib import Path

def test_01_bom_generation(request):
    """Test BOM (Bill of Materials) generation."""
    test_dir = Path(__file__).parent
    circuit_file = test_dir / "bom_circuit.py"
    output_dir = test_dir / "bom_circuit"
    schematic_file = output_dir / "bom_circuit.kicad_sch"
    cleanup = not request.config.getoption("--keep-output", default=False)

    try:
        # Generate circuit
        result = subprocess.run(["uv", "run", str(circuit_file)], cwd=test_dir, capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, f"Generation failed: {result.stderr}"
        assert schematic_file.exists(), "Schematic not generated"

        # Note: BOM generation typically requires KiCad CLI or Python-based extraction
        # For now, verify we can load the schematic and extract component data
        from kicad_sch_api import Schematic
        sch = Schematic.load(str(schematic_file))

        # Extract BOM data
        components = [c for c in sch.components if not c.reference.startswith("#PWR")]
        assert len(components) == 3, f"Expected 3 components, got {len(components)}"

        # Verify we have required BOM fields
        for comp in components:
            assert comp.reference, "Component missing reference"
            assert comp.value, "Component missing value"
            assert comp.footprint, "Component missing footprint"

        # Group by value for BOM
        bom = {}
        for comp in components:
            key = (comp.value, comp.footprint)
            if key not in bom:
                bom[key] = []
            bom[key].append(comp.reference)

        # Verify BOM structure
        assert len(bom) == 2, "Expected 2 BOM line items (2x 10k resistors grouped, 1x 100nF cap)"

        print(f"\n✅ Test 01 PASSED: BOM Generation")
        print(f"   BOM line items: {len(bom)}")
        print(f"   Total components: {len(components)}")
    finally:
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--keep-output"])
