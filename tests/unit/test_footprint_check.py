"""Unit tests for the Stage 22.9 footprint-existence check.

``check_footprints`` warns (never fails) when a component's ``Lib:Name`` footprint
id is absent from the installed KiCad footprint libraries. These tests drive it
against a fake footprint tree so they need no KiCad install, and cover the four
outcomes: valid id (silent), bad id in an existing lib (warn), missing lib (warn),
non-``Lib:Name`` id (skip), and no footprint root at all (silent).
"""

import logging
from types import SimpleNamespace

import pytest

from circuit_synth.kicad.sch_gen.footprint_check import check_footprints

pytestmark = pytest.mark.unit


def _comp(ref, footprint):
    return SimpleNamespace(reference=ref, footprint=footprint)


@pytest.fixture
def fake_root(tmp_path):
    """A footprint root with Resistor_SMD.pretty/R_0603_1608Metric.kicad_mod."""
    lib = tmp_path / "footprints" / "Resistor_SMD.pretty"
    lib.mkdir(parents=True)
    (lib / "R_0603_1608Metric.kicad_mod").write_text("(module)", encoding="utf-8")
    (lib / "R_0805_2012Metric.kicad_mod").write_text("(module)", encoding="utf-8")
    return tmp_path / "footprints"


def _warnings(caplog):
    return [r for r in caplog.records if r.levelno == logging.WARNING]


def test_valid_footprint_no_warning(fake_root, caplog):
    with caplog.at_level(logging.WARNING):
        n = check_footprints([_comp("R1", "Resistor_SMD:R_0603_1608Metric")],
                             roots=[fake_root])
    assert n == 0
    assert _warnings(caplog) == []


def test_missing_footprint_in_existing_lib_warns(fake_root, caplog):
    with caplog.at_level(logging.WARNING):
        n = check_footprints([_comp("R1", "Resistor_SMD:R_9999_NoSuchMetric")],
                             roots=[fake_root])
    assert n == 1
    msgs = "\n".join(r.getMessage() for r in _warnings(caplog))
    assert "R1" in msgs and "R_9999_NoSuchMetric" in msgs
    assert "footprint_link_issues" in msgs


def test_missing_library_warns(fake_root, caplog):
    with caplog.at_level(logging.WARNING):
        n = check_footprints([_comp("U1", "Package_QFN:QFN-20_NoSuchLib")],
                             roots=[fake_root])
    assert n == 1
    assert "QFN-20_NoSuchLib" in "\n".join(r.getMessage() for r in _warnings(caplog))


def test_non_libname_footprint_skipped(fake_root, caplog):
    with caplog.at_level(logging.WARNING):
        n = check_footprints(
            [_comp("R1", ""), _comp("R2", None), _comp("R3", "bareword")],
            roots=[fake_root],
        )
    assert n == 0
    assert _warnings(caplog) == []


def test_no_root_is_silent(caplog):
    with caplog.at_level(logging.WARNING):
        n = check_footprints([_comp("R1", "Resistor_SMD:R_9999_NoSuchMetric")],
                             roots=[])
    assert n == 0
    assert _warnings(caplog) == []


def test_default_root_none_skips_when_no_kicad(monkeypatch, caplog):
    """roots=None with no discoverable KiCad footprint root => silent skip."""
    monkeypatch.setattr(
        "circuit_synth.kicad.sch_gen.footprint_check._footprint_root_dirs",
        lambda: [],
    )
    with caplog.at_level(logging.WARNING):
        n = check_footprints([_comp("R1", "Resistor_SMD:R_9999_NoSuchMetric")])
    assert n == 0
    assert _warnings(caplog) == []


def test_per_lib_scan_is_cached(fake_root, monkeypatch):
    """A multi-part design scans each distinct library once, not once per part."""
    import circuit_synth.kicad.sch_gen.footprint_check as fc

    calls = {"n": 0}
    real = fc._lib_footprints

    def counting(lib, roots, cache):
        if lib not in cache:
            calls["n"] += 1
        return real(lib, roots, cache)

    monkeypatch.setattr(fc, "_lib_footprints", counting)
    comps = [_comp(f"R{i}", "Resistor_SMD:R_0603_1608Metric") for i in range(30)]
    n = check_footprints(comps, roots=[fake_root])
    assert n == 0
    # 30 parts, one distinct library => a single cache-miss scan.
    assert calls["n"] == 1
