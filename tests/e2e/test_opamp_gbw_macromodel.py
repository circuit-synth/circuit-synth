"""Acceptance test: opt-in 1-pole GBW op-amp macromodel on a SiPM/photodiode TIA.

End-to-end proof of stage 12.4 (report F3). An ideal op-amp (frequency-independent
VCVS) validates only the Rf*Cf transimpedance arithmetic: source/feedback capacitance
has no effect, so loop stability and cap-limited bandwidth are invisible. The opt-in
single-pole macromodel (``Sim.Gbw``) makes them simulatable.

Topology -- inverting shunt-feedback transimpedance amplifier (the SiPM TIA)::

    Iin --+--------+----> VOUT
          |        |
         Cd   Rf || Cf   (Cd = SiPM terminal cap 1.04 nF on the summing node)
          |        |
         GND     (feedback NINV <-> VOUT)
          |
    op-amp in- = NINV, in+ = GND, out = VOUT

With a 1 A AC drive the VOUT magnitude *is* the transimpedance, so the DC value is
Rf = 100 kOhm = 100 dBOhm.

Two things an ideal op-amp cannot reproduce, and this macromodel does:

* With a sensible Cf = 1.5 pF the amplifier is well-compensated: ~100 dBOhm passband
  and a FINITE -3 dB bandwidth set by the interplay of the Rf*Cf pole, Cd and the
  op-amp's own GBW (ADA4817: 1.4 GHz).
* With Cf removed (0.01 pF) the noise gain from Cd peaks against the finite loop
  bandwidth -> a large gain bump above the passband. The ideal op-amp stays perfectly
  flat there (test guards that contrast), so the bump proves the pole is real.

Skips cleanly (never fails) when PySpice or a loadable ngspice is unavailable.
"""

import numpy as np
import pytest

from circuit_synth import Component, Net, circuit

RF = "100k"  # transimpedance -> 100 kOhm = 100 dBOhm passband
CD = "1.04nF"  # SiPM terminal capacitance on the summing node
GBW = "1.4G"  # ADA4817-1 gain-bandwidth product


def _ngspice_available() -> bool:
    """True only if PySpice imports, the sim/op-amp symbols construct, ngspice loads."""
    try:
        from circuit_synth.simulation.simulator import PYSPICE_AVAILABLE

        if not PYSPICE_AVAILABLE:
            return False
        Component(symbol="Simulation_SPICE:ISIN", ref="I1", value="1")
        Component(symbol="Amplifier_Operational:ADA4817-1ACP", ref="U1")
        from PySpice.Spice.NgSpice.Shared import NgSpiceShared

        NgSpiceShared.new_instance()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _ngspice_available(),
    reason="PySpice, KiCad sim symbols, or a loadable ngspice is not available",
)


def _tia(cf_value, gbw=GBW):
    """SiPM TIA: ISIN 1 A into (Cd || Rf||Cf feedback) around an op-amp.

    ``gbw=None`` builds the ideal op-amp (no Sim.Gbw); otherwise the macromodel.
    """

    @circuit(name="GbwTIA")
    def _c():
        i1 = Component(symbol="Simulation_SPICE:ISIN", ref="I1", value="1A")
        kw = {"symbol": "Amplifier_Operational:ADA4817-1ACP", "ref": "U1"}
        if gbw is not None:
            kw["Sim.Gbw"] = gbw
        u1 = Component(**kw)
        rf = Component(symbol="Device:R", ref="Rf1", value=RF)
        cf = Component(symbol="Device:C", ref="Cf1", value=cf_value)
        cd = Component(symbol="Device:C", ref="Cd1", value=CD)

        ninv = Net("NINV")
        vout = Net("VOUT")
        gnd = Net("GND")

        u1[3] += ninv  # in-  (summing junction / virtual ground)
        u1[4] += gnd  # in+
        u1[2] += vout  # FB (tied to the true output, per the design)
        u1[7] += vout  # OUT
        rf[1] += ninv
        rf[2] += vout
        cf[1] += ninv
        cf[2] += vout
        cd[1] += ninv
        cd[2] += gnd
        i1[1] += ninv
        i1[2] += gnd

    return _c()


def _sweep(cf_value, gbw=GBW):
    return _tia(cf_value, gbw).simulate().ac_analysis(1e3, 5e6, points=120)


def _dc_and_peak(result):
    """(low-frequency transimpedance dBOhm, peak magnitude dB) for VOUT."""
    _, mag_db, _ = result.bode("VOUT")
    return float(mag_db[0]), float(np.max(mag_db))


def test_gbw_tia_passband_and_finite_bandwidth():
    """Well-compensated (Cf=1.5 pF): ~100 dBOhm passband, a finite MHz-range -3 dB."""
    result = _sweep("1.5pF")
    assert result.passband_gain_db("VOUT") == pytest.approx(100.0, abs=0.5)
    fc = result.cutoff_frequency("VOUT")
    assert fc is not None, "GBW-limited TIA must roll off (finite bandwidth)"
    # ADA4817 GBW + Rf*Cf + Cd give a -3 dB corner near 1.5 MHz; keep a loose window.
    assert 1.0e6 < fc < 2.5e6, f"cutoff {fc:.0f} Hz outside expected 1.0-2.5 MHz"


def test_gbw_tia_peaks_without_cf():
    """Cf removed: Cd noise-gain peaks against the finite loop bandwidth (a big bump).

    This is the whole point of the macromodel: an under-compensated TIA rings. The
    peak sits well above the 100 dBOhm passband (theory: tens of dB), somewhere in
    ~0.5-5 MHz. An ideal op-amp cannot produce this (see the guard test below).
    """
    dc, peak = _dc_and_peak(_sweep("0.01pF"))
    assert dc == pytest.approx(100.0, abs=1.0), f"DC transimpedance {dc:.1f} dBOhm"
    assert peak - dc > 3.0, f"expected gain peaking, got only {peak - dc:.2f} dB bump"


def test_ideal_opamp_cannot_peak():
    """Guard: with the ideal op-amp the same Cf-less TIA stays flat (no peaking).

    Confirms the bump in the previous test comes from the GBW pole, not the topology.
    """
    dc, peak = _dc_and_peak(_sweep("0.01pF", gbw=None))
    assert peak - dc < 0.5, f"ideal op-amp should not peak, saw {peak - dc:.2f} dB"
