"""External vendor models via Sim.Library / Sim.Name / Sim.Pins (Stage 9.3).

A component can attach an external ``.lib``/``.sub`` file: the converter emits a
one-time ``.include`` and either a subcircuit ``X`` instance (nodes ordered by
``Sim.Pins``) or, for a ``.model``-style file, a primitive referencing that model
name. Fixtures under ``tests/fixtures/spice/`` are self-authored (no vendor
licensing): an ideal-op-amp subckt and a custom diode ``.model``.
"""

import os

import pytest

from circuit_synth import Component, Net, circuit

FIXTURES = os.path.join(os.path.dirname(__file__), "..", "fixtures", "spice")
OPAMP_SUB = os.path.abspath(os.path.join(FIXTURES, "ideal_opamp.sub"))
DIODE_LIB = os.path.abspath(os.path.join(FIXTURES, "custom_diode.lib"))


def _symbols_available() -> bool:
    try:
        Component(symbol="Device:R", ref="R1", value="1k")
        return True
    except Exception:
        return False


def _pyspice_available() -> bool:
    try:
        from circuit_synth.simulation.converter import PYSPICE_AVAILABLE

        return PYSPICE_AVAILABLE
    except Exception:
        return False


def _ngspice_loads() -> bool:
    try:
        if not _pyspice_available():
            return False
        from PySpice.Spice.NgSpice.Shared import NgSpiceShared

        NgSpiceShared.new_instance()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _symbols_available(), reason="KiCad symbol libraries not available"
)
needs_pyspice = pytest.mark.skipif(
    not _pyspice_available(), reason="PySpice not available"
)
needs_ngspice = pytest.mark.skipif(
    not _ngspice_loads(), reason="ngspice not loadable"
)


def _converter(c):
    from circuit_synth.simulation.converter import SpiceConverter

    return SpiceConverter(c)


def _validate(c):
    from circuit_synth.simulation.converter import SimulationValidationError

    try:
        _converter(c).validate()
        return None
    except SimulationValidationError as e:
        return e


def _subckt_amp(pins="1=out 2=inp 3=inn", library=OPAMP_SUB, name="IDEALOA"):
    """Non-inverting gain-2 amp built on an ideal-op-amp subckt.

    A BC547 symbol (3 clean pins, no rails) is repurposed as the op-amp carrier so
    Sim.Pins fully specifies the mapping. Pins 1/2/3 -> subckt out/inp/inn.
    """

    @circuit(name="SubcktAmp")
    def cir():
        v1 = Component(symbol="Simulation_SPICE:VDC", ref="V1", value="1V")
        u1 = Component(
            symbol="Transistor_BJT:BC547",
            ref="U1",
            **{"Sim.Library": library, "Sim.Name": name, "Sim.Pins": pins},
        )
        rf = Component(symbol="Device:R", ref="RF", value="10k")
        rg = Component(symbol="Device:R", ref="RG", value="10k")
        vin = Net("IN")
        vout = Net("VOUT")
        fb = Net("FB")
        gnd = Net("GND")
        v1[1] += vin
        v1[2] += gnd
        u1[1] += vout  # out
        u1[2] += vin  # in+
        u1[3] += fb  # in-
        rf[1] += vout
        rf[2] += fb
        rg[1] += fb
        rg[2] += gnd

    return cir()


@needs_pyspice
def test_subckt_include_and_instance():
    """A Sim.Library subckt yields a .include plus an X instance in Sim.Pins order."""
    conv = _converter(_subckt_amp())
    netlist = str(conv.convert())
    assert ".include" in netlist
    assert "ideal_opamp.sub" in netlist.replace("\\", "/").split("/")[-1] or (
        "ideal_opamp.sub" in netlist
    )
    # X instance: nodes ordered out, in+, in- -> VOUT IN FB, then subckt name.
    assert "XU1 VOUT IN FB IDEALOA" in netlist
    assert conv.model_provenance["U1"].tier == "vendor_lib"


@needs_pyspice
def test_external_model_lib_diode():
    """A .model-style Sim.Library yields a primitive referencing the model name."""

    @circuit(name="ExtDiode")
    def cir():
        v1 = Component(symbol="Simulation_SPICE:VDC", ref="V1", value="5V")
        d1 = Component(
            symbol="Device:D",
            ref="D1",
            **{"Sim.Library": DIODE_LIB, "Sim.Name": "CUSTOMD"},
        )
        r1 = Component(symbol="Device:R", ref="R1", value="1k")
        vin = Net("VIN")
        out = Net("OUT")
        gnd = Net("GND")
        v1[1] += vin
        v1[2] += gnd
        d1[2] += vin  # A (anode): keeps DD1 VIN OUT node order, schematic-correct
        d1[1] += out  # K (cathode)
        r1[1] += out
        r1[2] += gnd

    conv = _converter(cir())
    netlist = str(conv.convert())
    assert ".include" in netlist
    assert "DD1 VIN OUT CUSTOMD" in netlist
    # We don't emit our own card for a model living in the external file.
    assert ".model CUSTOMD" not in netlist
    assert conv.model_provenance["D1"].tier == "vendor_lib"


def test_missing_library_file_raises():
    err = _validate(
        _subckt_amp(library=os.path.join(FIXTURES, "does_not_exist.sub"))
    )
    assert err is not None
    assert any("not found" in p for p in err.problems), err.problems


def test_name_not_in_library_raises():
    err = _validate(_subckt_amp(name="NOSUCHSUBCKT"))
    assert err is not None
    assert any("NOSUCHSUBCKT" in p for p in err.problems), err.problems


def test_library_without_name_raises():
    @circuit(name="NoName")
    def cir():
        v1 = Component(symbol="Simulation_SPICE:VDC", ref="V1", value="5V")
        u1 = Component(
            symbol="Transistor_BJT:BC547", ref="U1", **{"Sim.Library": OPAMP_SUB}
        )
        r1 = Component(symbol="Device:R", ref="R1", value="1k")
        a = Net("A")
        b = Net("B")
        gnd = Net("GND")
        v1[1] += a
        v1[2] += gnd
        u1[1] += a
        u1[2] += b
        u1[3] += gnd
        r1[1] += b
        r1[2] += gnd

    err = _validate(cir())
    assert err is not None
    assert any("without Sim.Name" in p for p in err.problems), err.problems


@needs_ngspice
def test_subckt_amp_simulates_gain_two():
    """The external op-amp subckt recovers non-inverting gain = 1 + Rf/Rg = 2."""
    from circuit_synth.simulation.simulator import CircuitSimulator

    sim = CircuitSimulator(_subckt_amp())
    res = sim.operating_point()
    vout = float(res.analysis["VOUT"][0])
    assert vout == pytest.approx(2.0, abs=0.02), vout
