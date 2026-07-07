#!/usr/bin/env python3
"""Optional pretty-rendering of a circuit-synth design via SKiDL (Stage 13).

Usage:
    # 1) one-time setup of a SKiDL-capable interpreter (see the plan/README):
    #    uv venv .venv-skidl --python 3.13
    #    uv pip install --python .venv-skidl/Scripts/python.exe skidl
    # 2) point circuit-synth at it and render:
    CIRCUIT_SYNTH_SKIDL_PYTHON=.venv-skidl/Scripts/python.exe \\
        uv run python tools/render_skidl.py

circuit-synth places components on a grid and connects them with labels. SKiDL has
a force-directed placer + maze router that produces ``.kicad_sch`` files with real
*routed wires*. This tool converts a circuit-synth ``@circuit`` into a SKiDL script
and runs it, writing a wire-routed render into ``skidl_render/``.

The circuit-synth ``.kicad_sch`` remains authoritative (it is what the edit/preserve
loop and simulation operate on); the SKiDL output is a human-readable *view* and is
electrically identical (same net connectivity).

Backend: the render runs in a *separate* interpreter (named by
``CIRCUIT_SYNTH_SKIDL_PYTHON``, else the current Python) that can ``import skidl``.
If skidl is not available there, this prints ``SKIDL_UNAVAILABLE: <reason>`` and
exits 2 (not a crash), so callers can degrade gracefully.

Copy this pattern for your own design: import your ``@circuit`` function, build it,
then call ``render_with_skidl(circuit, out_dir="skidl_render")``.
"""

import sys
from pathlib import Path

from circuit_synth import Component, Net, circuit
from circuit_synth.interop import render_with_skidl
from circuit_synth.interop.skidl_export import SkidlRenderError


@circuit(name="Resistor_Divider_Render")
def divider():
    """R1=1k (VIN_5V->VOUT_3V3), R2=2k (VOUT_3V3->GND)."""
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="1k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )
    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="2k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )
    vin_5v = Net("VIN_5V")
    vout_3v3 = Net("VOUT_3V3")
    gnd = Net("GND")
    r1[1] += vin_5v
    r1[2] += vout_3v3
    r2[1] += vout_3v3
    r2[2] += gnd


def main() -> int:
    c = divider()
    out_dir = Path("skidl_render")
    try:
        top = render_with_skidl(c, out_dir)
    except SkidlRenderError as e:
        print(f"SKIDL_UNAVAILABLE: {e}")
        return 2

    print(f"OK: wrote wire-routed render to {top}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
