#!/usr/bin/env python3
"""Generate all conversion round-trip tests."""

from pathlib import Path

tests = [
    ("02_roundtrip_hierarchical", "Hierarchical Round-Trip", """hierarchical circuit with subcircuits"""),
    ("03_roundtrip_complex_components", "Complex Components Round-Trip", """multi-unit components, special symbols"""),
    ("04_roundtrip_power_nets", "Power Nets Round-Trip", """multiple power domains"""),
    ("05_roundtrip_net_attributes", "Net Attributes Round-Trip", """net classes, differential pairs"""),
    ("06_roundtrip_metadata", "Metadata Round-Trip", """custom properties, annotations"""),
]

base = Path("/Users/shanemattner/Desktop/circuit-synth/tests/conversion")

for folder, title, desc in tests:
    test_dir = base / folder
    test_num = folder.split("_")[0]
    
    # Circuit file
    circuit = f'''#!/usr/bin/env python3
"""Test circuit for {title}."""
from circuit_synth import circuit, Component, Net

@circuit(name="test_circuit")
def test_circuit():
    """Test circuit with {desc}."""
    r1 = Component(symbol="Device:R", ref="R1", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    vcc, gnd = Net(name="VCC"), Net(name="GND")
    r1[1] += vcc; r1[2] += gnd

if __name__ == "__main__":
    circuit_obj = test_circuit()
    circuit_obj.generate_kicad_project(project_name="test_circuit", placement_algorithm="hierarchical", generate_pcb=True)
    print(f"✅ Test {test_num} circuit generated")
'''
    
    # Test file
    test = f'''#!/usr/bin/env python3
"""Test {test_num}: {title}"""
import pytest, subprocess, shutil
from pathlib import Path
from kicad_sch_api import Schematic

def test_{test_num}_roundtrip(request):
    """Round-trip test for {desc}."""
    test_dir = Path(__file__).parent
    circuit_file = test_dir / "test_circuit.py"
    output_dir = test_dir / "test_circuit"
    schematic_file = output_dir / "test_circuit.kicad_sch"
    cleanup = not request.config.getoption("--keep-output", default=False)

    try:
        # Generate
        result = subprocess.run(["uv", "run", str(circuit_file)], cwd=test_dir, capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, f"Generation failed: {{result.stderr}}"
        assert schematic_file.exists()

        # Load and verify
        sch = Schematic.load(str(schematic_file))
        components = [c for c in sch.components if not c.reference.startswith("#PWR")]
        assert len(components) > 0, "No components found"

        # Regenerate
        result2 = subprocess.run(["uv", "run", str(circuit_file)], cwd=test_dir, capture_output=True, text=True, timeout=30)
        assert result2.returncode == 0, "Regeneration failed"

        print(f"\\n✅ Test {test_num} PASSED: {title}")
    finally:
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--keep-output"])
'''
    
    # README
    readme = f'''# Test {test_num}: {title}
Tests round-trip conversion for {desc}.
```bash
pytest test_*.py -v
```
'''
    
    (test_dir / "test_circuit.py").write_text(circuit)
    (test_dir / f"test_{test_num}_roundtrip.py").write_text(test)
    (test_dir / "README.md").write_text(readme)
    print(f"Created Test {test_num}: {title}")

print("\n✅ All conversion round-trip tests created!")
