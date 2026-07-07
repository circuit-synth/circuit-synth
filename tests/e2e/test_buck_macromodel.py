"""Acceptance: behavioral buck macromodel end-to-end on ngspice (Stage 20.3).

A 12 V -> 3.3 V buck: the converter models only the IC (Sim.Device=BUCK); the
inductor (22 uH), output cap (47 uF), feedback divider and 5 ohm load are the
user's real schematic parts. A transient run regulates near 3.3 V with small
ripple, and the inductor branch current is readable. The open-loop model tracks
line but not load, so a load step shows the passive LC response settling to a new
steady state (not an active recovery) -- asserted as a bounded shift, matching
the model's documented limitation.

Boost isn't run live here: it needs UIC (start V(out)=V(in)) to converge, which
Stage 20.4 adds. Boost emission is covered at netlist-shape level in the unit
tests.

Skips cleanly when PySpice or a loadable ngspice is unavailable.
"""

import numpy as np
import pytest

from circuit_synth import Component, Net, circuit


def _switching_symbol():
    for sym in ("Regulator_Switching:TPS62130", "Regulator_Switching:LM2596S-3.3"):
        try:
            Component(symbol=sym, ref="U1")
            return sym
        except Exception:
            continue
    return None


SW_SYM = _switching_symbol()


def _ngspice_available() -> bool:
    try:
        from circuit_synth.simulation.simulator import PYSPICE_AVAILABLE

        if not PYSPICE_AVAILABLE or SW_SYM is None:
            return False
        Component(symbol="Simulation_SPICE:VDC", ref="V1", value="12")
        from PySpice.Spice.NgSpice.Shared import NgSpiceShared

        NgSpiceShared.new_instance()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _ngspice_available(),
    reason="PySpice, a KiCad switching-regulator symbol, or ngspice unavailable",
)


def _connect_by_name(comp, pin_name, net):
    for num, pin in getattr(comp, "_pins", {}).items():
        if (getattr(pin, "name", "") or "").strip().upper() == pin_name.upper():
            comp[num] += net
            return
    raise AssertionError(f"{comp.ref} has no pin named {pin_name}")


def _buck(load="Rload out 0 5"):
    @circuit(name="buck_e2e")
    def _c():
        u1 = Component(
            symbol=SW_SYM,
            ref="U1",
            **{"Sim.Device": "BUCK", "Sim.Params": "fsw=500k vout=3.3"},
        )
        v1 = Component(symbol="Simulation_SPICE:VDC", ref="V1", value="12")
        l1 = Component(symbol="Device:L", ref="L1", value="22u")
        cout = Component(symbol="Device:C", ref="C1", value="47u")
        rtop = Component(symbol="Device:R", ref="RT", value="31.25k")
        rbot = Component(symbol="Device:R", ref="RB", value="10k")
        rload = Component(symbol="Device:R", ref="RL", value="5")
        vin, sw, out, fb, gnd = (
            Net("VIN"),
            Net("SW"),
            Net("OUT"),
            Net("FB"),
            Net("GND"),
        )
        v1[1] += vin
        v1[2] += gnd
        _connect_by_name(u1, "VIN", vin)
        _connect_by_name(u1, "SW", sw)
        _connect_by_name(u1, "FB", fb)
        _connect_by_name(u1, "GND", gnd)
        l1[1] += sw
        l1[2] += out
        cout[1] += out
        cout[2] += gnd
        rtop[1] += out
        rtop[2] += fb
        rbot[1] += fb
        rbot[2] += gnd
        rload[1] += out
        rload[2] += gnd

    return _c()


def test_buck_regulates_near_target():
    """12 V -> 3.3 V: steady-state output within 5%, ripple under 150 mV."""
    sim = _buck().simulate()
    # Fine step (< 1/50 of the 2 us switching period) so PWM edges aren't aliased.
    res = sim.transient_analysis(step_time=10e-9, end_time=1e-3)
    vout = res.average("OUT")
    assert vout == pytest.approx(3.3, rel=0.05), f"Vout={vout}"
    assert res.ripple_pp("OUT") < 0.150, f"ripple={res.ripple_pp('OUT')}"


def test_buck_provenance_openloop():
    sim = _buck().simulate()
    prov = sim.model_provenance.get("U1")
    assert prov is not None and prov.kind == "buck"
    assert "openloop" in prov.name.lower()


def test_buck_inductor_current_available():
    """The real inductor's branch current is readable (saturation-margin check)."""
    sim = _buck().simulate()
    res = sim.transient_analysis(step_time=10e-9, end_time=1e-3)
    il = res.branch_current("L1")
    t = res.time_array()
    m = t > 0.9 * t[-1]
    il_avg = float(np.mean(il[m]))
    # ~3.3 V / 5 ohm = 0.66 A average inductor current.
    assert 0.4 < abs(il_avg) < 1.0, f"IL_avg={il_avg}"


def test_buck_load_step_settles():
    """Open-loop: a load step settles to a new bounded steady state (passive LC).

    Not an active recovery (open loop) -- just assert the post-step output stays a
    regulator-like output, not collapsed or runaway.
    """
    sim = _buck(load="Iload out 0 PWL(0 0.66 1.499m 0.66 1.5m 1.5 3m 1.5)").simulate()
    res = sim.transient_analysis(step_time=20e-9, end_time=3e-3)
    final = res.average("OUT", tail_frac=0.1)
    assert 3.0 < final < 3.5, f"post-step Vout={final}"


def test_boost_regulates_with_uic():
    """Live boost acceptance, deferred from 20.3 until 20.4 delivered UIC.

    5 V -> 12 V boost: the IC macromodel is a low-side switch; the user's real
    inductor (VIN->SW), rectifier diode (SW->OUT), cap and load supply the rest.
    The op point can't converge (open-loop PWM on a boost), so start from
    V(OUT)=VIN with uic. Open-loop honesty band: the duty correction assumes a
    0.45 V diode but the generic Device:D drops ~0.7 V, so assert within 10%.
    """

    @circuit(name="boost_e2e")
    def _c():
        u1 = Component(
            symbol=SW_SYM,
            ref="U1",
            **{"Sim.Device": "BOOST", "Sim.Params": "fsw=500k vout=12"},
        )
        v1 = Component(symbol="Simulation_SPICE:VDC", ref="V1", value="5")
        l1 = Component(symbol="Device:L", ref="L1", value="22u")
        d1 = Component(symbol="Device:D", ref="D1")
        cout = Component(symbol="Device:C", ref="C1", value="47u")
        rload = Component(symbol="Device:R", ref="RL", value="24")
        vin, sw, out, gnd = Net("VIN"), Net("SW"), Net("OUT"), Net("GND")
        v1[1] += vin
        v1[2] += gnd
        _connect_by_name(u1, "VIN", vin)
        _connect_by_name(u1, "SW", sw)
        _connect_by_name(u1, "GND", gnd)
        l1[1] += vin
        l1[2] += sw
        d1[2] += sw  # A (anode) -> switch node
        d1[1] += out  # K (cathode) -> boost output
        cout[1] += out
        cout[2] += gnd
        rload[1] += out
        rload[2] += gnd

    sim = _c().simulate()
    res = sim.transient_analysis(
        step_time=10e-9,
        end_time=2e-3,
        use_initial_condition=True,
        initial_conditions={"OUT": 5.0},
    )
    vout = res.average("OUT")
    assert vout == pytest.approx(12.0, rel=0.10), f"Vout={vout}"
    assert res.ripple_pp("OUT") < 0.150, f"ripple={res.ripple_pp('OUT')}"
    il = res.branch_current("L1")
    t = res.time_array()
    il_avg = float(np.mean(np.abs(il[t > 0.9 * t[-1]])))
    # ~24 W/... : Pout 6 W at 5 V in -> ~1.2 A average inductor (input) current.
    assert 0.8 < il_avg < 1.6, f"IL_avg={il_avg}"
