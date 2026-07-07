"""Unit tests for selective-wiring eligibility (Stage 14, Part B).

Pure Python: exercises the ``_eligible_nets`` rule against a fake schematic (no
kicad-cli, no kicad-sch-api). The draw + netlist-equivalence safety net is covered
by the kicad-cli e2e in ``tests/e2e/test_selective_wiring.py``.
"""

from collections import namedtuple

import pytest

from circuit_synth.kicad.sch_gen.selective_wiring import (
    DEFAULT_MAX_WIRE_DIST_MM,
    _eligible_nets,
    wire_local_nets,
)

pytestmark = pytest.mark.unit

Pt = namedtuple("Pt", "x y")


class _FakeSch:
    """Minimal stand-in exposing get_component_pin_position(ref, pin)."""

    def __init__(self, positions):
        # positions: {(ref, pin): Pt or None}
        self._pos = positions

    def get_component_pin_position(self, ref, pin):
        return self._pos.get((ref, pin))


def test_two_pin_short_signal_net_is_eligible():
    positions = {("R1", "2"): Pt(0, 0), ("R2", "1"): Pt(0, 10)}
    sch = _FakeSch(positions)
    named = {"VOUT": {("R1", "2"), ("R2", "1")}}
    out = _eligible_nets(sch, named, DEFAULT_MAX_WIRE_DIST_MM)
    assert out == [("R1", "2", "R2", "1")]


def test_power_net_excluded_by_name():
    sch = _FakeSch({("R2", "2"): Pt(0, 0), ("C1", "2"): Pt(0, 5)})
    named = {"GND": {("R2", "2"), ("C1", "2")}}
    assert _eligible_nets(sch, named, DEFAULT_MAX_WIRE_DIST_MM) == []


def test_net_with_power_symbol_pin_excluded():
    # A power net carries a #PWR pseudo-symbol pin -> never wired.
    sch = _FakeSch({("R2", "2"): Pt(0, 0), ("#PWR01", "1"): Pt(0, 5)})
    named = {"N$3": {("R2", "2"), ("#PWR01", "1")}}
    assert _eligible_nets(sch, named, DEFAULT_MAX_WIRE_DIST_MM) == []


def test_three_pin_net_excluded():
    sch = _FakeSch(
        {("Q1", "2"): Pt(0, 0), ("R1", "2"): Pt(0, 5), ("C1", "2"): Pt(0, 8)}
    )
    named = {"BASE": {("Q1", "2"), ("R1", "2"), ("C1", "2")}}
    assert _eligible_nets(sch, named, DEFAULT_MAX_WIRE_DIST_MM) == []


def test_long_net_excluded():
    sch = _FakeSch({("R1", "1"): Pt(0, 0), ("Q1", "1"): Pt(0, 200)})
    named = {"EMIT": {("R1", "1"), ("Q1", "1")}}
    # 200 mm manhattan >> 50.8 mm default threshold
    assert _eligible_nets(sch, named, DEFAULT_MAX_WIRE_DIST_MM) == []


def test_cross_sheet_net_excluded_when_pin_unresolved():
    # A pin on another sheet resolves to None on this sheet's schematic.
    sch = _FakeSch({("R1", "2"): Pt(0, 0), ("U2", "5"): None})
    named = {"V5": {("R1", "2"), ("U2", "5")}}
    assert _eligible_nets(sch, named, DEFAULT_MAX_WIRE_DIST_MM) == []


def test_coincident_pins_excluded():
    # Two pins at the SAME point (e.g. a multi-pad sensor's redundant/stacked pads
    # sharing a net, like the SiPM's TSV pins) must NOT be wired: a zero-length wire
    # crashes KiCad on save. dist == 0 -> skip.
    sch = _FakeSch({("D1", "C6"): Pt(73.66, 35.56), ("D1", "D6"): Pt(73.66, 35.56)})
    named = {"FAST": {("D1", "C6"), ("D1", "D6")}}
    assert _eligible_nets(sch, named, DEFAULT_MAX_WIRE_DIST_MM) == []


def test_threshold_boundary_inclusive():
    sch = _FakeSch(
        {("R1", "2"): Pt(0, 0), ("R2", "1"): Pt(0, DEFAULT_MAX_WIRE_DIST_MM)}
    )
    named = {"MID": {("R1", "2"), ("R2", "1")}}
    assert len(_eligible_nets(sch, named, DEFAULT_MAX_WIRE_DIST_MM)) == 1


def test_result_always_carries_wires_in_file_key(tmp_path):
    # Even on the early "schematic not found" return, the self-verifying
    # wires_in_file key is present (stage 17.5) so callers/logs can rely on it.
    result = wire_local_nets(str(tmp_path / "does_not_exist.kicad_sch"))
    assert result["reason"] == "schematic not found"
    assert result["wires_in_file"] == 0
