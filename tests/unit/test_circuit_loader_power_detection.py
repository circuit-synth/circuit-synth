#!/usr/bin/env python3
"""
Unit tests for power net auto-detection in circuit_loader.

Tests that circuit_loader.Net auto-detects power nets from names,
matching the behavior of circuit_synth.core.Net.

Issue: https://github.com/shanemmattner/circuit-synth/issues/551
"""

import json
import tempfile
from pathlib import Path

import pytest


def test_circuit_loader_autodetects_gnd_from_json():
    """
    Circuit loaded from JSON should auto-detect GND as power net.

    Bug: circuit_loader.Net doesn't auto-detect power nets, always defaults to is_power=False.
    Fix: Add auto-detection to Net.from_dict() method.
    """
    # Create a minimal circuit JSON with GND net (no is_power metadata)
    circuit_json = {
        "name": "test_circuit",
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
                "nodes": [
                    {"component": "R1", "pin": {"number": "2", "name": "~", "type": "passive"}}
                ]
                # Note: No is_power or power_symbol metadata - should auto-detect!
            }
        }
    }

    # Write to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(circuit_json, f)
        json_path = f.name

    try:
        # Load circuit using circuit_loader
        from circuit_synth.kicad.sch_gen.circuit_loader import load_circuit_hierarchy

        circuit, subcircuits = load_circuit_hierarchy(json_path)

        # Find GND net
        gnd_net = None
        for net in circuit.nets:
            if net.name == "GND":
                gnd_net = net
                break

        assert gnd_net is not None, "GND net not found in loaded circuit"

        # BUG: This currently fails - is_power=False, power_symbol=None
        # EXPECTED: Auto-detect GND as power net
        assert gnd_net.is_power is True, f"GND should auto-detect as power net, got is_power={gnd_net.is_power}"
        assert gnd_net.power_symbol == "power:GND", f"GND should have power_symbol='power:GND', got {gnd_net.power_symbol}"

    finally:
        Path(json_path).unlink()


def test_circuit_loader_autodetects_vcc_from_json():
    """VCC should auto-detect as power net when loaded from JSON."""
    circuit_json = {
        "name": "test_circuit",
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
            "VCC": {
                "nodes": [
                    {"component": "R1", "pin": {"number": "1", "name": "~", "type": "passive"}}
                ]
            }
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(circuit_json, f)
        json_path = f.name

    try:
        from circuit_synth.kicad.sch_gen.circuit_loader import load_circuit_hierarchy

        circuit, subcircuits = load_circuit_hierarchy(json_path)

        vcc_net = None
        for net in circuit.nets:
            if net.name == "VCC":
                vcc_net = net
                break

        assert vcc_net is not None
        assert vcc_net.is_power is True
        assert vcc_net.power_symbol == "power:VCC"

    finally:
        Path(json_path).unlink()


def test_circuit_loader_respects_explicit_is_power_false():
    """
    Explicit is_power=False should prevent auto-detection.

    This ensures backward compatibility - users can explicitly mark
    a net like "GND_SENSE" as NOT a power net.
    """
    circuit_json = {
        "name": "test_circuit",
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
                "is_power": False,  # Explicit override
                "power_symbol": None,
                "nodes": [
                    {"component": "R1", "pin": {"number": "2", "name": "~", "type": "passive"}}
                ]
            }
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(circuit_json, f)
        json_path = f.name

    try:
        from circuit_synth.kicad.sch_gen.circuit_loader import load_circuit_hierarchy

        circuit, subcircuits = load_circuit_hierarchy(json_path)

        gnd_net = None
        for net in circuit.nets:
            if net.name == "GND":
                gnd_net = net
                break

        assert gnd_net is not None
        # Explicit is_power=False should be respected, no auto-detection
        assert gnd_net.is_power is False
        assert gnd_net.power_symbol is None

    finally:
        Path(json_path).unlink()


def test_circuit_loader_old_format_autodetects():
    """
    Old JSON format (nets as list of connections) should also auto-detect.
    """
    circuit_json = {
        "name": "test_circuit",
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
            "GND": [  # Old format: just a list
                {"component": "R1", "pin": {"number": "2", "name": "~", "type": "passive"}}
            ]
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(circuit_json, f)
        json_path = f.name

    try:
        from circuit_synth.kicad.sch_gen.circuit_loader import load_circuit_hierarchy

        circuit, subcircuits = load_circuit_hierarchy(json_path)

        gnd_net = None
        for net in circuit.nets:
            if net.name == "GND":
                gnd_net = net
                break

        assert gnd_net is not None
        # Old format should also auto-detect
        assert gnd_net.is_power is True
        assert gnd_net.power_symbol == "power:GND"

    finally:
        Path(json_path).unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
