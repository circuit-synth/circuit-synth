#!/usr/bin/env python3
"""
Fixture: SPI bus connecting multiple peer subcircuits using global labels.

Demonstrates flat multi-sheet design (NO hierarchy) where peer subcircuits
share signals via global labels:
- Main sheet: MCU with SPI master
- Display sheet: Display controller (peer sheet)
- Sensor sheet: Sensor module (peer sheet) - COMMENTED OUT for test expansion

All sheets are peers (same level), connected via global labels (not hierarchical).

This tests whether circuit-synth supports global labels for cross-sheet
connectivity without parent-child hierarchy.
"""

from circuit_synth import circuit, Component, Circuit, Net


@circuit(name="spi_bus")
def spi_bus():
    """Multi-sheet circuit with global labels connecting peer subcircuits.

    Architecture:
    - Main sheet (root): MCU with SPI master
    - Display sheet (peer): Display controller
    - Sensor sheet (peer): Sensor module (initially commented out)

    Global labels "SPI_CLK", "SPI_MOSI", "SPI_MISO" should connect all sheets.
    """
    from circuit_synth.core.decorators import get_current_circuit

    root = get_current_circuit()

    # =========================================================================
    # Main Sheet (Root): MCU with SPI Master
    # =========================================================================
    mcu = Component(
        symbol="MCU_ST_STM32F1:STM32F103C8Tx",
        ref="U1",
        value="STM32F103C8T6",
        footprint="Package_QFP:LQFP-48_7x7mm_P0.5mm",
    )

    # Create global label nets for SPI bus
    # These should appear as global_label objects in KiCad (not hierarchical_label)
    spi_clk = Net("SPI_CLK")
    spi_mosi = Net("SPI_MOSI")
    spi_miso = Net("SPI_MISO")

    # Connect MCU SPI pins to global labels
    # STM32F103C8T6 SPI1: PA5=CLK, PA6=MISO, PA7=MOSI
    mcu["PA5"] += spi_clk   # SPI1_CLK
    mcu["PA6"] += spi_miso  # SPI1_MISO
    mcu["PA7"] += spi_mosi  # SPI1_MOSI

    # =========================================================================
    # Display Sheet (Peer Subcircuit 1)
    # =========================================================================
    display_sheet = Circuit("DisplaySheet")

    display = Component(
        symbol="Device:R",  # Simplified - using resistor as placeholder
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    display_sheet.add_component(display)

    # Connect display to same global label nets
    # In real design, these would be display controller SPI pins
    display[1] += spi_clk   # Display CLK pin
    display[2] += spi_mosi  # Display MOSI pin

    # Add display sheet as PEER (not parent-child hierarchy)
    root.add_subcircuit(display_sheet)

    # =========================================================================
    # Sensor Sheet (Peer Subcircuit 2) - COMMENTED OUT
    # Test will uncomment this to validate expansion
    # =========================================================================
    # sensor_sheet = Circuit("SensorSheet")
    #
    # sensor = Component(
    #     symbol="Device:R",  # Simplified - using resistor as placeholder
    #     ref="R2",
    #     value="4.7k",
    #     footprint="Resistor_SMD:R_0603_1608Metric",
    # )
    #
    # sensor_sheet.add_component(sensor)
    #
    # # Connect sensor to same global label nets
    # sensor[1] += spi_clk   # Sensor CLK pin
    # sensor[2] += spi_miso  # Sensor MISO pin
    #
    # # Add sensor sheet as PEER (not parent-child hierarchy)
    # root.add_subcircuit(sensor_sheet)


if __name__ == "__main__":
    # Generate KiCad project when run directly
    circuit_obj = spi_bus()

    circuit_obj.generate_kicad_project(
        project_name="spi_bus",
        placement_algorithm="simple",
        generate_pcb=True,
    )

    print("✅ SPI bus multi-sheet circuit generated successfully!")
    print("📁 Open in KiCad: spi_bus/spi_bus.kicad_pro")
    print("")
    print("🔍 Validation checks:")
    print("   1. Multiple .kicad_sch files (one per sheet)")
    print("   2. Global labels in each sheet (circle/globe visual)")
    print("   3. NO hierarchical sheet symbols (peer sheets)")
    print("   4. Netlist shows cross-sheet SPI_CLK connectivity")
    print("")
    print("⚠️  Expected behavior:")
    print("   - If circuit-synth supports global labels: PASS")
    print("   - If circuit-synth uses hierarchical labels: XFAIL")
