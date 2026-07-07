"""Unit tests for the stage-14 post-pass success logs (Stage 17.1, G2).

``generate_kicad_project`` logs a one-line summary after the selective-wiring and
ERC-gate post-passes. Those two ``context_logger.info(...)`` calls used printf-style
positional args, which ``ContextLogger.info(self, message, **kwargs)`` does not
accept -- so a *successful* pass raised ``TypeError`` inside the enclosing
``try/except`` and got mislabelled as "skipped". These tests monkeypatch the two
post-passes to return canned results (so no kicad-cli is needed) and assert via
caplog that the success line emits and the "skipped" line does not.
"""

import logging
import os
from tempfile import TemporaryDirectory
from types import SimpleNamespace

import pytest

import circuit_synth.kicad.sch_gen.erc_gate as erc_gate_mod
import circuit_synth.kicad.sch_gen.selective_wiring as selective_wiring_mod
from circuit_synth import Component, Net, circuit

pytestmark = pytest.mark.unit

R_FP = "Resistor_SMD:R_0603_1608Metric"


@circuit(name="LogDiv")
def _divider():
    r1 = Component(symbol="Device:R", ref="R1", value="1k", footprint=R_FP)
    r2 = Component(symbol="Device:R", ref="R2", value="2k", footprint=R_FP)
    vin, vout, gnd = Net("VIN_5V"), Net("VOUT_3V3"), Net("GND")
    r1[1] += vin
    r1[2] += vout
    r2[1] += vout
    r2[2] += gnd


def test_selective_wiring_success_logs_drew_not_skipped(monkeypatch, caplog):
    """A successful selective-wiring pass logs 'drew', never 'skipped'."""
    monkeypatch.setattr(
        selective_wiring_mod,
        "wire_local_nets",
        lambda *a, **k: {
            "wires_drawn": 2,
            "eligible": 2,
            "reverted": False,
            "reason": "",
        },
    )

    with TemporaryDirectory() as tmpdir:
        cwd = os.getcwd()
        os.chdir(tmpdir)
        try:
            with caplog.at_level(logging.INFO, logger="circuit_synth"):
                result = _divider().generate_kicad_project(
                    project_name="logdiv",
                    generate_pcb=False,
                    selective_wires=True,
                )
        finally:
            os.chdir(cwd)

    assert result["success"]
    assert result["selective_wires"]["wires_drawn"] == 2
    messages = "\n".join(r.getMessage() for r in caplog.records)
    assert "Selective wiring skipped" not in messages, messages
    assert "Selective wiring drew 2 wire(s)" in messages, messages


def test_erc_gate_success_logs_summary_not_skipped(monkeypatch, caplog):
    """A successful ERC gate logs its summary, never 'skipped'."""
    monkeypatch.setattr(
        erc_gate_mod,
        "erc_gate",
        lambda *a, **k: SimpleNamespace(
            error_count=0, warning_count=1, autofixes_applied=3
        ),
    )

    with TemporaryDirectory() as tmpdir:
        cwd = os.getcwd()
        os.chdir(tmpdir)
        try:
            with caplog.at_level(logging.INFO, logger="circuit_synth"):
                result = _divider().generate_kicad_project(
                    project_name="logdiv_erc",
                    generate_pcb=False,
                    erc_gate=True,
                )
        finally:
            os.chdir(cwd)

    assert result["success"]
    messages = "\n".join(r.getMessage() for r in caplog.records)
    assert "ERC gate skipped" not in messages, messages
    assert "ERC gate: 0 error(s), 1 warning(s), 3 autofix(es)" in messages, messages
