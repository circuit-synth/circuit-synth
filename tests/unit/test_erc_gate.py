"""Unit tests for the ERC gate parser + classifier (Stage 14, Part A).

Pure Python: they exercise KiCad-10 ERC JSON parsing, reference extraction, and
classification without running kicad-cli. The autofix + full loop are covered by
the kicad-cli e2e in ``tests/e2e/test_erc_gate_autofix.py``.
"""

import os
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

import circuit_synth.kicad.sch_gen.erc_gate as erc_gate_mod

from circuit_synth import Component, Net, circuit
from circuit_synth.kicad.sch_gen.erc_gate import (
    AUTOFIX_TYPES,
    ErcItem,
    ErcReport,
    ErcViolation,
    _apply_power_flag_autofixes,
    _invert_named_nets,
    _map_sheet_uuids_to_files,
    _next_flag_index,
    _parse_erc_json,
    classify,
)

pytestmark = pytest.mark.unit

# A representative KiCad-10 ERC JSON (violations nested under sheets[].violations,
# each with an items list carrying the "Symbol #REF Pin N ..." description).
_KICAD10_ERC = {
    "coordinate_units": "mm",
    "kicad_version": "10.0.0",
    "sheets": [
        {
            "path": "/",
            "uuid_path": "/",
            "violations": [
                {
                    "type": "power_pin_not_driven",
                    "severity": "error",
                    "description": "Input Power pin not driven by any Output Power pins",
                    "items": [
                        {
                            "description": "Symbol #PWR001 Pin 1 [Power input, Line]",
                            "pos": {"x": 55.88, "y": 39.37},
                            "uuid": "abc",
                        }
                    ],
                },
                {
                    "type": "isolated_pin_label",
                    "severity": "warning",
                    "description": "Label connected to only one pin",
                    "items": [
                        {"description": "Label 'VIN_5V'", "pos": {"x": 1.0, "y": 2.0}}
                    ],
                },
            ],
        }
    ],
}


def test_parse_kicad10_nested_json():
    report = _parse_erc_json(_KICAD10_ERC, "x.kicad_sch")
    assert len(report.violations) == 2
    assert report.error_count == 1
    assert report.warning_count == 1

    power = report.violations[0]
    assert power.type == "power_pin_not_driven"
    assert power.severity == "error"
    assert power.sheet == "/"
    assert power.items[0].x == 55.88 and power.items[0].y == 39.37


def test_item_reference_extraction():
    item = ErcItem(description="Symbol #PWR001 Pin 1 [Power input, Line]")
    assert item.reference == "#PWR001"
    # A non-symbol item (e.g. a label) yields no reference.
    assert ErcItem(description="Label 'VIN_5V'").reference is None


def test_violation_references():
    report = _parse_erc_json(_KICAD10_ERC, "x.kicad_sch")
    assert report.violations[0].references == ["#PWR001"]
    assert report.violations[1].references == []


# --------------------------------------------------------------------------- #
# Sheet-aware autofix (multi-sheet): uuid_path parse + sheet-uuid -> file map.
# --------------------------------------------------------------------------- #


def test_parse_uuid_path_for_child_sheet():
    """A violation in a subsheet carries that sheet's uuid_path (last = sheet sym)."""
    data = {
        "sheets": [
            {
                "path": "/psu/",
                "uuid_path": "/root-uuid/psu-sheet-uuid",
                "violations": [
                    {
                        "type": "power_pin_not_driven",
                        "severity": "error",
                        "description": "Input Power pin not driven",
                        "items": [
                            {"description": "Symbol #PWR001 Pin 1 [Power input, Line]"}
                        ],
                    }
                ],
            }
        ]
    }
    report = _parse_erc_json(data, "root.kicad_sch")
    v = report.violations[0]
    assert v.uuid_path == "/root-uuid/psu-sheet-uuid"
    assert v.sheet == "/psu/"


def test_map_sheet_uuids_to_files(tmp_path):
    """Each (sheet ...) block's uuid maps to its resolved Sheetfile path."""
    root = tmp_path / "root.kicad_sch"
    psu_uuid = "bdf9ae2d-b9a3-4281-9ee7-4e2bdf696442"
    load_uuid = "5613ed67-5960-4683-8924-2c6b97d6945c"
    pin_uuid = "aaaaaaaa-1111-2222-3333-444444444444"
    # KiCad indents sheet contents with two tabs; the block closes at one tab.
    root.write_text(
        "(kicad_sch\n"
        "\t(sheet\n"
        f'\t\t(uuid "{psu_uuid}")\n'
        '\t\t(property "Sheetname" "psu"\n\t\t\t(at 0 0 0)\n\t\t)\n'
        '\t\t(property "Sheetfile" "psu.kicad_sch"\n\t\t\t(at 0 0 0)\n\t\t)\n'
        f'\t\t(pin "V5" bidirectional\n\t\t\t(uuid "{pin_uuid}")\n\t\t)\n'
        "\t)\n"
        "\t(sheet\n"
        f'\t\t(uuid "{load_uuid}")\n'
        '\t\t(property "Sheetname" "load"\n\t\t\t(at 0 0 0)\n\t\t)\n'
        '\t\t(property "Sheetfile" "load.kicad_sch"\n\t\t\t(at 0 0 0)\n\t\t)\n'
        "\t)\n"
        ")\n",
        encoding="utf-8",
    )
    mapping = _map_sheet_uuids_to_files(str(root))
    assert mapping[psu_uuid] == str((tmp_path / "psu.kicad_sch").resolve())
    assert mapping[load_uuid] == str((tmp_path / "load.kicad_sch").resolve())
    # The pin's inner uuid must NOT be picked up as a sheet uuid (first uuid wins).
    assert pin_uuid not in mapping


def test_map_sheet_uuids_flat_has_no_sheets(tmp_path):
    """A flat schematic (no sheet blocks) maps to nothing (autofix falls to root)."""
    root = tmp_path / "flat.kicad_sch"
    root.write_text("(kicad_sch\n\t(symbol\n\t\t(uuid \"x\")\n\t)\n)\n", encoding="utf-8")
    assert _map_sheet_uuids_to_files(str(root)) == {}


# --------------------------------------------------------------------------- #
# Stage 18.1: ERC items expose the flagged pin number; violations expose ref_pins.
# --------------------------------------------------------------------------- #


def test_item_pin_extraction():
    # A real op-amp rail item carries the pin number after "Pin".
    assert (
        ErcItem(description="Symbol U1 Pin 8 [+V_{S}, Power input, Line]").pin == "8"
    )
    assert (
        ErcItem(description="Symbol U1 Pin 8 [+V_{S}, Power input, Line]").reference
        == "U1"
    )
    assert ErcItem(description="Symbol #PWR001 Pin 1 [Power input, Line]").pin == "1"
    # A non-symbol item (e.g. a label) has no pin.
    assert ErcItem(description="Label 'VIN_5V'").pin is None


def test_violation_ref_pins():
    v = ErcViolation(
        type="power_pin_not_driven",
        severity="error",
        description="Input Power pin not driven by any Output Power pins",
        items=[
            ErcItem(description="Symbol U1 Pin 8 [+V_{S}, Power input, Line]"),
            ErcItem(description="Symbol U1 Pin 5 [-V_{S}, Power input, Line]"),
            ErcItem(description="Label 'VIN_5V'"),  # no ref/pin -> excluded
        ],
    )
    assert v.ref_pins == [("U1", "8"), ("U1", "5")]


# --------------------------------------------------------------------------- #
# Stage 18.2: invert a netlist's named_nets to a (ref, pin) -> net map.
# --------------------------------------------------------------------------- #


def test_invert_named_nets():
    named = {
        "GND": {("R1", "2"), ("#PWR01", "1")},
        "V_POS_5V": {("U1", "1"), ("U1", "8")},
    }
    mapping = _invert_named_nets(named)
    assert mapping[("R1", "2")] == "GND"
    assert mapping[("#PWR01", "1")] == "GND"
    assert mapping[("U1", "1")] == "V_POS_5V"
    assert mapping[("U1", "8")] == "V_POS_5V"
    assert len(mapping) == 4


def test_invert_named_nets_empty():
    assert _invert_named_nets({}) == {}


def test_classify_only_power_pin_not_driven_is_autofix():
    report = _parse_erc_json(_KICAD10_ERC, "x.kicad_sch")
    assert classify(report.violations[0]) == "autofix"
    assert classify(report.violations[1]) == "report"
    assert AUTOFIX_TYPES == {"power_pin_not_driven"}


def test_report_summary_mentions_counts_and_types():
    report = _parse_erc_json(_KICAD10_ERC, "x.kicad_sch")
    report.iterations = 2
    report.autofixes_applied = 1
    text = report.summary()
    assert "1 error(s)" in text
    assert "1 warning(s)" in text
    assert "PWR_FLAG autofix" in text
    assert "isolated_pin_label" in text


def test_clean_report_summary():
    report = ErcReport(violations=[], schematic_path="x.kicad_sch")
    assert "Clean" in report.summary()
    assert report.error_count == 0


def test_empty_sheets_parse_to_no_violations():
    report = _parse_erc_json({"sheets": []}, "x.kicad_sch")
    assert report.violations == []
    assert report.error_count == 0


# --------------------------------------------------------------------------- #
# Stage 17.2 (G3): #FLG reference seeding avoids collisions across passes.
# --------------------------------------------------------------------------- #


def test_next_flag_index_empty_starts_at_one():
    assert _next_flag_index(["R1", "C2", "#PWR001"]) == 1


def test_next_flag_index_seeds_past_existing():
    # A schematic already carrying #FLG07 must allocate #FLG08 next, not #FLG01.
    assert _next_flag_index(["R1", "#FLG07", "#PWR001"]) == 8


def test_next_flag_index_uses_max_not_count():
    assert _next_flag_index(["#FLG01", "#FLG02"]) == 3
    # A gap does not reset the counter: max wins.
    assert _next_flag_index(["#FLG01", "#FLG05"]) == 6


def test_next_flag_index_ignores_non_flag_refs():
    # #FLAG.. / #PWR.. are not #FLG references.
    assert _next_flag_index(["#FLAG3", "#PWR12"]) == 1


def test_report_note_appears_in_summary():
    report = ErcReport(violations=[], schematic_path="x.kicad_sch")
    report.note = "autofix aborted on iteration 1: ValidationError: dup"
    assert "autofix aborted" in report.summary()


# --------------------------------------------------------------------------- #
# Stage 17.2 (G3): applying the PWR_FLAG autofix twice must not collide on #FLG.
# Uses kicad-sch-api (a hard dependency) + generation; no kicad-cli needed.
# --------------------------------------------------------------------------- #

R_FP = "Resistor_SMD:R_0603_1608Metric"


@circuit(name="FlgDiv")
def _flg_divider():
    r1 = Component(symbol="Device:R", ref="R1", value="1k", footprint=R_FP)
    r2 = Component(symbol="Device:R", ref="R2", value="2k", footprint=R_FP)
    vin, vout, gnd = Net("VIN_5V"), Net("VOUT_3V3"), Net("GND")
    r1[1] += vin
    r1[2] += vout
    r2[1] += vout
    r2[2] += gnd


def _generate_divider(tmpdir):
    cwd = os.getcwd()
    os.chdir(tmpdir)
    try:
        # erc_gate/selective_wires default to True (Stage-14 flip); this fixture must
        # control its own starting state, so opt out and drive the autofix by hand.
        _flg_divider().generate_kicad_project(
            project_name="flgdiv",
            generate_pcb=False,
            erc_gate=False,
            selective_wires=False,
        )
    finally:
        os.chdir(cwd)
    from pathlib import Path

    return next(Path(tmpdir).rglob("FlgDiv.kicad_sch"))


def _flg_refs_and_positions(sch_path):
    import re

    import kicad_sch_api as ksa

    sch = ksa.load_schematic(str(sch_path))
    refs, positions = [], []
    for c in sch.components:
        if re.match(r"#FLG\d+$", str(c.reference)):
            refs.append(str(c.reference))
            positions.append((round(c.position.x, 2), round(c.position.y, 2)))
    return refs, positions


def _report_for_power_symbols(sch_path):
    import kicad_sch_api as ksa

    sch = ksa.load_schematic(str(sch_path))
    pwr_refs = [
        str(c.reference)
        for c in sch.components
        if str(c.reference).startswith("#PWR")
    ]
    violations = [
        ErcViolation(
            type="power_pin_not_driven",
            severity="error",
            description="Input Power pin not driven by any Output Power pins",
            items=[ErcItem(description=f"Symbol {ref} Pin 1 [Power input, Line]")],
        )
        for ref in pwr_refs
    ]
    return ErcReport(violations=violations, schematic_path=str(sch_path)), pwr_refs


def test_apply_power_flag_autofixes_twice_does_not_collide_or_stack():
    """The G3 bug: a second autofix pass re-emitted #FLG01 and raised.

    Applying the fix twice against the same file must (a) not raise -- seeding past
    existing flags -- and (b) not add a second flag to a net that already carries
    one (the canonical-point guard), so all #FLG refs and positions stay unique and
    the second pass is a no-op. The #PWR nets resolve via the symbol value, so the
    passed map is irrelevant here (power symbols are absent from the netlist).
    """
    with TemporaryDirectory() as tmpdir:
        sch = _generate_divider(tmpdir)
        report, pwr_refs = _report_for_power_symbols(sch)
        assert pwr_refs, "expected the divider's GND power symbol"

        first = _apply_power_flag_autofixes(str(sch), report, {})
        assert first >= 1
        refs_1, pos_1 = _flg_refs_and_positions(sch)
        assert refs_1, "first pass should have added a #FLG"

        # Second pass: the net's canonical flag point is already occupied, so it is
        # skipped rather than stacked (and #FLG refs are seeded past the existing).
        second = _apply_power_flag_autofixes(str(sch), report, {})
        assert second == 0

        refs_2, pos_2 = _flg_refs_and_positions(sch)
        assert len(refs_2) == len(set(refs_2)), f"duplicate #FLG refs: {refs_2}"
        assert len(pos_2) == len(set(pos_2)), f"two flags stacked on a point: {pos_2}"


def test_apply_power_flag_autofix_skips_unconnected_net():
    """A flagged pin whose net is dangling (unconnected-*) must NOT get a flag --
    that would mask a real design error. Returns 0, adds nothing."""
    with TemporaryDirectory() as tmpdir:
        sch = _generate_divider(tmpdir)
        report = ErcReport(
            violations=[
                ErcViolation(
                    type="power_pin_not_driven",
                    severity="error",
                    description="Input Power pin not driven by any Output Power pins",
                    items=[
                        ErcItem(description="Symbol R1 Pin 1 [Power input, Line]")
                    ],
                )
            ],
            schematic_path=str(sch),
        )
        pin_net_map = {("R1", "1"): "unconnected-(R1-Pad1)"}
        added = _apply_power_flag_autofixes(str(sch), report, pin_net_map)
        assert added == 0
        refs, _ = _flg_refs_and_positions(sch)
        assert refs == [], "no PWR_FLAG should be added on a dangling net"


# --------------------------------------------------------------------------- #
# Stage 18.4: the gate reverts an iteration that increases non-autofixable errors.
# Fully monkeypatched -- no kicad-cli, no real ERC.
# --------------------------------------------------------------------------- #


def _autofix_error():
    return ErcViolation(
        type="power_pin_not_driven",
        severity="error",
        description="Input Power pin not driven by any Output Power pins",
        items=[ErcItem(description="Symbol #PWR001 Pin 1 [Power input, Line]")],
    )


def _nonautofix_error():
    return ErcViolation(
        type="pin_to_pin",
        severity="error",
        description="Pins of two nets are directly connected",
        items=[],
    )


def _mk_report(violations):
    return ErcReport(violations=list(violations), schematic_path="x.kicad_sch")


def _patch_gate(monkeypatch, report_sequence):
    """Wire erc_gate() free of kicad-cli: scripted run_erc, no-op map, mutating
    autofix that writes a marker so a revert is observable."""
    reports = iter(report_sequence)
    monkeypatch.setattr(erc_gate_mod, "_find_kicad_cli", lambda *a, **k: "dummy-cli")
    monkeypatch.setattr(erc_gate_mod, "_pin_net_map", lambda *a, **k: {})
    monkeypatch.setattr(erc_gate_mod, "run_erc", lambda *a, **k: next(reports))

    def _fake_apply(path, report, pin_net_map):
        Path(path).write_text("MUTATED", encoding="utf-8")
        return 1

    monkeypatch.setattr(erc_gate_mod, "_apply_power_flag_autofixes", _fake_apply)


def test_erc_gate_reverts_iteration_that_makes_erc_worse(tmp_path, monkeypatch):
    sch = tmp_path / "s.kicad_sch"
    original = "ORIGINAL-CONTENT\n"
    sch.write_text(original, encoding="utf-8")

    # initial: one autofixable error (residual 0). after autofix: a NEW non-autofix
    # error (residual 1 > 0) -> revert. after revert: re-run reflects restored file.
    _patch_gate(
        monkeypatch,
        [
            _mk_report([_autofix_error()]),
            _mk_report([_nonautofix_error()]),
            _mk_report([_nonautofix_error()]),
        ],
    )

    report = erc_gate_mod.erc_gate(str(sch))

    assert sch.read_text(encoding="utf-8") == original  # file rolled back
    assert report.note and "reverted" in report.note
    assert report.autofixes_applied == 0  # the reverted iteration does not count


def test_erc_gate_keeps_iteration_that_improves_erc(tmp_path, monkeypatch):
    sch = tmp_path / "s.kicad_sch"
    sch.write_text("ORIGINAL", encoding="utf-8")

    # initial: one autofixable error. after autofix: clean -> no revert, fix kept.
    _patch_gate(
        monkeypatch,
        [
            _mk_report([_autofix_error()]),
            _mk_report([]),
        ],
    )

    report = erc_gate_mod.erc_gate(str(sch))

    assert report.note is None  # nothing reverted
    assert report.autofixes_applied == 1
    assert sch.read_text(encoding="utf-8") == "MUTATED"  # the fix stayed on disk
