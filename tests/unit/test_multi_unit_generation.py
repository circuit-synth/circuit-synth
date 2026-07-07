#!/usr/bin/env python3
"""Unit tests for multi-unit (dual/quad) symbol generation.

Regression for bug #B (E2E run 4): a multi-unit symbol (LM358, ADA4807-2ACP, ...)
is placed as several unit bodies, each carrying its own ``(instances ...)`` block.
The schematic writer applied the rooted instance path to only ONE unit; the rest
kept kicad-sch-api's default ``(path "/")`` -- a dangling hierarchy reference that
null-derefs KiCad's writer on SAVE (segfault + 0-byte file), the same failure
class as the 2026-07-05 power-symbol crash. These tests assert every placed unit
gets ``/<root-uuid>``.
"""

import re
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from circuit_synth import Component, Net, circuit


def _lm358_divider():
    """LM358 (3 units: A=1,2,3  B=5,6,7  power=4,8) as a unity follower + R."""

    @circuit(name="mu_lm358")
    def _c():
        u1 = Component(symbol="Amplifier_Operational:LM358", ref="U1")
        r1 = Component(
            symbol="Device:R",
            ref="R1",
            value="1k",
            footprint="Resistor_SMD:R_0603_1608Metric",
        )
        n1, gnd, vcc = Net("N1"), Net("GND"), Net("VCC")
        u1[1] += n1  # OUTA
        u1[2] += n1  # -INA  (follower)
        u1[3] += gnd  # +INA
        u1[4] += gnd  # V-
        u1[8] += vcc  # V+
        r1[1] += n1
        r1[2] += gnd

    return _c()


def _generate_content(circ, name: str) -> str:
    with TemporaryDirectory() as tmpdir:
        circ.generate_kicad_project(
            project_name=f"{tmpdir}/{name}",
            generate_pcb=False,
            erc_gate=False,
            selective_wires=False,
        )
        sch = next(Path(tmpdir).rglob(f"{name}.kicad_sch"))
        return sch.read_text()


def _root_uuid(content: str) -> str:
    return re.search(
        r'\(uuid "([0-9a-f-]+)"\)', content[: content.index("(lib_symbols")]
    ).group(1)


def _instances(content: str):
    """Return [(ref, unit, path), ...] for every component instance."""
    return [
        (ref, int(unit), path)
        for (path, ref, unit) in re.findall(
            r'\(path "([^"]+)"\s*\(reference "([^"]+)"\)\s*\(unit (\d+)\)', content
        )
    ]


def test_multi_unit_instance_paths_include_root_uuid():
    """Every placed unit of a multi-unit symbol must use /<root-uuid>, not a
    dangling "/". A bare "/" crashes KiCad's writer on save."""
    content = _generate_content(_lm358_divider(), "mu_lm358")
    root = _root_uuid(content)

    u1 = [(u, p) for (ref, u, p) in _instances(content) if ref == "U1"]
    assert u1, "expected LM358 unit instances for U1"

    # LM358 has three units (two amps + one power) -- all three must be placed.
    assert sorted(u for (u, _) in u1) == [
        1,
        2,
        3,
    ], f"expected U1 instances for units 1,2,3, got {sorted(u for (u, _) in u1)}"
    for unit, path in u1:
        assert path == f"/{root}", (
            f"U1 unit {unit} has dangling instance path {path!r}; expected "
            f"/{root} (a bare '/' crashes KiCad on save)"
        )


def test_multi_unit_per_unit_pin_lists_match_kicad():
    """Each placed unit block lists ALL of the symbol's pins.

    NOTE: run-4's plan called an all-pins-per-unit list "defect 2", assuming
    KiCad emits only that unit's pins. Ground truth disproves this: a real
    ``eeschema``-authored TL072 reference (kicad-sch-api
    ``tests/reference_kicad_projects/multi_unit_tl072/test.kicad_sch``) lists all
    8 pins in every placed unit block, and kicad-sch-api's own reference test
    (``test_reference_pin_numbers_per_unit``) pins that as the KiCad format. So
    the current behavior is CORRECT; this test locks it in rather than "fixing"
    it (which would break kicad-sch-api's exact-format-preservation contract).
    """
    content = _generate_content(_lm358_divider(), "mu_lm358")
    # Isolate the three placed LM358 unit blocks (lib_id at instance level).
    blocks = re.split(r'\(lib_id "Amplifier_Operational:LM358"\)', content)[1:]
    assert len(blocks) == 3, f"expected 3 placed LM358 unit blocks, got {len(blocks)}"
    for i, block in enumerate(blocks, 1):
        # Stop at the instances section -- only count the placed-symbol pin uuids.
        head = block.split("(instances", 1)[0]
        pins = set(re.findall(r'\(pin "(\d+)"', head))
        assert pins == {
            "1",
            "2",
            "3",
            "4",
            "5",
            "6",
            "7",
            "8",
        }, f"LM358 placed unit {i} pin list {sorted(pins)} != all 8 (KiCad format)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
