#!/usr/bin/env python3
"""
KiCad to Python Synchronization Tool

This tool converts KiCad schematics to Python circuit definitions,
automatically creating the necessary files and directories.

Features:
- Parses KiCad schematics to extract components and nets
- Uses LLM-assisted code generation for intelligent merging
- Creates directories and files automatically if they don't exist
- Creates backups before overwriting existing files
- Preserves exact component references from KiCad

Usage:
    kicad-to-python <kicad_project> <python_file_or_directory>
    kicad-to-python <kicad_project> <python_file_or_directory> --backup
"""

import argparse
import json
import logging
import sys
import warnings
from pathlib import Path
from typing import Dict, Optional

from circuit_synth.tools.utilities.kicad_parser import KiCadParser

# Import refactored modules
from circuit_synth.tools.utilities.models import Circuit, Component, Net
from circuit_synth.tools.utilities.python_code_generator import PythonCodeGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class KiCadToPythonSyncer:
    """Main synchronization class"""

    def __init__(
        self,
        kicad_project_or_json: str,
        python_file: str,
        preview_only: bool = True,
        create_backup: bool = True,
    ):
        """
        Initialize syncer with JSON or KiCad project path.

        Args:
            kicad_project_or_json: Path to .json netlist (preferred)
                                   OR .kicad_pro file (deprecated)
            python_file: Target Python file path
            preview_only: If True, only preview changes
            create_backup: Create backup before overwriting
        """
        self.python_file_or_dir = Path(python_file)
        self.preview_only = preview_only
        self.create_backup = create_backup

        # Determine input type and handle accordingly
        input_path = Path(kicad_project_or_json)

        if input_path.suffix == ".json":
            # NEW PATH: Use JSON directly (preferred)
            self._json_path = Path(input_path)
            logger.info(f"Using JSON netlist: {self._json_path}")

        elif input_path.suffix == ".kicad_pro" or input_path.is_dir():
            # LEGACY PATH: Find or generate JSON (deprecated)
            warnings.warn(
                "Passing KiCad project directly is deprecated. "
                "Pass JSON netlist path instead. "
                "This will be removed in v2.0.",
                DeprecationWarning,
                stacklevel=2,
            )
            self._json_path = self._find_or_generate_json(input_path)
            logger.warning(f"Auto-generated/found JSON: {self._json_path}")

        else:
            raise ValueError(
                f"Unsupported input: {input_path}. "
                "Expected .json netlist or .kicad_pro project file."
            )

        # Load JSON data (unified path for both inputs)
        self.json_data = self._load_json()

        # Determine if we're working with a file or directory
        if self.python_file_or_dir.exists() and self.python_file_or_dir.is_dir():
            self.is_directory_mode = True
            self.python_file = self.python_file_or_dir / "main.py"
        elif str(python_file).endswith((".py",)):
            # Explicitly ends with .py, so it's a file
            self.is_directory_mode = False
            self.python_file = self.python_file_or_dir
        elif str(python_file).endswith("/") or str(python_file).endswith("\\"):
            # Ends with path separator, so it's intended as a directory
            self.is_directory_mode = True
            self.python_file = self.python_file_or_dir / "main.py"
        elif not self.python_file_or_dir.exists():
            # Doesn't exist - guess based on whether it looks like a file or directory
            # If it has no extension and doesn't end with separator, assume directory
            if "." not in self.python_file_or_dir.name:
                self.is_directory_mode = True
                self.python_file = self.python_file_or_dir / "main.py"
            else:
                self.is_directory_mode = False
                self.python_file = self.python_file_or_dir
        else:
            # If path exists but is not a directory and doesn't end in .py, assume directory mode
            self.is_directory_mode = True
            self.python_file = self.python_file_or_dir / "main.py"

        # Extract project name from JSON for code generation
        project_name = self.json_data.get("name", "circuit")
        self.code_generator = PythonCodeGenerator(project_name=project_name)

        # Store for backward compatibility (some methods may still use it)
        self.kicad_project = input_path

        logger.info(f"KiCadToPythonSyncer initialized")
        logger.info(f"JSON input: {self._json_path}")
        logger.info(f"Python target: {self.python_file_or_dir}")
        logger.info(f"Directory mode: {self.is_directory_mode}")
        logger.info(f"Preview mode: {self.preview_only}")

    @property
    def json_path(self) -> Path:
        """
        Path to the JSON netlist being used.

        Returns:
            Path to the JSON netlist file
        """
        return self._json_path

    @json_path.setter
    def json_path(self, value: Path) -> None:
        """Set the JSON path."""
        self._json_path = Path(value)

    def _find_or_generate_json(self, kicad_project: Path) -> Path:
        """
        Find existing JSON or generate from KiCad project.

        Args:
            kicad_project: Path to .kicad_pro or project directory

        Returns:
            Path to JSON netlist file

        Raises:
            RuntimeError: If JSON generation fails
        """
        # Determine project directory and name
        if kicad_project.is_file():
            project_dir = kicad_project.parent
            project_name = kicad_project.stem
        else:
            project_dir = kicad_project
            project_name = kicad_project.name

        # Check for existing JSON
        json_path = project_dir / f"{project_name}.json"

        if json_path.exists():
            logger.info(f"Found existing JSON: {json_path}")
            return json_path

        # Generate JSON from KiCad
        logger.info(f"No JSON found, generating from KiCad project...")
        return self._export_kicad_to_json(kicad_project)

    def _export_kicad_to_json(self, kicad_project: Path) -> Path:
        """
        Export KiCad project to JSON format.

        Uses KiCadSchematicParser (from #210) to parse .kicad_sch
        and export to canonical JSON format.

        If KiCadSchematicParser is not available (dependency #210 not merged),
        falls back to using KiCadParser.

        Args:
            kicad_project: Path to .kicad_pro or project directory

        Returns:
            Path to generated JSON file

        Raises:
            RuntimeError: If export fails
            FileNotFoundError: If schematic file not found
        """
        try:
            from circuit_synth.tools.utilities.kicad_schematic_parser import (
                KiCadSchematicParser,
            )

            # Find .kicad_sch file
            if kicad_project.is_file():
                project_dir = kicad_project.parent
                project_name = kicad_project.stem
                schematic_path = project_dir / f"{project_name}.kicad_sch"
            else:
                project_dir = kicad_project
                # Find first .kicad_sch in directory
                sch_files = list(project_dir.glob("*.kicad_sch"))
                if not sch_files:
                    raise FileNotFoundError(
                        f"No .kicad_sch files found in {project_dir}"
                    )
                schematic_path = sch_files[0]
                project_name = schematic_path.stem

            if not schematic_path.exists():
                raise FileNotFoundError(f"Schematic not found: {schematic_path}")

            # Generate JSON output path
            json_path = project_dir / f"{project_name}.json"

            # Parse and export
            logger.info(f"Parsing schematic: {schematic_path}")
            parser = KiCadSchematicParser(schematic_path)
            result = parser.parse_and_export(json_path)

            if not result.get("success"):
                raise RuntimeError(
                    f"Failed to export KiCad to JSON: {result.get('error')}"
                )

            logger.info(f"Successfully exported JSON: {json_path}")
            return Path(result["json_path"])

        except (ImportError, ModuleNotFoundError):
            # Fallback: KiCadSchematicParser not available (#210 not merged)
            # Use KiCadParser to generate circuits, then export to JSON
            logger.warning(
                "KiCadSchematicParser not available, using fallback KiCadParser"
            )

            # Determine project directory and name
            if kicad_project.is_file():
                project_dir = kicad_project.parent
                project_name = kicad_project.stem
            else:
                project_dir = kicad_project
                project_name = kicad_project.name

            json_path = project_dir / f"{project_name}.json"

            # Use KiCadParser to parse circuits
            parser = KiCadParser(str(kicad_project))
            circuits = parser.parse_circuits()

            if not circuits:
                raise RuntimeError("Failed to parse KiCad project")

            # Get main circuit
            main_circuit = circuits.get("main") or list(circuits.values())[0]

            # Convert circuit to JSON format (circuit-synth schema)
            # Transform from models.Circuit format to circuit-synth JSON format
            json_data = {
                "name": main_circuit.name,
                "components": {
                    comp.reference: {
                        "ref": comp.reference,
                        "symbol": comp.lib_id,
                        "value": comp.value,
                        "footprint": comp.footprint,
                    }
                    for comp in main_circuit.components
                },
                "nets": {
                    net.name: [
                        {
                            "component": conn[0],
                            "pin_id": (
                                int(conn[1]) if conn[1].isdigit() else conn[1]
                            ),
                        }
                        for conn in net.connections
                    ]
                    for net in main_circuit.nets
                },
            }

            # Add optional source_file if available
            if main_circuit.schematic_file:
                json_data["source_file"] = main_circuit.schematic_file

            # Write JSON file
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=2)

            logger.info(f"Successfully exported JSON (fallback): {json_path}")
            return json_path

    def _load_json(self) -> dict:
        """
        Load and parse JSON netlist.

        Returns:
            Parsed JSON data as dictionary

        Raises:
            FileNotFoundError: If JSON file doesn't exist
            ValueError: If JSON is malformed
        """
        if not self.json_path.exists():
            raise FileNotFoundError(f"JSON netlist not found: {self.json_path}")

        try:
            with open(self.json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            logger.info(
                f"Loaded JSON with {len(data.get('components', {}))} components"
            )
            return data

        except json.JSONDecodeError as e:
            raise ValueError(
                f"Invalid JSON format in {self.json_path}: {e}"
            ) from e

    def _json_to_circuits(self) -> Dict[str, Circuit]:
        """
        Convert JSON data to Circuit objects.

        Returns:
            Dictionary mapping circuit names to Circuit objects
        """
        circuits = {}

        # Parse main circuit
        circuit_name = self.json_data.get("name", "main")

        # Extract components from JSON dict format
        components = []
        for ref, comp_data in self.json_data.get("components", {}).items():
            component = Component(
                reference=comp_data.get("ref", ref),
                lib_id=comp_data.get("symbol", ""),
                value=comp_data.get("value", ""),
                footprint=comp_data.get("footprint", ""),
                position=(0.0, 0.0),  # Position not in JSON
            )
            components.append(component)

        # Extract nets from JSON dict format
        nets = []
        for net_name, connections in self.json_data.get("nets", {}).items():
            net_connections = []
            for conn in connections:
                comp_ref = conn.get("component")
                pin_num = conn.get("pin", {}).get("number", "")
                net_connections.append((comp_ref, pin_num))

            net = Net(name=net_name, connections=net_connections)
            nets.append(net)

        # Create circuit object
        circuit = Circuit(
            name=circuit_name,
            components=components,
            nets=nets,
            schematic_file=self.json_data.get("source_file", ""),
            is_hierarchical_sheet=False,
        )

        circuits[circuit_name] = circuit

        # Handle subcircuits if present in JSON
        subcircuits = self.json_data.get("subcircuits", [])
        if subcircuits:
            logger.info(f"Found {len(subcircuits)} subcircuits in JSON")
            # TODO: Implement hierarchical subcircuit support
            # For now, just log that they exist

        logger.info(f"Converted JSON to {len(circuits)} circuits")
        return circuits

    def sync(self) -> bool:
        """Perform the synchronization from JSON to Python"""
        logger.info("=== Starting JSON to Python Synchronization ===")

        try:
            # Step 1: Convert JSON to Circuit objects
            logger.info("Step 1: Converting JSON to Circuit objects")
            circuits = self._json_to_circuits()

            if not circuits:
                logger.error("No circuits found in KiCad project")
                return False

            logger.info(f"Found {len(circuits)} circuits:")
            for name, circuit in circuits.items():
                logger.info(
                    f"  - {name}: {len(circuit.components)} components, {len(circuit.nets)} nets"
                )

            # Step 2: Ensure output directory exists in directory mode
            if self.is_directory_mode:
                logger.info("Step 2: Ensuring output directory exists")
                if not self.preview_only:
                    self.python_file_or_dir.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Created directory: {self.python_file_or_dir}")
                else:
                    logger.info(
                        f"Preview mode - would create directory: {self.python_file_or_dir}"
                    )

            # Step 3: Create backup if requested
            if self.create_backup and not self.preview_only:
                logger.info("Step 3: Creating backup")
                backup_path = self._create_backup()
                if backup_path:
                    logger.info(f"Backup created: {backup_path}")
                else:
                    logger.warning("Failed to create backup")

            # Step 4: Extract hierarchical tree and update Python file
            logger.info("Step 4: Updating Python file")

            # Extract hierarchical tree from circuits (all circuits should have the same tree)
            hierarchical_tree = None
            for circuit in circuits.values():
                if circuit.hierarchical_tree:
                    hierarchical_tree = circuit.hierarchical_tree
                    break

            # Add debug logging for hierarchical tree
            if hierarchical_tree:
                logger.info(
                    f"🔧 HIERARCHICAL_TREE_DEBUG: Found hierarchical tree: {hierarchical_tree}"
                )
            else:
                logger.warning(
                    "🔧 HIERARCHICAL_TREE_DEBUG: No hierarchical tree found in circuits"
                )

            if self.is_directory_mode:
                # In directory mode, create the main.py file if it doesn't exist
                if not self.python_file.exists() and not self.preview_only:
                    logger.info("Creating main.py file for hierarchical project")
                    self.python_file.write_text(
                        "# Generated by circuit-synth KiCad-to-Python sync\n"
                    )

            updated_code = self.code_generator.update_python_file(
                self.python_file, circuits, self.preview_only, hierarchical_tree
            )

            if updated_code:
                if self.preview_only:
                    logger.info("=== PREVIEW MODE - Updated Code ===")
                    print(updated_code)
                    logger.info("=== END PREVIEW ===")
                else:
                    logger.info("✅ Python file updated successfully")

                return True
            else:
                logger.error("❌ Failed to update Python file")
                return False

        except Exception as e:
            logger.error(f"Synchronization failed: {e}")
            return False

    def _create_backup(self) -> Optional[Path]:
        """Create a backup of the Python file"""
        try:
            if not self.python_file.exists():
                logger.warning(f"Python file does not exist: {self.python_file}")
                return None

            backup_path = self.python_file.with_suffix(
                f"{self.python_file.suffix}.backup"
            )

            # Read and write to create backup
            with open(self.python_file, "r") as source:
                content = source.read()

            with open(backup_path, "w") as backup:
                backup.write(content)

            return backup_path

        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None


def _resolve_kicad_project_path(input_path: str) -> Optional[Path]:
    """Resolve KiCad project path from various input formats"""
    input_path = Path(input_path)

    # If it's a .kicad_pro file, use it directly
    if input_path.suffix == ".kicad_pro" and input_path.exists():
        return input_path

    # If it's a directory, look for .kicad_pro files
    if input_path.is_dir():
        pro_files = list(input_path.glob("*.kicad_pro"))
        if len(pro_files) == 1:
            return pro_files[0]
        elif len(pro_files) > 1:
            logger.error(f"Multiple .kicad_pro files found in {input_path}")
            for pro_file in pro_files:
                logger.error(f"  - {pro_file}")
            return None
        else:
            logger.error(f"No .kicad_pro files found in {input_path}")
            return None

    # If it's a file without extension, try adding .kicad_pro
    if input_path.suffix == "":
        pro_path = input_path.with_suffix(".kicad_pro")
        if pro_path.exists():
            return pro_path

    # If it's in a subdirectory, look in parent directories
    current_path = input_path
    while current_path.parent != current_path:
        pro_files = list(current_path.glob("*.kicad_pro"))
        if pro_files:
            if len(pro_files) == 1:
                return pro_files[0]
        current_path = current_path.parent

    logger.error(f"Could not resolve KiCad project path from: {input_path}")
    return None


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Synchronize KiCad schematics with Python circuit definitions"
    )
    parser.add_argument(
        "kicad_project", help="Path to KiCad project (.kicad_pro) or directory"
    )
    parser.add_argument(
        "python_file", help="Path to Python file or directory to create"
    )
    parser.add_argument(
        "--backup", action="store_true", help="Create backup before applying changes"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Resolve KiCad project path
    kicad_project = _resolve_kicad_project_path(args.kicad_project)
    if not kicad_project:
        return 1

    # Validate Python file path - allow non-existent directories to be created
    python_file = Path(args.python_file)
    if python_file.exists() and python_file.is_file():
        # If it's an existing file, that's fine
        pass
    elif not python_file.exists():
        # If it doesn't exist, we'll create it (file or directory)
        logger.info(f"Python target doesn't exist, will be created: {python_file}")
    elif python_file.exists() and python_file.is_dir():
        # If it's an existing directory, that's fine too
        pass

    # Create syncer and run
    syncer = KiCadToPythonSyncer(
        kicad_project=str(kicad_project),
        python_file=str(python_file),
        preview_only=False,  # Always apply changes
        create_backup=args.backup,
    )

    success = syncer.sync()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
