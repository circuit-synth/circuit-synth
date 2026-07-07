"""Headless PNG plot saving (Stage 10.1).

Each test runs a real ngspice analysis (via the bundled DLL) and asserts a valid
PNG lands on disk. The plotting module uses matplotlib's OO Agg API, so these
must pass headless under pytest with no interactive backend.

Skips cleanly (never fails) when PySpice or a loadable ngspice is unavailable.
"""

import numpy as np
import pytest

from circuit_synth import Component, Net, circuit

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _ngspice_available() -> bool:
    try:
        from circuit_synth.simulation.simulator import PYSPICE_AVAILABLE

        if not PYSPICE_AVAILABLE:
            return False
        Component(symbol="Simulation_SPICE:VSIN", ref="V1", value="1")
        from PySpice.Spice.NgSpice.Shared import NgSpiceShared

        NgSpiceShared.new_instance()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _ngspice_available(),
    reason="PySpice, KiCad sim symbols, or a loadable ngspice is not available",
)


def _assert_valid_png(path):
    assert path is not None, "plot function returned None (matplotlib missing?)"
    assert path.exists(), f"expected {path} to exist"
    data = path.read_bytes()
    assert len(data) > 1024, f"{path} is suspiciously small ({len(data)} bytes)"
    assert data.startswith(PNG_MAGIC), f"{path} is not a PNG"


# --- fixtures: minimal circuits exercising AC / transient / DC-sweep ---------


@circuit(name="RCLowPass")
def _rc_lowpass():
    """RC low-pass with an AC 1 V source; fc = 1/(2*pi*1k*159n) ~= 1 kHz."""
    v1 = Component(symbol="Simulation_SPICE:VSIN", ref="V1", value="1V")
    r1 = Component(symbol="Device:R", ref="R1", value="1k")
    c1 = Component(symbol="Device:C", ref="C1", value="159nF")
    vin, vout, gnd = Net("VIN"), Net("VOUT"), Net("GND")
    v1[1] += vin
    v1[2] += gnd
    r1[1] += vin
    r1[2] += vout
    c1[1] += vout
    c1[2] += gnd


@circuit(name="RCPulse")
def _rc_pulse():
    """RC driven by a pulse source, for a transient step response."""
    v1 = Component(
        symbol="Simulation_SPICE:VPULSE",
        ref="V1",
        value="0",
        initial_value="0",
        pulsed_value="5",
        delay_time="0",
        rise_time="1u",
        fall_time="1u",
        pulse_width="1m",
        period="2m",
    )
    r1 = Component(symbol="Device:R", ref="R1", value="1k")
    c1 = Component(symbol="Device:C", ref="C1", value="100nF")
    vin, vout, gnd = Net("VIN"), Net("VOUT"), Net("GND")
    v1[1] += vin
    v1[2] += gnd
    r1[1] += vin
    r1[2] += vout
    c1[1] += vout
    c1[2] += gnd


@circuit(name="Divider")
def _divider():
    """Resistor divider with a DC source to sweep."""
    v1 = Component(symbol="Simulation_SPICE:VDC", ref="V1", value="5")
    r1 = Component(symbol="Device:R", ref="R1", value="1k")
    r2 = Component(symbol="Device:R", ref="R2", value="1k")
    vin, vout, gnd = Net("VIN"), Net("VOUT"), Net("GND")
    v1[1] += vin
    v1[2] += gnd
    r1[1] += vin
    r1[2] += vout
    r2[1] += vout
    r2[2] += gnd


# --- tests -------------------------------------------------------------------


def test_save_bode_plot(tmp_path):
    result = _rc_lowpass().simulate().ac_analysis(10, 1e6, points=30)
    out = result.save_bode_plot(tmp_path / "bode.png", "VOUT")
    _assert_valid_png(out)


def test_save_transient_plot(tmp_path):
    result = _rc_pulse().simulate().transient_analysis(step_time=1e-6, end_time=2e-3)
    out = result.save_transient_plot(tmp_path / "transient.png", ["VOUT", "VIN"])
    _assert_valid_png(out)


def test_save_dc_transfer_plot(tmp_path):
    result = _divider().simulate().dc_analysis("VV1", 0.0, 5.0, 0.5)
    out = result.save_dc_transfer_plot(tmp_path / "dc.png", "VOUT", sweep_label="Vin")
    _assert_valid_png(out)


def test_transient_time_axis_recovered():
    """The transient plot should use the real time axis, not sample index."""
    result = _rc_pulse().simulate().transient_analysis(step_time=1e-6, end_time=2e-3)
    t = result.time_array()
    assert t[0] == pytest.approx(0.0, abs=1e-9)
    assert t[-1] == pytest.approx(2e-3, rel=0.05)
    assert len(t) == len(result.get_voltage("VOUT"))


def test_dc_sweep_axis_recovered():
    result = _divider().simulate().dc_analysis("VV1", 0.0, 5.0, 0.5)
    s = result.sweep_array()
    assert s[0] == pytest.approx(0.0, abs=1e-9)
    assert s[-1] == pytest.approx(5.0, rel=0.02)
