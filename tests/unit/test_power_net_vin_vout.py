"""Regression: bare VIN/VOUT/VBAT must not map to nonexistent power symbols.

KiCad's power.kicad_sym has no VIN/VOUT/VBAT symbol (only GND/VCC/+3V3/+5V/...),
but the power-net registry used to hardcode VIN->power:VIN etc. as builtin
defaults. Any Net("VIN") was then auto-classified as a power net and the schematic
writer tried to place a "power:VIN" symbol that does not exist, logging
"Unknown library ID: power:VIN" and placing no symbol. VIN/VOUT are signal/IO
nets, not rails.

This test locks in that:
  * VIN/VOUT/VBAT are NOT power nets,
  * real rails (GND/VCC/+3V3/+5V) still ARE,
  * generating a circuit with a Net("VIN") emits no power:VIN lib_id and instead
    labels VIN like any other signal net.
"""

import re
import tempfile
from pathlib import Path

import pytest

from circuit_synth import Component, Net, circuit
from circuit_synth.core.power_net_registry import get_power_symbol, is_power_net


@pytest.mark.parametrize("name", ["VIN", "VOUT", "VBAT"])
def test_vin_vout_vbat_are_not_power_nets(name):
    """Nets KiCad has no power symbol for must not be classified as power nets."""
    assert is_power_net(name) is False, f"{name} should not be a power net"
    assert get_power_symbol(name) is None, f"{name} should have no power symbol"


@pytest.mark.parametrize(
    "name,expected",
    [
        ("GND", "power:GND"),
        ("VCC", "power:VCC"),
        ("+3V3", "power:+3V3"),
        ("+5V", "power:+5V"),
    ],
)
def test_real_rails_still_detected(name, expected):
    """The fix must not break detection of rails that KiCad really provides."""
    assert is_power_net(name) is True, f"{name} should still be a power net"
    assert get_power_symbol(name) == expected


def _symbols_available() -> bool:
    try:
        Component(symbol="Device:R", ref="R1", value="1k")
        return True
    except Exception:
        return False


@pytest.mark.skipif(
    not _symbols_available(), reason="KiCad symbol libraries not available"
)
def test_net_vin_generates_as_signal_not_power_symbol():
    """A Net('VIN') generates as a labelled signal, with no power:VIN symbol."""

    @circuit(name="vin_signal")
    def vin_signal():
        r1 = Component(
            symbol="Device:R",
            ref="R1",
            value="1k",
            footprint="Resistor_SMD:R_0603_1608Metric",
        )
        r2 = Component(
            symbol="Device:R",
            ref="R2",
            value="2k",
            footprint="Resistor_SMD:R_0603_1608Metric",
        )
        vin = Net("VIN")
        gnd = Net("GND")
        vin += r1[1]
        r1[2] += r2[1]
        r2[2] += gnd

    with tempfile.TemporaryDirectory() as td:
        vin_signal().generate_kicad_project(
            str(Path(td) / "vin_signal"), generate_pcb=False, force_regenerate=True
        )
        content = next(Path(td).rglob("*.kicad_sch")).read_text(encoding="utf-8")

    # No attempt to place a nonexistent power:VIN symbol.
    assert "power:VIN" not in content, "VIN must not be emitted as a power symbol"
    # VIN is labelled like any other signal net (local label on a flat sheet).
    assert re.search(
        r'(?<!\(hierarchical_)\(label "VIN"', content
    ), "VIN should appear as a signal label"
    # GND is still a real power symbol (sanity that rails still work).
    assert "power:GND" in content
