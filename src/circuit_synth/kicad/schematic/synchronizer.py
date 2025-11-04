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
    PositionRenameStrategy,
    ReferenceMatchStrategy,
    SyncStrategy,
    UUIDMatchStrategy,
    ValueFootprintStrategy,
)

logger = logging.getLogger(__name__)

# Constants
POWER_SYMBOL_PREFIX = "#PWR"
PIN_LABEL_DISTANCE_TOLERANCE = 0.5  # mm - distance threshold for associating labels/symbols with pins


class PowerSymbolLabel:
    """
    Pseudo-label representing a power symbol at a pin location.

    This allows the synchronizer to detect power symbols the same way it detects
    regular and hierarchical labels, enabling unified handling of power net changes.
    """
    def __init__(self, power_comp):
        self.text = power_comp.value  # Power net name (VCC, GND, 3V3, etc.)
        self.position = power_comp.position
        self.component = power_comp  # Store reference to actual power symbol


@dataclass
class SyncReport:
    """Report of synchronization results."""

    matched: Dict[str, str] = field(default_factory=dict)  # circuit_id -> kicad_ref
    added: List[str] = field(default_factory=list)
    modified: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)
    preserved: List[str] = field(default_factory=list)
    renamed: List[Tuple[str, str]] = field(default_factory=list)  # (old_ref, new_ref)
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

        # Extract project name from schematic path
        project_name = self.schematic_path.stem  # e.g., "comprehensive_root.kicad_sch" -> "comprehensive_root"

        # Initialize API components
        self.component_manager = ComponentManager(self.schematic, project_name=project_name)
        self.label_manager = LabelManager(self.schematic)
        self.search_engine = SearchEngine(self.schematic)
        self.connection_tracer = ConnectionTracer(self.schematic)
        self.net_matcher = NetMatcher(self.connection_tracer)

        # Initialize matching strategies
        # Order matters: strategies are tried in sequence, first match wins
        self.strategies = [
            UUIDMatchStrategy(self.search_engine),        # UUID - most reliable (stable across changes)
            ReferenceMatchStrategy(self.search_engine),   # Exact reference match
            PositionRenameStrategy(self.search_engine),   # Detect renames by position+properties
            ConnectionMatchStrategy(self.net_matcher),    # Match by net topology
            ValueFootprintStrategy(self.search_engine),   # Match by value+footprint (fallback)
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

        # Store circuit for accessing nets (needed for power symbol placement)
        self.circuit = circuit

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

        # Components that were renamed
        if report.renamed:
            renamed_pairs = sorted(report.renamed)
            for old_ref, new_ref in renamed_pairs:
                print(f"   🔄 Rename: {old_ref} → {new_ref}")

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
                comp_position = getattr(comp, "position", None)
                comp_uuid = getattr(comp, "uuid", None)
            else:  # Circuit Synth Component
                comp_id = comp.id if hasattr(comp, "id") else comp.ref
                comp_ref = comp.ref
                comp_value = comp.value
                comp_symbol = getattr(comp, "symbol", None)
                comp_footprint = getattr(comp, "footprint", None)
                comp_position = getattr(comp, "position", None)
                comp_uuid = getattr(comp, "uuid", None)

            result[comp_id] = {
                "id": comp_id,
                "reference": comp_ref,
                "value": comp_value,
                "symbol": comp_symbol,  # Add symbol field
                "footprint": comp_footprint,
                "position": comp_position,  # Position for rename detection
                "uuid": comp_uuid,  # UUID for stable component identity
                "pins": self._extract_pin_info(comp),
                "original": comp,
            }

        # IMPORTANT: Also extract pin connections from nets
        # The component._pins may not be available after KiCad processing,
        # but the circuit.nets still contain the original connection information
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

    def _get_pin_labels(self, kicad_component: SchematicSymbol) -> Dict[str, tuple]:
        """
        Get existing labels at component pins.

        Returns:
            Dict mapping pin_number -> (Label object, label_type) tuple
            where label_type is either "regular" or "hierarchical"
        """
        pin_labels = {}

        # Get symbol data to know pin positions
        symbol_cache = get_symbol_cache()
        symbol_def = symbol_cache.get_symbol(kicad_component.lib_id)
        if not symbol_def or not hasattr(symbol_def, 'pins'):
            logger.warning(f"No pin data for {kicad_component.reference} ({kicad_component.lib_id})")
            return pin_labels

        # For each pin, check if there's a label at that position
        from .geometry_utils import GeometryUtils

        for pin in symbol_def.pins:
            # Use canonical pin position calculation
            # SchematicPin uses 'position' (Point) and 'rotation' instead of x/y/orientation
            pin_position = pin.position if hasattr(pin, 'position') else Point(0, 0)
            pin_dict = {
                "x": float(pin_position.x),
                "y": float(pin_position.y),
                "orientation": float(pin.rotation if hasattr(pin, 'rotation') else 0.0),
            }
            pin_pos, _ = GeometryUtils.calculate_pin_label_position_from_dict(
                pin_dict=pin_dict,
                component_position=kicad_component.position,
                component_rotation=kicad_component.rotation,
            )

            # Find labels near this pin position (within 0.5mm tolerance)
            # Check regular labels first
            for label in self.schematic.labels:
                distance = math.sqrt(
                    (label.position.x - pin_pos.x) ** 2 +
                    (label.position.y - pin_pos.y) ** 2
                )
                if distance < 0.5:  # 0.5mm tolerance
                    pin_labels[str(pin.number)] = (label, "regular")
                    break

            # Then check hierarchical labels if no regular label found
            if str(pin.number) not in pin_labels:
                for label in self.schematic.hierarchical_labels:
                    distance = math.sqrt(
                        (label.position.x - pin_pos.x) ** 2 +
                        (label.position.y - pin_pos.y) ** 2
                    )
                    if distance < 0.5:  # 0.5mm tolerance
                        pin_labels[str(pin.number)] = (label, "hierarchical")
                        break

            # Finally check for power symbols if no label found
            if str(pin.number) not in pin_labels:
                for component in self.schematic.components:
                    # Check if this is a power symbol
                    if component.reference.startswith(POWER_SYMBOL_PREFIX):
                        distance = math.sqrt(
                            (component.position.x - pin_pos.x) ** 2 +
                            (component.position.y - pin_pos.y) ** 2
                        )
                        if distance < PIN_LABEL_DISTANCE_TOLERANCE:
                            # Create a pseudo-label object representing the power symbol
                            # This allows the synchronizer to detect power net changes
                            pin_labels[str(pin.number)] = (PowerSymbolLabel(component), "power_symbol")
                            break

        return pin_labels

    def _get_net_object(self, net_name: str):
        """
        Get the Net object from the circuit by name.

        Args:
            net_name: Name of the net to find

        Returns:
            Net object if found, None otherwise
        """
        if not hasattr(self, 'circuit') or not self.circuit:
            return None

        # Access the circuit's nets
        if hasattr(self.circuit, 'nets'):
            for net in self.circuit.nets:
                if net.name == net_name:
                    return net

        return None

    def _get_next_power_reference(self) -> str:
        """
        Generate the next available power symbol reference.

        Returns:
            Next power reference like "#PWR01", "#PWR02", etc.
        """
        # Find highest existing power reference
        max_num = 0
        for component in self.schematic.components:
            ref = component.reference
            if ref.startswith("#PWR"):
                try:
                    num = int(ref[4:])
                    max_num = max(max_num, num)
                except (ValueError, IndexError):
                    continue

        # Return next reference
        next_num = max_num + 1
        return f"#PWR0{next_num:02d}"

    def _add_power_symbol(
        self,
        net_obj,
        net_name: str,
        position: Point,
        label_angle: float,
        component_ref: str,
        pin_number: str,
        report: SyncReport
    ) -> bool:
        """
        Add a power symbol at the specified position.

        This mirrors the logic in schematic_writer.py for consistency.

        Args:
            net_obj: The Net object containing power symbol info
            net_name: Name of the power net
            position: Position to place the power symbol
            label_angle: Label angle calculated for the pin
            component_ref: Component reference for logging
            pin_number: Pin number for logging
            report: Sync report to track the addition

        Returns:
            True if power symbol added successfully
        """
        try:
            # Generate unique power reference
            power_ref = self._get_next_power_reference()

            # Place power symbol directly at pin location (same as schematic_writer.py)
            power_x = position.x
            power_y = position.y

            # Calculate power symbol rotation (same logic as schematic_writer.py)
            # Power symbols use hierarchical label rotation with -90° adjustment
            base_rotation = (label_angle - 90) % 360

            # Check if this is a GND-type symbol (inverted)
            if "GND" in net_obj.power_symbol or "VSS" in net_obj.power_symbol:
                # GND symbols are inverted, need 180° flip
                power_rotation = float((base_rotation + 180) % 360)
            else:
                power_rotation = float(base_rotation)

            logger.debug(f"Power symbol rotation: label_angle={label_angle}° → base={base_rotation}° → final={power_rotation}°")

            # Add power symbol using component_manager (same as schematic_writer.py)
            # Note: We're using the synchronizer's component_manager directly
            power_comp = self.component_manager.add_component(
                library_id=net_obj.power_symbol,
                reference=power_ref,
                value=net_name,
                position=(power_x, power_y),
                footprint="",  # Power symbols have no footprint
                snap_to_grid=False,  # Power symbols need exact positioning
            )

            if not power_comp:
                logger.error(f"Failed to add power symbol {power_ref}")
                return False

            # Set rotation after creation
            power_comp.rotation = power_rotation

            # Power symbols are always in BOM but not on board
            power_comp.in_bom = True
            power_comp.on_board = True
            power_comp.dnp = False

            # FIX Issue #476: Adjust Value property position for power symbols
            # Same as schematic_writer.py - must be done AFTER rotation is set
            if hasattr(power_comp, "properties") and "Value" in power_comp.properties:
                value_prop = power_comp.properties["Value"]
                if hasattr(value_prop, "position"):
                    offset = 5.08  # Standard KiCad offset

                    if power_rotation == 0:  # Pointing up (VCC)
                        value_prop.position = Point(power_x, power_y - offset)
                    elif power_rotation == 90:  # Pointing left
                        value_prop.position = Point(power_x - offset, power_y)
                    elif power_rotation == 180:  # Pointing down (GND)
                        value_prop.position = Point(power_x, power_y + offset)
                    elif power_rotation == 270:  # Pointing right
                        value_prop.position = Point(power_x + offset, power_y)


            logger.info(f"Added power symbol {power_ref} for {net_name} at {component_ref} pin {pin_number}")
            report.labels_added.append((component_ref, pin_number, net_name))

            return True

        except Exception as e:
            logger.error(f"Failed to add power symbol: {e}", exc_info=True)
            return False

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
        # Get pin data from symbol library using the SAME source as initial placement
        # This ensures consistent pin orientation data between generation and synchronization
        from ..kicad_symbol_cache import SymbolLibCache
        from ..sch_gen.schematic_writer import find_pin_by_identifier
        from .geometry_utils import GeometryUtils

        lib_data = SymbolLibCache.get_symbol_data(kicad_component.lib_id)
        if not lib_data or "pins" not in lib_data:
            logger.error(f"No pin data for {kicad_component.reference}")
            return False

        # Find the pin using the same helper as initial placement
        pin_dict = find_pin_by_identifier(lib_data["pins"], pin_number)
        if not pin_dict:
            logger.warning(f"Pin {pin_number} not found on {kicad_component.reference}")
            return False

        # pin_dict now has correct format: {"x": ..., "y": ..., "orientation": ...}
        # No conversion needed - this is the canonical format

        logger.debug(f"SYNC LABEL: {kicad_component.reference} pin {pin_number}")
        logger.debug(f"  pin_dict: {pin_dict}")
        logger.debug(f"  component position: ({kicad_component.position.x}, {kicad_component.position.y})")
        logger.debug(f"  component rotation: {kicad_component.rotation}°")

        label_pos, label_angle = GeometryUtils.calculate_pin_label_position_from_dict(
            pin_dict=pin_dict,
            component_position=kicad_component.position,
            component_rotation=kicad_component.rotation,
        )

        logger.debug(f"  → label position: ({label_pos.x}, {label_pos.y})")
        logger.debug(f"  → label angle: {label_angle}°")

        # CHECK FOR POWER NETS: Place power symbol instead of hierarchical label
        # This matches the behavior in schematic_writer.py for consistency
        net_obj = self._get_net_object(net_name)

        if net_obj and hasattr(net_obj, 'is_power') and net_obj.is_power and hasattr(net_obj, 'power_symbol'):
            logger.info(f"Detected power net '{net_name}' -> placing power symbol instead of label")
            success = self._add_power_symbol(
                net_obj=net_obj,
                net_name=net_name,
                position=label_pos,
                label_angle=label_angle,
                component_ref=kicad_component.reference,
                pin_number=pin_number,
                report=report
            )
            return success

        # Use kicad-sch-api's add_hierarchical_label() method
        # Hierarchical labels create electrical connections (regular labels don't)
        try:
            logger.debug(f"Adding hierarchical label using schematic.add_hierarchical_label() API")

            # Use schematic.add_hierarchical_label() with proper signature
            label_uuid = self.schematic.add_hierarchical_label(
                text=net_name,
                position=(label_pos.x, label_pos.y),
                shape="bidirectional",  # Default to bidirectional for nets
                rotation=label_angle,  # CRITICAL: Must pass rotation for correct orientation!
            )

            # Use canonical justification calculation from label_utils
            from .label_utils import calculate_hierarchical_label_justify
            justify = calculate_hierarchical_label_justify(label_angle)

            # Update the label's justify in the schematic data
            if hasattr(self.schematic, "_data") and "hierarchical_labels" in self.schematic._data:
                for label_dict in self.schematic._data["hierarchical_labels"]:
                    if label_dict.get("uuid") == label_uuid:
                        # Ensure effects dict exists before updating justify
                        if "effects" not in label_dict:
                            label_dict["effects"] = {}
                        label_dict["effects"]["justify"] = justify
                        logger.debug(f"Set hierarchical label justify={justify} for rotation={label_angle}°")
                        break

            logger.debug(f"Label added: '{net_name}' at ({label_pos.x:.2f}, {label_pos.y:.2f}), angle={label_angle:.0f}, justify={justify}, UUID={label_uuid}")
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
        report: SyncReport,
        label_type: str = "regular"
    ) -> bool:
        """
        Remove a label from the schematic.

        Args:
            label: Label to remove
            component_ref: Component reference for tracking
            pin_number: Pin number for tracking
            report: Sync report to track the removal
            label_type: Type of label - "regular" or "hierarchical"

        Returns:
            True if label removed successfully
        """
        try:
            # Use the appropriate removal method based on label type
            if label_type == "hierarchical":
                removed = self.schematic.remove_hierarchical_label(label.uuid)
            else:
                removed = self.schematic.remove_label(label.uuid)

            if removed:
                logger.info(f"Removed {label_type} label '{label.text}' from {component_ref} pin {pin_number}")
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
        report: SyncReport,
        label_type: str = "regular"
    ) -> bool:
        """
        Update a label's net name.

        For power symbols, this removes the old power symbol and adds a new one
        because different power nets use different KiCad library symbols.

        Args:
            label: Label to update (or PowerSymbolLabel for power symbols)
            new_net_name: New net name
            component_ref: Component reference for tracking
            pin_number: Pin number for tracking
            report: Sync report to track the update
            label_type: Type of label - "regular", "hierarchical", or "power_symbol"

        Returns:
            True if label updated successfully
        """
        old_name = label.text

        try:
            # Special handling for power symbols - must replace (not just update text)
            # because different power nets use different KiCad library symbols
            if label_type == "power_symbol":
                logger.info(f"Power net changed at {component_ref} pin {pin_number}: '{old_name}' -> '{new_net_name}'")

                # Get the component first (fail fast if missing)
                kicad_comp = None
                for comp in self.schematic.components:
                    if comp.reference == component_ref:
                        kicad_comp = comp
                        break

                if not kicad_comp:
                    logger.error(f"Could not find component {component_ref} to update power symbol")
                    return False

                # Add new power symbol first
                add_success = self._add_pin_label(kicad_comp, pin_number, new_net_name, report)
                if not add_success:
                    logger.error(f"Failed to add new power symbol for {new_net_name} at {component_ref} pin {pin_number}")
                    return False

                # Only remove old power symbol after new one is successfully added
                old_power_symbol = label.component
                removed = self.component_manager.remove_component(old_power_symbol.reference)
                if not removed:
                    logger.warning(f"Could not remove old power symbol {old_power_symbol.reference} - new symbol added but old may remain")
                    # Don't return False - new symbol is in place, so partial success
                else:
                    logger.debug(f"Removed old power symbol {old_power_symbol.reference} ({old_name})")

                logger.info(f"Replaced power symbol at {component_ref} pin {pin_number}: '{old_name}' -> '{new_net_name}'")
                report.labels_updated.append((component_ref, pin_number, old_name, new_net_name))
                return True

            # Regular label or hierarchical label - just update the text
            else:
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

    def _reconcile_component_pins(
        self,
        circuit_id: str,
        kicad_ref: str,
        circuit_components: Dict,
        kicad_components: Dict,
        report: SyncReport,
    ):
        """
        Reconcile pin connections for a single component.

        For the component:
        1. Get Python pin→net mapping
        2. Get KiCad pin→label mapping
        3. Add missing labels (Python has net, KiCad doesn't)
        4. Remove stale labels (KiCad has label, Python doesn't)
        5. Update changed labels (net name changed)

        Args:
            circuit_id: Circuit component ID
            kicad_ref: KiCad component reference
            circuit_components: Components from Python circuit
            kicad_components: Components from KiCad schematic
            report: Sync report to track changes
        """
        circuit_comp = circuit_components[circuit_id]
        kicad_comp = kicad_components[kicad_ref]

        # Python says: these pins should connect to these nets
        python_pins = circuit_comp.get("pins", {})  # {pin_num: net_name}

        # KiCad says: these pins have these labels
        kicad_labels = self._get_pin_labels(kicad_comp)  # {pin_num: (Label, type)}

        logger.debug(f"  Component {kicad_ref}:")
        logger.debug(f"    Python pins: {python_pins}")
        logger.debug(f"    KiCad labels: {list(kicad_labels.keys())}")

        # Reconcile each pin
        all_pins = set(python_pins.keys()) | set(kicad_labels.keys())

        for pin_num in all_pins:
            python_net = python_pins.get(pin_num)
            kicad_label_tuple = kicad_labels.get(pin_num)

            # Unpack label and type if present
            kicad_label = kicad_label_tuple[0] if kicad_label_tuple else None
            label_type = kicad_label_tuple[1] if kicad_label_tuple else None

            if python_net and not kicad_label:
                # ADD label - Python has net but KiCad doesn't have label
                logger.debug(f"    ➕ ADD label: pin {pin_num} -> {python_net}")
                self._add_pin_label(kicad_comp, pin_num, python_net, report)

            elif not python_net and kicad_label:
                # REMOVE label - KiCad has label but Python doesn't have net
                logger.debug(f"    ➖ REMOVE label: pin {pin_num} (was {kicad_label.text}, type={label_type})")
                self._remove_pin_label(kicad_label, kicad_ref, pin_num, report, label_type)

            elif python_net and kicad_label and python_net != kicad_label.text:
                # UPDATE label - Net name changed
                logger.debug(f"    🔧 UPDATE label: pin {pin_num} '{kicad_label.text}' -> '{python_net}' (type={label_type})")
                self._update_pin_label(kicad_label, python_net, kicad_ref, pin_num, report, label_type)

            else:
                # No change needed
                logger.debug(f"    ✅ KEEP label: pin {pin_num} -> {python_net}")

    def _reconcile_pin_connections(
        self,
        circuit_components: Dict,
        kicad_components: Dict,
        matches: Dict[str, str],
        report: SyncReport,
    ):
        """
        Reconcile pin connections for all matched components.

        Args:
            circuit_components: Components from Python circuit
            kicad_components: Components from KiCad schematic
            matches: Matched circuit_id -> kicad_ref
            report: Sync report to track changes
        """
        logger.info("🔌 Reconciling pin connections and labels")

        for circuit_id, kicad_ref in matches.items():
            self._reconcile_component_pins(
                circuit_id, kicad_ref, circuit_components, kicad_components, report
            )

        logger.info(f"✅ Pin reconciliation complete: "
                   f"{len(report.labels_added)} added, "
                   f"{len(report.labels_removed)} removed, "
                   f"{len(report.labels_updated)} updated")

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
        """Process matched components for updates and renames."""
        for circuit_id, kicad_ref in matches.items():
            circuit_comp = circuit_components[circuit_id]
            kicad_comp = kicad_components[kicad_ref]
            circuit_ref = circuit_comp["reference"]

            # Check if this is a rename (different reference but matched)
            if circuit_ref != kicad_ref:
                # This is a RENAME
                logger.info(f"Detected rename: {kicad_ref} → {circuit_ref}")
                success = self.component_manager.rename_component(
                    old_ref=kicad_ref,
                    new_ref=circuit_ref
                )
                if success:
                    report.renamed.append((kicad_ref, circuit_ref))
                    # Update kicad_components dict key for subsequent operations
                    kicad_components[circuit_ref] = kicad_components.pop(kicad_ref)
                    # Update matches dict so subsequent code uses new reference
                    matches[circuit_id] = circuit_ref
                    # NOTE: Don't set kicad_comp.reference directly!
                    # rename_component() already updated it, and setting it again
                    # will trigger kicad-sch-api validation error "Reference already exists"
                    # Update kicad_ref to use new reference for remaining operations
                    kicad_ref = circuit_ref
                else:
                    report.errors.append(f"Failed to rename {kicad_ref} → {circuit_ref}")
                    continue

            # Check if update needed (value, footprint, symbol, etc.)
            if self._needs_update(circuit_comp, kicad_comp):
                success = self.component_manager.update_component(
                    kicad_ref,  # Use current reference (after rename if applicable)
                    value=circuit_comp["value"],
                    footprint=circuit_comp.get("footprint"),
                    lib_id=circuit_comp.get("symbol"),
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
        # Check for symbol (lib_id) change
        circuit_symbol = circuit_comp.get("symbol")
        if circuit_symbol and circuit_symbol != str(kicad_comp.lib_id):
            logger.info(
                f"Symbol change detected for {kicad_comp.reference}: {kicad_comp.lib_id} → {circuit_symbol}"
            )
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

            # Issue #489: Also reconcile pin connections for newly added components
            # This ensures hierarchical labels and power symbols are added for the new component's pins
            kicad_ref = comp_data["reference"]
            if kicad_ref in self.schematic.components_dict:
                logger.debug(f"    🔌 Reconciling pins for newly added component {kicad_ref}")
                # Update kicad_components dict with newly added component
                kicad_components[kicad_ref] = self.schematic.components_dict[kicad_ref]
                self._reconcile_component_pins(
                    circuit_id, kicad_ref, circuit_components, kicad_components, report
                )

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

            # Always preserve power symbols - they're auto-generated from power nets
            if kicad_ref.startswith("#PWR"):
                logger.info(f"      -> PRESERVING (power symbol)")
                report.preserved.append(kicad_ref)
            elif self.preserve_user_components:
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
        logger.info("Saving schematic changes...")

        # kicad-sch-api's save() method automatically syncs all collections to _data
        # including wires, labels, components, junctions, hierarchical_labels, etc.
        # See: kicad_sch_api/core/schematic.py:408-416 (save method calls all _sync_*_to_data methods)

        # Fix schematic name to match project name
        # kicad-sch-api's save() method uses schematic.name to fix all component instance project references
        # If the schematic was loaded with wrong name, we need to correct it before saving
        correct_project_name = self.schematic_path.stem  # e.g., "comprehensive_root.kicad_sch" -> "comprehensive_root"
        if self.schematic.name != correct_project_name:
            logger.info(f"🔧 Fixing schematic.name: '{self.schematic.name}' -> '{correct_project_name}'")
            self.schematic.name = correct_project_name

        logger.info(f"💾 Calling schematic.save(preserve_format=False)")
        logger.info(f"   - Save path: {self.schematic_path}")
        logger.info(f"   - Using preserve_format=False to force full rewrite from _data")

        # Using preserve_format=False forces full rewrite from _data dictionary
        self.schematic.save(str(self.schematic_path), preserve_format=False)

        logger.info(f"✅ Save completed")
        logger.info("=" * 70)
