"""Simulation validation layer (Stage 7.1).

``SpiceConverter.validate()`` inspects a circuit *before* it is converted and
raises ``SimulationValidationError`` listing every problem at once, instead of the
old behaviour of silently ``logger.warning``-ing and skipping unknown components
(which produced a wrong-but-"successful" simulation). ``convert()`` runs it by
default (``strict=True``); ``convert(strict=False)`` restores the lenient path.

These tests build real ``@circuit`` objects and only need the KiCad symbol
libraries to construct components -- ``validate()`` itself needs neither ngspice
nor PySpice. The two ``convert()`` tests additionally need PySpice.
"""

import pytest

from circuit_synth import Component, Net, circuit


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


pytestmark = pytest.mark.skipif(
    not _symbols_available(),
    reason="KiCad symbol libraries not available",
)


def _converter(c):
    from circuit_synth.simulation.converter import SpiceConverter

    return SpiceConverter(c)


def _validate(c):
    """Run validate() and return the raised SimulationValidationError, or None."""
    from circuit_synth.simulation.converter import SimulationValidationError

    try:
        _converter(c).validate()
        return None
    except SimulationValidationError as e:
        return e


def test_good_divider_validates():
    """An explicit-source divider is valid and does not raise."""

    @circuit(name="GoodDivider")
    def good():
        v1 = Component(symbol="Simulation_SPICE:VDC", ref="V1", value="9V")
        r1 = Component(symbol="Device:R", ref="R1", value="1k")
        r2 = Component(symbol="Device:R", ref="R2", value="2k")
        vin = Net("VIN")
        vout = Net("VOUT")
        gnd = Net("GND")
        v1[1] += vin
        v1[2] += gnd
        r1[1] += vin
        r1[2] += vout
        r2[1] += vout
        r2[2] += gnd

    assert _validate(good()) is None


def test_unrecognized_component_raises():
    """A real-but-non-SPICE symbol (Device:Varistor) is reported, not skipped."""

    @circuit(name="HasVaristor")
    def cir():
        v1 = Component(symbol="Simulation_SPICE:VDC", ref="V1", value="5V")
        r1 = Component(symbol="Device:R", ref="R1", value="1k")
        rv = Component(symbol="Device:Varistor", ref="RV1", value="")
        vin = Net("VIN")
        gnd = Net("GND")
        v1[1] += vin
        v1[2] += gnd
        r1[1] += vin
        r1[2] += gnd
        rv[1] += vin
        rv[2] += gnd

    err = _validate(cir())
    assert err is not None
    assert any("RV1" in p for p in err.problems), err.problems


def test_floating_net_raises():
    """A net with a single connection and no source is flagged as floating."""

    @circuit(name="Floating")
    def cir():
        v1 = Component(symbol="Simulation_SPICE:VDC", ref="V1", value="5V")
        r1 = Component(symbol="Device:R", ref="R1", value="1k")
        vin = Net("VIN")
        gnd = Net("GND")
        sig = Net("SIG")  # only R1 pin 2 lands here -> floating
        v1[1] += vin
        v1[2] += gnd
        r1[1] += vin
        r1[2] += sig

    err = _validate(cir())
    assert err is not None
    assert any("SIG" in p for p in err.problems), err.problems


def test_no_source_raises():
    """A passive loop with no source and no ground has no excitation."""

    @circuit(name="NoSource")
    def cir():
        r1 = Component(symbol="Device:R", ref="R1", value="1k")
        r2 = Component(symbol="Device:R", ref="R2", value="1k")
        n1 = Net("N1")
        n2 = Net("N2")
        r1[1] += n1
        r1[2] += n2
        r2[1] += n2
        r2[2] += n1

    err = _validate(cir())
    assert err is not None
    assert any("no voltage or current source" in p for p in err.problems), err.problems


def test_opamp_missing_connection_raises():
    """An op-amp with fewer than three connected pins is flagged."""

    @circuit(name="BadOpAmp")
    def cir():
        u1 = Component(symbol="Amplifier_Operational:LM358", ref="U1", value="LM358")
        r1 = Component(symbol="Device:R", ref="R1", value="1k")
        vin = Net("VIN")
        vout = Net("VOUT")
        gnd = Net("GND")
        u1[1] += vout  # output
        u1[3] += vin  # non-inverting input; inverting input + rails left open
        r1[1] += vout
        r1[2] += gnd

    err = _validate(cir())
    assert err is not None
    assert any("op-amp" in p.lower() for p in err.problems), err.problems


@pytest.mark.skipif(not _pyspice_available(), reason="PySpice not available")
def test_convert_strict_raises_on_unknown():
    """convert() defaults to strict and refuses an unrecognized component."""
    from circuit_synth.simulation.converter import SimulationValidationError

    @circuit(name="StrictUnknown")
    def cir():
        v1 = Component(symbol="Simulation_SPICE:VDC", ref="V1", value="5V")
        rv = Component(symbol="Device:Varistor", ref="RV1", value="")
        vin = Net("VIN")
        gnd = Net("GND")
        v1[1] += vin
        v1[2] += gnd
        rv[1] += vin
        rv[2] += gnd

    with pytest.raises(SimulationValidationError):
        _converter(cir()).convert()


@pytest.mark.skipif(not _pyspice_available(), reason="PySpice not available")
def test_convert_non_strict_skips_unknown():
    """convert(strict=False) restores the lenient warn-and-skip path."""

    @circuit(name="LenientUnknown")
    def cir():
        v1 = Component(symbol="Simulation_SPICE:VDC", ref="V1", value="5V")
        r1 = Component(symbol="Device:R", ref="R1", value="1k")
        rv = Component(symbol="Device:Varistor", ref="RV1", value="")
        vin = Net("VIN")
        gnd = Net("GND")
        v1[1] += vin
        v1[2] += gnd
        r1[1] += vin
        r1[2] += gnd
        rv[1] += vin
        rv[2] += gnd

    spice = _converter(cir()).convert(strict=False)
    netlist = str(spice)
    assert "VV1" in netlist  # source kept
    assert "RR1" in netlist  # resistor kept
    # the varistor is skipped, not emitted
    assert "RV1" not in netlist
