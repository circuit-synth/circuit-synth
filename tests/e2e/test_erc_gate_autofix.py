"""E2E: the ERC gate clears power_pin_not_driven via PWR_FLAG (Stage 14, Part A).

Requires KiCad 10's kicad-cli (skips cleanly if absent). Generates the template
divider — whose GND power symbol has no driver, so KiCad ERC flags
``power_pin_not_driven`` — and asserts the gate auto-fixes it.
"""

import os
from pathlib import Path

import pytest

from circuit_synth import Component, Net, circuit
from circuit_synth.kicad.sch_gen.erc_gate import ErcUnavailable, erc_gate, run_erc

pytestmark = pytest.mark.e2e

R_FP = "Resistor_SMD:R_0603_1608Metric"


@circuit(name="ErcGateDiv")
def _divider():
    r1 = Component(symbol="Device:R", ref="R1", value="1k", footprint=R_FP)
    r2 = Component(symbol="Device:R", ref="R2", value="2k", footprint=R_FP)
    vin, vout, gnd = Net("VIN_5V"), Net("VOUT_3V3"), Net("GND")
    r1[1] += vin
    r1[2] += vout
    r2[1] += vout
    r2[2] += gnd


def _generate(tmp_path: Path) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        # Defaults flipped on (Stage-14): opt out so the gate runs only when the
        # test drives it, and "before" ERC still shows the unfixed violation.
        _divider().generate_kicad_project(
            project_name="ercgatediv",
            generate_pcb=False,
            erc_gate=False,
            selective_wires=False,
        )
    finally:
        os.chdir(cwd)
    return next(tmp_path.rglob("ErcGateDiv.kicad_sch"))


def _require_erc(sch: Path):
    try:
        return run_erc(str(sch))
    except ErcUnavailable:
        pytest.skip("kicad-cli (KiCad 10) not available")


def test_erc_gate_clears_power_pin_not_driven(tmp_path):
    sch = _generate(tmp_path / "proj")

    before = _require_erc(sch)
    assert any(
        v.type == "power_pin_not_driven" for v in before.violations
    ), "expected the bare divider's GND symbol to trip power_pin_not_driven"

    report = erc_gate(str(sch))
    assert report.autofixes_applied >= 1
    assert not any(v.type == "power_pin_not_driven" for v in report.violations)
    assert (
        report.error_count == 0
    )  # only the benign isolated_pin_label warning may remain


def test_generate_kicad_project_erc_gate_flag(tmp_path):
    tmp_path.mkdir(parents=True, exist_ok=True)
    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        result = _divider().generate_kicad_project(
            project_name="ercflag",
            generate_pcb=False,
            erc_gate=True,
            selective_wires=False,
        )
    finally:
        os.chdir(cwd)

    report = result.get("erc_report")
    if report is None:
        pytest.skip("kicad-cli (KiCad 10) not available — gate skipped")
    assert report.error_count == 0
    assert report.autofixes_applied >= 1


@circuit(name="TwoRail")
def _two_rail():
    # Two undriven power rails (VCC + GND) -> two power_pin_not_driven violations,
    # mirroring the canary's multi-rail op-amp. The gate must flag both with
    # *unique* #FLG references and run to completion (Stage 17.2, G3).
    r1 = Component(symbol="Device:R", ref="R1", value="10k", footprint=R_FP)
    r2 = Component(symbol="Device:R", ref="R2", value="10k", footprint=R_FP)
    vcc, gnd, sig = Net("VCC"), Net("GND"), Net("SIG")
    r1[1] += vcc
    r1[2] += sig
    r2[1] += sig
    r2[2] += gnd


def test_erc_gate_two_rails_unique_flags_runs_to_completion(tmp_path):
    tmp_path.mkdir(parents=True, exist_ok=True)
    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        _two_rail().generate_kicad_project(
            project_name="tworail",
            generate_pcb=False,
            erc_gate=False,
            selective_wires=False,
        )
    finally:
        os.chdir(cwd)
    sch = next(tmp_path.rglob("TwoRail.kicad_sch"))

    before = _require_erc(sch)
    assert (
        sum(1 for v in before.violations if v.type == "power_pin_not_driven") >= 2
    ), "expected two undriven rails"

    # Runs to completion without propagating an exception.
    report = erc_gate(str(sch))
    assert report.autofixes_applied >= 2

    # All #FLG references written are unique (the G3 collision would abort here).
    import re

    import kicad_sch_api as ksa

    reloaded = ksa.load_schematic(str(sch))
    flg_refs = [
        str(c.reference)
        for c in reloaded.components
        if re.match(r"#FLG\d+$", str(c.reference))
    ]
    assert len(flg_refs) == len(set(flg_refs)), f"duplicate #FLG refs: {flg_refs}"
    assert len(flg_refs) >= 2


# --------------------------------------------------------------------------- #
# Stage 18.3 acceptance: an op-amp whose *power rails* are the undriven pins.
# This is the case Stage 17 could not fix (value == part number, not the net, and
# pin "1" is a signal pin). The net-aware autofix must clear both rails.
# --------------------------------------------------------------------------- #

OPAMP_FP = "Package_CSP:Analog_LFCSP-8-1EP_3x3mm_P0.5mm_EP1.53x1.85mm"


@circuit(name="OpampRails")
def _opamp_rails():
    # Mirrors the canary's ADA4817 wiring (sipm_tia.py L93-108), minus the caps/SiPM.
    # Pins accessed by number, exactly as the canary does.
    u1 = Component(
        symbol="Amplifier_Operational:ADA4817-1ACP",
        ref="U1",
        value="ADA4817-1ACP",
        footprint=OPAMP_FP,
    )
    rf = Component(symbol="Device:R", ref="RF1", value="100k", footprint=R_FP)
    ninv, vout, gnd = Net("NINV"), Net("VOUT"), Net("GND")
    vpos, vneg = Net("V_POS_5V"), Net("V_NEG_5V")
    u1[4] += gnd      # + (non-inverting input)
    u1[3] += ninv     # - (inverting input)
    u1[7] += vout     # OUT
    u1[2] += vout     # FB -> VOUT (hardware-correct output tie)
    u1[8] += vpos     # +Vs
    u1[5] += vneg     # -Vs
    u1[1] += vpos     # ~PD tied high (like the canary; makes pin 1 rail-tied)
    u1[9] += vneg     # EP -> -Vs
    rf[1] += ninv
    rf[2] += vout


def test_erc_gate_clears_opamp_power_rails(tmp_path):
    tmp_path.mkdir(parents=True, exist_ok=True)
    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        _opamp_rails().generate_kicad_project(
            project_name="opamprails",
            generate_pcb=False,
            erc_gate=False,
            selective_wires=False,
        )
    finally:
        os.chdir(cwd)
    sch = next(tmp_path.rglob("OpampRails.kicad_sch"))

    before = _require_erc(sch)
    assert (
        sum(1 for v in before.violations if v.type == "power_pin_not_driven") >= 2
    ), "expected the op-amp's two undriven rails to trip power_pin_not_driven"

    report = erc_gate(str(sch))

    # The headline: NO power_pin_not_driven remains -- both rails cleared. Stage 17
    # could only ever clear the pin-1-accident rail, never V_NEG_5V.
    assert not any(
        v.type == "power_pin_not_driven" for v in report.violations
    ), report.summary()
    assert report.autofixes_applied >= 2

    # No flag-vs-flag / flag-vs-pin short introduced by the autofix.
    flag_shorts = [
        v
        for v in report.violations
        if v.type == "pin_to_pin"
        and any(str(r).startswith("#FLG") for r in v.references)
    ]
    assert not flag_shorts, f"autofix introduced a #FLG short: {report.summary()}"

    # #FLG refs + positions all unique.
    import re

    import kicad_sch_api as ksa

    reloaded = ksa.load_schematic(str(sch))
    flg = [
        (str(c.reference), (round(c.position.x, 2), round(c.position.y, 2)))
        for c in reloaded.components
        if re.match(r"#FLG\d+$", str(c.reference))
    ]
    refs = [r for r, _ in flg]
    pos = [p for _, p in flg]
    assert len(refs) == len(set(refs)), f"duplicate #FLG refs: {refs}"
    assert len(pos) == len(set(pos)), f"two flags stacked on a point: {pos}"
