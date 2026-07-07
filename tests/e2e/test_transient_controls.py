"""Acceptance: transient UIC / .ic controls on live ngspice (Stage 20.4).

An RC charging circuit (5 V source through 1k into 1uF to ground) is a clean probe
for initial conditions: with the cap forced to V(out)=2.0 and ``uic``, the first
transient sample sits at ~2 V and rises toward 5 V; with ``uic`` and no ``.ic`` the
cap starts discharged so the first sample is ~0 V. This distinguishes the new
controls from the default op-point start (which would begin at the DC solution).

Skips cleanly when PySpice or a loadable ngspice is unavailable.
"""

import numpy as np
import pytest

from circuit_synth import Component, Net, circuit


def _ngspice_available() -> bool:
    try:
        from circuit_synth.simulation.simulator import PYSPICE_AVAILABLE

        if not PYSPICE_AVAILABLE:
            return False
        from PySpice.Spice.NgSpice.Shared import NgSpiceShared

        NgSpiceShared.new_instance()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _ngspice_available(), reason="PySpice or ngspice unavailable"
)


def _rc():
    @circuit(name="rc_charge")
    def _c():
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

    return _c()


def _first_vout(res) -> float:
    v = np.real(np.asarray(res.analysis["OUT"])).astype(float)
    return float(v[0])


def test_initial_condition_sets_start_voltage():
    """uic + .ic v(out)=2.0 -> first sample ~2 V (not the 0 V discharged start)."""
    sim = _rc().simulate()
    res = sim.transient_analysis(
        step_time=1e-6,
        end_time=5e-3,
        use_initial_condition=True,
        initial_conditions={"OUT": 2.0},
    )
    assert _first_vout(res) == pytest.approx(2.0, abs=0.15)
    # And it charges toward the 5 V rail.
    assert res.average("OUT", tail_frac=0.1) > 4.0


def test_uic_without_ic_starts_discharged():
    """uic and no .ic -> capacitor starts at 0 V (not the DC op point ~5 V)."""
    sim = _rc().simulate()
    res = sim.transient_analysis(
        step_time=1e-6, end_time=5e-3, use_initial_condition=True
    )
    assert _first_vout(res) == pytest.approx(0.0, abs=0.15)
    # Still charges toward the rail by the end.
    assert res.average("OUT", tail_frac=0.1) > 4.0
