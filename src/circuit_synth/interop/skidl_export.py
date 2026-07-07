"""circuit_synth -> SKiDL render adapter (Stage 13).

This is an *optional pretty-rendering backend*. circuit_synth places components on
a grid and connects them with labels; SKiDL has a force-directed placer + switchbox
maze router (``skidl/schematics/place.py`` + ``route.py``) that emit ``.kicad_sch``
files with *real routed wires*. This adapter converts a circuit_synth
:class:`~circuit_synth.core.circuit.Circuit` into a standalone SKiDL **script**, then
runs that script with a SKiDL-capable interpreter to render a wire-routed schematic
into a separate output directory.

Why a script + subprocess rather than an in-process bridge:

* Interpreter isolation -- SKiDL declares support for Python 3.6-3.13; the
  circuit_synth env here runs on 3.14. The child runs under a dedicated
  ``.venv-skidl`` (see Stage 13 Phase 0), so the version question disappears.
* The emitted script is an inspectable, re-runnable artifact and doubles as a
  general circuit_synth -> SKiDL exporter.

The circuit_synth-generated ``.kicad_sch`` remains authoritative (the edit/preserve
loop and simulation operate on it); the SKiDL render is a human-readable *view*.

Nothing in this module imports ``skidl``; the import happens only inside the emitted
script, executed by the child interpreter.

Public API
----------
``export_skidl_script(circuit, out_path, ...)`` -- emit the SKiDL script only.
``render_with_skidl(circuit, out_dir, ...)`` -- emit + run it, returning the top
    ``.kicad_sch`` path.
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Default KiCad-10 symbol library path (same .kicad_sym format SKiDL's kicad9
# reader consumes). Overridable per call and by a pre-set KICAD9_SYMBOL_DIR in the
# child's environment (the emitted script uses os.environ.setdefault).
DEFAULT_KICAD_SYMBOL_DIR = r"C:\Program Files\KiCad\10.0\share\kicad\symbols"

# Env var naming the interpreter that can import skidl (the Stage-13 .venv-skidl).
SKIDL_PYTHON_ENV = "CIRCUIT_SYNTH_SKIDL_PYTHON"


# --------------------------------------------------------------------------- #
# Traversal
# --------------------------------------------------------------------------- #


class _IdentFactory:
    """Hands out unique, valid Python identifiers derived from arbitrary names."""

    def __init__(self, prefix: str = "n"):
        self._prefix = prefix
        self._used: Dict[str, str] = {}
        self._taken: set = set()

    def get(self, key: str) -> str:
        if key in self._used:
            return self._used[key]
        base = "".join(ch if (ch.isalnum() or ch == "_") else "_" for ch in str(key))
        if not base or not (base[0].isalpha() or base[0] == "_"):
            base = f"{self._prefix}_{base}"
        candidate = base
        i = 1
        while candidate in self._taken:
            candidate = f"{base}_{i}"
            i += 1
        self._taken.add(candidate)
        self._used[key] = candidate
        return candidate


def _iter_groups(circuit) -> List[Tuple[str, object, list]]:
    """Flatten the circuit tree into (group_name, circuit_node, components) tuples.

    One group per circuit node (top circuit + each subcircuit, depth-first), mirroring
    circuit_synth's own hierarchy so each becomes an independently placed/routed SKiDL
    ``@subcircuit``. Groups with no components of their own are dropped.
    """
    groups: List[Tuple[str, object, list]] = []
    names = _IdentFactory(prefix="grp")

    def walk(node, path: str):
        comps = list(getattr(node, "_components", {}).values())
        raw_name = getattr(node, "name", None) or "circuit"
        gname = names.get(f"{path}/{raw_name}")
        if comps:
            groups.append((gname, node, comps))
        for sub in getattr(node, "_subcircuits", []) or []:
            walk(sub, f"{path}/{raw_name}")

    walk(circuit, "")
    return groups


def _component_pin_nets(component) -> List[Tuple[object, object]]:
    """[(pin_key, net)] for a component's *connected* pins, in pin-number order.

    ``pin_key`` is an int for numeric pin numbers (so ``part[1]``) else the raw
    string. Pins with no net attached are skipped.
    """
    pin_map = getattr(component, "_pins", None) or {}

    def sort_key(item):
        num = str(item[0])
        return (0, int(num)) if num.isdigit() else (1, num)

    out: List[Tuple[object, object]] = []
    for num, pin in sorted(pin_map.items(), key=sort_key):
        net = getattr(pin, "net", None)
        if net is None or not getattr(net, "name", None):
            continue
        num_s = str(num)
        pin_key = int(num_s) if num_s.isdigit() else num_s
        out.append((pin_key, net))
    return out


# --------------------------------------------------------------------------- #
# Script emission
# --------------------------------------------------------------------------- #


def _split_symbol(symbol: str) -> Tuple[str, str]:
    """'Device:R' -> ('Device', 'R'); a bare 'R' -> ('', 'R')."""
    if symbol and ":" in symbol:
        lib, name = symbol.split(":", 1)
        return lib, name
    return "", symbol or ""


def _render_script_text(
    circuit,
    *,
    top_name: str,
    title: str,
    flatness: float,
    auto_stub: bool,
    symbol_dir: str,
) -> str:
    groups = _iter_groups(circuit)
    if not groups:
        raise ValueError(
            "circuit has no components to render; nothing to hand to SKiDL"
        )

    # Global net table: name -> is_power (OR-reduced across every pin that sees it).
    net_is_power: Dict[str, bool] = {}
    for _gname, _node, comps in groups:
        for comp in comps:
            for _pin_key, net in _component_pin_nets(comp):
                name = net.name
                net_is_power[name] = net_is_power.get(name, False) or bool(
                    getattr(net, "is_power", False)
                )

    net_vars = _IdentFactory(prefix="n")
    net_var = {name: net_vars.get(name) for name in net_is_power}

    lines: List[str] = []
    w = lines.append

    w('"""Auto-generated by circuit_synth.interop.skidl_export -- do not edit by hand.')
    w("")
    w(f"Renders circuit {circuit.name!r} to a wire-routed KiCad schematic via SKiDL.")
    w("Run with a skidl-capable interpreter (Stage-13 .venv-skidl):")
    w(f"    python {top_name}_skidl.py")
    w('"""')
    w("import os")
    w("")
    w("os.environ.setdefault(" f'"KICAD9_SYMBOL_DIR", r"{symbol_dir}")')
    w("")
    w("from skidl import POWER, Net, Part, generate_schematic, reset, subcircuit")
    w("")
    w("")

    # One @subcircuit function per group.
    group_call_args: List[Tuple[str, List[str]]] = []
    for gname, _node, comps in groups:
        # Determine the ordered set of net names this group references.
        group_net_order: List[str] = []
        seen = set()
        for comp in comps:
            for _pin_key, net in _component_pin_nets(comp):
                if net.name not in seen:
                    seen.add(net.name)
                    group_net_order.append(net.name)

        params = _IdentFactory(prefix="p")
        param_of = {name: params.get(name) for name in group_net_order}
        param_list = [param_of[name] for name in group_net_order]

        w("@subcircuit")
        w(f"def {gname}({', '.join(param_list)}):")
        if not comps:
            w("    pass")
        refs = _IdentFactory(prefix="part")
        for comp in comps:
            lib, name = _split_symbol(getattr(comp, "symbol", "") or "")
            var = refs.get(getattr(comp, "ref", None) or "part")
            kwargs = [f"{lib!r}", f"{name!r}"]
            ref = getattr(comp, "ref", None)
            if ref:
                kwargs.append(f"ref={ref!r}")
            value = getattr(comp, "value", None)
            if value is not None and str(value) != "":
                kwargs.append(f"value={str(value)!r}")
            footprint = getattr(comp, "footprint", None)
            if footprint:
                kwargs.append(f"footprint={str(footprint)!r}")
            w(f"    {var} = Part({', '.join(kwargs)})")
            for pin_key, net in _component_pin_nets(comp):
                w(f"    {var}[{pin_key!r}] += {param_of[net.name]}")
        w("")
        w("")
        group_call_args.append((gname, [net_var[n] for n in group_net_order]))

    # build(): create every net once, then call each group with its nets.
    w("def build():")
    w("    reset()")
    for name in net_is_power:
        var = net_var[name]
        w(f"    {var} = Net({name!r})")
        if net_is_power[name]:
            w(f"    {var}.drive = POWER")
    w("")
    for gname, call_args in group_call_args:
        w(f"    {gname}({', '.join(call_args)})")
    w("")
    w("")
    w('if __name__ == "__main__":')
    w("    build()")
    w("    generate_schematic(")
    w('        filepath=".",')
    w(f"        top_name={top_name!r},")
    w(f"        title={title!r},")
    w(f"        flatness={float(flatness)!r},")
    w(f"        auto_stub={bool(auto_stub)!r},")
    w('        auto_stub_fallback="labels",')
    w("    )")
    w('    print("SKIDL_RENDER_OK")')
    w("")

    return "\n".join(lines)


def export_skidl_script(
    circuit,
    out_path,
    *,
    top_name: Optional[str] = None,
    title: Optional[str] = None,
    flatness: float = 0.0,
    auto_stub: bool = True,
    symbol_dir: Optional[str] = None,
) -> Path:
    """Emit a standalone SKiDL script that renders *circuit* to a ``.kicad_sch``.

    The script is self-contained: it sets ``KICAD9_SYMBOL_DIR`` (via ``setdefault``,
    so a pre-set env wins), builds the SKiDL part/net model from *circuit*, and calls
    ``generate_schematic``. It does **not** import circuit_synth, so it runs under any
    skidl-capable interpreter.

    Returns the path the script was written to.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    top = top_name or _safe_top_name(circuit.name)
    text = _render_script_text(
        circuit,
        top_name=top,
        title=title or f"{circuit.name} (SKiDL render)",
        flatness=flatness,
        auto_stub=auto_stub,
        symbol_dir=symbol_dir or DEFAULT_KICAD_SYMBOL_DIR,
    )
    out_path.write_text(text, encoding="utf-8")
    logger.info("Wrote SKiDL export script to %s", out_path)
    return out_path


def _safe_top_name(name: str) -> str:
    base = "".join(
        ch if (ch.isalnum() or ch == "_") else "_" for ch in str(name or "circuit")
    )
    if not base or not (base[0].isalpha() or base[0] == "_"):
        base = f"c_{base}"
    return base


# --------------------------------------------------------------------------- #
# Rendering (subprocess)
# --------------------------------------------------------------------------- #


class SkidlRenderError(RuntimeError):
    """SKiDL rendering failed (missing interpreter, import error, or a run error)."""


def render_with_skidl(
    circuit,
    out_dir,
    *,
    python_exe: Optional[str] = None,
    top_name: Optional[str] = None,
    title: Optional[str] = None,
    flatness: float = 0.0,
    auto_stub: bool = True,
    symbol_dir: Optional[str] = None,
    timeout: int = 600,
) -> Path:
    """Render *circuit* to a wire-routed ``.kicad_sch`` set under *out_dir* via SKiDL.

    Emits the export script into *out_dir* and runs it with *python_exe* (default:
    ``$CIRCUIT_SYNTH_SKIDL_PYTHON`` else ``sys.executable``). The child must be able
    to ``import skidl`` -- see Stage-13 Phase 0 (``.venv-skidl``).

    Returns the path to the top ``<top_name>.kicad_sch``. Raises
    :class:`SkidlRenderError` with actionable text on any failure.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    top = top_name or _safe_top_name(circuit.name)

    script_path = out_dir / f"{top}_skidl.py"
    export_skidl_script(
        circuit,
        script_path,
        top_name=top,
        title=title,
        flatness=flatness,
        auto_stub=auto_stub,
        symbol_dir=symbol_dir,
    )

    exe = python_exe or os.environ.get(SKIDL_PYTHON_ENV) or sys.executable
    logger.info("Rendering with SKiDL: %s %s (cwd=%s)", exe, script_path.name, out_dir)

    try:
        proc = subprocess.run(
            [exe, script_path.name],
            cwd=str(out_dir),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError as e:
        raise SkidlRenderError(
            f"Could not launch SKiDL interpreter {exe!r}: {e}. Set the "
            f"{SKIDL_PYTHON_ENV} environment variable to a Python that can "
            "'import skidl' (see Stage-13 Phase 0: create .venv-skidl)."
        ) from e
    except subprocess.TimeoutExpired as e:
        raise SkidlRenderError(
            f"SKiDL render timed out after {timeout}s (placement/routing can be "
            "slow on large circuits; raise the timeout= argument)."
        ) from e

    if proc.returncode != 0 or "SKIDL_RENDER_OK" not in (proc.stdout or ""):
        detail = (proc.stdout or "") + "\n" + (proc.stderr or "")
        hint = ""
        if "No module named 'skidl'" in detail or "ModuleNotFoundError" in detail:
            hint = (
                f"\n\nThe interpreter {exe!r} cannot import skidl. Set "
                f"{SKIDL_PYTHON_ENV} to the Stage-13 .venv-skidl python "
                "(Phase 0: `uv pip install --python .venv-skidl\\Scripts\\python.exe "
                "-e .\\skidl`)."
            )
        raise SkidlRenderError(
            f"SKiDL render failed (exit {proc.returncode}).{hint}\n"
            f"--- script ---\n{script_path}\n--- output ---\n{detail.strip()}"
        )

    top_sch = out_dir / f"{top}.kicad_sch"
    if not top_sch.exists():
        # SKiDL derives the top filename from top_name; if that ever changes, fall
        # back to the newest .kicad_sch produced.
        candidates = sorted(
            out_dir.glob("*.kicad_sch"), key=lambda p: p.stat().st_mtime, reverse=True
        )
        if not candidates:
            raise SkidlRenderError(
                f"SKiDL reported success but produced no .kicad_sch in {out_dir}."
            )
        top_sch = candidates[0]
    logger.info("SKiDL render complete: %s", top_sch)
    return top_sch
