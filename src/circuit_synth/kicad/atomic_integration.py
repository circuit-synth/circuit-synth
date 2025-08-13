#!/usr/bin/env python3
"""
Atomic Integration: Bridge atomic operations with circuit-synth pipeline
Provides production-ready integration of atomic KiCad operations
"""

import logging
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from .atomic_operations_exact import (
    add_component_to_schematic_exact,
    remove_component_from_schematic_exact,
)

logger = logging.getLogger(__name__)


class AtomicKiCadIntegration:
    """
    Production integration of atomic operations with circuit-synth pipeline.
    Enables incremental KiCad project updates without full regeneration.
    """

    def __init__(self, project_path: Union[str, Path]):
        """
        Initialize atomic integration for a KiCad project.

        Args:
            project_path: Path to KiCad project directory
        """
        self.project_path = Path(project_path)
        self.logger = logging.getLogger(f"{__class__.__name__}")

    def add_component_atomic(self, schematic_name: str, component_data: Dict) -> bool:
        """
        Add a component using atomic operations.

        Args:
            schematic_name: Name of schematic file (e.g., "main" or "power_supply")
            component_data: Component dictionary with symbol, ref, value, etc.

        Returns:
            True if component added successfully
        """
        schematic_path = self.project_path / f"{schematic_name}.kicad_sch"

        if not schematic_path.exists():
            self.logger.error(f"Schematic not found: {schematic_path}")
            return False

        self.logger.info(
            f"Adding component {component_data.get('ref', 'Unknown')} to {schematic_name}"
        )

        return add_component_to_schematic_exact(
            schematic_path,
            lib_id=component_data.get("symbol", "Device:R"),
            reference=component_data.get("ref", "R"),
            value=component_data.get("value", ""),
            position=component_data.get("position", (100, 100)),
            footprint=component_data.get("footprint", ""),
        )

    def remove_component_atomic(self, schematic_name: str, reference: str) -> bool:
        """
        Remove a component using atomic operations.

        Args:
            schematic_name: Name of schematic file
            reference: Component reference (e.g., "R1", "U2")

        Returns:
            True if component removed successfully
        """
        schematic_path = self.project_path / f"{schematic_name}.kicad_sch"

        if not schematic_path.exists():
            self.logger.error(f"Schematic not found: {schematic_path}")
            return False

        self.logger.info(f"Removing component {reference} from {schematic_name}")

        return remove_component_from_schematic_exact(schematic_path, reference)

    def add_sheet_reference(
        self,
        main_schematic: str,
        sheet_name: str,
        filename: str,
        position: Tuple[float, float],
        size: Tuple[float, float],
    ) -> bool:
        """
        Add hierarchical sheet reference to main schematic.

        Args:
            main_schematic: Main schematic name (usually project name)
            sheet_name: Display name for sheet
            filename: Sheet filename (e.g., "power.kicad_sch")
            position: (x, y) position in mm
            size: (width, height) in mm

        Returns:
            True if sheet reference added successfully
        """
        main_path = self.project_path / f"{main_schematic}.kicad_sch"

        if not main_path.exists():
            self.logger.error(f"Main schematic not found: {main_path}")
            return False

        return self._add_sheet_to_schematic(
            main_path, sheet_name, filename, position, size
        )

    def _add_sheet_to_schematic(
        self,
        file_path: Path,
        sheet_name: str,
        filename: str,
        position: Tuple[float, float],
        size: Tuple[float, float],
    ) -> bool:
        """Add hierarchical sheet to schematic file."""
        sheet_uuid = str(uuid.uuid4())

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            self.logger.error(f"Failed to read schematic: {e}")
            return False

        # Create sheet S-expression
        sheet_entry = f"""	(sheet
		(at {position[0]} {position[1]})
		(size {size[0]} {size[1]})
		(stroke
			(width 0.12)
			(type solid)
		)
		(fill
			(color 0 0 0 0.0000)
		)
		(uuid "{sheet_uuid}")
		(property "Sheetname" "{sheet_name}"
			(at {position[0]} {position[1] - 1.27} 0)
			(effects
				(font
					(size 1.27 1.27)
				)
				(justify left bottom)
			)
		)
		(property "Sheetfile" "{filename}"
			(at {position[0]} {position[1] + size[1] + 1.27} 0)
			(effects
				(font
					(size 1.27 1.27)
				)
				(justify left top)
			)
		)
		(instances
			(project ""
				(path "/{sheet_uuid}"
					(page "1")
				)
			)
		)
	)"""

        # Find insertion point
        sheet_instances_pos = content.find("\t(sheet_instances")
        if sheet_instances_pos == -1:
            sheet_instances_pos = content.find("\t(embedded_fonts")
        if sheet_instances_pos == -1:
            sheet_instances_pos = content.rfind(")")

        # Insert sheet reference
        new_content = (
            content[:sheet_instances_pos]
            + sheet_entry
            + "\n"
            + content[sheet_instances_pos:]
        )

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            self.logger.info(f"Added sheet '{sheet_name}' to schematic")
            return True
        except Exception as e:
            self.logger.error(f"Failed to write schematic: {e}")
            return False

    def fix_hierarchical_main_schematic(self, subcircuits: List[Dict]) -> bool:
        """
        Fix a blank main schematic by adding sheet references for all subcircuits.

        Args:
            subcircuits: List of subcircuit definitions with name, filename, position, size

        Returns:
            True if all sheet references added successfully
        """
        # Find the main schematic file
        kicad_files = list(self.project_path.glob("*.kicad_sch"))
        if not kicad_files:
            self.logger.error(f"No KiCad schematic files found in {self.project_path}")
            return False

        # Use the first schematic file as main (usually matches project name)
        main_schematic_path = kicad_files[0]
        main_schematic = main_schematic_path.stem

        self.logger.info(f"Fixing hierarchical main schematic: {main_schematic}")

        success_count = 0
        for subcircuit in subcircuits:
            success = self.add_sheet_reference(
                main_schematic,
                subcircuit["name"],
                subcircuit["filename"],
                subcircuit["position"],
                subcircuit["size"],
            )
            if success:
                success_count += 1

        self.logger.info(f"Added {success_count}/{len(subcircuits)} sheet references")
        return success_count == len(subcircuits)


def migrate_circuit_to_atomic(
    json_netlist_path: Union[str, Path], output_dir: Union[str, Path]
) -> bool:
    """
    Migrate a circuit-synth JSON netlist to KiCad using atomic operations.

    Args:
        json_netlist_path: Path to JSON netlist file
        output_dir: Directory to create KiCad project

    Returns:
        True if migration successful
    """
    import json

    json_path = Path(json_netlist_path)
    output_path = Path(output_dir)

    if not json_path.exists():
        logger.error(f"JSON netlist not found: {json_path}")
        return False

    # Load JSON netlist
    try:
        with open(json_path, "r") as f:
            netlist_data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load JSON netlist: {e}")
        return False

    # Create output directory
    output_path.mkdir(exist_ok=True)

    # Initialize atomic integration
    atomic = AtomicKiCadIntegration(output_path)

    # Create main schematic (blank initially)
    main_name = netlist_data.get("name", "main")
    main_schematic = output_path / f"{main_name}.kicad_sch"

    # Create blank main schematic
    blank_content = f"""(kicad_sch
	(version 20250114)
	(generator "circuit_synth")
	(generator_version "9.0")
	(uuid "{str(uuid.uuid4())}")
	(paper "A4")
	(lib_symbols
	)
	(sheet_instances
	)
)"""

    with open(main_schematic, "w") as f:
        f.write(blank_content)

    logger.info(f"Created main schematic: {main_schematic}")

    # Process subcircuits using atomic operations
    subcircuits = netlist_data.get("subcircuits", [])
    sheet_configs = []

    for i, subcircuit in enumerate(subcircuits):
        subcircuit_name = subcircuit.get("name", f"subcircuit_{i}")

        # Create subcircuit schematic using atomic operations
        sub_schematic = output_path / f"{subcircuit_name}.kicad_sch"

        with open(sub_schematic, "w") as f:
            f.write(blank_content.replace(main_name, subcircuit_name))

        # Add components to subcircuit using atomic operations
        for comp_ref, comp_data in subcircuit.get("components", {}).items():
            atomic.add_component_atomic(
                subcircuit_name,
                {
                    "symbol": comp_data.get("symbol", "Device:R"),
                    "ref": comp_ref,
                    "value": comp_data.get("value", ""),
                    "footprint": comp_data.get("footprint", ""),
                    "position": (100 + i * 20, 100),  # Simple positioning
                },
            )

        # Prepare sheet configuration for main schematic
        sheet_configs.append(
            {
                "name": subcircuit_name,
                "filename": f"{subcircuit_name}.kicad_sch",
                "position": (50 + i * 60, 50),
                "size": (50, 30),
            }
        )

    # Fix main schematic with sheet references
    success = atomic.fix_hierarchical_main_schematic(sheet_configs)

    if success:
        logger.info(
            f"✅ Successfully migrated circuit to KiCad using atomic operations: {output_path}"
        )
    else:
        logger.error(f"❌ Failed to migrate circuit to KiCad")

    return success


# Integration with existing Circuit class
def add_atomic_methods_to_circuit():
    """Add atomic operation methods to Circuit class."""
    from circuit_synth.core.circuit import Circuit

    def generate_kicad_project_atomic(
        self, project_name: str, **kwargs
    ) -> Optional[Path]:
        """Generate KiCad project using atomic operations for better reliability."""
        # First generate JSON
        json_path = f"{project_name}.json"
        self.generate_json_netlist(json_path)

        # Use atomic migration
        output_dir = Path(project_name)
        success = migrate_circuit_to_atomic(json_path, output_dir)

        return output_dir if success else None

    # Add method to Circuit class
    Circuit.generate_kicad_project_atomic = generate_kicad_project_atomic

    logger.info("✅ Added atomic methods to Circuit class")


# Auto-initialize when imported
try:
    add_atomic_methods_to_circuit()
except ImportError:
    logger.warning("Circuit class not available - atomic methods not added")
