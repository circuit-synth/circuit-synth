"""Acceptance: behavioral flyback macromodel end-to-end on ngspice (Stage 21.2).

A 12 V -> 5 V flyback: the converter models only the controller/switch IC
(``Sim.Device=FLYBACK``); the transformer (``Device:Transformer_1P_1S``,
lp=100u n=0.5 -- Stage 21.1 coupled inductors), output rectifier, 220 uF cap and
5 ohm load are the user's real schematic parts. Flyback polarity comes from
wiring (primary dot AA to VIN, secondary dot SA to the return); the secondary
return shares the sim's GND (SPICE DC-path requirement, documented).

The op point can't converge (open-loop PWM), so runs start from V(OUT)=0 with
uic (Stage 20.4 controls). Spiked 2026-07-05: k=1 lands 4.666 V (-6.7%, inside
the open-loop honesty band); k=0.999 leakage rings the ideal switch to kV
without the emitted drain clamp, and the clamp pins it at BV.

Skips cleanly when PySpice, the needed KiCad symbols, or ngspice is unavailable.
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
        Component(symbol="Device:Transformer_1P_1S", ref="T1")
        from PySpice.Spice.NgSpice.Shared import NgSpiceShared

        NgSpiceShared.new_instance()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _ngspice_available(),
    reason="PySpice, a KiCad switching/transformer symbol, or ngspice unavailable",
)


def _connect_by_name(comp, pin_name, net):
    for num, pin in getattr(comp, "_pins", {}).items():
        if (getattr(pin, "name", "") or "").strip().upper() == pin_name.upper():
            comp[num] += net
            return
    raise AssertionError(f"{comp.ref} has no pin named {pin_name}")


def _flyback(xfmr_params="lp=100u n=0.5 k=1"):
    @circuit(name="flyback_e2e")
    def _c():
        u1 = Component(
            symbol=SW_SYM,
            ref="U1",
            **{"Sim.Device": "FLYBACK", "Sim.Params": "fsw=100k vout=5 n=0.5"},
        )
        t1 = Component(
            symbol="Device:Transformer_1P_1S",
            ref="T1",
            **{"Sim.Params": xfmr_params},
        )
        v1 = Component(symbol="Simulation_SPICE:VDC", ref="V1", value="12")
        # A 5 V / 1 A flyback uses a Schottky rectifier in practice; the ~0.4 V
        # drop also matches the macromodel's first-order VF=0.45 correction (the
        # generic silicon diode drops ~0.9 V here and reads ~15% low).
        d1 = Component(symbol="Device:D", ref="D1", **{"Sim.Params": "IS=1e-6"})
        cout = Component(symbol="Device:C", ref="C1", value="220u")
        rload = Component(symbol="Device:R", ref="RL", value="5")
        vin, sw, sec, out, gnd = (
            Net("VIN"), Net("SW"), Net("SEC"), Net("OUT"), Net("GND"),
        )
        v1[1] += vin
        v1[2] += gnd
        _connect_by_name(u1, "VIN", vin)
        _connect_by_name(u1, "SW", sw)
        _connect_by_name(u1, "GND", gnd)
        _connect_by_name(t1, "AA", vin)  # primary dot to VIN
        _connect_by_name(t1, "AB", sw)   # other end to the IC's drain
        _connect_by_name(t1, "SA", gnd)  # secondary dot to the return (flyback flip)
        _connect_by_name(t1, "SB", sec)  # rectifier feed
        d1[2] += sec  # A (anode) -> rectifier feed
        d1[1] += out  # K (cathode) -> output
        cout[1] += out
        cout[2] += gnd
        rload[1] += out
        rload[2] += gnd

    return _c()


def _run(sim, end_time):
    # <= 1/50 of the 10 us switching period so PWM edges aren't aliased.
    return sim.transient_analysis(
        step_time=100e-9,
        end_time=end_time,
        use_initial_condition=True,
        initial_conditions={"OUT": 0.0},
    )


def test_flyback_regulates_near_target():
    """12 V -> 5 V with an ideal-coupling (k=1) transformer: within 10% (open loop)."""
    res = _run(_flyback().simulate(), 5e-3)
    vout = res.average("OUT")
    assert vout == pytest.approx(5.0, rel=0.10), f"Vout={vout}"
    assert res.ripple_pp("OUT") < 0.200, f"ripple={res.ripple_pp('OUT')}"


def test_flyback_primary_current_readable():
    """The 21.1 transformer's primary winding current is readable (magnetics margin)."""
    res = _run(_flyback().simulate(), 5e-3)
    ip = res.branch_current("T1_P")
    t = res.time_array()
    ip_pk = float(np.max(np.abs(ip[t > 0.9 * t[-1]])))
    # ~5 W out at 12 V in, D~0.48: peak primary current is A-scale, not mA or kA.
    assert 0.3 < ip_pk < 5.0, f"Ip_pk={ip_pk}"


def test_flyback_leakage_run_converges_and_clamp_holds():
    """Real coupling (default k=0.999): converges, and the drain clamp pins the
    leakage spike at ~BV (default 150 V) instead of the unclamped kV ring."""
    sim = _flyback(xfmr_params="lp=100u n=0.5").simulate()
    res = _run(sim, 1.5e-3)
    vsw = np.real(np.asarray(res.analysis["SW"])).astype(float)
    assert float(vsw.max()) < 170.0, f"SW peak {vsw.max():.0f} V (clamp not holding)"
    # Charging toward regulation, not collapsed or runaway.
    tail = res.average("OUT", tail_frac=0.1)
    assert 3.0 < tail < 6.0, f"Vout(tail)={tail}"


def test_flyback_provenance_openloop():
    sim = _flyback().simulate()
    prov = sim.model_provenance.get("U1")
    assert prov is not None and prov.kind == "flyback", prov
    assert "flyback_openloop" in prov.name.lower(), prov
    xf = sim.model_provenance.get("T1")
    assert xf is not None and xf.kind == "transformer", xf
