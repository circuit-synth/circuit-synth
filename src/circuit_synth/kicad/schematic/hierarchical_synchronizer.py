"""
Hierarchical Synchronizer for KiCad Projects

This module provides synchronization for hierarchical KiCad projects,
properly handling multi-level circuit hierarchies and preserving manual
edits at all levels.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import kicad_sch_api as ksa

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

    def _reload_hierarchical_structure(self):
        """Reload the hierarchical structure from disk.

        This is necessary after adding new sheets to ensure the in-memory
        representation matches the actual KiCad files.
        """
        logger.info("Reloading hierarchical structure...")
        self.root_sheet = self._build_hierarchy()
        logger.info(f"Reloaded - root now has {len(self.root_sheet.children)} child sheet(s)")

    def _load_sheet_hierarchy(self, sheet: HierarchicalSheet):
        """Recursively load sheet hierarchy."""
        logger.debug(f"Loading sheet: {sheet.file_path}")

        try:
            # Parse the schematic using kicad-sch-api
            schematic = ksa.Schematic.load(str(sheet.file_path))
            sheet.schematic = schematic

            logger.debug(f"Parsed schematic has {len(schematic.components)} components")

            # Check kicad-sch-api version for compatibility
            if hasattr(ksa, '__version__'):
                version = ksa.__version__
                logger.debug(f"Using kicad-sch-api version: {version}")

                # Warn if version is very old
                try:
                    from packaging import version as pkg_version
                    if pkg_version.parse(version) < pkg_version.parse('0.4.0'):
                        logger.warning(
                            f"kicad-sch-api {version} is older than 0.4.0. "
                            "Hierarchical sheet detection may not work correctly. "
                            "Consider upgrading with: pip install --upgrade kicad-sch-api"
                        )
                except Exception:
                    # Ignore if packaging not available or version parsing fails
                    pass

            # Create synchronizer for this sheet
            sheet.synchronizer = APISynchronizer(
                str(sheet.file_path),
                preserve_user_components=self.preserve_user_components,
            )

            # Find hierarchical sheet instances using sheet_manager API
            # kicad-sch-api v0.4.3+ uses sheet_manager instead of direct sheets attribute
            if hasattr(schematic, '_sheet_manager'):
                logger.debug("Using sheet_manager to find hierarchical sheets")
                try:
                    hierarchy = schematic._sheet_manager.get_sheet_hierarchy()

                    if 'root' in hierarchy and 'children' in hierarchy['root']:
                        children = hierarchy['root']['children']
                        logger.debug(f"Found {len(children)} child sheets in hierarchy")

                        for sheet_data in children:
                            # sheet_data is a dict with keys: 'name', 'filename', 'uuid', etc.
                            sheet_name = sheet_data.get('name')
                            sheet_file = sheet_data.get('filename')

                            logger.debug(f"Processing sheet: {sheet_name} -> {sheet_file}")

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
                        logger.debug("No child sheets found in hierarchy")
                except Exception as e:
                    logger.warning(f"Error reading sheet hierarchy via sheet_manager: {e}")
                    logger.debug("Will try fallback component scan")
            else:
                logger.debug(
                    "Schematic has no _sheet_manager attribute (old kicad-sch-api version?)"
                )

            # Alternative: Look in components for sheet instances (fallback)
            # This fallback is rarely needed with modern kicad-sch-api
            if len(sheet.children) == 0:
                logger.debug("No sheets found via sheet_manager, trying component fallback")
                for comp in schematic.components:
                    # Check if this is a sheet (has Sheetfile property)
                    sheet_file = None
                    sheet_name = None

                    if hasattr(comp, "properties") and isinstance(comp.properties, dict):
                        # Properties is a dict in kicad-sch-api v0.4.3+
                        # Keys are property names, values are property values
                        sheet_file = comp.properties.get("Sheetfile")
                        sheet_name = comp.properties.get("Sheetname")

                        if sheet_file:
                            logger.debug(
                                f"Found sheet in component properties: {sheet_name} -> {sheet_file}"
                            )

                    if sheet_file:
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

        print(f"\n{'='*80}")
        print(f"🔍 SYNC SHEET: '{sheet.name}' at {sheet.get_hierarchical_path()}")
        print(f"{'='*80}")

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

        # Detect and create missing sheets
        if sheet_circuit:
            # Get expected child circuits from Python
            expected_children = []
            if hasattr(sheet_circuit, 'child_instances'):
                expected_children = [child['sub_name'] for child in sheet_circuit.child_instances]
            elif hasattr(sheet_circuit, '_subcircuits'):
                expected_children = [subcirc.name for subcirc in sheet_circuit._subcircuits]

            # Get existing child sheets from KiCad
            existing_children = [child.name for child in sheet.children]

            # Find missing sheets
            missing_sheets = [name for name in expected_children if name not in existing_children]

            if missing_sheets:
                print(f"\n🚨 NEED TO CREATE {len(missing_sheets)} NEW SHEET(S):")
                for missing_name in missing_sheets:
                    print(f"      - {missing_name}")
                    print(f"        → Should create sheet symbol in {sheet.file_path}")
                    print(f"        → Should create {missing_name}.kicad_sch file")
                    print(f"        → Should synchronize components into new sheet")

                # Attempt to create missing sheets
                print(f"\n🔧 ATTEMPTING TO CREATE MISSING SHEETS...")
                for missing_name in missing_sheets:
                    print(f"\n{'='*80}")
                    print(f"🏗️  Creating sheet: {missing_name}")
                    print(f"{'='*80}")

                    # Get the circuit object for this missing sheet
                    missing_circuit = subcircuit_dict.get(missing_name)
                    if not missing_circuit:
                        print(f"❌ ERROR: Circuit '{missing_name}' not found in subcircuit_dict!")
                        continue

                    print(f"✅ Found circuit object: {missing_circuit.name}")
                    print(f"   Circuit has {len(missing_circuit.components) if hasattr(missing_circuit, 'components') else 'unknown'} components")

                    # Try to create the new sheet
                    try:
                        self._create_missing_sheet(sheet, missing_name, missing_circuit, subcircuit_dict)

                        # CRITICAL: After creating a sheet, we need to reload the hierarchical structure
                        # so that sheet.children reflects the newly added sheet. Otherwise, the next
                        # sync will think the sheet is still missing and create a duplicate!
                        print(f"\n🔄 Reloading hierarchical structure to recognize new sheet...")
                        self._reload_hierarchical_structure()

                    except Exception as e:
                        print(f"❌ ERROR creating sheet: {e}")
                        import traceback
                        traceback.print_exc()

    def _create_missing_sheet(
        self,
        parent_sheet: HierarchicalSheet,
        sheet_name: str,
        circuit_obj: Any,
        subcircuit_dict: Dict[str, Any],
    ):
        """Create a new hierarchical sheet that's missing in KiCad but exists in Python."""
        print(f"\n🔨 _create_missing_sheet() called")
        print(f"   Parent sheet: {parent_sheet.name}")
        print(f"   New sheet name: {sheet_name}")
        print(f"   Circuit object: {circuit_obj.name}")
        print(f"   Project dir: {self.project_dir}")

        # Step 1: Create blank child .kicad_sch file
        child_sch_path = self.project_dir / f"{sheet_name}.kicad_sch"
        print(f"\n📝 STEP 1: Create blank {child_sch_path}")

        if child_sch_path.exists():
            print(f"   ⚠️  File already exists, will synchronize")
        else:
            print(f"   Creating new minimal schematic file...")
            try:
                # Create a minimal blank KiCad 8 schematic manually
                import uuid as uuid_module

                sch_uuid = str(uuid_module.uuid4())
                minimal_sch = f'''(kicad_sch
\t(version 20231120)
\t(generator "circuit-synth")
\t(generator_version "0.11.1")
\t(uuid "{sch_uuid}")
\t(paper "A4")
\t(lib_symbols)
\t(sheet_instances
\t\t(path "/"
\t\t\t(page "1")
\t\t)
\t)
)
'''
                # Write the minimal schematic
                with open(child_sch_path, 'w') as f:
                    f.write(minimal_sch)

                print(f"   ✅ Created minimal schematic: {child_sch_path}")

            except Exception as e:
                print(f"   ❌ ERROR creating schematic file: {e}")
                import traceback
                traceback.print_exc()
                raise

        # Step 2: Add sheet symbol to parent schematic FIRST
        # This must happen BEFORE adding components so the hierarchical path is available
        print(f"\n📝 STEP 2: Add sheet symbol to parent schematic")
        print(f"   Parent schematic: {parent_sheet.file_path}")

        sheet_uuid = None
        try:
            import kicad_sch_api as ksa
            import uuid as uuid_module

            # Load the parent schematic
            parent_sch = ksa.Schematic.load(str(parent_sheet.file_path))

            # CRITICAL: Set the project name for proper sheet instance references
            # Without this, sheet instances get "project None" causing R? display
            project_name = parent_sheet.file_path.parent.name
            parent_sch.name = project_name
            if hasattr(parent_sch, '_parser'):
                parent_sch._parser.project_name = project_name

            print(f"   ✅ Loaded parent schematic (project: {project_name})")

            # Create a sheet symbol
            sheet_uuid = str(uuid_module.uuid4())
            print(f"   Creating sheet symbol with UUID: {sheet_uuid}")

            # Determine position for the new sheet (simple: place at 50, 50)
            sheet_x = 50.0
            sheet_y = 50.0
            sheet_width = 50.0
            sheet_height = 30.0

            print(f"   Position: ({sheet_x}, {sheet_y}), Size: {sheet_width}x{sheet_height}")

            # Create sheet using kicad-sch-api
            new_sheet = parent_sch.add_sheet(
                name=sheet_name,
                filename=f"{sheet_name}.kicad_sch",
                position=(sheet_x, sheet_y),
                size=(sheet_width, sheet_height),
                uuid=sheet_uuid
            )

            print(f"   ✅ Added sheet symbol to parent")

            # Save the parent schematic
            parent_sch.save(str(parent_sheet.file_path))
            print(f"   ✅ Saved parent schematic with new sheet symbol")

        except Exception as e:
            print(f"   ❌ ERROR adding sheet symbol: {e}")
            print(f"   Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            print(f"   ⚠️  Continuing to add components (sheet hierarchy may be incorrect)")

        # Step 3: NOW synchronize components into the child sheet
        # The sheet exists in parent now, so hierarchical paths will be correct
        print(f"\n📝 STEP 3: Synchronize components into child sheet")
        print(f"   Circuit has {len(circuit_obj.components)} components to sync")

        # Log component references BEFORE sync
        print(f"\n🔍 COMPONENT REFERENCES BEFORE SYNC:")
        for i, comp in enumerate(circuit_obj.components):
            ref = comp.reference if hasattr(comp, 'reference') else '???'
            lib_id = comp.lib_id if hasattr(comp, 'lib_id') else '???'
            print(f"      [{i}] {ref} ({lib_id})")

        try:
            # Create a synchronizer for the new child sheet
            child_synchronizer = APISynchronizer(
                str(child_sch_path),
                preserve_user_components=self.preserve_user_components
            )

            # Synchronize the circuit into the new sheet
            sync_report = child_synchronizer.sync_with_circuit(circuit_obj)

            # Handle both dict and SyncReport object
            if hasattr(sync_report, 'added'):
                added_count = len(sync_report.added)
            elif isinstance(sync_report, dict):
                added_count = sync_report.get('added', 0)
            else:
                added_count = 0

            print(f"   ✅ Synchronized {added_count} components")

            # Log what was actually added
            if hasattr(sync_report, 'added'):
                print(f"\n🔍 COMPONENTS ADDED BY SYNC:")
                for comp_ref in sync_report.added:
                    print(f"      - {comp_ref}")

        except Exception as e:
            print(f"   ❌ ERROR synchronizing components: {e}")
            import traceback
            traceback.print_exc()
            raise

        # All steps complete
        print(f"\n✅ Sheet creation complete!")
        print(f"   - Blank sheet file created")
        print(f"   - Sheet symbol added to parent with UUID: {sheet_uuid}")
        print(f"   - Components synchronized to child sheet")

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
