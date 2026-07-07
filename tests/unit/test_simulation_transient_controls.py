"""Transient controls: UIC / .ic / start_time / max_time (Stage 20.4).

``CircuitSimulator.transient_analysis`` gained keyword-only controls that PSU
simulations need: ``use_initial_condition`` (skip the DC op point), ``initial_
conditions`` (``.ic`` node voltages), ``start_time`` (discard the settling head)
and ``max_time`` (cap the internal timestep). This exercises the plumbing with a
recording fake simulator -- no ngspice. The live behavior (a capacitor starting
at an .ic voltage) is in ``tests/e2e/test_transient_controls.py``.

Baseline protection: with none of the new controls requested, ``transient()`` is
called with *exactly* the legacy kwargs (``step_time`` / ``end_time``) and no
``initial_condition`` call -- so default transient runs are byte-identical.
"""

import pytest

from circuit_synth import Component, Net, circuit


def _pyspice_available() -> bool:
    try:
        from circuit_synth.simulation.simulator import PYSPICE_AVAILABLE

        return bool(PYSPICE_AVAILABLE)
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _pyspice_available(), reason="PySpice not available"
)


class _RecordingSimulator:
    """Stand-in for a PySpice simulator; records the transient/.ic calls."""

    def __init__(self):
        self.ic_calls = []
        self.transient_kwargs = None

    def initial_condition(self, **kwargs):
        self.ic_calls.append(kwargs)

    def transient(self, **kwargs):
        self.transient_kwargs = kwargs
        return object()  # opaque fake analysis; SimulationResult tolerates it


@circuit(name="rc")
def _rc():
    v1 = Component(symbol="Simulation_SPICE:VDC", ref="V1", value="5")
    r1 = Component(symbol="Device:R", ref="R1", value="1k")
    c1 = Component(symbol="Device:C", ref="C1", value="1u")
    vin, out, gnd = Net("VIN"), Net("OUT"), Net("GND")
    v1[1] += vin
    v1[2] += gnd
    r1[1] += vin
    r1[2] += out
    c1[1] += out
    c1[2] += gnd


def _sim_with_fake(monkeypatch):
    """Build a real CircuitSimulator but swap in a recording fake simulator."""
    sim = _rc().simulate()
    fake = _RecordingSimulator()
    monkeypatch.setattr(sim, "_make_simulator", lambda temperature, options: fake)
    return sim, fake


def test_defaults_are_legacy_call(monkeypatch):
    """No new controls -> transient() gets exactly step_time/end_time, no .ic."""
    sim, fake = _sim_with_fake(monkeypatch)
    sim.transient_analysis(step_time=1e-6, end_time=1e-3)

    assert set(fake.transient_kwargs) == {"step_time", "end_time"}
    assert fake.ic_calls == []
    assert float(fake.transient_kwargs["step_time"]) == pytest.approx(1e-6)
    assert float(fake.transient_kwargs["end_time"]) == pytest.approx(1e-3)


def test_use_initial_condition_only(monkeypatch):
    """UIC without .ic adds use_initial_condition=True, still no .ic call."""
    sim, fake = _sim_with_fake(monkeypatch)
    sim.transient_analysis(
        step_time=1e-6, end_time=1e-3, use_initial_condition=True
    )

    assert fake.transient_kwargs["use_initial_condition"] is True
    assert fake.ic_calls == []


def test_initial_conditions_call(monkeypatch):
    """initial_conditions -> initial_condition(**dict) with the net name passed through."""
    sim, fake = _sim_with_fake(monkeypatch)
    sim.transient_analysis(
        step_time=1e-6,
        end_time=1e-3,
        use_initial_condition=True,
        initial_conditions={"OUT": 0.0},
    )

    assert fake.ic_calls == [{"OUT": 0.0}]
    assert fake.transient_kwargs["use_initial_condition"] is True


def test_empty_initial_conditions_no_call(monkeypatch):
    """A falsy initial_conditions ({} / None) does not emit an .ic line."""
    sim, fake = _sim_with_fake(monkeypatch)
    sim.transient_analysis(step_time=1e-6, end_time=1e-3, initial_conditions={})
    assert fake.ic_calls == []


def test_start_and_max_time(monkeypatch):
    """start_time / max_time ride the transient() call as PySpice-unit values."""
    sim, fake = _sim_with_fake(monkeypatch)
    sim.transient_analysis(
        step_time=1e-6, end_time=1e-3, start_time=2e-4, max_time=5e-7
    )

    assert float(fake.transient_kwargs["start_time"]) == pytest.approx(2e-4)
    assert float(fake.transient_kwargs["max_time"]) == pytest.approx(5e-7)
    # UIC not requested -> absent.
    assert "use_initial_condition" not in fake.transient_kwargs


def test_zero_start_time_omitted(monkeypatch):
    """start_time=0 (the default) is omitted to keep the legacy call shape."""
    sim, fake = _sim_with_fake(monkeypatch)
    sim.transient_analysis(step_time=1e-6, end_time=1e-3, start_time=0)
    assert "start_time" not in fake.transient_kwargs
