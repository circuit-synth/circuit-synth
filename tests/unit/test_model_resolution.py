"""Tiered device-model resolution with provenance (Stage 9.2).

Active devices resolve their SPICE ``.model`` through a ladder --
datasheet-fit (the built-in ``ModelLibrary``: real 1N4148/2N3904/... params) then
textbook generic (``Default*``) -- and the converter records *which tier* every
device got, so a generic is never silently passed off as the real part. Naming a
part the ladder can't resolve is a hard validation error, not a silent generic.

Netlist-level tests need PySpice; the resolution/provenance dict is inspected on
the converter directly.
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
    not _symbols_available(), reason="KiCad symbol libraries not available"
)
needs_pyspice = pytest.mark.skipif(
    not _pyspice_available(), reason="PySpice not available"
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


def _diode_circuit(diode_value):
    @circuit(name="DiodeCkt")
    def cir():
        v1 = Component(symbol="Simulation_SPICE:VDC", ref="V1", value="5V")
        d1 = Component(symbol="Device:D", ref="D1", value=diode_value)
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

    return cir()


@needs_pyspice
def test_named_diode_resolves_datasheet_fit():
    """value='1N4148' emits the library's datasheet-fit card, tier datasheet_fit."""
    conv = _converter(_diode_circuit("1N4148"))
    netlist = str(conv.convert())
    assert ".model 1N4148 D" in netlist
    assert "DD1 VIN OUT 1N4148" in netlist
    prov = conv.model_provenance["D1"]
    assert prov.tier == "datasheet_fit"
    assert prov.name == "1N4148"
    # A datasheet-fit param distinct from the generic diode (RS=0.1) proves the
    # library values -- not the textbook generic -- reached the netlist.
    assert "0.568" in netlist  # 1N4148 RS


@needs_pyspice
def test_empty_diode_falls_back_to_generic():
    """An unnamed diode gets the generic model, recorded as tier generic."""
    conv = _converter(_diode_circuit(""))
    netlist = str(conv.convert())
    assert ".model DefaultDiode D" in netlist
    prov = conv.model_provenance["D1"]
    assert prov.tier == "generic"
    assert prov.name == "DefaultDiode"


# --------------------------------------------------------------------------- #
# Stage 22.5: Schottky models + Sim.Params fallback for unresolved names.
# --------------------------------------------------------------------------- #


def _schottky_circuit(diode_value, sim_params=None):
    props = {}
    if sim_params is not None:
        props["Sim.Params"] = sim_params

    @circuit(name="SchottkyCkt")
    def cir():
        v1 = Component(symbol="Simulation_SPICE:VDC", ref="V1", value="5V")
        d1 = Component(
            symbol="Device:D_Schottky", ref="D1", value=diode_value, **props
        )
        r1 = Component(symbol="Device:R", ref="R1", value="1k")
        vin, out, gnd = Net("VIN"), Net("OUT"), Net("GND")
        v1[1] += vin
        v1[2] += gnd
        d1[2] += vin  # A (anode)
        d1[1] += out  # K (cathode)
        r1[1] += out
        r1[2] += gnd

    return cir()


@needs_pyspice
@pytest.mark.parametrize("part", ["SS14", "1N5819"])
def test_schottky_named_part_resolves_datasheet_fit(part):
    conv = _converter(_schottky_circuit(part))
    netlist = str(conv.convert())
    assert f".model {part} D" in netlist
    assert f"DD1 VIN OUT {part}" in netlist
    prov = conv.model_provenance["D1"]
    assert prov.tier == "datasheet_fit" and prov.name == part


@needs_pyspice
def test_default_schottky_is_generic():
    conv = _converter(_schottky_circuit("DefaultSchottky"))
    netlist = str(conv.convert())
    assert ".model DefaultSchottky D" in netlist
    prov = conv.model_provenance["D1"]
    assert prov.tier == "generic" and prov.name == "DefaultSchottky"


@needs_pyspice
def test_unresolved_name_with_params_falls_back_to_generic(caplog):
    """An unknown value + Sim.Params degrades to DefaultDiode + overrides, not error."""
    import logging

    conv = _converter(_schottky_circuit("NoSuchDiode9000", sim_params="IS=2e-6"))
    with caplog.at_level(logging.WARNING, logger="circuit_synth.simulation.converter"):
        netlist = str(conv.convert())  # validates strictly + emits
    # Derived per-ref card off the generic, carrying the override.
    assert ".model DefaultDiode_D1 D" in netlist
    assert "DD1 VIN OUT DefaultDiode_D1" in netlist
    assert "2e-06" in netlist or "2e-6" in netlist  # IS override reached the card
    prov = conv.model_provenance["D1"]
    assert prov.tier == "generic" and prov.overridden is True
    assert any(
        "not in library" in r.getMessage() and "NoSuchDiode9000" in r.getMessage()
        for r in caplog.records
    ), [r.getMessage() for r in caplog.records]


@needs_pyspice
def test_unresolved_name_without_params_still_errors():
    """Regression guard: an unknown value with NO Sim.Params stays a hard error."""
    from circuit_synth.simulation.converter import SimulationValidationError

    with pytest.raises(SimulationValidationError) as exc:
        _converter(_schottky_circuit("NoSuchDiode9000")).convert()
    assert "NoSuchDiode9000" in str(exc.value)


@needs_pyspice
def test_named_bjt_resolves_datasheet_fit():
    """value='2N3904' resolves to the library NPN card."""

    @circuit(name="BjtCkt")
    def cir():
        v1 = Component(symbol="Simulation_SPICE:VDC", ref="V1", value="5V")
        q1 = Component(symbol="Transistor_BJT:BC547", ref="Q1", value="2N3904")
        rc = Component(symbol="Device:R", ref="RC", value="1k")
        rb = Component(symbol="Device:R", ref="RB", value="100k")
        vcc = Net("VCC")
        c = Net("C")
        b = Net("B")
        gnd = Net("GND")
        v1[1] += vcc
        v1[2] += gnd
        rc[1] += vcc
        rc[2] += c
        rb[1] += vcc
        rb[2] += b
        q1[1] += c
        q1[2] += b
        q1[3] += gnd

    conv = _converter(cir())
    netlist = str(conv.convert())
    assert ".model 2N3904 NPN" in netlist
    assert conv.model_provenance["Q1"].tier == "datasheet_fit"


def test_unknown_named_model_is_validation_error():
    """A value naming a part the ladder can't resolve is a hard error, not generic."""
    err = _validate(_diode_circuit("NOSUCHPART9000"))
    assert err is not None
    assert any("NOSUCHPART9000" in p for p in err.problems), err.problems


@needs_pyspice
def test_sim_params_override_on_datasheet_base():
    """Sim.Params overlays a datasheet-fit base under a per-device derived card."""

    @circuit(name="OverrideLib")
    def cir():
        v1 = Component(symbol="Simulation_SPICE:VDC", ref="V1", value="5V")
        d1 = Component(
            symbol="Device:D", ref="D1", value="1N4148", **{"Sim.Params": "N=1.9"}
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
    assert "1N4148_D1" in netlist  # derived card
    assert "N=1.9" in netlist
    # base still recorded as the datasheet-fit part
    assert conv.model_provenance["D1"].name == "1N4148"


@needs_pyspice
def test_simulator_exposes_provenance():
    """CircuitSimulator surfaces model_provenance from its converter."""
    from circuit_synth.simulation.simulator import CircuitSimulator

    sim = CircuitSimulator(_diode_circuit("1N4148"))
    assert sim.model_provenance["D1"].tier == "datasheet_fit"
