#!/usr/bin/env python3
"""
circuit3.py

Demonstrates a multi-level hierarchy:
 - Grandchild: opamp_stage (an op amp + feedback resistor)
 - Child: active_filter_child (uses opamp_stage + R/C filter)
 - Parent: multi_level_circuit (instantiates active_filter_child)

We will produce a JSON netlist showing:
 - Top level subcircuit: active_filter_child
 - Inside that child, a subcircuit: opamp_stage
"""

import logging

from circuit_synth import *

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@circuit(name="opamp_stage")
def opamp_stage(signal_in, signal_out, gnd):
    """
    Grandchild subcircuit: a simple unity-gain buffer op amp stage.
      - Negative input tied to output
      - Positive input is signal_in
      - Output is signal_out
      - Single supply op amp with GND as reference
    """

    # Example op amp symbol; adjust as needed for your KiCad libraries
    op_amp = Component(
        symbol="Amplifier_Operational:TL081",
        ref="U",
        footprint="Package_DIP:DIP-8_W7.62mm",
    )
    # Suppose pin 3 is non-inverting (+), pin 2 is inverting (-), pin 6 is output, pin 4=V-, pin 7=V+ in some library
    # We'll tie V+ to some higher supply if you like, but here we just show GND for simplicity
    # For a real design, you'd typically have two rails or a single supply net. We'll connect V- to GND and skip V+.

    # Positive input => signal_in
    op_amp[3] += signal_in

    # Output => signal_out
    op_amp[6] += signal_out

    # Negative input => feedback from the output
    op_amp[2] += signal_out

    # V- (pin 4) => GND
    op_amp[4] += gnd

    # We'll leave pin 7 unconnected or also tied to gnd if we want single-supply.
    # For demonstration, let's just tie it to gnd as well:
    op_amp[7] += gnd

    # Optionally, a feedback resistor from output -> inverting input (but we're already shorted)
    # This is a unity buffer, so we can omit the explicit resistor, or place a placeholder if needed.


@circuit(name="active_filter_child")
def active_filter_child(sig_in, sig_out, gnd):
    """
    Child subcircuit: RC low-pass filter + an op amp buffer stage inside.
      - R and C create a filter node
      - That node feeds into the opamp_stage grandchild
      - The child circuit has its own subcircuit list = [opamp_stage(...)]

    The parent circuit passes sig_in, sig_out, gnd.
    We'll keep a local node filter_node for the R/C connection.
    """

    filter_node = Net("FILTER_NODE")

    # R from input to filter_node
    r_filter = Component(
        symbol="Device:R", ref="R", value="10k", footprint="Resistor_SMD:R_0805"
    )
    r_filter[1] += sig_in
    r_filter[2] += filter_node

    # C from filter_node to ground
    c_filter = Component(
        symbol="Device:C", ref="C", value="0.1uF", footprint="Capacitor_SMD:C_0805"
    )
    c_filter[1] += filter_node
    c_filter[2] += gnd

    # Instantiate the grandchild op amp stage
    opamp_stage(filter_node, sig_out, gnd)


@circuit(name="multi_level_circuit")
def multi_level_circuit():
    """
    Parent circuit:
      - Provides 'audio_in', 'audio_out', 'gnd'
      - Instantiates active_filter_child(...)
        which internally calls opamp_stage(...)
    """

    audio_in = Net("AUDIO_IN")
    audio_out = Net("AUDIO_OUT")
    gnd = Net("GND")

    # Now place the child subcircuit
    active_filter_child(audio_in, audio_out, gnd)


if __name__ == "__main__":
    c = multi_level_circuit()

    netlist_text = c.generate_text_netlist()
    print("=== TEXT NETLIST ===")
    print(netlist_text)

    # Generate JSON netlist
    output_file = "circuit3.json"
    c.generate_json_netlist(output_file)
    logger.info(f"JSON netlist saved to {output_file}")
