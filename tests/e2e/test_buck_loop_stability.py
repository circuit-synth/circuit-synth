"""Acceptance: averaged buck loop-stability analysis on live ngspice (Stage 20.5).

A 12 -> 3.3 V voltage-mode buck built with ``Sim.Params MODE=avg`` simulates as an
averaged (non-switching) model: a gm-C error amp + a continuous averaged PWM
switch. Under ``.ac`` with a voltage-injection source in the feedback path, the
loop gain is real and measurable -- crossover frequency and phase margin come out,
the question the cycle-accurate 20.3 model structurally cannot answer.

Structural (not exact-value) assertions, per the plan: a gain crossover exists and
is below FSW/5; the phase margin is a stable value in (5, 90) deg; slowing the
error amp (larger Cea) raises the phase margin monotonically. Exact-value
assertions on a behavioral macromodel are brittle (the Stage-12 "plan predicted the
wrong cutoff" lesson). Also cross-checks that the averaged model's DC output matches
the cycle-accurate model's steady-state average within 5%.

Skips cleanly when PySpice, a KiCad switching-regulator symbol, or ngspice is
unavailable.
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

FSW = 500e3


def _connect_by_name(comp, pin_name, net):
    for num, pin in getattr(comp, "_pins", {}).items():
        if (getattr(pin, "name", "") or "").strip().upper() == pin_name.upper():
            comp[num] += net
            return
    raise AssertionError(f"{comp.ref} has no pin named {pin_name}")


def _buck(mode_params, inject: bool):
    """A modeled buck IC + real L/Cout/divider/load. With ``inject`` an ac=1 source
    is spliced between the divider tap (FB_A) and the FB pin (FB_B) to break the
    loop for injection; without it the divider tap wires straight to the FB pin.

    Built as an isolated top-level circuit: the conftest ``mock_active_circuit``
    autouse fixture sets a shared active circuit, which would make each build a
    subcircuit of it and collide refs (U1) when a test builds two circuits. Setting
    the active circuit to None for the duration makes each build self-contained.
    """
    from circuit_synth.core.decorators import get_current_circuit, set_current_circuit

    _saved = get_current_circuit()
    set_current_circuit(None)

    @circuit(name="buck_loop")
    def _c():
        u1 = Component(
            symbol=SW_SYM, ref="U1",
            **{"Sim.Device": "BUCK", "Sim.Params": mode_params},
        )
        v1 = Component(symbol="Simulation_SPICE:VDC", ref="V1", value="12")
        l1 = Component(symbol="Device:L", ref="L1", value="22u")
        cout = Component(symbol="Device:C", ref="C1", value="47u")
        rtop = Component(symbol="Device:R", ref="RT", value="31.25k")
        rbot = Component(symbol="Device:R", ref="RB", value="10k")
        rload = Component(symbol="Device:R", ref="RL", value="5")
        vin, sw, out, gnd = Net("VIN"), Net("SW"), Net("OUT"), Net("GND")
        fb_pin = Net("FB_B")  # the controller FB pin side
        tap = Net("FB_A") if inject else fb_pin  # divider-tap side
        v1[1] += vin
        v1[2] += gnd
        _connect_by_name(u1, "VIN", vin)
        _connect_by_name(u1, "SW", sw)
        _connect_by_name(u1, "FB", fb_pin)
        _connect_by_name(u1, "GND", gnd)
        l1[1] += sw
        l1[2] += out
        cout[1] += out
        cout[2] += gnd
        rtop[1] += out
        rtop[2] += tap
        rbot[1] += tap
        rbot[2] += gnd
        rload[1] += out
        rload[2] += gnd
        if inject:
            vinj = Component(
                symbol="Simulation_SPICE:VSIN", ref="VJ", amplitude="0", offset="0"
            )
            vinj[1] += tap     # FB_A (loop output / divider side)
            vinj[2] += fb_pin  # FB_B (error-amp input / pin side)

    try:
        return _c()
    finally:
        set_current_circuit(_saved)


def _avg_params(cea, gm="4e-4"):
    return f"fsw=500k vout=3.3 vref=0.8 mode=avg gm={gm} cea={cea}"


def _loop(cea):
    sim = _buck(_avg_params(cea), inject=True).simulate()
    return sim.ac_analysis(start_freq=10, stop_freq=1e6, points=100)


def test_crossover_below_fsw_over_5():
    """A 0 dB gain crossover exists and sits below FSW/5 (a sane control bandwidth)."""
    res = _loop("1e-7")
    freq, mag_db, _ = res.loop_gain("FB_A", "FB_B")
    crossover = None
    for i in range(1, len(freq)):
        if mag_db[i - 1] >= 0 > mag_db[i]:
            crossover = freq[i]
            break
    assert crossover is not None, "no 0 dB crossover found"
    assert crossover < FSW / 5, f"crossover {crossover:.0f} Hz not below FSW/5"


def test_phase_margin_is_stable_value():
    """Phase margin is a real, stable value in (5, 90) deg."""
    pm = _loop("1e-7").phase_margin("FB_A", "FB_B")
    assert pm is not None, "no phase margin (loop never crosses 0 dB)"
    assert 5.0 < pm < 90.0, f"phase margin {pm:.1f} deg outside the stable band"


def test_phase_margin_increases_with_cea():
    """Slowing the error amp (larger Cea) lowers crossover and raises phase margin."""
    pm_fast = _loop("1e-7").phase_margin("FB_A", "FB_B")
    pm_slow = _loop("2e-7").phase_margin("FB_A", "FB_B")
    assert pm_fast is not None and pm_slow is not None
    assert pm_slow > pm_fast, f"PM did not increase with Cea: {pm_fast} -> {pm_slow}"


def test_averaged_dc_output_matches_cycle_model():
    """Averaged model's DC output is within 5% of the cycle-accurate model's steady state."""
    avg_out = float(
        np.real(
            np.asarray(
                _buck(_avg_params("1e-7"), inject=True).simulate().operating_point().analysis["OUT"]
            )
        ).flatten()[0]
    )
    cyc = _buck("fsw=500k vout=3.3", inject=False).simulate()
    cyc_out = cyc.transient_analysis(step_time=10e-9, end_time=1e-3).average("OUT")
    assert avg_out == pytest.approx(cyc_out, rel=0.05), f"avg={avg_out} cycle={cyc_out}"
