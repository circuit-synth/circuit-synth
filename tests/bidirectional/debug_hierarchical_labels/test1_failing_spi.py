#!/usr/bin/env python3
"""
Test 1: Copy of failing Test 59 fixture (spi_subcircuit.py)

This test currently fails with:
  CircuitSynthError: Cannot create Net('DATA_IN'): No active circuit found.

This is the existing broken test case that demonstrates Issue #427.
"""

from circuit_synth import Circuit, Component, Net, circuit


@circuit
def main():
    # Create root (parent) circuit
    root = Circuit("spi_subcircuit")

    # Create data net in parent (will be renamed DATA_IN → SPI_MOSI)
    data_in = Net("DATA_IN")

    # Create SPI_Driver subcircuit (child circuit)
    spi_driver = Circuit("SPI_Driver")

    # Add resistor in subcircuit that connects to data input
    resistor = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    spi_driver.add_component(resistor)

    # Connect resistor to data net
    # Since data_in is from parent and resistor is in subcircuit,
    # this should create hierarchical label in subcircuit
    resistor[1] += data_in  # R1 pin 1 to DATA_IN (hierarchical label)

    # Add subcircuit to root circuit
    # The net connection should automatically create hierarchical labels
    root.add_subcircuit(spi_driver)

    # Generate KiCad project
    print(f"Generating KiCad project: spi_subcircuit")
    print(f"  Parent circuit: {root.name}")
    print(f"  Subcircuit: {spi_driver.name}")
    print(f"  Hierarchical port: DATA_IN")
    print(f"  Components in subcircuit: R1 (resistor)")

    root.generate_kicad_project("test1_spi_output", force_regenerate=True)

    print(f"\n✅ Project generated successfully!")
    print(f"   Expected hierarchical structure:")
    print(f"   - Parent: spi_subcircuit.kicad_sch (with sheet symbol)")
    print(f"   - Subcircuit: SPI_Driver.kicad_sch (with hierarchical label)")
    print(f"   - Sheet symbol should have pin: DATA_IN")
    print(f"   - Subcircuit should have hierarchical label: DATA_IN")


if __name__ == "__main__":
    main()
