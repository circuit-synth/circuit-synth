#!/usr/bin/env python3
"""
circuit8.py

Demonstrates dictionary of nets usage:
 - A top-level circuit "net_dict_example_circuit" with an SPI dictionary of 4 nets.
 - A subcircuit "spi_peripheral" that expects an SPI dictionary of nets.
 - We map dictionary keys to MISO, MOSI, SCK, CS.

We produce circuit8.json and confirm that each net is properly named
in the final JSON, and the subcircuit references them correctly.
"""
import logging

from circuit_synth import *

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@circuit(name="spi_peripheral")
def spi_peripheral(spi_nets, gnd):
    """
    A simple SPI peripheral subcircuit expecting:
      spi_nets["miso"] -> MISO
      spi_nets["mosi"] -> MOSI
      spi_nets["sck"] -> SCK
      spi_nets["cs"] -> CS
    plus a GND reference for its ground pin.

    In real hardware, you'd have more pins, a power supply, etc.
    """
    # A mock "shift register" or "SPI device" symbol
    # We'll pretend pins: 1=MOSI, 2=MISO, 3=SCK, 4=CS, 5=GND, 6=Some Output
    imu = Component(
        symbol="Sensor_Motion:LSM6DSL",
        ref="U",
        footprint="Package_LGA:LGA-14_3x2.5mm_P0.5mm_LayoutBorder3x4y",
    )

    # Connect SPI nets
    imu[1] += spi_nets["miso"]  # MISO
    imu[2] += spi_nets["mosi"]  # MOSI
    imu[3] += spi_nets["sck"]  # SCK
    imu[12] += spi_nets["cs"]  # CS

    # Ground
    imu[6] += gnd

    # For demonstration, let's make pin 6 an output net
    out_net = Net("PERIPH_OUT")
    imu[4] += out_net


@circuit(name="net_dict_example_circuit")
def net_dict_example_circuit():
    """
    Top-level circuit with:
      - A dictionary of 4 SPI nets
      - A subcircuit "spi_peripheral(...)" that connects to these nets
      - We use dictionary keys "miso", "mosi", "sck", "cs" for clarity

    We'll confirm in the JSON that nets appear as 'SPI_MISO', 'SPI_MOSI', 'SPI_SCK', 'SPI_CS'
    and that the subcircuit references them properly.
    """
    gnd = Net("GND")

    # Create a dictionary of SPI nets
    spi_nets = {
        "miso": Net("SPI_MISO"),
        "mosi": Net("SPI_MOSI"),
        "sck": Net("SPI_SCK"),
        "cs": Net("SPI_CS"),
    }

    # Now instantiate the subcircuit
    spi_peripheral(spi_nets, gnd)


if __name__ == "__main__":
    c = net_dict_example_circuit()

    netlist_text = c.generate_text_netlist()
    print("=== TEXT NETLIST ===")
    print(netlist_text)

    output_file = "circuit8.json"
    c.generate_json_netlist(output_file)
    logger.info(f"JSON netlist saved to {output_file}")
