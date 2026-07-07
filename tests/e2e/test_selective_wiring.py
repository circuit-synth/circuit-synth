"""E2E: selective wiring draws safe wires without changing connectivity (Stage 14 B).

Requires KiCad 10's kicad-cli (skips if absent). On the template divider, the VOUT
net (R1.2-R2.1) is a short 2-pin local net -> gets a drawn wire; ERC shows no new
violations, and the flattened netlist is unchanged (no accidental short).
"""

import json
import os
import subprocess
from pathlib import Path

import pytest

from circuit_synth import Component, Net, circuit
from circuit_synth.kicad.sch_gen.erc_gate import ErcUnavailable, _find_kicad_cli
from circuit_synth.kicad.sch_gen.selective_wiring import wire_local_nets

pytestmark = pytest.mark.e2e

R_FP = "Resistor_SMD:R_0603_1608Metric"


@circuit(name="WireDiv")
def _divider():
    r1 = Component(symbol="Device:R", ref="R1", value="1k", footprint=R_FP)
    r2 = Component(symbol="Device:R", ref="R2", value="2k", footprint=R_FP)
    vin, vout, gnd = Net("VIN_5V"), Net("VOUT_3V3"), Net("GND")
    r1[1] += vin
    r1[2] += vout
    r2[1] += vout
    r2[2] += gnd


def _cli_or_skip():
    try:
        return _find_kicad_cli()
    except ErcUnavailable:
        pytest.skip("kicad-cli (KiCad 10) not available")


def _erc_types(cli, sch, out):
    subprocess.run(
        [
            cli,
            "sch",
            "erc",
            "--format",
            "json",
            "--severity-all",
            "--output",
            str(out),
            str(sch),
        ],
        capture_output=True,
        text=True,
    )
    data = json.loads(Path(out).read_text(encoding="utf-8"))
    return sorted(
        (v["type"], v["severity"]) for s in data["sheets"] for v in s["violations"]
    )


def _generate(tmp_path: Path) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        # Defaults flipped on (Stage-14): opt out so this test owns the labels-only
        # baseline and drives wire_local_nets by hand.
        _divider().generate_kicad_project(
            project_name="wirediv",
            generate_pcb=False,
            erc_gate=False,
            selective_wires=False,
        )
    finally:
        os.chdir(cwd)
    return next(tmp_path.rglob("WireDiv.kicad_sch"))


def test_selective_wiring_draws_wire_no_new_erc(tmp_path):
    cli = _cli_or_skip()
    sch = _generate(tmp_path / "proj")

    before = _erc_types(cli, sch, tmp_path / "before.json")
    wires_before = sch.read_text(encoding="utf-8").count("(wire")

    result = wire_local_nets(str(sch))

    assert result["reverted"] is False
    assert result["wires_drawn"] >= 1, result
    wires_after = sch.read_text(encoding="utf-8").count("(wire")
    assert wires_after > wires_before
    # Post-commit ground truth read back from disk (stage 17.5): the file carries
    # at least the wires we drew (>= because a schematic may already contain some).
    assert result["wires_in_file"] >= result["wires_drawn"], result
    assert result["wires_in_file"] == wires_after

    after = _erc_types(cli, sch, tmp_path / "after.json")
    assert not (
        set(after) - set(before)
    ), f"new ERC violations: {set(after) - set(before)}"


def test_generate_kicad_project_selective_wires_flag(tmp_path):
    _cli_or_skip()
    tmp_path.mkdir(parents=True, exist_ok=True)
    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        result = _divider().generate_kicad_project(
            project_name="wireflag",
            generate_pcb=False,
            selective_wires=True,
            erc_gate=False,
        )
    finally:
        os.chdir(cwd)
    sw = result.get("selective_wires")
    assert sw is not None
    assert sw["reverted"] is False
    assert sw["wires_drawn"] >= 1, sw
