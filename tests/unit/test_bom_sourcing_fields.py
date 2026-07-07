"""Unit tests for BOM sourcing-field auto-detection (Stage 17.4, G5).

``generate_bom`` extends KiCad's default columns with any attached sourcing fields
(MPN/Manufacturer/Distributor/LCSC) so they aren't silently dropped. The detection
logic is pure (no kicad-cli); the SPICE-exclusion + populated-column behaviour is
covered by the kicad-cli e2e in ``tests/e2e/test_bom_sourcing.py``.
"""

import pytest

from circuit_synth import Component, Net, circuit

pytestmark = pytest.mark.unit

R_FP = "Resistor_SMD:R_0603_1608Metric"


def test_detect_no_sourcing_fields_returns_empty():
    @circuit(name="NoSrc")
    def _c():
        r1 = Component(symbol="Device:R", ref="R1", value="1k", footprint=R_FP)
        gnd = Net("GND")
        r1[2] += gnd

    assert _c()._detect_sourcing_fields() == []


def test_detect_mpn_field():
    @circuit(name="Mpn")
    def _c():
        r1 = Component(
            symbol="Device:R",
            ref="R1",
            value="100k",
            footprint=R_FP,
            MPN="RC0603FR-07100KL",
        )
        gnd = Net("GND")
        r1[2] += gnd

    assert _c()._detect_sourcing_fields() == ["MPN"]


def test_detect_multiple_fields_stable_order():
    @circuit(name="MultiSrc")
    def _c():
        # Attach fields out of canonical order; detection must return canonical order.
        r1 = Component(
            symbol="Device:R",
            ref="R1",
            value="100k",
            footprint=R_FP,
            LCSC="C123",
            MPN="RC0603FR-07100KL",
            Manufacturer="Yageo",
        )
        gnd = Net("GND")
        r1[2] += gnd

    assert _c()._detect_sourcing_fields() == ["MPN", "Manufacturer", "LCSC"]
