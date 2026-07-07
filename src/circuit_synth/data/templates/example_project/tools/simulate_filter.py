#!/usr/bin/env python3
"""Known-good AC-sweep simulation reference for circuit-synth.

Usage:
    uv run python tools/simulate_filter.py

Builds a first-order INVERTING active low-pass filter (R1=RF=10k, CF=1.5915n ->
fc ~= 10 kHz, passband gain = 1 / 0 dB), runs an AC sweep through circuit-synth's
simulator, and prints the passband gain, -3 dB cutoff frequency, and high-frequency
roll-off, then exits 0 on success. Copy this pattern to characterize your own
frequency-domain circuit: declare a ``Simulation_SPICE:VSIN`` source (it carries an
AC magnitude of 1 V, so the output node *is* the transfer function), build the
``@circuit``, call ``circuit.simulate().ac_analysis(start_hz, stop_hz, points)``,
then read ``.cutoff_frequency("NET")`` / ``.passband_gain_db("NET")`` / ``.bode("NET")``.

Declare the input as ``Simulation_SPICE:VSIN`` (NOT the fictitious ``Device:V`` --
that is not a real KiCad symbol) for AC/transient stimulus, or
``Simulation_SPICE:VDC`` for a DC supply.

Backend: on Windows the ngspice DLL bundled with KiCad is auto-configured, so no
separate ngspice install is needed. If PySpice or ngspice is unavailable the
script prints ``SIMULATION_UNAVAILABLE: <reason>`` and exits 2 (not a crash), so
callers can degrade gracefully.
"""

import sys

from circuit_synth import Component, Net, circuit

FC_HZ = 10_000.0  # design target: 1/(2*pi*RF*CF)


@circuit(name="Opamp_LowPass_Filter_Sim")
def lowpass_filter():
    """First-order inverting active LPF. R1=RF=10k, CF=1.5915n -> fc ~= 10 kHz.

    VSIN drives VIN with AC magnitude 1 V; the inverting node (NINV) is shared by
    R1, the RF||CF feedback, and the op-amp inverting input; the non-inverting
    input is grounded. LM358 unit A pinout: 1=out, 2=in-, 3=in+.
    """
    v1 = Component(symbol="Simulation_SPICE:VSIN", ref="V1", value="1V")
    r1 = Component(symbol="Device:R", ref="R1", value="10k")
    rf = Component(symbol="Device:R", ref="RF", value="10k")
    cf = Component(symbol="Device:C", ref="CF", value="1.5915nF")
    u1 = Component(symbol="Amplifier_Operational:LM358", ref="U1")

    vin = Net("VIN")
    vout = Net("VOUT")
    ninv = Net("NINV")
    gnd = Net("GND")

    v1[1] += vin
    v1[2] += gnd
    r1[1] += vin
    r1[2] += ninv
    rf[1] += ninv
    rf[2] += vout
    cf[1] += ninv
    cf[2] += vout
    u1[1] += vout
    u1[2] += ninv
    u1[3] += gnd


def main() -> int:
    c = lowpass_filter()
    try:
        sim = c.simulate()
        result = sim.ac_analysis(100, 1e6, points=50)  # 100 Hz .. 1 MHz
    except Exception as e:  # PySpice/ngspice missing or failed to load
        print(f"SIMULATION_UNAVAILABLE: {e}")
        return 2

    try:
        import numpy as np

        passband_db = result.passband_gain_db("VOUT")
        fc = result.cutoff_frequency("VOUT")
        freq, mag_db, _ = result.bode("VOUT")

        def mag_at(target):
            return mag_db[int(np.argmin(np.abs(freq - target)))]

        # Roll-off measured on the asymptote (10*fc -> 100*fc).
        rolloff = mag_at(10 * FC_HZ) - mag_at(100 * FC_HZ)
    except Exception as e:
        print(f"SIMULATION_UNAVAILABLE: {e}")
        return 2

    print(f"passband_gain_db={passband_db:.3f}")
    print(f"cutoff_hz={fc:.1f}" if fc is not None else "cutoff_hz=None")
    print(f"rolloff_db_per_decade={rolloff:.2f}")

    # Save a headless Bode PNG next to the log (returns None if matplotlib is
    # missing -- harmless). This is the pattern the design-circuit loop uses to
    # embed plots in design_log.md.
    plot_path = result.save_bode_plot("sim_plots/lowpass_filter_bode.png", "VOUT")
    if plot_path is not None:
        print(f"bode_plot={plot_path}")

    if fc is None or abs(fc - FC_HZ) / FC_HZ > 0.05:
        print(f"FAIL: cutoff {fc} Hz not within 5% of {FC_HZ} Hz")
        return 1
    print(
        f"OK: fc={fc:.1f} Hz (target {FC_HZ:.0f} Hz), gain={passband_db:.2f} dB, "
        f"roll-off={rolloff:.1f} dB/decade"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
