#!/usr/bin/env python3
"""
KiCad schematic parser for exporting to circuit-synth JSON format.

This module provides functionality to parse .kicad_sch files and export
them to the circuit-synth canonical JSON format.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict

from circuit_synth.tools.utilities.kicad_parser import KiCadParser
from circuit_synth.tools.utilities.models import Circuit

logger = logging.getLogger(__name__)


class KiCadSchematicParser:
    """
    Parse .kicad_sch files and export to circuit-synth JSON format.

    This class orchestrates the parsing of KiCad schematic files and their
    export to the canonical circuit-synth JSON format. It leverages existing
    KiCadParser functionality for the actual parsing and adds JSON export
    capability.
    """

    def __init__(self, schematic_path: Path):
        """
        Initialize parser with path to .kicad_sch file.

        Args:
            schematic_path: Path to the .kicad_sch file to parse
        """
        self.schematic_path = Path(schematic_path)
        self.project_dir = self.schematic_path.parent
        self.kicad_parser = None

        # Try to initialize KiCadParser if project structure is valid
        # This may fail if .kicad_pro is missing, which is OK
        try:
            self.kicad_parser = KiCadParser(str(self.project_dir))
            logger.info(f"Initialized KiCadSchematicParser for {self.schematic_path}")
        except Exception as e:
            logger.warning(f"Could not initialize KiCadParser: {e}")
            logger.warning("Parser will attempt fallback methods")

    def parse_schematic(self) -> Circuit:
        """
        Parse .kicad_sch file to Circuit object.

        Uses KiCadParser's existing parsing methods to extract components,
        nets, and hierarchical structure from the schematic.

        Returns:
            Circuit object containing parsed components and nets

        Raises:
            FileNotFoundError: If schematic file doesn't exist
            ValueError: If parsing fails
        """
        if not self.schematic_path.exists():
            raise FileNotFoundError(f"Schematic file not found: {self.schematic_path}")

        logger.info(f"Parsing schematic: {self.schematic_path}")

        try:
            # If KiCadParser is not available, return empty circuit
            if self.kicad_parser is None:
                logger.warning("KiCadParser not available, returning empty circuit")
                return Circuit(
                    name=self.schematic_path.stem,
                    components=[],
                    nets=[],
                    schematic_file=self.schematic_path.name,
                )

            # Use KiCadParser to parse the entire project
            # This handles netlist generation, component extraction, and hierarchy
            circuits = self.kicad_parser.parse_circuits()

            if not circuits:
                logger.warning("No circuits parsed from schematic")
                # Return empty circuit
                return Circuit(
                    name=self.schematic_path.stem,
                    components=[],
                    nets=[],
                    schematic_file=self.schematic_path.name,
                )

            # Return the main circuit (or first circuit if multiple)
            if "main" in circuits:
                circuit = circuits["main"]
            else:
                circuit = list(circuits.values())[0]

            logger.info(
                f"Parsed circuit '{circuit.name}': "
                f"{len(circuit.components)} components, {len(circuit.nets)} nets"
            )

            return circuit

        except Exception as e:
            logger.error(f"Failed to parse schematic: {e}")
            raise ValueError(f"Schematic parsing failed: {e}") from e

    def export_to_json(self, circuit: Circuit, json_path: Path) -> None:
        """
        Export Circuit to circuit-synth JSON format.

        Uses Circuit.to_circuit_synth_json() to transform the circuit data
        into the canonical JSON format and writes it to a file.

        Args:
            circuit: Circuit object to export
            json_path: Path where JSON file should be written

        Raises:
            IOError: If writing JSON file fails
        """
        logger.info(f"Exporting circuit to JSON: {json_path}")

        try:
            # Convert circuit to JSON format
            json_data = circuit.to_circuit_synth_json()

            # Write to file with pretty formatting
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=2, default=str)

            logger.info(f"Successfully exported JSON to {json_path}")

        except Exception as e:
            logger.error(f"Failed to export JSON: {e}")
            raise IOError(f"JSON export failed: {e}") from e

    def parse_and_export(self, json_path: Path) -> Dict[str, Any]:
        """
        Complete workflow: parse schematic and export to JSON.

        This is a convenience method that combines parsing and export
        into a single operation with comprehensive error handling.

        Args:
            json_path: Path where JSON file should be written

        Returns:
            Result dictionary with keys:
                - success (bool): True if operation succeeded
                - json_path (Path): Path to exported JSON (if success)
                - error (str): Error message (if not success)
        """
        try:
            # Parse the schematic
            circuit = self.parse_schematic()

            # Export to JSON
            self.export_to_json(circuit, json_path)

            return {"success": True, "json_path": json_path}

        except FileNotFoundError as e:
            error_msg = f"Schematic file not found: {e}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

        except ValueError as e:
            error_msg = f"Parsing failed: {e}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

        except IOError as e:
            error_msg = f"Export failed: {e}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
