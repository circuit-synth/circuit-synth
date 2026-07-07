#!/usr/bin/env python3
"""Minimal two-sheet (hierarchical) circuit-synth reference.

Usage:
    uv run python tools/hierarchical_example.py

Demonstrates the multi-sheet pattern: one ``@circuit`` function per functional
block, and a top ``@circuit`` that creates the *shared* nets and passes the
same ``Net`` objects into each block. circuit-synth generates one
``.kicad_sch`` per block plus the root; a net shared between two blocks (here
``V5``) becomes a **sheet pin** on each, while power nets (``GND``) use global
power symbols.

Two blocks:
  * ``psu``  -- a 9 V source and an R1/R2 divider producing the ``V5`` rail.
  * ``load`` -- a resistive load across ``V5``.
``V5`` and ``GND`` are shared by passing the same Net objects into both blocks.

Not wired into ``main.py`` -- it is a standalone example. Simulation flattens
the hierarchy automatically, so ``top().simulate().operating_point()`` would
read ``V5`` by net name just like a flat circuit.
"""

import sys

from circuit_synth import Component, Net, circuit


@circuit(name="psu")
def psu(vin_9v, v5, gnd):
    """9 V in, ~5 V out via an R1/R2 divider (illustrative, not regulated)."""
    vsrc = Component(symbol="Simulation_SPICE:VDC", ref="V", value="9V")
    r1 = Component(symbol="Device:R", ref="R", value="800")
    r2 = Component(symbol="Device:R", ref="R", value="1k")
    vsrc[1] += vin_9v
    vsrc[2] += gnd
    r1[1] += vin_9v
    r1[2] += v5
    r2[1] += v5
    r2[2] += gnd


@circuit(name="load")
def load(v5, gnd):
    """A resistive load across the shared 5 V rail."""
    rload = Component(symbol="Device:R", ref="R", value="10k")
    rload[1] += v5
    rload[2] += gnd


@circuit(name="hierarchical_example")
def top():
    vin_9v = Net("VIN_9V")
    v5 = Net("V5")  # shared between psu and load -> becomes a sheet pin on each
    gnd = Net("GND")  # power net -> global power symbol, not a sheet pin
    psu(vin_9v, v5, gnd)
    load(v5, gnd)


def main() -> int:
    c = top()
    result = c.generate_kicad_project(
        project_name="hierarchical_example", generate_pcb=False
    )
    ok = bool(result.get("success"))
    print("OK: generated multi-sheet project" if ok else "FAIL: generation failed")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
