"""
KiCad API-based Schematic Synchronizer

This module provides the main synchronization functionality using the KiCad API
components for improved accuracy and performance.
"""

import logging
import math
import uuid as uuid_module
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import kicad_sch_api as ksa
from kicad_sch_api.core.types import Label, LabelType, Point, Schematic, SchematicSymbol

from ..core.symbol_cache import get_symbol_cache
from .component_manager import ComponentManager
from .connection_tracer import ConnectionTracer
from .label_manager import LabelManager
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

    # Net/label tracking
    labels_added: List[Tuple[str, str, str]] = field(default_factory=list)  # (component, pin, net)
    labels_removed: List[Tuple[str, str, str]] = field(default_factory=list)  # (component, pin, net)
    labels_updated: List[Tuple[str, str, str, str]] = field(default_factory=list)  # (component, pin, old_net, new_net)

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

    def __init__(self, schematic_path: str, preserve_user_components: bool = False):
        """
        Initialize the API synchronizer.

        Args:
            schematic_path: Path to the KiCad schematic file
            preserve_user_components: Whether to keep components not in circuit (default: False)
        """
        self.schematic_path = Path(schematic_path)
        self.preserve_user_components = preserve_user_components

        # Load schematic
        self.schematic = self._load_schematic()

        # NOTE: file_path is already set when the schematic is loaded from file
        # The Schematic object's file_path property is read-only, so we can't set it

        # Initialize API components
        self.component_manager = ComponentManager(self.schematic)
        self.label_manager = LabelManager(self.schematic)
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
        if not hasattr(schematic, "sheets") or schematic.sheets is None:
            logger.debug(
                f"Schematic has no sheets attribute or it's None - skipping hierarchical loading"
            )
            return

        # Check if sheets is empty
        try:
            sheets_list = list(schematic.sheets) if schematic.sheets else []
        except (TypeError, AttributeError):
            logger.debug(
                f"Schematic.sheets is not iterable - skipping hierarchical loading"
            )
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
                if (
                    hasattr(sheet_schematic, "components")
                    and sheet_schematic.components
                ):
                    for comp in sheet_schematic.components:
                        schematic.add_component(comp)

                # Add all wires from the sheet (if they exist)
                if hasattr(sheet_schematic, "wires") and sheet_schematic.wires:
                    try:
                        for wire in sheet_schematic.wires:
                            schematic.add_wire(wire)
                    except (TypeError, AttributeError) as e:
                        logger.debug(f"Could not add wires from sheet: {e}")

                # Add all labels from the sheet (if they exist)
                if hasattr(sheet_schematic, "labels") and sheet_schematic.labels:
                    try:
                        for label in sheet_schematic.labels:
                            schematic.add_label(label)
                    except (TypeError, AttributeError) as e:
                        logger.debug(f"Could not add labels from sheet: {e}")

                # Recursively load any sub-sheets (if they exist)
                if hasattr(sheet_schematic, "sheets") and sheet_schematic.sheets:
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

            # Reconcile pin connections and labels
            self._reconcile_pin_connections(
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
        print("\n" + "=" * 70)
        print("📋 Synchronization Summary")
        print("=" * 70)

        # Components in schematic (KiCad)
        kicad_refs = sorted(kicad_components.keys()) if kicad_components else []
        print(
            f"Components in schematic: {', '.join(kicad_refs) if kicad_refs else '(none)'}"
        )

        # Components in Python code
        circuit_refs = sorted(
            [comp["reference"] for comp in circuit_components.values()]
        )
        print(
            f"Components in Python:    {', '.join(circuit_refs) if circuit_refs else '(none)'}"
        )

        print("\nActions:")

        # Components that were kept (matched)
        if report.matched:
            matched_refs = sorted(
                [kicad_ref for _, kicad_ref in report.matched.items()]
            )
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
        removed_refs = sorted(
            [
                ref
                for ref in kicad_refs
                if ref not in matched_kicad_refs and ref not in report.added
            ]
        )
        if removed_refs:
            for ref in removed_refs:
                print(f"   ⚠️  Remove: {ref} (not in Python code)")

        # Components that were preserved (exist in KiCad but not Python)
        if report.preserved:
            preserved_refs = sorted(report.preserved)
            print(f"\n   ⚠️  PRESERVED (preserve_user_components=True):")
            for ref in preserved_refs:
                print(f"      {ref} (exists in KiCad but not in Python)")
            print(f"   💡 Tip: Set preserve_user_components=False to remove these")

        if (
            not report.matched
            and not report.added
            and not report.modified
            and not removed_refs
            and not report.preserved
        ):
            print("   (no changes)")

        # Net/Label operations
        if report.labels_added or report.labels_removed or report.labels_updated:
            print("\nNet Labels:")

            if report.labels_added:
                print(f"   ➕ Added {len(report.labels_added)} label(s):")
                for comp_ref, pin, net in sorted(report.labels_added):
                    print(f"      {comp_ref} pin {pin} → {net}")

            if report.labels_removed:
                print(f"   ➖ Removed {len(report.labels_removed)} label(s):")
                for comp_ref, pin, net in sorted(report.labels_removed):
                    print(f"      {comp_ref} pin {pin} (was {net})")

            if report.labels_updated:
                print(f"   🔧 Updated {len(report.labels_updated)} label(s):")
                for comp_ref, pin, old_net, new_net in sorted(report.labels_updated):
                    print(f"      {comp_ref} pin {pin}: '{old_net}' → '{new_net}'")

        print("=" * 70 + "\n")

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

        # IMPORTANT: Also extract pin connections from nets
        # The component._pins may not be available after KiCad processing,
        # but the circuit.nets still contain the original connection information
        logger.debug(f"🔍 Circuit has nets attribute: {hasattr(circuit, 'nets')}")
        if hasattr(circuit, "nets"):
            nets_dict = circuit.nets if isinstance(circuit.nets, dict) else {n.name: n for n in circuit.nets}
            logger.debug(f"Extracting pin info from {len(nets_dict)} nets")
            for net_name, net in nets_dict.items():
                if hasattr(net, "connections"):
                    logger.debug(f"  Net '{net_name}' has {len(net.connections)} connections")
                    for comp_ref, pin_num in net.connections:
                        # Find the component in result
                        comp_data = None
                        for cid, cdata in result.items():
                            if cdata["reference"] == comp_ref:
                                comp_data = cdata
                                break

                        if comp_data:
                            # Add pin connection
                            if not comp_data["pins"]:
                                comp_data["pins"] = {}
                            comp_data["pins"][str(pin_num)] = net_name
                            logger.debug(f"    Added: {comp_ref} pin {pin_num} -> {net_name}")

        return result

    def _extract_pin_info(self, component) -> Dict[str, str]:
        """Extract pin to net mapping for a component."""
        pins = {}
        if hasattr(component, "_pins"):
            for pin_num, pin in component._pins.items():
                if pin.net:
                    pins[pin_num] = pin.net.name
        return pins

    def _get_pin_labels(self, kicad_component: SchematicSymbol) -> Dict[str, Label]:
        """
        Get existing labels at component pins.

        Returns:
            Dict mapping pin_number -> Label object for labels at this component's pins
        """
        pin_labels = {}

        # Get symbol data to know pin positions
        symbol_cache = get_symbol_cache()
        symbol_def = symbol_cache.get_symbol(kicad_component.lib_id)
        if not symbol_def or not hasattr(symbol_def, 'pins'):
            logger.warning(f"No pin data for {kicad_component.reference} ({kicad_component.lib_id})")
            return pin_labels

        # For each pin, check if there's a label at that position
        for pin in symbol_def.pins:
            pin_pos = self._calculate_pin_position(kicad_component, pin)
            if pin_pos:
                # Find labels near this pin position (within 0.5mm tolerance)
                for label in self.schematic.labels:
                    distance = math.sqrt(
                        (label.position.x - pin_pos.x) ** 2 +
                        (label.position.y - pin_pos.y) ** 2
                    )
                    if distance < 0.5:  # 0.5mm tolerance
                        pin_labels[str(pin.number)] = label
                        break

        return pin_labels

    def _calculate_pin_position(self, component: SchematicSymbol, pin) -> Optional[Point]:
        """
        Calculate the absolute position of a pin on a component.

        Args:
            component: The schematic component
            pin: The pin definition from symbol library

        Returns:
            Point with absolute pin position, or None if cannot calculate
        """
        try:
            # Get pin position from library data
            anchor_x = float(pin.x if hasattr(pin, 'x') else 0.0)
            anchor_y = float(pin.y if hasattr(pin, 'y') else 0.0)

            # Rotate by component rotation
            r = math.radians(component.rotation)
            local_x = anchor_x
            local_y = -anchor_y  # KiCad Y axis is inverted
            rx = (local_x * math.cos(r)) - (local_y * math.sin(r))
            ry = (local_x * math.sin(r)) + (local_y * math.cos(r))

            # Add component position
            global_x = component.position.x + rx
            global_y = component.position.y + ry

            return Point(global_x, global_y)

        except (AttributeError, TypeError) as e:
            logger.warning(f"Could not calculate pin position: {e}")
            return None

    def _add_pin_label(
        self,
        kicad_component: SchematicSymbol,
        pin_number: str,
        net_name: str,
        report: SyncReport
    ) -> bool:
        """
        Add a label at a component pin.

        Args:
            kicad_component: The KiCad component
            pin_number: Pin number to add label at
            net_name: Net name for the label
            report: Sync report to track the addition

        Returns:
            True if label added successfully
        """
        # Get symbol data
        symbol_cache = get_symbol_cache()
        symbol_def = symbol_cache.get_symbol(kicad_component.lib_id)
        if not symbol_def or not hasattr(symbol_def, 'pins'):
            logger.error(f"No pin data for {kicad_component.reference}")
            return False

        # Find the pin
        pin = None
        for p in symbol_def.pins:
            if str(p.number) == str(pin_number):
                pin = p
                break

        if not pin:
            logger.warning(f"Pin {pin_number} not found on {kicad_component.reference}")
            return False

        # Calculate pin position
        pin_pos = self._calculate_pin_position(kicad_component, pin)
        if not pin_pos:
            return False

        # Calculate label angle (opposite to pin direction)
        pin_angle = float(pin.angle if hasattr(pin, 'angle') else 0.0)
        label_angle = (pin_angle + 180) % 360
        global_angle = (label_angle + kicad_component.rotation) % 360

        # Use kicad-sch-api's add_hierarchical_label() method
        # Hierarchical labels create electrical connections (regular labels don't)
        try:
            logger.debug(f"Adding hierarchical label using schematic.add_hierarchical_label() API")

            # Use schematic.add_hierarchical_label() with proper signature
            # Note: hierarchical_label uses 'shape' instead of 'rotation' and 'size'
            label_uuid = self.schematic.add_hierarchical_label(
                text=net_name,
                position=(pin_pos.x, pin_pos.y),  # Tuple or Point both work
                shape="bidirectional"  # Default to bidirectional for nets
            )

            logger.debug(f"Label added: '{net_name}' at ({pin_pos.x:.2f}, {pin_pos.y:.2f}), UUID={label_uuid}")
            logger.info(f"Added label '{net_name}' at {kicad_component.reference} pin {pin_number}")
            report.labels_added.append((kicad_component.reference, pin_number, net_name))
            return True

        except Exception as e:
            logger.error(f"Failed to add label: {e}", exc_info=True)
            return False

    def _remove_pin_label(
        self,
        label: Label,
        component_ref: str,
        pin_number: str,
        report: SyncReport
    ) -> bool:
        """
        Remove a label from the schematic.

        Args:
            label: Label to remove
            component_ref: Component reference for tracking
            pin_number: Pin number for tracking
            report: Sync report to track the removal

        Returns:
            True if label removed successfully
        """
        try:
            # Use schematic.remove_label() API which handles both collection and _data
            removed = self.schematic.remove_label(label.uuid)

            if removed:
                logger.info(f"Removed label '{label.text}' from {component_ref} pin {pin_number}")
                report.labels_removed.append((component_ref, pin_number, label.text))
                return True
            else:
                logger.warning(f"Label {label.uuid} not found for removal")
                return False

        except Exception as e:
            logger.error(f"Failed to remove label: {e}", exc_info=True)
            return False

    def _update_pin_label(
        self,
        label: Label,
        new_net_name: str,
        component_ref: str,
        pin_number: str,
        report: SyncReport
    ) -> bool:
        """
        Update a label's net name.

        Args:
            label: Label to update
            new_net_name: New net name
            component_ref: Component reference for tracking
            pin_number: Pin number for tracking
            report: Sync report to track the update

        Returns:
            True if label updated successfully
        """
        old_name = label.text

        try:
            # Update label text directly - the collection wrapper handles sync
            label.text = new_net_name

            # Manually sync to _data since label property setter might not trigger it
            self.schematic._sync_labels_to_data()
            self.schematic._modified = True

            logger.info(f"Updated label at {component_ref} pin {pin_number}: '{old_name}' -> '{new_net_name}'")
            report.labels_updated.append((component_ref, pin_number, old_name, new_net_name))
            return True

        except Exception as e:
            logger.error(f"Failed to update label: {e}", exc_info=True)
            return False

    def _reconcile_pin_connections(
        self,
        circuit_components: Dict,
        kicad_components: Dict,
        matches: Dict[str, str],
        report: SyncReport,
    ):
        """
        Reconcile pin connections for all matched components.

        For each matched component:
        1. Get Python pin→net mapping
        2. Get KiCad pin→label mapping
        3. Add missing labels (Python has net, KiCad doesn't)
        4. Remove stale labels (KiCad has label, Python doesn't)
        5. Update changed labels (net name changed)

        Args:
            circuit_components: Components from Python circuit
            kicad_components: Components from KiCad schematic
            matches: Matched circuit_id -> kicad_ref
            report: Sync report to track changes
        """
        logger.info("🔌 Reconciling pin connections and labels")

        for circuit_id, kicad_ref in matches.items():
            circuit_comp = circuit_components[circuit_id]
            kicad_comp = kicad_components[kicad_ref]

            # Python says: these pins should connect to these nets
            python_pins = circuit_comp.get("pins", {})  # {pin_num: net_name}

            # KiCad says: these pins have these labels
            kicad_labels = self._get_pin_labels(kicad_comp)  # {pin_num: Label}

            logger.debug(f"  Component {kicad_ref}:")
            logger.debug(f"    Python pins: {python_pins}")
            logger.debug(f"    KiCad labels: {list(kicad_labels.keys())}")

            # Reconcile each pin
            all_pins = set(python_pins.keys()) | set(kicad_labels.keys())

            for pin_num in all_pins:
                python_net = python_pins.get(pin_num)
                kicad_label = kicad_labels.get(pin_num)

                if python_net and not kicad_label:
                    # ADD label - Python has net but KiCad doesn't have label
                    logger.debug(f"    ➕ ADD label: pin {pin_num} -> {python_net}")
                    self._add_pin_label(kicad_comp, pin_num, python_net, report)

                elif not python_net and kicad_label:
                    # REMOVE label - KiCad has label but Python doesn't have net
                    logger.debug(f"    ➖ REMOVE label: pin {pin_num} (was {kicad_label.text})")
                    self._remove_pin_label(kicad_label, kicad_ref, pin_num, report)

                elif python_net and kicad_label and python_net != kicad_label.text:
                    # UPDATE label - Net name changed
                    logger.debug(f"    🔧 UPDATE label: pin {pin_num} '{kicad_label.text}' -> '{python_net}'")
                    self._update_pin_label(kicad_label, python_net, kicad_ref, pin_num, report)

                else:
                    # No change needed
                    logger.debug(f"    ✅ KEEP label: pin {pin_num} -> {python_net}")

        logger.info(f"✅ Pin reconciliation complete: "
                   f"{len(report.labels_added)} added, "
                   f"{len(report.labels_removed)} removed, "
                   f"{len(report.labels_updated)} updated")

        # INVESTIGATION: Check if labels survived
        logger.info(f"🔍 POST-RECONCILIATION CHECK:")
        logger.info(f"   - Labels in collection: {len(list(self.schematic.labels))}")
        logger.info(f"   - Labels in _data: {len(self.schematic._data.get('labels', []))}")
        if hasattr(self.schematic, 'labels'):
            for i, label in enumerate(list(self.schematic.labels)[:3]):
                logger.info(f"   - Label {i}: {label.text}")

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
        logger.info("=" * 70)
        logger.info("🔍 SAVE INVESTIGATION: Starting schematic save")
        logger.info("=" * 70)

        # Investigate what's in the schematic before save
        logger.info(f"📊 Schematic state before save:")
        logger.info(f"   - Schematic path: {self.schematic_path}")
        logger.info(f"   - Has _data: {hasattr(self.schematic, '_data')}")

        if hasattr(self.schematic, '_data'):
            logger.info(f"   - Keys in _data: {list(self.schematic._data.keys())}")
            logger.info(f"   - Labels in _data: {len(self.schematic._data.get('labels', []))}")
            logger.info(f"   - Hierarchical labels in _data: {len(self.schematic._data.get('hierarchical_labels', []))}")

            # Log actual label content
            for i, label in enumerate(self.schematic._data.get('labels', [])[:5]):  # First 5
                logger.info(f"   - Label {i}: {label}")

        logger.info(f"   - Has labels collection: {hasattr(self.schematic, 'labels')}")
        if hasattr(self.schematic, 'labels'):
            try:
                labels_list = list(self.schematic.labels)
                logger.info(f"   - Labels in collection: {len(labels_list)}")
                for i, label in enumerate(labels_list[:5]):  # First 5
                    logger.info(f"   - Collection label {i}: text={label.text}, type={label.label_type}, pos={label.position}")
            except Exception as e:
                logger.error(f"   - Error accessing labels collection: {e}")

        # WORKAROUND: kicad-sch-api bug where WireCollection doesn't sync to _data["wires"]
        # Manually sync wires from collection to _data before saving
        self._sync_wires_to_data()

        # Labels are now synced automatically via schematic.add_label() API
        # which calls _sync_labels_to_data() internally, so no manual sync needed

        logger.info(f"💾 Calling schematic.save(preserve_format=False)")
        logger.info(f"   - Save path: {self.schematic_path}")
        logger.info(f"   - Using preserve_format=False to force full rewrite from _data")

        # Using preserve_format=False forces full rewrite from _data dictionary
        self.schematic.save(str(self.schematic_path), preserve_format=False)

        logger.info(f"✅ Save completed")
        logger.info("=" * 70)

    def _sync_wires_to_data(self):
        """
        Sync wires from WireCollection to _data dictionary.

        WORKAROUND for kicad-sch-api bug: The WireCollection maintains wires in memory
        but doesn't update _data["wires"], so when saving, wires are lost. This method
        manually syncs the wire collection to _data before saving.
        """
        if not hasattr(self.schematic, "_data"):
            logger.warning("Schematic has no _data attribute")
            return

        if not hasattr(self.schematic, "wires"):
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
            if not hasattr(wire, "uuid") or not hasattr(wire, "points"):
                continue

            # Build wire dictionary matching KiCad S-expression format
            wire_dict = {"uuid": wire.uuid, "points": []}

            # Add points
            for point in wire.points:
                wire_dict["points"].append({"x": point.x, "y": point.y})

            # Add stroke info if present
            if hasattr(wire, "stroke_width") and wire.stroke_width > 0:
                wire_dict["stroke"] = {"width": wire.stroke_width, "type": "default"}

            wire_dicts.append(wire_dict)

        # Update _data["wires"]
        self.schematic._data["wires"] = wire_dicts
        logger.info(f"Synced {len(wire_dicts)} wires to _data")
