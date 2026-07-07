#!/usr/bin/env python3
"""Known-good SPICE simulation reference for circuit-synth.

Usage:
    uv run python tools/simulate_example.py

Builds a 5V -> 3.333V resistor divider, runs a DC operating-point analysis
through circuit-synth's simulator, and prints one ``NODE=VALUE`` line per node
(volts), then exits 0 on success. Copy this pattern to simulate your own
``@circuit`` function: build it, call ``circuit.simulate()``, then
``.operating_point()`` and ``.get_voltage("NET_NAME")``.

Backend: on Windows the ngspice DLL bundled with KiCad is auto-configured, so
no separate ngspice install is needed. If PySpice or ngspice is unavailable the
script prints ``SIMULATION_UNAVAILABLE: <reason>`` and exits 2 (not a crash), so
callers can degrade gracefully.
"""
import sys

from circuit_synth import Component, Net, circuit


@circuit(name="Resistor_Divider_Sim")
def divider():
    """R1=1k (VIN_5V->VOUT_3V3), R2=2k (VOUT_3V3->GND). Vout = 5 * 2/3 = 3.333 V."""
    r1 = Component(symbol="Device:R", ref="R1", value="1k")
    r2 = Component(symbol="Device:R", ref="R2", value="2k")
    vin_5v = Net("VIN_5V")
    vout_3v3 = Net("VOUT_3V3")
    gnd = Net("GND")
    r1[1] += vin_5v
    r1[2] += vout_3v3
    r2[1] += vout_3v3
    r2[2] += gnd


def main() -> int:
    c = divider()
    try:
        sim = c.simulate()
        result = sim.operating_point()
    except Exception as e:  # PySpice/ngspice missing or failed to load
        print(f"SIMULATION_UNAVAILABLE: {e}")
        return 2

    # Print NODE=VALUE for the divider's named nets (ngspice is case-insensitive).
    for node in ("VIN_5V", "VOUT_3V3"):
        try:
            print(f"{node}={result.get_voltage(node):.4f}")
        except KeyError:
            print(f"{node}=NaN")

    vout = result.get_voltage("VOUT_3V3")
    expected = 10 / 3
    if abs(vout - expected) > 0.01:
        print(f"FAIL: VOUT_3V3={vout:.4f} V, expected {expected:.4f} V")
        return 1
    print(f"OK: VOUT_3V3={vout:.4f} V (expected {expected:.4f} V)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
