"""Enforce the language-agnostic loop boundary (Stage 16).

Grep/AST-level checks that the design loop's *agnostic* layer stays DSL-neutral, so
a future circuit-synth -> SKiDL (or any DSL) swap stays a live option at zero cost.
Rules R2/R3/R4 of ``workingdocs/design_considerations/loop-boundary-contract.md``; R1 lives in
``kicad-sch-api/tests/mcp/test_boundary_contract.py``. Pure file reads — fast,
dependency-free.
"""

import ast
import re
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

# circuit-synth repo root: .../circuit-synth/tests/unit/<this file>
REPO = Path(__file__).resolve().parents[2]
TEMPLATE = REPO / "src" / "circuit_synth" / "data" / "templates" / "example_project"
TOOLS = TEMPLATE / "tools"
SKILL = TEMPLATE / ".claude" / "skills" / "design-circuit" / "SKILL.md"

# circuit_synth-specific DSL / simulation-API tokens. Every occurrence in SKILL.md
# must live inside a <!-- language-coupled --> region (rule R3). Curated to the core
# API surface (Component/Net appear in agnostic Phase-2 sourcing prose and are
# intentionally not enforced here — see the contract doc's layer table).
COUPLED_TOKENS = [
    "@circuit",
    "generate_kicad_project(",
    "circuit.simulate(",
    ".operating_point(",
    ".ac_analysis(",
    ".transient_analysis(",
    "force_regenerate",
    ".save_bode_plot(",
    ".save_transient_plot(",
    ".save_dc_transfer_plot(",
    "model_provenance",
    ".get_voltage(",
]

OPEN_MARK = "<!-- language-coupled"
CLOSE_MARK = "<!-- /language-coupled"


def _coupled_regions(lines):
    """Return inclusive (start, end) 0-based line ranges of language-coupled blocks.

    Raises AssertionError if markers are unbalanced or improperly nested.
    """
    regions = []
    open_at = None
    for i, line in enumerate(lines):
        if CLOSE_MARK in line:
            assert open_at is not None, f"close marker without open at line {i + 1}"
            regions.append((open_at, i))
            open_at = None
        elif OPEN_MARK in line:
            assert open_at is None, f"nested/duplicate open marker at line {i + 1}"
            open_at = i
    assert open_at is None, "unclosed language-coupled marker"
    return regions


def _inside(regions, idx):
    return any(start <= idx <= end for start, end in regions)


# --------------------------------------------------------------------------- #
# R2 — find_symbol.py stays stdlib-only
# --------------------------------------------------------------------------- #


def test_r2_find_symbol_is_stdlib_only():
    src = (TOOLS / "find_symbol.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:  # relative import -> not stdlib
                roots.add(f".<relative level {node.level}>")
            elif node.module:
                roots.add(node.module.split(".")[0])

    stdlib = set(sys.stdlib_module_names)
    non_stdlib = {r for r in roots if r not in stdlib}
    assert not non_stdlib, (
        f"find_symbol.py must import stdlib only (R2); found non-stdlib roots: "
        f"{sorted(non_stdlib)}"
    )


# --------------------------------------------------------------------------- #
# R4 — every tool the skill references ships in the template
# --------------------------------------------------------------------------- #


def test_r4_skill_referenced_tools_exist():
    text = SKILL.read_text(encoding="utf-8")
    referenced = sorted(set(re.findall(r"tools/([A-Za-z0-9_]+\.py)", text)))
    assert referenced, "expected SKILL.md to reference at least one tools/*.py"
    missing = [name for name in referenced if not (TOOLS / name).exists()]
    assert not missing, f"SKILL.md references tools absent from the template (R4): {missing}"


# --------------------------------------------------------------------------- #
# R3 — coupled DSL/API confined to marked sections
# --------------------------------------------------------------------------- #


def test_r3_markers_present_and_balanced():
    lines = SKILL.read_text(encoding="utf-8").splitlines()
    regions = _coupled_regions(lines)
    assert regions, "SKILL.md has no <!-- language-coupled --> regions (R3)"


def test_r3_coupled_tokens_only_inside_marked_regions():
    lines = SKILL.read_text(encoding="utf-8").splitlines()
    regions = _coupled_regions(lines)

    violations = []
    for i, line in enumerate(lines):
        if line.strip().startswith("<!--"):
            continue  # the marker comments themselves may name tokens
        for tok in COUPLED_TOKENS:
            if tok in line and not _inside(regions, i):
                violations.append((i + 1, tok, line.strip()))
    assert not violations, (
        "coupled DSL/API tokens found outside a <!-- language-coupled --> region "
        f"(R3):\n" + "\n".join(f"  line {ln}: {tok!r} in {txt}" for ln, tok, txt in violations)
    )


def test_r3_no_bare_circuit_synth_import_outside_marked_regions():
    lines = SKILL.read_text(encoding="utf-8").splitlines()
    regions = _coupled_regions(lines)
    for i, line in enumerate(lines):
        if "from circuit_synth import" in line or "import circuit_synth" in line:
            assert _inside(regions, i), (
                f"raw circuit_synth import outside a language-coupled region at "
                f"line {i + 1} (R3): {line.strip()}"
            )
