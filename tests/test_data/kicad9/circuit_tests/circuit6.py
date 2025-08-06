#!/usr/bin/env python3
"""
circuit6.py

Demonstrates net name mismatch & merging:
 - A subcircuit named 'oscillator_subcircuit' with parameters (x_in, x_out, gnd).
 - A top-level circuit 'net_name_mismatch_circuit' that calls
   oscillator_subcircuit(CRYSTAL_IN, CRYSTAL_OUT, GND).

We confirm that in the final JSON, the child subcircuit's net references
are updated to match the parent's net names (CRYSTAL_IN, CRYSTAL_OUT, GND).
"""
import logging

from circuit_synth import *

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@circuit(name="oscillator_subcircuit")
def oscillator_subcircuit(x_in, x_out, gnd):
    """
    Subcircuit that expects:
      x_in -- an input net
      x_out -- an output net
      gnd -- ground reference

    We'll pretend it's a simple crystal oscillator arrangement,
    but for simplicity, just a resistor + capacitor forming feedback.
    """
    # A resistor from x_in to x_out
    r_osc = Component(
        symbol="Device:R", ref="R", value="1Meg", footprint="Resistor_SMD:R_0805"
    )
    r_osc[1] += x_in
    r_osc[2] += x_out

    # A capacitor from x_out to gnd
    c_osc = Component(
        symbol="Device:C", ref="C", value="20pF", footprint="Capacitor_SMD:C_0805"
    )
    c_osc[1] += x_out
    c_osc[2] += gnd


@circuit(name="net_name_mismatch_circuit")
def net_name_mismatch_circuit():
    """
    The parent circuit calls oscillator_subcircuit with
    parent-level nets: CRYSTAL_IN, CRYSTAL_OUT, GND.

    This tests that the child's x_in/x_out nets properly merge into
    CRYSTAL_IN/CRYSTAL_OUT in the final JSON.
    """
    crystal_in = Net("CRYSTAL_IN")
    crystal_out = Net("CRYSTAL_OUT")
    ground = Net("GND")  # We'll keep this the standard GND

    # Instantiate subcircuit:
    #    child param: x_in   -> parent net: CRYSTAL_IN
    #    child param: x_out  -> parent net: CRYSTAL_OUT
    #    child param: gnd    -> parent net: GND
    oscillator_subcircuit(crystal_in, crystal_out, ground)


if __name__ == "__main__":
    c = net_name_mismatch_circuit()

    # Print out a text netlist (optional for debugging)
    netlist_text = c.generate_text_netlist()
    print("=== TEXT NETLIST ===")
    print(netlist_text)

    # Generate the JSON netlist
    output_file = "circuit6.json"
    c.generate_json_netlist(output_file)
    logger.info(f"JSON netlist saved to {output_file}")
