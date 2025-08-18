# -*- coding: utf-8 -*-
#
# schematic_writer.py
#
# KiCad API Phase 2 Integration - Direct usage of KiCad API
# This version replaces custom placement and reference management with the KiCad API
#
# Writes a .kicad_sch file from in-memory circuit data using the new KiCad API
#

# Performance debugging imports
try:
    from .debug_performance import (
        log_component_processing,
        log_net_label_creation,
        log_symbol_lookup,
        print_performance_summary,
        timed_operation,
    )

    PERF_DEBUG = True
except ImportError:
    PERF_DEBUG = False

    def timed_operation(*args, **kwargs):
        from contextlib import contextmanager

        @contextmanager
        def dummy():
            yield

        return dummy()


import datetime
import logging
import math

# Configure logging for this module
import os
import time
import uuid as uuid_module
from pathlib import Path
from typing import Dict, List, Optional, Tuple

log_level = os.environ.get("CIRCUIT_SYNTH_LOG_LEVEL", "WARNING")
try:
    level = getattr(logging, log_level.upper())
except AttributeError:
    level = logging.WARNING

logging.basicConfig(
    level=level, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

from sexpdata import Symbol, dumps

from circuit_synth.kicad.core.s_expression import SExpressionParser

# Add performance timing
try:
    from ...core.performance_profiler import quick_time
except ImportError:
    # Fallback if profiler not available
    def quick_time(name):
        def decorator(func):
            return func

        return decorator


from sexpdata import Symbol

# Use optimized symbol cache from core.component for better performance,
# but keep Python fallback for graphics data
from circuit_synth.core.component import SymbolLibCache

# Import from KiCad API
from circuit_synth.kicad.core.types import (
    Junction,
    Label,
    LabelType,
    Point,
    Rectangle,
    Schematic,
    SchematicSymbol,
    Sheet,
    SheetPin,
    SymbolInstance,
    Text,
    Wire,
)

# Import Python symbol cache specifically for graphics data
from circuit_synth.kicad.kicad_symbol_cache import (
    SymbolLibCache as PythonSymbolLibCache,
)
from circuit_synth.kicad.schematic.component_manager import ComponentManager
from circuit_synth.kicad.schematic.placement import PlacementEngine, PlacementStrategy

# Import existing dependencies
from ...core.circuit import Circuit
from .collision_manager import SHEET_MARGIN
from .integrated_reference_manager import IntegratedReferenceManager

# from .kicad_formatter import format_kicad_schematic  # Removed - using integrated formatter
from .shape_drawer import arc_s_expr, circle_s_expr, polyline_s_expr, rectangle_s_expr

# Python-only implementation



# Python implementation for generate_component_sexp
def generate_component_sexp(component_data):
    """Python implementation for component S-expression generation"""
    # CRITICAL DEBUG: Log all component data to identify reference issue
    logger.debug(
        f"🔍 GENERATE_COMPONENT_SEXP: Input component_data keys: {list(component_data.keys())}"
    )
    logger.debug(f"🔍 GENERATE_COMPONENT_SEXP: Full component_data: {component_data}")

    # CRITICAL FIX: Never use hard-coded fallbacks - always preserve original reference
    ref = component_data.get("ref")
    if not ref:
        logger.error(
            f"❌ GENERATE_COMPONENT_SEXP: NO REFERENCE found in component_data!"
        )
        logger.error(
            f"❌ GENERATE_COMPONENT_SEXP: This indicates a bug in component processing"
        )
        # Don't use hard-coded fallback - this masks the real issue
        ref = "REF_ERROR"  # Make it obvious when this happens
    else:
        logger.debug(f"✅ GENERATE_COMPONENT_SEXP: Found reference: '{ref}'")

    lib_id = component_data.get("lib_id", "Device:UNKNOWN")  # More descriptive fallback
    at = component_data.get("at", [0, 0, 0])
    uuid = component_data.get("uuid", "00000000-0000-0000-0000-000000000000")

    logger.debug(
        f"🔍 GENERATE_COMPONENT_SEXP: Using ref='{ref}', lib_id='{lib_id}', at={at}"
    )

    # Build basic S-expression
    sexp = [
        Symbol("symbol"),
        [Symbol("lib_id"), lib_id],
        (
            [Symbol("at"), at[0], at[1], at[2]]
            if len(at) >= 3
            else [Symbol("at"), at[0], at[1]]
        ),
        [Symbol("uuid"), uuid],
    ]

    # Add properties if present
    if "properties" in component_data:
        for prop in component_data["properties"]:
            sexp.append(prop)

    # Add reference property
    sexp.append(
        [
            Symbol("property"),
            "Reference",
            ref,
            [Symbol("at"), 0, -5, 0],
            [Symbol("effects"), [Symbol("font"), [Symbol("size"), 1.27, 1.27]]],
        ]
    )

    return sexp


logger = logging.getLogger(__name__)

# TestPoint symbol rendering constants
TESTPOINT_RADIUS_SCALE_FACTOR = 0.6


def find_pin_by_identifier(pins, identifier):
    """
    Find a pin by its ID, number, or name.

    Args:
        pins: List of pin dictionaries from the library data
        identifier: String identifier that could be a pin_id, number, or name

    Returns:
        The matching pin dictionary or None if not found
    """
    # Try by pin_id
    pin = next((p for p in pins if str(p.get("pin_id")) == identifier), None)
    if pin:
        return pin

    # Try by pin number
    pin = next((p for p in pins if str(p.get("number")) == identifier), None)
    if pin:
        return pin

    # Try by pin name
    pin = next((p for p in pins if p.get("name") == identifier), None)
    if pin:
        return pin

    return None


def validate_arc_geometry(start, mid, end):
    """
    Validate that an arc has valid geometry.

    Args:
        start: [x, y] coordinates of arc start
        mid: [x, y] coordinates of arc midpoint (can be None)
        end: [x, y] coordinates of arc end

    Returns:
        Tuple of (is_valid, corrected_mid) where corrected_mid is calculated if needed
    """
    # Check if start and end are the same
    if start == end:
        return False, None

    # Check if midpoint is missing or invalid
    if mid is None or mid == [0, 0] or mid == start or mid == end:
        # Calculate a valid midpoint
        calc_mid = [(start[0] + end[0]) / 2, (start[1] + end[1]) / 2]

        # Calculate perpendicular offset for a reasonable arc
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        length = math.sqrt(dx * dx + dy * dy)

        if length > 0:
            # Normalize and create perpendicular vector
            dx_norm = dx / length
            dy_norm = dy / length
            perp_x = -dy_norm * length * 0.2  # 20% offset for visible arc
            perp_y = dx_norm * length * 0.2

            calc_mid[0] += perp_x
            calc_mid[1] += perp_y

            return True, calc_mid
        else:
            return False, None

    # Check collinearity
    v1x = mid[0] - start[0]
    v1y = mid[1] - start[1]
    v2x = end[0] - start[0]
    v2y = end[1] - start[1]

    cross = v1x * v2y - v1y * v2x
    if abs(cross) < 0.001:  # Nearly collinear
        # Adjust midpoint slightly to create a valid arc
        perp_x = -v2y * 0.1
        perp_y = v2x * 0.1
        new_mid = [mid[0] + perp_x, mid[1] + perp_y]
        return True, new_mid

    return True, mid


class SchematicWriter:
    """
    Builds a KiCad schematic using the new KiCad API.
    This version uses ComponentManager and PlacementEngine for better integration.
    """

    def __init__(
        self,
        circuit: Circuit,
        circuit_dict: dict,
        instance_naming_map: dict,
        paper_size: str = "A4",
        project_name: str = None,
        hierarchical_path: list = None,
        reference_manager: IntegratedReferenceManager = None,
        draw_bounding_boxes: bool = False,
        uuid: str = None,
    ):
        """
        :param circuit: The Circuit object (subcircuit or top-level) to be written.
        :param circuit_dict: Dict of all subcircuits keyed by subcircuit name -> Circuit
        :param instance_naming_map: For advanced usage (unused here).
        :param paper_size: Paper size to use for the schematic (e.g., "A4", "A3")
        :param project_name: The actual KiCad project name (for instances block)
        :param hierarchical_path: List of UUIDs representing the full path from root
        :param reference_manager: Optional shared reference manager for global uniqueness
        :param uuid: Optional UUID for the schematic (if not provided, generates a new one)
        """
        self.circuit = circuit
        self.all_subcircuits = circuit_dict
        self.instance_naming_map = instance_naming_map
        self.uuid_top = uuid if uuid else str(uuid_module.uuid4())
        self.paper_size = paper_size
        self.project_name = project_name or circuit.name
        self.hierarchical_path = hierarchical_path or []
        self.draw_bounding_boxes = draw_bounding_boxes

        # Create KiCad API Schematic object
        self.schematic = Schematic(
            uuid=self.uuid_top,
            title=circuit.name,
            date=datetime.datetime.now().strftime("%Y-%m-%d"),
            company="Circuit-Synth",
            hierarchical_path=self.hierarchical_path,  # Pass hierarchical path for sheet_instances
        )

        # Initialize KiCad API managers
        self.component_manager = ComponentManager(self.schematic)
        self.placement_engine = PlacementEngine(self.schematic)

        # Initialize S-expression parser
        self.parser = SExpressionParser()

        # Initialize the reference manager for compatibility
        # Use provided reference manager for global uniqueness, or create a new one
        if reference_manager is not None:
            self.reference_manager = reference_manager
            logger.debug(f"  - Using shared reference manager")
        else:
            self.reference_manager = IntegratedReferenceManager()
            logger.info(f"  - Created new reference manager")

        # Initialize component to UUID mapping for symbol_instances table
        self.component_uuid_map = {}

        # Initialize sheet symbol tracking for hierarchical references
        self.sheet_symbol_map = {}  # Maps subcircuit name to sheet symbol UUID

        # Log initialization details
        logger.debug(f"SchematicWriter initialized for circuit '{circuit.name}'")
        logger.debug(f"  - Using KiCad API Phase 2 integration")
        logger.debug(f"  - Hierarchical path: {self.hierarchical_path}")
        logger.debug(f"  - Self UUID (uuid_top): {self.uuid_top}")
        logger.debug(f"  - Project name: {self.project_name}")

    @quick_time("Generate S-Expression")
    def generate_s_expr(self) -> list:
        """
        Create the full top-level (kicad_sch ...) list structure for this circuit.

        PERFORMANCE MONITORING: Times each major operation.
        """
        start_time = time.perf_counter()
        logger.info(
            f"🚀 GENERATE_S_EXPR: Starting schematic generation for circuit '{self.circuit.name}'"
        )
        logger.info(
            f"📊 GENERATE_S_EXPR: Components: {len(self.circuit.components)}, Nets: {len(self.circuit.nets)}"
        )
        logger.info(f"🐍 GENERATE_S_EXPR: Using Python implementation for components")

        # Add components using the new API - time this critical operation
        comp_start = time.perf_counter()
        logger.info(f"⚡ STEP 1/8: Adding {len(self.circuit.components)} components...")
        self._add_components()
        comp_time = time.perf_counter() - comp_start
        logger.info(f"✅ STEP 1/8: Components added in {comp_time*1000:.2f}ms")

        # Place components using the placement engine
        place_start = time.perf_counter()
        logger.info("⚡ STEP 2/8: Placing components...")
        self._place_components()
        place_time = time.perf_counter() - place_start
        logger.info(f"✅ STEP 2/8: Components placed in {place_time*1000:.2f}ms")

        # Add pin-level net labels
        labels_start = time.perf_counter()
        logger.info(
            f"⚡ STEP 3/8: Adding pin-level net labels for {len(self.circuit.nets)} nets..."
        )
        self._add_pin_level_net_labels()
        labels_time = time.perf_counter() - labels_start
        logger.info(f"✅ STEP 3/8: Net labels added in {labels_time*1000:.2f}ms")

        # Add subcircuit sheets if needed
        sheets_start = time.perf_counter()
        subcircuit_count = (
            len(self.circuit.child_instances) if self.circuit.child_instances else 0
        )
        logger.info(f"⚡ STEP 4/8: Adding {subcircuit_count} subcircuit sheets...")
        self._add_subcircuit_sheets()
        sheets_time = time.perf_counter() - sheets_start
        logger.info(f"✅ STEP 4/8: Subcircuit sheets added in {sheets_time*1000:.2f}ms")

        # Add bounding boxes if enabled
        bbox_start = time.perf_counter()
        if self.draw_bounding_boxes:
            logger.info(
                f"⚡ STEP 5/8: Adding bounding boxes for {len(self.circuit.components)} components..."
            )
            self._add_component_bounding_boxes()
            bbox_time = time.perf_counter() - bbox_start
            logger.info(f"✅ STEP 5/8: Bounding boxes added in {bbox_time*1000:.2f}ms")
        else:
            logger.info("⏭️  STEP 5/8: Bounding boxes disabled, skipping")
            bbox_time = 0

        # Add text annotations (TextBox, TextProperty, etc.)
        self._add_annotations()

        # Convert to S-expression format using the parser
        sexpr_start = time.perf_counter()
        logger.info("⚡ STEP 6/8: Converting to S-expression format...")
        schematic_sexpr = self.parser.from_schematic(self.schematic)
        sexpr_time = time.perf_counter() - sexpr_start
        logger.info(
            f"✅ STEP 6/8: S-expression conversion completed in {sexpr_time*1000:.2f}ms"
        )

        # Add additional sections
        sections_start = time.perf_counter()
        logger.info(
            "⚡ STEP 7/8: Adding additional sections (paper, lib_symbols, sheet_instances)..."
        )

        # Paper size is now added by the parser, so we don't need to add it again
        paper_start = time.perf_counter()
        # self._add_paper_size(schematic_sexpr)  # Removed to avoid duplicate
        paper_time = 0  # No paper processing time

        # Add lib_symbols section
        libsym_start = time.perf_counter()
        self._add_symbol_definitions(schematic_sexpr)
        libsym_time = time.perf_counter() - libsym_start

        # Add sheet_instances section - CRITICAL for proper reference assignment
        sheetinst_start = time.perf_counter()
        self._add_sheet_instances(schematic_sexpr)
        sheetinst_time = time.perf_counter() - sheetinst_start

        # Add embedded_fonts no at the end (required for KiCad 9)
        schematic_sexpr.append([Symbol("embedded_fonts"), Symbol("no")])

        sections_time = time.perf_counter() - sections_start
        logger.info(
            f"✅ STEP 7/8: Additional sections added in {sections_time*1000:.2f}ms"
        )
        logger.debug(f"  📄 Paper size: {paper_time*1000:.3f}ms")
        logger.debug(f"  📚 Lib symbols: {libsym_time*1000:.2f}ms")
        logger.debug(f"  📋 Sheet instances: {sheetinst_time*1000:.3f}ms")

        # Add symbol_instances section - DISABLED for new KiCad format (20250114+)
        # The new format uses instances within each symbol instead
        # self._add_symbol_instances_table(schematic_sexpr)

        total_time = time.perf_counter() - start_time
        expr_size = len(str(schematic_sexpr)) if schematic_sexpr else 0

        logger.info("🏁 STEP 8/8: Schematic generation complete!")
        logger.info(f"✅ GENERATE_S_EXPR: ✅ TOTAL TIME: {total_time*1000:.2f}ms")
        logger.info(
            f"📊 GENERATE_S_EXPR: Generated S-expression: {expr_size:,} characters"
        )
        logger.info(
            f"⚡ GENERATE_S_EXPR: Throughput: {expr_size/(total_time*1000):.1f} chars/ms"
        )

        # Performance breakdown
        logger.info("📈 PERFORMANCE_BREAKDOWN:")
        logger.info(
            f"  🔧 Components: {comp_time*1000:.2f}ms ({comp_time/total_time*100:.1f}%)"
        )
        logger.info(
            f"  📍 Placement: {place_time*1000:.2f}ms ({place_time/total_time*100:.1f}%)"
        )
        logger.info(
            f"  🏷️  Labels: {labels_time*1000:.2f}ms ({labels_time/total_time*100:.1f}%)"
        )
        logger.info(
            f"  📄 Sheets: {sheets_time*1000:.2f}ms ({sheets_time/total_time*100:.1f}%)"
        )
        if bbox_time > 0:
            logger.info(
                f"  📦 Bounding boxes: {bbox_time*1000:.2f}ms ({bbox_time/total_time*100:.1f}%)"
            )
        logger.info(
            f"  🔄 S-expression: {sexpr_time*1000:.2f}ms ({sexpr_time/total_time*100:.1f}%)"
        )
        logger.info(
            f"  📚 Sections: {sections_time*1000:.2f}ms ({sections_time/total_time*100:.1f}%)"
        )

        # Performance metrics
        logger.info(f"⚡ PERFORMANCE: Completed in {total_time*1000:.2f}ms")

        # Add symbol_instances section - DISABLED for new KiCad format (20250114+)
        # The new format uses instances within each symbol instead
        # self._add_symbol_instances_table(schematic_sexpr)

        return schematic_sexpr

    @quick_time("Add Components to Schematic")
    def _add_components(self):
        """
        Add all components from the circuit using the ComponentManager.
        """
        logger.debug(f"=== ADDING COMPONENTS FOR CIRCUIT: {self.circuit.name} ===")
        logger.debug(f"  Number of components: {len(self.circuit.components)}")

        # Track reference mapping for net updates
        self.reference_mapping = {}

        for idx, comp in enumerate(self.circuit.components):
            comp_start = time.perf_counter()
            comp_details = {
                "reference": comp.reference,
                "lib_id": comp.lib_id,
                "circuit": self.circuit.name,
            }

            logger.debug(
                f"  [{idx}] Processing component: {comp.reference} ({comp.lib_id})"
            )

            # Store the original reference
            original_ref = comp.reference

            # For reference assignment, we need to check if this should be reassigned
            # The main circuit should get lower numbers than subcircuits
            if hasattr(
                self.reference_manager, "should_reassign"
            ) and self.reference_manager.should_reassign(comp.reference):
                # Force a new reference assignment
                new_ref = self.reference_manager.get_next_reference_for_type(
                    comp.lib_id
                )
                logger.debug(
                    f"      Reassigning reference: {comp.reference} -> {new_ref}"
                )
            else:
                # Use the existing reference assignment logic
                new_ref = self.reference_manager.get_reference_for_symbol(comp)
            logger.debug(f"      Assigned reference: {new_ref}")

            # Track the mapping
            self.reference_mapping[original_ref] = new_ref

            # Add component using the API
            # Time the component manager operation
            with timed_operation(
                f"add_component[{comp.lib_id}]", threshold_ms=20, details=comp_details
            ):
                api_component = self.component_manager.add_component(
                    library_id=comp.lib_id,
                    reference=new_ref,
                    value=comp.value,
                    position=(comp.position.x, comp.position.y),
                    placement_strategy=PlacementStrategy.AUTO,
                    footprint=comp.footprint,
                )

            if api_component:
                # Update our mapping
                self.component_uuid_map[new_ref] = api_component.uuid

                # Update the original component reference
                comp.reference = new_ref

                # Copy additional properties
                api_component.rotation = comp.rotation
                api_component.unit = comp.unit
                api_component.in_bom = comp.in_bom
                api_component.on_board = comp.on_board
                api_component.dnp = comp.dnp
                api_component.mirror = comp.mirror

                # Store hierarchy path and project name for instances generation
                if self.hierarchical_path:
                    api_component.properties["hierarchy_path"] = "/" + "/".join(
                        self.hierarchical_path
                    )

                # Store project name for the instances section in new KiCad format
                api_component.properties["project_name"] = self.project_name

                # Create instances for the new KiCad format (20250114+)
                # The path should contain only sheet UUIDs, not component UUID
                logger.debug(f"=== CREATING INSTANCE FOR COMPONENT {new_ref} ===")
                logger.debug(f"  Component lib_id: {comp.lib_id}")
                logger.debug(f"  Component UUID: {api_component.uuid}")
                logger.debug(f"  Current circuit: {self.circuit.name}")
                logger.debug(f"  Hierarchical path: {self.hierarchical_path}")
                logger.debug(
                    f"  Hierarchical path length: {len(self.hierarchical_path) if self.hierarchical_path else 0}"
                )

                # Add path validation
                if self.hierarchical_path:
                    logger.debug(f"  Path UUIDs:")
                    for i, uuid in enumerate(self.hierarchical_path):
                        logger.debug(f"    [{i}]: {uuid}")

                if self.hierarchical_path and len(self.hierarchical_path) > 0:
                    # For sub-sheets, use only the sheet hierarchy path
                    instance_path = "/" + "/".join(self.hierarchical_path)
                    logger.debug(
                        f"  Creating SUB-SHEET instance with path: {instance_path}"
                    )
                else:
                    # Root sheet - use schematic UUID in path
                    instance_path = f"/{self.schematic.uuid}"
                    logger.debug(
                        f"  Creating ROOT SHEET instance with path: {instance_path}"
                    )

                # Clear any existing instances that might have been added by component_manager
                # We need to control the project name ourselves
                api_component.instances.clear()

                # Create the instance
                # CRITICAL FIX: Use consistent project naming for ALL components
                # The inconsistency between component and sheet instances causes KiCad GUI annotation issues
                # UNIVERSAL SOLUTION: Always use the actual project name for consistency
                instance_project = self.project_name or "default_project"
                logger.debug(
                    f"🔧 UNIVERSAL_PROJECT_NAMING: Using consistent project name: '{instance_project}'"
                )

                instance = SymbolInstance(
                    project=instance_project,
                    path=instance_path,
                    reference=new_ref,
                    unit=comp.unit,
                )
                api_component.instances.append(instance)

                logger.debug(f"  Instance created:")
                logger.debug(f"    - Project: {instance.project}")
                logger.debug(f"    - Path: {instance.path}")
                logger.debug(f"    - Reference: {instance.reference}")
                logger.debug(f"    - Unit: {instance.unit}")
                logger.debug(
                    f"  Total instances on component: {len(api_component.instances)}"
                )
                logger.debug(f"=== END INSTANCE CREATION FOR {new_ref} ===")

                logger.debug(
                    f"Added component {new_ref} ({comp.lib_id}) at ({comp.position.x}, {comp.position.y})"
                )
            else:
                logger.error(f"Failed to add component {comp.reference}")

        # Update net connections with new references
        logger.debug("Updating net connections with new references")
        if hasattr(self, "reference_mapping"):
            for net in self.circuit.nets:
                updated_connections = []
                for comp_ref, pin_identifier in net.connections:
                    # Use the reference mapping to find the new reference
                    if comp_ref in self.reference_mapping:
                        new_ref = self.reference_mapping[comp_ref]
                        updated_connections.append((new_ref, pin_identifier))
                    else:
                        # If not in mapping, keep the original
                        updated_connections.append((comp_ref, pin_identifier))

                net.connections = updated_connections

    def _place_components(self):
        """
        Use the PlacementEngine to arrange components.

        PERFORMANCE OPTIMIZATION: Uses force-directed placement algorithms.
        """
        if not self.schematic.components:
            logger.debug("No components to place")
            return

        start_time = time.perf_counter()
        logger.info(
            f"🚀 PLACE_COMPONENTS: Starting placement of {len(self.schematic.components)} components"
        )
        logger.info(f"🐍 PLACE_COMPONENTS: Using Python placement engine")

        # Check if components need repositioning (have default positions)
        components_needing_placement = []
        for comp in self.schematic.components:
            # If component is at origin or has no meaningful position, it needs placement
            if (
                comp.position.x <= 25.4 and comp.position.y <= 25.4
            ):  # Within 1 inch of origin
                components_needing_placement.append(comp)

        if not components_needing_placement:
            logger.info(
                "⏭️  PLACE_COMPONENTS: All components already have valid positions, skipping placement"
            )
            return

        logger.info(
            f"🔧 PLACE_COMPONENTS: {len(components_needing_placement)} components need placement"
        )

        # Use the PlacementEngine
        try:
            placement_start = time.perf_counter()

            # Try force-directed placement for optimal results
            if (
                len(components_needing_placement) >= 3
            ):  # Force-directed works best with multiple components
                logger.info(
                    "🦀 PLACE_COMPONENTS: Using force-directed placement for optimal component arrangement"
                )
                self.placement_engine.arrange_components(
                    components_needing_placement,
                    arrangement="force_directed",
                    # Python implementation
                )
            else:
                # For few components, use grid placement
                logger.info(
                    "🔧 PLACE_COMPONENTS: Using grid placement for few components"
                )
                self.placement_engine.arrange_components(
                    components_needing_placement, arrangement="grid"
                )

            placement_time = time.perf_counter() - placement_start
            logger.info(
                f"✅ PLACE_COMPONENTS: Component placement completed in {placement_time*1000:.2f}ms"
            )

            # Log final positions
            logger.debug("🔧 PLACE_COMPONENTS: Final component positions:")
            for comp in components_needing_placement:
                logger.debug(
                    f"  {comp.reference}: ({comp.position.x:.1f}, {comp.position.y:.1f})"
                )

        except Exception as e:
            placement_error_time = time.perf_counter() - start_time
            logger.error(
                f"❌ PLACE_COMPONENTS: PLACEMENT FAILED after {placement_error_time*1000:.2f}ms: {e}"
            )
            logger.warning("🔄 PLACE_COMPONENTS: Using fallback grid placement")

            # Fallback to simple grid placement
            try:
                self.placement_engine._arrange_grid(components_needing_placement)
                logger.info("✅ PLACE_COMPONENTS: Fallback grid placement completed")
            except Exception as fallback_error:
                logger.error(
                    f"❌ PLACE_COMPONENTS: Even fallback placement failed: {fallback_error}"
                )
                # Leave components at their current positions

        total_time = time.perf_counter() - start_time
        logger.info(
            f"🏁 PLACE_COMPONENTS: ✅ PLACEMENT COMPLETE in {total_time*1000:.2f}ms"
        )

    def _add_pin_level_net_labels(self):
        """
        Add local net labels at component pins for all nets.
        """
        logger.debug(f"Adding pin-level net labels for circuit '{self.circuit.name}'.")

        # Get component lookup from the API
        for net in self.circuit.nets:
            net_name = net.name
            logger.debug(
                f"Processing net '{net_name}' with {len(net.connections)} connections"
            )

            for comp_ref, pin_identifier in net.connections:
                label_start = time.perf_counter()
                label_details = {
                    "net": net_name,
                    "component": comp_ref,
                    "pin": str(pin_identifier),
                }

                # Don't use reference mapping here - net connections have already been updated
                actual_ref = comp_ref

                # Find component using the API
                comp = self.component_manager.find_component(actual_ref)

                if not comp:
                    logger.debug(f"Component {actual_ref} not found for net {net_name}")
                    continue

                # Get pin position from library data
                # Time symbol data lookup
                sym_start = time.perf_counter()
                lib_data = SymbolLibCache.get_symbol_data(comp.lib_id)
                sym_time = (time.perf_counter() - sym_start) * 1000
                if PERF_DEBUG and sym_time > 10:
                    log_symbol_lookup(
                        comp.lib_id, lib_data is not None, sym_time, "SymbolLibCache"
                    )

                if not lib_data or "pins" not in lib_data:
                    logger.warning(
                        f"No pin data found for component {comp_ref} ({comp.lib_id})"
                    )
                    continue

                # Find the pin
                pin_dict = find_pin_by_identifier(lib_data["pins"], pin_identifier)

                if not pin_dict:
                    logger.warning(
                        f"Pin {pin_identifier} not found for component {comp_ref} in net {net_name}"
                    )
                    continue

                # Calculate pin position
                anchor_x = float(pin_dict.get("x", 0.0))
                anchor_y = float(pin_dict.get("y", 0.0))
                pin_angle = float(pin_dict.get("orientation", 0.0))

                # Rotate coords by component rotation
                r = math.radians(comp.rotation)
                local_x = anchor_x
                local_y = -anchor_y
                rx = (local_x * math.cos(r)) - (local_y * math.sin(r))
                ry = (local_x * math.sin(r)) + (local_y * math.cos(r))

                global_x = comp.position.x + rx
                global_y = comp.position.y + ry

                # Calculate label angle
                label_angle = (pin_angle + 180) % 360
                global_angle = (label_angle + comp.rotation) % 360

                # Create hierarchical label using the API
                label = Label(
                    text=net_name,
                    position=Point(global_x, global_y),
                    label_type=LabelType.HIERARCHICAL,
                    orientation=int(global_angle),
                )

                self.schematic.add_label(label)
                label_time = (time.perf_counter() - label_start) * 1000
                if PERF_DEBUG and label_time > 5:
                    log_net_label_creation(
                        net_name, actual_ref, str(pin_identifier), label_time
                    )
                logger.debug(
                    f"Added hierarchical label for net {net_name} at component {actual_ref}.{pin_identifier}"
                )

    def _add_subcircuit_sheets(self):
        """
        For each child subcircuit instance, add a sheet using the KiCad API.
        """
        if not self.circuit.child_instances:
            logger.debug(
                "Circuit '%s' has no child subcircuits, skipping sheets.",
                self.circuit.name,
            )
            return

        logger.debug(
            "Circuit '%s' has %d child subcircuits. Adding sheet symbols...",
            self.circuit.name,
            len(self.circuit.child_instances),
        )

        for child_info in self.circuit.child_instances:
            sub_name = child_info["sub_name"]
            usage_label = child_info["instance_label"]

            child_circ = self.all_subcircuits[sub_name]

            # Get all net names for this subcircuit to create sheet pins
            # For hierarchical sheets, we need to include both internal nets AND
            # the parameters passed to the subcircuit function
            pin_list = sorted([n.name for n in child_circ.nets])

            # CRITICAL FIX: Also include the parameters from child circuit instances
            # For subcircuits that only contain other subcircuits (no components),
            # the parameters won't show up as nets, so we need to extract them from
            # the instance connections
            if hasattr(child_info, "instance_nets") and child_info.get("instance_nets"):
                # If instance_nets mapping is available, use it
                instance_nets = child_info["instance_nets"]
                for param_name, net_name in instance_nets.items():
                    if net_name not in pin_list:
                        pin_list.append(net_name)
                pin_list = sorted(pin_list)
            elif (
                len(child_circ.components) == 0 and len(child_circ.child_instances) > 0
            ):
                # This is a hierarchical sheet with only subcircuits
                # We need to infer the parameters from the parent circuit's nets
                # that connect to this subcircuit instance
                logger.debug(
                    f"Subcircuit '{sub_name}' has no components, checking parent connections"
                )

                # Look for nets in the parent circuit that might connect to this instance
                # This is a heuristic approach - ideally we'd have explicit parameter info
                parent_nets = set()
                for net in self.circuit.nets:
                    # Add all parent nets as potential connections
                    # In a more sophisticated implementation, we'd track which nets
                    # actually connect to this specific subcircuit instance
                    parent_nets.add(net.name)

                # For now, use common signal names that are likely to be hierarchical connections
                common_hierarchical_signals = [
                    "VCC",
                    "GND",
                    "VIN",
                    "VOUT",
                    "INPUT",
                    "OUTPUT",
                    "FILTERED",
                    "PROCESSED",
                    "V_MONITOR",
                ]
                for signal in common_hierarchical_signals:
                    if signal in parent_nets and signal not in pin_list:
                        pin_list.append(signal)

                # Also check the subcircuit's child instances to infer parameters
                for child_inst in child_circ.child_instances:
                    child_sub = self.all_subcircuits.get(child_inst["sub_name"])
                    if child_sub:
                        # Add any nets from child subcircuits that might be parameters
                        for net in child_sub.nets:
                            if net.name not in pin_list and net.name in parent_nets:
                                pin_list.append(net.name)

                pin_list = sorted(pin_list)
                logger.info(f"Inferred hierarchical pins for '{sub_name}': {pin_list}")

            # Use pre-calculated position and size
            cx = child_info.get("x", 50.0)
            cy = child_info.get("y", 50.0)
            width = child_info.get("width", 30.0)
            height = child_info.get("height", 30.0)

            # Calculate sheet position (upper-left corner) and snap to grid
            # KiCad uses 50mil (1.27mm) grid
            grid_size = 1.27
            sheet_x = round((cx - (width / 2)) / grid_size) * grid_size
            sheet_y = round((cy - (height / 2)) / grid_size) * grid_size

            # Create sheet using the API
            sheet = Sheet(
                name=usage_label,
                filename=f"{sub_name}.kicad_sch",
                position=Point(sheet_x, sheet_y),
                size=(width, height),
            )

            # Add project name to sheet for instances generation
            sheet._project_name = self.project_name

            # Add pins for all child's net names
            grid_size = 1.27  # KiCad 50mil grid
            sheet_right = sheet_x + width
            pin_spacing = 2.54  # 100mil spacing
            start_y = sheet_y + 2.54

            for i, net_name in enumerate(pin_list):
                # Ensure pin positions are grid-aligned
                pin_x = sheet_right  # Place pins on right edge of sheet
                pin_y = round((start_y + (i * pin_spacing)) / grid_size) * grid_size

                # Create sheet pin
                sheet_pin = SheetPin(
                    name=net_name,
                    position=Point(pin_x - 1.27, pin_y),
                    orientation=0,  # on right side of the sheet
                    shape="passive",
                )

                sheet.pins.append(sheet_pin)
                logger.debug(
                    f"Created sheet pin '{net_name}' with orientation {sheet_pin.orientation}"
                )

                label_x = pin_x
                label = Label(
                    text=net_name,
                    position=Point(label_x, pin_y),
                    label_type=LabelType.HIERARCHICAL,
                    orientation=0,
                )
                self.schematic.add_label(label)

            # Add sheet to schematic
            self.schematic.sheets.append(sheet)

            # Track sheet symbol UUID for hierarchical references
            self.sheet_symbol_map[sub_name] = sheet.uuid

            # Debug logging for sheet creation
            logger.debug(f"=== ADDING SHEET SYMBOL ===")
            logger.debug(f"  Sheet name: {usage_label}")
            logger.debug(f"  Sheet symbol UUID: {sheet.uuid}")
            logger.debug(f"  Target schematic file: {sheet.filename}")
            logger.debug(f"  Target subcircuit: {sub_name}")
            logger.debug(f"  Current hierarchical path: {self.hierarchical_path}")
            logger.debug(f"  Stored mapping: {sub_name} -> {sheet.uuid}")
            logger.debug(f"  Added sheet '{usage_label}' with {len(pin_list)} pins")

    def _add_component_bounding_boxes(self):
        """Add bounding box rectangles using KiCad API."""
        logger.debug(
            f"Adding bounding boxes for {len(self.schematic.components)} components"
        )

        for comp in self.schematic.components:
            # Get precise bounding box from existing calculator
            lib_data = SymbolLibCache.get_symbol_data(comp.lib_id)
            if not lib_data:
                logger.warning(
                    f"No symbol data found for {comp.lib_id}, skipping bounding box"
                )
                continue

            try:
                from .symbol_geometry import SymbolBoundingBoxCalculator

                min_x, min_y, max_x, max_y = (
                    SymbolBoundingBoxCalculator.calculate_bounding_box(lib_data)
                )

                # Create Rectangle using API types
                bbox_rect = Rectangle(
                    start=Point(comp.position.x + min_x, comp.position.y + min_y),
                    end=Point(comp.position.x + max_x, comp.position.y + max_y),
                    stroke_width=0.127,  # Thin stroke (5 mils)
                    stroke_type="solid",
                    fill_type="none",
                    # No stroke_color - KiCad uses default color
                )

                # Add to schematic using API method
                self.schematic.add_rectangle(bbox_rect)
                logger.debug(
                    f"Added bounding box for {comp.reference} at ({comp.position.x + min_x:.2f}, {comp.position.y + min_y:.2f}) to ({comp.position.x + max_x:.2f}, {comp.position.y + max_y:.2f})"
                )

            except Exception as e:
                logger.error(
                    f"Failed to add bounding box for {comp.reference} ({comp.lib_id}): {e}"
                )
                continue

    def _add_annotations(self):
        """Add text annotations (TextBox, TextProperty, etc.) to the schematic."""
        if not hasattr(self.circuit, "_annotations") or not self.circuit._annotations:
            return

        logger.debug(
            f"Adding {len(self.circuit._annotations)} annotations to schematic"
        )

        for annotation in self.circuit._annotations:
            try:
                # Handle both annotation objects and dictionary data
                if isinstance(annotation, dict):
                    annotation_type = annotation.get("type", "Unknown")
                elif hasattr(annotation, "__class__"):
                    annotation_type = annotation.__class__.__name__
                else:
                    annotation_type = type(annotation).__name__

                if annotation_type == "TextBox":
                    self._add_textbox_annotation(annotation)
                elif annotation_type == "TextProperty":
                    self._add_text_annotation(annotation)
                elif annotation_type == "Table":
                    self._add_table_annotation(annotation)
                else:
                    logger.warning(f"Unknown annotation type: {annotation_type}")

            except Exception as e:
                logger.error(f"Failed to add annotation {annotation}: {e}")

    def _add_textbox_annotation(self, textbox):
        """Add a TextBox annotation as a KiCad text_box element."""
        from circuit_synth.kicad.core.types import Text

        # Handle both dictionary data and object data
        if isinstance(textbox, dict):
            text = textbox.get("text", "")
            position = textbox.get(
                "position", (184.0, 110.0)
            )  # Double the default coordinates
            text_size = textbox.get("text_size", 1.27)
            rotation = textbox.get("rotation", 0)
            size = textbox.get("size", (40.0, 20.0))
            margins = textbox.get("margins", (1.0, 1.0, 1.0, 1.0))
            background = textbox.get("background", True)
            background_color = textbox.get("background_color", "white")
            border = textbox.get("border", True)
            uuid = textbox.get("uuid", "")
        else:
            text = textbox.text
            position = textbox.position
            text_size = textbox.text_size
            rotation = textbox.rotation
            size = textbox.size
            margins = textbox.margins
            background = textbox.background
            background_color = textbox.background_color
            border = textbox.border
            uuid = textbox.uuid

        # Create a Text object (we'll handle the box in S-expression generation)
        text_element = Text(
            content=text,
            position=Point(position[0], position[1]),
            size=text_size,
            orientation=rotation,
        )

        # Store additional textbox properties for S-expression generation
        text_element._is_textbox = True
        text_element._textbox_size = size
        text_element._textbox_margins = margins
        text_element._textbox_background = background
        text_element._textbox_background_color = background_color
        text_element._textbox_border = border
        text_element._textbox_uuid = uuid

        self.schematic.add_text(text_element)
        logger.debug(f"Added TextBox annotation: '{text}' at {position}")

    def _add_text_annotation(self, text_prop):
        """Add a TextProperty annotation as a simple KiCad text element."""
        from circuit_synth.kicad.core.types import Text

        # Handle both dictionary data and object data
        if isinstance(text_prop, dict):
            text = text_prop.get("text", "")
            position = text_prop.get("position", (10.0, 10.0))
            size = text_prop.get("size", 1.27)
            rotation = text_prop.get("rotation", 0)
            bold = text_prop.get("bold", False)
            italic = text_prop.get("italic", False)
            color = text_prop.get("color", "black")
            uuid = text_prop.get("uuid", "")
        else:
            text = text_prop.text
            position = text_prop.position
            size = text_prop.size
            rotation = text_prop.rotation
            bold = text_prop.bold
            italic = text_prop.italic
            color = text_prop.color
            uuid = text_prop.uuid

        text_element = Text(
            content=text,
            position=Point(position[0], position[1]),
            size=size,
            orientation=rotation,
        )

        # Store additional text properties
        text_element._text_bold = bold
        text_element._text_italic = italic
        text_element._text_color = color
        text_element._text_uuid = uuid

        self.schematic.add_text(text_element)
        logger.debug(f"Added TextProperty annotation: '{text}' at {position}")

    def _add_table_annotation(self, table):
        """Add a Table annotation as multiple text elements."""
        # Handle both dictionary data and object data
        if isinstance(table, dict):
            data = table.get("data", [])
            position = table.get("position", (10.0, 10.0))
            cell_width = table.get("cell_width", 20.0)
            cell_height = table.get("cell_height", 5.0)
            text_size = table.get("text_size", 1.0)
            header_bold = table.get("header_bold", True)
            uuid = table.get("uuid", "")
        else:
            data = table.data
            position = table.position
            cell_width = table.cell_width
            cell_height = table.cell_height
            text_size = table.text_size
            header_bold = table.header_bold
            uuid = table.uuid

        logger.debug(f"Adding Table annotation with {len(data)} rows at {position}")

        x_start, y_start = position

        for row_idx, row in enumerate(data):
            for col_idx, cell_text in enumerate(row):
                if cell_text:  # Skip empty cells
                    cell_x = x_start + (col_idx * cell_width)
                    cell_y = y_start + (row_idx * cell_height)

                    from circuit_synth.kicad.core.types import Text

                    text_element = Text(
                        content=str(cell_text),
                        position=Point(cell_x, cell_y),
                        size=text_size,
                    )

                    # Make header row bold
                    if row_idx == 0 and header_bold:
                        text_element._text_bold = True

                    text_element._text_uuid = f"{uuid}_{row_idx}_{col_idx}"

                    self.schematic.add_text(text_element)

    def _add_paper_size(self, schematic_expr: list):
        """Add paper size to the schematic expression."""
        # Find the right place to insert paper size
        for i, item in enumerate(schematic_expr):
            if isinstance(item, list) and item and item[0] == Symbol("uuid"):
                # Insert paper after uuid
                schematic_expr.insert(i + 1, [Symbol("paper"), self.paper_size])
                break

    def _add_symbol_definitions(self, schematic_expr: list):
        """
        Add symbol definitions to the lib_symbols section.
        """
        logger.info(
            f"🔍 _add_symbol_definitions: Starting with {len(self.schematic.components)} components"
        )

        # Find or create lib_symbols block
        lib_symbols_block = None
        for item in schematic_expr:
            if (
                isinstance(item, list)
                and item
                and isinstance(item[0], Symbol)
                and item[0].value() == "lib_symbols"
            ):
                lib_symbols_block = item
                logger.info(
                    f"✅ Found existing lib_symbols block at position {schematic_expr.index(item)}"
                )
                break

        if not lib_symbols_block:
            logger.warning("⚠️ No lib_symbols block found, creating new one")
            lib_symbols_block = [Symbol("lib_symbols")]
            # Insert after paper
            for i, item in enumerate(schematic_expr):
                if isinstance(item, list) and item and item[0] == Symbol("paper"):
                    schematic_expr.insert(i + 1, lib_symbols_block)
                    logger.info(
                        f"✅ Inserted lib_symbols block after paper at position {i+1}"
                    )
                    break

        # Clear any existing symbols in the lib_symbols block
        # Keep only the first element which is the Symbol("lib_symbols")
        if lib_symbols_block and len(lib_symbols_block) > 1:
            logger.info(
                f"🧹 Clearing {len(lib_symbols_block)-1} existing items from lib_symbols block"
            )
            lib_symbols_block[:] = [lib_symbols_block[0]]

        # Gather all lib_ids
        symbol_ids = set()
        for comp in self.schematic.components:
            symbol_ids.add(comp.lib_id)
            logger.debug(f"  Component {comp.reference}: lib_id = {comp.lib_id}")

        logger.info(
            f"📚 Processing {len(symbol_ids)} unique lib_ids: {sorted(symbol_ids)}"
        )

        for sym_id in sorted(symbol_ids):
            logger.info(f"📚 SCHEMATIC_WRITER: Fetching symbol data for '{sym_id}'")
            lib_data = SymbolLibCache.get_symbol_data(sym_id)
            if not lib_data:
                logger.error(
                    f"❌ No symbol library data found for '{sym_id}'. Skipping definition."
                )
                continue
            logger.debug(
                f"    ✅ SCHEMATIC_WRITER: Got symbol data for '{sym_id}' with properties: {list(lib_data.get('properties', {}).keys()) if isinstance(lib_data, dict) else 'N/A'}"
            )

            # Check if graphics data is missing from cache - if so, use Python fallback
            if "graphics" not in lib_data or not lib_data["graphics"]:
                logger.info(
                    f"Graphics data missing for {sym_id}, using Python fallback"
                )
                try:
                    python_lib_data = PythonSymbolLibCache.get_symbol_data(sym_id)
                    if python_lib_data and "graphics" in python_lib_data:
                        # Merge graphics data from Python cache into cache data
                        lib_data["graphics"] = python_lib_data["graphics"]
                        logger.info(
                            f"Added {len(python_lib_data['graphics'])} graphics elements from Python cache"
                        )
                    else:
                        logger.warning(
                            f"Python fallback also has no graphics for {sym_id}"
                        )
                except Exception as e:
                    logger.warning(
                        f"Failed to get graphics from Python fallback for {sym_id}: {e}"
                    )
            else:
                pass  # Graphics data already available

            if isinstance(lib_data, list):
                # It's already an S-expression block
                logger.info(f"✅ Adding S-expression symbol definition for {sym_id}")
                lib_symbols_block.append(lib_data)
            else:
                # Build from JSON-based library data
                logger.info(f"🔨 Building symbol definition from JSON for {sym_id}")
                new_sym_def = self._create_symbol_definition(sym_id, lib_data)
                if new_sym_def:
                    logger.info(
                        f"✅ Created symbol definition for {sym_id}, adding to lib_symbols"
                    )
                    if isinstance(new_sym_def[0], Symbol):
                        lib_symbols_block.append(new_sym_def)
                    else:
                        lib_symbols_block.extend(new_sym_def)
                else:
                    logger.error(f"❌ Failed to create symbol definition for {sym_id}")

        logger.info(
            f"📦 lib_symbols block now has {len(lib_symbols_block)} items (including header)"
        )
        # Only show error if we have components but no symbols
        if len(lib_symbols_block) <= 1 and len(self.schematic.components) > 0:
            logger.error(
                "❌❌❌ lib_symbols block is EMPTY - no symbol definitions added!"
            )
        elif len(lib_symbols_block) <= 1 and len(self.schematic.components) == 0:
            logger.info(
                "📋 No components in this sheet (hierarchical sheet with sub-sheets only)"
            )

    def _create_symbol_definition(self, lib_id: str, lib_data: dict):
        """
        Build a full KiCad (symbol ...) block from the library JSON data.
        """
        logger.debug(f"🔧 SCHEMATIC_WRITER: Creating symbol definition for '{lib_id}'")
        base_name = lib_id.split(":")[-1]

        symbol_block = [
            Symbol("symbol"),
            lib_id,
            [Symbol("pin_numbers"), Symbol("hide")],
            [Symbol("pin_names"), [Symbol("offset"), 0]],
            [Symbol("exclude_from_sim"), Symbol("no")],
            [Symbol("in_bom"), Symbol("yes")],
            [Symbol("on_board"), Symbol("yes")],
        ]

        # Properties
        props = lib_data.get("properties", {})
        logger.debug(
            f"    📋 SCHEMATIC_WRITER: Symbol '{lib_id}' has {len(props)} properties"
        )
        for prop_name, prop_value in props.items():
            logger.debug(
                f"        🏷️  SCHEMATIC_WRITER: Property '{prop_name}' = '{prop_value}' (type: {type(prop_value).__name__})"
            )
            hide_symbol = Symbol("no")
            if prop_name in (
                "Footprint",
                "Datasheet",
                "Description",
                "ki_keywords",
                "ki_fp_filters",
            ):
                hide_symbol = Symbol("yes")

            symbol_block.append(
                [
                    Symbol("property"),
                    prop_name,
                    prop_value,
                    [Symbol("at"), 0.0, 0.0, 0],
                    [
                        Symbol("effects"),
                        [Symbol("font"), [Symbol("size"), 1.27, 1.27]],
                        [Symbol("hide"), hide_symbol],
                    ],
                ]
            )

        # Graphics
        shapes = lib_data.get("graphics", [])
        if shapes:
            body_sym_name = f"{base_name}_0_1"
            body_sym_block = [Symbol("symbol"), body_sym_name]

            for g in shapes:
                shape_type = g.get("shape_type", "").lower()
                shape_expr = None

                if shape_type == "rectangle":
                    st = g.get("start", [0, 0])
                    en = g.get("end", [0, 0])
                    shape_expr = rectangle_s_expr(
                        start_x=st[0],
                        start_y=st[1],
                        end_x=en[0],
                        end_y=en[1],
                        stroke_width=g.get("stroke_width", 0.254),
                        fill_type=g.get("fill_type", "none"),
                    )
                elif shape_type == "polyline":
                    pts = g.get("points", [])
                    shape_expr = polyline_s_expr(
                        points=pts,
                        stroke_width=g.get("stroke_width", 0.254),
                        stroke_type=g.get("stroke_type", "default"),
                        fill_type=g.get("fill_type", "none"),
                    )
                elif shape_type == "circle":
                    cx, cy = g.get("center", [0, 0])
                    r = g.get("radius", 2.54)

                    # TestPoint handling
                    if "TestPoint" in lib_id:
                        r = r * TESTPOINT_RADIUS_SCALE_FACTOR

                    shape_expr = circle_s_expr(
                        center_x=cx,
                        center_y=cy,
                        radius=r,
                        stroke_width=g.get("stroke_width", 0.254),
                        fill_type=g.get("fill_type", "none"),
                    )
                elif shape_type == "arc":
                    start = g.get("start", [0, 0])
                    mid = g.get("mid", None)
                    end = g.get("end", [0, 0])

                    is_valid, corrected_mid = validate_arc_geometry(start, mid, end)

                    if not is_valid:
                        logger.warning(
                            f"Arc in '{lib_id}' has invalid geometry, skipping"
                        )
                        continue

                    if corrected_mid != mid:
                        mid = corrected_mid

                    shape_expr = arc_s_expr(
                        start_xy=start,
                        mid_xy=mid,
                        end_xy=end,
                        stroke_width=g.get("stroke_width", 0.254),
                    )

                if shape_expr:
                    body_sym_block.append(shape_expr)

            symbol_block.append(body_sym_block)

        # Pins
        pins = lib_data.get("pins", [])
        if pins:
            pin_sym_name = f"{base_name}_1_1"
            pin_sym_block = [Symbol("symbol"), pin_sym_name]

            for p in pins:
                pin_func = p.get("function", "passive")
                px = float(p.get("x", 0))
                py = float(p.get("y", 0))
                orientation = int(p.get("orientation", 0))
                length = float(p.get("length", 2.54))
                # Ensure pin names are always strings, even if they're numeric
                pin_name = str(p.get("name", "~"))
                pin_num = str(p.get("number", ""))

                pin_sym_block.append(
                    [
                        Symbol("pin"),
                        Symbol(pin_func),
                        Symbol("line"),
                        [Symbol("at"), px, py, orientation],
                        [Symbol("length"), length],
                        [
                            Symbol("name"),
                            pin_name,
                            [
                                Symbol("effects"),
                                [Symbol("font"), [Symbol("size"), 1.27, 1.27]],
                            ],
                        ],
                        [
                            Symbol("number"),
                            pin_num,
                            [
                                Symbol("effects"),
                                [Symbol("font"), [Symbol("size"), 1.27, 1.27]],
                            ],
                        ],
                    ]
                )

            symbol_block.append(pin_sym_block)

        return symbol_block

    def _add_sheet_instances(self, schematic_expr: list):
        """Add sheet_instances section or replace empty one."""
        sheet_instances = [
            Symbol("sheet_instances"),
            [Symbol("path"), "/", [Symbol("page"), "1"]],
        ]

        # Check if sheet_instances already exists
        for i, item in enumerate(schematic_expr):
            if isinstance(item, list) and item and item[0] == Symbol("sheet_instances"):
                # Replace empty sheet_instances with proper one
                if len(item) <= 1:  # Empty or header-only
                    schematic_expr[i] = sheet_instances
                    return
                else:
                    # Already has content, don't duplicate
                    return

        # Find where to insert (before symbol_instances if it exists)
        insert_pos = len(schematic_expr)
        for i, item in enumerate(schematic_expr):
            if (
                isinstance(item, list)
                and item
                and item[0] == Symbol("symbol_instances")
            ):
                insert_pos = i
                break

        schematic_expr.insert(insert_pos, sheet_instances)

    def _add_symbol_instances_table(self, schematic_expr: list):
        """
        Add the symbol_instances section at the end of the schematic.
        This is CRITICAL for KiCad to properly assign component references.
        """
        # Create the symbol_instances block
        symbol_instances = [Symbol("symbol_instances")]

        # Add an entry for each component
        for comp in self.schematic.components:
            # Get the component's UUID
            comp_uuid = comp.uuid

            # Construct hierarchical path
            # For hierarchical designs, we need to include the sheet UUID in the path
            # But we need to use the correct UUID - the sheet symbol UUID from the parent, not arbitrary UUIDs
            if self.hierarchical_path and len(self.hierarchical_path) > 0:
                # For sub-sheets in a hierarchy, use the hierarchical path
                # The path should be /<sheet_uuid>/<component_uuid>
                parent_uuid = self.hierarchical_path[-1]
                path = f"/{parent_uuid}/{comp_uuid}"
            else:
                # For flat designs or the root sheet, use just the component UUID
                path = f"/{comp_uuid}"

            # Create the instance entry
            instance = [
                Symbol("path"),
                path,
                [Symbol("reference"), comp.reference],
                [Symbol("unit"), comp.unit],
                [Symbol("value"), comp.value or ""],
                [Symbol("footprint"), comp.footprint or ""],
            ]
            symbol_instances.append(instance)

        # Append the symbol_instances block to the schematic
        schematic_expr.append(symbol_instances)
        logger.debug(
            f"Added symbol_instances table with {len(self.schematic.components)} entries"
        )


def write_schematic_file(schematic_expr: list, out_path: str):
    """
    Helper to serialize the final S-expression to a .kicad_sch file.
    
    HYBRID APPROACH: Uses modern kicad-sch-api if available, otherwise falls back to legacy.
    The legacy system handles positioning and hierarchy, modern API handles file writing.
    """
    # Try to use modern API for file writing if available
    try:
        from ..config import KiCadConfig, is_kicad_sch_api_available
        
        if is_kicad_sch_api_available():
            # Check if this contains hierarchical sheets - if so, use legacy for now
            import sexpdata
            from pathlib import Path
            has_sheets = _contains_sheet_symbols(schematic_expr)
            
            # For now, only use modern API for component-level schematics
            # Main hierarchical schematics need legacy writer for proper sheet symbol support
            filename = Path(out_path).name
            is_main_schematic = not ('/' in filename or filename.count('.') > 1)
            
            if has_sheets or is_main_schematic:
                logger.info(f"Using legacy writer for hierarchical schematic: {out_path}")
            else:
                logger.info(f"Using modern kicad-sch-api for component schematic: {out_path}")
                return _write_with_modern_api(schematic_expr, out_path)
        else:
            logger.info(f"Modern API not available, using legacy writer: {out_path}")
            
    except Exception as e:
        logger.warning(f"Modern API check failed, using legacy: {e}")
    
    # Fallback to legacy S-expression writing
    return _write_with_legacy_sexpr(schematic_expr, out_path)


def _write_with_modern_api(schematic_expr: list, out_path: str) -> None:
    """Write schematic using modern kicad-sch-api."""
    try:
        import kicad_sch_api as ksa
        import sexpdata
        from pathlib import Path
        
        # Create new schematic
        project_name = Path(out_path).stem
        schematic = ksa.create_schematic(project_name)
        
        # Check if this S-expression contains sheet symbols or individual components
        has_sheets = _contains_sheet_symbols(schematic_expr)
        has_components = _contains_component_symbols(schematic_expr)
        
        if has_components:
            # Extract components and their positions from S-expression
            components_data = _extract_components_from_sexpr(schematic_expr)
            logger.info(f"Modern API: Adding {len(components_data)} positioned components")
            
            # Add components with their calculated positions
            for comp_data in components_data:
                try:
                    kicad_component = schematic.components.add(
                        lib_id=comp_data['lib_id'],
                        reference=comp_data['reference'],
                        value=comp_data.get('value', ''),
                        position=comp_data['position'],
                        footprint=comp_data.get('footprint', None)
                    )
                    logger.debug(f"Added component {comp_data['reference']} at {comp_data['position']}")
                except Exception as e:
                    logger.error(f"Failed to add component {comp_data.get('reference')}: {e}")
        
        # Save using modern API
        schematic.save(str(out_path), preserve_format=True)
        
        logger.info(f"Modern API: Successfully wrote {out_path}")
        
    except Exception as e:
        logger.error(f"Modern API: Failed to write schematic: {e}")
        raise


def _extract_components_from_sexpr(schematic_expr: list) -> List[Dict]:
    """Extract component data with positions from legacy S-expression."""
    components = []
    import sexpdata
    
    def extract_component_data(expr, path=""):
        if isinstance(expr, list) and len(expr) > 0:
            if isinstance(expr[0], sexpdata.Symbol) and str(expr[0]) == 'symbol':
                # Found a component symbol
                comp_data = {
                    'lib_id': None,
                    'reference': 'U',
                    'value': '',
                    'position': (100.0, 100.0),
                    'footprint': None
                }
                
                # Extract component properties
                for item in expr[1:]:
                    if isinstance(item, list) and len(item) > 1:
                        if isinstance(item[0], sexpdata.Symbol):
                            key = str(item[0])
                            if key == 'lib_id' and len(item) > 1:
                                comp_data['lib_id'] = str(item[1]).strip('"')
                            elif key == 'at' and len(item) >= 3:
                                try:
                                    comp_data['position'] = (float(item[1]), float(item[2]))
                                except (ValueError, IndexError):
                                    pass
                            elif key == 'property' and len(item) >= 3:
                                prop_name = str(item[1]).strip('"')
                                prop_value = str(item[2]).strip('"')
                                if prop_name == 'Reference':
                                    comp_data['reference'] = prop_value
                                elif prop_name == 'Value':
                                    comp_data['value'] = prop_value
                                elif prop_name == 'Footprint':
                                    comp_data['footprint'] = prop_value
                
                if comp_data['lib_id']:  # Only add if we found a valid lib_id
                    components.append(comp_data)
                    
            # Recursively search nested lists
            for item in expr:
                if isinstance(item, list):
                    extract_component_data(item, path)
    
    extract_component_data(schematic_expr)
    return components


def _contains_sheet_symbols(schematic_expr: list) -> bool:
    """Check if S-expression contains sheet symbols (hierarchical design)."""
    import sexpdata
    
    def find_sheets(expr):
        if isinstance(expr, list) and len(expr) > 0:
            if isinstance(expr[0], sexpdata.Symbol) and str(expr[0]) == 'sheet':
                return True
            for item in expr:
                if isinstance(item, list) and find_sheets(item):
                    return True
        return False
    
    return find_sheets(schematic_expr)


def _contains_component_symbols(schematic_expr: list) -> bool:
    """Check if S-expression contains component symbols."""
    import sexpdata
    
    def find_components(expr):
        if isinstance(expr, list) and len(expr) > 0:
            if isinstance(expr[0], sexpdata.Symbol) and str(expr[0]) == 'symbol':
                return True
            for item in expr:
                if isinstance(item, list) and find_components(item):
                    return True
        return False
    
    return find_components(schematic_expr)


def _extract_sheets_from_sexpr(schematic_expr: list) -> List[Dict]:
    """Extract sheet symbols from legacy S-expression."""
    sheets = []
    import sexpdata
    
    def extract_sheet_data(expr):
        if isinstance(expr, list) and len(expr) > 0:
            if isinstance(expr[0], sexpdata.Symbol) and str(expr[0]) == 'sheet':
                # Found a sheet symbol
                sheet_data = {
                    'name': 'Unknown',
                    'file': 'unknown.kicad_sch',
                    'position': (100.0, 100.0),
                    'size': (50.0, 30.0),
                    'uuid': None,
                    'pins': []
                }
                
                # Extract sheet properties
                for item in expr[1:]:
                    if isinstance(item, list) and len(item) > 1:
                        if isinstance(item[0], sexpdata.Symbol):
                            key = str(item[0])
                            if key == 'at' and len(item) >= 3:
                                try:
                                    sheet_data['position'] = (float(item[1]), float(item[2]))
                                except (ValueError, IndexError):
                                    pass
                            elif key == 'size' and len(item) >= 3:
                                try:
                                    sheet_data['size'] = (float(item[1]), float(item[2]))
                                except (ValueError, IndexError):
                                    pass
                            elif key == 'property' and len(item) >= 3:
                                prop_name = str(item[1]).strip('"')
                                prop_value = str(item[2]).strip('"')
                                if prop_name == 'Sheet name':
                                    sheet_data['name'] = prop_value
                                elif prop_name == 'Sheet file':
                                    sheet_data['file'] = prop_value
                            elif key == 'uuid' and len(item) > 1:
                                sheet_data['uuid'] = str(item[1]).strip('"')
                            elif key == 'pin' and len(item) > 1:
                                # Extract sheet pin information
                                pin_info = {'name': str(item[1]).strip('"'), 'type': 'input', 'position': (0, 0)}
                                for pin_item in item[2:]:
                                    if isinstance(pin_item, list) and len(pin_item) > 1:
                                        if isinstance(pin_item[0], sexpdata.Symbol):
                                            pin_key = str(pin_item[0])
                                            if pin_key == 'at' and len(pin_item) >= 3:
                                                pin_info['position'] = (float(pin_item[1]), float(pin_item[2]))
                                            elif pin_key == 'type' and len(pin_item) > 1:
                                                pin_info['type'] = str(pin_item[1])
                                sheet_data['pins'].append(pin_info)
                
                sheets.append(sheet_data)
                    
            # Recursively search nested lists
            for item in expr:
                if isinstance(item, list):
                    extract_sheet_data(item)
    
    extract_sheet_data(schematic_expr)
    return sheets


def _write_with_legacy_sexpr(schematic_expr: list, out_path: str) -> None:
    """Legacy S-expression writing method."""
    start_time = time.perf_counter()
    expr_size = len(str(schematic_expr)) if schematic_expr else 0

    logger.info(f"📜 LEGACY WRITER: Starting file write to {out_path}")
    logger.info(f"📊 LEGACY WRITER: Input S-expression size: {expr_size:,} characters")

    # Use the original legacy S-expression parser
    try:
        from circuit_synth.kicad.core.s_expression import SExpressionParser
        parser = SExpressionParser()
        parser.write_file(schematic_expr, out_path)
        
        # Analyze the output file
        with open(out_path, "r", encoding="utf-8") as f:
            content = f.read()

        total_time = time.perf_counter() - start_time
        throughput = len(content) / (total_time * 1000) if total_time > 0 else 0

        logger.info(f"📜 LEGACY WRITER: File written successfully in {total_time*1000:.2f}ms")
        logger.info(f"📊 LEGACY WRITER: Output size: {len(content):,} characters")
        logger.info(f"⚡ LEGACY WRITER: Throughput: {throughput:.1f} chars/ms")
        
    except Exception as e:
        logger.error(f"📜 LEGACY WRITER: Failed to write schematic: {e}")
        raise
    start_time = time.perf_counter()
    expr_size = len(str(schematic_expr)) if schematic_expr else 0

    logger.info(f"🚀 WRITE_SCHEMATIC_FILE: Starting file write to {out_path}")
    logger.info(
        f"📊 WRITE_SCHEMATIC_FILE: Input S-expression size: {expr_size:,} characters"
    )
    logger.info(f"🐍 WRITE_SCHEMATIC_FILE: Using Python formatting")

    # Debug: Check for sheet pins with orientation - time this analysis
    debug_start = time.perf_counter()
    import sexpdata

    sheet_pin_count = 0

    logger.debug("Using KiCad formatter")

    # Debug: Check for sheet pins with orientation
    import sexpdata

    def find_sheet_pins_in_expr(expr, path="", in_sheet=False):
        nonlocal sheet_pin_count
        if isinstance(expr, list):
            if len(expr) > 0 and isinstance(expr[0], sexpdata.Symbol):
                tag = str(expr[0])
                if tag == "sheet":
                    # We're in a sheet, look for pins inside
                    for i, item in enumerate(expr):
                        find_sheet_pins_in_expr(item, f"{path}[{i}]", in_sheet=True)
                elif tag == "pin" and in_sheet:
                    sheet_pin_count += 1
                    # Found a sheet pin, look for its "at" expression
                    logger.debug(
                        f"Found sheet pin '{expr[1] if len(expr) > 1 else '?'}' at {path}"
                    )
                    for item in expr:
                        if (
                            isinstance(item, list)
                            and len(item) > 0
                            and isinstance(item[0], sexpdata.Symbol)
                            and str(item[0]) == "at"
                        ):
                            logger.debug(f"  Sheet pin 'at' expression: {item}")
                else:
                    for i, item in enumerate(expr):
                        find_sheet_pins_in_expr(item, f"{path}[{i}]", in_sheet=in_sheet)

    find_sheet_pins_in_expr(schematic_expr)
    debug_time = time.perf_counter() - debug_start
    logger.debug(
        f"🔍 WRITE_SCHEMATIC_FILE: Debug analysis completed in {debug_time*1000:.2f}ms, found {sheet_pin_count} sheet pins"
    )

    # This uses the Python format_kicad_schematic function
    parser_start = time.perf_counter()
    logger.info("⚡ WRITE_SCHEMATIC_FILE: Starting S-expression parsing and formatting")

    from circuit_synth.kicad.core.s_expression import SExpressionParser

    parser = SExpressionParser()
    parser.write_file(schematic_expr, out_path)

    parser_time = time.perf_counter() - parser_start
    logger.info(
        f"✅ WRITE_SCHEMATIC_FILE: S-expression parsing and formatting completed in {parser_time*1000:.2f}ms"
    )

    # Analyze the output file
    file_analysis_start = time.perf_counter()
    with open(out_path, "r", encoding="utf-8") as f:
        content = f.read()
    file_analysis_time = time.perf_counter() - file_analysis_start

    total_time = time.perf_counter() - start_time
    throughput = len(content) / (total_time * 1000) if total_time > 0 else 0

    logger.info(f"🏁 WRITE_SCHEMATIC_FILE: ✅ FILE WRITE COMPLETE")
    logger.info(f"⏱️  WRITE_SCHEMATIC_FILE: Total time: {total_time*1000:.2f}ms")
    logger.info(
        f"📊 WRITE_SCHEMATIC_FILE: Output file size: {len(content):,} characters"
    )
    logger.info(f"📄 WRITE_SCHEMATIC_FILE: Output file: {out_path}")
    logger.info(
        f"⚡ WRITE_SCHEMATIC_FILE: Write throughput: {throughput:.1f} chars/ms ({throughput*1000:.0f} chars/sec)"
    )

    # Performance breakdown
    logger.info("📈 WRITE_PERFORMANCE_BREAKDOWN:")
    logger.info(
        f"  🔍 Debug analysis: {debug_time*1000:.2f}ms ({debug_time/total_time*100:.1f}%)"
    )
    logger.info(
        f"  🔄 S-expression formatting: {parser_time*1000:.2f}ms ({parser_time/total_time*100:.1f}%)"
    )
    logger.info(
        f"  📊 File analysis: {file_analysis_time*1000:.2f}ms ({file_analysis_time/total_time*100:.1f}%)"
    )

    # Compression ratio analysis
    compression_ratio = len(content) / expr_size if expr_size > 0 else 1.0
    logger.info(
        f"📦 WRITE_SCHEMATIC_FILE: Size change: {expr_size:,} → {len(content):,} chars ({compression_ratio:.2f}x)"
    )

    # Performance summary
    logger.info(f"⚡ PERFORMANCE: Schematic written in {total_time*1000:.2f}ms")

    logger.info(
        f"✅ WRITE_SCHEMATIC_FILE: Successfully wrote {len(content):,} characters to {out_path}"
    )

    # Log the file size
    with open(out_path, "r", encoding="utf-8") as f:
        content = f.read()
    logger.debug(f"Schematic written. Length = {len(content)} chars.")
