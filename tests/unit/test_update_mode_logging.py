"""Unit tests for the Stage 22.6 update-mode visibility logs (bug #10).

``generate_kicad_project`` defaults to update mode (``force_regenerate=False``).
In run 3 a plain re-run silently kept the OLD schematic after a structural edit,
and nothing at INFO level said "update mode ran and matched N components", so the
staleness was invisible until the file was diffed.

These tests generate the same divider circuit twice into the same output dir
(second run = update mode) and assert via caplog that:

* run 1 logs the fresh-build banner (and no update banner / no summary),
* run 2 logs the update-mode banner and the ``Update mode: matched N ...`` summary.

This is a logging/visibility fix only -- matching behavior and the default are
unchanged. Modeled on ``tests/unit/test_generation_result_logging.py``.
"""

import logging
import os
from tempfile import TemporaryDirectory

import pytest

from circuit_synth import Component, Net, circuit

pytestmark = pytest.mark.unit

R_FP = "Resistor_SMD:R_0603_1608Metric"

FRESH_BANNER = "(fresh build)"
UPDATE_BANNER = "in place (force_regenerate=False)"
SUMMARY_PREFIX = "Update mode: matched"


@circuit(name="UpdLogDiv")
def _divider():
    r1 = Component(symbol="Device:R", ref="R1", value="1k", footprint=R_FP)
    r2 = Component(symbol="Device:R", ref="R2", value="2k", footprint=R_FP)
    vin, vout, gnd = Net("VIN_5V"), Net("VOUT_3V3"), Net("GND")
    r1[1] += vin
    r1[2] += vout
    r2[1] += vout
    r2[2] += gnd


def _messages(caplog):
    return "\n".join(r.getMessage() for r in caplog.records)


def test_update_mode_banner_and_summary_logged(caplog):
    """Run 1 logs fresh banner; run 2 (same dir) logs update banner + summary."""
    # One circuit built once, generated twice (avoids the conftest
    # mock_active_circuit ref collision two @circuit builds would cause).
    div = _divider()

    with TemporaryDirectory() as tmpdir:
        cwd = os.getcwd()
        os.chdir(tmpdir)
        try:
            # --- Run 1: fresh build ---------------------------------------
            with caplog.at_level(logging.INFO, logger="circuit_synth"):
                caplog.clear()
                result1 = div.generate_kicad_project(
                    project_name="updlogdiv",
                    generate_pcb=False,
                    erc_gate=False,
                    selective_wires=False,
                )
                run1 = _messages(caplog)

            assert result1["success"]
            assert FRESH_BANNER in run1, run1
            assert UPDATE_BANNER not in run1, run1
            assert SUMMARY_PREFIX not in run1, run1

            # --- Run 2: update mode (project already exists) --------------
            with caplog.at_level(logging.INFO, logger="circuit_synth"):
                caplog.clear()
                result2 = div.generate_kicad_project(
                    project_name="updlogdiv",
                    generate_pcb=False,
                    erc_gate=False,
                    selective_wires=False,
                )
                run2 = _messages(caplog)
        finally:
            os.chdir(cwd)

    assert result2["success"]
    assert UPDATE_BANNER in run2, run2
    assert SUMMARY_PREFIX in run2, run2
    # The two divider resistors match on the update, none added/removed.
    assert "matched 2" in run2, run2
    assert FRESH_BANNER not in run2, run2
