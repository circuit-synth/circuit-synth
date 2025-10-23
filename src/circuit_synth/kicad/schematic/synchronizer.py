"""
KiCad API-based Schematic Synchronizer

This module provides the main synchronization functionality using the KiCad API
components for improved accuracy and performance.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import kicad_sch_api as ksa
from kicad_sch_api.core.types import Schematic, SchematicSymbol
from .component_manager import ComponentManager
from .connection_tracer import ConnectionTracer
from .net_matcher import NetMatcher
from .search_engine import SearchEngine, SearchQueryBuilder
from .sync_strategies import (
    ConnectionMatchStrategy,
    ReferenceMatchStrategy,
    SyncStrategy,
    ValueFootprintStrategy,
)

logger = logging.getLogger(__name__)


@dataclass
class SyncReport:
    """Report of synchronization results."""

    matched: Dict[str, str] = field(default_factory=dict)  # circuit_id -> kicad_ref
    added: List[str] = field(default_factory=list)
    modified: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)
    preserved: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for compatibility."""
        return {
            "matched_components": self.matched,
            "components_to_add": [{"circuit_id": cid} for cid in self.added],
            "components_to_modify": [{"reference": ref} for ref in self.modified],
            "components_to_preserve": [{"reference": ref} for ref in self.preserved],
            "summary": {
                "matched": len(self.matched),
                "added": len(self.added),
                "modified": len(self.modified),
                "preserved": len(self.preserved),
                "removed": len(self.removed),
            },
        }


class APISynchronizer:
    """
    API-based synchronizer for updating KiCad schematics from Circuit Synth.

    This class uses the new KiCad API components for improved matching
    and manipulation of schematic elements.
    """

    def __init__(self, schematic_path: str, preserve_user_components: bool = True):
        """
        Initialize the API synchronizer.

        Args:
            schematic_path: Path to the KiCad schematic file
            preserve_user_components: Whether to keep components not in circuit
        """
        self.schematic_path = Path(schematic_path)
        self.preserve_user_components = preserve_user_components

        # Load schematic
        self.schematic = self._load_schematic()

        # NOTE: file_path is already set when the schematic is loaded from file
        # The Schematic object's file_path property is read-only, so we can't set it

        # Initialize API components
        self.component_manager = ComponentManager(self.schematic)
        self.search_engine = SearchEngine(self.schematic)
        self.connection_tracer = ConnectionTracer(self.schematic)
        self.net_matcher = NetMatcher(self.connection_tracer)

        # Initialize matching strategies
        self.strategies = [
            ReferenceMatchStrategy(self.search_engine),
            ConnectionMatchStrategy(self.net_matcher),
            ValueFootprintStrategy(self.search_engine),
        ]

        logger.info(f"APISynchronizer initialized for: {schematic_path}")

    def _load_schematic(self) -> Schematic:
        """Load schematic from file and recursively load all hierarchical sheets."""
        # Load the main schematic
        main_schematic = ksa.Schematic.load(str(self.schematic_path))

        # Track loaded files to avoid infinite recursion
        loaded_files = set()
        loaded_files.add(str(self.schematic_path.resolve()))

        # Recursively load all components from hierarchical sheets
        self._load_sheets_recursively(
            main_schematic, self.schematic_path.parent, loaded_files
        )

        return main_schematic

    def _load_sheets_recursively(
        self, schematic: Schematic, base_path: Path, loaded_files: set
    ):
        """Recursively load components from all hierarchical sheets."""
        # Check if the schematic has sheets attribute and if it's iterable
        if not hasattr(schematic, 'sheets') or schematic.sheets is None:
            logger.debug(f"Schematic has no sheets attribute or it's None - skipping hierarchical loading")
            return

        # Check if sheets is empty
        try:
            sheets_list = list(schematic.sheets) if schematic.sheets else []
        except (TypeError, AttributeError):
            logger.debug(f"Schematic.sheets is not iterable - skipping hierarchical loading")
            return

        if not sheets_list:
            logger.debug(f"Schematic has no sheets - skipping hierarchical loading")
            return

        for sheet in sheets_list:
            # Construct the full path to the sheet file
            sheet_path = base_path / sheet.filename

            # Skip if we've already loaded this file (avoid infinite recursion)
            if str(sheet_path.resolve()) in loaded_files:
                continue

            if sheet_path.exists():
                logger.info(
                    f"Loading hierarchical sheet: {sheet.name} from {sheet.filename}"
                )
                loaded_files.add(str(sheet_path.resolve()))

                # Parse the sheet schematic
                sheet_schematic = ksa.Schematic.load(str(sheet_path))

                # Add all components from the sheet to the main schematic
                if hasattr(sheet_schematic, 'components') and sheet_schematic.components:
                    for comp in sheet_schematic.components:
                        schematic.add_component(comp)

                # Add all wires from the sheet (if they exist)
                if hasattr(sheet_schematic, 'wires') and sheet_schematic.wires:
                    try:
                        for wire in sheet_schematic.wires:
                            schematic.add_wire(wire)
                    except (TypeError, AttributeError) as e:
                        logger.debug(f"Could not add wires from sheet: {e}")

                # Add all labels from the sheet (if they exist)
                if hasattr(sheet_schematic, 'labels') and sheet_schematic.labels:
                    try:
                        for label in sheet_schematic.labels:
                            schematic.add_label(label)
                    except (TypeError, AttributeError) as e:
                        logger.debug(f"Could not add labels from sheet: {e}")

                # Recursively load any sub-sheets (if they exist)
                if hasattr(sheet_schematic, 'sheets') and sheet_schematic.sheets:
                    self._load_sheets_recursively(schematic, base_path, loaded_files)
            else:
                logger.warning(f"Sheet file not found: {sheet_path}")

    def sync_with_circuit(self, circuit) -> SyncReport:
        """
        Synchronize the KiCad schematic with a Circuit Synth circuit.

        Args:
            circuit: Circuit object from Circuit Synth

        Returns:
            SyncReport with synchronization results
        """
        logger.info("Starting API-based synchronization")

        report = SyncReport()

        try:
            # Extract components from circuit
            circuit_components = self._extract_circuit_components(circuit)
            logger.info(f"=== CIRCUIT COMPONENTS EXTRACTED ===")
            for comp_id, comp_data in circuit_components.items():
                logger.info(f"  Circuit Component: {comp_id}")
                logger.info(f"    Reference: {comp_data.get('reference')}")
                logger.info(f"    Value: {comp_data.get('value')}")
                logger.info(f"    Symbol: {comp_data.get('symbol')}")

            kicad_components = {c.reference: c for c in self.schematic.components}
            logger.info(f"=== KICAD COMPONENTS FOUND ===")
            for ref, comp in kicad_components.items():
                logger.info(f"  KiCad Component: {ref}")
                logger.info(f"    Value: {getattr(comp, 'value', 'N/A')}")
                logger.info(f"    Symbol: {getattr(comp, 'lib_id', 'N/A')}")
                logger.info(
                    f"    Position: ({getattr(comp, 'at_x', 'N/A')}, {getattr(comp, 'at_y', 'N/A')})"
                )

            # Match components using strategies
            matches = self._match_components(circuit_components, kicad_components)
            report.matched = matches

            logger.info(f"=== MATCHING RESULTS ===")
            logger.info(f"  Total circuit components: {len(circuit_components)}")
            logger.info(f"  Total KiCad components: {len(kicad_components)}")
            logger.info(f"  Total matches found: {len(matches)}")
            for circuit_id, kicad_ref in matches.items():
                logger.info(f"    MATCHED: {circuit_id} -> {kicad_ref}")

            # Process matches
            self._process_matches(circuit_components, kicad_components, matches, report)

            # Handle unmatched components
            self._process_unmatched(
                circuit_components, kicad_components, matches, report
            )

            # Save changes
            self._save_schematic()

            # Print user-friendly synchronization summary
            self._print_sync_summary(circuit_components, kicad_components, report)

            logger.info(
                f"Synchronization complete: {len(report.matched)} matched, "
                f"{len(report.added)} added, {len(report.modified)} modified"
            )

        except Exception as e:
            logger.error(f"Synchronization failed: {e}")
            print(f"[ERROR] Synchronization failed: {e}")
            import traceback

            traceback.print_exc()
            report.errors.append(str(e))
            raise

        return report

    def _print_sync_summary(
        self, circuit_components: Dict, kicad_components: Dict, report: SyncReport
    ):
        """Print a user-friendly synchronization summary."""
        print("\n" + "="*70)
        print("📋 Synchronization Summary")
        print("="*70)

        # Components in schematic (KiCad)
        kicad_refs = sorted(kicad_components.keys()) if kicad_components else []
        print(f"Components in schematic: {', '.join(kicad_refs) if kicad_refs else '(none)'}")

        # Components in Python code
        circuit_refs = sorted([comp['reference'] for comp in circuit_components.values()])
        print(f"Components in Python:    {', '.join(circuit_refs) if circuit_refs else '(none)'}")

        print("\nActions:")

        # Components that were kept (matched)
        if report.matched:
            matched_refs = sorted([kicad_ref for _, kicad_ref in report.matched.items()])
            for ref in matched_refs:
                print(f"   ✅ Keep: {ref} (matches Python)")

        # Components that were added
        if report.added:
            added_refs = sorted(report.added)
            for ref in added_refs:
                print(f"   ➕ Add: {ref} (new in Python)")

        # Components that were modified
        if report.modified:
            modified_refs = sorted(report.modified)
            for ref in modified_refs:
                print(f"   🔧 Update: {ref} (changed in Python)")

        # Components that will be removed (in KiCad but not in Python)
        matched_kicad_refs = set(report.matched.values())
        removed_refs = sorted([ref for ref in kicad_refs if ref not in matched_kicad_refs and ref not in report.added])
        if removed_refs:
            for ref in removed_refs:
                print(f"   ⚠️  Remove: {ref} (not in Python code)")

        if not report.matched and not report.added and not report.modified and not removed_refs:
            print("   (no changes)")

        print("="*70 + "\n")

    def _extract_circuit_components(self, circuit) -> Dict[str, Dict[str, Any]]:
        """Extract component information from Circuit Synth circuit."""
        result = {}

        # Recursive function to get all components including from subcircuits
        def get_all_components(circ):
            components = []

            # Get direct components
            if hasattr(circ, "_components"):
                components.extend(circ._components.values())
            elif hasattr(circ, "components"):
                components.extend(circ.components)

            # Get components from subcircuits
            if hasattr(circ, "_subcircuits"):
                for subcircuit in circ._subcircuits:
                    components.extend(get_all_components(subcircuit))

            return components

        # Get all components recursively
        all_components = get_all_components(circuit)

        for comp in all_components:
            # Debug: Check component type and attributes
            logger.debug(
                f"Processing component: {type(comp).__name__}, attributes: {dir(comp)}"
            )

            # Handle different component types
            if hasattr(comp, "reference"):  # KiCad SchematicSymbol
                comp_id = comp.reference
                comp_ref = comp.reference
                comp_value = getattr(comp, "value", "")
                comp_symbol = getattr(comp, "lib_id", None)
                comp_footprint = getattr(comp, "footprint", None)
            else:  # Circuit Synth Component
                comp_id = comp.id if hasattr(comp, "id") else comp.ref
                comp_ref = comp.ref
                comp_value = comp.value
                comp_symbol = getattr(comp, "symbol", None)
                comp_footprint = getattr(comp, "footprint", None)

            result[comp_id] = {
                "id": comp_id,
                "reference": comp_ref,
                "value": comp_value,
                "symbol": comp_symbol,  # Add symbol field
                "footprint": comp_footprint,
                "pins": self._extract_pin_info(comp),
                "original": comp,
            }

        return result

    def _extract_pin_info(self, component) -> Dict[str, str]:
        """Extract pin to net mapping for a component."""
        pins = {}
        if hasattr(component, "_pins"):
            for pin_num, pin in component._pins.items():
                if pin.net:
                    pins[pin_num] = pin.net.name
        return pins

    def _match_components(
        self, circuit_components: Dict, kicad_components: Dict
    ) -> Dict[str, str]:
        """Match components using multiple strategies."""
        all_matches = {}

        logger.info(f"=== COMPONENT MATCHING STRATEGIES ===")
        for i, strategy in enumerate(self.strategies):
            strategy_name = strategy.__class__.__name__
            logger.info(f"  Strategy {i+1}: {strategy_name}")

            matches = strategy.match_components(circuit_components, kicad_components)
            logger.info(f"    Found {len(matches)} matches:")
            for circuit_id, kicad_ref in matches.items():
                logger.info(f"      {circuit_id} -> {kicad_ref}")

            # Add new matches that don't conflict
            new_matches_added = 0
            for circuit_id, kicad_ref in matches.items():
                if (
                    circuit_id not in all_matches
                    and kicad_ref not in all_matches.values()
                ):
                    all_matches[circuit_id] = kicad_ref
                    new_matches_added += 1
                    logger.info(f"      ADDED: {circuit_id} -> {kicad_ref}")
                else:
                    if circuit_id in all_matches:
                        logger.info(
                            f"      SKIPPED (circuit_id conflict): {circuit_id} already matched to {all_matches[circuit_id]}"
                        )
                    if kicad_ref in all_matches.values():
                        existing_circuit_id = [
                            k for k, v in all_matches.items() if v == kicad_ref
                        ][0]
                        logger.info(
                            f"      SKIPPED (kicad_ref conflict): {kicad_ref} already matched to {existing_circuit_id}"
                        )

            logger.info(
                f"    New matches added from this strategy: {new_matches_added}"
            )

        logger.info(f"  Final matches after all strategies: {len(all_matches)}")
        return all_matches

    def _process_matches(
        self,
        circuit_components: Dict,
        kicad_components: Dict,
        matches: Dict[str, str],
        report: SyncReport,
    ):
        """Process matched components for updates."""
        for circuit_id, kicad_ref in matches.items():
            circuit_comp = circuit_components[circuit_id]
            kicad_comp = kicad_components[kicad_ref]

            # Check if update needed
            if self._needs_update(circuit_comp, kicad_comp):
                success = self.component_manager.update_component(
                    kicad_ref,
                    value=circuit_comp["value"],
                    footprint=circuit_comp.get("footprint"),
                )
                if success:
                    report.modified.append(kicad_ref)

    def _needs_update(self, circuit_comp: Dict, kicad_comp: SchematicSymbol) -> bool:
        """Check if a component needs updating."""
        if circuit_comp["value"] != kicad_comp.value:
            return True
        if (
            circuit_comp.get("footprint")
            and circuit_comp["footprint"] != kicad_comp.footprint
        ):
            return True
        # Always ensure components have proper BOM and board inclusion flags
        # This fixes the "?" symbol issue caused by in_bom=no or on_board=no
        if not kicad_comp.in_bom or not kicad_comp.on_board:
            logger.debug(
                f"Component {kicad_comp.reference} needs update for BOM/board flags: in_bom={kicad_comp.in_bom}, on_board={kicad_comp.on_board}"
            )
            return True
        return False

    def _process_unmatched(
        self,
        circuit_components: Dict,
        kicad_components: Dict,
        matches: Dict[str, str],
        report: SyncReport,
    ):
        """Process unmatched components."""
        logger.info(f"=== PROCESSING UNMATCHED COMPONENTS ===")

        # Find circuit components to add
        matched_circuit_ids = set(matches.keys())
        unmatched_circuit_components = []
        for circuit_id, comp_data in circuit_components.items():
            if circuit_id not in matched_circuit_ids:
                unmatched_circuit_components.append((circuit_id, comp_data))

        logger.info(f"  Circuit components to ADD: {len(unmatched_circuit_components)}")
        for circuit_id, comp_data in unmatched_circuit_components:
            logger.info(
                f"    ADDING: {circuit_id} (ref={comp_data.get('reference')}, value={comp_data.get('value')})"
            )
            self._add_component(comp_data, report)

        # Find KiCad components to preserve/remove
        matched_kicad_refs = set(matches.values())
        unmatched_kicad_components = []
        for kicad_ref in kicad_components:
            if kicad_ref not in matched_kicad_refs:
                unmatched_kicad_components.append(kicad_ref)

        logger.info(
            f"  KiCad components to PRESERVE/REMOVE: {len(unmatched_kicad_components)}"
        )
        for kicad_ref in unmatched_kicad_components:
            kicad_comp = kicad_components[kicad_ref]
            logger.info(
                f"    UNMATCHED KiCad: {kicad_ref} (value={getattr(kicad_comp, 'value', 'N/A')})"
            )
            if self.preserve_user_components:
                logger.info(f"      -> PRESERVING (preserve_user_components=True)")
                report.preserved.append(kicad_ref)
            else:
                logger.info(f"      -> REMOVING (preserve_user_components=False)")
                self.component_manager.remove_component(kicad_ref)
                report.removed.append(kicad_ref)

    def _add_component(self, comp_data: Dict, report: SyncReport):
        """Add a new component to the schematic."""
        # Determine library ID from component type
        lib_id = self._determine_library_id(comp_data)

        component = self.component_manager.add_component(
            library_id=lib_id,
            reference=comp_data["reference"],
            value=comp_data["value"],
            footprint=comp_data.get("footprint"),
            placement_strategy="edge_right",  # Place new components on right edge
        )

        if component:
            report.added.append(comp_data["id"])

    def _determine_library_id(self, comp_data: Dict) -> str:
        """Determine KiCad library ID from component data."""
        # Check if the component has a symbol field
        if "symbol" in comp_data and comp_data["symbol"]:
            return comp_data["symbol"]

        # Fallback to simple mapping based on reference
        ref = comp_data["reference"]
        if ref.startswith("R"):
            return "Device:R"
        elif ref.startswith("C"):
            return "Device:C"
        elif ref.startswith("L"):
            return "Device:L"
        elif ref.startswith("D"):
            return "Device:D"
        elif ref.startswith("U"):
            return "Device:R"  # Generic IC placeholder
        elif ref.startswith("J") or ref.startswith("P"):
            return "Connector:Conn_01x02_Pin"  # Generic connector
        else:
            return "Device:R"  # Default

    def _save_schematic(self):
        """Save the modified schematic using kicad-sch-api's native save."""
        logger.debug("Saving schematic")

        # WORKAROUND: kicad-sch-api bug where WireCollection doesn't sync to _data["wires"]
        # Manually sync wires from collection to _data before saving
        self._sync_wires_to_data()

        # Use kicad-sch-api's built-in save method which handles all S-expression formatting
        # and lib_symbols automatically. This preserves format and includes wires/labels.
        self.schematic.save(str(self.schematic_path), preserve_format=True)
        logger.info(f"✅ Schematic saved successfully")

    def _sync_wires_to_data(self):
        """
        Sync wires from WireCollection to _data dictionary.

        WORKAROUND for kicad-sch-api bug: The WireCollection maintains wires in memory
        but doesn't update _data["wires"], so when saving, wires are lost. This method
        manually syncs the wire collection to _data before saving.
        """
        if not hasattr(self.schematic, '_data'):
            logger.warning("Schematic has no _data attribute")
            return

        if not hasattr(self.schematic, 'wires'):
            logger.warning("Schematic has no wires attribute")
            return

        # Get all wires from the wire collection
        try:
            wires_list = list(self.schematic.wires)
            logger.debug(f"Retrieved {len(wires_list)} wires from collection")
        except (TypeError, AttributeError) as e:
            logger.warning(f"Could not access wires collection: {e}")
            return

        if not wires_list:
            # No wires to sync
            logger.debug("No wires to sync (empty list)")
            return

        logger.debug(f"Syncing {len(wires_list)} wires to _data")

        # Convert Wire objects to dictionaries for _data
        wire_dicts = []
        for wire in wires_list:
            if not hasattr(wire, 'uuid') or not hasattr(wire, 'points'):
                continue

            # Build wire dictionary matching KiCad S-expression format
            wire_dict = {
                "uuid": wire.uuid,
                "points": []
            }

            # Add points
            for point in wire.points:
                wire_dict["points"].append({
                    "x": point.x,
                    "y": point.y
                })

            # Add stroke info if present
            if hasattr(wire, 'stroke_width') and wire.stroke_width > 0:
                wire_dict["stroke"] = {
                    "width": wire.stroke_width,
                    "type": "default"
                }

            wire_dicts.append(wire_dict)

        # Update _data["wires"]
        self.schematic._data["wires"] = wire_dicts
        logger.info(f"Synced {len(wire_dicts)} wires to _data")
