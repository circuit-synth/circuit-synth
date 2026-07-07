"""Headless ERC correction gate for generated schematics (Stage 14, Part A).

Runs KiCad 10's ``kicad-cli sch erc`` on a generated ``.kicad_sch``, parses the
(KiCad-10-nested) JSON report, applies the one reliable autofix -- adding a
``power:PWR_FLAG`` to power nets flagged ``power_pin_not_driven`` -- and iterates a
few times. Everything else is reported, not touched. Modelled on the *idea* of
SKiDL's ``auto_stub`` ERC loop, but circuit_synth-native (no SKiDL dependency).

The gate is **opt-in** (``generate_kicad_project(erc_gate=True)``) and degrades
gracefully: if ``kicad-cli`` is not found it raises :class:`ErcUnavailable`, which
the generator catches and turns into a warning rather than a failure.

Note: this module intentionally re-implements JSON parsing rather than using
``circuit_synth.quality_assurance.erc.run_erc`` -- that helper predates KiCad 10 and
parses a flat ``violations`` list, whereas KiCad 10 nests violations under
``sheets[].violations`` with an ``items`` list. See the Stage-14 findings.
"""

from __future__ import annotations

import json
import logging
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Violation types this gate will auto-repair. Everything else is reported only.
AUTOFIX_TYPES = {"power_pin_not_driven"}

# Regex to pull a component reference (e.g. "#PWR001", "U1") out of an ERC item
# description like: 'Symbol #PWR001 Pin 1 [Power input, Line]'.
_REF_RE = re.compile(r"Symbol\s+(\S+)\s+Pin")

# Same shape but also captures the pin number (group 2), e.g. from
# 'Symbol U1 Pin 8 [+V_{S}, Power input, Line]' -> ("U1", "8").
_REF_PIN_RE = re.compile(r"Symbol\s+(\S+)\s+Pin\s+(\S+)")


class ErcUnavailable(RuntimeError):
    """kicad-cli could not be located, so ERC could not run."""


@dataclass
class ErcItem:
    description: str
    x: Optional[float] = None
    y: Optional[float] = None
    uuid: Optional[str] = None

    @property
    def reference(self) -> Optional[str]:
        m = _REF_RE.search(self.description or "")
        return m.group(1) if m else None

    @property
    def pin(self) -> Optional[str]:
        """The flagged pin number, e.g. "8" from '... Pin 8 [+V_{S}, ...]'."""
        m = _REF_PIN_RE.search(self.description or "")
        return m.group(2) if m else None


@dataclass
class ErcViolation:
    type: str
    severity: str
    description: str
    sheet: str = "/"
    uuid_path: str = "/"
    items: List[ErcItem] = field(default_factory=list)

    @property
    def references(self) -> List[str]:
        return [it.reference for it in self.items if it.reference]

    @property
    def ref_pins(self) -> List[Tuple[str, str]]:
        """[(ref, pin)] for every item that names both a symbol and a pin."""
        out: List[Tuple[str, str]] = []
        for it in self.items:
            if it.reference and it.pin:
                out.append((it.reference, it.pin))
        return out


@dataclass
class ErcReport:
    """Parsed ERC result for one schematic (root sheet + its subsheets)."""

    violations: List[ErcViolation]
    schematic_path: str
    iterations: int = 1
    autofixes_applied: int = 0
    note: Optional[str] = None

    @property
    def error_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == "warning")

    def summary(self) -> str:
        """One-paragraph human summary suitable for pasting into design_log.md."""
        head = (
            f"ERC: {self.error_count} error(s), {self.warning_count} warning(s) "
            f"after {self.iterations} iteration(s)"
        )
        if self.autofixes_applied:
            head += f"; {self.autofixes_applied} PWR_FLAG autofix(es) applied"
        if self.note:
            head += f" [{self.note}]"
        if not self.violations:
            return head + ". Clean."
        lines = [head + ":"]
        for v in self.violations:
            refs = ", ".join(v.references) if v.references else ""
            lines.append(f"  - [{v.severity}] {v.type} {refs}".rstrip())
        return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Running kicad-cli
# --------------------------------------------------------------------------- #


def _find_kicad_cli(explicit: Optional[str] = None) -> str:
    if explicit and Path(explicit).exists():
        return explicit
    # Reuse the robust KiCad-10-aware discovery used by the PCB/netlist paths.
    try:
        from ...pcb.kicad_cli import get_kicad_cli

        cli = get_kicad_cli()
        path = getattr(cli, "kicad_cli_path", None)
        if path and Path(str(path)).exists():
            return str(path)
    except Exception as e:  # pragma: no cover - discovery best-effort
        logger.debug("kicad-cli discovery via pcb.kicad_cli failed: %s", e)
    import shutil

    which = shutil.which("kicad-cli")
    if which:
        return which
    raise ErcUnavailable(
        "kicad-cli not found; install KiCad 10 or pass kicad_cli_path. "
        "ERC gate skipped."
    )


def _parse_erc_json(data: dict, schematic_path: str) -> ErcReport:
    """Parse KiCad-10 ERC JSON (violations nested under sheets[].violations)."""
    violations: List[ErcViolation] = []
    for sheet in data.get("sheets", []):
        sheet_path = sheet.get("path", "/")
        sheet_uuid_path = sheet.get("uuid_path", "/")
        for v in sheet.get("violations", []):
            items = []
            for it in v.get("items", []):
                pos = it.get("pos") or {}
                items.append(
                    ErcItem(
                        description=it.get("description", ""),
                        x=pos.get("x"),
                        y=pos.get("y"),
                        uuid=it.get("uuid"),
                    )
                )
            violations.append(
                ErcViolation(
                    type=v.get("type", "unknown"),
                    severity=v.get("severity", "warning"),
                    description=v.get("description", ""),
                    sheet=sheet_path,
                    uuid_path=sheet_uuid_path,
                    items=items,
                )
            )
    return ErcReport(violations=violations, schematic_path=str(schematic_path))


def run_erc(
    schematic_path, kicad_cli_path: Optional[str] = None, timeout: int = 60
) -> ErcReport:
    """Run ``kicad-cli sch erc --format json --severity-all`` and parse the result.

    Raises :class:`ErcUnavailable` if kicad-cli is missing, ``FileNotFoundError`` if
    the schematic is missing, ``RuntimeError`` if kicad-cli errors for another reason.
    """
    sch = Path(schematic_path)
    if not sch.exists():
        raise FileNotFoundError(f"Schematic not found: {schematic_path}")
    cli = _find_kicad_cli(kicad_cli_path)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tf:
        out_json = tf.name
    try:
        proc = subprocess.run(
            [
                cli,
                "sch",
                "erc",
                "--format",
                "json",
                "--severity-all",
                "--output",
                out_json,
                str(sch),
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        # kicad-cli returns 5 when violations exist (with --exit-code-violations);
        # without that flag it returns 0. Treat 0 and 5 as success.
        if proc.returncode not in (0, 5):
            raise RuntimeError(
                f"kicad-cli sch erc failed (exit {proc.returncode}): {proc.stderr.strip()}"
            )
        with open(out_json, "r", encoding="utf-8") as f:
            data = json.load(f)
    finally:
        Path(out_json).unlink(missing_ok=True)

    return _parse_erc_json(data, str(sch))


# --------------------------------------------------------------------------- #
# (ref, pin) -> net resolution (KiCad ground truth via kicad-cli netlist)
# --------------------------------------------------------------------------- #


def _invert_named_nets(
    named_nets: Dict[str, set],
) -> Dict[Tuple[str, str], str]:
    """Invert ``{net_name: {(ref, pin), ...}}`` to ``{(ref, pin): net_name}``.

    Pure (no kicad-cli), so it is unit-testable with a plain dict. If a (ref, pin)
    appears under more than one net name (should not happen in a valid netlist), the
    last one wins -- callers treat this as a best-effort map.
    """
    mapping: Dict[Tuple[str, str], str] = {}
    for net_name, pins in named_nets.items():
        for ref, pin in pins:
            mapping[(ref, pin)] = net_name
    return mapping


def _pin_net_map(schematic_path: str, kicad_cli: str) -> Dict[Tuple[str, str], str]:
    """(ref, pin) -> net name, from ``kicad-cli sch export netlist`` (KiCad ground
    truth). Raises on export/parse failure -- the caller decides how to degrade."""
    from ...interop.netlist_compare import parse_netlist
    from .selective_wiring import _export_netlist

    tmpdir = Path(tempfile.mkdtemp(prefix="cs_ercfix_"))
    try:
        out = tmpdir / "erc_autofix.net"
        if not _export_netlist(kicad_cli, Path(schematic_path), out):
            raise RuntimeError("netlist export failed")
        parsed = parse_netlist(out)
        return _invert_named_nets(parsed.named_nets)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# --------------------------------------------------------------------------- #
# Classification + autofix
# --------------------------------------------------------------------------- #


def classify(violation: ErcViolation) -> str:
    """``"autofix"`` if the gate can repair this violation, else ``"report"``."""
    return "autofix" if violation.type in AUTOFIX_TYPES else "report"


# A top-level (sheet ...) block: everything up to the first line that is exactly
# one tab + ")" (the sheet's own close; inner closes are more deeply indented).
_SHEET_BLOCK_RE = re.compile(r"\(sheet\b.*?\n\t\)", re.DOTALL)


def _map_sheet_uuids_to_files(root_path: str) -> Dict[str, str]:
    """Map each sheet-symbol UUID to the child ``.kicad_sch`` file it instantiates.

    KiCad's ERC JSON identifies the sheet a violation sits in by ``uuid_path`` =
    ``/<root_uuid>/<sheet_symbol_uuid>[/...]``; the last UUID is the sheet symbol.
    Every ``(sheet ...)`` block (in any schematic in the project dir) carries that
    UUID plus a ``"Sheetfile"`` property, so scanning them lets us resolve a
    violation to the exact subsheet file -- robust to the ``#PWR`` reference
    collisions that make the ref alone ambiguous across sheets. Best-effort: a
    parse miss just leaves that UUID unmapped (caller falls back to the root).
    """
    result: Dict[str, str] = {}
    root = Path(root_path)
    for sch_file in root.parent.glob("*.kicad_sch"):
        try:
            text = sch_file.read_text(encoding="utf-8")
        except OSError:
            continue
        for m in _SHEET_BLOCK_RE.finditer(text):
            block = m.group(0)
            um = re.search(r'\(uuid\s+"?([0-9a-fA-F-]+)"?\)', block)
            fm = re.search(r'"Sheetfile"\s+"([^"]+)"', block)
            if um and fm:
                result[um.group(1)] = str((sch_file.parent / fm.group(1)).resolve())
    return result


_FLG_RE = re.compile(r"#FLG0*(\d+)$")


def _next_flag_index(references) -> int:
    """Return the first free ``#FLG`` numeric suffix given existing references.

    Seeds past any ``#FLGnn`` already present so a second autofix pass (across
    ``erc_gate()`` iterations) does not re-emit ``#FLG01`` and collide with a flag
    written by the previous pass. ``#FLG07`` present -> 8; none present -> 1.
    """
    nums = [
        int(m.group(1)) for ref in references if (m := _FLG_RE.match(str(ref)))
    ]
    return (max(nums) + 1) if nums else 1


def _apply_power_flag_autofixes(
    schematic_path: str,
    report: ErcReport,
    pin_net_map: Dict[Tuple[str, str], str],
) -> int:
    """Add a ``power:PWR_FLAG`` per undriven *net*, wired to the actual flagged pin.

    **Net resolution is hybrid** because ``kicad-cli sch export netlist`` omits power
    pseudo-symbols (refs beginning with ``#`` -- ``#PWR``, and our own ``#FLG``):

    - A flagged pin on a ``#``-prefixed power symbol resolves via the symbol's
      ``value`` (a power symbol's value *is* the net name, and its only pin is "1").
    - A flagged pin on a real part (e.g. an op-amp's +Vs/-Vs rails) resolves via the
      netlist ``pin_net_map`` = (ref, pin) -> net name.

    This fixes the Stage-17 limitation: the old code assumed ``value`` was the net
    and always wired to pin "1", which only held for power symbols, so a real-part
    rail (value == part number, pin "1" a signal pin) could never clear.

    **Sheet-aware (multi-sheet designs).** A hierarchical design's ``#PWR`` symbols
    live in the *child* sheet files (the root sheet may have none), and their refs
    even collide across sheets (two ``#PWR001``). So each violation is routed to the
    subsheet it sits in -- via its ``uuid_path`` (last UUID = sheet symbol) mapped to
    the ``.kicad_sch`` file -- and its ``#PWR`` value/pin position are read from
    THAT file, where the flag + wire are placed and saved. Power nets are global, so
    one flag per net (in whichever sheet its anchor lives) drives it everywhere. On a
    flat design every violation routes to the root file, so behaviour is unchanged.

    One flag per undriven net, wired to that net's deterministic anchor pin. Dangling
    nets (``unconnected-*``) are skipped -- a flag there would mask a real error. The
    canonical flag point (anchor pin + 5.08 mm) being already occupied is the
    stack/re-flag guard: it is deterministic per net (same net -> same anchor -> same
    point), so a flag written by a prior iteration blocks a duplicate here (this is
    the stage-17 position guard, and it doubles as the "net already flagged" guard
    since ``#FLG`` symbols are absent from the netlist).

    Returns the number of flags added; returns 0 (and logs) if kicad-sch-api is
    unavailable or nothing is actionable.
    """
    # Every flagged (ref, pin), tagged with the sheet uuid_path it was reported in
    # and its ERC-item position (a placement fallback when the pin position cannot be
    # resolved from the schematic).
    undriven: List[Tuple[str, str, str, Tuple[Optional[float], Optional[float]]]] = []
    for v in report.violations:
        if classify(v) != "autofix":
            continue
        for it in v.items:
            if it.reference and it.pin:
                undriven.append((it.reference, it.pin, v.uuid_path, (it.x, it.y)))
    if not undriven:
        return 0

    try:
        import kicad_sch_api as ksa
    except Exception as e:  # pragma: no cover
        logger.warning("kicad-sch-api unavailable; cannot apply ERC autofix: %s", e)
        return 0

    root_path = str(Path(schematic_path).resolve())
    sheet_files = _map_sheet_uuids_to_files(schematic_path)

    def _target_file(uuid_path: str) -> str:
        # The last UUID in the path is the sheet symbol; a root-sheet violation
        # (path == '/<root_uuid>') has no child sheet UUID -> the root file.
        if uuid_path:
            last = uuid_path.rstrip("/").rsplit("/", 1)[-1]
            if last in sheet_files:
                return sheet_files[last]
        return root_path

    def _pt_key(x, y):
        return (round(float(x), 2), round(float(y), 2))

    # Lazy per-file loaded schematic + its ref map + occupied #FLG points. Positions
    # are per-sheet, so occupied must be per-file too.
    loaded: Dict[str, dict] = {}

    def _load(file: str) -> dict:
        if file not in loaded:
            sch = ksa.load_schematic(file)
            by_ref = {str(c.reference): c for c in sch.components}
            occupied = {
                _pt_key(c.position.x, c.position.y)
                for c in sch.components
                if str(c.reference).startswith("#FLG") and getattr(c, "position", None)
            }
            loaded[file] = {
                "sch": sch,
                "by_ref": by_ref,
                "occupied": occupied,
                "dirty": False,
            }
        return loaded[file]

    # Seed the flag index past any #FLG already present in ANY involved sheet, so
    # #FLG refs stay unique hierarchy-wide and a second pass never re-emits #FLG01
    # (stage 17.2). For a flat design this is just the root file (unchanged).
    involved = {_target_file(u) for (_, _, u, _) in undriven}
    all_refs: List[str] = []
    for file in involved:
        all_refs.extend(_load(file)["by_ref"].keys())
    flag_index = _next_flag_index(all_refs)

    def _net_of(file_state: dict, ref: str, pin: str) -> Optional[str]:
        # Power pseudo-symbols are excluded from the netlist -> use their value
        # (read from the sheet file the pin actually lives in).
        if ref.startswith("#"):
            comp = file_state["by_ref"].get(ref)
            val = getattr(comp, "value", None) if comp is not None else None
            return str(val) if val else None
        return pin_net_map.get((ref, pin))

    # Group flagged pins by the (global) net they belong to, carrying each pin's
    # sheet file so the flag lands where the anchor actually is.
    net_pins: Dict[str, List[Tuple[str, str, str, Tuple]]] = {}
    for ref, pin, uuid_path, pos in undriven:
        file = _target_file(uuid_path)
        fs = _load(file)
        net = _net_of(fs, ref, pin)
        if net is None:
            logger.debug("ERC autofix: %s could not resolve to a net; skipping", (ref, pin))
            continue
        if net.startswith("unconnected-"):
            # A genuinely dangling power pin -- a flag here masks a real error.
            logger.debug("ERC autofix: %s on dangling net %r; report-only", (ref, pin), net)
            continue
        net_pins.setdefault(net, []).append((ref, pin, file, pos))

    added = 0
    for net in sorted(net_pins):
        # Deterministic anchor: sort by (ref, pin, file), take the first.
        ref, pin, file, item_pos = sorted(net_pins[net])[0]
        fs = _load(file)
        sch = fs["sch"]
        pos = sch.get_component_pin_position(ref, pin)
        if pos is not None:
            px, py = pos.x, pos.y
        elif item_pos and item_pos[0] is not None and item_pos[1] is not None:
            px, py = item_pos
        else:
            logger.debug(
                "ERC autofix: no pin position for %s pin %s; skipping", ref, pin
            )
            continue

        # Canonical flag point for this net. Deterministic (same net -> same anchor
        # -> same point), so an existing flag here means the net is already flagged.
        flag_pos = (px, py + 5.08)
        if _pt_key(*flag_pos) in fs["occupied"]:
            logger.debug(
                "ERC autofix: canonical flag point for net %r already occupied "
                "(via %s pin %s); skipping to avoid stacking",
                net,
                ref,
                pin,
            )
            continue

        flag_ref = f"#FLG{flag_index:02d}"
        flag_index += 1
        sch.components.add(
            "power:PWR_FLAG",
            reference=flag_ref,
            value="PWR_FLAG",
            position=flag_pos,
        )
        fs["occupied"].add(_pt_key(*flag_pos))
        wire = sch.add_wire_between_pins(ref, pin, flag_ref, "1")
        if wire is None:
            logger.debug(
                "ERC autofix: could not wire PWR_FLAG to %s pin %s", ref, pin
            )
            continue
        fs["dirty"] = True
        added += 1
        logger.info(
            "ERC autofix: added PWR_FLAG on net '%s' (via %s pin %s in %s)",
            net,
            ref,
            pin,
            Path(file).name,
        )

    for fs in loaded.values():
        if fs["dirty"]:
            fs["sch"].save()
    return added


# --------------------------------------------------------------------------- #
# The gate loop
# --------------------------------------------------------------------------- #


def _residual_errors(report: ErcReport) -> int:
    """Count non-autofixable *error* violations -- the errors the gate cannot repair.

    The revert guard compares this before/after an autofix iteration: the gate may
    only ever reduce (or hold) the count of errors it can't fix; an iteration that
    increases it (e.g. a wire that shorted two pins) is rolled back.
    """
    return sum(
        1
        for v in report.violations
        if v.severity == "error" and classify(v) != "autofix"
    )


def erc_gate(
    schematic_path,
    max_iterations: int = 3,
    kicad_cli_path: Optional[str] = None,
) -> ErcReport:
    """Run ERC, apply PWR_FLAG autofixes, and iterate until clean or capped.

    Returns the final :class:`ErcReport` (with ``iterations`` and
    ``autofixes_applied`` populated). Raises :class:`ErcUnavailable` if kicad-cli is
    missing -- callers that want graceful degradation should catch it.
    """
    cli = _find_kicad_cli(kicad_cli_path)
    report = run_erc(schematic_path, cli)
    total_fixes = 0
    iteration = 1
    abort_note: Optional[str] = None

    # Snapshot dir for the revert-on-regression guard (stage 18.4). An autofix now
    # draws wires near real symbol bodies, so a wire could in principle touch a third
    # pin and create a NEW error; the gate must never leave the schematic worse.
    backup_dir = Path(tempfile.mkdtemp(prefix="cs_ercgate_"))
    try:
        while iteration < max_iterations:
            if not any(classify(v) == "autofix" for v in report.violations):
                break
            prev_residual = _residual_errors(report)
            backup = backup_dir / "backup.kicad_sch"
            try:
                shutil.copyfile(str(schematic_path), backup)
                # Rebuild the (ref, pin) -> net map each iteration -- the schematic
                # changed on the previous pass, so a stale map would misattribute pins.
                pin_net_map = _pin_net_map(str(schematic_path), cli)
                applied = _apply_power_flag_autofixes(
                    str(schematic_path), report, pin_net_map
                )
            except Exception as e:
                # The gate's contract is "never break generation, always return an
                # honest report". Contain a per-iteration autofix failure: end the
                # loop and return the current report with a note, not propagate.
                abort_note = f"autofix aborted on iteration {iteration}: {type(e).__name__}: {e}"
                logger.warning("ERC gate: %s", abort_note)
                break
            if applied == 0:
                break  # nothing actionable left; don't spin

            new_report = run_erc(schematic_path, cli)
            if _residual_errors(new_report) > prev_residual:
                # This iteration made ERC worse -- roll the file back and stop. The
                # returned report must reflect what is on disk (the restored file).
                shutil.copyfile(backup, str(schematic_path))
                abort_note = f"iteration {iteration} made ERC worse; reverted"
                logger.warning("ERC gate: %s", abort_note)
                report = run_erc(schematic_path, cli)
                break

            total_fixes += applied
            iteration += 1
            report = new_report
    finally:
        shutil.rmtree(backup_dir, ignore_errors=True)

    report.iterations = iteration
    report.autofixes_applied = total_fixes
    report.note = abort_note
    return report
