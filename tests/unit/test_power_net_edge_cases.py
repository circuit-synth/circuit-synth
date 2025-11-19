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

    @pytest.mark.parametrize("net_name", ["AGND", "DGND", "PGND"])
    def test_ground_variants(self, net_name):
        """
        Common ground variants (AGND, DGND, PGND) might not be in registry.

        This is a KNOWN LIMITATION - these nets will need explicit is_power=True
        unless we add them to the PowerNetRegistry.
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

            # Known limitation: these might not be in registry
            # Document the current behavior
            from circuit_synth.core.power_net_registry import is_power_net
            if is_power_net(net_name):
                assert net.is_power is True, f"{net_name} in registry, should auto-detect"
            else:
                pytest.skip(f"{net_name} not in registry - known limitation")

        finally:
            Path(json_path).unlink()

    @pytest.mark.parametrize("net_name", ["VBAT", "VIN", "VOUT"])
    def test_voltage_rail_variants(self, net_name):
        """
        Common voltage rails (VBAT, VIN, VOUT) might not be in registry.

        KNOWN LIMITATION: These nets will need explicit is_power=True.
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

            # Check if in registry
            from circuit_synth.core.power_net_registry import is_power_net
            if is_power_net(net_name):
                assert net.is_power is True, f"{net_name} in registry, should auto-detect"
            else:
                # Known limitation - document it
                assert net.is_power is False, f"{net_name} not in registry"
                pytest.skip(f"{net_name} not in registry - known limitation, need explicit is_power=True")

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
