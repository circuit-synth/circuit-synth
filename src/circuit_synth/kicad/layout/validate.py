# -*- coding: utf-8 -*-
"""Check that a layout still draws the circuit it came from.

A placement decides where wires run, so it can change what is connected to
what. Nothing else in the toolchain would notice: the schematic stays valid and
KiCad opens it happily, only the design is now wrong. Every layout is therefore
checked against the circuit JSON it was generated from, pin for pin.
"""

import json
import logging
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, FrozenSet, List, Optional

logger = logging.getLogger(__name__)

KICAD_NODE = re.compile(r'\(ref\s+"([^"]+)"\)\s*\(pin\s+"([^"]+)"\)')

CLI_CANDIDATES = (
    Path(r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"),
    Path.home() / r"AppData\Local\Programs\KiCad\10.0\bin\kicad-cli.exe",
    Path("/usr/bin/kicad-cli"),
    Path("/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"),
)


def find_kicad_cli() -> Optional[str]:
    """Locate the kicad-cli executable.

    Returns:
        The path to kicad-cli, or None when it is not installed.
    """
    found = shutil.which("kicad-cli")
    if found:
        return found
    return next((str(path) for path in CLI_CANDIDATES if path.exists()), None)


@dataclass
class LayoutProblem:
    """One way a layout differs from the circuit it should draw.

    Attributes:
        kind: ``"shorted"``, ``"broken"`` or ``"missing"``.
        pin: The ``"REF.PIN"`` token affected.
        detail: What changed about it.
    """

    kind: str
    pin: str
    detail: str

    def __str__(self) -> str:
        return f"{self.kind.upper():8s} {self.pin}: {self.detail}"


class _Union:
    """Minimal union-find over hashable keys."""

    def __init__(self) -> None:
        self._parent: Dict[object, object] = {}

    def find(self, key: object) -> object:
        """Return the representative of the set holding a key."""
        self._parent.setdefault(key, key)
        while self._parent[key] != key:
            self._parent[key] = self._parent[self._parent[key]]
            key = self._parent[key]
        return key

    def join(self, first: object, second: object) -> None:
        """Merge the sets holding two keys."""
        left, right = self.find(first), self.find(second)
        if left != right:
            self._parent[left] = right


def intended_partition(circuit_json: Path) -> Dict[str, FrozenSet[str]]:
    """Build the connectivity the Python circuit described.

    The JSON is walked as a hierarchy so two instances of one block keep their
    internal nets apart. A net crosses a sheet boundary exactly where a
    hierarchical port says it does, and a rail drawn with power symbols joins
    by name everywhere, so those are the only places sheets are joined.

    Args:
        circuit_json: The generated circuit JSON.

    Returns:
        A mapping of ``"REF.PIN"`` to the set of pins sharing its net.
    """
    union = _Union()
    tokens = set()

    def walk(node: dict, path: str) -> None:
        for net_name, info in (node.get("nets") or {}).items():
            entries = info.get("nodes", info) if isinstance(info, dict) else info
            is_power = isinstance(info, dict) and info.get("power_symbol")
            key = ("power", net_name) if is_power else (path, net_name)
            for entry in entries:
                token = f"{entry['component']}.{entry['pin']['number']}"
                tokens.add(token)
                union.join(token, key)

        for index, child in enumerate(node.get("subcircuits") or []):
            child_path = f"{path}/{child.get('name', '?')}#{index}"
            for port in child.get("ports") or []:
                union.join((child_path, port["net"]), (path, port["net"]))
            walk(child, child_path)

    walk(json.loads(circuit_json.read_text(encoding="utf-8")), "")

    groups: Dict[object, set] = {}
    for token in tokens:
        groups.setdefault(union.find(token), set()).add(token)

    # Power symbols and PWR_FLAGs exist only in the schematic.
    return {
        token: frozenset(real)
        for group in groups.values()
        if (real := {item for item in group if not item.startswith("#")})
        for token in real
    }


def kicad_partition(root_schematic: Path, work_dir: Path) -> Dict[str, FrozenSet[str]]:
    """Build the connectivity KiCad reads back from a project.

    Args:
        root_schematic: The project's root .kicad_sch.
        work_dir: Directory the exported netlist is written to.

    Returns:
        A mapping of ``"REF.PIN"`` to the set of pins sharing its net.

    Raises:
        RuntimeError: If kicad-cli is unavailable or the export fails.
    """
    cli = find_kicad_cli()
    if cli is None:
        raise RuntimeError("kicad-cli is not installed")

    netlist = work_dir / "layout_check.net"
    result = subprocess.run(
        [
            cli,
            "sch",
            "export",
            "netlist",
            "--format",
            "kicadsexpr",
            "-o",
            str(netlist),
            str(root_schematic),
        ],
        capture_output=True,
        text=True,
        timeout=900,
    )
    if not netlist.exists():
        raise RuntimeError(f"netlist export failed: {result.stderr[-500:]}")

    text = netlist.read_text(encoding="utf-8")
    section = text[text.index("(nets") :]

    partition: Dict[str, FrozenSet[str]] = {}
    for start in (match.start() for match in re.finditer(r"\(net\s", section)):
        depth = 0
        block = ""
        for index in range(start, len(section)):
            if section[index] == "(":
                depth += 1
            elif section[index] == ")":
                depth -= 1
                if depth == 0:
                    block = section[start : index + 1]
                    break
        name = re.search(r'\(name\s+"([^"]*)"\)', block)
        if name and name.group(1).startswith("unconnected"):
            continue
        pins = frozenset(
            f"{ref}.{pin}"
            for ref, pin in KICAD_NODE.findall(block)
            if not ref.startswith("#")
        )
        for token in pins:
            partition[token] = pins
    return partition


def validate_layout(
    root_schematic: Path, circuit_json: Path, work_dir: Optional[Path] = None
) -> List[LayoutProblem]:
    """Compare a laid-out project against the circuit it was generated from.

    Args:
        root_schematic: The project's root .kicad_sch.
        circuit_json: The generated circuit JSON.
        work_dir: Where to write the exported netlist. Defaults to the
            project directory.

    Returns:
        The differences found, empty when the layout draws the circuit exactly.
    """
    expected = intended_partition(circuit_json)
    actual = kicad_partition(root_schematic, work_dir or root_schematic.parent)

    problems: List[LayoutProblem] = []
    for pin, group in sorted(expected.items()):
        found = actual.get(pin)
        if found is None:
            problems.append(
                LayoutProblem("missing", pin, "not present in the netlist at all")
            )
            continue
        if found == group:
            continue
        extra = sorted(found - group)
        lost = sorted(group - found)
        if extra:
            problems.append(LayoutProblem("shorted", pin, f"also joined to {extra}"))
        else:
            problems.append(LayoutProblem("broken", pin, f"no longer joined to {lost}"))
    return problems


def erc_violations(root_schematic: Path, work_dir: Optional[Path] = None) -> List[str]:
    """Run KiCad ERC and return the violation type of each reported error.

    Args:
        root_schematic: The project's root .kicad_sch.
        work_dir: Where to write the report.

    Returns:
        The bracketed violation names, one per error.
    """
    cli = find_kicad_cli()
    if cli is None:
        return []

    report = (work_dir or root_schematic.parent) / "layout_erc.rpt"
    subprocess.run(
        [cli, "sch", "erc", "--severity-error", "-o", str(report), str(root_schematic)],
        capture_output=True,
        text=True,
        timeout=900,
        check=False,
    )
    if not report.exists():
        return []
    return re.findall(r"^\[(\w+)\]", report.read_text(encoding="utf-8"), re.M)
