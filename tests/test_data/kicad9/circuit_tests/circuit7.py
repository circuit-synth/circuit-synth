#!/usr/bin/env python3
"""
circuit7.py

Demonstrates pin-type edge cases:
  - An op amp symbol (TL081) which includes an NC pin (pin 8).
  - Power pins V+ and V-, connected to nets 12V and GND.
  - A no-connect pin is left unconnected and should appear
    as "pin_id": 8 with "func": "no_connect" in the JSON.

We verify that:
  - The NC pin remains unconnected.
  - Power pins appear in nets as usual.
  - Normal I/O pins can be connected or left out.
"""
import logging

from circuit_synth import *

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@circuit(name="pin_edge_cases_circuit")
def pin_edge_cases_circuit():
    """
    A top-level circuit with an op amp that has:
      - NC pin
      - Power pins
      - Input/Output pins

    We'll connect V+ to 12V, V- to GND,
    and leave the NC pin floating.
    """
    # Define nets
    rail_12v = Net("12V")
    gnd = Net("GND")
    output_net = Net("OUT")  # For demonstration

    # Place the op amp
    # According to the typical TL081 pin definitions:
    #   1 = NULL offset, 2 = -, 3 = +,
    #   4 = V-, 5 = NULL offset, 6 = output,
    #   7 = V+, 8 = NC
    op_amp = Component(
        symbol="Amplifier_Operational:TL081",
        ref="U1",
        footprint="Package_DIP:DIP-8_W7.62mm",
    )

    # Connect power pins
    op_amp[4] += gnd  # V-
    op_amp[7] += rail_12v  # V+

    # Connect the output
    op_amp[6] += output_net

    # Let’s leave pin 8 (NC) unconnected
    # We do nothing with it here.

    # We could optionally connect the input pins if needed,
    # but let's leave them unconnected for demonstration.
    # That will allow us to see how they appear in JSON.


if __name__ == "__main__":
    c = pin_edge_cases_circuit()

    # Print a text netlist (optional for debugging)
    netlist_text = c.generate_text_netlist()
    print("=== TEXT NETLIST ===")
    print(netlist_text)

    # Generate the JSON netlist
    output_file = "circuit7.json"
    c.generate_json_netlist(output_file)
    logger.info(f"JSON netlist saved to {output_file}")
