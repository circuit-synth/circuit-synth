#!/usr/bin/env python3
"""
Freerouting Integration Example

This example demonstrates how to use the DSN exporter with the Freerouting runner
to automatically route a PCB design.

Author: Circuit Synth Team
Date: 2025-06-23
"""

import logging
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from circuit_synth.kicad_api.pcb.routing import (
    FreeroutingConfig,
    FreeroutingRunner,
    RoutingEffort,
    export_pcb_to_dsn,
    route_pcb,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def progress_callback(progress: float, status: str):
    """Callback to display routing progress"""
    print(f"\rRouting progress: {progress:.1f}% - {status}", end="", flush=True)


def route_pcb_with_freerouting(pcb_file: str, output_dir: str = None):
    """
    Complete example of routing a PCB with Freerouting

    Args:
        pcb_file: Path to KiCad PCB file
        output_dir: Directory for output files (defaults to PCB directory)
    """
    pcb_path = Path(pcb_file)
    if not pcb_path.exists():
        logger.error(f"PCB file not found: {pcb_file}")
        return

    # Set output directory
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
    else:
        output_path = pcb_path.parent

    # File paths
    dsn_file = output_path / f"{pcb_path.stem}.dsn"
    ses_file = output_path / f"{pcb_path.stem}.ses"

    print(f"Routing PCB: {pcb_path.name}")
    print(f"Output directory: {output_path}")

    # Step 1: Export PCB to DSN format
    print("\n1. Exporting PCB to DSN format...")
    try:
        export_pcb_to_dsn(str(pcb_path), str(dsn_file))
        print(f"   ✓ DSN exported to: {dsn_file}")
    except Exception as e:
        logger.error(f"Failed to export DSN: {e}")
        return

    # Step 2: Run Freerouting
    print("\n2. Running Freerouting...")
    print("   (This may take several minutes depending on circuit complexity)")

    # Method 1: Using convenience function
    success, result = route_pcb(
        str(dsn_file),
        str(ses_file),
        effort="medium",
        optimization_passes=10,
        timeout_seconds=1800,  # 30 minutes
        progress_callback=progress_callback,
    )

    print()  # New line after progress

    if success:
        print(f"   ✓ Routing complete! Session file: {result}")
        print(f"\n3. Next steps:")
        print(f"   - Import {ses_file.name} back into KiCad")
        print(f"   - In KiCad PCB editor: File → Import → Specctra Session")
        print(f"   - Review and adjust the routing as needed")
    else:
        print(f"   ✗ Routing failed: {result}")


def advanced_routing_example(pcb_file: str):
    """
    Advanced example with custom configuration
    """
    pcb_path = Path(pcb_file)
    dsn_file = pcb_path.with_suffix(".dsn")
    ses_file = pcb_path.with_suffix(".ses")

    print(f"\nAdvanced routing example for: {pcb_path.name}")

    # Export DSN
    print("Exporting to DSN...")
    export_pcb_to_dsn(str(pcb_path), str(dsn_file))

    # Create custom configuration
    config = FreeroutingConfig(
        # Use high effort for better results
        effort=RoutingEffort.HIGH,
        # More optimization passes for cleaner routing
        optimization_passes=20,
        # Higher via cost to minimize vias
        via_costs=100.0,
        # Restrict to specific layers (e.g., 2-layer board)
        allowed_layers=[0, 31],  # F.Cu and B.Cu
        # Allocate more memory for complex boards
        memory_mb=2048,
        # Custom timeout
        timeout_seconds=3600,  # 1 hour
        # Progress tracking
        progress_callback=lambda p, s: print(
            f"\r[{p:5.1f}%] {s[:50]:<50}", end="", flush=True
        ),
    )

    # Create runner with custom config
    runner = FreeroutingRunner(config)

    # Check if Freerouting is available
    if not runner.config.freerouting_jar:
        print("\n⚠️  Freerouting JAR not found!")
        print(
            "Please download Freerouting from: https://github.com/freerouting/freerouting"
        )
        print("Then either:")
        print("  1. Place freerouting.jar in the current directory")
        print("  2. Set config.freerouting_jar to the JAR path")
        return

    # Run routing
    print(f"\nStarting routing with HIGH effort...")
    success, result = runner.route(str(dsn_file), str(ses_file))

    print()  # New line after progress

    if success:
        print(f"✓ Routing successful!")
        print(f"  Session file: {result}")

        # Get final statistics
        progress, status = runner.get_progress()
        print(f"  Final status: {status}")
    else:
        print(f"✗ Routing failed: {result}")


def batch_routing_example(pcb_directory: str):
    """
    Example of routing multiple PCBs in batch
    """
    pcb_dir = Path(pcb_directory)
    pcb_files = list(pcb_dir.glob("*.kicad_pcb"))

    if not pcb_files:
        print(f"No PCB files found in: {pcb_dir}")
        return

    print(f"Found {len(pcb_files)} PCB files to route")

    # Create output directory
    output_dir = pcb_dir / "routed"
    output_dir.mkdir(exist_ok=True)

    # Route each PCB
    for i, pcb_file in enumerate(pcb_files, 1):
        print(f"\n{'='*60}")
        print(f"Routing PCB {i}/{len(pcb_files)}: {pcb_file.name}")
        print("=" * 60)

        # Export and route
        dsn_file = output_dir / f"{pcb_file.stem}.dsn"
        ses_file = output_dir / f"{pcb_file.stem}.ses"

        try:
            # Export
            export_pcb_to_dsn(str(pcb_file), str(dsn_file))

            # Route with fast settings for batch processing
            success, result = route_pcb(
                str(dsn_file),
                str(ses_file),
                effort="fast",
                optimization_passes=5,
                timeout_seconds=600,  # 10 minutes per board
            )

            if success:
                print(f"✓ Successfully routed: {ses_file.name}")
            else:
                print(f"✗ Failed to route: {result}")

        except Exception as e:
            print(f"✗ Error processing {pcb_file.name}: {e}")

    print(f"\n{'='*60}")
    print(f"Batch routing complete. Results in: {output_dir}")


def main():
    """Main function with example usage"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Freerouting integration example for Circuit Synth"
    )
    parser.add_argument("pcb_file", help="Path to KiCad PCB file (.kicad_pcb)")
    parser.add_argument(
        "-o", "--output", help="Output directory (defaults to PCB directory)"
    )
    parser.add_argument(
        "-a",
        "--advanced",
        action="store_true",
        help="Use advanced routing configuration",
    )
    parser.add_argument(
        "-b",
        "--batch",
        action="store_true",
        help="Batch mode: route all PCBs in directory",
    )

    args = parser.parse_args()

    if args.batch:
        batch_routing_example(args.pcb_file)
    elif args.advanced:
        advanced_routing_example(args.pcb_file)
    else:
        route_pcb_with_freerouting(args.pcb_file, args.output)


if __name__ == "__main__":
    # Example usage
    if len(sys.argv) > 1:
        main()
    else:
        print("Freerouting Integration Example")
        print("==============================")
        print()
        print("This example shows how to:")
        print("1. Export a KiCad PCB to DSN format")
        print("2. Run Freerouting to auto-route the board")
        print("3. Import the results back into KiCad")
        print()
        print("Usage:")
        print("  python freerouting_example.py <pcb_file>")
        print("  python freerouting_example.py <pcb_file> --advanced")
        print("  python freerouting_example.py <directory> --batch")
        print()
        print("Note: Freerouting JAR must be installed.")
        print("Download from: https://github.com/freerouting/freerouting")
