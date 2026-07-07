"""Rail-name heuristic token anchoring (Stage 22.1, bug #13).

``_heuristic_source_voltage`` used to test rail keywords as *substrings*, so an
intermediate net named ``VINT_RAW`` matched ``"VIN" in upper`` and got a phantom
5 V supply injected -- clamping a 32.5 V boost output to 5 V. The fix matches
whole tokens. These tests pin the preserved/changed classification directly on
the method, plus a converter-level netlist regression that no phantom
``V_supply`` lands on ``VINT_RAW`` (while a legit ``VIN_9V`` still gets one).
"""

import logging

import pytest

from circuit_synth import Component, Net, circuit
from circuit_synth.simulation.converter import PYSPICE_AVAILABLE, SpiceConverter


# --- A trivial circuit just so we can instantiate the converter -------------


@circuit(name="trivial")
def _trivial():
    r1 = Component(symbol="Device:R", ref="R1", value="1k")
    a = Net("A")
    b = Net("B")
    r1[1] += a
    r1[2] += b


def _converter():
    return SpiceConverter(_trivial())


# --- Direct classification tests --------------------------------------------

# (net name, expected voltage-or-None) -- every preserved & changed case from
# the fix spec.
PRESERVED = [
    ("VIN_5V", 5.0),
    ("VIN_9V", 9.0),
    ("VIN", 5.0),
    ("VCC_3V3", 3.3),
    ("VDD_3", 3.0),
    ("+12V", 12.0),
    ("VCC", None),  # bare VCC: no embedded number -> not driven
]

CHANGED = [
    ("VINT_RAW", None),
    ("VINT_FILT", None),
    ("VINTAGE", None),
    ("DVINT", None),
    ("SVINX", None),
]


@pytest.mark.parametrize("name,expected", PRESERVED + CHANGED)
def test_heuristic_source_voltage(name, expected):
    conv = _converter()
    assert conv._heuristic_source_voltage(name) == expected


def test_vsupply_token_still_matches():
    conv = _converter()
    assert conv._heuristic_source_voltage("VSUPPLY") == 5.0
    # substring-only match no longer fires
    assert conv._heuristic_source_voltage("VSUPPLYING") is None


# --- Converter-level netlist regression -------------------------------------


needs_pyspice = pytest.mark.skipif(
    not PYSPICE_AVAILABLE, reason="PySpice not available"
)


@circuit(name="vint_tail")
def _vint_tail_circuit():
    """R divider off a VDC with the mid node named VINT_RAW (an intermediate rail).

    VINT_RAW is a real 2-connection node driven only through R1 -- with the old
    substring heuristic it would ALSO get a phantom 5 V supply.
    """
    v1 = Component(symbol="Simulation_SPICE:VDC", ref="V1", value="5")
    r1 = Component(symbol="Device:R", ref="R1", value="1k")
    r2 = Component(symbol="Device:R", ref="R2", value="1k")
    vin = Net("VIN_SRC")
    vint = Net("VINT_RAW")
    gnd = Net("GND")
    v1[1] += vin
    v1[2] += gnd
    r1[1] += vin
    r1[2] += vint
    r2[1] += vint
    r2[2] += gnd


@circuit(name="vin9_tail")
def _vin9_tail_circuit():
    """Same shape but the tail net is VIN_9V (a legit named rail, no source)."""
    r1 = Component(symbol="Device:R", ref="R1", value="1k")
    r2 = Component(symbol="Device:R", ref="R2", value="1k")
    vin9 = Net("VIN_9V")
    mid = Net("MID")
    r1[1] += vin9
    r1[2] += mid
    r2[1] += mid
    r2[2] += Net("GND")


@needs_pyspice
def test_no_phantom_supply_on_vint_raw():
    lines = str(SpiceConverter(_vint_tail_circuit()).convert()).lower().splitlines()
    supplies = [ln for ln in lines if "v_supply" in ln]
    assert not any("vint_raw" in ln for ln in supplies), lines


@needs_pyspice
def test_legit_named_rail_still_gets_supply():
    lines = str(SpiceConverter(_vin9_tail_circuit()).convert()).lower().splitlines()
    supplies = [ln for ln in lines if "v_supply" in ln]
    # a 9 V supply is injected on VIN_9V (the legacy heuristic path still works)
    assert any("vin_9v" in ln and "9.0v" in ln for ln in supplies), lines


@needs_pyspice
def test_injection_logs_info_once(caplog):
    with caplog.at_level(logging.INFO, logger="circuit_synth.simulation.converter"):
        SpiceConverter(_vin9_tail_circuit()).convert()
    injects = [
        r
        for r in caplog.records
        if "injecting heuristic" in r.getMessage() and "VIN_9V" in r.getMessage()
    ]
    assert len(injects) == 1, [r.getMessage() for r in caplog.records]
