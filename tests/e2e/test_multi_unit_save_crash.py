"""E2E: multi-unit symbols must not crash KiCad's writer on save (bug #B).

Before the Stage-23.1 fix, a design placing a multi-unit symbol (LM358,
ADA4807-2ACP) generated a schematic whose extra units carried a dangling
``(path "/")``; ``kicad-cli sch upgrade --force`` segfaulted (rc=139) and
truncated the file to 0 bytes -- a headless proxy for the KiCad GUI save crash.

Requires KiCad 10's kicad-cli (skips cleanly if absent).
"""

import os
from pathlib import Path

import pytest

from circuit_synth import Component, Net, circuit

from .kicad_gate_utils import assert_kicad_save_ok

pytestmark = pytest.mark.e2e

R_FP = "Resistor_SMD:R_0603_1608Metric"


@circuit(name="MuLM358")
def _lm358_design():
    u1 = Component(symbol="Amplifier_Operational:LM358", ref="U1")
    r1 = Component(symbol="Device:R", ref="R1", value="1k", footprint=R_FP)
    n1, gnd, vcc = Net("N1"), Net("GND"), Net("VCC")
    u1[1] += n1
    u1[2] += n1
    u1[3] += gnd
    u1[4] += gnd
    u1[8] += vcc
    r1[1] += n1
    r1[2] += gnd


@circuit(name="MuADA4807")
def _ada4807_dual_design():
    # ADA4807-2ACP: dual op-amp, 10-pin. Wire unit A as a follower, unit B idle.
    u1 = Component(symbol="Amplifier_Operational:ADA4807-2ACP", ref="U1")
    r1 = Component(symbol="Device:R", ref="R1", value="1k", footprint=R_FP)
    n1, gnd, vpos = Net("N1"), Net("GND"), Net("VPOS")
    # OUTA=1 -INA=2 +INA=3 V-=4 ... V+ pin varies; wire the amp + power rails.
    u1[1] += n1
    u1[2] += n1
    u1[3] += gnd
    r1[1] += n1
    r1[2] += gnd


def _generate(circ, name: str, tmp_path: Path) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        circ.generate_kicad_project(
            project_name=name,
            generate_pcb=False,
            erc_gate=False,
            selective_wires=False,
        )
    finally:
        os.chdir(cwd)
    return next(tmp_path.rglob(f"{name}.kicad_sch"))


def test_lm358_multi_unit_saves_without_crash(tmp_path):
    sch = _generate(_lm358_design(), "MuLM358", tmp_path / "lm358")
    assert_kicad_save_ok(sch)


def test_ada4807_dual_saves_without_crash(tmp_path):
    sch = _generate(_ada4807_dual_design(), "MuADA4807", tmp_path / "ada4807")
    assert_kicad_save_ok(sch)
