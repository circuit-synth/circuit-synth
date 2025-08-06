#!/usr/bin/env python3
"""
circuit5.py

Demonstrates user-assigned references without collisions, so we can
focus on JSON output rather than collision exceptions.

We force references in both the top-level circuit and a child subcircuit,
but choose distinct names to avoid collisions.
"""

import logging

from circuit_synth import *

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@circuit(name="child_amp_stage")
def child_amp_stage(sig_in, sig_out, gnd):
    """
    Child subcircuit that uses forced references U11 and R11
    (no collision with the parent's references).
    """
    op_amp = Component(
        symbol="Amplifier_Operational:TL081",
        ref="U11",  # forced user reference, distinct from parent's
        footprint="Package_DIP:DIP-8_W7.62mm",
    )
    resistor = Component(
        symbol="Device:R", ref="R11", value="1k", footprint="Resistor_SMD:R_0805"
    )

    # Simple unity-buffer style connection
    op_amp[3] += sig_in  # + input
    op_amp[2] += sig_out  # - input
    op_amp[6] += sig_out  # output
    op_amp[4] += gnd  # V-
    op_amp[7] += gnd  # V+ (for single-rail example)

    resistor[1] += sig_out
    resistor[2] += op_amp[2]  # feedback to inverting input


@circuit(name="user_refs_circuit")
def user_refs_circuit():
    """
    Parent circuit with forced references U10 and R10.
    Instantiates the child_amp_stage, which uses U11 and R11.
    No collisions => We can confirm references in the JSON output.
    """
    vin = Net("VIN")
    vout = Net("VOUT")
    gnd = Net("GND")

    # Top-level forced references
    main_amp = Component(
        symbol="Amplifier_Operational:TL081",
        ref="U10",
        footprint="Package_DIP:DIP-8_W7.62mm",
    )
    main_res = Component(
        symbol="Device:R", ref="R10", value="10k", footprint="Resistor_SMD:R_0805"
    )

    # Wire up a quick buffer
    main_amp[3] += vin
    main_amp[2] += vout
    main_amp[6] += vout
    main_amp[4] += gnd
    main_amp[7] += gnd

    main_res[1] += vout
    main_res[2] += main_amp[2]

    # Now instantiate the child subcircuit with forced references U11, R11
    child_amp_stage(vout, Net("CHILD_OUT"), gnd)


if __name__ == "__main__":
    c = user_refs_circuit()

    netlist_text = c.generate_text_netlist()
    print("=== TEXT NETLIST ===")
    print(netlist_text)

    output_file = "circuit5.json"
    c.generate_json_netlist(output_file)
    logger.info(f"JSON netlist saved to {output_file}")
