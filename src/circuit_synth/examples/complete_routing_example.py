"""
Complete PCB routing workflow example.

This example demonstrates the full auto-routing workflow:
1. Export PCB to DSN format
2. Run Freerouting
3. Import routed board back from SES format
"""

import logging
from pathlib import Path
from circuit_synth.kicad_api.pcb.routing import (
    export_pcb_to_dsn,
    route_pcb,
    import_ses_to_pcb
)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def complete_routing_workflow(pcb_file: str, output_dir: str = None):
    """
    Complete PCB routing workflow.
    
    Args:
        pcb_file: Path to input KiCad PCB file
        output_dir: Directory for output files (defaults to PCB directory)
    """
    pcb_path = Path(pcb_file)
    if not pcb_path.exists():
        raise FileNotFoundError(f"PCB file not found: {pcb_file}")
    
    # Set up output directory
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
    else:
        output_path = pcb_path.parent
    
    # File paths
    dsn_file = output_path / f"{pcb_path.stem}.dsn"
    ses_file = output_path / f"{pcb_path.stem}.ses"
    routed_pcb = output_path / f"{pcb_path.stem}_routed.kicad_pcb"
    
    logger.info("=" * 60)
    logger.info("Complete PCB Routing Workflow")
    logger.info("=" * 60)
    
    # Step 1: Export to DSN
    logger.info("\n1. Exporting PCB to DSN format...")
    try:
        export_pcb_to_dsn(str(pcb_path), str(dsn_file))
        logger.info(f"   ✓ DSN exported to: {dsn_file}")
    except Exception as e:
        logger.error(f"   ✗ DSN export failed: {e}")
        return
    
    # Step 2: Run Freerouting
    logger.info("\n2. Running Freerouting...")
    logger.info("   (This may take several minutes for complex boards)")
    
    def progress_callback(progress, status):
        logger.info(f"   Progress: {progress:.1f}% - {status}")
    
    try:
        success, result = route_pcb(
            str(dsn_file),
            str(ses_file),
            effort='medium',
            optimization_passes=10,
            progress_callback=progress_callback
        )
        
        if success:
            logger.info(f"   ✓ Routing complete! Session file: {ses_file}")
        else:
            logger.error(f"   ✗ Routing failed: {result}")
            return
    except Exception as e:
        logger.error(f"   ✗ Routing error: {e}")
        logger.info("\n   Make sure Freerouting is installed:")
        logger.info("   - Java 21 or later is required")
        logger.info("   - Download Freerouting from: https://github.com/freerouting/freerouting/releases")
        logger.info("   - Place freerouting-*.jar in ~/freerouting/ or C:\\freerouting\\")
        return
    
    # Step 3: Import routed board
    logger.info("\n3. Importing routed board...")
    try:
        result_file = import_ses_to_pcb(str(pcb_path), str(ses_file), str(routed_pcb))
        logger.info(f"   ✓ Routed PCB saved to: {result_file}")
    except Exception as e:
        logger.error(f"   ✗ Import failed: {e}")
        return
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Routing Complete!")
    logger.info("=" * 60)
    logger.info(f"\nOriginal PCB: {pcb_path}")
    logger.info(f"Routed PCB:   {routed_pcb}")
    logger.info("\nNext steps:")
    logger.info("1. Open the routed PCB in KiCad PCB Editor")
    logger.info("2. Run Design Rules Check (DRC)")
    logger.info("3. Review and adjust routing as needed")
    logger.info("4. Generate manufacturing files")


def batch_routing_workflow(pcb_directory: str, output_dir: str = None):
    """
    Route all PCB files in a directory.
    
    Args:
        pcb_directory: Directory containing PCB files
        output_dir: Directory for output files (optional)
    """
    pcb_dir = Path(pcb_directory)
    if not pcb_dir.exists():
        raise FileNotFoundError(f"Directory not found: {pcb_directory}")
    
    # Find all PCB files
    pcb_files = list(pcb_dir.glob("*.kicad_pcb"))
    if not pcb_files:
        logger.warning(f"No PCB files found in {pcb_directory}")
        return
    
    logger.info(f"Found {len(pcb_files)} PCB files to route")
    
    # Process each PCB
    for i, pcb_file in enumerate(pcb_files, 1):
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing {i}/{len(pcb_files)}: {pcb_file.name}")
        logger.info(f"{'='*60}")
        
        try:
            complete_routing_workflow(str(pcb_file), output_dir)
        except Exception as e:
            logger.error(f"Failed to process {pcb_file.name}: {e}")
            continue


def routing_with_custom_settings(pcb_file: str):
    """
    Example with custom routing settings.
    
    Args:
        pcb_file: Path to input PCB file
    """
    from circuit_synth.kicad_api.pcb.routing import (
        DSNExporter,
        FreeroutingRunner,
        FreeroutingConfig,
        RoutingEffort,
        SESImporter
    )
    
    pcb_path = Path(pcb_file)
    dsn_file = pcb_path.with_suffix('.dsn')
    ses_file = pcb_path.with_suffix('.ses')
    routed_pcb = pcb_path.with_stem(f"{pcb_path.stem}_custom_routed")
    
    logger.info("Custom routing workflow with specific settings")
    
    # Step 1: Export with custom design rules
    logger.info("\n1. Exporting with custom design rules...")
    exporter = DSNExporter(
        pcb_file=str(pcb_path),
        track_width=0.2,      # 0.2mm tracks
        clearance=0.15,       # 0.15mm clearance
        via_diameter=0.6,     # 0.6mm vias
        via_drill=0.3         # 0.3mm drill
    )
    exporter.export(str(dsn_file))
    logger.info(f"   ✓ Exported with custom rules")
    
    # Step 2: Route with custom settings
    logger.info("\n2. Routing with high effort and optimization...")
    config = FreeroutingConfig(
        effort=RoutingEffort.HIGH,
        optimization_passes=20,
        via_costs=150.0,  # Higher via cost = fewer vias
        memory_mb=2048,   # 2GB memory for complex boards
        timeout_seconds=7200  # 2 hour timeout
    )
    
    runner = FreeroutingRunner(config)
    success, result = runner.route(str(dsn_file), str(ses_file))
    
    if not success:
        logger.error(f"Routing failed: {result}")
        return
    
    logger.info("   ✓ High-quality routing complete")
    
    # Step 3: Import routed board
    logger.info("\n3. Importing routed board...")
    importer = SESImporter(str(pcb_path), str(ses_file))
    result_file = importer.import_routing(str(routed_pcb))
    logger.info(f"   ✓ Imported to: {result_file}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python complete_routing_example.py <pcb_file>")
        print("  python complete_routing_example.py <pcb_directory> --batch")
        print("\nExamples:")
        print("  python complete_routing_example.py my_board.kicad_pcb")
        print("  python complete_routing_example.py ./pcb_files/ --batch")
        sys.exit(1)
    
    if len(sys.argv) >= 3 and sys.argv[2] == "--batch":
        # Batch mode
        batch_routing_workflow(sys.argv[1])
    else:
        # Single file mode
        complete_routing_workflow(sys.argv[1])