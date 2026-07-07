"""E2E: BOM auto-includes sourcing columns and excludes SPICE stimuli (Stage 17.4 G5).

Requires KiCad 10's kicad-cli (skips cleanly if absent). Generates a canary-shaped
circuit -- a resistor carrying an MPN, a model-only capacitor flagged
``in_bom=False``, and a ``Simulation_SPICE:ISIN`` current stimulus -- then exports
the default BOM and asserts:
  * the MPN column is present and populated,
  * the ISIN stimulus (Simulation_SPICE:*) is dropped natively via (in_bom no),
  * the model-only cap (in_bom=False) is dropped too.
"""

import csv
import os
from pathlib import Path

import pytest

from circuit_synth import Component, Net, circuit
from circuit_synth.kicad.sch_gen.erc_gate import ErcUnavailable, _find_kicad_cli

pytestmark = pytest.mark.e2e

R_FP = "Resistor_SMD:R_0603_1608Metric"
C_FP = "Capacitor_SMD:C_0603_1608Metric"
R_MPN = "RC0603FR-07100KL"


@circuit(name="BomG5")
def _bom_circuit():
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="100k",
        footprint=R_FP,
        MPN=R_MPN,
        Manufacturer="Yageo",
    )
    # Model-only passive (e.g. a device's terminal capacitance): not a BOM part.
    c1 = Component(
        symbol="Device:C", ref="C1", value="1n", footprint=C_FP, in_bom=False
    )
    # Simulation stimulus -> excluded from BOM natively.
    i1 = Component(symbol="Simulation_SPICE:ISIN", ref="I1", value="ISIN")
    a, b = Net("A"), Net("B")
    r1[1] += a
    r1[2] += b
    c1[1] += a
    c1[2] += b
    i1[1] += a
    i1[2] += b


def _cli_or_skip():
    try:
        return _find_kicad_cli()
    except ErcUnavailable:
        pytest.skip("kicad-cli (KiCad 10) not available")


def test_bom_includes_mpn_excludes_spice_and_model_only(tmp_path):
    _cli_or_skip()
    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        result = _bom_circuit().generate_bom(project_name="bomg5")
    finally:
        os.chdir(cwd)

    assert result.get("success"), result

    # The generated schematic marks the SPICE stimulus and the model-only cap
    # (in_bom no) so kicad-cli drops them.
    sch = next(tmp_path.rglob("BomG5.kicad_sch"))
    sch_text = sch.read_text(encoding="utf-8")
    assert "(in_bom no)" in sch_text, "expected an (in_bom no) symbol"

    csv_path = next(tmp_path.rglob("bomg5.csv"))
    rows = list(csv.DictReader(csv_path.open(encoding="utf-8")))
    header = rows[0].keys() if rows else []

    # MPN column present and populated for R1.
    assert "MPN" in header, list(header)
    all_cells = "\n".join(",".join(str(v) for v in r.values()) for r in rows)
    assert R_MPN in all_cells, all_cells

    # Neither the ISIN stimulus (I1) nor the model-only cap (C1) appears.
    refs_col = "Refs" if "Refs" in header else "Reference"
    all_refs = ",".join(r.get(refs_col, "") for r in rows)
    assert "I1" not in all_refs, all_refs
    assert "C1" not in all_refs, all_refs
    # R1 (a real BOM part) is present.
    assert "R1" in all_refs, all_refs
