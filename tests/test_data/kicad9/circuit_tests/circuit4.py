#!/usr/bin/env python3
"""
circuit4.py

Demonstrates repeated subcircuits:
 - Subcircuit 'low_pass_filter' with R + C to ground.
 - A parent circuit 'stereo_filter_circuit' that instantiates two copies
   of low_pass_filter (left & right channels).
"""

import logging

from circuit_synth import *

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@circuit(name="low_pass_filter")
def low_pass_filter(sig_in, sig_out, gnd):
    """
    A simple RC low-pass filter:
      (sig_in) ---[R=10k]---+---(sig_out)
                            |
                           [C=100nF]
                            |
                           (gnd)
    """
    r_filter = Component(
        symbol="Device:R", ref="R", value="10k", footprint="Resistor_SMD:R_0805"
    )
    c_filter = Component(
        symbol="Device:C", ref="C", value="100nF", footprint="Capacitor_SMD:C_0805"
    )

    # R from sig_in -> filter node
    filter_node = Net("FILTER_NODE")
    r_filter[1] += sig_in
    r_filter[2] += filter_node

    # C from filter node -> GND
    c_filter[1] += filter_node
    c_filter[2] += gnd

    # The filter node is also the output
    sig_out += filter_node


@circuit(name="stereo_filter_circuit")
def stereo_filter_circuit():
    """
    Parent circuit that instantiates 'low_pass_filter' twice:
      - Once for left channel
      - Once for right channel

    This tests repeated subcircuits and checks that references
    remain unique (e.g., R1, R2 in the first instance, R3, R4 in the second).
    """
    gnd = Net("GND")

    # Left channel nets
    left_in = Net("LEFT_IN")
    left_out = Net("LEFT_OUT")

    # Right channel nets
    right_in = Net("RIGHT_IN")
    right_out = Net("RIGHT_OUT")

    # Instantiate subcircuit #1 (left channel)
    low_pass_filter(left_in, left_out, gnd)

    # Instantiate subcircuit #2 (right channel)
    low_pass_filter(right_in, right_out, gnd)


if __name__ == "__main__":
    c = stereo_filter_circuit()

    netlist_text = c.generate_text_netlist()
    print("=== TEXT NETLIST ===")
    print(netlist_text)

    output_file = "circuit4.json"
    c.generate_json_netlist(output_file)
    logger.info(f"JSON netlist saved to {output_file}")
