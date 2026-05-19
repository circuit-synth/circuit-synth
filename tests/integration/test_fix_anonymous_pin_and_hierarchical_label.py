#!/usr/bin/env python3
"""
Tests for two bugs in schematic generation for circuits with anonymous-pin
components (Device:C, Device:FerriteBead, etc.) and flat single-sheet designs.

Bug 1 — circuit_loader.py line 286: anonymous-pin stacking
  Empty-string pin names (`""`) passed the `!= "~"` guard, so pin_identifier
  was set to `""` for every pin of Device:C / Device:FerriteBead / etc.
  find_pin_by_identifier("") always resolved to pin 1, putting every power
  symbol at pin 1's coordinates regardless of which pin was actually connected.

  Fix: added `and pin_data["name"]` so empty strings fall through to the
  pin-number branch.

Bug 2 — schematic_writer.py _is_net_hierarchical(): always returned True
  The method was a stub that unconditionally returned True, causing every
  non-power net to be emitted as a (hierarchical_label) even on a flat
  single-sheet design. Hierarchical labels do not self-connect by name within
  a sheet, so shared signal nets are silently split into isolated stubs.

  Fix: uncommented and cleaned up the existing TODO logic that inspects
  parent/child circuit membership, returning False for purely internal nets.
"""

import re
import os
import tempfile
from pathlib import Path

import pytest

# These tests require the KiCad symbol library to resolve Device:C etc.
# Skip gracefully if KICAD_SYMBOL_DIR is not set.
pytestmark = pytest.mark.skipif(
    not os.environ.get("KICAD_SYMBOL_DIR"),
    reason="KICAD_SYMBOL_DIR not set — KiCad symbol library required",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _generate_sch(circuit_fn, tmp_path: Path) -> str:
    """Run circuit_fn(), generate a KiCad project in tmp_path, return .kicad_sch text."""
    circ = circuit_fn()
    result = circ.generate_kicad_project(
        project_name=str(tmp_path),
        generate_pcb=False,
        force_regenerate=True,
        update_source_refs=False,
    )
    assert result["success"], f"generate_kicad_project failed: {result.get('error')}"
    sch_files = list(tmp_path.glob("*.kicad_sch"))
    assert sch_files, "No .kicad_sch file generated"
    return sch_files[0].read_text()


def _power_symbol_positions(sch_text: str) -> list[tuple[str, float, float]]:
    """
    Return [(net_value, x, y), ...] for every power symbol instance in the schematic.
    """
    # Each symbol block: (symbol\n  (lib_id "power:X")\n  (at X Y ...)\n  ... Value "V" ...)
    blocks = re.findall(r"\(symbol\s*\n.*?\n\t\)", sch_text, re.DOTALL)
    result = []
    for block in blocks:
        lib_m = re.search(r'\(lib_id "power:([^"]+)"', block)
        at_m  = re.search(r'\(at ([\d.\-]+) ([\d.\-]+)', block)
        val_m = re.search(r'"Value" "([^"]+)"', block)
        if lib_m and at_m and val_m:
            result.append((val_m.group(1), float(at_m.group(1)), float(at_m.group(2))))
    return result


def _hierarchical_labels(sch_text: str) -> list[str]:
    """Return all hierarchical_label text values in the schematic."""
    return re.findall(r'\(hierarchical_label "([^"]+)"', sch_text)


def _local_labels(sch_text: str) -> list[str]:
    """Return all local label text values in the schematic."""
    # KiCad local labels: (label "NAME" ...)
    return re.findall(r'(?<!\(hierarchical_)\(label "([^"]+)"', sch_text)


# ---------------------------------------------------------------------------
# Bug 1: anonymous-pin power symbol stacking
# ---------------------------------------------------------------------------

class TestAnonymousPinIdentifier:
    """
    Bug 1 — power symbols for Device:C / FerriteBead stacked on pin 1.

    Device:C has two anonymous pins (name=""). Before the fix, both pins
    resolved to pin 1's coordinates, so GND and +5V (or any two nets on the
    same component) appeared at the same schematic position.
    """

    def test_capacitor_power_symbols_at_distinct_pins(self, tmp_path):
        """
        A capacitor with +5V on pin 1 and GND on pin 2 must place their power
        symbols at distinct y-coordinates (separated by 2 × pin_length ≈ 7.62 mm).
        """
        from circuit_synth import Component, Net, circuit

        @circuit(name="cap_test")
        def cap_test():
            pwr = Net("+5V")
            gnd = Net("GND")
            c = Component(
                symbol="Device:C",
                ref="C1",
                value="100nF",
                footprint="Capacitor_SMD:C_0402_1005Metric",
            )
            c[1] += pwr
            c[2] += gnd

        sch = _generate_sch(cap_test, tmp_path)
        positions = _power_symbol_positions(sch)

        # Collect y-coords for each net at the capacitor's x-column
        by_net: dict[str, list[float]] = {}
        for net, x, y in positions:
            by_net.setdefault(net, []).append(y)

        assert "+5V" in by_net, "No +5V power symbol found in schematic"
        assert "GND" in by_net, "No GND power symbol found in schematic"

        vcc_ys = by_net["+5V"]
        gnd_ys = by_net["GND"]

        # The two symbols must NOT share the same y-coordinate
        # (allow 0.01 mm tolerance for floating-point rounding)
        for vy in vcc_ys:
            for gy in gnd_ys:
                assert abs(vy - gy) > 0.01, (
                    f"Bug 1 regression: +5V (y={vy:.3f}) and GND (y={gy:.3f}) "
                    f"are at the same position — both landed on pin 1."
                )

        # The separation must be approximately 2 × 3.81 = 7.62 mm
        # (the pin length defined in Device:C)
        min_vcc_y = min(vcc_ys)
        max_gnd_y = max(gnd_ys)
        separation = abs(max_gnd_y - min_vcc_y)
        assert separation > 5.0, (
            f"Pin separation {separation:.2f} mm is too small — "
            f"expected ~7.62 mm between pin 1 (+5V) and pin 2 (GND)."
        )

    def test_ferrite_bead_power_symbols_at_distinct_pins(self, tmp_path):
        """
        A FerriteBead with two different nets on its pins must place their
        power symbols at distinct y-coordinates.
        """
        from circuit_synth import Component, Net, circuit
        from circuit_synth.core.power_net_registry import PowerNetRegistry

        # Register the non-standard rail so it gets a power symbol, not a
        # hierarchical label (needed to inspect its placement coordinates).
        PowerNetRegistry()._power_symbols["+3V3_RF"] = "power:+3V3"

        @circuit(name="fb_test")
        def fb_test():
            rail  = Net("+3V3")
            rail_rf = Net("+3V3_RF")
            fb = Component(
                symbol="Device:FerriteBead",
                ref="FB1",
                value="600R@100MHz",
                footprint="Inductor_SMD:L_0805_2012Metric",
            )
            fb[1] += rail
            fb[2] += rail_rf

        sch = _generate_sch(fb_test, tmp_path)
        positions = _power_symbol_positions(sch)

        by_net: dict[str, list[float]] = {}
        for net, x, y in positions:
            by_net.setdefault(net, []).append(y)

        assert "+3V3" in by_net,    "No +3V3 power symbol found"
        assert "+3V3_RF" in by_net, "No +3V3_RF power symbol found"

        for v1 in by_net["+3V3"]:
            for v2 in by_net["+3V3_RF"]:
                assert abs(v1 - v2) > 0.01, (
                    f"Bug 1 regression: +3V3 (y={v1:.3f}) and +3V3_RF (y={v2:.3f}) "
                    f"are at the same position on FB1."
                )

    def test_polarized_capacitor_power_symbols_at_distinct_pins(self, tmp_path):
        """Device:C_Polarized has the same anonymous-pin structure as Device:C."""
        from circuit_synth import Component, Net, circuit
        from circuit_synth.core.power_net_registry import PowerNetRegistry

        PowerNetRegistry()._power_symbols["+3V3_RF"] = "power:+3V3"

        @circuit(name="cpol_test")
        def cpol_test():
            rf  = Net("+3V3_RF")
            gnd = Net("GND")
            c = Component(
                symbol="Device:C_Polarized",
                ref="C1",
                value="47uF",
                footprint="Capacitor_SMD:CP_Elec_5x5.3",
            )
            c[1] += rf   # + terminal
            c[2] += gnd  # – terminal

        sch = _generate_sch(cpol_test, tmp_path)
        positions = _power_symbol_positions(sch)

        by_net: dict[str, list[float]] = {}
        for net, x, y in positions:
            by_net.setdefault(net, []).append(y)

        assert "+3V3_RF" in by_net, "No +3V3_RF power symbol found"
        assert "GND"     in by_net, "No GND power symbol found"

        for v1 in by_net["+3V3_RF"]:
            for v2 in by_net["GND"]:
                assert abs(v1 - v2) > 0.01, (
                    f"Bug 1 regression: +3V3_RF and GND at same y on C_Polarized."
                )


# ---------------------------------------------------------------------------
# Bug 2: _is_net_hierarchical() always returned True
# ---------------------------------------------------------------------------

class TestHierarchicalLabelLogic:
    """
    Bug 2 — every non-power net emitted as hierarchical_label.

    In a flat single-sheet design, hierarchical labels do NOT self-connect by
    name (unlike local labels). A net shared between two components on the same
    flat sheet must use a local label so KiCad renders the connection.

    After the fix, _is_net_hierarchical() returns True only for nets that
    genuinely cross a sheet boundary (i.e. shared with a parent or child
    subcircuit). Purely internal flat-sheet nets get local labels.
    """

    def test_internal_net_gets_local_label_not_hierarchical(self, tmp_path):
        """
        A signal net shared between two resistors on a flat sheet must appear
        as a (label ...) not a (hierarchical_label ...) in the .kicad_sch.
        """
        from circuit_synth import Component, Net, circuit

        @circuit(name="flat_test")
        def flat_test():
            vin  = Net("+5V")
            mid  = Net("MID_SIGNAL")   # internal net — no parent/child crossing
            gnd  = Net("GND")
            r1 = Component("Device:R", ref="R1", value="1k",
                           footprint="Resistor_SMD:R_0402_1005Metric")
            r2 = Component("Device:R", ref="R2", value="2k",
                           footprint="Resistor_SMD:R_0402_1005Metric")
            r1[1] += vin
            r1[2] += mid
            r2[1] += mid
            r2[2] += gnd

        sch = _generate_sch(flat_test, tmp_path)

        hier_labels = _hierarchical_labels(sch)
        local_labels = _local_labels(sch)

        assert "MID_SIGNAL" not in hier_labels, (
            "Bug 2 regression: MID_SIGNAL emitted as hierarchical_label. "
            "Internal flat-sheet nets must use local labels."
        )
        assert "MID_SIGNAL" in local_labels, (
            "MID_SIGNAL not found as a local label — internal nets must use "
            "(label ...) so KiCad connects them by name within the sheet."
        )

    def test_subcircuit_shared_net_gets_hierarchical_label(self, tmp_path):
        """
        A net passed into a @circuit subcircuit genuinely crosses a sheet
        boundary and must remain a hierarchical_label on the child sheet.
        """
        from circuit_synth import Component, Net, circuit

        @circuit(name="child_block")
        def child_block(shared_net):
            r = Component("Device:R", ref="R", value="100",
                          footprint="Resistor_SMD:R_0402_1005Metric")
            gnd = Net("GND")
            r[1] += shared_net
            r[2] += gnd

        @circuit(name="parent_flat")
        def parent_flat():
            bus = Net("SHARED_BUS")   # crosses into child_block
            pwr = Net("+5V")
            r_top = Component("Device:R", ref="R", value="1k",
                               footprint="Resistor_SMD:R_0402_1005Metric")
            r_top[1] += pwr
            r_top[2] += bus
            child_block(bus)

        sch = _generate_sch(parent_flat, tmp_path)
        hier_labels = _hierarchical_labels(sch)

        # SHARED_BUS must appear as a hierarchical label because it connects
        # the parent sheet to the child sheet.
        assert "SHARED_BUS" in hier_labels, (
            "SHARED_BUS should be a hierarchical_label because it is shared "
            "with a child subcircuit (crosses a sheet boundary)."
        )
