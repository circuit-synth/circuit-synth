#!/usr/bin/env python3
"""
Integration test for Issue #551: Power symbols placement instead of hierarchical labels.

This test verifies that when a circuit is loaded from JSON (without explicit is_power metadata),
power nets like GND, VCC are auto-detected and generate power symbols in the KiCad schematic
instead of hierarchical labels.

Issue: https://github.com/shanemmattner/circuit-synth/issues/551
"""

import json
import re
import tempfile
from pathlib import Path

import pytest


def test_json_loaded_circuit_generates_power_symbols():
    """
    End-to-end test: JSON → circuit_loader → schematic generation → power symbols.

    Bug before fix: GND in JSON generates hierarchical_label in .kicad_sch
    Expected after fix: GND in JSON generates power:GND symbol in .kicad_sch
    """
    # Create a circuit JSON with GND and VCC (no is_power metadata)
    circuit_json = {
        "name": "power_test",
        "components": {
            "R1": {
                "symbol": "Device:R",
                "ref": "R1",
                "value": "10k",
                "footprint": "Resistor_SMD:R_0603_1608Metric",
                "pins": [
                    {
                        "pin_id": "1",
                        "name": "~",
                        "func": "passive",
                        "unit": 1,
                        "x": 0,
                        "y": 2.54,
                        "length": 2.54,
                        "orientation": 180,
                    },
                    {
                        "pin_id": "2",
                        "name": "~",
                        "func": "passive",
                        "unit": 1,
                        "x": 0,
                        "y": -2.54,
                        "length": 2.54,
                        "orientation": 0,
                    },
                ],
            },
            "R2": {
                "symbol": "Device:R",
                "ref": "R2",
                "value": "1k",
                "footprint": "Resistor_SMD:R_0603_1608Metric",
                "pins": [
                    {
                        "pin_id": "1",
                        "name": "~",
                        "func": "passive",
                        "unit": 1,
                        "x": 0,
                        "y": 2.54,
                        "length": 2.54,
                        "orientation": 180,
                    },
                    {
                        "pin_id": "2",
                        "name": "~",
                        "func": "passive",
                        "unit": 1,
                        "x": 0,
                        "y": -2.54,
                        "length": 2.54,
                        "orientation": 0,
                    },
                ],
            },
        },
        "nets": {
            "VCC": {
                "nodes": [
                    {"component": "R1", "pin": {"number": "1", "name": "~", "type": "passive"}}
                ]
                # No is_power metadata - should auto-detect!
            },
            "SIGNAL": {
                "nodes": [
                    {"component": "R1", "pin": {"number": "2", "name": "~", "type": "passive"}},
                    {"component": "R2", "pin": {"number": "1", "name": "~", "type": "passive"}},
                ]
                # Regular signal net - should use hierarchical labels
            },
            "GND": {
                "nodes": [
                    {"component": "R2", "pin": {"number": "2", "name": "~", "type": "passive"}}
                ]
                # No is_power metadata - should auto-detect!
            },
        },
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        # Write JSON file
        json_path = Path(tmpdir) / "power_test.json"
        with open(json_path, "w") as f:
            json.dump(circuit_json, f)

        # Load circuit using circuit_loader
        from circuit_synth.kicad.sch_gen.circuit_loader import load_circuit_hierarchy

        circuit, subcircuits = load_circuit_hierarchy(str(json_path))

        # Verify nets are loaded with correct is_power flags
        gnd_net = None
        vcc_net = None
        signal_net = None

        for net in circuit.nets:
            if net.name == "GND":
                gnd_net = net
            elif net.name == "VCC":
                vcc_net = net
            elif net.name == "SIGNAL":
                signal_net = net

        assert gnd_net is not None
        assert gnd_net.is_power is True
        assert gnd_net.power_symbol == "power:GND"

        assert vcc_net is not None
        assert vcc_net.is_power is True
        assert vcc_net.power_symbol == "power:VCC"

        assert signal_net is not None
        assert signal_net.is_power is False
        assert signal_net.power_symbol is None

        # Now generate KiCad schematic
        from circuit_synth.kicad.sch_gen.main_generator import SchematicGenerator

        generator = SchematicGenerator(
            output_dir=tmpdir,
            project_name="power_test",
        )

        result = generator.generate_project(
            json_file=str(json_path),
            schematic_placement="simple",
            generate_pcb=False,
        )

        assert result["success"] is True

        # Check generated schematic file
        sch_file = Path(tmpdir) / "power_test" / "power_test.kicad_sch"
        assert sch_file.exists(), f"Schematic file not found: {sch_file}"

        content = sch_file.read_text()

        # Verify GND uses power symbol, not hierarchical label
        assert 'lib_id "power:GND"' in content, "GND should generate power:GND symbol"
        assert (
            'hierarchical_label "GND"' not in content
        ), "GND should NOT generate hierarchical label"

        # Verify VCC uses power symbol, not hierarchical label
        assert 'lib_id "power:VCC"' in content, "VCC should generate power:VCC symbol"
        assert (
            'hierarchical_label "VCC"' not in content
        ), "VCC should NOT generate hierarchical label"

        # Verify regular SIGNAL net still uses hierarchical label
        assert (
            'hierarchical_label "SIGNAL"' in content
        ), "SIGNAL should generate hierarchical label"

        # Verify power symbols have #PWR references
        pwr_refs = re.findall(r'reference "#PWR\d+"', content)
        assert len(pwr_refs) >= 2, f"Should have at least 2 power symbols, found {len(pwr_refs)}"

        print(f"✅ Test passed! Generated {len(pwr_refs)} power symbols")
        print(f"   - GND: power symbol ✓")
        print(f"   - VCC: power symbol ✓")
        print(f"   - SIGNAL: hierarchical label ✓")


if __name__ == "__main__":
    pytest.main([__file__, "-xvs"])
