#!/usr/bin/env python3
"""
Test power net auto-detection in hierarchical circuits.

Verifies that power nets in subcircuits are properly auto-detected
and generate power symbols instead of hierarchical labels.
"""

import json
import re
import tempfile
from pathlib import Path

import pytest


def test_hierarchical_circuit_power_nets():
    """
    Test that power nets in subcircuits auto-detect correctly.

    Scenario: Parent circuit and subcircuit both use GND and VCC.
    Expected: Both should generate power symbols, not hierarchical labels.
    """
    # Create hierarchical circuit with subcircuit
    circuit_json = {
        "name": "parent",
        "components": {
            "R1": {
                "symbol": "Device:R",
                "ref": "R1",
                "value": "10k",
                "footprint": "Resistor_SMD:R_0603_1608Metric",
                "pins": [
                    {"pin_id": "1", "name": "~", "func": "passive", "unit": 1, "x": 0, "y": 2.54, "length": 2.54, "orientation": 180},
                    {"pin_id": "2", "name": "~", "func": "passive", "unit": 1, "x": 0, "y": -2.54, "length": 2.54, "orientation": 0}
                ]
            }
        },
        "nets": {
            "VCC": {
                "nodes": [{"component": "R1", "pin": {"number": "1"}}]
            },
            "GND": {
                "nodes": [{"component": "R1", "pin": {"number": "2"}}]
            }
        },
        "subcircuits": [
            {
                "name": "child",
                "components": {
                    "R2": {
                        "symbol": "Device:R",
                        "ref": "R2",
                        "value": "1k",
                        "footprint": "Resistor_SMD:R_0603_1608Metric",
                        "pins": [
                            {"pin_id": "1", "name": "~", "func": "passive", "unit": 1, "x": 0, "y": 2.54, "length": 2.54, "orientation": 180},
                            {"pin_id": "2", "name": "~", "func": "passive", "unit": 1, "x": 0, "y": -2.54, "length": 2.54, "orientation": 0}
                        ]
                    }
                },
                "nets": {
                    "VCC": {
                        "nodes": [{"component": "R2", "pin": {"number": "1"}}]
                    },
                    "GND": {
                        "nodes": [{"component": "R2", "pin": {"number": "2"}}]
                    }
                }
            }
        ]
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "parent.json"
        with open(json_path, "w") as f:
            json.dump(circuit_json, f)

        # Load hierarchy
        from circuit_synth.kicad.sch_gen.circuit_loader import load_circuit_hierarchy

        parent, subcircuits = load_circuit_hierarchy(str(json_path))

        # Verify parent circuit power nets
        parent_gnd = next((net for net in parent.nets if net.name == "GND"), None)
        parent_vcc = next((net for net in parent.nets if net.name == "VCC"), None)

        assert parent_gnd is not None, "Parent should have GND net"
        assert parent_gnd.is_power is True, "Parent GND should auto-detect"
        assert parent_gnd.power_symbol == "power:GND"

        assert parent_vcc is not None, "Parent should have VCC net"
        assert parent_vcc.is_power is True, "Parent VCC should auto-detect"
        assert parent_vcc.power_symbol == "power:VCC"

        # Verify subcircuit power nets
        assert "child" in subcircuits, "Should have child subcircuit"
        child = subcircuits["child"]

        child_gnd = next((net for net in child.nets if net.name == "GND"), None)
        child_vcc = next((net for net in child.nets if net.name == "VCC"), None)

        assert child_gnd is not None, "Child should have GND net"
        assert child_gnd.is_power is True, "Child GND should auto-detect"
        assert child_gnd.power_symbol == "power:GND"

        assert child_vcc is not None, "Child should have VCC net"
        assert child_vcc.is_power is True, "Child VCC should auto-detect"
        assert child_vcc.power_symbol == "power:VCC"

        # Generate schematics and verify both parent and child use power symbols
        from circuit_synth.kicad.sch_gen.main_generator import SchematicGenerator

        generator = SchematicGenerator(
            output_dir=tmpdir,
            project_name="parent",
        )

        result = generator.generate_project(
            json_file=str(json_path),
            schematic_placement="simple",
            generate_pcb=False,
        )

        assert result["success"] is True

        # Check parent schematic
        parent_sch = Path(tmpdir) / "parent" / "parent.kicad_sch"
        assert parent_sch.exists()
        parent_content = parent_sch.read_text()

        assert 'lib_id "power:GND"' in parent_content, "Parent should use GND power symbol"
        assert 'lib_id "power:VCC"' in parent_content, "Parent should use VCC power symbol"

        # Check child schematic
        child_sch = Path(tmpdir) / "parent" / "child.kicad_sch"
        assert child_sch.exists()
        child_content = child_sch.read_text()

        assert 'lib_id "power:GND"' in child_content, "Child should use GND power symbol"
        assert 'lib_id "power:VCC"' in child_content, "Child should use VCC power symbol"

        # Verify NO hierarchical labels for power nets
        assert 'hierarchical_label "GND"' not in parent_content, "Parent should NOT have GND hierarchical label"
        assert 'hierarchical_label "VCC"' not in parent_content, "Parent should NOT have VCC hierarchical label"
        assert 'hierarchical_label "GND"' not in child_content, "Child should NOT have GND hierarchical label"
        assert 'hierarchical_label "VCC"' not in child_content, "Child should NOT have VCC hierarchical label"

        print("✅ Hierarchical circuit test passed!")
        print(f"   - Parent: {parent_content.count('lib_id \"power:')} power symbols")
        print(f"   - Child: {child_content.count('lib_id \"power:')} power symbols")


if __name__ == "__main__":
    pytest.main([__file__, "-xvs"])
