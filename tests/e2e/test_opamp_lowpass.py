"""Acceptance test: first-order inverting active low-pass filter.

End-to-end proof of the Stage-7 simulation stack: an ``@circuit`` declaring its
own AC stimulus (``Simulation_SPICE:VSIN``, AC magnitude 1 V) and an op-amp
(mapped to an ideal VCVS), converted to SPICE and swept with ``ac_analysis``,
then measured with the ``SimulationResult`` bode/cutoff helpers.

Topology -- first-order INVERTING active LPF (analytically exact with an ideal
op-amp)::

    VIN --R1--+--Rf--+--> VOUT      fc = 1/(2*pi*Rf*Cf)
              |      |               passband gain = -Rf/R1
             (-)in  Cf (Rf || Cf feedback)
             (+)in --- GND

Values: R1 = Rf = 10 kOhm, Cf = 1.5915 nF -> fc ~= 10.0 kHz, |gain| = 1 (0 dB).

Skips cleanly (never fails) when PySpice or a loadable ngspice is unavailable.
"""

import numpy as np
import pytest

from circuit_synth import Component, Net, circuit

R1_R = "10k"
RF_R = "10k"
CF_C = "1.5915nF"  # 1/(2*pi*10k*1.5915n) ~= 10.0 kHz
FC_HZ = 10_000.0


def _ngspice_available() -> bool:
    """True only if PySpice imports, the sim symbols construct, and ngspice loads."""
    try:
        from circuit_synth.simulation.simulator import PYSPICE_AVAILABLE

        if not PYSPICE_AVAILABLE:
            return False
        # Sim + op-amp symbols must be discoverable to build the circuit.
        Component(symbol="Simulation_SPICE:VSIN", ref="V1", value="1")
        Component(symbol="Amplifier_Operational:LM358", ref="U1")
        from PySpice.Spice.NgSpice.Shared import NgSpiceShared

        NgSpiceShared.new_instance()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _ngspice_available(),
    reason="PySpice, KiCad sim symbols, or a loadable ngspice is not available",
)


@circuit(name="OpampLowPassFilter")
def _opamp_lpf():
    """R1=Rf=10k, Cf=1.5915n first-order inverting active LPF, fc~=10 kHz."""
    v1 = Component(symbol="Simulation_SPICE:VSIN", ref="V1", value="1V")
    r1 = Component(symbol="Device:R", ref="R1", value=R1_R)
    rf = Component(symbol="Device:R", ref="Rf", value=RF_R)
    cf = Component(symbol="Device:C", ref="Cf", value=CF_C)
    u1 = Component(symbol="Amplifier_Operational:LM358", ref="U1")

    vin = Net("VIN")
    vout = Net("VOUT")
    ninv = Net("NINV")  # inverting-input node, shared by R1, Rf, Cf, U1 in-
    gnd = Net("GND")

    v1[1] += vin  # VSIN pin 1 = + (AC 1 V)
    v1[2] += gnd  # VSIN pin 2 = -
    r1[1] += vin
    r1[2] += ninv
    rf[1] += ninv  # Rf || Cf feedback from VOUT to the inverting node
    rf[2] += vout
    cf[1] += ninv
    cf[2] += vout
    # LM358 unit A pinout: 1 = out, 2 = in-, 3 = in+
    u1[1] += vout
    u1[2] += ninv
    u1[3] += gnd


def _sweep():
    """AC sweep 100 Hz .. 1 MHz, 50 points/decade."""
    return _opamp_lpf().simulate().ac_analysis(100, 1e6, points=50)


def _mag_at(freq, mag_db, target_hz):
    return mag_db[int(np.argmin(np.abs(freq - target_hz)))]


def test_passband_is_flat_below_corner():
    """Below fc/10 the magnitude is flat at 0 dB (unity gain) within +/-0.2 dB."""
    result = _sweep()
    freq, mag_db, _ = result.bode("VOUT")
    assert _mag_at(freq, mag_db, FC_HZ / 10) == pytest.approx(0.0, abs=0.2)
    assert result.passband_gain_db("VOUT") == pytest.approx(0.0, abs=0.2)


def test_cutoff_is_10kHz_within_5pct():
    """The -3 dB corner is 10 kHz within +/-5 %."""
    fc = _sweep().cutoff_frequency("VOUT")
    assert fc is not None
    assert fc == pytest.approx(FC_HZ, rel=0.05)


def test_rolloff_is_20db_per_decade():
    """Well above fc the response falls off at -20 dB/decade.

    Measured on the asymptote (10*fc -> 100*fc). NOTE: fc -> 10*fc only spans
    ~17 dB because fc itself sits on the -3 dB knee, not on the asymptote.
    """
    freq, mag_db, _ = _sweep().bode("VOUT")
    drop = _mag_at(freq, mag_db, 10 * FC_HZ) - _mag_at(freq, mag_db, 100 * FC_HZ)
    assert drop == pytest.approx(20.0, abs=1.0)
