"""Transient / waveform voltage sources (Stage 7 waveform-sources item).

Beyond DC (VDC) and the AC magnitude added in 7.4a, a source can now carry a
transient waveform whose parameters come from the component's extra fields (any
kwarg passed to ``Component`` is stored in ``_extra_fields``):

* ``Simulation_SPICE:VSIN``   -> ``SIN(offset ampl freq td theta)`` + an AC mag
* ``Simulation_SPICE:VPULSE`` -> ``PULSE(v1 v2 td tr tf pw per)``
* ``Simulation_SPICE:VPWL``   -> ``PWL(t1 v1 t2 v2 ...)`` from a ``points`` field

Numbers keep their SI suffix (``1k``/``1m``/``1u``/``1n``) -- ngspice parses them.

Netlist-level tests need no ngspice; one end-to-end test (a pulse step into an RC)
is skipped without a loadable ngspice.
"""

import pytest

from circuit_synth import Component, Net, circuit
from circuit_synth.simulation.converter import SpiceConverter


def _sim_available() -> bool:
    try:
        from circuit_synth.simulation.converter import PYSPICE_AVAILABLE

        if not PYSPICE_AVAILABLE:
            return False
        Component(symbol="Simulation_SPICE:VSIN", ref="V1")
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _sim_available(),
    reason="PySpice or the KiCad Simulation_SPICE symbols are not available",
)


def _netlist(c) -> str:
    return str(SpiceConverter(c).convert())


def _src_line(netlist: str) -> str:
    for line in netlist.splitlines():
        if line.startswith("VV1 "):
            return line
    raise AssertionError(f"no V1 source line in:\n{netlist}")


def _source_line(symbol: str, **source_kwargs) -> str:
    """Build 'source -> R1 -> GND', convert, and return V1's netlist line.

    The source is created *inside* the @circuit so it registers with the circuit.
    """

    @circuit(name="SrcTest")
    def build():
        v1 = Component(symbol=symbol, ref="V1", **source_kwargs)
        r1 = Component(symbol="Device:R", ref="R1", value="1k")
        vin = Net("VIN")
        gnd = Net("GND")
        v1[1] += vin
        v1[2] += gnd
        r1[1] += vin
        r1[2] += gnd

    return _src_line(_netlist(build()))


def test_vsin_default_spec():
    """VSIN with no params emits SIN with textbook defaults plus AC 1."""
    line = _source_line("Simulation_SPICE:VSIN")
    assert "SIN(0 1 1k 0 0)" in line, line
    assert "AC 1" in line, line


def test_vsin_honors_extra_field_params():
    """amplitude/frequency/offset extra fields feed the SIN spec."""
    line = _source_line(
        "Simulation_SPICE:VSIN", amplitude="2", frequency="2k", offset="0.5"
    )
    assert "SIN(0.5 2 2k 0 0)" in line, line


def test_vpulse_spec():
    """VPULSE emits PULSE(v1 v2 td tr tf pw per) with params + defaults."""
    line = _source_line("Simulation_SPICE:VPULSE", v1="0", v2="5", pw="1m", per="2m")
    assert "PULSE(0 5 0 1n 1n 1m 2m)" in line, line


def test_vpwl_from_string():
    """VPWL renders points given as a whitespace string."""
    line = _source_line("Simulation_SPICE:VPWL", points="0 0 1m 5 2m 0")
    assert "PWL(0 0 1m 5 2m 0)" in line, line


def test_vpwl_from_pairs():
    """VPWL renders points given as a list of (t, v) pairs."""
    line = _source_line("Simulation_SPICE:VPWL", points=[(0, 0), ("1m", 5), ("2m", 0)])
    assert "PWL(0 0 1m 5 2m 0)" in line, line


def test_vdc_unchanged():
    """VDC still emits a plain DC value (no waveform function)."""
    line = _source_line("Simulation_SPICE:VDC", value="9V")
    assert "SIN" not in line and "PULSE" not in line and "PWL" not in line, line
    assert line.split()[-1] == "9.0", line


def _ngspice_loads() -> bool:
    try:
        from circuit_synth.simulation.simulator import PYSPICE_AVAILABLE

        if not PYSPICE_AVAILABLE:
            return False
        from PySpice.Spice.NgSpice.Shared import NgSpiceShared

        NgSpiceShared.new_instance()
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _ngspice_loads(), reason="no loadable ngspice library")
def test_pulse_step_into_rc_settles():
    """End-to-end: a 0->5 V pulse step into an RC charges the cap toward 5 V.

    R=1k, C=1u -> tau=1 ms. A step at t=0 with a long width; after ~5 tau the
    output is within a few % of 5 V and it starts near 0. Proves the transient
    source + transient_analysis path works, options passthrough included.
    """

    @circuit(name="RCStep")
    def rc():
        v1 = Component(
            symbol="Simulation_SPICE:VPULSE",
            ref="V1",
            v1="0",
            v2="5",
            td="0",
            tr="1n",
            tf="1n",
            pw="1",
            per="2",
        )
        r1 = Component(symbol="Device:R", ref="R1", value="1k")
        c1 = Component(symbol="Device:C", ref="C1", value="1u")
        vin = Net("VIN")
        vout = Net("VOUT")
        gnd = Net("GND")
        v1[1] += vin
        v1[2] += gnd
        r1[1] += vin
        r1[2] += vout
        c1[1] += vout
        c1[2] += gnd

    result = (
        rc()
        .simulate()
        .transient_analysis(step_time=50e-6, end_time=6e-3, options={"reltol": 1e-3})
    )
    vout = result.get_voltage("VOUT")  # list over time
    assert vout[0] < 1.0, f"start not near 0: {vout[0]}"
    assert vout[-1] == pytest.approx(5.0, abs=0.3), f"end not near 5 V: {vout[-1]}"
