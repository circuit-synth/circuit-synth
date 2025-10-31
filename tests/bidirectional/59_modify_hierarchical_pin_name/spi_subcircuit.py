#!/usr/bin/env python3
"""
SPI subcircuit test fixture for hierarchical pin renaming.

Demonstrates hierarchical pin connection that will be renamed:
- Parent circuit has DATA_IN net (later renamed to SPI_MOSI)
- SPI_Driver subcircuit requires DATA_IN via hierarchical port
- Hierarchical label in subcircuit connects to sheet pin in parent

This fixture is modified by the test to rename the hierarchical pin
from generic "DATA_IN" to specific "SPI_MOSI".
"""

from circuit_synth import *


@circuit
def spi_driver_subcircuit(data_in: Net):
    """SPI Driver subcircuit with hierarchical DATA_IN connection."""
    # Add resistor in subcircuit that connects to data input
    resistor = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # Connect resistor to hierarchical port (DATA_IN)
    # This will create hierarchical label in subcircuit
    resistor[1] += data_in  # R1 pin 1 to DATA_IN (hierarchical label)


@circuit(name="spi_subcircuit")
def main():
    """Root circuit with SPI driver subcircuit."""
    # Create data net in parent (will be renamed DATA_IN → SPI_MOSI)
    data_in = Net("DATA_IN")

    # START_MARKER: Test will modify pin name between these markers
    # END_MARKER

    # Call subcircuit - creates hierarchical sheet
    # This creates:
    # 1. Hierarchical label "DATA_IN" in spi_driver_subcircuit.kicad_sch
    # 2. Sheet symbol in parent with hierarchical pin "DATA_IN"
    # 3. Connection between parent data_in net and sheet pin
    spi_driver_subcircuit(data_in)

    print(f"Generating KiCad project: spi_subcircuit")
    print(f"  Hierarchical port: DATA_IN (will be renamed to SPI_MOSI)")
    print(f"  Components in subcircuit: R1 (resistor)")
    print(f"\n✅ Project generated successfully!")
    print(f"   Expected hierarchical structure:")
    print(f"   - Parent: spi_subcircuit.kicad_sch (with sheet symbol)")
    print(
        f"   - Subcircuit: spi_driver_subcircuit_1.kicad_sch (with hierarchical label)"
    )
    print(f"   - Sheet symbol should have pin: DATA_IN")
    print(f"   - Subcircuit should have hierarchical label: DATA_IN")


if __name__ == "__main__":
    circuit_obj = main()
    circuit_obj.generate_kicad_project(project_name="spi_subcircuit")
