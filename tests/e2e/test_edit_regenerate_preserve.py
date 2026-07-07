"""Stage 11.1 acceptance — conversational EDIT loop via source + regenerate.

This is the go/no-go for Stage 11's decision (Python-source-primary editing).
It exercises the *realistic* edit workflow the design-circuit skill uses: a
circuit-synth ``.py`` on disk is run as a subprocess (``python divider.py``),
manually re-placed in KiCad (simulated with kicad-sch-api), then the ``.py`` is
edited (value change + a new component) and re-run in **update mode**
(``force_regenerate=False``). We assert that:

* untouched components keep their UUIDs (stable identity across regeneration),
* a manually-moved component keeps its position,
* an edited value is applied,
* a newly-added component appears,
* the result still netlists via ``kicad-cli sch export netlist``,
* the ``.py`` source is not CRLF-corrupted by the source-ref rewriter
  (regression guard for the historical ``SourceRefRewriter`` newline bug).

Running from a real ``.py`` (not an inline circuit) is deliberate: only that
path triggers ``Circuit._update_source_refs`` / ``SourceRefRewriter``, which is
where the CRLF concern lives, and it mirrors what the skill actually does.
"""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import kicad_sch_api as ksa
import pytest
from kicad_sch_api.core.types import Point

KICAD_CLI = Path(r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe")

PROJECT = "edit_divider"

DIVIDER_V1 = '''\
from circuit_synth import Component, Net, circuit


@circuit(name="edit_divider")
def divider():
    r1 = Component(symbol="Device:R", ref="R1", value="1k",
                   footprint="Resistor_SMD:R_0603_1608Metric")
    r2 = Component(symbol="Device:R", ref="R2", value="2k",
                   footprint="Resistor_SMD:R_0603_1608Metric")
    vin = Net("VIN_5V")
    vout = Net("VOUT_3V3")
    gnd = Net("GND")
    r1[1] += vin
    r1[2] += vout
    r2[1] += vout
    r2[2] += gnd


if __name__ == "__main__":
    divider().generate_kicad_project(project_name="edit_divider",
                                     generate_pcb=False)
'''

# v2: R2 value 2k -> 4.7k, and a bypass cap C1 added across VOUT_3V3/GND.
DIVIDER_V2 = '''\
from circuit_synth import Component, Net, circuit


@circuit(name="edit_divider")
def divider():
    r1 = Component(symbol="Device:R", ref="R1", value="1k",
                   footprint="Resistor_SMD:R_0603_1608Metric")
    r2 = Component(symbol="Device:R", ref="R2", value="4.7k",
                   footprint="Resistor_SMD:R_0603_1608Metric")
    c1 = Component(symbol="Device:C", ref="C1", value="100n",
                   footprint="Capacitor_SMD:C_0603_1608Metric")
    vin = Net("VIN_5V")
    vout = Net("VOUT_3V3")
    gnd = Net("GND")
    r1[1] += vin
    r1[2] += vout
    r2[1] += vout
    r2[2] += gnd
    c1[1] += vout
    c1[2] += gnd


if __name__ == "__main__":
    divider().generate_kicad_project(project_name="edit_divider",
                                     generate_pcb=False)
'''


def _run_generate(workdir: Path, script: Path) -> None:
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    proc = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(workdir),
        env=env,
        capture_output=True,
        text=True,
        timeout=600,
    )
    if proc.returncode != 0:
        raise AssertionError(
            f"generation failed (rc={proc.returncode})\n"
            f"STDOUT:\n{proc.stdout[-3000:]}\n\nSTDERR:\n{proc.stderr[-3000:]}"
        )


def _components(sch):
    """Map reference -> component object for the loaded schematic."""
    return {c.reference: c for c in sch.components}


@pytest.mark.skipif(not KICAD_CLI.exists(), reason="kicad-cli not installed")
def test_edit_regenerate_preserves_and_updates(tmp_path):
    workdir = tmp_path
    script = workdir / "divider.py"
    script.write_text(DIVIDER_V1, encoding="utf-8", newline="\n")

    # --- Generate v1 -------------------------------------------------------
    _run_generate(workdir, script)
    sch_path = workdir / PROJECT / f"{PROJECT}.kicad_sch"
    assert sch_path.exists(), f"schematic not generated at {sch_path}"

    sch = ksa.Schematic.load(str(sch_path))
    comps = _components(sch)
    assert set(comps) >= {"R1", "R2"}, f"expected R1/R2, got {list(comps)}"
    r1_uuid, r2_uuid = comps["R1"].uuid, comps["R2"].uuid

    # --- Simulate a manual placement edit in KiCad -------------------------
    moved = Point(180.0, 120.0)
    comps["R1"].position = moved
    sch.save(str(sch_path), preserve_format=True)

    # --- Edit the .py: change R2 value + add C1, then regenerate (update) --
    script.write_text(DIVIDER_V2, encoding="utf-8", newline="\n")
    _run_generate(workdir, script)

    sch2 = ksa.Schematic.load(str(sch_path))
    comps2 = _components(sch2)

    # UUID stability for untouched components (identity survives regen).
    assert comps2["R1"].uuid == r1_uuid, "R1 UUID changed across regeneration"
    assert comps2["R2"].uuid == r2_uuid, "R2 UUID changed across regeneration"

    # Manual placement of R1 preserved.
    assert abs(comps2["R1"].position.x - moved.x) < 0.05, (
        f"R1 X not preserved: {comps2['R1'].position.x} != {moved.x}"
    )
    assert abs(comps2["R1"].position.y - moved.y) < 0.05, (
        f"R1 Y not preserved: {comps2['R1'].position.y} != {moved.y}"
    )

    # Value edit applied.
    assert comps2["R2"].value == "4.7k", f"R2 value not updated: {comps2['R2'].value}"

    # New component added.
    assert "C1" in comps2, f"C1 not added; components are {list(comps2)}"
    assert comps2["C1"].value == "100n"

    # --- Netlist still exports via kicad-cli -------------------------------
    netlist_out = workdir / "netlist.net"
    cli = subprocess.run(
        [str(KICAD_CLI), "sch", "export", "netlist",
         "--output", str(netlist_out), str(sch_path)],
        capture_output=True, text=True, timeout=300,
    )
    assert cli.returncode == 0, f"kicad-cli netlist failed:\n{cli.stderr}"
    assert netlist_out.exists()
    netlist = netlist_out.read_text(encoding="utf-8", errors="replace")
    for net in ("VIN_5V", "VOUT_3V3", "GND"):
        assert net in netlist, f"net {net} missing from exported netlist"

    # --- Source .py not corrupted by the ref rewriter ----------------------
    raw = script.read_bytes()
    assert b"\r\r" not in raw, "source .py has doubled CR (CRLF corruption)"
    # Still valid, runnable Python defining the circuit.
    text = raw.decode("utf-8")
    assert "def divider()" in text
    assert re.search(r'value="4\.7k"', text), "edited value missing from source"
