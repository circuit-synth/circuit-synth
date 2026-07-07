"""Averaged buck model + loop-gain / phase-margin analysis (Stage 20.5).

``Sim.Params MODE=avg`` on a ``Sim.Device=BUCK`` part swaps the cycle-accurate
20.3 model (sawtooth + comparator + switch + diode) for an *averaged*
(non-switching) voltage-mode model: a gm-C error amplifier plus a continuous
averaged PWM switch. That model linearizes under ``.ac``, so a voltage-injection
loop-gain run yields crossover frequency and phase margin -- the question the
cycle model structurally cannot answer.

Netlist-shape + pure-numpy helper tests here (no ngspice); the live averaged
``.ac`` run is in ``tests/e2e/test_buck_loop_stability.py``.
"""

import numpy as np
import pytest

from circuit_synth import Component, Net, circuit
from circuit_synth.simulation.converter import SpiceConverter


def _symbols_available() -> bool:
    try:
        from circuit_synth.simulation.converter import PYSPICE_AVAILABLE

        if not PYSPICE_AVAILABLE:
            return False
        Component(symbol="Device:R", ref="R1", value="1k")
        return True
    except Exception:
        return False


def _switching_symbol():
    for sym in (
        "Regulator_Switching:TPS62130",
        "Regulator_Switching:LM2596S-3.3",
        "Regulator_Switching:MP1584",
    ):
        try:
            Component(symbol=sym, ref="U1")
            return sym
        except Exception:
            continue
    return None


SW_SYM = _switching_symbol()
needs_switching_symbol = pytest.mark.skipif(
    SW_SYM is None or not _symbols_available(),
    reason="no KiCad Regulator_Switching symbol available",
)


def _connect_by_name(comp, pin_name, net):
    for num, pin in getattr(comp, "_pins", {}).items():
        if (getattr(pin, "name", "") or "").strip().upper() == pin_name.upper():
            comp[num] += net
            return
    raise AssertionError(f"{comp.ref} has no pin named {pin_name}")


def _real_buck(sim_params="fsw=500k vout=3.3 vref=0.8 mode=avg"):
    @circuit(name="buck_avg")
    def _c():
        u1 = Component(symbol=SW_SYM, ref="U1", **{"Sim.Device": "BUCK",
                                                   "Sim.Params": sim_params})
        v1 = Component(symbol="Simulation_SPICE:VDC", ref="V1", value="12")
        L1 = Component(symbol="Device:L", ref="L1", value="22u")
        cout = Component(symbol="Device:C", ref="C1", value="47u")
        rtop = Component(symbol="Device:R", ref="RT", value="31.25k")
        rbot = Component(symbol="Device:R", ref="RB", value="10k")
        rload = Component(symbol="Device:R", ref="RL", value="5")
        vin, sw, out, fb, gnd = (
            Net("VIN"), Net("SW"), Net("OUT"), Net("FB"), Net("GND"),
        )
        v1[1] += vin
        v1[2] += gnd
        for name, net in (("VIN", vin), ("SW", sw), ("FB", fb), ("GND", gnd)):
            _connect_by_name(u1, name, net)
        L1[1] += sw
        L1[2] += out
        cout[1] += out
        cout[2] += gnd
        rtop[1] += out
        rtop[2] += fb
        rbot[1] += fb
        rbot[2] += gnd
        rload[1] += out
        rload[2] += gnd

    return _c()


def _netlist(c):
    return str(SpiceConverter(c).convert()).splitlines()


# --- netlist shape ----------------------------------------------------------


@needs_switching_symbol
def test_avg_emits_error_amp_and_averaged_switch():
    lines = _netlist(_real_buck())
    low = [ln.lower() for ln in lines]
    # gm-C error amp: current source of GM*(VREF - V(fb)), plus C and R on node c.
    assert any(ln.startswith("bu1_ea ") and "v(fb)" in ln for ln in low), lines
    assert any(ln.startswith("cu1_ea ") for ln in low), lines
    assert any(ln.startswith("ru1_ea ") for ln in low), lines
    # averaged (multiplicative) PWM switch: V(swi) = V(c) * V(vin); series RON to sw.
    # No duty-clamp node (a hard min/max saturation breaks .ac op-point convergence).
    assert any(ln.startswith("bu1_sw ") and "* v(" in ln for ln in low), lines
    assert any(ln.startswith("ru1_sw ") for ln in low), lines
    assert not any(ln.startswith("bu1_d ") for ln in low), lines


@needs_switching_symbol
def test_avg_has_no_switching_elements():
    """The averaged model replaces the sawtooth/comparator/switch/diode entirely."""
    low = [ln.lower() for ln in _netlist(_real_buck())]
    assert not any("u1_saw" in ln or "pulse" in ln for ln in low), low
    assert not any(ln.startswith(".model swu1") for ln in low), low
    assert not any(ln.startswith("su1_") for ln in low), low  # no S switch
    assert not any(ln.startswith("du1_") for ln in low), low  # no diode


@needs_switching_symbol
def test_avg_provenance_marks_averaged():
    conv = SpiceConverter(_real_buck())
    conv.convert()
    prov = conv.model_provenance.get("U1")
    assert prov is not None and prov.kind == "buck", prov
    assert "averaged" in prov.name.lower(), prov


@needs_switching_symbol
def test_mode_defaults_to_cycle():
    """No MODE (or MODE!=avg) -> the cycle-accurate 20.3 model (sawtooth, no EA)."""
    low = [ln.lower() for ln in _netlist(_real_buck(sim_params="fsw=500k vout=3.3"))]
    assert any("pulse" in ln for ln in low), low
    assert not any(ln.startswith("bu1_ea ") for ln in low), low


@needs_switching_symbol
def test_avg_missing_vref_skips_model(caplog):
    """MODE=avg without VREF: warn and emit nothing for the IC (no error amp)."""
    import logging

    with caplog.at_level(logging.WARNING):
        low = [ln.lower() for ln in _netlist(_real_buck(
            sim_params="fsw=500k vout=3.3 mode=avg"))]
    assert not any(ln.startswith("bu1_ea ") for ln in low), low
    assert any("vref" in r.message.lower() for r in caplog.records)


# --- pure-numpy margin helpers ---------------------------------------------


def test_phase_and_gain_margin_exact():
    """A hand-built loop gain: 0 dB crossing at PM=30 deg, -180 crossing at GM=12 dB."""
    from circuit_synth.simulation.simulator import SimulationResult

    freq = np.array([1.0, 10.0, 100.0, 1000.0])
    mag_db = np.array([20.0, 6.0, -12.0, -30.0])
    phase = np.array([-90.0, -135.0, -180.0, -225.0])
    T = 10 ** (mag_db / 20) * np.exp(1j * np.deg2rad(phase))
    # 0 dB crossing between (10 Hz, 6 dB, -135 deg) and (100 Hz, -12 dB, -180 deg):
    # interpolated phase -150 deg -> PM = 30 deg.
    assert SimulationResult._phase_margin_from(freq, T) == pytest.approx(30.0, abs=0.5)
    # -180 deg phase crossing lands on the 100 Hz sample where mag = -12 dB -> GM 12 dB.
    assert SimulationResult._gain_margin_from(freq, T) == pytest.approx(12.0, abs=0.5)


def test_integrator_has_90_deg_pm_and_no_gain_margin():
    """A pure integrator: |T|=1 at wc, phase -90 deg everywhere -> PM 90, GM None."""
    from circuit_synth.simulation.simulator import SimulationResult

    f = np.logspace(1, 5, 4001)  # 10 Hz .. 100 kHz
    w = 2 * np.pi * f
    wc = 2 * np.pi * 1000.0
    T = wc / (1j * w)
    assert SimulationResult._phase_margin_from(f, T) == pytest.approx(90.0, abs=1.0)
    # phase is a flat -90 deg -> never reaches -180 -> no gain margin.
    assert SimulationResult._gain_margin_from(f, T) is None


def test_no_zero_db_crossing_returns_none():
    """Loop gain below 0 dB everywhere -> no crossover -> phase_margin None."""
    from circuit_synth.simulation.simulator import SimulationResult

    f = np.array([1.0, 10.0, 100.0])
    T = 10 ** (np.array([-6.0, -12.0, -20.0]) / 20) * np.exp(1j * np.deg2rad([-80, -100, -120]))
    assert SimulationResult._phase_margin_from(f, T) is None
