"""Acceptance: a two-sheet hierarchical design end-to-end (Stage 10.8).

Ties together the Stage-10 feedback-loop extensions on one artifact:
- **Hierarchy (Part C):** a PSU sheet + a common-emitter amp sheet, written as
  nested ``@circuit`` blocks sharing the ``VCC``/``GND`` nets by object identity;
  generation emits a root + two child ``.kicad_sch``, and the shared ``VCC``
  rail (a power net) crosses sheets via global power symbols -- verified by the
  KiCad netlist joining PSU and amp nodes on that net.
- **Flattened simulation (10.6):** ``simulate()`` flattens the hierarchy, so the
  operating point reads across sheets -- PSU delivers ~12 V and the amp bias
  lands at the proven Stage-9.5 numbers (IC ~= 1.35 mA, datasheet_fit 2N3904).
- **Plots (Part A):** ``save_transient_plot`` writes a valid PNG headlessly.

Design note: the amp keeps its proven Stage-9.5 **12 V** rail (not the 5 V the
plan sketched) so the datasheet-linked bias assertions remain valid; the PSU is
a genuine power block (source + bulk decoupling) feeding the shared rail. The
KiCad-native netlist cross-sheet check is gated on kicad-cli being installed.

Skips cleanly when PySpice or a loadable ngspice is unavailable.
"""

import shutil
from pathlib import Path

import numpy as np
import pytest

from circuit_synth import Component, Net, circuit

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _ngspice_available() -> bool:
    try:
        from circuit_synth.simulation.simulator import PYSPICE_AVAILABLE

        if not PYSPICE_AVAILABLE:
            return False
        Component(symbol="Simulation_SPICE:VDC", ref="V", value="12")
        Component(symbol="Transistor_BJT:BC547", ref="Q", value="2N3904")
        from PySpice.Spice.NgSpice.Shared import NgSpiceShared

        NgSpiceShared.new_instance()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _ngspice_available(),
    reason="PySpice, KiCad sim symbols, or a loadable ngspice is not available",
)


@circuit(name="psu")
def _psu(vcc, gnd):
    """12 V supply block with bulk decoupling; drives the shared VCC rail."""
    vsrc = Component(symbol="Simulation_SPICE:VDC", ref="V", value="12V")
    cbulk = Component(symbol="Device:C", ref="C", value="10uF")
    vsrc[1] += vcc
    vsrc[2] += gnd
    cbulk[1] += vcc
    cbulk[2] += gnd


@circuit(name="ce_amp")
def _ce_amp(vcc, gnd, sig_in):
    """Emitter-degenerated 2N3904 CE amp (Stage-9.5 design) on the shared rail."""
    vac = Component(
        symbol="Simulation_SPICE:VSIN", ref="V", value="0.01V", frequency="10k"
    )
    cin = Component(symbol="Device:C", ref="Cin", value="10uF")
    r1 = Component(symbol="Device:R", ref="R", value="47k")
    r2 = Component(symbol="Device:R", ref="R", value="10k")
    rc = Component(symbol="Device:R", ref="R", value="4.7k")
    re = Component(symbol="Device:R", ref="R", value="1k")
    q1 = Component(symbol="Transistor_BJT:BC547", ref="Q", value="2N3904")
    b, c, e = Net("B"), Net("C"), Net("E")
    vac[1] += sig_in
    vac[2] += gnd
    cin[1] += sig_in
    cin[2] += b
    r1[1] += vcc
    r1[2] += b
    r2[1] += b
    r2[2] += gnd
    rc[1] += vcc
    rc[2] += c
    re[1] += e
    re[2] += gnd
    # BC547 pinout: 1 = C, 2 = B, 3 = E.
    q1[1] += c
    q1[2] += b
    q1[3] += e


@circuit(name="amp_board")
def _amp_board():
    vcc, gnd, sig_in = Net("VCC"), Net("GND"), Net("SIG_IN")
    _psu(vcc, gnd)
    _ce_amp(vcc, gnd, sig_in)


def test_flattened_operating_point_across_sheets():
    """PSU rail ~12 V and amp bias (IC ~= 1.35 mA) via flattened simulation."""
    sim = _amp_board().simulate()
    res = sim.operating_point()
    vcc = float(np.array(res.analysis["VCC"])[0])
    vc = float(np.array(res.analysis["C"])[0])
    ic = (vcc - vc) / 4700.0
    assert vcc == pytest.approx(12.0, abs=0.05)  # PSU output crosses to the amp
    assert 1.0e-3 <= ic <= 1.8e-3, f"IC={ic*1e3:.3f} mA outside design band"
    assert 1.0 < vc < 11.0, f"collector {vc:.2f} V not in the active region"
    # Provenance survives flattening.
    assert sim.model_provenance["Q1"].tier == "datasheet_fit"
    assert sim.model_provenance["Q1"].name == "2N3904"


def test_transient_plot_saved(tmp_path):
    """save_transient_plot writes a valid PNG from the flattened hierarchy."""
    sim = _amp_board().simulate()
    res = sim.transient_analysis(step_time=2e-6, end_time=4e-4)
    out = res.save_transient_plot(tmp_path / "amp_tran.png", ["C", "VCC"])
    assert out is not None and out.exists()
    data = out.read_bytes()
    assert len(data) > 1024 and data.startswith(PNG_MAGIC)


def test_generation_emits_child_sheets_and_cross_sheet_net(tmp_path):
    """Root + 2 child .kicad_sch; the VCC rail joins both sheets in the netlist.

    VCC/GND are power nets, so they cross sheets via global power symbols (not
    sheet pins) -- that is correct hierarchical behavior. The authoritative
    cross-sheet proof is KiCad's own netlist: the VCC net must contain nodes
    from both the PSU block (its 12 V source / bulk cap) and the amp block (its
    bias/collector resistors).
    """
    import os

    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        result = _amp_board().generate_kicad_project(
            project_name="amp_board", generate_pcb=False
        )
    finally:
        os.chdir(cwd)
    assert result.get("success")

    proj = tmp_path / "amp_board"
    for name in ("amp_board.kicad_sch", "psu.kicad_sch", "ce_amp.kicad_sch"):
        assert (proj / name).exists(), f"missing {name}"

    # Power nets use global symbols, never sheet pins.
    root = (proj / "amp_board.kicad_sch").read_text(encoding="utf-8")
    assert '(pin "VCC"' not in root
    assert '(pin "GND"' not in root

    kicad_cli = shutil.which("kicad-cli") or _find_kicad_cli()
    if kicad_cli is None:
        pytest.skip("kicad-cli not found; netlist cross-sheet check skipped")

    import re
    import subprocess

    net = proj / "amp_board.net"
    r = subprocess.run(
        [
            kicad_cli,
            "sch",
            "export",
            "netlist",
            str(proj / "amp_board.kicad_sch"),
            "-o",
            str(net),
        ],
        capture_output=True,
        text=True,
    )
    # Exit 0 is authoritative; the "annotation errors" stderr warning is benign
    # for headless netlist export (see plans/stage-10.5-hierarchy-findings.md).
    assert r.returncode == 0, r.stderr

    text = net.read_text(encoding="utf-8")
    block = re.split(r"\n\t\t\(net\n", text[text.find("(nets") :])
    vcc_refs = set()
    for b in block[1:]:
        nm = re.search(r'\(name "([^"]+)"\)', b)
        if nm and nm.group(1).upper() == "VCC":
            vcc_refs = set(re.findall(r'\(ref "([^"]+)"\)', b))
    assert vcc_refs, "no VCC net in the exported netlist"
    # V1/C1 originate on the PSU sheet; the R* bias/collector on the amp sheet.
    assert any(x.startswith(("V", "C")) for x in vcc_refs), vcc_refs
    assert any(x.startswith("R") for x in vcc_refs), vcc_refs


def _find_kicad_cli():
    """Locate kicad-cli under a standard Windows KiCad install, else None."""
    import os

    base = Path(os.environ.get("PROGRAMFILES", r"C:\Program Files")) / "KiCad"
    if not base.is_dir():
        return None
    for ver in sorted(base.iterdir(), reverse=True):
        exe = ver / "bin" / "kicad-cli.exe"
        if exe.exists():
            return str(exe)
    return None
