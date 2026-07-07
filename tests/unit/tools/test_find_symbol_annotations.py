"""find_symbol.py annotates pin counts + extends-parents (Stage 23.7).

Surfaces the derived-symbol trap from run 4: ADA4807-2ARM's KiCad symbol
`(extends "LM2904")` inherits an 8-pin dual pinout while the ARMZ part is
MSOP-10, so wiring it blind mis-maps pins. The annotation makes both the
derived-ness and the (parent-resolved) pin count visible in the tool output.

Loads the bundled template tool by path and drives its ``find_symbols`` against
the stock KiCad ``Amplifier_Operational`` library; skips if KiCad is absent.
"""

import importlib.util
from pathlib import Path

import pytest

_TOOL = (
    Path(__file__).resolve().parents[3]
    / "src/circuit_synth/data/templates/example_project/tools/find_symbol.py"
)


def _load_tool():
    spec = importlib.util.spec_from_file_location("find_symbol_tool", _TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _has_kicad_symbols(mod) -> bool:
    return mod._share_dir("symbols") is not None


def test_annotations_surface_pins_and_extends(capsys):
    mod = _load_tool()
    if not _has_kicad_symbols(mod):
        pytest.skip("no KiCad symbol library available")

    mod.find_symbols("ADA4807-2", limit=50)
    out = capsys.readouterr().out
    lines = {
        ln.split()[0]: ln
        for ln in out.splitlines()
        if ln.startswith("Amplifier_Operational:ADA4807-2")
    }

    arm = lines.get("Amplifier_Operational:ADA4807-2ARM")
    acp = lines.get("Amplifier_Operational:ADA4807-2ACP")
    assert arm and acp, f"expected both ADA4807-2 variants in:\n{out}"

    # The derived part shows its parent AND the inherited (8-pin) count.
    assert "extends LM2904" in arm, arm
    assert "8 pins" in arm, arm
    # The non-derived part shows a pin count and no extends note.
    assert "pins]" in acp and "extends" not in acp, acp


def test_pin_count_helper_follows_extends():
    mod = _load_tool()
    blocks = {
        "Child": '(extends "Parent")',
        "Parent": '(pin (number "1"))(pin (number "2"))(pin (number "3"))',
    }
    # Child inherits Parent's 3 pins; the annotation names the parent.
    assert mod._pin_count("Child", blocks) == 3
    assert mod._pin_annotation("Child", blocks) == "  [3 pins, extends Parent]"
    assert mod._pin_annotation("Parent", blocks) == "  [3 pins]"


def test_pin_count_helper_survives_missing_parent():
    mod = _load_tool()
    blocks = {"Orphan": '(extends "Gone")'}
    # No parent to resolve -> just the extends note, no crash.
    assert mod._pin_count("Orphan", blocks) is None
    assert mod._pin_annotation("Orphan", blocks) == "  [extends Gone]"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
