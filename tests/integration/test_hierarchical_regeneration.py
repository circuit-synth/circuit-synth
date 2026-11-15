"""
Regression: regenerating a hierarchical project into an existing directory
must update child sheets, not just the root sheet.

Previously HierarchicalSynchronizer never discovered child sheets (it expected
attribute-style sheet objects, kicad-sch-api returns dicts), so only the root
sheet was synced and child sheets silently kept stale connectivity.
"""

import re
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List

import kicad_sch_api as ksa
import pytest

from circuit_synth import Component, Net, circuit
from circuit_synth.kicad.schematic.hierarchical_synchronizer import (
    HierarchicalSynchronizer,
)


def _make_r() -> Component:
    return Component(
        symbol="Device:R",
        ref="R",
        value="1k",
        footprint="Resistor_SMD:R_0402_1005Metric",
    )


def _make_c() -> Component:
    return Component(
        symbol="Device:C",
        ref="C",
        value="100nF",
        footprint="Capacitor_SMD:C_0402_1005Metric",
    )


def _build_v1():
    """R2 and C1 joined pin-to-pin across sheets, other pins unconnected."""

    @circuit(name="sheet_a")
    def sheet_a(holder):
        holder["r"] = _make_r()

    @circuit(name="sheet_b")
    def sheet_b(r):
        c = _make_c()
        r["2"] += c["1"]

    @circuit(name="top")
    def top():
        holder: Dict = {}
        sheet_a(holder)
        sheet_b(holder["r"])

    return top()


def _build_v2():
    """Shared named nets gnd and r_c_mid across sibling sheets."""

    @circuit(name="sheet_a")
    def sheet_a(mid_net, gnd):
        r = _make_r()
        r["2"] += mid_net
        r["1"] += gnd

    @circuit(name="sheet_b")
    def sheet_b(mid_net, gnd):
        c = _make_c()
        c["1"] += mid_net
        c["2"] += gnd

    @circuit(name="top")
    def top():
        gnd = Net(name="gnd")
        mid_net = Net(name="r_c_mid")
        sheet_a(mid_net, gnd)
        sheet_b(mid_net, gnd)

    return top()


def _generate(circ, project_dir: Path) -> None:
    result = circ.generate_kicad_project(
        str(project_dir), generate_pcb=False, update_source_refs=False
    )
    assert result["success"], result.get("error")


def _hier_label_names(sch_path: Path) -> List[str]:
    sch = ksa.Schematic.load(str(sch_path))
    return sorted(lbl.text for lbl in sch.hierarchical_labels)


def _kicad_cli_nets(sch_path: Path, out: Path) -> Dict[str, List[str]]:
    subprocess.run(
        [
            "kicad-cli",
            "sch",
            "export",
            "netlist",
            "--format",
            "kicadsexpr",
            "-o",
            str(out),
            str(sch_path),
        ],
        check=True,
        capture_output=True,
    )
    text = out.read_text()
    nets: Dict[str, List[str]] = {}
    for block in re.split(r"\(net\s+\(code", text)[1:]:
        name = re.search(r'\(name "([^"]*)"\)', block).group(1)
        nodes = re.findall(r'\(ref "([^"]+)"\)\s*\(pin "([^"]+)"\)', block)
        nets[name] = sorted(f"{r}.{p}" for r, p in nodes)
    return nets


@pytest.fixture
def regenerated_project(tmp_path: Path) -> Path:
    project_dir = tmp_path / "top"
    _generate(_build_v1(), project_dir)
    _generate(_build_v2(), project_dir)
    return project_dir


def test_synchronizer_discovers_child_sheets(tmp_path: Path) -> None:
    project_dir = tmp_path / "top"
    _generate(_build_v2(), project_dir)

    sync = HierarchicalSynchronizer(str(project_dir / "top.kicad_pro"))

    child_files = sorted(c.file_path.name for c in sync.root_sheet.children)
    assert child_files == ["sheet_a.kicad_sch", "sheet_b.kicad_sch"]


def test_regeneration_updates_child_sheet_labels(regenerated_project: Path) -> None:
    for sheet in ("sheet_a", "sheet_b"):
        labels = _hier_label_names(regenerated_project / f"{sheet}.kicad_sch")
        assert "gnd" in labels, f"{sheet}: {labels}"
        assert "r_c_mid" in labels, f"{sheet}: {labels}"
        assert "N$1" not in labels, f"{sheet}: stale label kept: {labels}"


@pytest.mark.skipif(shutil.which("kicad-cli") is None, reason="kicad-cli required")
def test_regeneration_netlist_matches_python(
    regenerated_project: Path, tmp_path: Path
) -> None:
    nets = _kicad_cli_nets(regenerated_project / "top.kicad_sch", tmp_path / "n.net")

    assert nets.get("/gnd") == ["C1.2", "R1.1"], nets
    assert nets.get("/r_c_mid") == ["C1.1", "R1.2"], nets
    assert not any(n.startswith("unconnected") for n in nets), nets


def _build_v2_with_parent_component():
    """Parent uses gnd itself; r_c_mid only passes between sibling sheets."""

    @circuit(name="sheet_a")
    def sheet_a(mid_net, gnd):
        r = _make_r()
        r["2"] += mid_net
        r["1"] += gnd

    @circuit(name="sheet_b")
    def sheet_b(mid_net, gnd):
        c = _make_c()
        c["1"] += mid_net
        c["2"] += gnd

    @circuit(name="top")
    def top():
        gnd = Net(name="gnd")
        mid_net = Net(name="r_c_mid")
        sheet_a(mid_net, gnd)
        sheet_b(mid_net, gnd)
        c2 = _make_c()
        c2["1"] += gnd
        c2["2"] += gnd

    return top()


@pytest.mark.skipif(shutil.which("kicad-cli") is None, reason="kicad-cli required")
@pytest.mark.parametrize("regenerate", [False, True], ids=["fresh", "regenerated"])
def test_sibling_only_net_connects_when_parent_has_nets(
    tmp_path: Path, regenerate: bool
) -> None:
    project_dir = tmp_path / "top"
    if regenerate:
        _generate(_build_v1(), project_dir)
    _generate(_build_v2_with_parent_component(), project_dir)

    nets = _kicad_cli_nets(project_dir / "top.kicad_sch", tmp_path / "n.net")

    assert nets.get("/r_c_mid") == ["C1.1", "R1.2"], nets
    assert nets.get("/gnd") == ["C1.2", "C2.1", "C2.2", "R1.1"], nets

