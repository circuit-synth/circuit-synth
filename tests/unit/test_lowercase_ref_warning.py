"""Lowercase-prefix reference warning (Stage 17.3, G1, circuit-synth side).

KiCad and the kicad-sch-api fork accept refs like "Rf1", but PyPI
kicad-sch-api <=0.5.5 (what bootstrapped projects install) rejects them on save.
circuit-synth must not hard-fail on them -- it only warns so the round-trip risk
is visible until the fork's fix is released.
"""

import logging

import pytest

from circuit_synth import Component, Net, circuit

pytestmark = pytest.mark.unit

R_FP = "Resistor_SMD:R_0603_1608Metric"


def _messages(caplog):
    return "\n".join(r.getMessage() for r in caplog.records)


def test_lowercase_prefix_ref_warns(caplog):
    @circuit(name="LowerRef")
    def _c():
        with caplog.at_level(logging.WARNING, logger="circuit_synth"):
            Component(symbol="Device:R", ref="Rf1", value="100k", footprint=R_FP)

    _c()
    msgs = _messages(caplog)
    assert "Rf1" in msgs
    assert "lowercase prefix" in msgs
    assert "RF1" in msgs  # suggested uppercase form


def test_uppercase_prefix_ref_does_not_warn(caplog):
    @circuit(name="UpperRef")
    def _c():
        with caplog.at_level(logging.WARNING, logger="circuit_synth"):
            Component(symbol="Device:R", ref="R1", value="100k", footprint=R_FP)

    _c()
    assert "lowercase prefix" not in _messages(caplog)


def test_power_flag_ref_does_not_warn(caplog):
    # "#PWR01" / "#FLG01" have an all-uppercase alphabetic prefix -> no warning.
    @circuit(name="PwrRef")
    def _c():
        with caplog.at_level(logging.WARNING, logger="circuit_synth"):
            Component(symbol="Device:R", ref="R1", value="1k", footprint=R_FP)

    _c()
    assert "lowercase prefix" not in _messages(caplog)
