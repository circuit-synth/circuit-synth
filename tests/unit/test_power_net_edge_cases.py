#!/usr/bin/env python3
"""
Edge case tests for power net auto-detection.

Tests edge cases like:
- Case sensitivity
- Missing common power nets (AGND, VBAT, VIN, VOUT)
- Hierarchical circuits with power nets
- Explicit power_symbol without is_power
"""

import json
import tempfile
from pathlib import Path

import pytest


class TestCaseSensitivity:
    """Test case sensitivity of power net names."""

    def test_lowercase_gnd_not_detected(self):
        """Lowercase 'gnd' should NOT auto-detect (registry is case-sensitive)."""
        circuit_json = {
            "name": "test",
            "components": {
                "R1": {
                    "symbol": "Device:R",
                    "ref": "R1",
                    "value": "10k",
                    "pins": [
                        {"pin_id": "1", "name": "~", "func": "passive", "unit": 1, "x": 0, "y": 2.54, "length": 2.54, "orientation": 180},
                        {"pin_id": "2", "name": "~", "func": "passive", "unit": 1, "x": 0, "y": -2.54, "length": 2.54, "orientation": 0}
                    ]
                }
            },
            "nets": {
                "gnd": {  # Lowercase!
                    "nodes": [{"component": "R1", "pin": {"number": "2"}}]
                }
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(circuit_json, f)
            json_path = f.name

        try:
            from circuit_synth.kicad.sch_gen.circuit_loader import load_circuit_hierarchy

            circuit, _ = load_circuit_hierarchy(json_path)

            gnd_net = next((net for net in circuit.nets if net.name == "gnd"), None)
            assert gnd_net is not None

            # Case-sensitive registry won't recognize lowercase "gnd"
            assert gnd_net.is_power is False, "Lowercase 'gnd' should NOT auto-detect"
            assert gnd_net.power_symbol is None

        finally:
            Path(json_path).unlink()


class TestMissingCommonPowerNets:
    """Test commonly used power nets that might not be in registry."""

    @pytest.mark.parametrize("net_name,expected_symbol", [
        ("AGND", "power:GND"),
        ("DGND", "power:GND"),
        ("PGND", "power:GND"),
    ])
    def test_ground_variants(self, net_name, expected_symbol):
        """
        Common ground variants (AGND, DGND, PGND) should auto-detect.

        These are now in the PowerNetRegistry builtin defaults and map to power:GND.
        """
        circuit_json = {
            "name": "test",
            "components": {
                "R1": {
                    "symbol": "Device:R",
                    "ref": "R1",
                    "value": "10k",
                    "pins": [
                        {"pin_id": "1", "name": "~", "func": "passive", "unit": 1, "x": 0, "y": 2.54, "length": 2.54, "orientation": 180},
                        {"pin_id": "2", "name": "~", "func": "passive", "unit": 1, "x": 0, "y": -2.54, "length": 2.54, "orientation": 0}
                    ]
                }
            },
            "nets": {
                net_name: {
                    "nodes": [{"component": "R1", "pin": {"number": "2"}}]
                }
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(circuit_json, f)
            json_path = f.name

        try:
            from circuit_synth.kicad.sch_gen.circuit_loader import load_circuit_hierarchy

            circuit, _ = load_circuit_hierarchy(json_path)

            net = next((n for n in circuit.nets if n.name == net_name), None)
            assert net is not None

            # These ground variants should now auto-detect
            assert net.is_power is True, f"{net_name} should auto-detect as power net"
            assert net.power_symbol == expected_symbol, f"{net_name} should use {expected_symbol}"

        finally:
            Path(json_path).unlink()

    @pytest.mark.parametrize("net_name", ["VBAT", "VIN", "VOUT"])
    def test_voltage_rail_variants(self, net_name):
        """
        Common voltage rails (VBAT, VIN, VOUT) should auto-detect.

        These are now in the PowerNetRegistry builtin defaults.
        """
        circuit_json = {
            "name": "test",
            "components": {
                "R1": {
                    "symbol": "Device:R",
                    "ref": "R1",
                    "value": "10k",
                    "pins": [
                        {"pin_id": "1", "name": "~", "func": "passive", "unit": 1, "x": 0, "y": 2.54, "length": 2.54, "orientation": 180},
                        {"pin_id": "2", "name": "~", "func": "passive", "unit": 1, "x": 0, "y": -2.54, "length": 2.54, "orientation": 0}
                    ]
                }
            },
            "nets": {
                net_name: {
                    "nodes": [{"component": "R1", "pin": {"number": "1"}}]
                }
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(circuit_json, f)
            json_path = f.name

        try:
            from circuit_synth.kicad.sch_gen.circuit_loader import load_circuit_hierarchy

            circuit, _ = load_circuit_hierarchy(json_path)

            net = next((n for n in circuit.nets if n.name == net_name), None)
            assert net is not None

            # These voltage rails should now auto-detect
            assert net.is_power is True, f"{net_name} should auto-detect as power net"
            assert net.power_symbol == f"power:{net_name}", f"{net_name} should use power:{net_name}"

        finally:
            Path(json_path).unlink()


class TestExplicitPowerSymbolWithoutIsPower:
    """Test behavior when power_symbol is specified without is_power."""

    def test_power_symbol_without_is_power_ignored(self):
        """
        If power_symbol is specified but is_power is not set,
        the net should still auto-detect based on name.
        """
        circuit_json = {
            "name": "test",
            "components": {
                "R1": {
                    "symbol": "Device:R",
                    "ref": "R1",
                    "value": "10k",
                    "pins": [
                        {"pin_id": "1", "name": "~", "func": "passive", "unit": 1, "x": 0, "y": 2.54, "length": 2.54, "orientation": 180},
                        {"pin_id": "2", "name": "~", "func": "passive", "unit": 1, "x": 0, "y": -2.54, "length": 2.54, "orientation": 0}
                    ]
                }
            },
            "nets": {
                "GND": {
                    "power_symbol": "power:+5V",  # Wrong symbol for GND!
                    # No is_power specified
                    "nodes": [{"component": "R1", "pin": {"number": "2"}}]
                }
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(circuit_json, f)
            json_path = f.name

        try:
            from circuit_synth.kicad.sch_gen.circuit_loader import load_circuit_hierarchy

            circuit, _ = load_circuit_hierarchy(json_path)

            gnd_net = next((net for net in circuit.nets if net.name == "GND"), None)
            assert gnd_net is not None

            # Should auto-detect GND and use the explicitly provided power_symbol
            assert gnd_net.is_power is True, "GND should auto-detect"
            # The explicit power_symbol should be preserved (even if wrong!)
            assert gnd_net.power_symbol == "power:+5V", "Explicit power_symbol should be used"

        finally:
            Path(json_path).unlink()


class TestEmptyNetNames:
    """Test handling of empty or None net names."""

    def test_empty_net_name(self):
        """Empty net name should not crash and should not auto-detect."""
        circuit_json = {
            "name": "test",
            "components": {
                "R1": {
                    "symbol": "Device:R",
                    "ref": "R1",
                    "value": "10k",
                    "pins": [
                        {"pin_id": "1", "name": "~", "func": "passive", "unit": 1, "x": 0, "y": 2.54, "length": 2.54, "orientation": 180},
                        {"pin_id": "2", "name": "~", "func": "passive", "unit": 1, "x": 0, "y": -2.54, "length": 2.54, "orientation": 0}
                    ]
                }
            },
            "nets": {
                "": {  # Empty string!
                    "nodes": [{"component": "R1", "pin": {"number": "2"}}]
                }
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(circuit_json, f)
            json_path = f.name

        try:
            from circuit_synth.kicad.sch_gen.circuit_loader import load_circuit_hierarchy

            circuit, _ = load_circuit_hierarchy(json_path)

            empty_net = next((net for net in circuit.nets if net.name == ""), None)
            assert empty_net is not None

            # Empty name should not trigger auto-detection (code checks `if net_name:`)
            assert empty_net.is_power is False
            assert empty_net.power_symbol is None

        finally:
            Path(json_path).unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
