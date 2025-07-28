"""
KiCad Schematic Synchronizer

This module provides the main synchronization functionality for updating existing
KiCad schematics with changes from Circuit Synth JSON definitions.

The synchronizer handles:
- Loading existing KiCad schematic data
- Matching components between representations
- Updating component properties and connections
- Preserving user-added components and modifications
- Generating synchronization reports
"""

import logging
import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..canonical import CanonicalCircuit, CircuitMatcher
from ..netlist_importer import CircuitSynthParser
from ..sch_editor.schematic_exporter import SchematicExporter
from ..sch_editor.schematic_reader import SchematicReader
from .component_matcher import ComponentMatcher, MatchResult
from .schematic_updater import (
    ComponentUpdate,
    SchematicUpdater,
    create_component_updates_from_sync_report,
)

logger = logging.getLogger(__name__)


@dataclass
class SyncReport:
    """Report of synchronization operation results"""

    matched: int = 0
    added: int = 0
    modified: int = 0
    preserved: int = 0
    details: List[str] = None

    def __post_init__(self):
        if self.details is None:
            self.details = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for easy serialization"""
        return {
            "matched": self.matched,
            "added": self.added,
            "modified": self.modified,
            "preserved": self.preserved,
            "details": self.details,
        }


class SchematicSynchronizer:
    """
    Main synchronization class for updating KiCad schematics with Circuit Synth changes.

    This class orchestrates the synchronization process:
    1. Load existing KiCad schematic
    2. Extract component information from Circuit Synth JSON
    3. Match components between representations
    4. Update/add/preserve components as needed
    5. Write updated schematic back to KiCad
    """

    def __init__(
        self,
        project_path: str,
        match_criteria: List[str] = None,
        preserve_user_components: bool = True,
    ):
        """
        Initialize the schematic synchronizer.

        Args:
            project_path: Path to KiCad project file (.kicad_pro)
            match_criteria: Component matching criteria (default: reference, value, footprint)
            preserve_user_components: Whether to keep components not in circuit definition
        """
        self.project_path = Path(project_path)
        self.match_criteria = match_criteria or ["reference", "value", "footprint"]
        self.preserve_user_components = preserve_user_components

        # Initialize component matcher
        self.matcher = ComponentMatcher(self.match_criteria)

        # Validate project path
        if not self.project_path.suffix == ".kicad_pro":
            raise ValueError(f"Expected .kicad_pro file, got: {project_path}")
        if not self.project_path.exists():
            raise FileNotFoundError(f"KiCad project not found: {project_path}")

        logger.info(
            f"SchematicSynchronizer initialized for project: {self.project_path}"
        )
        logger.debug(f"Match criteria: {self.match_criteria}")
        logger.debug(f"Preserve user components: {self.preserve_user_components}")

    def sync_with_circuit(self, circuit) -> Dict[str, Any]:
        """
        Synchronize KiCad schematic with Circuit Synth definition using canonical matching.

        This is the main entry point that integrates the canonical matching system.

        Args:
            circuit: Circuit Synth circuit object

        Returns:
            Dictionary containing synchronization report with components_to_add,
            components_to_modify, components_to_preserve, etc.
        """
        logger.info("Starting schematic synchronization with canonical matching")

        # Initialize sync report structure
        sync_report = {
            "components_to_add": [],
            "components_to_modify": [],
            "components_to_preserve": [],
            "matched_components": {},
            "kicad_components": {},  # Will be populated after loading
            "circuit_components": {},  # Will be populated after extraction
            "summary": {"matched": 0, "added": 0, "modified": 0, "preserved": 0},
        }

        try:
            # Step 1: Load existing KiCad schematic
            kicad_schematic = self._load_kicad_schematic()
            kicad_components = self._extract_kicad_components(kicad_schematic)
            logger.info(
                f"Loaded {len(kicad_components)} components from KiCad schematic"
            )

            # Step 2: Try canonical matching first
            canonical_matches = self._match_components_canonical(
                circuit, kicad_schematic
            )

            if canonical_matches:
                logger.info(
                    f"Canonical matching successful: {len(canonical_matches)} matches found"
                )

                # Build sync report using canonical matches
                circuit_components = self._extract_circuit_components(circuit)

                # Process matched components
                # We need to check if connections have changed even for matched components
                for circuit_id, kicad_ref in canonical_matches.items():
                    if (
                        circuit_id in circuit_components
                        and kicad_ref in kicad_components
                    ):
                        circuit_comp = circuit_components[circuit_id]
                        kicad_comp = kicad_components[kicad_ref]

                        sync_report["matched_components"][circuit_id] = kicad_ref

                        # Check if component needs updating (properties or connections)
                        needs_update = self._component_needs_update(
                            circuit_comp, kicad_comp
                        )

                        # Also check if connections have changed by comparing canonical forms
                        connection_changed = self._check_connection_changes(
                            circuit,
                            circuit_id,
                            kicad_ref,
                            canonical_matches,
                            circuit_components,
                            kicad_components,
                        )

                        if needs_update or connection_changed:
                            updates = self._get_component_updates(
                                circuit_comp, kicad_comp
                            )
                            if connection_changed:
                                updates["connections"] = {
                                    "changed": True,
                                    "message": "Component connections have changed",
                                }

                            sync_report["components_to_modify"].append(
                                {
                                    "reference": kicad_ref,
                                    "circuit_id": circuit_id,
                                    "updates": updates,
                                }
                            )
                            sync_report["summary"]["modified"] += 1
                        else:
                            sync_report["summary"]["matched"] += 1

                # Find components to add (in circuit but not matched)
                matched_circuit_ids = set(canonical_matches.keys())
                for circuit_id, circuit_comp in circuit_components.items():
                    if circuit_id not in matched_circuit_ids:
                        sync_report["components_to_add"].append(
                            {"circuit_id": circuit_id, "component": circuit_comp}
                        )
                        sync_report["summary"]["added"] += 1

                # Find components to preserve or remove (in KiCad but not matched)
                matched_kicad_refs = set(canonical_matches.values())
                for kicad_ref, kicad_comp in kicad_components.items():
                    if kicad_ref not in matched_kicad_refs:
                        if self.preserve_user_components:
                            sync_report["components_to_preserve"].append(
                                {"reference": kicad_ref, "component": kicad_comp}
                            )
                            sync_report["summary"]["preserved"] += 1
                        else:
                            # Track components to remove
                            sync_report["components_to_preserve"].append(
                                {"reference": kicad_ref, "component": kicad_comp}
                            )
                            # Also track in summary
                            if "removed" not in sync_report["summary"]:
                                sync_report["summary"]["removed"] = 0
                            sync_report["summary"]["removed"] += 1

            else:
                # Fall back to traditional synchronize method
                logger.info(
                    "Canonical matching failed or returned no matches, falling back to traditional matching"
                )
                return self.synchronize(circuit)

            # Log summary
            summary = sync_report["summary"]
            logger.info(
                f"Sync complete - Matched: {summary['matched']}, "
                f"Modified: {summary['modified']}, "
                f"Added: {summary['added']}, "
                f"Preserved: {summary['preserved']}"
            )

        except Exception as e:
            logger.error(f"Synchronization failed: {e}")
            sync_report["error"] = str(e)
            raise

        return sync_report

    def _get_component_updates(
        self, circuit_comp: Dict, kicad_comp: Dict
    ) -> Dict[str, Any]:
        """Get the specific updates needed for a component."""
        updates = {}

        # Check each property that might need updating
        for prop in ["value", "footprint"]:
            circuit_val = circuit_comp.get(prop)
            kicad_val = kicad_comp.get(prop)

            if circuit_val and circuit_val != kicad_val:
                updates[prop] = {"old": kicad_val, "new": circuit_val}

        return updates

    def synchronize(self, circuit) -> Dict[str, Any]:
        """
        Legacy synchronization method (fallback when canonical matching fails).

        Args:
            circuit: Circuit Synth circuit object or JSON data

        Returns:
            Dictionary containing synchronization report
        """
        logger.info("Starting schematic synchronization (legacy method)")

        # Initialize report
        report = SyncReport()

        try:
            # Step 1: Load existing KiCad schematic
            kicad_schematic = self._load_kicad_schematic()
            kicad_components = self._extract_kicad_components(kicad_schematic)
            logger.info(
                f"Loaded {len(kicad_components)} components from KiCad schematic"
            )

            # Step 2: Extract circuit components
            circuit_components = self._extract_circuit_components(circuit)
            logger.info(
                f"Extracted {len(circuit_components)} components from circuit definition"
            )

            # Store component data for later use in _write_updated_schematic
            self._last_circuit_components = circuit_components
            self._last_kicad_components = kicad_components

            # Step 3: Match components
            match_result = self.matcher.match_components(
                circuit_components, kicad_components
            )
            report.matched = len(match_result.matched_pairs)

            # Step 4: Process matches and updates
            self._process_component_matches(
                match_result, circuit_components, kicad_components, report
            )

            # Step 5: Handle unmatched components
            self._process_unmatched_components(
                match_result, circuit_components, kicad_components, report
            )

            # Step 6: Write updated schematic (placeholder for now)
            self._write_updated_schematic(kicad_schematic, report)

            logger.info("Schematic synchronization completed successfully")

        except Exception as e:
            logger.error(f"Synchronization failed: {e}")
            report.details.append(f"Error: {e}")
            raise

        return report.to_dict()

    def _load_kicad_schematic(self):
        """Load KiCad schematic from project"""
        # Find the main schematic file
        schematic_path = self._find_main_schematic()

        # Store the schematic path for later use
        self._schematic_path = schematic_path

        # Check if this is a hierarchical design
        self._hierarchical_sheet_uuid = None
        project_name = self.project_path.stem
        cover_sheet_path = self.project_path.parent / f"{project_name}.kicad_sch"

        if cover_sheet_path.exists() and cover_sheet_path != schematic_path:
            # We're loading a circuit schematic in a hierarchical design
            # Extract the sheet UUID that references this schematic
            self._hierarchical_sheet_uuid = self._find_sheet_uuid_for_schematic(
                cover_sheet_path, schematic_path.name
            )
            if self._hierarchical_sheet_uuid:
                logger.info(
                    f"Found hierarchical sheet UUID: {self._hierarchical_sheet_uuid}"
                )

        # Use SchematicReader to load the schematic
        reader = SchematicReader()
        schematic = reader.read_file(str(schematic_path))

        # Set the hierarchical path if we're in a hierarchical design
        if self._hierarchical_sheet_uuid:
            schematic.hierarchical_path = f"/{self._hierarchical_sheet_uuid}"

        logger.debug(f"Loaded schematic from: {schematic_path}")
        return schematic

    def _find_main_schematic(self) -> Path:
        """Find the main schematic file for the project"""
        # Look for .kicad_sch file with same name as project
        project_name = self.project_path.stem
        schematic_path = self.project_path.parent / f"{project_name}.kicad_sch"

        # Check if the main schematic has components, if not look for circuit schematics
        if schematic_path.exists():
            # Check if this schematic has actual components (not just a cover sheet)
            if self._schematic_has_components(schematic_path):
                return schematic_path
            else:
                logger.info(
                    f"Main schematic {schematic_path} appears to be a cover sheet, looking for circuit schematics"
                )

        # Look for schematic files that contain actual components
        sch_files = list(self.project_path.parent.glob("*.kicad_sch"))
        for sch_file in sch_files:
            if sch_file != schematic_path and self._schematic_has_components(sch_file):
                logger.info(f"Found circuit schematic with components: {sch_file}")
                return sch_file

        # Fallback: use the main schematic even if it's a cover sheet
        if schematic_path.exists():
            logger.warning(
                f"No circuit schematics found with components, using main schematic: {schematic_path}"
            )
            return schematic_path

        # Last resort: use any schematic file
        if sch_files:
            logger.warning(f"Main schematic not found, using: {sch_files[0]}")
            return sch_files[0]

        raise FileNotFoundError(
            f"No schematic files found in project directory: {self.project_path.parent}"
        )

    def _find_sheet_uuid_for_schematic(
        self, cover_sheet_path: Path, schematic_filename: str
    ) -> Optional[str]:
        """Find the UUID of the sheet that references the given schematic file"""
        try:
            with open(cover_sheet_path, "r") as f:
                content = f.read()

            # Parse the cover sheet to find the sheet that references our schematic
            from circuit_synth.kicad_api.core.s_expression import SExpressionParser

            parser = SExpressionParser()
            data = parser.parse_string(content)

            # Look for sheet blocks
            import sexpdata

            sheets = self._find_sections(data, "sheet")
            for sheet in sheets:
                # Find the Sheetfile property
                for item in sheet:
                    if (
                        isinstance(item, list)
                        and len(item) >= 3
                        and isinstance(item[0], sexpdata.Symbol)
                        and str(item[0]) == "property"
                        and item[1] == "Sheetfile"
                        and item[2] == schematic_filename
                    ):
                        # Found the sheet, now get its UUID
                        for uuid_item in sheet:
                            if (
                                isinstance(uuid_item, list)
                                and len(uuid_item) >= 2
                                and isinstance(uuid_item[0], sexpdata.Symbol)
                                and str(uuid_item[0]) == "uuid"
                            ):
                                return uuid_item[1]
                        break

            return None
        except Exception as e:
            logger.warning(f"Failed to extract sheet UUID from cover sheet: {e}")
            return None

    def _find_sections(self, expr: List[Any], name: str) -> List[List[Any]]:
        """Find all sections with the given name in an S-expression.

        Args:
            expr: S-expression to search (as nested lists)
            name: Name of sections to find (e.g., "sheet", "symbol")

        Returns:
            List of matching sections
        """
        import sexpdata

        result = []
        if isinstance(expr, list):
            for item in expr:
                if isinstance(item, list) and len(item) > 0:
                    # Check if first element is a symbol with the given name
                    first_elem = item[0]
                    if (
                        isinstance(first_elem, sexpdata.Symbol)
                        and str(first_elem) == name
                    ):
                        result.append(item)
                    # Recursively search in nested lists
                    result.extend(self._find_sections(item, name))
        return result

    def _schematic_has_components(self, schematic_path: Path) -> bool:
        """Check if a schematic file contains actual components (not just a cover sheet)"""
        try:
            with open(schematic_path, "r") as f:
                content = f.read()

            # Look for symbol instances in the schematic
            # A schematic with components will have (symbol ... (lib_id "...") entries
            # Note: symbol and lib_id may be on different lines
            import re

            # First check if there are any symbol blocks
            symbol_pattern = r"\(\s*symbol\s+"
            symbols = re.findall(symbol_pattern, content)

            # If we found symbol blocks, check if they have lib_id (not power symbols)
            if symbols:
                # Check for lib_id entries that aren't power symbols
                lib_id_pattern = r'\(lib_id\s+"(?!power:|Power:|#PWR|#FLG)[^"]+"\)'
                lib_ids = re.findall(lib_id_pattern, content)
                symbols = lib_ids  # Use lib_ids count for actual components

            logger.debug(
                f"Schematic {schematic_path} has {len(symbols)} component symbols"
            )
            return len(symbols) > 0

        except Exception as e:
            logger.warning(f"Could not check components in {schematic_path}: {e}")
            return False

    def _extract_kicad_components(self, schematic) -> Dict[str, Any]:
        """Extract component information from KiCad schematic"""
        components = {}

        # Extract components from schematic object
        if hasattr(schematic, "components"):
            for component in schematic.components:
                ref = getattr(component, "reference", None)
                if ref:
                    components[ref] = {
                        "reference": ref,
                        "value": getattr(component, "value", None),
                        "footprint": getattr(component, "footprint", None),
                        "properties": getattr(component, "properties", {}),
                        "original_component": component,
                    }

        logger.debug(f"Extracted {len(components)} components from KiCad schematic")
        return components

    def _extract_circuit_components(self, circuit) -> Dict[str, Any]:
        """Extract component information from Circuit Synth definition"""
        components = {}

        # Handle different circuit formats
        if hasattr(circuit, "_components"):
            # Circuit object with private _components attribute
            for comp_id, component in circuit._components.items():
                components[comp_id] = {
                    "reference": getattr(
                        component, "ref", comp_id
                    ),  # Circuit uses 'ref' not 'reference'
                    "value": getattr(component, "value", None),
                    "footprint": getattr(component, "footprint", None),
                    "original_component": component,
                }
        elif hasattr(circuit, "components"):
            # Circuit object with public components attribute
            # Note: circuit.components is a property that returns a list, not a dict
            for component in circuit.components:
                comp_id = getattr(component, "id", getattr(component, "ref", None))
                if comp_id:
                    components[comp_id] = {
                        "reference": getattr(component, "ref", comp_id),
                        "value": getattr(component, "value", None),
                        "footprint": getattr(component, "footprint", None),
                        "original_component": component,
                    }
        elif isinstance(circuit, dict) and "components" in circuit:
            # JSON-like dictionary
            for comp_id, component in circuit["components"].items():
                components[comp_id] = {
                    "reference": component.get("reference", comp_id),
                    "value": component.get("value"),
                    "footprint": component.get("footprint"),
                    "original_component": component,
                }
        else:
            logger.warning("Unable to extract components from circuit definition")

        logger.debug(f"Extracted {len(components)} components from circuit definition")
        return components

    def _process_component_matches(
        self,
        match_result: MatchResult,
        circuit_components: Dict,
        kicad_components: Dict,
        report: SyncReport,
    ):
        """Process matched components and identify modifications needed"""
        for circuit_id, kicad_ref in match_result.matched_pairs:
            circuit_comp = circuit_components[circuit_id]
            kicad_comp = kicad_components[kicad_ref]

            # Check if component needs updating
            needs_update = self._component_needs_update(circuit_comp, kicad_comp)

            if needs_update:
                report.modified += 1
                report.details.append(f"Modified: {kicad_ref} ({circuit_id})")
                logger.debug(f"Component {kicad_ref} needs update")
            else:
                logger.debug(f"Component {kicad_ref} is up to date")

    def _process_unmatched_components(
        self,
        match_result: MatchResult,
        circuit_components: Dict,
        kicad_components: Dict,
        report: SyncReport,
    ):
        """Process components that don't have matches"""
        # Handle circuit components with no KiCad match (need to be added)
        for circuit_id in match_result.unmatched_circuit:
            report.added += 1
            report.details.append(f"Added: {circuit_id}")
            logger.debug(f"Circuit component {circuit_id} will be added to KiCad")

        # Handle KiCad components with no circuit match
        if self.preserve_user_components:
            for kicad_ref in match_result.unmatched_kicad:
                report.preserved += 1
                report.details.append(f"Preserved: {kicad_ref}")
                logger.debug(f"KiCad component {kicad_ref} will be preserved")
        else:
            for kicad_ref in match_result.unmatched_kicad:
                # Track removed components in a new counter
                if not hasattr(report, "removed"):
                    report.removed = 0
                report.removed += 1
                report.details.append(f"Removed: {kicad_ref}")
                logger.debug(f"KiCad component {kicad_ref} will be removed")

    def _component_needs_update(self, circuit_comp: Dict, kicad_comp: Dict) -> bool:
        """Check if a KiCad component needs to be updated based on circuit definition"""
        # Compare key properties
        for prop in ["value", "footprint"]:
            circuit_val = circuit_comp.get(prop)
            kicad_val = kicad_comp.get(prop)

            if circuit_val and circuit_val != kicad_val:
                return True

        # Check if connections have changed
        # This requires comparing the nets connected to each component
        # For now, we'll mark it as needing update if we detect connection differences
        # This will be enhanced in _get_component_updates to provide connection details

        return False

    def _check_connection_changes(
        self,
        circuit,
        circuit_id: str,
        kicad_ref: str,
        canonical_matches: Dict[str, str],
        circuit_components: Dict,
        kicad_components: Dict,
    ) -> bool:
        """
        Check if a component's connections have changed between circuit and KiCad.

        This is done by comparing the nets connected to the component in both representations.

        Args:
            circuit: The Python circuit object
            circuit_id: ID of the component in the circuit
            kicad_ref: Reference of the component in KiCad
            canonical_matches: All component matches
            circuit_components: All circuit components
            kicad_components: All KiCad components

        Returns:
            True if connections have changed, False otherwise
        """
        try:
            # Get the component from the circuit
            circuit_comp = None
            for comp in circuit._components.values():
                if (
                    hasattr(comp, "id") and comp.id == circuit_id
                ) or comp.ref == circuit_id:
                    circuit_comp = comp
                    break

            if not circuit_comp:
                return False

            # Get the nets connected to this component in the circuit
            circuit_nets = set()
            for pin in circuit_comp._pins.values():
                if pin.net:
                    circuit_nets.add(pin.net.name)

            # Get the nets from KiCad component (from the stored data)
            kicad_comp_data = kicad_components.get(kicad_ref, {})
            kicad_nets = set()

            # Extract nets from KiCad component data
            # This depends on how the KiCad component data is structured
            if "nets" in kicad_comp_data:
                kicad_nets = set(kicad_comp_data["nets"].values())
            elif "pins" in kicad_comp_data:
                for pin_data in kicad_comp_data["pins"].values():
                    if "net" in pin_data:
                        kicad_nets.add(pin_data["net"])

            # Compare the net sets
            if circuit_nets != kicad_nets:
                logger.info(
                    f"Connection change detected for {kicad_ref}: "
                    f"Circuit nets: {circuit_nets}, KiCad nets: {kicad_nets}"
                )
                return True

            return False

        except Exception as e:
            logger.warning(
                f"Error checking connection changes for {circuit_id}/{kicad_ref}: {e}"
            )
            # If we can't determine, assume no change to avoid false positives
            return False

    def _export_kicad_netlist(self) -> Path:
        """
        Export the KiCad project to a netlist file using KiCad CLI.

        Returns:
            Path to the exported netlist file

        Raises:
            RuntimeError: If KiCad CLI is not available or export fails
        """
        logger.info("Exporting KiCad project to netlist")

        # Find the main schematic file
        schematic_path = self._find_main_schematic()

        # Create a temporary file for the netlist
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".net", delete=False
        ) as tmp_file:
            netlist_path = Path(tmp_file.name)

        try:
            # Try to use kicad-cli (KiCad 7+)
            # The netlist importer expects the old XML format, not the new S-expression format
            cmd = [
                "kicad-cli",
                "sch",
                "export",
                "netlist",
                "--format",
                "kicadsexpr",  # Try S-expression format first
                "-o",
                str(netlist_path),
                str(schematic_path),
            ]

            logger.debug(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                # Try alternative command for older KiCad versions
                logger.warning(f"kicad-cli failed: {result.stderr}")
                logger.info("Trying alternative netlist export method")

                # Try using eeschema directly (older KiCad versions)
                cmd = [
                    "eeschema",
                    "--export-netlist",
                    str(netlist_path),
                    str(schematic_path),
                ]

                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode != 0:
                    raise RuntimeError(f"Failed to export netlist: {result.stderr}")

            logger.info(f"Successfully exported netlist to: {netlist_path}")
            return netlist_path

        except FileNotFoundError:
            logger.error(
                "KiCad CLI tools not found. Please ensure KiCad is installed and in PATH"
            )
            raise RuntimeError("KiCad CLI tools not found")
        except Exception as e:
            # Clean up temp file on error
            if netlist_path.exists():
                netlist_path.unlink()
            raise

    def _match_components_canonical(self, circuit, kicad_schematic) -> Dict[str, str]:
        """
        Match components using the canonical form matching system with netlist export.

        Args:
            circuit: Python Circuit object
            kicad_schematic: KiCad schematic data (Schematic object) - not used in netlist approach

        Returns:
            Dictionary mapping circuit component IDs to KiCad references
        """
        logger.info("Using netlist-based canonical matching system")

        netlist_path = None
        try:
            # Step 1: Export KiCad project to netlist
            netlist_path = self._export_kicad_netlist()

            # Step 2: Import netlist to Circuit object
            logger.info("Importing KiCad netlist")

            parser = CircuitSynthParser()
            kicad_circuit = parser.parse_kicad_netlist(netlist_path)

            # Step 3: Create canonical forms of both circuits
            logger.debug("Creating canonical form of Python circuit")
            new_canonical = CanonicalCircuit.from_circuit(circuit)
            logger.info(
                f"Python circuit canonical form: {new_canonical.component_count} components"
            )

            logger.debug("Creating canonical form of KiCad circuit from netlist")
            old_canonical = CanonicalCircuit.from_circuit(kicad_circuit)
            logger.info(
                f"KiCad circuit canonical form: {old_canonical.component_count} components"
            )

            # Step 4: Use CircuitMatcher to find component matches
            matcher = CircuitMatcher()
            matches = matcher.match(old_canonical, new_canonical)

            # Log matching results
            matched_count = sum(1 for v in matches.values() if v != -1)
            logger.info(f"Canonical matching found {matched_count} component matches")

            # Step 5: Convert the canonical matching results back to actual component mappings
            component_mapping = {}

            # Get the ordered lists of components from both circuits
            circuit_components = list(circuit._components.values())

            # Get KiCad components in canonical order from the root circuit
            kicad_components = []
            self._collect_components_recursive(kicad_circuit.root, kicad_components)

            logger.debug(f"Found {len(kicad_components)} KiCad components from netlist")

            # Map the matches back to component IDs and references
            for old_idx, new_idx in matches.items():
                if (
                    new_idx != -1
                    and old_idx < len(kicad_components)
                    and new_idx < len(circuit_components)
                ):
                    kicad_comp = kicad_components[old_idx]
                    circuit_comp = circuit_components[new_idx]

                    # Get the reference from KiCad component
                    kicad_ref = kicad_comp.reference

                    # Get the ID from circuit component
                    circuit_id = (
                        circuit_comp.id
                        if hasattr(circuit_comp, "id")
                        else circuit_comp.ref
                    )

                    component_mapping[circuit_id] = kicad_ref
                    logger.debug(f"Canonical match: {circuit_id} -> {kicad_ref}")

            return component_mapping

        except Exception as e:
            logger.error(f"Netlist-based canonical matching failed: {e}", exc_info=True)
            logger.info("Falling back to traditional matching")
            return {}
        finally:
            # Clean up temporary netlist file
            if netlist_path and netlist_path.exists():
                try:
                    netlist_path.unlink()
                    logger.debug(f"Cleaned up temporary netlist file: {netlist_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up netlist file: {e}")

    def _collect_components_recursive(self, subcircuit, components_list):
        """
        Recursively collect all components from a subcircuit hierarchy.

        Args:
            subcircuit: Subcircuit object from netlist importer
            components_list: List to append components to
        """
        # Add components from this subcircuit
        for comp in subcircuit.components.values():
            components_list.append(comp)

        # Recursively process child subcircuits
        for child in subcircuit.children.values():
            self._collect_components_recursive(child, components_list)

    def _extract_symbols_ordered(self, schematic_data) -> List[Any]:
        """Extract symbols from schematic data in order (for canonical mapping)."""
        symbols = []

        def extract_symbols_recursive(data):
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, list) and len(item) > 0:
                        if str(item[0]) == "symbol":
                            # Check if it's not a power symbol
                            lib_id = None
                            for sub_item in item[1:]:
                                if isinstance(sub_item, list) and len(sub_item) >= 2:
                                    if str(sub_item[0]) == "lib_id":
                                        lib_id = str(sub_item[1])
                                        break

                            # Skip power symbols
                            if lib_id and not any(
                                pwr in lib_id
                                for pwr in ["power:", "Power:", "#PWR", "#FLG"]
                            ):
                                symbols.append(item)
                        else:
                            extract_symbols_recursive(item)

        extract_symbols_recursive(schematic_data)
        return symbols

    def _extract_properties_from_symbol(self, symbol) -> Dict[str, str]:
        """Extract properties from a symbol S-expression."""
        properties = {}

        for item in symbol[1:]:  # Skip 'symbol' token
            if isinstance(item, list) and len(item) >= 2:
                if str(item[0]) == "property" and len(item) >= 3:
                    prop_name = str(item[1]).strip('"')
                    prop_value = str(item[2]).strip('"')
                    properties[prop_name] = prop_value

        return properties

    def _write_updated_schematic(self, schematic, report: SyncReport):
        """Write the updated schematic back to KiCad using SchematicUpdater"""
        logger.info("Writing updated schematic to KiCad")

        try:
            # Create SchematicUpdater with the actual schematic path
            # IMPORTANT: Use the schematic path that was loaded, not the project path
            schematic_path = getattr(self, "_schematic_path", None)
            logger.info(f"Using schematic path for updates: {schematic_path}")
            updater = SchematicUpdater(schematic, self.project_path, schematic_path)

            # Create component updates from sync report
            # We need to get the component data for this
            circuit_components = getattr(self, "_last_circuit_components", {})
            kicad_components = getattr(self, "_last_kicad_components", {})

            updates = create_component_updates_from_sync_report(
                report.to_dict(), circuit_components, kicad_components
            )

            # Check if there are any actual changes to apply
            actual_changes = [
                u for u in updates if u.action in ["add", "modify", "remove"]
            ]

            if not actual_changes:
                logger.info("No changes detected - skipping schematic re-export")
                report.details.append("No changes needed - schematic not modified")
                return

            # Apply updates
            updater.apply_updates(updates)

            # Save the schematic
            updater.save_schematic()

            report.details.append("Schematic successfully updated and saved")
            logger.info("Schematic writing completed successfully")

        except Exception as e:
            error_msg = f"Failed to write updated schematic: {e}"
            logger.error(error_msg)
            report.details.append(f"Error: {error_msg}")
            raise
