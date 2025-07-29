"""
Example: Export PCB to DSN format for Freerouting.

This example demonstrates how to use the DSN exporter to prepare
a PCB for auto-routing with Freerouting.
"""

import logging
from pathlib import Path

from circuit_synth.kicad_api.pcb import PCBBoard
from circuit_synth.kicad_api.pcb.routing import DSNExporter, export_pcb_to_dsn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def export_pcb_for_routing(pcb_file: Path) -> Path:
    """
    Export a KiCad PCB file to DSN format for auto-routing.

    Args:
        pcb_file: Path to the .kicad_pcb file

    Returns:
        Path to the generated .dsn file
    """
    # Generate DSN filename
    dsn_file = pcb_file.with_suffix(".dsn")

    logger.info(f"Exporting PCB to DSN format...")
    logger.info(f"Input: {pcb_file}")
    logger.info(f"Output: {dsn_file}")

    # Export using the convenience function
    export_pcb_to_dsn(pcb_file, dsn_file)

    logger.info("Export complete!")
    logger.info("\nNext steps:")
    logger.info("1. Open Freerouting (https://github.com/freerouting/freerouting)")
    logger.info(f"2. Load the DSN file: {dsn_file}")
    logger.info("3. Run auto-routing")
    logger.info("4. Export the routed board as .ses file")
    logger.info("5. Import the .ses file back into KiCad")

    return dsn_file


def create_example_pcb_and_export():
    """
    Create an example PCB and export it to DSN format.

    This demonstrates the complete workflow from circuit creation
    to DSN export.
    """
    logger.info("Creating example PCB...")

    # Create a new PCB
    board = PCBBoard()

    # Add components for a simple voltage divider circuit
    components = [
        # Reference, Footprint_lib, Value, X, Y, Rotation
        ("R1", "Resistor_SMD:R_0603_1608Metric", "10k", 50, 40, 0),
        ("R2", "Resistor_SMD:R_0603_1608Metric", "10k", 50, 50, 0),
        ("C1", "Capacitor_SMD:C_0603_1608Metric", "100nF", 60, 45, 90),
        (
            "J1",
            "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
            "CONN",
            40,
            45,
            0,
        ),
    ]

    for ref, footprint_lib, value, x, y, rotation in components:
        board.add_footprint(
            reference=ref,
            footprint_lib=footprint_lib,
            x=x,
            y=y,
            rotation=rotation,
            value=value,
        )

    # Define nets
    nets = [
        (1, "VIN"),
        (2, "VOUT"),
        (3, "GND"),
    ]

    for num, name in nets:
        board.pcb_data["nets"].append(board.parser.Net(num, name))

    # Connect components (assign nets to pads)
    # J1: Pin 1 = VIN, Pin 2 = VOUT, Pin 3 = GND
    j1 = board.get_footprint("J1")
    if j1 and len(j1.pads) >= 3:
        j1.pads[0].net = 1
        j1.pads[0].net_name = "VIN"
        j1.pads[1].net = 2
        j1.pads[1].net_name = "VOUT"
        j1.pads[2].net = 3
        j1.pads[2].net_name = "GND"

    # R1: Top = VIN, Bottom = VOUT
    r1 = board.get_footprint("R1")
    if r1 and len(r1.pads) >= 2:
        r1.pads[0].net = 1
        r1.pads[0].net_name = "VIN"
        r1.pads[1].net = 2
        r1.pads[1].net_name = "VOUT"

    # R2: Top = VOUT, Bottom = GND
    r2 = board.get_footprint("R2")
    if r2 and len(r2.pads) >= 2:
        r2.pads[0].net = 2
        r2.pads[0].net_name = "VOUT"
        r2.pads[1].net = 3
        r2.pads[1].net_name = "GND"

    # C1: Left = VOUT, Right = GND
    c1 = board.get_footprint("C1")
    if c1 and len(c1.pads) >= 2:
        c1.pads[0].net = 2
        c1.pads[0].net_name = "VOUT"
        c1.pads[1].net = 3
        c1.pads[1].net_name = "GND"

    # Save the PCB
    pcb_file = Path("example_output/voltage_divider.kicad_pcb")
    pcb_file.parent.mkdir(parents=True, exist_ok=True)
    board.save(pcb_file)
    logger.info(f"PCB saved to: {pcb_file}")

    # Export to DSN
    logger.info("\nExporting to DSN format...")
    exporter = DSNExporter(board)
    dsn_file = pcb_file.with_suffix(".dsn")
    exporter.export(dsn_file)

    logger.info(f"DSN file created: {dsn_file}")

    # Display some statistics
    logger.info("\nPCB Statistics:")
    logger.info(f"  Components: {len(board.pcb_data['footprints'])}")
    logger.info(f"  Nets: {len(board.pcb_data['nets']) - 1}")  # Subtract net 0
    logger.info(f"  Connections to route: {count_connections(board)}")

    return pcb_file, dsn_file


def count_connections(board: PCBBoard) -> int:
    """Count the number of connections that need routing."""
    # Count unique nets with more than one pad
    net_pads = {}

    for fp in board.pcb_data["footprints"]:
        for pad in fp.pads:
            if pad.net and pad.net > 0:
                if pad.net not in net_pads:
                    net_pads[pad.net] = 0
                net_pads[pad.net] += 1

    # Count nets with multiple connections
    connections = sum(1 for count in net_pads.values() if count > 1)
    return connections


def advanced_dsn_export_example():
    """
    Advanced example showing custom DSN export options.
    """
    logger.info("\n=== Advanced DSN Export Example ===")

    # Load an existing PCB
    board = PCBBoard()

    # Create a more complex circuit
    # ... (add components and nets as needed)

    # Create DSN exporter with custom settings
    exporter = DSNExporter(board)

    # Customize design rules before export
    exporter.DEFAULT_TRACK_WIDTH = 0.2  # 8 mil tracks
    exporter.DEFAULT_CLEARANCE = 0.15  # 6 mil clearance
    exporter.DEFAULT_VIA_SIZE = 0.6  # 24 mil vias
    exporter.DEFAULT_VIA_DRILL = 0.3  # 12 mil drill

    # Export with custom rules
    dsn_file = Path("example_output/advanced_example.dsn")
    exporter.export(dsn_file)

    logger.info(f"Advanced DSN export complete: {dsn_file}")


if __name__ == "__main__":
    # Example 1: Create a PCB and export to DSN
    pcb_file, dsn_file = create_example_pcb_and_export()

    # Example 2: Export an existing PCB file
    if pcb_file.exists():
        export_pcb_for_routing(pcb_file)

    # Example 3: Advanced export with custom settings
    advanced_dsn_export_example()

    logger.info("\n=== DSN Export Examples Complete ===")
    logger.info("\nTo use with Freerouting:")
    logger.info(
        "1. Download Freerouting from: https://github.com/freerouting/freerouting"
    )
    logger.info("2. Run: java -jar freerouting.jar")
    logger.info("3. Open your .dsn file")
    logger.info("4. Click 'Autoroute' to start routing")
    logger.info("5. Save as .ses file when complete")
    logger.info("6. Import .ses back into KiCad PCB editor")
