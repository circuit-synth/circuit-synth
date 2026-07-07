"""Diode terminal resolution by A/K pin name (Stage 22.2, bug #12).

SPICE ``D`` is (anode, cathode), but KiCad ``Device:D*``/``LED`` define pin 1 = K
(cathode), pin 2 = A (anode). The old converter emitted nodes in pin-NUMBER
order and called pin 1 the anode, so a schematically-correct diode simulated
backwards. The fix resolves terminals by pin NAME; these tests pin that the
netlist node order follows the A/K names, not the pin numbers, and that an
unresolvable diode warns and falls back to positional order.
"""

import logging

import pytest

from circuit_synth import Component, Net, circuit
from circuit_synth.simulation.converter import PYSPICE_AVAILABLE, SpiceConverter


needs_pyspice = pytest.mark.skipif(
    not PYSPICE_AVAILABLE, reason="PySpice not available"
)


def _diode_line(netlist: str):
    for ln in netlist.splitlines():
        if ln.strip().lower().startswith("dd1 "):
            return ln.split()
    return None


@needs_pyspice
def test_schematic_correct_diode_anode_first():
    """pin2(A)->NA, pin1(K)->NK  =>  netlist 'DD1 NA NK' (anode first)."""

    @circuit(name="fwd")
    def _c():
        v1 = Component(symbol="Simulation_SPICE:VDC", ref="V1", value="5")
        r1 = Component(symbol="Device:R", ref="R1", value="1k")
        d1 = Component(symbol="Device:D", ref="D1")
        r2 = Component(symbol="Device:R", ref="R2", value="1k")
        na, nk, gnd = Net("NA"), Net("NK"), Net("GND")
        v1[1] += na
        v1[2] += gnd
        r1[1] += na
        r1[2] += nk
        d1[2] += na  # A (anode)
        d1[1] += nk  # K (cathode)
        r2[1] += nk
        r2[2] += gnd

    parts = _diode_line(str(SpiceConverter(_c()).convert()))
    assert parts is not None
    assert parts[1] == "NA" and parts[2] == "NK", parts


@needs_pyspice
def test_reversed_wiring_flips_node_order():
    """Swap which nets carry A and K -> node order flips (follows names)."""

    @circuit(name="rev")
    def _c():
        v1 = Component(symbol="Simulation_SPICE:VDC", ref="V1", value="5")
        r1 = Component(symbol="Device:R", ref="R1", value="1k")
        d1 = Component(symbol="Device:D", ref="D1")
        r2 = Component(symbol="Device:R", ref="R2", value="1k")
        na, nk, gnd = Net("NA"), Net("NK"), Net("GND")
        v1[1] += na
        v1[2] += gnd
        r1[1] += na
        r1[2] += nk
        d1[2] += nk  # A (anode) now on NK
        d1[1] += na  # K (cathode) now on NA
        r2[1] += nk
        r2[2] += gnd

    parts = _diode_line(str(SpiceConverter(_c()).convert()))
    assert parts is not None
    assert parts[1] == "NK" and parts[2] == "NA", parts


@needs_pyspice
def test_unresolvable_pins_warn_and_fall_back(caplog):
    """A diode whose pins aren't named A/K warns and uses positional order."""

    @circuit(name="unnamed")
    def _c():
        v1 = Component(symbol="Simulation_SPICE:VDC", ref="V1", value="5")
        r1 = Component(symbol="Device:R", ref="R1", value="1k")
        d1 = Component(symbol="Device:D", ref="D1")
        r2 = Component(symbol="Device:R", ref="R2", value="1k")
        na, nk, gnd = Net("NA"), Net("NK"), Net("GND")
        v1[1] += na
        v1[2] += gnd
        r1[1] += na
        r1[2] += nk
        d1[2] += na  # A wired to NA
        d1[1] += nk  # K wired to NK
        r2[1] += nk
        r2[2] += gnd
        # Strip the pin names so the resolver can't classify them.
        for pin in d1._pins.values():
            pin.name = "X"

    with caplog.at_level(logging.WARNING, logger="circuit_synth.simulation.converter"):
        parts = _diode_line(str(SpiceConverter(_c()).convert()))
    assert parts is not None
    # Positional fallback: pin-number order [pin1=NK, pin2=NA].
    assert parts[1] == "NK" and parts[2] == "NA", parts
    assert any(
        "not resolvable by A/K name" in r.getMessage() for r in caplog.records
    ), [r.getMessage() for r in caplog.records]
