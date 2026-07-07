"""KiCad ``Sim.*`` property layer (Stage 9.1).

circuit-synth mirrors KiCad's simulation-only model attach: a component can carry
``Sim.Enable``/``Sim.Device``/``Sim.Params`` fields (KiCad's native, dotted
spelling) and the SPICE converter honors them without touching the symbol or
footprint. These are read off ``_extra_fields`` exactly like the waveform params.

* ``Sim.Enable="0"`` excludes a part from simulation -- ``convert()`` skips it and
  ``validate()`` neither checks it nor counts its pins toward net connectivity.
* ``Sim.Device`` overrides symbol classification (a sim-only stand-in on any symbol).
* ``Sim.Params`` overlays ngspice model params, emitted under a per-device derived
  model name so two parts with different overrides do not collide.

Most tests are netlist-level (need PySpice); the validate/property tests need only
the KiCad symbol libraries.
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

needs_pyspice = pytest.mark.skipif(
    not _pyspice_available(), reason="PySpice not available"
)


def _converter(c):
    from circuit_synth.simulation.converter import SpiceConverter

    return SpiceConverter(c)


def _netlist(c) -> str:
    return str(_converter(c).convert())


def _validate(c):
    from circuit_synth.simulation.converter import SimulationValidationError

    try:
        _converter(c).validate()
        return None
    except SimulationValidationError as e:
        return e


# --------------------------------------------------------------------------- #
# Property layer: dotted Sim.* fields are accepted and round-trip              #
# --------------------------------------------------------------------------- #


def test_dotted_sim_property_accepted_and_roundtrips():
    """KiCad's dotted Sim.* names are valid properties and survive to_dict/from_dict."""
    c = Component(
        symbol="Device:R",
        ref="RSIM1",
        value="1k",
        **{"Sim.Enable": "0", "Sim.Device": "R"},
    )
    assert getattr(c, "Sim.Enable") == "0"
    assert c._extra_fields["Sim.Device"] == "R"

    # Round-trip via the circuit-synth dict form (distinct ref avoids the global
    # reference registry flagging a collision with the original).
    data = c.to_dict()
    data["ref"] = "RSIM2"
    revived = Component.from_dict(data)
    assert revived._extra_fields.get("Sim.Enable") == "0"
    assert revived._extra_fields.get("Sim.Device") == "R"


# --------------------------------------------------------------------------- #
# Sim.Enable exclusion                                                         #
# --------------------------------------------------------------------------- #


@needs_pyspice
def test_sim_enable_zero_excludes_from_netlist():
    """A Sim.Enable=0 part is absent from the emitted netlist."""

    @circuit(name="Excluded")
    def cir():
        v1 = Component(symbol="Simulation_SPICE:VDC", ref="V1", value="5V")
        r1 = Component(symbol="Device:R", ref="R1", value="1k")
        # A decorative connector rides on the same nets but opts out of sim.
        r2 = Component(
            symbol="Device:R", ref="R2", value="10k", **{"Sim.Enable": "0"}
        )
        vin = Net("VIN")
        gnd = Net("GND")
        v1[1] += vin
        v1[2] += gnd
        r1[1] += vin
        r1[2] += gnd
        r2[1] += vin
        r2[2] += gnd

    netlist = _netlist(cir())
    assert "RR1" in netlist
    assert "RR2" not in netlist  # excluded


def test_sim_enable_zero_unknown_symbol_passes_validate():
    """An unrecognized symbol marked Sim.Enable=0 is not a validation error."""

    @circuit(name="ExcludedUnknown")
    def cir():
        v1 = Component(symbol="Simulation_SPICE:VDC", ref="V1", value="5V")
        r1 = Component(symbol="Device:R", ref="R1", value="1k")
        # Non-SPICE symbol that would normally fail validation, opted out.
        deco = Component(
            symbol="Device:Varistor", ref="RV1", value="", **{"Sim.Enable": "0"}
        )
        vin = Net("VIN")
        gnd = Net("GND")
        v1[1] += vin
        v1[2] += gnd
        r1[1] += vin
        r1[2] += gnd
        deco[1] += vin
        deco[2] += gnd

    assert _validate(cir()) is None


def test_excluded_source_is_no_excitation():
    """A Sim.Enable=0 source no longer counts as the circuit's excitation."""

    @circuit(name="ExcludedSource")
    def cir():
        v1 = Component(
            symbol="Simulation_SPICE:VDC", ref="V1", value="5V", **{"Sim.Enable": "0"}
        )
        r1 = Component(symbol="Device:R", ref="R1", value="1k")
        r2 = Component(symbol="Device:R", ref="R2", value="1k")
        # Non-rail net name so the source-name heuristic doesn't supply excitation
        # on its own -- the excluded V1 must be the only candidate source.
        na = Net("NA")
        gnd = Net("GND")
        v1[1] += na
        v1[2] += gnd
        r1[1] += na
        r1[2] += gnd
        r2[1] += na
        r2[2] += gnd

    err = _validate(cir())
    assert err is not None
    assert any("no voltage or current source" in p for p in err.problems), err.problems


def test_net_orphaned_by_exclusion_is_floating():
    """Excluding a part can strand a net; that is still a floating-node error."""

    @circuit(name="OrphanedNet")
    def cir():
        v1 = Component(symbol="Simulation_SPICE:VDC", ref="V1", value="5V")
        r1 = Component(symbol="Device:R", ref="R1", value="1k")
        # R2 is the only *other* thing on SIG; excluding it strands SIG.
        r2 = Component(
            symbol="Device:R", ref="R2", value="1k", **{"Sim.Enable": "0"}
        )
        vin = Net("VIN")
        gnd = Net("GND")
        sig = Net("SIG")
        v1[1] += vin
        v1[2] += gnd
        r1[1] += vin
        r1[2] += sig
        r2[1] += sig
        r2[2] += gnd

    err = _validate(cir())
    assert err is not None
    assert any("SIG" in p for p in err.problems), err.problems


def test_net_private_to_excluded_part_is_dropped_not_floating():
    """A net whose ONLY pins belong to Sim.Enable=0 parts is dropped, not flagged.

    Report F6: a sensor/connector placed with Sim.Enable=0 (schematic/BOM only)
    carries private rails -- e.g. the SiPM's V_BIAS_NEG / FAST -- whose every pin
    is excluded from the netlist. Those nets never enter SPICE, so they are absent,
    not floating; flagging them aborts an otherwise valid simulation.
    """

    @circuit(name="PrivateExcludedNet")
    def cir():
        v1 = Component(symbol="Simulation_SPICE:VDC", ref="V1", value="5V")
        r1 = Component(symbol="Device:R", ref="R1", value="1k")
        r2 = Component(symbol="Device:R", ref="R2", value="2k")
        # A sim-disabled connector: pin 1 rides the live VIN rail, pin 2 goes to a
        # private BIAS net that nothing else in the sim touches.
        j1 = Component(
            symbol="Device:R", ref="J1", value="0", **{"Sim.Enable": "0"}
        )
        vin = Net("VIN")
        out = Net("OUT")
        gnd = Net("GND")
        bias = Net("BIAS")  # private to the excluded J1
        v1[1] += vin
        v1[2] += gnd
        r1[1] += vin
        r1[2] += out
        r2[1] += out
        r2[2] += gnd
        j1[1] += vin
        j1[2] += bias

    assert _validate(cir()) is None


def test_net_private_to_enabled_part_still_floating():
    """The same private net, with the part sim-ENABLED, is still a floating error.

    Guards the F6 fix from over-reaching: only an *all-excluded* net is dropped.
    """

    @circuit(name="PrivateEnabledNet")
    def cir():
        v1 = Component(symbol="Simulation_SPICE:VDC", ref="V1", value="5V")
        r1 = Component(symbol="Device:R", ref="R1", value="1k")
        r2 = Component(symbol="Device:R", ref="R2", value="2k")
        # Same topology, but J1 is now part of the simulation: its pin-2 dangles.
        j1 = Component(symbol="Device:R", ref="J1", value="0")
        vin = Net("VIN")
        out = Net("OUT")
        gnd = Net("GND")
        bias = Net("BIAS")
        v1[1] += vin
        v1[2] += gnd
        r1[1] += vin
        r1[2] += out
        r2[1] += out
        r2[2] += gnd
        j1[1] += vin
        j1[2] += bias

    err = _validate(cir())
    assert err is not None
    assert any("BIAS" in p for p in err.problems), err.problems


# --------------------------------------------------------------------------- #
# Sim.Device classification override                                          #
# --------------------------------------------------------------------------- #


def test_sim_device_overrides_classification_unit():
    """_kind() honors Sim.Device over the symbol's own classification."""
    conv = _converter(None)
    r_as_diode = Component(symbol="Device:R", ref="R1", **{"Sim.Device": "D"})
    npn = Component(symbol="Device:R", ref="R2", **{"Sim.Device": "NPN"})
    plain_r = Component(symbol="Device:R", ref="R3", value="1k")
    assert conv._kind(r_as_diode) == "diode"
    assert conv._kind(npn) == "bjt"
    assert conv._kind(plain_r) == "resistor"


@needs_pyspice
def test_sim_device_emits_overridden_instance():
    """A resistor symbol with Sim.Device=D becomes a diode device in the netlist."""

    @circuit(name="StandIn")
    def cir():
        v1 = Component(symbol="Simulation_SPICE:VDC", ref="V1", value="5V")
        # Sim-only stand-in: a diode riding on a resistor symbol (value cleared so
        # it falls back to the generic diode model rather than naming "1k").
        d1 = Component(symbol="Device:R", ref="R1", **{"Sim.Device": "D"})
        rload = Component(symbol="Device:R", ref="R2", value="1k")
        vin = Net("VIN")
        out = Net("OUT")
        gnd = Net("GND")
        v1[1] += vin
        v1[2] += gnd
        d1[1] += vin
        d1[2] += out
        rload[1] += out
        rload[2] += gnd

    netlist = _netlist(cir())
    assert "DR1" in netlist  # emitted as a diode element, not a resistor
    assert ".model DefaultDiode D" in netlist


# --------------------------------------------------------------------------- #
# Sim.Params override                                                          #
# --------------------------------------------------------------------------- #


@needs_pyspice
def test_sim_params_emits_derived_model_card():
    """Sim.Params overlays base model params under a per-device derived name."""

    @circuit(name="Overridden")
    def cir():
        v1 = Component(symbol="Simulation_SPICE:VDC", ref="V1", value="5V")
        q1 = Component(
            symbol="Transistor_BJT:BC547",
            ref="Q1",
            **{"Sim.Params": "BF=250 VAF=80"},
        )
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
        # C, B, E order on BC547 mapped by pin number.
        q1[1] += c
        q1[2] += b
        q1[3] += gnd

    netlist = _netlist(cir())
    # A derived model card carrying the override, named per-device.
    assert "DefaultNPN_Q1" in netlist
    assert "BF=250" in netlist
    assert "VAF=80" in netlist
