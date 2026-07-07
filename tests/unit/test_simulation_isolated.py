"""Coupled inductors / transformer (K elements) + flyback macromodel (Stage 21).

21.1: a KiCad ``Device:Transformer_1P_1S`` symbol (or ``Sim.Device=TRANSFORMER``)
simulates as two coupled inductors + a ``K`` card. The transformer is a real
user part; only its SPICE model is emitted. Pin names AA/AB (primary) and SA/SB
(secondary); node order puts the SPICE dots at AA/SA, matching the symbol's
printed dots, so flyback polarity comes from user wiring.

21.2: ``Sim.Device=FLYBACK`` emits the Stage-20.3-style open-loop computed-duty
macromodel with a low-side switch and a drain avalanche clamp (leakage into an
ideal switch otherwise rings to kV -- spiked).

Netlist-shape + validation tests here (no ngspice); the live flyback run is in
``tests/e2e/test_flyback_macromodel.py``.
"""

import numpy as np
import pytest

from circuit_synth import Component, Net, circuit
from circuit_synth.simulation.converter import (
    SimulationValidationError,
    SpiceConverter,
)


# --- Pure classification -----------------------------------------------------


def test_classify_transformer_symbol():
    assert SpiceConverter._classify("Device:Transformer_1P_1S") == "transformer"


def test_sim_device_transformer_kinds():
    assert SpiceConverter._SIM_DEVICE_KINDS.get("TRANSFORMER") == "transformer"
    assert SpiceConverter._SIM_DEVICE_KINDS.get("XFMR") == "transformer"


def test_sim_device_flyback_kind():
    assert SpiceConverter._SIM_DEVICE_KINDS.get("FLYBACK") == "flyback"


# --- Fixtures ----------------------------------------------------------------


def _symbols_available() -> bool:
    try:
        from circuit_synth.simulation.converter import PYSPICE_AVAILABLE

        if not PYSPICE_AVAILABLE:
            return False
        Component(symbol="Device:Transformer_1P_1S", ref="T1")
        return True
    except Exception:
        return False


needs_symbols = pytest.mark.skipif(
    not _symbols_available(),
    reason="PySpice or the KiCad Transformer_1P_1S symbol not available",
)


def _connect_by_name(comp, pin_name, net):
    for num, pin in getattr(comp, "_pins", {}).items():
        if (getattr(pin, "name", "") or "").strip().upper() == pin_name.upper():
            comp[num] += net
            return
    raise AssertionError(f"{comp.ref} has no pin named {pin_name}")


def _xfmr_circuit(sim_params="lp=100u n=0.5", wire_all=True):
    """A transformer driven by a source on the primary, loaded on the secondary."""

    @circuit(name="xfmr_unit")
    def _c():
        t1 = Component(
            symbol="Device:Transformer_1P_1S",
            ref="T1",
            **({"Sim.Params": sim_params} if sim_params else {}),
        )
        v1 = Component(symbol="Simulation_SPICE:VSIN", ref="V1", amplitude="1")
        rl = Component(symbol="Device:R", ref="RL", value="50")
        vin, gnd, sec = Net("VIN"), Net("GND"), Net("SEC")
        v1[1] += vin
        v1[2] += gnd
        _connect_by_name(t1, "AA", vin)
        _connect_by_name(t1, "AB", gnd)
        _connect_by_name(t1, "SA", gnd)  # shared sim ground (isolation caveat)
        if wire_all:
            _connect_by_name(t1, "SB", sec)
            rl[1] += sec
        else:
            rl[1] += gnd
        rl[2] += gnd

    return _c()


def _netlist(c) -> list:
    return str(SpiceConverter(c).convert()).splitlines()


# --- 21.1 netlist shape -------------------------------------------------------


@needs_symbols
def test_transformer_emits_coupled_inductors():
    lines = _netlist(_xfmr_circuit())
    low = [ln.lower() for ln in lines]
    # Primary: dot (first node) at AA's net (vin); LP as given.
    lp = next((ln for ln in low if ln.startswith("lt1_p ")), None)
    assert lp is not None and lp.split()[1] == "vin", lines
    assert float(lp.split()[3]) == pytest.approx(100e-6)
    # Secondary: dot at SA's net (gnd -> spice node 0); LS = LP*N^2 = 25u.
    ls = next((ln for ln in low if ln.startswith("lt1_s ")), None)
    assert ls is not None and ls.split()[1] == "0", lines
    assert float(ls.split()[3]) == pytest.approx(25e-6)
    # K card couples the two windings at the default 0.999.
    k = next((ln for ln in low if ln.startswith("kt1 ")), None)
    assert k is not None and k.split()[1:3] == ["lt1_p", "lt1_s"], lines
    assert float(k.split()[3]) == pytest.approx(0.999)


@needs_symbols
def test_transformer_explicit_ls_wins_and_k_override():
    lines = _netlist(_xfmr_circuit(sim_params="lp=100u n=0.5 ls=30u k=1"))
    low = [ln.lower() for ln in lines]
    ls = next(ln for ln in low if ln.startswith("lt1_s "))
    assert float(ls.split()[3]) == pytest.approx(30e-6)  # explicit ls beats lp*n^2
    k = next(ln for ln in low if ln.startswith("kt1 "))
    assert float(k.split()[3]) == pytest.approx(1.0)


@needs_symbols
def test_transformer_provenance():
    conv = SpiceConverter(_xfmr_circuit())
    conv.convert()
    prov = conv.model_provenance.get("T1")
    assert prov is not None and prov.kind == "transformer", prov
    assert "xfmr" in prov.name.lower(), prov


# --- 21.1 validation ----------------------------------------------------------


@needs_symbols
def test_transformer_missing_params_is_validation_error():
    with pytest.raises(SimulationValidationError) as exc:
        _netlist(_xfmr_circuit(sim_params=None))
    msg = str(exc.value)
    assert "T1" in msg and "lp" in msg.lower()


@needs_symbols
def test_transformer_missing_ratio_is_validation_error():
    with pytest.raises(SimulationValidationError) as exc:
        _netlist(_xfmr_circuit(sim_params="lp=100u"))  # no n, no ls
    assert "T1" in str(exc.value)


@needs_symbols
def test_transformer_bad_k_is_validation_error():
    with pytest.raises(SimulationValidationError) as exc:
        _netlist(_xfmr_circuit(sim_params="lp=100u n=0.5 k=1.5"))
    msg = str(exc.value)
    assert "T1" in msg and "k" in msg.lower()


@needs_symbols
def test_transformer_unconnected_pin_is_validation_error():
    with pytest.raises(SimulationValidationError) as exc:
        _netlist(_xfmr_circuit(wire_all=False))
    msg = str(exc.value)
    assert "T1" in msg and ("pin" in msg.lower() or "connected" in msg.lower())


# --- 21.2 flyback macromodel --------------------------------------------------


def _switching_symbol():
    for sym in (
        "Regulator_Switching:TPS62130",
        "Regulator_Switching:LM2596S-3.3",
    ):
        try:
            Component(symbol=sym, ref="U1")
            return sym
        except Exception:
            continue
    return None


SW_SYM = _switching_symbol()
needs_flyback_symbols = pytest.mark.skipif(
    SW_SYM is None or not _symbols_available(),
    reason="no KiCad Regulator_Switching / Transformer symbol available",
)


def _flyback_circuit(sim_params="fsw=100k vout=5 n=0.5"):
    """The full flyback shape: IC macromodel + real transformer/rectifier/output."""

    @circuit(name="flyback_unit")
    def _c():
        u1 = Component(
            symbol=SW_SYM,
            ref="U1",
            **{"Sim.Device": "FLYBACK", "Sim.Params": sim_params},
        )
        t1 = Component(
            symbol="Device:Transformer_1P_1S",
            ref="T1",
            **{"Sim.Params": "lp=100u n=0.5"},
        )
        v1 = Component(symbol="Simulation_SPICE:VDC", ref="V1", value="12")
        d1 = Component(symbol="Device:D", ref="D1")
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
        # Primary dot (AA) to VIN, other end to the IC's SW (drain).
        _connect_by_name(t1, "AA", vin)
        _connect_by_name(t1, "AB", sw)
        # Flyback polarity by wiring: secondary dot (SA) to the return, SB
        # feeds the rectifier. Secondary return shares the sim's GND.
        _connect_by_name(t1, "SA", gnd)
        _connect_by_name(t1, "SB", sec)
        d1[2] += sec  # A (anode) -> rectifier feed
        d1[1] += out  # K (cathode) -> output
        cout[1] += out
        cout[2] += gnd
        rload[1] += out
        rload[2] += gnd

    return _c()


@needs_flyback_symbols
def test_flyback_emits_low_side_switch_and_clamp():
    lines = _netlist(_flyback_circuit())
    low = [ln.lower() for ln in lines]
    assert any("u1_saw" in ln and "pulse" in ln for ln in low), lines  # PWM ramp
    # Duty: (VOUT+VF)/((VOUT+VF) + N*V(vin)) -- the N*V(vin) product is the tell.
    duty = next((ln for ln in low if ln.startswith("bu1_d ")), None)
    assert duty is not None and "0.5*v(vin)" in duty.replace(" ", ""), lines
    assert any(ln.startswith("su1_ls ") for ln in low), lines  # low-side switch
    # Drain avalanche clamp with the default 150 V breakdown.
    assert any(ln.startswith("du1_cl ") for ln in low), lines
    clamp_model = next((ln for ln in low if ln.startswith(".model dclu1 ")), None)
    assert clamp_model is not None and "bv=150" in clamp_model.replace(" ", ""), lines
    # No freewheel diode (that is the buck's element; the rectifier is the user's).
    assert not any(ln.startswith("du1_fw ") for ln in low), lines


@needs_flyback_symbols
def test_flyback_vclamp_override():
    lines = _netlist(_flyback_circuit(sim_params="fsw=100k vout=5 n=0.5 vclamp=650"))
    low = [ln.lower() for ln in lines]
    clamp_model = next(ln for ln in low if ln.startswith(".model dclu1 "))
    assert "bv=650" in clamp_model.replace(" ", "")


@needs_flyback_symbols
def test_flyback_missing_n_is_validation_error():
    with pytest.raises(SimulationValidationError) as exc:
        _netlist(_flyback_circuit(sim_params="fsw=100k vout=5"))
    msg = str(exc.value)
    assert "U1" in msg and "turns" in msg.lower()


@needs_flyback_symbols
def test_flyback_provenance_openloop():
    conv = SpiceConverter(_flyback_circuit())
    conv.convert()
    prov = conv.model_provenance.get("U1")
    assert prov is not None and prov.kind == "flyback", prov
    assert "flyback_openloop" in prov.name.lower(), prov


@needs_flyback_symbols
def test_flyback_mode_avg_falls_back_to_cycle(caplog):
    """MODE=avg stays voltage-mode-buck-only: flyback warns + emits the cycle model."""
    import logging

    with caplog.at_level(logging.WARNING):
        lines = _netlist(
            _flyback_circuit(sim_params="fsw=100k vout=5 n=0.5 mode=avg")
        )
    low = [ln.lower() for ln in lines]
    assert any("pulse" in ln for ln in low), lines  # cycle model emitted
    assert not any(ln.startswith("bu1_ea ") for ln in low), lines  # no averaged EA
    assert any("mode=avg" in r.message.lower() or "buck-only" in r.message.lower()
               for r in caplog.records)
