"""Op-amp pin mapping (Stage 7.2): map by pin function/name, not pin number.

An op-amp is modelled as an ideal VCVS (SPICE E source):
``Vout = Aol * (V(in+) - V(in-))``. The three signal terminals must be identified
by their KiCad pin function/name (output / input "+" / input "-"), NOT by pin
order -- an LM358 unit is out=1, in-=2, in+=3, so positional mapping would swap
the two inputs. PySpice renders the element as
``E<ref> <out+> <out-> <in+> <in-> <gain>``.

Mostly netlist-level (no ngspice); one closed-loop op-point test is skipped when
ngspice is unavailable.
"""

import pytest

from circuit_synth import Component, Net, circuit


def _symbols_available() -> bool:
    try:
        from circuit_synth.simulation.converter import PYSPICE_AVAILABLE

        if not PYSPICE_AVAILABLE:
            return False
        Component(symbol="Amplifier_Operational:LM358", ref="U1", value="LM358")
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _symbols_available(),
    reason="PySpice or the KiCad op-amp symbol library is not available",
)


def _netlist(c) -> str:
    from circuit_synth.simulation.converter import SpiceConverter

    return str(SpiceConverter(c).convert())


def _e_line(netlist: str, ref: str) -> list:
    for line in netlist.splitlines():
        if line.startswith(f"E{ref} "):
            return line.split()
    raise AssertionError(f"no VCVS E{ref} in netlist:\n{netlist}")


@circuit(name="noninv_amp")
def _noninv_amp():
    """Non-inverting amp so in+ (VIN) and in- (FB) are distinct nets.

    in- is the Rf/Rg divider tap from VOUT, so a positional mapping (which would
    put pin 2 = in- into the '+' slot) is distinguishable from the correct one.
    """
    v1 = Component(symbol="Simulation_SPICE:VDC", ref="V1", value="1")
    u1 = Component(symbol="Amplifier_Operational:LM358", ref="U1", value="LM358")
    rf = Component(
        symbol="Device:R",
        ref="RF",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )
    rg = Component(
        symbol="Device:R",
        ref="RG",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )
    vin = Net("VIN")
    vout = Net("VOUT")
    fb = Net("FB")
    gnd = Net("GND")
    v1[1] += vin
    v1[2] += gnd
    u1[3] += vin  # in+  (non-inverting)
    u1[2] += fb  # in-  (inverting)
    u1[1] += vout  # out
    rf[1] += vout
    rf[2] += fb
    rg[1] += fb
    rg[2] += gnd


def test_opamp_terminals_mapped_by_function():
    """out/in+/in- are resolved by pin function+name, not pin number."""
    parts = _e_line(_netlist(_noninv_amp()), "U1")
    # E<ref> <out+> <out-> <in+> <in-> <gain>
    assert parts[1] == "VOUT", f"output node wrong: {parts}"
    assert parts[2] == "0", f"output- should be ground: {parts}"
    assert parts[3] == "VIN", f"non-inverting (+) input wrong: {parts}"
    assert parts[4] == "FB", f"inverting (-) input wrong: {parts}"


def test_opamp_modeled_as_high_gain_vcvs():
    """The ideal model uses a high open-loop gain."""
    parts = _e_line(_netlist(_noninv_amp()), "U1")
    assert float(parts[5]) >= 1e5, f"op-amp gain should be high (ideal): {parts}"


def test_unused_unit_of_dual_opamp_ignored():
    """Only the connected unit of a dual op-amp is modelled (one VCVS)."""
    netlist = _netlist(_noninv_amp())
    e_lines = [ln for ln in netlist.splitlines() if ln.startswith("EU1 ")]
    assert len(e_lines) == 1, f"expected exactly one VCVS for U1:\n{netlist}"


def _ngspice_loads() -> bool:
    try:
        from circuit_synth.simulation.simulator import PYSPICE_AVAILABLE

        if not PYSPICE_AVAILABLE:
            return False
        from PySpice.Spice.NgSpice.Shared import NgSpiceShared

        NgSpiceShared.new_instance()
        return True
    except Exception:
        return False


# --- Dual-output symbols: deterministic OUT vs FB resolution (report F4) -----
#
# Some op-amp symbols expose two output-typed pins -- e.g. ADA4817-1ACP has pin 2
# FB (feedback, output-typed) and pin 7 OUT. The old code kept whichever iterated
# last, so with FB and OUT on different nets the ideal VCVS could drive the wrong
# node and silently open the loop. The fix prefers the non-FB pin and warns when
# output pins span more than one net.
import logging


def _ada4817_available() -> bool:
    try:
        Component(symbol="Amplifier_Operational:ADA4817-1ACP", ref="U1")
        return True
    except Exception:
        return False


ada4817 = pytest.mark.skipif(
    not _ada4817_available(),
    reason="KiCad Amplifier_Operational:ADA4817-1ACP symbol not available",
)


def _ada4817_amp(fb_net_name, out_net_name):
    """ADA4817 with in- = NINV, in+ = GND, FB (pin 2) and OUT (pin 7) as given.

    fb_net_name == out_net_name reproduces the E2E workaround (FB tied to VOUT);
    distinct names reproduce the ambiguous case F4 addresses.
    """

    @circuit(name="ada4817_amp")
    def _c():
        v1 = Component(symbol="Simulation_SPICE:VDC", ref="V1", value="1")
        u1 = Component(symbol="Amplifier_Operational:ADA4817-1ACP", ref="U1")
        rf = Component(symbol="Device:R", ref="RF", value="100k")
        rfb = Component(symbol="Device:R", ref="RFB", value="1k")  # keeps FB net live
        ninv = Net("NINV")
        gnd = Net("GND")
        vout = Net(out_net_name)
        fb = Net(fb_net_name)
        vpos = Net("VPOS")
        vneg = Net("VNEG")
        v1[1] += ninv
        v1[2] += gnd
        u1[3] += ninv  # in-
        u1[4] += gnd  # in+
        u1[2] += fb  # FB (output-typed)
        u1[7] += vout  # OUT (the real output)
        u1[8] += vpos
        u1[5] += vneg
        u1[1] += vpos
        u1[9] += vneg
        rf[1] += ninv  # feedback resistor closes NINV <-> OUT
        rf[2] += vout
        rfb[1] += fb  # a second pin on the FB net so it isn't a floating node
        rfb[2] += gnd

    return _c()


@ada4817
def test_dual_output_prefers_non_fb_pin(caplog):
    """FB and OUT on different nets -> the VCVS drives OUT (non-FB), and warns."""
    with caplog.at_level(logging.WARNING, logger="circuit_synth.simulation.converter"):
        parts = _e_line(_netlist(_ada4817_amp("VFB", "VOUT")), "U1")
    assert parts[1] == "VOUT", f"should drive the non-FB OUT pin: {parts}"
    warnings = [r.getMessage() for r in caplog.records if r.levelno >= logging.WARNING]
    assert any("U1" in m and "VFB" in m for m in warnings), warnings


@ada4817
def test_dual_output_same_net_no_warning(caplog):
    """FB tied to VOUT (E2E workaround wiring) -> same node, no ambiguity warning."""
    with caplog.at_level(logging.WARNING, logger="circuit_synth.simulation.converter"):
        parts = _e_line(_netlist(_ada4817_amp("VOUT", "VOUT")), "U1")
    assert parts[1] == "VOUT", parts
    warnings = [
        r.getMessage()
        for r in caplog.records
        if r.levelno >= logging.WARNING and "output pins on multiple nets" in r.getMessage()
    ]
    assert not warnings, warnings


def test_single_output_opamp_no_warning(caplog):
    """A plain single-output op-amp (LM358) resolves without any ambiguity warning."""
    with caplog.at_level(logging.WARNING, logger="circuit_synth.simulation.converter"):
        parts = _e_line(_netlist(_noninv_amp()), "U1")
    assert parts[1] == "VOUT", parts
    warnings = [
        r.getMessage()
        for r in caplog.records
        if "output pins on multiple nets" in r.getMessage()
    ]
    assert not warnings, warnings


# --- Opt-in 1-pole GBW macromodel (report F3, stage 12.4) --------------------
#
# By default an op-amp is an ideal frequency-independent VCVS. With a GBW (explicit
# Sim.Gbw, or a ModelLibrary OPAMP entry) it becomes a single-pole macromodel:
# gain-stage VCVS -> R-C pole -> unity buffer, so cap-limited bandwidth and peaking
# become simulatable. The internal nodes are named {ref}_p1 / {ref}_p2.


def _lm358_amp(gbw=None):
    """The non-inverting LM358 amp, optionally carrying a Sim.Gbw field."""

    @circuit(name="lm358_gbw_amp")
    def _c():
        v1 = Component(symbol="Simulation_SPICE:VDC", ref="V1", value="1")
        kw = {"symbol": "Amplifier_Operational:LM358", "ref": "U1", "value": "LM358"}
        if gbw is not None:
            kw["Sim.Gbw"] = gbw
        u1 = Component(**kw)
        rf = Component(symbol="Device:R", ref="RF", value="10k")
        rg = Component(symbol="Device:R", ref="RG", value="10k")
        vin = Net("VIN")
        vout = Net("VOUT")
        fb = Net("FB")
        gnd = Net("GND")
        v1[1] += vin
        v1[2] += gnd
        u1[3] += vin
        u1[2] += fb
        u1[1] += vout
        rf[1] += vout
        rf[2] += fb
        rg[1] += fb
        rg[2] += gnd

    return _c()


def test_opamp_without_gbw_stays_ideal_single_vcvs():
    """No Sim.Gbw -> exactly one VCVS, no macromodel internal nodes (byte-identical)."""
    netlist = _netlist(_lm358_amp())
    e_lines = [ln for ln in netlist.splitlines() if ln.startswith("EU1 ")]
    assert len(e_lines) == 1, f"ideal op-amp should be a single VCVS:\n{netlist}"
    assert "U1_p1" not in netlist and "U1_p2" not in netlist, netlist


def test_opamp_gbw_macromodel_emits_pole_and_buffer():
    """Sim.Gbw -> gain VCVS + R-C pole + buffer VCVS on internal nodes."""
    netlist = _netlist(_lm358_amp(gbw="1.4G"))
    assert "EU1_a U1_p1 0 VIN FB" in netlist, netlist  # gain stage
    assert "EU1_b VOUT 0 U1_p2 0" in netlist, netlist  # unity buffer to output
    assert any(
        ln.startswith("RU1_p ") and "U1_p1 U1_p2" in ln for ln in netlist.splitlines()
    ), netlist
    assert any(
        ln.startswith("CU1_p ") and "U1_p2 0" in ln for ln in netlist.splitlines()
    ), netlist
    # No plain ideal VCVS remains.
    assert not any(
        ln.startswith("EU1 ") for ln in netlist.splitlines()
    ), netlist


def test_opamp_gbw_pole_frequency_matches_gbw_over_aol0():
    """The R-C pole sits at GBW/Aol0: fp = 1/(2*pi*R*C) == 1.4G/1e6 = 1400 Hz."""
    import re as _re

    netlist = _netlist(_lm358_amp(gbw="1.4G"))
    r_val = c_val = None
    for ln in netlist.splitlines():
        if ln.startswith("RU1_p "):
            r_val = float(ln.split()[-1])
        elif ln.startswith("CU1_p "):
            c_val = float(_re.sub(r"[a-zA-Z]+$", "", ln.split()[-1]))
    assert r_val is not None and c_val is not None, netlist
    fp = 1.0 / (2 * 3.141592653589793 * r_val * c_val)
    assert fp == pytest.approx(1400.0, rel=0.02), fp


def test_opamp_unparsable_gbw_falls_back_to_ideal(caplog):
    """A garbage Sim.Gbw warns and falls back to the ideal single VCVS."""
    with caplog.at_level(logging.WARNING, logger="circuit_synth.simulation.converter"):
        netlist = _netlist(_lm358_amp(gbw="banana"))
    e_lines = [ln for ln in netlist.splitlines() if ln.startswith("EU1 ")]
    assert len(e_lines) == 1, netlist
    assert any("Sim.Gbw" in r.getMessage() for r in caplog.records), caplog.records


@pytest.mark.skipif(not _ngspice_loads(), reason="no loadable ngspice library")
def test_noninverting_closed_loop_gain():
    """End-to-end: the ideal op-amp gives the analytic closed-loop gain.

    Non-inverting amp with Rf=Rg=10k has gain 1 + Rf/Rg = 2, so VIN=1 V -> VOUT=2 V.
    Wrong input mapping (in+/in- swapped) makes the feedback positive and the
    op-point diverges, so this also guards the pin mapping through simulation.
    """
    result = _noninv_amp().simulate().operating_point()
    assert result.get_voltage("VIN") == pytest.approx(1.0, abs=0.01)
    assert result.get_voltage("VOUT") == pytest.approx(2.0, abs=0.02)
