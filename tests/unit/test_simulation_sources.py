"""Explicit SPICE source support.

A circuit can declare its own voltage/current source with a real KiCad symbol
(``Simulation_SPICE:VDC`` / ``IDC``) and an explicit value, instead of relying on
the net-name heuristic in ``converter._add_power_sources`` (which only injects a
supply for nets whose names match rail patterns like ``VCC*``/``VIN*``).

Two layers of coverage:

* **Netlist-level** (no ngspice needed): build the circuit, run ``SpiceConverter``,
  and assert on the emitted SPICE netlist string -- the source is present with the
  right value, its pins map to the right SPICE nodes in pin-number order (KiCad
  ``VDC`` declares ``Sim.Pins "1=+ 2=-"``), and the net-name heuristic did *not*
  add a second supply on a net the explicit source already drives.
* **End-to-end** (skipped without a loadable ngspice): a DC operating point proves
  the declared source actually drives the circuit with the correct sign.

Both layers skip cleanly (never fail) when PySpice or the KiCad Simulation_SPICE
symbol library is unavailable, matching ``tests/test_simulation_smoke.py``.
"""

import pytest

from circuit_synth import Component, Net, circuit


def _sim_symbols_available() -> bool:
    """True only if PySpice is importable and ``Simulation_SPICE:VDC`` constructs.

    Constructing the component proves the KiCad Simulation_SPICE symbol library is
    discoverable on this machine (the converter never needs ngspice to build a
    netlist, only PySpice).
    """
    try:
        from circuit_synth.simulation.converter import PYSPICE_AVAILABLE

        if not PYSPICE_AVAILABLE:
            return False
        Component(symbol="Simulation_SPICE:VDC", ref="V1", value="1")
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _sim_symbols_available(),
    reason="PySpice or the KiCad Simulation_SPICE symbol library is not available",
)


@circuit(name="ExplicitSourceDivider")
def _explicit_divider():
    """Explicit 9 V source -> 1k/2k divider. VOUT = 9 * 2/3 = 6.0 V.

    VDC declares ``Sim.Pins "1=+ 2=-"``, so pin 1 -> VIN (+), pin 2 -> GND (-).
    """
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


def _netlist(c) -> str:
    from circuit_synth.simulation.converter import SpiceConverter

    return str(SpiceConverter(c).convert())


def _v1_line(netlist: str) -> str:
    """The emitted SPICE line for source V1 (PySpice names it 'VV1')."""
    for line in netlist.splitlines():
        if line.startswith("VV1 "):
            return line
    raise AssertionError(f"no V source for V1 in netlist:\n{netlist}")


def test_explicit_voltage_source_emitted_with_value():
    """The declared VDC becomes a SPICE V source carrying its 9 V value."""
    parts = _v1_line(_netlist(_explicit_divider())).split()
    # 'VV1 <+node> <-node> <value>'
    assert float(parts[3]) == pytest.approx(9.0), parts


def test_explicit_source_polarity_follows_pin_numbers():
    """Pin 1 (+) -> VIN, pin 2 (-) -> GND(0): node order is 'VIN 0', not '0 VIN'."""
    parts = _v1_line(_netlist(_explicit_divider())).split()
    assert parts[1] == "VIN" and parts[2] == "0", parts


def test_explicit_source_suppresses_net_name_heuristic():
    """No auto 'V_supply' is added on a net an explicit source already drives."""
    netlist = _netlist(_explicit_divider())
    assert "V_supply" not in netlist, f"heuristic double-drove the net:\n{netlist}"


def test_polarity_swaps_with_pin_assignment():
    """Swapping which pin connects to VIN flips the emitted node order.

    This is the guard against the old behaviour, where nodes were sorted
    alphabetically and a source's polarity was independent of its pin wiring.
    """

    @circuit(name="SwappedSource")
    def swapped():
        v1 = Component(symbol="Simulation_SPICE:VDC", ref="V1", value="9V")
        r1 = Component(symbol="Device:R", ref="R1", value="1k")
        vin = Net("VIN")
        gnd = Net("GND")
        v1[1] += gnd  # + -> GND
        v1[2] += vin  # - -> VIN
        r1[1] += vin
        r1[2] += gnd

    parts = _v1_line(_netlist(swapped())).split()
    assert parts[1] == "0" and parts[2] == "VIN", parts


def _vsin_available() -> bool:
    """True only if the KiCad ``Simulation_SPICE:VSIN`` symbol constructs.

    ``VSIN`` (not ``VAC`` -- which does not exist in KiCad 10) is the AC/transient
    stimulus symbol; the converter gives it an ``AC`` magnitude so its driven node
    is the transfer function during an AC sweep.
    """
    try:
        from circuit_synth.simulation.converter import PYSPICE_AVAILABLE

        if not PYSPICE_AVAILABLE:
            return False
        Component(symbol="Simulation_SPICE:VSIN", ref="V1", value="1")
        return True
    except Exception:
        return False


@pytest.mark.skipif(
    not _vsin_available(), reason="KiCad Simulation_SPICE:VSIN symbol not available"
)
def test_ac_source_emits_ac_magnitude():
    """A VSIN source emits an ``AC <mag>`` term (default 1) in its netlist line."""

    @circuit(name="ACSource")
    def ac_src():
        v1 = Component(symbol="Simulation_SPICE:VSIN", ref="V1")
        r1 = Component(symbol="Device:R", ref="R1", value="1k")
        vin = Net("VIN")
        gnd = Net("GND")
        v1[1] += vin
        v1[2] += gnd
        r1[1] += vin
        r1[2] += gnd

    line = _v1_line(_netlist(ac_src()))
    assert "AC 1" in line.upper(), line


@pytest.mark.skipif(
    not _vsin_available(), reason="KiCad Simulation_SPICE:VSIN symbol not available"
)
def test_ac_source_honors_explicit_magnitude():
    """An explicit ``value`` on a VSIN source becomes its AC magnitude."""

    @circuit(name="ACSourceMag")
    def ac_src():
        v1 = Component(symbol="Simulation_SPICE:VSIN", ref="V1", value="2V")
        r1 = Component(symbol="Device:R", ref="R1", value="1k")
        vin = Net("VIN")
        gnd = Net("GND")
        v1[1] += vin
        v1[2] += gnd
        r1[1] += vin
        r1[2] += gnd

    line = _v1_line(_netlist(ac_src())).upper()
    assert "AC 2" in line, line


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
def test_explicit_source_drives_operating_point():
    """End-to-end: the explicit 9 V source yields VIN=+9 V, VOUT=+6 V via ngspice."""
    result = _explicit_divider().simulate().operating_point()
    assert result.get_voltage("VIN") == pytest.approx(9.0, abs=0.01)
    assert result.get_voltage("VOUT") == pytest.approx(6.0, abs=0.01)


# --- Current sources (report F7, stage 12.1) --------------------------------
#
# ``_add_current_source`` used to emit a DC-only current for EVERY current-source
# symbol, so ``Simulation_SPICE:ISIN`` carried zero AC magnitude and AC analysis of
# any current-driven circuit (photodiode / SiPM TIA) read -inf dB. The fix mirrors
# the voltage-source path with a symbol-aware ``_current_source_spec``. PySpice names
# the emitted current source ``II1`` (element letter 'I' + ref 'I1').


def _isin_available() -> bool:
    """True only if the KiCad ``Simulation_SPICE:ISIN`` symbol constructs."""
    try:
        from circuit_synth.simulation.converter import PYSPICE_AVAILABLE

        if not PYSPICE_AVAILABLE:
            return False
        Component(symbol="Simulation_SPICE:ISIN", ref="I1", value="1")
        return True
    except Exception:
        return False


def _sim_current_symbol_available(symbol: str) -> bool:
    """True only if ``symbol`` constructs (probed once, at import, no circuit ctx)."""
    try:
        from circuit_synth.simulation.converter import PYSPICE_AVAILABLE

        if not PYSPICE_AVAILABLE:
            return False
        Component(symbol=symbol, ref="I1")
        return True
    except Exception:
        return False


_IPULSE_OK = _sim_current_symbol_available("Simulation_SPICE:IPULSE")
_IDC_OK = _sim_current_symbol_available("Simulation_SPICE:IDC")


def _i1_line(netlist: str) -> str:
    """The emitted SPICE line for current source I1 (PySpice names it 'II1')."""
    for line in netlist.splitlines():
        if line.startswith("II1 "):
            return line
    raise AssertionError(f"no I source for I1 in netlist:\n{netlist}")


def _isin_rc(value=None, **src_kwargs):
    """1-current-source + 1-resistor circuit; ISIN drives NINV, R to GND."""

    @circuit(name="ISIN_RC")
    def _c():
        kw = {"symbol": "Simulation_SPICE:ISIN", "ref": "I1"}
        if value is not None:
            kw["value"] = value
        kw.update(src_kwargs)
        i1 = Component(**kw)
        r1 = Component(symbol="Device:R", ref="R1", value="1k")
        ninv = Net("NINV")
        gnd = Net("GND")
        i1[1] += ninv
        i1[2] += gnd
        r1[1] += ninv
        r1[2] += gnd

    return _c()


@pytest.mark.skipif(
    not _isin_available(), reason="KiCad Simulation_SPICE:ISIN symbol not available"
)
def test_isin_emits_ac_magnitude_and_sine():
    """ISIN value='1A' -> the line carries 'AC 1' (for .ac) and 'SIN(0 1 ...)'."""
    line = _i1_line(_netlist(_isin_rc(value="1A"))).upper()
    assert "AC 1" in line, line
    assert "SIN(0 1 " in line, line


@pytest.mark.skipif(
    not _isin_available(), reason="KiCad Simulation_SPICE:ISIN symbol not available"
)
def test_isin_honors_param_overrides():
    """amplitude/frequency/ac kwargs override the value-derived defaults."""
    line = _i1_line(
        _netlist(_isin_rc(value="1A", amplitude="2m", frequency="10k", ac="1m"))
    ).upper()
    assert "AC 1M" in line, line  # explicit ac= wins over value
    assert "SIN(0 2M 10K " in line, line  # amplitude + frequency overrides


@pytest.mark.skipif(
    not _IPULSE_OK, reason="KiCad Simulation_SPICE:IPULSE symbol not available"
)
def test_ipulse_emits_pulse_waveform():
    """IPULSE with i1/i2 -> a PULSE(...) spec starting '0 1m'."""

    @circuit(name="IPULSE_RC")
    def _c():
        i1 = Component(
            symbol="Simulation_SPICE:IPULSE", ref="I1", **{"i1": "0", "i2": "1m"}
        )
        r1 = Component(symbol="Device:R", ref="R1", value="1k")
        ninv = Net("NINV")
        gnd = Net("GND")
        i1[1] += ninv
        i1[2] += gnd
        r1[1] += ninv
        r1[2] += gnd

    line = _i1_line(_netlist(_c())).upper()
    assert "PULSE(0 1M " in line, line


@pytest.mark.skipif(
    not _IDC_OK, reason="KiCad Simulation_SPICE:IDC symbol not available"
)
def test_idc_stays_plain_dc():
    """IDC value='5u' -> a plain 5 uA DC current, no AC/SIN text (no-regression)."""

    @circuit(name="IDC_RC")
    def _c():
        i1 = Component(symbol="Simulation_SPICE:IDC", ref="I1", value="5u")
        r1 = Component(symbol="Device:R", ref="R1", value="1k")
        ninv = Net("NINV")
        gnd = Net("GND")
        i1[1] += ninv
        i1[2] += gnd
        r1[1] += ninv
        r1[2] += gnd

    line = _i1_line(_netlist(_c())).upper()
    assert "AC" not in line, line
    assert "SIN" not in line, line
    # 5u -> 5e-06 A
    assert float(line.split()[3]) == pytest.approx(5e-6), line


@pytest.mark.skipif(not _ngspice_loads(), reason="no loadable ngspice library")
@pytest.mark.skipif(
    not _isin_available(), reason="KiCad Simulation_SPICE:ISIN symbol not available"
)
def test_isin_ac_drives_current_rc_end_to_end():
    """End-to-end: ISIN 1 A into R=1k || C -> passband = R (60 dBOhm), pole 1/(2piRC).

    This is the property F7 broke: with a DC-only current source the AC sweep saw
    zero drive and read -inf dB everywhere. A 1 A AC current into a 1 kOhm shunt
    gives |V| = 1 kV = 60 dBOhm in the passband; the R||C corner is 1/(2*pi*R*C).
    C = 159.15 nF -> fc ~= 1.0 kHz.
    """
    import numpy as np

    R_OHM = 1000.0
    C_F = 159.15e-9  # 1/(2*pi*1k*159.15n) ~= 1000 Hz
    FC_HZ = 1.0 / (2.0 * np.pi * R_OHM * C_F)

    @circuit(name="ISIN_AC_RC")
    def _c():
        i1 = Component(symbol="Simulation_SPICE:ISIN", ref="I1", value="1A")
        r1 = Component(symbol="Device:R", ref="R1", value="1k")
        cf = Component(symbol="Device:C", ref="C1", value="159.15nF")
        ninv = Net("VOUT")
        gnd = Net("GND")
        i1[1] += ninv
        i1[2] += gnd
        r1[1] += ninv
        r1[2] += gnd
        cf[1] += ninv
        cf[2] += gnd

    result = _c().simulate().ac_analysis(10, 1e6, points=50)
    assert result.passband_gain_db("VOUT") == pytest.approx(60.0, abs=0.1)
    fc = result.cutoff_frequency("VOUT")
    assert fc is not None
    assert fc == pytest.approx(FC_HZ, rel=0.05)
