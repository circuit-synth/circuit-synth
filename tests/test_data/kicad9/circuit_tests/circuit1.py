#!/usr/bin/env python3
import logging

from circuit_synth import *

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@circuit
def resistor_divider():
    """
    A simple resistor divider:
      VIN ---[R1=10k]---+---[R2=5k]--- GND
                       |
                      VMEAS
    """
    vin = Net("VIN")
    vmeas = Net("MEAS")
    gnd = Net("GND")

    r1 = Component(
        symbol="Device:R",  # KiCad symbol
        ref="R",  # Let the circuit auto-assign final references
        value="10k",
        footprint="Resistor_SMD:R_0805",
    )

    r2 = Component(
        symbol="Device:R", ref="R", value="5k", footprint="Resistor_SMD:R_0805"
    )

    # Connect the resistor pins
    r1[1] += vin
    r1[2] += vmeas
    r2[1] += vmeas
    r2[2] += gnd


if __name__ == "__main__":
    c = resistor_divider()

    netlist_text = c.generate_text_netlist()
    print("=== TEXT NETLIST ===")
    print(netlist_text)

    output_file = "circuit1.json"
    c.generate_json_netlist(output_file)
    logger.info(f"JSON netlist saved to {output_file}")
