"""Flattening subcircuit hierarchy for SPICE (Stage 10.6).

The converter iterates only the top-level circuit, so a hierarchical design
(components living in subcircuits) must be flattened before conversion. These
tests prove:
- a block placed in a subcircuit simulates identically to the same block inline,
- every subcircuit's components survive flattening (none merged/dropped) and
  keep globally-unique refs,
- Sim.Enable="0" on a part *inside* a subcircuit is still honored.

Netlist-level tests need PySpice + a loadable ngspice; they skip cleanly if
absent. The flatten mechanism itself is exercised through convert().
"""

import pytest

from circuit_synth import Component, Net, circuit


def _ngspice_available() -> bool:
    try:
        from circuit_synth.simulation.simulator import PYSPICE_AVAILABLE

        if not PYSPICE_AVAILABLE:
            return False
        Component(symbol="Simulation_SPICE:VDC", ref="V", value="5")
        from PySpice.Spice.NgSpice.Shared import NgSpiceShared

        NgSpiceShared.new_instance()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _ngspice_available(),
    reason="PySpice or a loadable ngspice is not available",
)


# --- topologies --------------------------------------------------------------


@circuit(name="divider_block")
def _divider_block(vin, vout, gnd):
    r1 = Component(symbol="Device:R", ref="R", value="1k")
    r2 = Component(symbol="Device:R", ref="R", value="2k")
    r1[1] += vin
    r1[2] += vout
    r2[1] += vout
    r2[2] += gnd


@circuit(name="hier_divider")
def _hier_divider():
    """5 V source at top; the divider lives in a subcircuit."""
    vin, vout, gnd = Net("VIN"), Net("VOUT"), Net("GND")
    v = Component(symbol="Simulation_SPICE:VDC", ref="V", value="5")
    v[1] += vin
    v[2] += gnd
    _divider_block(vin, vout, gnd)


@circuit(name="flat_divider")
def _flat_divider():
    """The same 5 V divider, entirely inline."""
    vin, vout, gnd = Net("VIN"), Net("VOUT"), Net("GND")
    v = Component(symbol="Simulation_SPICE:VDC", ref="V", value="5")
    r1 = Component(symbol="Device:R", ref="R", value="1k")
    r2 = Component(symbol="Device:R", ref="R", value="2k")
    v[1] += vin
    v[2] += gnd
    r1[1] += vin
    r1[2] += vout
    r2[1] += vout
    r2[2] += gnd


@circuit(name="two_dividers")
def _two_dividers():
    """Two divider blocks off one supply -> 4 resistors, globally-unique refs."""
    vin, gnd = Net("VIN"), Net("GND")
    outa, outb = Net("OUTA"), Net("OUTB")
    v = Component(symbol="Simulation_SPICE:VDC", ref="V", value="6")
    v[1] += vin
    v[2] += gnd
    _divider_block(vin, outa, gnd)
    _divider_block(vin, outb, gnd)


@circuit(name="block_with_disabled")
def _block_with_disabled(vin, vout, gnd):
    r1 = Component(symbol="Device:R", ref="R", value="1k")
    r2 = Component(symbol="Device:R", ref="R", value="2k")
    # A decorative test-point resistor excluded from simulation.
    rtp = Component(symbol="Device:R", ref="R", value="1meg", **{"Sim.Enable": "0"})
    r1[1] += vin
    r1[2] += vout
    r2[1] += vout
    r2[2] += gnd
    rtp[1] += vout
    rtp[2] += gnd


@circuit(name="hier_disabled")
def _hier_disabled():
    vin, vout, gnd = Net("VIN"), Net("VOUT"), Net("GND")
    v = Component(symbol="Simulation_SPICE:VDC", ref="V", value="5")
    v[1] += vin
    v[2] += gnd
    _block_with_disabled(vin, vout, gnd)


# --- tests -------------------------------------------------------------------


def test_hierarchical_matches_flat():
    """A divider in a subcircuit gives the same node voltage as inline."""
    h = _hier_divider().simulate().operating_point()
    f = _flat_divider().simulate().operating_point()
    assert h.get_voltage("VOUT") == pytest.approx(f.get_voltage("VOUT"), abs=1e-4)
    assert h.get_voltage("VOUT") == pytest.approx(10.0 / 3.0, abs=1e-3)


def test_all_subcircuit_components_present():
    """Both blocks' resistors survive flattening with unique refs; both work."""
    sim = _two_dividers().simulate()
    elements = sorted(str(e.name) for e in sim.spice_circuit.elements)
    # PySpice prefixes: 4 resistors (RR1..RR4) + 1 source (VV1).
    resistors = [e for e in elements if e.startswith("RR")]
    assert len(resistors) == 4, elements
    assert len(set(resistors)) == 4  # all distinct -> none merged
    res = sim.operating_point()
    # 6 V * 2k/(1k+2k) = 4.0 V on each independent divider.
    assert res.get_voltage("OUTA") == pytest.approx(4.0, abs=1e-3)
    assert res.get_voltage("OUTB") == pytest.approx(4.0, abs=1e-3)


def test_sim_enable_zero_inside_subcircuit_honored():
    """A Sim.Enable=0 part inside a subcircuit is excluded from the netlist."""
    sim = _hier_disabled().simulate()
    resistors = [
        e
        for e in (str(x.name) for x in sim.spice_circuit.elements)
        if e.startswith("RR")
    ]
    # Only the two divider resistors; the disabled test-point resistor is gone.
    assert len(resistors) == 2, resistors
    # And it did not perturb the divider output.
    assert sim.operating_point().get_voltage("VOUT") == pytest.approx(
        10.0 / 3.0, abs=1e-3
    )
