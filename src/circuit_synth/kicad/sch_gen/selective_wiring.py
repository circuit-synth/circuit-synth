"""Selective wire routing for simple local nets (Stage 14, Part B).

circuit_synth connects everything with labels and draws no wires. SKiDL's
``auto_stub`` does the inverse: route wires by default, and *stub* (label) only the
hard nets -- power, high-fanout, long. This module applies SKiDL's heuristic
backwards: draw a real ``(wire ...)`` for the nets SKiDL would happily route -- a
**2-pin, short, same-sheet, non-power** net -- and leave everything else as labels.

It runs as a **post-generation pass** on the written ``.kicad_sch`` (opt-in via
``generate_kicad_project(selective_wires=True)``), so it needs no surgery inside the
placement code. Safety comes from a netlist-equivalence gate: a drawn wire could in
principle cross a third pin and short two nets, so after drawing we re-export the
netlist and require the pin-partition to be **unchanged** vs. the labels-only
baseline. If anything shifted, the whole pass reverts and the original file is kept.

Scope: fresh generation. The labels are left in place (the wire is redundant-but-
visible connectivity); removing them is a later refinement.
"""

from __future__ import annotations

import logging
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Mirror SKiDL's auto_stub_max_wire_dist (2000 mils) as the max pin-to-pin span we
# will route. 2000 mil = 50.8 mm.
DEFAULT_MAX_WIRE_DIST_MM = 50.8


def _manhattan(a, b) -> float:
    return abs(a.x - b.x) + abs(a.y - b.y)


def _export_netlist(cli: str, sch: Path, out: Path, timeout: int = 60) -> bool:
    proc = subprocess.run(
        [cli, "sch", "export", "netlist", str(sch), "--output", str(out)],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return out.exists() and proc.returncode == 0


def wire_local_nets(
    schematic_path,
    *,
    max_wire_dist_mm: float = DEFAULT_MAX_WIRE_DIST_MM,
    kicad_cli_path: Optional[str] = None,
) -> Dict[str, object]:
    """Draw wires for eligible 2-pin local nets on *schematic_path* (in place).

    Returns a summary dict: ``{"wires_drawn", "eligible", "reverted", "reason"}``.
    Never raises for the "cannot verify" cases -- it degrades to drawing nothing.
    """
    result: Dict[str, object] = {
        "wires_drawn": 0,
        "eligible": 0,
        "reverted": False,
        "reason": "",
        "wires_in_file": 0,
    }

    sch_path = Path(schematic_path)
    if not sch_path.exists():
        result["reason"] = "schematic not found"
        return result

    # kicad-cli + kicad-sch-api are both required to verify safely.
    try:
        from .erc_gate import ErcUnavailable, _find_kicad_cli

        cli = _find_kicad_cli(kicad_cli_path)
    except Exception as e:
        result["reason"] = f"kicad-cli unavailable: {e}"
        return result
    try:
        import kicad_sch_api as ksa

        from ...interop.netlist_compare import parse_netlist
    except Exception as e:  # pragma: no cover
        result["reason"] = f"dependency unavailable: {e}"
        return result

    tmpdir = Path(tempfile.mkdtemp(prefix="cs_selwire_"))
    try:
        # 1) Baseline connectivity (labels only).
        base_net = tmpdir / "before.net"
        if not _export_netlist(cli, sch_path, base_net):
            result["reason"] = "baseline netlist export failed"
            return result
        before = parse_netlist(base_net)
        partition_before = before.partition()

        # 2) Find eligible nets and their pin coordinates.
        sch = ksa.load_schematic(str(sch_path))
        candidates = _eligible_nets(sch, before.named_nets, max_wire_dist_mm)
        result["eligible"] = len(candidates)
        if not candidates:
            result["reason"] = "no eligible 2-pin local nets"
            return result

        # 3) Draw the wires.
        drawn = 0
        for r1, p1, r2, p2 in candidates:
            wire = sch.add_wire_between_pins(r1, p1, r2, p2)
            if wire is not None:
                drawn += 1
        if drawn == 0:
            result["reason"] = "no wires could be drawn (pin lookup failed)"
            return result

        # 4) Save to a temp copy and verify connectivity is unchanged.
        trial = tmpdir / sch_path.name
        sch.save(str(trial))
        after_net = tmpdir / "after.net"
        if not _export_netlist(cli, trial, after_net):
            result["reason"] = "post-wire netlist export failed; reverted"
            result["reverted"] = True
            return result
        partition_after = parse_netlist(after_net).partition()

        if partition_after != partition_before:
            # A wire shorted something -- do not touch the real file.
            result["reverted"] = True
            result["reason"] = "wiring changed connectivity; reverted"
            logger.warning(
                "Selective wiring reverted on %s: pin-partition changed", sch_path.name
            )
            return result

        # 5) Safe -- commit to the real file.
        shutil.copyfile(trial, sch_path)
        result["wires_drawn"] = drawn
        # Read the committed file back and report the actual wire count as ground
        # truth (stage 17.5). A false "skipped" log (G2) plus a bad grep pattern
        # (counting "(wire " with a trailing space, which the writer never emits)
        # produced a confident, wrong wire-persistence bug report. Callers/logs now
        # carry what is on disk, not intent. Token-boundary pattern -- the writer
        # emits "(wire\n".
        committed_text = sch_path.read_text(encoding="utf-8")
        result["wires_in_file"] = len(re.findall(r"\(wire\b", committed_text))
        logger.info(
            "Selective wiring drew %d wire(s) on %s (%d in file)",
            drawn,
            sch_path.name,
            result["wires_in_file"],
        )
        return result
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def _eligible_nets(
    sch, named_nets: Dict[str, set], max_wire_dist_mm: float
) -> List[Tuple[str, str, str, str]]:
    """Return [(ref1, pin1, ref2, pin2)] for nets eligible for a drawn wire.

    Eligible = exactly 2 real (non-``#``) pins, no power pseudo-symbol on the net,
    not a power net by name, both pins resolvable on this sheet, and pin-to-pin
    manhattan distance within ``max_wire_dist_mm``.
    """
    try:
        from ...core.power_net_registry import is_power_net
    except Exception:  # pragma: no cover

        def is_power_net(_name):  # type: ignore
            return False

    out: List[Tuple[str, str, str, str]] = []
    for name, pins in named_nets.items():
        has_pseudo = any(ref.startswith("#") for ref, _ in pins)
        real = sorted((ref, pin) for ref, pin in pins if not ref.startswith("#"))
        if has_pseudo or len(real) != 2:
            continue
        if is_power_net(name):
            continue
        (r1, p1), (r2, p2) = real
        pos1 = sch.get_component_pin_position(r1, p1)
        pos2 = sch.get_component_pin_position(r2, p2)
        if pos1 is None or pos2 is None:  # a pin on another sheet -> not local
            continue
        dist = _manhattan(pos1, pos2)
        if dist > max_wire_dist_mm:
            continue
        # Two pins at the SAME point (e.g. a multi-pad sensor's redundant/stacked
        # pads sharing a net, like the SiPM's TSV pins) would produce a zero-length
        # wire, which KiCad loads but crashes on when saving. They are already
        # electrically coincident, so no wire is needed -- skip them.
        if dist == 0:
            continue
        out.append((r1, p1, r2, p2))
    return out
