"""End-to-end tests for the SKiDL render backend (Stage 13, Phase C).

Gated by ``requires_skidl``: needs a skidl-capable interpreter (Stage-13
``.venv-skidl`` or ``$CIRCUIT_SYNTH_SKIDL_PYTHON``) AND KiCad 10's ``kicad-cli``.
Both are skipped cleanly when absent, so the suite stays green on machines without
the SKiDL render environment.

What they prove:
  * ``render_with_skidl`` emits a ``.kicad_sch`` set that KiCad 10 parses.
  * the render contains routed ``(wire ...)`` segments (the whole point of the stage).
  * the render is electrically equivalent (pin-partition) to circuit_synth's own
    ``.kicad_sch`` for the same design.
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from circuit_synth import Component, Net, circuit
from circuit_synth.interop import render_with_skidl
from circuit_synth.interop.netlist_compare import compare_netlists

pytestmark = [pytest.mark.e2e, pytest.mark.requires_skidl]

R_FP = "Resistor_SMD:R_0603_1608Metric"
C_FP = "Capacitor_SMD:C_0603_1608Metric"


# --------------------------------------------------------------------------- #
# Environment discovery
# --------------------------------------------------------------------------- #


def _find_kicad_cli() -> str | None:
    env = os.environ.get("KICAD_CLI")
    if env and Path(env).exists():
        return env
    for cand in (
        r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe",
        shutil.which("kicad-cli"),
    ):
        if cand and Path(cand).exists():
            return cand
    return None


def _find_skidl_python() -> str | None:
    exe = os.environ.get("CIRCUIT_SYNTH_SKIDL_PYTHON")
    candidates = []
    if exe:
        candidates.append(exe)
    # circ-synth/.venv-skidl relative to this repo (circ-synth/circuit-synth/...)
    repo_root = Path(__file__).resolve().parents[2]  # .../circuit-synth
    parent = repo_root.parent  # .../circ-synth
    candidates.append(str(parent / ".venv-skidl" / "Scripts" / "python.exe"))
    candidates.append(str(parent / ".venv-skidl" / "bin" / "python"))
    for cand in candidates:
        if cand and Path(cand).exists():
            try:
                # Run the probe in a temp cwd: `import skidl` drops a
                # skidl_REPL.log in the working directory, which we don't want
                # littering the repo.
                proc = subprocess.run(
                    [cand, "-c", "import skidl"],
                    capture_output=True,
                    text=True,
                    timeout=120,
                    cwd=tempfile.gettempdir(),
                )
            except Exception:
                continue
            if proc.returncode == 0:
                return cand
    return None


@pytest.fixture(scope="module")
def kicad_cli() -> str:
    cli = _find_kicad_cli()
    if not cli:
        pytest.skip("kicad-cli (KiCad 10) not found")
    return cli


@pytest.fixture(scope="module")
def skidl_python() -> str:
    exe = _find_skidl_python()
    if not exe:
        pytest.skip(
            "no skidl-capable interpreter (set CIRCUIT_SYNTH_SKIDL_PYTHON or create "
            ".venv-skidl per Stage-13 Phase 0)"
        )
    return exe


def _netlist(kicad_cli: str, sch: Path, out: Path) -> Path:
    proc = subprocess.run(
        [kicad_cli, "sch", "export", "netlist", str(sch), "--output", str(out)],
        capture_output=True,
        text=True,
    )
    assert out.exists(), f"kicad-cli netlist failed: {proc.stdout}\n{proc.stderr}"
    return out


def _wire_count(sch_dir: Path) -> int:
    total = 0
    for f in sch_dir.glob("*.kicad_sch"):
        total += f.read_text(encoding="utf-8", errors="replace").count("(wire")
    return total


# --------------------------------------------------------------------------- #
# Circuits
# --------------------------------------------------------------------------- #


@circuit(name="SkidlDivider")
def _divider():
    r1 = Component(symbol="Device:R", ref="R1", value="1k", footprint=R_FP)
    r2 = Component(symbol="Device:R", ref="R2", value="2k", footprint=R_FP)
    vin, vout, gnd = Net("VIN_5V"), Net("VOUT_3V3"), Net("GND")
    r1[1] += vin
    r1[2] += vout
    r2[1] += vout
    r2[2] += gnd


@circuit(name="filt")
def _filt(vin, v5, gnd):
    r = Component(symbol="Device:R", ref="R1", value="100", footprint=R_FP)
    cin = Component(symbol="Device:C", ref="C1", value="100nF", footprint=C_FP)
    cout = Component(symbol="Device:C", ref="C2", value="10uF", footprint=C_FP)
    r[1] += vin
    r[2] += v5
    cin[1] += vin
    cin[2] += gnd
    cout[1] += v5
    cout[2] += gnd


@circuit(name="load")
def _load(v5, gnd):
    r1 = Component(symbol="Device:R", ref="R2", value="10k", footprint=R_FP)
    r2 = Component(symbol="Device:R", ref="R3", value="10k", footprint=R_FP)
    r1[1] += v5
    r1[2] += gnd
    r2[1] += v5
    r2[2] += gnd


@circuit(name="SkidlHier")
def _hier():
    vin, v5, gnd = Net("VIN"), Net("V5"), Net("GND")
    _filt(vin, v5, gnd)
    _load(v5, gnd)


# --------------------------------------------------------------------------- #
# Tests
# --------------------------------------------------------------------------- #


def _generate_cs(circ, tmp_path: Path, project: str) -> Path:
    """Generate a circuit_synth project and return its ROOT ``.kicad_sch``.

    For a hierarchical design there are several sheets; the root is the one whose
    stem matches the ``.kicad_pro`` (kicad-cli traverses the full hierarchy only
    when given the root).
    """
    tmp_path.mkdir(parents=True, exist_ok=True)
    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        circ.generate_kicad_project(project_name=project, generate_pcb=False)
    finally:
        os.chdir(cwd)
    pro = next(tmp_path.rglob("*.kicad_pro"))
    root = pro.with_suffix(".kicad_sch")
    return root if root.exists() else next(tmp_path.rglob("*.kicad_sch"))


def test_render_divider_equivalent(tmp_path, kicad_cli, skidl_python):
    c = _divider()

    cs_sch = _generate_cs(c, tmp_path / "cs", "divider")
    render_dir = tmp_path / "skidl"
    top = render_with_skidl(c, render_dir, python_exe=skidl_python)

    # KiCad 10 parses the render (netlist export succeeds).
    cs_net = _netlist(kicad_cli, cs_sch, tmp_path / "cs.net")
    sk_net = _netlist(kicad_cli, top, tmp_path / "sk.net")

    # Routed wires exist.
    assert _wire_count(render_dir) > 0, "SKiDL render produced no (wire ...) segments"

    # Electrically equivalent.
    result = compare_netlists(cs_net, sk_net)
    assert result.equivalent, "\n".join(result.messages)


def test_render_hierarchical_has_wires_and_equivalent(
    tmp_path, kicad_cli, skidl_python
):
    c = _hier()

    cs_sch = _generate_cs(c, tmp_path / "cs", "hier")
    render_dir = tmp_path / "skidl"
    render_with_skidl(c, render_dir, python_exe=skidl_python)

    # Compare against the flattened netlists (kicad-cli flattens hierarchy).
    cs_net = _netlist(kicad_cli, cs_sch, tmp_path / "cs.net")
    # The SKiDL top sheet references child sheets; netlist the top.
    sk_top = render_dir / "SkidlHier.kicad_sch"
    sk_net = _netlist(kicad_cli, sk_top, tmp_path / "sk.net")

    assert _wire_count(render_dir) > 0, "hierarchical render produced no wires"

    result = compare_netlists(cs_net, sk_net)
    assert result.equivalent, "\n".join(result.messages)
