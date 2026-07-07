"""AC response measurement helpers on ``SimulationResult``.

These test the pure-math accessors (``bode``/``cutoff_frequency``/
``passband_gain_db``) against a *synthetic* first-order low-pass response
``H(f) = 1/(1 + j f/fc)`` -- no ngspice, no PySpice circuit. A tiny stand-in
analysis object exposes just what the helpers read: a ``.frequency`` array and
``__getitem__`` returning the complex node response.
"""

import numpy as np
import pytest

from circuit_synth.simulation.simulator import SimulationResult

FC = 10_000.0  # 10 kHz corner


class _FakeAC:
    """Minimal stand-in for a PySpice AC analysis object."""

    def __init__(self, frequency, nodes):
        self.frequency = frequency
        self._nodes = nodes

    def __getitem__(self, key):
        return self._nodes[key]


def _first_order_lpf(fc: float = FC) -> SimulationResult:
    freq = np.logspace(2, 6, 400)  # 100 Hz .. 1 MHz, log-spaced
    H = 1.0 / (1.0 + 1j * freq / fc)
    return SimulationResult(_FakeAC(freq, {"VOUT": H}), "ac")


def test_cutoff_frequency_finds_corner():
    """The -3 dB point of a first-order LPF is its corner frequency fc."""
    result = _first_order_lpf(FC)
    fc = result.cutoff_frequency("VOUT")
    assert fc == pytest.approx(FC, rel=0.05)


def test_cutoff_frequency_scales_with_fc():
    """A different corner is recovered too (no hardcoded 10 kHz)."""
    result = _first_order_lpf(2_500.0)
    assert result.cutoff_frequency("VOUT") == pytest.approx(2_500.0, rel=0.05)


def test_passband_gain_db_is_unity():
    """Passband gain of the unity LPF is 0 dB."""
    result = _first_order_lpf(FC)
    assert result.passband_gain_db("VOUT") == pytest.approx(0.0, abs=0.1)


def test_bode_returns_aligned_arrays():
    """bode() returns frequency, magnitude(dB) and phase(deg) of equal length."""
    freq, mag_db, phase_deg = _first_order_lpf(FC).bode("VOUT")
    assert len(freq) == len(mag_db) == len(phase_deg)
    # DC-ish end is ~0 dB, ~0 deg; well above fc it is attenuated and phase -> -90.
    assert mag_db[0] == pytest.approx(0.0, abs=0.1)
    assert phase_deg[0] == pytest.approx(0.0, abs=1.0)
    assert phase_deg[-1] == pytest.approx(-90.0, abs=2.0)


def test_bode_rolloff_is_20db_per_decade():
    """Above the corner a first-order LPF rolls off at -20 dB/decade."""
    freq, mag_db, _ = _first_order_lpf(FC).bode("VOUT")

    def mag_at(f):
        return mag_db[int(np.argmin(np.abs(freq - f)))]

    # Two decades above fc: one decade of separation -> ~20 dB drop.
    drop = mag_at(1e5) - mag_at(1e6)
    assert drop == pytest.approx(20.0, abs=1.0)


def test_cutoff_frequency_none_when_no_crossing():
    """A flat (all-pass) response never crosses -3 dB -> None."""
    freq = np.logspace(2, 6, 50)
    flat = np.ones_like(freq, dtype=complex)
    result = SimulationResult(_FakeAC(freq, {"VOUT": flat}), "ac")
    assert result.cutoff_frequency("VOUT") is None
