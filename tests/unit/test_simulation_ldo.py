"""LDO / linear-regulator Tier-A behavioral macromodel (Stage 20.1).

A linear-regulator part simulates as a datasheet-parameterized behavioral
macromodel emitted by the converter -- no vendor model file needed:

    B<ref>_reg <reg> <gnd> V = min(<VOUT>, V(<in>,<gnd>)-<VDROP>)
    R<ref>_ser <reg> <out> <RSER>
    B<ref>_iq  <in> <gnd> I = <IQ>

Parameters come from ``Sim.Params`` (tier ``sim_params``) or a ModelLibrary
entry carrying a ``VOUT`` param (tier ``datasheet_fit``); a part with neither is
a validation error (a regulator's output cannot be guessed). Classification is by
``Regulator_Linear:`` symbol or an explicit ``Sim.Device=LDO``.

Mostly netlist-level (no ngspice); the classification/parsing tests need no KiCad
library at all.
"""

import logging

import pytest

from circuit_synth import Component, Net, circuit
from circuit_synth.simulation.converter import SpiceConverter, SimulationValidationError


# --- Pure helpers: no PySpice / KiCad library needed -------------------------


def test_classify_regulator_linear_is_ldo():
    assert SpiceConverter._classify("Regulator_Linear:AMS1117-3.3") == "ldo"


def test_classify_regulator_with_lm_prefix_not_opamp():
    """A regulator whose name contains 'lm' (LM1117) must not fall to the op-amp
    substring heuristic -- the Regulator_Linear check has to come first."""
    assert SpiceConverter._classify("Regulator_Linear:LM1117-3.3") == "ldo"


def test_sim_device_ldo_maps_to_ldo_kind():
    assert SpiceConverter._SIM_DEVICE_KINDS.get("LDO") == "ldo"


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("3.3", 3.3),
        ("0.3", 0.3),
        ("100m", 0.1),  # milli (a bare 'm' is milli for LDO params, not mega)
        ("2m", 0.002),
        ("1u", 1e-6),
        ("5", 5.0),
        ("banana", None),
        ("", None),
        (None, None),
    ],
)
def test_parse_si_number(raw, expected):
    assert SpiceConverter._parse_si_number(raw) == expected


# --- Netlist-shape tests: need the KiCad regulator symbol + PySpice -----------


def _symbols_available() -> bool:
    try:
        from circuit_synth.simulation.converter import PYSPICE_AVAILABLE

        if not PYSPICE_AVAILABLE:
            return False
        Component(symbol="Regulator_Linear:AMS1117-3.3", ref="U1")
        return True
    except Exception:
        return False


needs_symbol = pytest.mark.skipif(
    not _symbols_available(),
    reason="PySpice or the KiCad Regulator_Linear:AMS1117-3.3 symbol not available",
)


def _ldo_circuit(sim_params=None, value=None, sim_device="LDO"):
    """An LDO (AMS1117 pinout: 1=GND, 2=VO, 3=VI) fed by a VDC, with a load.

    Uses Sim.Device to force the kind so the test is independent of whether the
    symbol name classifies -- both routes must reach _add_ldo.
    """

    @circuit(name="ldo_test")
    def _c():
        kw = {"symbol": "Regulator_Linear:AMS1117-3.3", "ref": "U1"}
        if sim_device:
            kw["Sim.Device"] = sim_device
        if sim_params:
            kw["Sim.Params"] = sim_params
        if value:
            kw["value"] = value
        u1 = Component(**kw)
        v1 = Component(symbol="Simulation_SPICE:VDC", ref="V1", value="5")
        rload = Component(symbol="Device:R", ref="RL", value="33")
        vin = Net("VIN")
        vout = Net("VOUT")
        gnd = Net("GND")
        v1[1] += vin
        v1[2] += gnd
        u1[3] += vin  # VI
        u1[1] += gnd  # GND
        u1[2] += vout  # VO
        rload[1] += vout
        rload[2] += gnd

    return _c()


def _netlist(c) -> str:
    return str(SpiceConverter(c).convert())


@needs_symbol
def test_ldo_emits_behavioral_macromodel():
    netlist = _netlist(_ldo_circuit(sim_params="vout=3.3"))
    lines = netlist.splitlines()
    # Regulating B-source with a min() clamp on the input voltage.
    assert any(
        ln.startswith("BU1_reg ") and "min(" in ln and "V(VIN" in ln for ln in lines
    ), netlist
    # Series output resistance.
    assert any(ln.startswith("RU1_ser ") for ln in lines), netlist
    # Quiescent-current draw from the input.
    assert any(ln.startswith("BU1_iq ") and " I =" in ln for ln in lines), netlist


@needs_symbol
def test_ldo_provenance_tier_sim_params():
    conv = SpiceConverter(_ldo_circuit(sim_params="vout=3.3"))
    conv.convert()
    prov = conv.model_provenance.get("U1")
    assert prov is not None and prov.kind == "ldo" and prov.tier == "sim_params", prov
    assert "vout=3.3" in prov.name.lower()


@needs_symbol
def test_ldo_defaults_applied_when_only_vout_given():
    """Only vout set -> VDROP defaults to 0.3 and RSER to 0.05."""
    netlist = _netlist(_ldo_circuit(sim_params="vout=3.3"))
    reg = next(ln for ln in netlist.splitlines() if ln.startswith("BU1_reg "))
    assert "-0.3)" in reg.replace(" ", ""), reg  # VDROP default in the min() expr
    ser = next(ln for ln in netlist.splitlines() if ln.startswith("RU1_ser "))
    assert ser.split()[-1] == "0.05", ser  # RSER default


@needs_symbol
def test_ldo_params_override_defaults():
    netlist = _netlist(_ldo_circuit(sim_params="vout=3.3 vdrop=0.5 rser=0.1 iq=2m"))
    reg = next(ln for ln in netlist.splitlines() if ln.startswith("BU1_reg "))
    assert "-0.5)" in reg.replace(" ", ""), reg
    ser = next(ln for ln in netlist.splitlines() if ln.startswith("RU1_ser "))
    assert float(ser.split()[-1]) == pytest.approx(0.1), ser
    iq = next(ln for ln in netlist.splitlines() if ln.startswith("BU1_iq "))
    assert iq.strip().endswith("0.002"), iq


@needs_symbol
def test_ldo_missing_vout_is_validation_error():
    with pytest.raises(SimulationValidationError) as exc:
        _netlist(_ldo_circuit(sim_params="vdrop=0.3"))  # no vout
    msg = str(exc.value)
    assert "U1" in msg and "Sim.Params" in msg and "vout" in msg.lower(), msg


@needs_symbol
def test_ldo_datasheet_fit_from_model_library():
    """A ModelLibrary SUBCKT entry carrying VOUT resolves at tier datasheet_fit."""
    from circuit_synth.simulation.models import get_model_library
    from circuit_synth.simulation.models import SpiceModel

    lib = get_model_library()
    lib.add_model(
        SpiceModel(
            name="TESTLDO33",
            model_type="SUBCKT",
            parameters={"VOUT": 3.3, "VDROPOUT": 0.25, "IQ": 0.005},
        )
    )
    try:
        conv = SpiceConverter(_ldo_circuit(value="TESTLDO33", sim_device="LDO"))
        conv.convert()
        prov = conv.model_provenance.get("U1")
        assert prov is not None and prov.tier == "datasheet_fit", prov
        netlist = str(conv.spice_circuit)
        reg = next(ln for ln in netlist.splitlines() if ln.startswith("BU1_reg "))
        assert "-0.25)" in reg.replace(" ", ""), reg  # VDROPOUT mapped to VDROP
    finally:
        lib.models.pop("TESTLDO33", None)


@needs_symbol
def test_ldo_under_connected_is_validation_error():
    """An LDO with fewer than 3 connected pins is reported, not silently skipped."""

    @circuit(name="ldo_underconnected")
    def _c():
        u1 = Component(
            symbol="Regulator_Linear:AMS1117-3.3", ref="U1", **{"Sim.Device": "LDO", "Sim.Params": "vout=3.3"}
        )
        v1 = Component(symbol="Simulation_SPICE:VDC", ref="V1", value="5")
        vin = Net("VIN")
        gnd = Net("GND")
        v1[1] += vin
        v1[2] += gnd
        u1[3] += vin  # only VI connected
        u1[1] += gnd  # and GND -> 2 pins, no VO

    with pytest.raises(SimulationValidationError) as exc:
        _netlist(_c())
    assert "U1" in str(exc.value)
