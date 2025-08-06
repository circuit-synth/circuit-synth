#!/usr/bin/env python3
"""
circuit2.py

Defines two circuits:
  (1) resistor_divider_child(...)  - a subcircuit for a resistor divider
  (2) regulator_circuit(...)       - top-level circuit that includes the
                                     resistor divider as a child and hooks
                                     its output to a simple regulator.
"""
import logging

from circuit_synth import *

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@circuit(name="resistor_divider_child")
def resistor_divider_child(VIN, VMEAS, GND):
    """
    A standalone resistor divider subcircuit.
      VIN ---[R1=10k]---+---[R2=5k]--- GND
                       |
                      VMEAS

    The parent circuit must provide VIN, VMEAS, GND nets.
    """
    r1 = Component(
        symbol="Device:R", ref="R", value="10k", footprint="Resistor_SMD:R_0805"
    )

    r2 = Component(
        symbol="Device:R", ref="R", value="5k", footprint="Resistor_SMD:R_0805"
    )

    # Top resistor: VIN -> (divider node = VMEAS)
    r1[1] += VIN
    r1[2] += VMEAS

    # Bottom resistor: VMEAS -> GND
    r2[1] += VMEAS
    r2[2] += GND


@circuit(name="regulator_circuit")
def regulator_circuit():
    """
    Top-level circuit that instantiates the resistor divider as a child,
    then attaches the divider's top node to the regulator input.

     5V_SUPPLY --- resistor_divider_child(...) --> node: DIV_OUT
       DIV_OUT -> [ Regulator Input ]
       GND
       Regulator Output -> REG_3V3
    """

    # Define the main nets in this top-level circuit
    supply_5v = Net("SUPPLY_5V")
    div_out = Net("DIV_OUT")  # The midpoint from the child resistor divider
    gnd = Net("GND")
    reg_3v3 = Net("REG_3V3")  # The regulator's output

    # Instantiate the child resistor divider circuit
    # Top resistor node is supply_5v, midpoint is div_out, bottom is gnd
    resistor_divider_child(supply_5v, div_out, gnd)

    # Define a simple regulator with no bypass caps
    # (Pin1=GND, Pin2=VOUT, Pin3=VIN on many linear regulators)
    regulator = Component(
        symbol="Regulator_Linear:NCP1117-3.3_SOT223",
        ref="U1",
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2",
    )
    regulator[1] += gnd  # GND
    regulator[2] += reg_3v3  # Regulator output net
    regulator[3] += supply_5v  # Input from the resistor divider


if __name__ == "__main__":
    c = regulator_circuit()

    # Text netlist
    netlist_text = c.generate_text_netlist()
    print("=== TEXT NETLIST ===")
    print(netlist_text)

    # JSON netlist
    output_file = "circuit2.json"
    c.generate_json_netlist(output_file)
    logger.info(f"JSON netlist saved to {output_file}")
