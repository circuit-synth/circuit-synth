"""Per-unit op-amp SPICE emission for multi-unit symbols (bug #A, Stage 23.3).

A dual/quad op-amp placed as ONE Component with both units wired used to collapse
into a single ideal VCVS, leaving the second section's output net undriven ->
``singular matrix`` -> hard sim failure. The fix emits one model per WIRED
amplifier unit: the first unit keeps the plain ``E<ref>`` element name (netlist
backward-compat), later units get ``E<ref>u<unit>``.

Mostly netlist-level; the op-point test is skipped when ngspice is unavailable.
"""

import logging

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


def _e_lines(netlist: str, prefix: str) -> list:
    return [ln for ln in netlist.splitlines() if ln.startswith(prefix)]


def _dual_two_inverting_stages(gbw=None):
    """LM358 with BOTH units wired as two cascaded inverting stages (gain -1 each).

    Stage A (unit 1: out=1 in-=2 in+=3): VIN -RinA-> NA -> out MID, RfA MID->NA.
    Stage B (unit 2: out=7 in-=6 in+=5): MID -RinB-> NB -> out OUT2, RfB OUT2->NB.
    VIN=1 -> MID=-1 -> OUT2=+1. Both output nets (MID, OUT2) must be driven.
    """

    @circuit(name="lm358_dual")
    def _c():
        v1 = Component(symbol="Simulation_SPICE:VDC", ref="V1", value="1")
        kw = {"symbol": "Amplifier_Operational:LM358", "ref": "U1", "value": "LM358"}
        if gbw is not None:
            kw["Sim.Gbw"] = gbw
        u1 = Component(**kw)
        rina = Component(symbol="Device:R", ref="RINA", value="10k")
        rfa = Component(symbol="Device:R", ref="RFA", value="10k")
        rinb = Component(symbol="Device:R", ref="RINB", value="10k")
        rfb = Component(symbol="Device:R", ref="RFB", value="10k")
        vin, mid, out2 = Net("VIN"), Net("MID"), Net("OUT2")
        na, nb, gnd = Net("NA"), Net("NB"), Net("GND")
        v1[1] += vin
        v1[2] += gnd
        # Stage A (unit 1)
        rina[1] += vin
        rina[2] += na
        rfa[1] += na
        rfa[2] += mid
        u1[2] += na  # in-
        u1[3] += gnd  # in+
        u1[1] += mid  # out
        # Stage B (unit 2)
        rinb[1] += mid
        rinb[2] += nb
        rfb[1] += nb
        rfb[2] += out2
        u1[6] += nb  # in-
        u1[5] += gnd  # in+
        u1[7] += out2  # out

    return _c()


def _single_stage_unit_a():
    """LM358 with ONLY unit 1 wired (a plain inverting amp). Unit 2 unwired."""

    @circuit(name="lm358_single")
    def _c():
        v1 = Component(symbol="Simulation_SPICE:VDC", ref="V1", value="1")
        u1 = Component(symbol="Amplifier_Operational:LM358", ref="U1", value="LM358")
        rin = Component(symbol="Device:R", ref="RIN", value="10k")
        rf = Component(symbol="Device:R", ref="RF", value="10k")
        vin, mid, na, gnd = Net("VIN"), Net("MID"), Net("NA"), Net("GND")
        v1[1] += vin
        v1[2] += gnd
        rin[1] += vin
        rin[2] += na
        rf[1] += na
        rf[2] += mid
        u1[2] += na
        u1[3] += gnd
        u1[1] += mid

    return _c()


def test_dual_both_units_emit_two_vcvs():
    """Both wired units -> two E-sources; each drives its own output net."""
    netlist = _netlist(_dual_two_inverting_stages())
    ea = _e_lines(netlist, "EU1 ")
    eb = _e_lines(netlist, "EU1u2 ")
    assert len(ea) == 1, f"expected first-unit VCVS EU1:\n{netlist}"
    assert len(eb) == 1, f"expected second-unit VCVS EU1u2:\n{netlist}"
    # E<ref> <out+> <out-> <in+> <in-> <gain>
    assert ea[0].split()[1] == "MID", ea
    assert eb[0].split()[1] == "OUT2", eb


def test_single_unit_used_is_backward_compatible():
    """Only unit A wired -> exactly one E-source named EU1 (no EU1u2), so existing
    single-unit-used netlists are unchanged."""
    netlist = _netlist(_single_stage_unit_a())
    assert len(_e_lines(netlist, "EU1 ")) == 1, netlist
    assert len(_e_lines(netlist, "EU1u2 ")) == 0, netlist


def test_dual_gbw_gives_each_unit_its_own_pole_network():
    """Sim.Gbw on a dual -> both units become 1-pole macromodels with distinct
    internal nodes (U1_p1/p2 and U1u2_p1/p2)."""
    netlist = _netlist(_dual_two_inverting_stages(gbw="1.4G"))
    assert "EU1_a U1_p1 0" in netlist, netlist
    assert "EU1u2_a U1u2_p1 0" in netlist, netlist
    assert any(ln.startswith("RU1_p ") for ln in netlist.splitlines()), netlist
    assert any(ln.startswith("RU1u2_p ") for ln in netlist.splitlines()), netlist
    # No plain ideal VCVS left for either unit.
    assert not _e_lines(netlist, "EU1 "), netlist
    assert not _e_lines(netlist, "EU1u2 "), netlist


def test_dual_provenance_single_entry_notes_units():
    """One provenance entry per ref, noting the wired unit count."""
    from circuit_synth.simulation.converter import SpiceConverter

    conv = SpiceConverter(_dual_two_inverting_stages())
    conv.convert()
    prov = conv.model_provenance["U1"]
    assert prov.kind == "opamp"
    assert "2 units" in prov.name, prov.name


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


@pytest.mark.skipif(not _ngspice_loads(), reason="no loadable ngspice library")
def test_dual_both_sections_converge_no_singular_matrix():
    """End-to-end: two -1 inverting stages -> VIN=1 -> MID=-1 -> OUT2=+1. Before
    the fix the second section was undriven (singular matrix)."""
    result = _dual_two_inverting_stages().simulate().operating_point()
    assert result.get_voltage("MID") == pytest.approx(-1.0, abs=0.02)
    assert result.get_voltage("OUT2") == pytest.approx(1.0, abs=0.02)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
