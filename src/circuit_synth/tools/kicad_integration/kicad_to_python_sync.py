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
import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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
        kicad_project: str,
        python_file: str,
        preview_only: bool = True,
        create_backup: bool = True,
    ):
        self.kicad_project = Path(kicad_project)
        self.python_file_or_dir = Path(python_file)
        self.preview_only = preview_only
        self.create_backup = create_backup

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

        # Initialize components
        self.parser = KiCadParser(str(self.kicad_project))

        # Extract project name from KiCad project path for code generation
        project_name = (
            self.kicad_project.stem
            if self.kicad_project.suffix == ".kicad_pro"
            else self.kicad_project.name
        )
        self.code_generator = PythonCodeGenerator(project_name=project_name)

        logger.info(f"KiCadToPythonSyncer initialized")
        logger.info(f"KiCad project: {self.kicad_project}")
        logger.info(f"Python target: {self.python_file_or_dir}")
        logger.info(f"Directory mode: {self.is_directory_mode}")
        logger.info(f"Preview mode: {self.preview_only}")

    def sync(self) -> bool:
        """Perform the synchronization from KiCad to Python"""
        logger.info("=== Starting KiCad to Python Synchronization ===")

        try:
            # Step 1: Parse KiCad circuits (hierarchical)
            logger.info("Step 1: Parsing KiCad project")
            circuits = self.parser.parse_circuits()

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
