"""Stage 22.9 generation sanity: the divider fixture generates warning-free.

The resistor divider uses real KiCad footprint ids, so a full in-process
generation must emit no footprint-not-found warning. This holds both with KiCad
installed (ids resolve) and without it (the check skips silently), so the
assertion is robust either way. Modeled on test_generation_result_logging.py.
"""

import logging
import os
from tempfile import TemporaryDirectory

import pytest

from circuit_synth import Component, Net, circuit

pytestmark = pytest.mark.unit

R_FP = "Resistor_SMD:R_0603_1608Metric"
NOT_FOUND = "not found in KiCad libraries"


@circuit(name="FpChkDiv")
def _divider():
    r1 = Component(symbol="Device:R", ref="R1", value="1k", footprint=R_FP)
    r2 = Component(symbol="Device:R", ref="R2", value="2k", footprint=R_FP)
    vin, vout, gnd = Net("VIN_5V"), Net("VOUT_3V3"), Net("GND")
    r1[1] += vin
    r1[2] += vout
    r2[1] += vout
    r2[2] += gnd


def test_divider_generates_without_footprint_warning(caplog):
    with TemporaryDirectory() as tmpdir:
        cwd = os.getcwd()
        os.chdir(tmpdir)
        try:
            with caplog.at_level(logging.WARNING, logger="circuit_synth"):
                result = _divider().generate_kicad_project(
                    project_name="fpchkdiv",
                    generate_pcb=False,
                    erc_gate=False,
                    selective_wires=False,
                )
        finally:
            os.chdir(cwd)

    assert result["success"]
    offending = [r.getMessage() for r in caplog.records if NOT_FOUND in r.getMessage()]
    assert not offending, offending
