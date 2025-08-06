"""
Hierarchical Synchronizer for KiCad Projects

This module provides synchronization for hierarchical KiCad projects,
properly handling multi-level circuit hierarchies and preserving manual
edits at all levels.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..core.s_expression import SExpressionParser
from .synchronizer import APISynchronizer

logger = logging.getLogger(__name__)


class HierarchicalSheet:
    """Represents a sheet in the hierarchical structure."""

    def __init__(
        self, name: str, file_path: Path, parent: Optional["HierarchicalSheet"] = None
    ):
        self.name = name
        self.file_path = file_path
        self.parent = parent
        self.children: List[HierarchicalSheet] = []
        self.synchronizer: Optional[APISynchronizer] = None
        self.schematic = None

    def add_child(self, child: "HierarchicalSheet"):
        """Add a child sheet."""
        self.children.append(child)
        child.parent = self

    def get_hierarchical_path(self) -> str:
        """Get the full hierarchical path to this sheet."""
        if self.parent is None:
            return "/"
        parent_path = self.parent.get_hierarchical_path()
        if parent_path == "/":
            return f"/{self.name}"
        return f"{parent_path}/{self.name}"


class HierarchicalSynchronizer:
    """
    Synchronizer for hierarchical KiCad projects.

    This synchronizer handles multi-level circuit hierarchies by:
    1. Building a hierarchical tree of all schematic sheets
    2. Matching sheets to circuit subcircuits
    3. Synchronizing each sheet with its corresponding subcircuit
    4. Preserving manual edits at all levels
    """

    def __init__(self, project_path: str, preserve_user_components: bool = True):
        """
        Initialize the hierarchical synchronizer.

        Args:
            project_path: Path to KiCad project file (.kicad_pro)
            preserve_user_components: Whether to keep components not in circuit
        """
        self.project_path = Path(project_path)
        self.project_dir = self.project_path.parent
        self.project_name = self.project_path.stem
        self.preserve_user_components = preserve_user_components

        # Parser for loading schematics
        self.parser = SExpressionParser()

        # Build hierarchical structure
        self.root_sheet = self._build_hierarchy()

    def _build_hierarchy(self) -> HierarchicalSheet:
        """Build the hierarchical structure of the project."""
        logger.info(f"Building hierarchy for project: {self.project_name}")

        # Start with the main schematic
        main_sch_path = self.project_dir / f"{self.project_name}.kicad_sch"
        if not main_sch_path.exists():
            raise FileNotFoundError(f"Main schematic not found: {main_sch_path}")

        root = HierarchicalSheet(self.project_name, main_sch_path)

        # Load the schematic and find hierarchical sheets
        self._load_sheet_hierarchy(root)

        return root

    def _load_sheet_hierarchy(self, sheet: HierarchicalSheet):
        """Recursively load sheet hierarchy."""
        logger.debug(f"Loading sheet: {sheet.file_path}")

        try:
            # Parse the schematic
            schematic = self.parser.parse_file(str(sheet.file_path))
            sheet.schematic = schematic

            logger.debug(f"Parsed schematic has {len(schematic.components)} components")

            # Create synchronizer for this sheet
            sheet.synchronizer = APISynchronizer(
                str(sheet.file_path),
                preserve_user_components=self.preserve_user_components,
            )

            # Find hierarchical sheet instances
            # Look for sheet elements in the schematic
            if hasattr(schematic, "sheets") and schematic.sheets:
                logger.debug(f"Schematic has {len(schematic.sheets)} sheets")
                for sheet_elem in schematic.sheets:
                    logger.debug(f"Processing sheet element: {sheet_elem}")
                    logger.debug(f"Sheet attributes: {dir(sheet_elem)}")

                    # Try different ways to get sheet info
                    sheet_file = None
                    sheet_name = None

                    # Direct attributes
                    if hasattr(sheet_elem, "filename"):
                        sheet_file = sheet_elem.filename
                    elif hasattr(sheet_elem, "file"):
                        sheet_file = sheet_elem.file
                    if hasattr(sheet_elem, "name"):
                        sheet_name = sheet_elem.name

                    # From at property (position)
                    if hasattr(sheet_elem, "at"):
                        logger.debug(f"Sheet at: {sheet_elem.at}")

                    # From properties
                    if hasattr(sheet_elem, "properties"):
                        for prop in sheet_elem.properties:
                            if prop.name == "Sheetfile":
                                sheet_file = prop.value
                            elif prop.name == "Sheetname":
                                sheet_name = prop.value

                    logger.debug(f"Sheet file: {sheet_file}, name: {sheet_name}")

                    if sheet_file:
                        logger.info(f"Found sheet: {sheet_name} -> {sheet_file}")
                        # Resolve the file path
                        child_path = self.project_dir / sheet_file

                        if child_path.exists():
                            # Create child sheet and load recursively
                            child = HierarchicalSheet(
                                sheet_name or sheet_file, child_path, sheet
                            )
                            sheet.add_child(child)
                            self._load_sheet_hierarchy(child)
                        else:
                            logger.warning(
                                f"Hierarchical sheet file not found: {child_path}"
                            )
            else:
                logger.debug(
                    "Schematic has no sheets attribute or sheets list is empty"
                )

            # Alternative: Look in components for sheet instances
            if len(sheet.children) == 0:
                for comp in schematic.components:
                    # Check if this is a sheet (has Sheetfile property)
                    sheet_file = None
                    sheet_name = None

                    if hasattr(comp, "properties"):
                        for prop in comp.properties:
                            if prop.name == "Sheetfile":
                                sheet_file = prop.value
                            elif prop.name == "Sheetname":
                                sheet_name = prop.value

                    if sheet_file:
                        logger.debug(
                            f"Found sheet component: {sheet_name} -> {sheet_file}"
                        )
                        # Resolve the file path
                        child_path = self.project_dir / sheet_file

                        if child_path.exists():
                            # Create child sheet and load recursively
                            child = HierarchicalSheet(
                                sheet_name or sheet_file, child_path, sheet
                            )
                            sheet.add_child(child)
                            self._load_sheet_hierarchy(child)
                        else:
                            logger.warning(
                                f"Hierarchical sheet file not found: {child_path}"
                            )

        except Exception as e:
            logger.error(f"Failed to load sheet {sheet.file_path}: {e}")

    def sync_with_circuit(
        self, circuit, subcircuit_dict: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Synchronize the hierarchical project with the circuit.

        Args:
            circuit: The main circuit object
            subcircuit_dict: Dictionary mapping subcircuit names to circuit objects

        Returns:
            Dictionary containing synchronization report
        """
        logger.info("Starting hierarchical synchronization")

        # Build subcircuit mapping if not provided
        if subcircuit_dict is None:
            subcircuit_dict = self._build_subcircuit_dict(circuit)

        # Log subcircuit information
        logger.info(f"Found {len(subcircuit_dict)} subcircuits in circuit definition")
        for name in subcircuit_dict:
            logger.debug(f"  Subcircuit: {name}")

        # Synchronize recursively
        report = {
            "sheets_synchronized": 0,
            "total_matched": 0,
            "total_added": 0,
            "total_modified": 0,
            "total_preserved": 0,
            "sheet_reports": {},
        }

        self._sync_sheet_recursive(self.root_sheet, circuit, subcircuit_dict, report)

        logger.info(
            f"Hierarchical synchronization complete: {report['sheets_synchronized']} sheets processed"
        )
        return report

    def _sync_sheet_recursive(
        self,
        sheet: HierarchicalSheet,
        circuit,
        subcircuit_dict: Dict[str, Any],
        report: Dict[str, Any],
    ):
        """Recursively synchronize sheets with their corresponding circuits."""
        logger.info(
            f"Synchronizing sheet: {sheet.name} at {sheet.get_hierarchical_path()}"
        )

        # Find the corresponding circuit for this sheet
        sheet_circuit = self._find_circuit_for_sheet(sheet, circuit, subcircuit_dict)

        if sheet_circuit and sheet.synchronizer:
            # Synchronize this sheet
            sheet_sync_report = sheet.synchronizer.sync_with_circuit(sheet_circuit)

            # Convert SyncReport object to dict format
            sheet_report = {}
            if hasattr(sheet_sync_report, "matched"):
                # It's a SyncReport object
                sheet_report["matched"] = len(sheet_sync_report.matched)
                sheet_report["added"] = len(sheet_sync_report.added)
                sheet_report["modified"] = len(sheet_sync_report.modified)
                sheet_report["preserved"] = len(
                    getattr(sheet_sync_report, "preserved", [])
                )
            else:
                # It's already a dict
                sheet_report = sheet_sync_report

            # Update totals
            report["sheets_synchronized"] += 1
            report["total_matched"] += sheet_report.get("matched", 0)
            report["total_added"] += sheet_report.get("added", 0)
            report["total_modified"] += sheet_report.get("modified", 0)
            report["total_preserved"] += sheet_report.get("preserved", 0)
            report["sheet_reports"][sheet.get_hierarchical_path()] = sheet_report

            logger.info(
                f"Sheet {sheet.name}: {sheet_report.get('matched', 0)} matched, "
                f"{sheet_report.get('added', 0)} added, {sheet_report.get('modified', 0)} modified"
            )
        else:
            logger.warning(f"No circuit found for sheet: {sheet.name}")

        # Synchronize child sheets
        for child in sheet.children:
            self._sync_sheet_recursive(child, circuit, subcircuit_dict, report)

    def _find_circuit_for_sheet(
        self, sheet: HierarchicalSheet, main_circuit, subcircuit_dict: Dict[str, Any]
    ) -> Any:
        """Find the circuit object corresponding to a sheet."""
        # For the root sheet, use the main circuit
        if sheet.parent is None:
            return main_circuit

        # For subcircuits, try to match by name
        # Remove file extension if present
        sheet_name = sheet.name
        if sheet_name.endswith(".kicad_sch"):
            sheet_name = sheet_name[:-10]

        # Try exact match first
        if sheet_name in subcircuit_dict:
            return subcircuit_dict[sheet_name]

        # Try matching the file name
        file_stem = sheet.file_path.stem
        if file_stem in subcircuit_dict:
            return subcircuit_dict[file_stem]

        # Log available subcircuits for debugging
        logger.debug(f"Available subcircuits: {list(subcircuit_dict.keys())}")
        logger.debug(f"Looking for: {sheet_name} or {file_stem}")

        return None

    def _build_subcircuit_dict(self, circuit) -> Dict[str, Any]:
        """Build a dictionary mapping subcircuit names to circuit objects."""
        subcircuit_dict = {}

        # This should be populated by the caller
        # The circuit object doesn't contain subcircuit instances directly
        logger.warning(
            "_build_subcircuit_dict called without subcircuit_dict parameter - returning empty dict"
        )

        return subcircuit_dict

    def get_hierarchy_info(self) -> str:
        """Get a string representation of the project hierarchy."""
        lines = ["Project Hierarchy:"]
        self._add_hierarchy_lines(self.root_sheet, lines, 0)
        return "\n".join(lines)

    def _add_hierarchy_lines(
        self, sheet: HierarchicalSheet, lines: List[str], level: int
    ):
        """Recursively add hierarchy lines."""
        indent = "  " * level
        lines.append(f"{indent}- {sheet.name} ({sheet.file_path.name})")
        for child in sheet.children:
            self._add_hierarchy_lines(child, lines, level + 1)
