"""Behavioral switching-regulator (buck/boost) macromodel + measurement helpers
(Stage 20.3).

A switching-regulator IC simulates as a behavioral macromodel emitted by the
converter -- the converter replaces *only the IC*; the inductor, output cap, and
feedback divider stay the user's real schematic parts. v1 emits a computed-duty
*open-loop* model (duty = f(VOUT, VIN), with a first-order diode-drop
correction): rock-solid convergence and correct steady-state ripple / inductor
stress, but no active load-step recovery (that needs the Stage 20.5 averaged
model or a stable closed loop). Provenance is marked ``*_openloop`` so this is
never mistaken for a closed-loop result.

Netlist-shape + helper tests here (no ngspice); the live buck run is in
``tests/e2e/test_buck_macromodel.py``.
"""

import numpy as np
import pytest

from circuit_synth import Component, Net, circuit
from circuit_synth.simulation.converter import SpiceConverter, SimulationValidationError


# --- Pure classification -----------------------------------------------------


def test_sim_device_buck_boost_map_to_kinds():
    assert SpiceConverter._SIM_DEVICE_KINDS.get("BUCK") == "buck"
    assert SpiceConverter._SIM_DEVICE_KINDS.get("BOOST") == "boost"


def test_classify_regulator_switching_is_switcher_unknown():
    """Topology can't be read from the symbol name -> a pseudo-kind validate() flags."""
    assert (
        SpiceConverter._classify("Regulator_Switching:TPS62130")
        == "switcher_unknown"
    )


# --- Netlist-shape tests (need PySpice + KiCad symbols) -----------------------


def _symbols_available() -> bool:
    try:
        from circuit_synth.simulation.converter import PYSPICE_AVAILABLE

        if not PYSPICE_AVAILABLE:
            return False
        Component(symbol="Device:R", ref="R1", value="1k")
        return True
    except Exception:
        return False


needs_pyspice = pytest.mark.skipif(
    not _symbols_available(), reason="PySpice or KiCad symbols not available"
)


# The shape tests need a part whose pins carry SW/VIN/GND/FB names. Build one from
# a real KiCad switching-regulator symbol when present; otherwise skip.
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


def _netlist(c) -> str:
    return str(SpiceConverter(c).convert())


def _real_buck(sim_params="fsw=500k vout=3.3", device="BUCK"):
    """A modeled switcher IC + real L/Cout/divider/load, wired by pin name."""

    @circuit(name="buck_real")
    def _c():
        kw = {"symbol": SW_SYM, "ref": "U1"}
        if device:
            kw["Sim.Device"] = device
        if sim_params:
            kw["Sim.Params"] = sim_params
        u1 = Component(**kw)
        v1 = Component(symbol="Simulation_SPICE:VDC", ref="V1", value="12")
        L1 = Component(symbol="Device:L", ref="L1", value="22u")
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
        # Wire the IC by pin name (works regardless of pin numbering).
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


def _connect_by_name(comp, pin_name, net):
    """Connect the first pin whose KiCad name matches (case-insensitive) to net."""
    pins = getattr(comp, "_pins", {})
    for num, pin in pins.items():
        if (getattr(pin, "name", "") or "").strip().upper() == pin_name.upper():
            comp[num] += net
            return
    raise AssertionError(f"{comp.ref} has no pin named {pin_name}")


@needs_switching_symbol
def test_buck_emits_open_loop_macromodel():
    netlist = _netlist(_real_buck())
    lines = netlist.splitlines()
    assert any("U1_saw" in ln and "PULSE" in ln for ln in lines), netlist  # ramp
    assert any(ln.startswith("BU1_d ") and "min(" in ln for ln in lines), netlist
    assert any(
        ln.startswith("BU1_g ") and "u1_saw" in ln.lower() for ln in lines
    ), netlist  # comparator
    assert any(ln.startswith("SU1_hs ") for ln in lines), netlist  # high-side switch
    assert any(
        ln.lower().startswith(".model swu1 ") and "sw(" in ln.lower() for ln in lines
    ), netlist
    assert any(
        ln.startswith("DU1_fw ") for ln in lines
    ), netlist  # buck freewheel diode


@needs_switching_symbol
def test_buck_provenance_marks_openloop():
    conv = SpiceConverter(_real_buck())
    conv.convert()
    prov = conv.model_provenance.get("U1")
    assert prov is not None and prov.kind == "buck", prov
    assert "openloop" in prov.name.lower(), prov


@needs_switching_symbol
def test_boost_low_side_switch_and_no_freewheel_diode():
    netlist = _netlist(_real_buck(sim_params="fsw=500k vout=12", device="BOOST"))
    lines = netlist.splitlines()
    assert any(ln.startswith("SU1_ls ") for ln in lines), netlist  # low-side switch
    # Boost relies on the user's external rectifier diode -> the model emits none.
    assert not any(ln.startswith("DU1_") for ln in lines), netlist


@needs_switching_symbol
def test_switcher_unknown_is_validation_error():
    with pytest.raises(SimulationValidationError) as exc:
        _netlist(_real_buck(device=None))  # Regulator_Switching symbol, no Sim.Device
    assert "BUCK" in str(exc.value) and "BOOST" in str(exc.value)


@needs_switching_symbol
def test_buck_missing_params_is_validation_error():
    with pytest.raises(SimulationValidationError) as exc:
        _netlist(_real_buck(sim_params="fsw=500k"))  # no vout
    msg = str(exc.value)
    assert "U1" in msg and "vout" in msg.lower()


# --- Measurement helpers (pure numpy, synthetic analyses) --------------------


class _FakeAnalysis:
    """Minimal stand-in for a PySpice transient analysis object."""

    def __init__(self, time, nodes):
        self.time = np.asarray(time)
        self._nodes = {k: np.asarray(v) for k, v in nodes.items()}

    def __getitem__(self, key):
        return self._nodes[key]


def _result(time, nodes):
    from circuit_synth.simulation.simulator import SimulationResult

    return SimulationResult(_FakeAnalysis(time, nodes), "transient")


def test_average_over_tail():
    t = np.linspace(0, 1e-3, 1000)
    # ramp 0..2 for first 80%, flat 3.3 for last 20%
    v = np.where(t < 0.8e-3, t / 0.8e-3 * 2.0, 3.3)
    r = _result(t, {"out": v})
    assert r.average("out", tail_frac=0.2) == pytest.approx(3.3, abs=1e-6)


def test_ripple_pp_over_tail():
    t = np.linspace(0, 1e-3, 1000)
    # 5 kHz so the 1 us sampling resolves it (one full period in the 200 us tail).
    v = 3.3 + 0.05 * np.sin(2 * np.pi * 5e3 * t)  # +/-50 mV ripple
    r = _result(t, {"out": v})
    assert r.ripple_pp("out", tail_frac=0.2) == pytest.approx(0.1, abs=5e-3)


def test_settling_time_within_tolerance():
    t = np.linspace(0, 1e-3, 1000)
    # steps to 3.3 at t=0.5ms and stays
    v = np.where(t < 0.5e-3, 0.0, 3.3)
    r = _result(t, {"out": v})
    ts = r.settling_time("out", final=3.3, tol=0.02)
    assert ts == pytest.approx(0.5e-3, abs=2e-6)


def test_settling_time_none_if_never_settles():
    t = np.linspace(0, 1e-3, 1000)
    # cos so the last sample sits at a peak (outside the +/-2% band) -> never settles.
    v = 3.3 + 0.5 * np.cos(2 * np.pi * 2e3 * t)  # always +/-15%
    r = _result(t, {"out": v})
    assert r.settling_time("out", final=3.3, tol=0.02) is None
