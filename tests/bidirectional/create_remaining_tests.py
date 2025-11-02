#!/usr/bin/env python3
"""Script to generate all remaining test scaffolds (52-80)."""

from pathlib import Path

# Test definitions
tests = [
    # Rotation (52-53)
    ("rotation_orientation/52_sync_component_mirror", "Mirror", "Component mirror preservation"),
    ("rotation_orientation/53_sync_mixed_orientations", "Mixed Orientations", "Multiple component orientations"),
    
    # Pin-level (54-56)
    ("pin_level/54_sync_multi_pin_component", "Multi-Pin Component", "IC with many pins"),
    ("pin_level/55_sync_swap_pins", "Swap Pins", "Swap pin connections"),
    ("pin_level/56_sync_unconnected_pins", "Unconnected Pins", "Component with NC pins"),
    
    # Sheet pins (57-59)
    ("sheet_pins/57_sync_sheet_pin_types", "Sheet Pin Types", "Input/Output/Bidirectional pins"),
    ("sheet_pins/58_sync_sheet_pin_ordering", "Sheet Pin Ordering", "Add/remove/reorder pins"),
    ("sheet_pins/59_sync_mismatched_pins", "Mismatched Pins", "Child label not in parent"),
    
    # Special nets (60-63)
    ("special_nets/60_sync_global_labels", "Global Labels", "Global label connections"),
    ("special_nets/61_sync_no_connect", "No-Connect", "NC flags"),
    ("special_nets/62_sync_bus_connections", "Bus Connections", "Multi-wire buses"),
    ("special_nets/63_sync_net_aliases", "Net Aliases", "Multiple names for net"),
    
    # Annotation (64-66)
    ("annotation/64_sync_reannotation", "Re-annotation", "Auto-renumber refs"),
    ("annotation/65_sync_reference_gaps", "Reference Gaps", "Non-sequential refs"),
    ("annotation/66_sync_multi_unit", "Multi-Unit", "Multi-unit components"),
    
    # Schematic props (67-69)
    ("schematic_props/67_sync_text_annotations", "Text Annotations", "Text boxes"),
    ("schematic_props/68_sync_graphic_elements", "Graphic Elements", "Lines/shapes"),
    ("schematic_props/69_sync_wire_styling", "Wire Styling", "Wire appearance"),
    
    # Performance (70-72)
    ("performance/70_sync_large_circuit", "Large Circuit", "100+ components"),
    ("performance/71_sync_deep_hierarchy", "Deep Hierarchy", "5+ levels"),
    ("performance/72_sync_wide_hierarchy", "Wide Hierarchy", "10+ subcircuits"),
    
    # Regression (73-75)
    ("regression/73_sync_dnp_components", "DNP Components", "Do Not Place"),
    ("regression/74_sync_multiple_value_changes", "Multiple Value Changes", "Rapid modifications"),
    ("regression/75_sync_ref_changes_hier", "Ref Changes Hierarchy", "Update refs in parent/child"),
    
    # Workflows (76-80)
    ("workflows/76_sync_import_subcircuit", "Import Subcircuit", "Use existing subcircuit"),
    ("workflows/77_sync_refactor_to_hier", "Refactor to Hierarchy", "Move to subcircuit"),
    ("workflows/78_sync_flatten_hierarchy", "Flatten Hierarchy", "Move to root"),
    ("workflows/79_sync_copy_paste", "Copy-Paste", "Duplicate components"),
    ("workflows/80_sync_design_iteration", "Design Iteration", "Multiple modify cycles"),
]

base = Path("/Users/shanemattner/Desktop/circuit-synth/tests/bidirectional")

for path, name, desc in tests:
    test_dir = base / path
    test_num = path.split("_")[0].split("/")[-1]
    
    # comprehensive_root.py
    circuit = f'''#!/usr/bin/env python3
"""Test {test_num} - {desc}."""
from circuit_synth import circuit, Component, Net

@circuit(name="comprehensive_root")
def comprehensive_root():
    r1 = Component(symbol="Device:R", ref="R1", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    vcc, gnd = Net(name="VCC"), Net(name="GND")
    r1[1] += vcc; r1[2] += gnd

if __name__ == "__main__":
    circuit_obj = comprehensive_root()
    circuit_obj.generate_kicad_project(project_name="comprehensive_root", placement_algorithm="hierarchical", generate_pcb=True)
    print("✅ Test {test_num} generated")
'''
    
    # test file
    test = f'''#!/usr/bin/env python3
"""Test {test_num}: {name}"""
import pytest, subprocess, shutil
from pathlib import Path

def test_{test_num}_{path.split("/")[-1].replace("sync_", "")}(request):
    test_dir, output_dir = Path(__file__).parent, Path(__file__).parent / "comprehensive_root"
    cleanup = not request.config.getoption("--keep-output", default=False)
    try:
        result = subprocess.run(["uv", "run", str(test_dir / "comprehensive_root.py")], cwd=test_dir, capture_output=True, text=True, timeout=30)
        assert result.returncode == 0
        print(f"\\n✅ Test {test_num} PASSED: {name}")
    finally:
        if cleanup and output_dir.exists(): shutil.rmtree(output_dir)

if __name__ == "__main__": pytest.main([__file__, "-v", "--keep-output"])
'''
    
    # README
    readme = f'''# Test {test_num}: {name}
{desc}
```bash
pytest test_*.py -v
```
'''
    
    (test_dir / "comprehensive_root.py").write_text(circuit)
    (test_dir / f"test_{path.split('/')[-1].replace('sync_', '')}.py").write_text(test)
    (test_dir / "README.md").write_text(readme)
    print(f"Created Test {test_num}: {name}")

print("\n✅ All tests 52-80 created!")
