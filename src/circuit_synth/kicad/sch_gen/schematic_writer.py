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
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

log_level = os.environ.get("CIRCUIT_SYNTH_LOG_LEVEL", "WARNING")
try:
    level = getattr(logging, log_level.upper())
except AttributeError:
    level = logging.WARNING

logging.basicConfig(
    level=level, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

from kicad_sch_api.core.parser import SExpressionParser
from sexpdata import Symbol, dumps

# Add performance timing
try:
    from ...core.performance_profiler import quick_time
except ImportError:
    # Fallback if profiler not available
    def quick_time(name):
        def decorator(func):
            return func

        return decorator


# Import full Schematic class with save() method
from kicad_sch_api.core.schematic import Schematic

# Import from KiCad API
from kicad_sch_api.core.types import (
    Junction,
    Label,
    LabelType,
    Point,
    Rectangle,
    SchematicSymbol,
    Sheet,
    SheetPin,
    SymbolInstance,
    Text,
    Wire,
)
from sexpdata import Symbol

# Import symbol cache for multi-unit component support
from ..core.symbol_cache import get_symbol_cache

# Use optimized symbol cache from kicad_symbol_cache for better performance,
# but keep Python fallback for graphics data
from circuit_synth.kicad.kicad_symbol_cache import SymbolLibCache

# Import Python symbol cache specifically for graphics data
from circuit_synth.kicad.kicad_symbol_cache import (
    SymbolLibCache as PythonSymbolLibCache,
)
from circuit_synth.kicad.schematic.component_manager import ComponentManager
from circuit_synth.kicad.schematic.component_unit import ComponentUnit
from circuit_synth.kicad.schematic.placement import PlacementEngine, PlacementStrategy

# Import existing dependencies
from ...core.circuit import Circuit
from ...core.hierarchy import PortDirection
from .collision_manager import SHEET_MARGIN
from .integrated_reference_manager import IntegratedReferenceManager

# from .kicad_formatter import format_kicad_schematic  # Removed - using integrated formatter
from .shape_drawer import arc_s_expr, circle_s_expr, polyline_s_expr, rectangle_s_expr
from .symbol_geometry import SymbolBoundingBoxCalculator
from .wired_layout import (
    ComponentInfo,
    LayoutPlan,
    NetRole,
    PinInfo,
    WiredLayoutEngine,
    outward_step,
    rotate_offset,
)
from .wired_layout import GRID, LABEL_STUB, POWER_STUB
from .wired_layout import SHEET_MARGIN_Y as LAYOUT_MARGIN_Y

# Gap between the bottom of the child sheet symbols and the first row of parts.
LAYOUT_SHEET_GAP = 20.32

# How far the reference and value text sit above and below a rotated part.
FIELD_OFFSET = 5.08

# Clear space kept between two power symbols so their rail names do not collide.
POWER_TEXT_CLEARANCE = 7.62

# Geometry of hierarchical sheet pins, in mm. KiCad snaps schematic geometry to
# a 50mil grid, and 100mil pin spacing matches the symbol libraries.
GRID_SIZE = 1.27
SHEET_PORT_SPACING = 2.54
SHEET_PORT_MARGIN = 5.08
SHEET_PORT_STUB = 5.08
PIN_NAME_CHAR_WIDTH = 1.4

# Where free-standing labels for unconnected ports are parked.
ORPHAN_PORT_X = 12.7
ORPHAN_PORT_Y = 190.5

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

        # Create KiCad API Schematic object using create() factory method
        self.schematic = Schematic.create(
            name=self.project_name,
            version="20250114",
            generator="circuit_synth",
            generator_version="0.8.36",
            paper=self.paper_size,
            uuid=self.uuid_top,
        )

        # Initialize KiCad API managers
        self.component_manager = ComponentManager(self.schematic, project_name=self.project_name)
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

        # Cached answer for _uses_declared_ports(), the set of ports that have
        # picked up a label while this sheet is being written, and the parts
        # whose reference and value text the layout repositions.
        self._declared_ports_in_use = None
        self._ports_labelled = set()
        self._laid_out_fields: Dict[str, Tuple[float, float]] = {}
        self._power_positions: List[Tuple[float, float]] = []

        # Log initialization details
        logger.debug(f"SchematicWriter initialized for circuit '{circuit.name}'")
        logger.debug(f"  - Using KiCad API Phase 2 integration")
        logger.debug(f"  - Hierarchical path: {self.hierarchical_path}")
        logger.debug(f"  - Self UUID (uuid_top): {self.uuid_top}")
        logger.debug(f"  - Project name: {self.project_name}")

        # CRITICAL DEBUG: Log hierarchical path for UUID fix verification
        import sys

        print(
            f"\n🔍 WRITER_INIT: Circuit='{circuit.name}'", file=sys.stderr, flush=True
        )
        print(
            f"🔍 WRITER_INIT:   Hierarchical path={self.hierarchical_path}",
            file=sys.stderr,
            flush=True,
        )
        print(
            f"🔍 WRITER_INIT:   Self UUID={self.uuid_top}", file=sys.stderr, flush=True
        )
        if self.hierarchical_path and len(self.hierarchical_path) > 0:
            print(
                f"🔍 WRITER_INIT:   Root UUID (path[0])={self.hierarchical_path[0]}",
                file=sys.stderr,
                flush=True,
            )

    @staticmethod
    def _escape_kicad_string(text: str) -> str:
        r"""
        Escape a string for safe inclusion in KiCad S-expression format.

        KiCad's S-expression parser expects:
        - Backslashes to be escaped: \ -> \\
        - Quotes to be escaped: " -> \"
        - Newlines to be escaped: \n (actual newline) -> \\n (escaped newline)

        Unicode characters (including box-drawing characters and symbols) are preserved
        as they are valid in UTF-8 strings.

        Args:
            text: The raw string to escape

        Returns:
            The escaped string safe for KiCad S-expression format
        """
        if not isinstance(text, str):
            text = str(text)

        # Escape backslashes first (must be done before other replacements)
        text = text.replace("\\", "\\\\")

        # Escape quotes
        text = text.replace('"', '\\"')

        # Escape newlines (convert actual newlines to escaped representation)
        text = text.replace("\n", "\\n")

        # Escape carriage returns
        text = text.replace("\r", "\\r")

        # Escape tabs
        text = text.replace("\t", "\\t")

        return text

    @quick_time("Generate S-Expression")
    def generate_s_expr(self) -> list:
        """
        Create the full top-level (kicad_sch ...) list structure for this circuit.

        PERFORMANCE MONITORING: Times each major operation.
        """
        with open("/tmp/circuit_synth_debug.log", "a") as f:
            f.write(f"generate_s_expr called for circuit {self.circuit.name}\n")
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

        # Lay the components out and wire them together. Anything the layout
        # engine cannot route tidily falls back to a label at every pin, which
        # is what the generator did for all nets before.
        layout_plan = self._apply_wired_layout()

        # Add pin-level net labels
        labels_start = time.perf_counter()
        logger.info(
            f"⚡ STEP 3/8: Adding pin-level net labels for {len(self.circuit.nets)} nets..."
        )
        component_labels = self._add_pin_level_net_labels(layout_plan)
        labels_time = time.perf_counter() - labels_start
        logger.info(f"✅ STEP 3/8: Net labels added in {labels_time*1000:.2f}ms")
        logger.debug(
            f"  Label tracking: {len(component_labels)} components with labels"
        )

        # Add subcircuit sheets if needed
        sheets_start = time.perf_counter()
        subcircuit_count = (
            len(self.circuit.child_instances) if self.circuit.child_instances else 0
        )
        logger.info(f"⚡ STEP 4/8: Adding {subcircuit_count} subcircuit sheets...")
        self._add_subcircuit_sheets()
        sheets_time = time.perf_counter() - sheets_start
        logger.info(f"✅ STEP 4/8: Subcircuit sheets added in {sheets_time*1000:.2f}ms")

        # Any declared port that neither a component pin nor a child sheet pin
        # picked up still has to appear, or the block's interface is incomplete.
        self._add_unconnected_port_labels()

        # Create ComponentUnits (bundles component + labels + bbox)
        units_start = time.perf_counter()
        logger.info(
            f"⚡ STEP 5/8: Creating ComponentUnits for {len(self.circuit.components)} components..."
        )
        component_units = self._create_component_units(component_labels)
        units_time = time.perf_counter() - units_start
        logger.info(f"✅ STEP 5/8: ComponentUnits created in {units_time*1000:.2f}ms")

        # Draw bounding boxes if enabled
        bbox_start = time.perf_counter()
        if self.draw_bounding_boxes:
            logger.info(
                f"⚡ STEP 6/8: Drawing bounding boxes for {len(component_units)} ComponentUnits..."
            )
            self._draw_component_unit_bboxes(component_units)
            bbox_time = time.perf_counter() - bbox_start
            logger.info(f"✅ STEP 6/8: Bounding boxes drawn in {bbox_time*1000:.2f}ms")
        else:
            logger.info("⏭️  STEP 6/8: Bounding boxes disabled, skipping")
            bbox_time = 0

        # Add text annotations (TextBox, TextProperty, etc.)
        self._add_annotations()

        # Populate lib_symbols from the symbol cache
        lib_start = time.perf_counter()
        logger.info("⚡ STEP 7/8: Populating symbol library definitions...")
        self._populate_lib_symbols()
        lib_time = time.perf_counter() - lib_start
        logger.info(f"✅ STEP 7/8: Symbol library populated in {lib_time*1000:.2f}ms")

        total_time = time.perf_counter() - start_time

        logger.info("🏁 STEP 8/8: Schematic generation complete!")
        logger.info(f"✅ GENERATE_S_EXPR: ✅ TOTAL TIME: {total_time*1000:.2f}ms")

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
            f"  📚 Lib symbols: {lib_time*1000:.2f}ms ({lib_time/total_time*100:.1f}%)"
        )

        logger.info(f"⚡ PERFORMANCE: Completed in {total_time*1000:.2f}ms")

        # Return the Schematic object instead of S-expression
        return self.schematic

    @quick_time("Add Components to Schematic")
    def _add_components(self):
        """
        Add all components from the circuit using the ComponentManager.
        """
        logger.debug(f"=== ADDING COMPONENTS FOR CIRCUIT: {self.circuit.name} ===")

        # circuit.components is a list of SchematicSymbols (from circuit_loader.py Circuit class)
        # This contains only components that belong directly to THIS circuit
        direct_components = self.circuit.components

        logger.debug(f"  Number of direct components: {len(direct_components)}")

        # Track reference mapping for net updates
        self.reference_mapping = {}

        for idx, comp in enumerate(direct_components):
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

            # Extract user properties from SchematicSymbol.properties
            # At this point, comp is a SchematicSymbol loaded from JSON
            # Properties were already extracted by circuit_loader.py
            from ..property_utils import filter_user_properties

            user_properties = (
                filter_user_properties(comp.properties)
                if hasattr(comp, "properties")
                else {}
            )

            # Check if DNP flag is set via properties or flags
            dnp_value = False
            if "DNP" in user_properties:
                dnp_str = user_properties["DNP"]
                dnp_value = (
                    dnp_str.lower() in ("true", "yes", "1")
                    if isinstance(dnp_str, str)
                    else bool(dnp_str)
                )
            elif hasattr(comp, "in_bom") and not comp.in_bom:
                # If in_bom is False, component is DNP
                dnp_value = True

            logger.debug(
                f"      Component properties: {len(user_properties)} user properties"
            )
            if user_properties:
                logger.debug(f"      Property keys: {list(user_properties.keys())}")

            # Check if this is a multi-unit component
            symbol_cache = get_symbol_cache()
            symbol_def = symbol_cache.get_symbol(comp.lib_id)
            # Use 'units' attribute which contains the number of units
            unit_count = getattr(symbol_def, "units", 1) if symbol_def else 1

            logger.debug(f"      Component {comp.lib_id} has {unit_count} unit(s)")

            # Add component using the API - for multi-unit, add each unit separately
            # Time the component manager operation
            with timed_operation(
                f"add_component[{comp.lib_id}]", threshold_ms=20, details=comp_details
            ):
                # For multi-unit components, add each unit as a separate symbol instance
                if unit_count > 1:
                    logger.debug(
                        f"      Adding multi-unit component with {unit_count} units"
                    )
                    # Add each unit with a vertical offset
                    unit_spacing = (
                        12.7  # 0.5 inch (12.7mm) vertical spacing between units
                    )
                    for unit_num in range(1, unit_count + 1):
                        unit_position = (
                            comp.position.x,
                            comp.position.y + (unit_num - 1) * unit_spacing,
                        )
                        logger.debug(
                            f"        Adding unit {unit_num} at position {unit_position}"
                        )
                        api_component = self.component_manager.add_component(
                            library_id=comp.lib_id,
                            reference=new_ref,
                            value=comp.value,
                            position=unit_position,
                            placement_strategy=PlacementStrategy.AUTO,  # Position is explicit so it will be used
                            footprint=comp.footprint,
                            snap_to_grid=True,  # Snap to grid for proper alignment
                            unit=unit_num,  # Specify the unit number
                            **user_properties,  # Pass user properties
                        )

                        if api_component and unit_num == 1:
                            # Store the first unit as the main component for mapping
                            first_api_component = api_component
                else:
                    # Single-unit component - add as before
                    api_component = self.component_manager.add_component(
                        library_id=comp.lib_id,
                        reference=new_ref,
                        value=comp.value,
                        position=(comp.position.x, comp.position.y),
                        placement_strategy=PlacementStrategy.AUTO,
                        footprint=comp.footprint,
                        unit=1,  # Explicitly set unit 1
                        **user_properties,  # Pass user properties
                    )
                    first_api_component = api_component

            if first_api_component:
                # Update our mapping (use the first unit for UUID mapping)
                self.component_uuid_map[new_ref] = first_api_component.uuid

                # Update the original component reference
                comp.reference = new_ref

                # Copy additional properties to first unit
                first_api_component.rotation = comp.rotation
                # Note: unit is already set during add_component call
                first_api_component.in_bom = getattr(comp, "in_bom", True)
                first_api_component.on_board = getattr(comp, "on_board", True)
                # dnp and mirror may not exist in kicad-sch-api SchematicSymbol
                if hasattr(first_api_component, "dnp") and hasattr(comp, "dnp"):
                    first_api_component.dnp = comp.dnp
                if hasattr(first_api_component, "mirror") and hasattr(comp, "mirror"):
                    first_api_component.mirror = comp.mirror

                # Store hierarchy path and project name for instances generation
                if self.hierarchical_path:
                    first_api_component.properties["hierarchy_path"] = "/" + "/".join(
                        self.hierarchical_path
                    )

                # Store project name for the instances section in new KiCad format
                first_api_component.properties["project_name"] = self.project_name

                # CRITICAL: Store root UUID for instances path generation
                # The parser needs this to create correct instance paths
                if self.hierarchical_path and len(self.hierarchical_path) > 0:
                    root_uuid = self.hierarchical_path[0]
                    first_api_component.properties["root_uuid"] = root_uuid
                    logger.debug(f"  Storing root_uuid property: {root_uuid}")

                # Create instances for the new KiCad format (20250114+)
                # The path should contain only sheet UUIDs, not component UUID
                logger.debug(f"=== CREATING INSTANCE FOR COMPONENT {new_ref} ===")
                logger.debug(f"  Component lib_id: {comp.lib_id}")
                logger.debug(f"  Component UUID: {first_api_component.uuid}")
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

                # CRITICAL FIX FOR KICAD ANNOTATION:
                # Component instances MUST use the FULL hierarchical path
                # This includes the root UUID + all sheet symbol UUIDs in the path
                # For KiCad to properly annotate references (avoid "?" display)
                if self.hierarchical_path and len(self.hierarchical_path) > 0:
                    # Use the FULL hierarchical path (root + all sheet symbols)
                    # The hierarchical_path contains [root_uuid, sheet_symbol_uuid, sub_sheet_symbol_uuid, ...]
                    # For USB_Port: [root_uuid, usb_port_sheet_symbol_uuid]
                    # For nested sheets like LED_Blinker: [root_uuid, esp32_mcu_sheet_symbol_uuid, led_blinker_sheet_symbol_uuid]
                    instance_path = "/" + "/".join(self.hierarchical_path)
                    logger.debug(
                        f"  Creating SUB-SHEET component instance with FULL hierarchical path: {instance_path}"
                    )
                    logger.debug(
                        f"    Full hierarchical path: {self.hierarchical_path}"
                    )
                    logger.debug(f"    Number of levels: {len(self.hierarchical_path)}")
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
                    path=instance_path,
                    reference=new_ref,
                    unit=comp.unit,
                )
                api_component.instances.append(instance)

                logger.debug(f"  Instance created:")
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
        Use text-flow placement algorithm for component arrangement.

        Places components left-to-right, wrapping to new rows when needed.
        Automatically selects appropriate sheet size (A4 or A3).
        """
        import sys

        print("=" * 80, file=sys.stderr, flush=True)
        print(
            "🔤 TEXT-FLOW PLACEMENT _place_components() called!",
            file=sys.stderr,
            flush=True,
        )
        print("=" * 80, file=sys.stderr, flush=True)

        if not self.schematic.components:
            logger.debug("No components to place")
            print("⚠️  No components to place!", file=sys.stderr, flush=True)
            return

        start_time = time.perf_counter()
        print(
            f"🚀 PLACE_COMPONENTS: Starting placement of {len(self.schematic.components)} components",
            file=sys.stderr,
            flush=True,
        )
        print(
            f"🔤 PLACE_COMPONENTS: Using text-flow placement algorithm",
            file=sys.stderr,
            flush=True,
        )
        logger.info(
            f"🚀 PLACE_COMPONENTS: Starting placement of {len(self.schematic.components)} components"
        )
        logger.info(f"🔤 PLACE_COMPONENTS: Using text-flow placement algorithm")

        # Print current positions
        print("\n🔍 Component positions before placement:")
        for comp in self.schematic.components:
            print(f"  {comp.reference}: ({comp.position.x:.1f}, {comp.position.y:.1f})")

        # Use text-flow placement for ALL components (ignore existing positions)
        components_needing_placement = list(self.schematic.components)

        print(
            f"\n📊 Components to place with text-flow: {len(components_needing_placement)}"
        )

        logger.info(
            f"🔧 PLACE_COMPONENTS: {len(components_needing_placement)} components need placement"
        )

        # Use text-flow placement
        try:
            from ..kicad_symbol_cache import SymbolLibCache
            from ..schematic.text_flow_placement import place_with_text_flow
            from .symbol_geometry import SymbolBoundingBoxCalculator

            placement_start = time.perf_counter()

            # Get accurate bounding boxes using SymbolBoundingBoxCalculator
            # (same method used to draw the bbox rectangles)
            component_bboxes = []

            # Add components individually (multi-unit components will be placed side-by-side)
            # Create unique placement keys for multi-unit components
            placement_key_map = {}  # Maps unique placement key -> component
            for comp in components_needing_placement:
                # Create unique key for placement (reference + unit number)
                unit_num = getattr(comp, "unit", 1)
                placement_key = f"{comp.reference}_U{unit_num}"
                placement_key_map[placement_key] = comp

                # Get symbol library data
                lib_data = SymbolLibCache.get_symbol_data(comp.lib_id)
                if not lib_data:
                    logger.warning(
                        f"No symbol data found for {comp.lib_id}, using fallback size"
                    )
                    # Fallback to reasonable defaults
                    width, height = 10.0, 10.0
                else:
                    # Calculate accurate bounding box including pin labels for proper collision detection
                    import sys

                    print(
                        f"\n🔍 PLACEMENT: About to calculate bbox for {placement_key} ({comp.lib_id})",
                        file=sys.stderr,
                        flush=True,
                    )
                    min_x, min_y, max_x, max_y = (
                        SymbolBoundingBoxCalculator.calculate_bounding_box(
                            lib_data, include_properties=True
                        )
                    )
                    width = max_x - min_x
                    height = max_y - min_y
                    print(
                        f"🔍 PLACEMENT: Calculated bbox for {placement_key}: {width:.2f} x {height:.2f} mm",
                        file=sys.stderr,
                        flush=True,
                    )

                component_bboxes.append((placement_key, width, height))
                logger.debug(f"  {placement_key}: bbox {width:.1f}x{height:.1f}mm")

            # Add sheets (if any)
            if (
                hasattr(self.circuit, "child_instances")
                and self.circuit.child_instances
            ):
                print(f"\n📄 Found {len(self.circuit.child_instances)} sheets to place")
                logger.debug(
                    f"Found {len(self.circuit.child_instances)} sheets to place"
                )

                for child in self.circuit.child_instances:
                    sub_name = child["sub_name"]

                    # Calculate sheet dimensions (same logic as main_generator.py)
                    sub_circ = self.all_subcircuits.get(sub_name)
                    sub_ports = list(getattr(sub_circ, "ports", []) or []) if sub_circ else []
                    if sub_ports:
                        # A declared interface gives an exact pin count, so the
                        # sheet can be sized to fit its pins and pin names.
                        left_ports, right_ports = self._split_ports_by_side(sub_ports)
                        name_width = len(sub_name) * 1.5 + 10
                        sheet_width, sheet_height = self._size_sheet_for_ports(
                            max(25.4, name_width), 20.32, left_ports, right_ports
                        )
                        # Reserve room either side for the stub labels.
                        longest_net = max(
                            (len(p.net_name) for p in sub_ports), default=0
                        )
                        bbox_width = sheet_width + 2 * (
                            SHEET_PORT_STUB + longest_net * PIN_NAME_CHAR_WIDTH
                        )

                        child["sheet_width"] = sheet_width
                        child["sheet_height"] = sheet_height
                        child["bbox_width"] = bbox_width
                        child["bbox_height"] = sheet_height
                        component_bboxes.append(
                            (f"SHEET_{sub_name}", bbox_width, sheet_height)
                        )
                        child["placement_ref"] = f"SHEET_{sub_name}"
                        logger.debug(
                            f"  Sheet {sub_name}: {len(sub_ports)} declared port(s), "
                            f"bbox {bbox_width:.1f}x{sheet_height:.1f}mm"
                        )
                        continue

                    if sub_circ:
                        pin_count = len(sub_circ.nets)

                        # Calculate height based on pin count
                        pin_spacing = 2.54
                        min_height = 20.32
                        padding = 5.08
                        calculated_height = (pin_count * pin_spacing) + (2 * padding)
                        sheet_height = max(min_height, calculated_height)

                        # Calculate width based on name and labels
                        min_width = 25.4
                        char_width = 1.5
                        name_width = len(sub_name) * char_width + 10

                        # Find longest net name
                        max_label_length = max(
                            (len(net.name) for net in sub_circ.nets), default=0
                        )

                        # Calculate bbox including labels that extend beyond sheet
                        label_char_width = 1.27
                        label_width = max_label_length * label_char_width + 10

                        # Bbox width = sheet width + label extension
                        sheet_width = max(min_width, name_width)
                        bbox_width = sheet_width + label_width

                        print(
                            f"🔍 PLACEMENT: Sheet {sub_name}: sheet={sheet_width:.1f}mm, labels={label_width:.1f}mm, bbox={bbox_width:.1f}x{sheet_height:.1f}mm"
                        )
                        logger.debug(
                            f"  Sheet {sub_name}: bbox {bbox_width:.1f}x{sheet_height:.1f}mm"
                        )

                        # Store dimensions for later use
                        child["sheet_width"] = sheet_width
                        child["sheet_height"] = sheet_height
                        child["bbox_width"] = bbox_width
                        child["bbox_height"] = sheet_height
                    else:
                        # Use defaults
                        sheet_width = 50.8
                        sheet_height = 25.4
                        bbox_width = sheet_width + 20  # Add some space for labels
                        child["sheet_width"] = sheet_width
                        child["sheet_height"] = sheet_height
                        child["bbox_width"] = bbox_width
                        child["bbox_height"] = sheet_height

                    # Add to placement list using a sheet identifier
                    sheet_ref = f"SHEET_{sub_name}"
                    component_bboxes.append((sheet_ref, bbox_width, sheet_height))
                    child["placement_ref"] = sheet_ref

            # Run text-flow placement algorithm
            # Use larger spacing to account for hierarchical labels (not included in placement bbox)
            placements, selected_sheet = place_with_text_flow(
                component_bboxes, spacing=15.0
            )

            logger.info(f"📄 PLACE_COMPONENTS: Selected sheet size: {selected_sheet}")

            # Apply placements to components and sheets
            placement_map = {ref: (x, y) for ref, x, y in placements}

            # Apply to components (each unit placed independently using unique keys)
            for placement_key, comp in placement_key_map.items():
                if placement_key in placement_map:
                    x, y = placement_map[placement_key]
                    comp.position = Point(x, y)
                    logger.debug(
                        f"      Applied position to {comp.reference} unit {getattr(comp, 'unit', 1)}: ({x}, {y})"
                    )

            # Apply to sheets
            if (
                hasattr(self.circuit, "child_instances")
                and self.circuit.child_instances
            ):
                for child in self.circuit.child_instances:
                    sheet_ref = child.get("placement_ref")
                    if sheet_ref and sheet_ref in placement_map:
                        x, y = placement_map[sheet_ref]
                        child["x"] = x
                        child["y"] = y
                        print(
                            f"📄 Placed sheet {child['sub_name']} at ({x:.1f}, {y:.1f})"
                        )
                        logger.debug(
                            f"Placed sheet {child['sub_name']} at ({x:.1f}, {y:.1f})"
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
                f"❌ PLACE_COMPONENTS: TEXT-FLOW PLACEMENT FAILED after {placement_error_time*1000:.2f}ms: {e}"
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

    def _is_net_hierarchical(self, net_obj):
        """
        Check if a net should have a hierarchical label (vs local label).

        A net needs a hierarchical label if it:
        1. Is shared with the parent circuit (passed as parameter), OR
        2. Is used by any child circuit (needs to connect down to children)

        Local labels are ONLY for nets that are purely internal to this sheet.

        Args:
            net_obj: The Net object to check

        Returns:
            bool: True if net should have hierarchical label, False for local label
        """
        # Once any block in this part of the hierarchy declares its ports, the
        # interface is known exactly: a net leaves the sheet only through a
        # declared port, and those are labelled by the caller. Everything else
        # is internal and must be a local label - a hierarchical label with no
        # matching sheet pin is an ERC error in KiCad.
        if self._uses_declared_ports():
            return False

        # TEMPORARY: Always use hierarchical labels for now
        # We want all labels to be hierarchical until we're ready to differentiate
        # between local (internal) and hierarchical (cross-circuit) nets.
        # The logic below is correct but bypassed for now.
        return True

        # TODO: Enable this logic when ready to support local labels
        # ============================================================
        # # Check if shared with parent
        # parent_circuit = None
        # for circ_name, circ in self.all_subcircuits.items():
        #     for child_info in circ.child_instances:
        #         if child_info["sub_name"] == self.circuit.name:
        #             parent_circuit = circ
        #             break
        #     if parent_circuit:
        #         break
        #
        # if parent_circuit:
        #     # Check if this Net OBJECT (not name) is used in the parent
        #     parent_nets = parent_circuit.nets.values() if isinstance(parent_circuit.nets, dict) else parent_circuit.nets
        #     for parent_net in parent_nets:
        #         if parent_net is net_obj:  # Same object reference!
        #             return True
        #
        #     # Fallback to name matching (for JSON-loaded circuits)
        #     parent_net_names = {n.name for n in parent_nets}
        #     if net_obj.name in parent_net_names:
        #         return True
        #
        # # Check if used by any child circuit
        # for child_info in self.circuit.child_instances:
        #     child_circ = self.all_subcircuits[child_info["sub_name"]]
        #     child_nets = child_circ.nets.values() if isinstance(child_circ.nets, dict) else child_circ.nets
        #
        #     for child_net in child_nets:
        #         # Check object identity
        #         if child_net is net_obj:
        #             return True
        #         # Fallback to name matching
        #         if child_net.name == net_obj.name:
        #             return True
        #
        # return False

    def _net_role(self, net) -> NetRole:
        """Classify how a net should be drawn on this sheet.

        Args:
            net: The circuit's Net object.

        Returns:
            POWER for rails that render as power symbols, PORT for nets leaving
            the sheet through a declared port, SIGNAL for everything else.
        """
        if net.name in self._ports_by_net():
            return NetRole.PORT
        if getattr(net, "is_power", False) and getattr(net, "power_symbol", None):
            return NetRole.POWER
        return NetRole.SIGNAL

    def _collect_layout_components(self) -> List[ComponentInfo]:
        """Describe this sheet's components for the layout engine.

        Returns:
            One ComponentInfo per component whose symbol has usable pin data.
            Components with no pin data are skipped so they keep their existing
            placement rather than being dropped.
        """
        pins_by_component: Dict[str, Dict[str, str]] = defaultdict(dict)
        circuit_nets = (
            self.circuit.nets.values()
            if isinstance(self.circuit.nets, dict)
            else self.circuit.nets
        )
        for net in circuit_nets:
            for comp_ref, pin_identifier in net.connections:
                pins_by_component[comp_ref][str(pin_identifier)] = net.name

        collected: List[ComponentInfo] = []
        for comp in self.circuit.components:
            reference = comp.reference
            lib_data = SymbolLibCache.get_symbol_data(comp.lib_id)
            if not lib_data or not lib_data.get("pins"):
                logger.debug(
                    "No pin data for %s (%s), leaving it to the default placement",
                    reference,
                    comp.lib_id,
                )
                continue

            pins = []
            for pin_data in lib_data["pins"]:
                identifier = str(pin_data.get("number", ""))
                pins.append(
                    PinInfo(
                        component=reference,
                        identifier=identifier,
                        offset_x=float(pin_data.get("x", 0.0)),
                        offset_y=float(pin_data.get("y", 0.0)),
                        orientation=float(pin_data.get("orientation", 0.0)),
                        net=pins_by_component[reference].get(identifier),
                    )
                )

            try:
                # Measure the symbol body only. Including the reference and
                # value text would report a resistor as tens of millimetres
                # tall and blow the spacing out of proportion; the layout adds
                # its own margin for text instead.
                width, height = SymbolBoundingBoxCalculator.get_symbol_dimensions(
                    lib_data, include_properties=False
                )
            except Exception as error:  # pragma: no cover - defensive
                logger.debug("Bounding box for %s failed: %s", reference, error)
                width, height = 10.0, 10.0

            collected.append(
                ComponentInfo(
                    reference=reference,
                    lib_id=comp.lib_id,
                    pins=pins,
                    width=width,
                    height=height,
                )
            )
        return collected

    def _sheet_bottom(self) -> float:
        """Find the lowest edge of the sheet symbols already placed.

        Returns:
            The y coordinate below every child sheet symbol, or the top margin
            when the circuit has no child sheets.
        """
        bottom = LAYOUT_MARGIN_Y
        for child in self.circuit.child_instances or []:
            centre_y = child.get("y")
            height = child.get("sheet_height", child.get("height", 25.4))
            if centre_y is None:
                continue
            bottom = max(bottom, centre_y + height / 2)
        return bottom

    def _apply_wired_layout(self) -> Optional[LayoutPlan]:
        """Place this sheet's components and draw the wires between them.

        Overrides the positions chosen by the generic placement pass with a
        layout built from the circuit's connectivity, then emits the wires,
        junctions and power symbols that go with it.

        Returns:
            The layout plan, or None when the sheet has nothing to lay out.
        """
        components = self._collect_layout_components()
        if not components:
            return None

        circuit_nets = (
            self.circuit.nets.values()
            if isinstance(self.circuit.nets, dict)
            else self.circuit.nets
        )
        net_roles = {}
        power_symbols = {}
        for net in circuit_nets:
            net_roles[net.name] = self._net_role(net)
            if net_roles[net.name] is NetRole.POWER:
                power_symbols[net.name] = net.power_symbol

        origin_y = self._sheet_bottom()
        if self.circuit.child_instances:
            origin_y += LAYOUT_SHEET_GAP

        engine = WiredLayoutEngine(
            components=components,
            net_roles=net_roles,
            power_symbols=power_symbols,
            origin_y=origin_y,
        )
        plan = engine.build()

        for reference, placement in plan.placements.items():
            comp = self.component_manager.find_component(reference)
            if comp is None:
                continue
            comp.position = Point(placement.x, placement.y)
            comp.rotation = placement.rotation
            if placement.rotation in (90.0, 270.0):
                # A quarter-turned passive gets its reference and value stacked
                # to one side by the default rules, where they run into each
                # other. Put them above and below the body instead.
                self._laid_out_fields[reference] = (placement.x, placement.y)

        for start, end in plan.wires:
            self._add_wire(start, end)
        for junction in plan.junctions:
            self._add_junction(junction)

        power_counter = 1
        for lib_id, net_name, x, y, rotation in plan.power_symbols:
            # The engine reports the pin point; stand the symbol off it and
            # stagger it clear of any rail name already placed nearby.
            outward = (rotation + 90.0) % 360.0
            if "GND" in lib_id or "VSS" in lib_id:
                outward = (outward + 180.0) % 360.0
            position = self._staggered_power_position(
                (x, y), outward, self._power_positions
            )
            if position != (x, y):
                self._add_wire((x, y), position)
            self._add_power_symbol(
                lib_id=lib_id,
                reference=f"#PWR0{power_counter:02d}",
                value=net_name,
                position=position,
                rotation=rotation,
            )
            power_counter += 1

        for net_name, x, y, rotation in plan.node_labels:
            port = self._ports_by_net().get(net_name)
            if port is not None:
                self._add_label(
                    text=port.name,
                    position=(x, y),
                    rotation=rotation,
                    label_type=LabelType.HIERARCHICAL,
                    shape=port.direction.value,
                )
                self._ports_labelled.add(port.name)
            else:
                self._add_label(
                    text=net_name,
                    position=(x, y),
                    rotation=rotation,
                    label_type=LabelType.LOCAL,
                )

        logger.info(
            "Wired layout: %d part(s), %d wire segment(s), %d junction(s), "
            "%d power symbol(s), %d net(s) fully wired",
            len(plan.placements),
            len(plan.wires),
            len(plan.junctions),
            len(plan.power_symbols),
            len(plan.fully_wired_nets),
        )
        return plan

    def _pin_point_index(self) -> Dict[Tuple[float, float], Set[str]]:
        """Index every component pin point on this sheet by the nets on it.

        Returns:
            A mapping of rounded ``(x, y)`` point to the set of net names whose
            pins sit there.
        """
        index: Dict[Tuple[float, float], Set[str]] = defaultdict(set)
        circuit_nets = (
            self.circuit.nets.values()
            if isinstance(self.circuit.nets, dict)
            else self.circuit.nets
        )
        for net in circuit_nets:
            for comp_ref, pin_identifier in net.connections:
                comp = self.component_manager.find_component(comp_ref)
                if comp is None:
                    continue
                lib_data = SymbolLibCache.get_symbol_data(comp.lib_id)
                if not lib_data or "pins" not in lib_data:
                    continue
                pin_dict = find_pin_by_identifier(lib_data["pins"], pin_identifier)
                if not pin_dict:
                    continue
                dx, dy = rotate_offset(
                    float(pin_dict.get("x", 0.0)),
                    float(pin_dict.get("y", 0.0)),
                    comp.rotation,
                )
                point = (
                    round(comp.position.x + dx, 2),
                    round(comp.position.y + dy, 2),
                )
                index[point].add(net.name)
        return index

    @staticmethod
    def _staggered_power_position(
        pin: Tuple[float, float],
        angle: float,
        placed: List[Tuple[float, float]],
    ) -> Tuple[float, float]:
        """Choose where a power symbol sits so its rail name stays readable.

        Power pins are often grouped a tenth of an inch apart, which puts the
        rail names of neighbouring symbols on top of one another. Extending the
        stub for each successive symbol staggers them instead.

        Args:
            pin: The pin's connection point.
            angle: The outward direction for the symbol, in degrees.
            placed: Positions already used on this sheet. Appended to in place.

        Returns:
            The position for the power symbol.
        """
        for multiplier in range(1, 5):
            step_x, step_y = outward_step(angle, POWER_STUB * multiplier)
            candidate = (round(pin[0] + step_x, 2), round(pin[1] + step_y, 2))
            crowded = any(
                abs(candidate[0] - other[0]) < POWER_TEXT_CLEARANCE
                and abs(candidate[1] - other[1]) < POWER_TEXT_CLEARANCE
                for other in placed
            )
            if not crowded:
                placed.append(candidate)
                return candidate

        placed.append(pin)
        return pin

    @staticmethod
    def _segment_points(
        start: Tuple[float, float], end: Tuple[float, float]
    ) -> List[Tuple[float, float]]:
        """List the grid points an orthogonal wire segment passes through.

        Args:
            start: One end of the segment.
            end: The other end.

        Returns:
            The rounded points along the segment, both ends included.
        """
        points = []
        length = max(abs(end[0] - start[0]), abs(end[1] - start[1]))
        steps = max(1, int(round(length / GRID)))
        for index in range(steps + 1):
            ratio = index / steps
            points.append(
                (
                    round(start[0] + (end[0] - start[0]) * ratio, 2),
                    round(start[1] + (end[1] - start[1]) * ratio, 2),
                )
            )
        return points

    @staticmethod
    def _safe_stub(
        pin: Tuple[float, float],
        angle: float,
        net_name: str,
        pin_points: Dict[Tuple[float, float], Set[str]],
        claimed: Dict[Tuple[float, float], str],
    ) -> Tuple[float, float]:
        """Find how far a label can stand off its pin without touching anything.

        Args:
            pin: The pin's connection point.
            angle: The outward direction for the label, in degrees.
            net_name: The net the label names.
            pin_points: Every pin point on the sheet, by net.
            claimed: Stub endpoints already taken, by net. Updated in place.

        Returns:
            The point to put the label on. Equal to ``pin`` when no stub is
            safe, in which case the label sits on the pin as before.
        """
        for length in (LABEL_STUB, LABEL_STUB / 2):
            step_x, step_y = outward_step(angle, length)
            candidate = (round(pin[0] + step_x, 2), round(pin[1] + step_y, 2))

            # Walk the stub in grid steps. A pin belonging to another net
            # anywhere along it, not just at the far end, would be connected by
            # the wire passing over it.
            steps = max(1, int(round(length / GRID)))
            blocked = False
            for index in range(1, steps + 1):
                part_x, part_y = outward_step(angle, GRID * index)
                point = (round(pin[0] + part_x, 2), round(pin[1] + part_y, 2))
                owners = pin_points.get(point, set())
                if owners and owners != {net_name}:
                    blocked = True
                    break
                taken = claimed.get(point)
                if taken is not None and taken != net_name:
                    blocked = True
                    break
            if blocked:
                continue

            for index in range(1, steps + 1):
                part_x, part_y = outward_step(angle, GRID * index)
                claimed[(round(pin[0] + part_x, 2), round(pin[1] + part_y, 2))] = net_name
            return candidate

        logger.debug(
            "No clear stub for net '%s' at %s, labelling the pin directly",
            net_name,
            pin,
        )
        return pin

    def _add_junction(self, position: Tuple[float, float]) -> None:
        """Add a junction dot where three or more connections meet.

        Args:
            position: The (x, y) point in mm.
        """
        if not hasattr(self.schematic, "_data"):
            return
        self.schematic._data.setdefault("junctions", []).append(
            {
                "uuid": str(uuid_module.uuid4()),
                "position": {"x": position[0], "y": position[1]},
                "diameter": 0,
            }
        )

    def _uses_declared_ports(self) -> bool:
        """Report whether this sheet takes part in a declared-port hierarchy.

        True when this circuit declares ports, or when any of its children do.
        In that case every crossing of a sheet boundary is described by a port,
        so labels can be typed correctly instead of falling back to making
        everything hierarchical. Circuits that declare nothing keep the older
        net-name matching behaviour.

        Returns:
            True if declared ports govern this sheet's labels.
        """
        if self._declared_ports_in_use is None:
            in_use = bool(getattr(self.circuit, "ports", None))
            if not in_use:
                for child_info in self.circuit.child_instances or []:
                    child = self.all_subcircuits.get(child_info["sub_name"])
                    if getattr(child, "ports", None):
                        in_use = True
                        break
            self._declared_ports_in_use = in_use
        return self._declared_ports_in_use

    def _ports_by_net(self) -> Dict[str, Any]:
        """Index this circuit's declared hierarchical ports by the net they export.

        Returns:
            ``{net_name: Port}``. Empty when the circuit declares no interface.
            If two ports export the same net, the first declaration wins, since
            that is the name KiCad will use for the merged net.
        """
        by_net: Dict[str, Any] = {}
        for port in getattr(self.circuit, "ports", []) or []:
            by_net.setdefault(port.net_name, port)
        return by_net

    def _add_label(
        self,
        text: str,
        position: Tuple[float, float],
        rotation: float,
        label_type: LabelType,
        shape: Optional[str] = None,
    ) -> Label:
        """Add a local or hierarchical label to the schematic.

        Args:
            text: The label text, which is what determines connectivity.
            position: (x, y) anchor point in mm. For the label to connect, this
                must sit on a wire end, a pin or a sheet pin.
            rotation: Label rotation in degrees. 0 points right, 180 points left.
            label_type: ``LabelType.HIERARCHICAL`` or ``LabelType.LOCAL``.
            shape: Hierarchical label shape ("input", "output", "bidirectional",
                "tri_state" or "passive"). Ignored for local labels; defaults to
                "input" when omitted.

        Returns:
            The label that was added.
        """
        label = Label(
            uuid=str(uuid_module.uuid4()),
            position=Point(position[0], position[1]),
            text=text,
            label_type=label_type,
            rotation=float(rotation),
        )
        if shape is not None:
            label.shape = shape

        if not hasattr(self.schematic, "_data"):
            self.schematic.labels.append(label)
            return label

        if label.label_type == LabelType.HIERARCHICAL:
            from ..schematic.label_utils import calculate_hierarchical_label_justify

            self.schematic._data.setdefault("hierarchical_labels", []).append(
                {
                    "uuid": label.uuid,
                    "position": {"x": label.position.x, "y": label.position.y},
                    "text": label.text,
                    "rotation": label.rotation,
                    "size": label.size,
                    "shape": label.shape if label.shape else "input",
                    "justify": calculate_hierarchical_label_justify(label.rotation),
                }
            )
        else:
            self.schematic._data.setdefault("labels", []).append(
                {
                    "uuid": label.uuid,
                    "position": {"x": label.position.x, "y": label.position.y},
                    "text": label.text,
                    "label_type": (
                        label.label_type.value
                        if hasattr(label.label_type, "value")
                        else label.label_type
                    ),
                    "rotation": label.rotation,
                    "size": label.size,
                }
            )
        return label

    def _add_wire(
        self, start: Tuple[float, float], end: Tuple[float, float]
    ) -> None:
        """Add a two-point wire segment to the schematic.

        Args:
            start: (x, y) of the first end point in mm.
            end: (x, y) of the second end point in mm.
        """
        if not hasattr(self.schematic, "_data"):
            logger.debug("Schematic has no _data store, skipping wire")
            return

        self.schematic._data.setdefault("wires", []).append(
            {
                "uuid": str(uuid_module.uuid4()),
                "points": [
                    {"x": start[0], "y": start[1]},
                    {"x": end[0], "y": end[1]},
                ],
            }
        )

    def _add_power_symbol(
        self,
        lib_id: str,
        reference: str,
        value: str,
        position: Tuple[float, float],
        rotation: float = 0.0,
    ) -> Optional[str]:
        """
        Add a KiCad power symbol component.

        Args:
            lib_id: Power symbol library ID (e.g., "power:GND")
            reference: Power symbol reference (e.g., "#PWR01")
            value: Net name (e.g., "GND")
            position: (x, y) position to place symbol
            rotation: Rotation angle in degrees (default: 0.0)

        Returns:
            UUID of the created power symbol, or None if failed

        Example:
            >>> self._add_power_symbol("power:GND", "#PWR01", "GND", (100, 100), rotation=180)
        """
        logger.debug(
            f"Adding power symbol {lib_id} at {position} with value '{value}' rotation={rotation}"
        )

        try:
            # Add power symbol as a component
            # Power symbols must be placed exactly at pin positions, not snapped to grid
            power_comp = self.component_manager.add_component(
                library_id=lib_id,
                reference=reference,
                value=value,
                position=position,
                placement_strategy=PlacementStrategy.AUTO,
                footprint="",  # Power symbols have no footprint
                snap_to_grid=False,  # Power symbols need exact positioning at pin locations
            )

            if power_comp:
                # Set rotation after creation
                power_comp.rotation = rotation

                # Power symbols are always in BOM but not on board
                power_comp.in_bom = True
                power_comp.on_board = True
                power_comp.dnp = False

                # Fix Value property position - kicad-sch-api places it incorrectly
                # The Value should be positioned based on symbol rotation:
                # - 0° (up): Value above symbol
                # - 90° (left): Value to the left
                # - 180° (down): Value below symbol
                # - 270° (right): Value to the right
                # Standard offset is ~5.08mm from symbol center
                if (
                    hasattr(power_comp, "properties")
                    and "Value" in power_comp.properties
                ):
                    value_prop = power_comp.properties["Value"]
                    if hasattr(value_prop, "position"):
                        # Calculate correct position based on rotation
                        offset = (
                            5.08  # Standard KiCad offset for power symbol value text
                        )

                        if rotation == 0:  # Pointing up
                            value_prop.position = Point(
                                position[0], position[1] - offset
                            )
                        elif rotation == 90:  # Pointing left
                            value_prop.position = Point(
                                position[0] - offset, position[1]
                            )
                        elif rotation == 180:  # Pointing down
                            value_prop.position = Point(
                                position[0], position[1] + offset
                            )
                        elif rotation == 270:  # Pointing right
                            value_prop.position = Point(
                                position[0] + offset, position[1]
                            )

                logger.debug(
                    f"Created power symbol {reference} (UUID: {power_comp.uuid}) rotation={rotation}"
                )

                # Track power symbol for post-processing text positions
                if not hasattr(self, "_power_symbols_to_fix"):
                    self._power_symbols_to_fix = []
                self._power_symbols_to_fix.append(
                    {
                        "uuid": power_comp.uuid,
                        "position": position,
                        "rotation": rotation,
                        "value": value,
                        "lib_id": lib_id,  # Track symbol type for text positioning
                    }
                )

                return power_comp.uuid
            else:
                logger.warning(f"Failed to create power symbol {reference}")
                return None

        except Exception as e:
            logger.error(f"Error creating power symbol {reference}: {e}")
            return None

    def _fix_power_symbol_text_positions(self, sch_file_path: str):
        """
        Post-process schematic file to fix power symbol Value property positions.
        kicad-sch-api doesn't expose property positioning API, so we fix it in the file.
        """
        if not hasattr(self, "_power_symbols_to_fix") or not self._power_symbols_to_fix:
            # A sheet can still have rotated parts whose fields need moving,
            # even when it has no power symbols at all.
            self._fix_rotated_field_positions(sch_file_path)
            return

        logger.debug(
            f"Fixing Value positions for {len(self._power_symbols_to_fix)} power symbols..."
        )

        import re

        with open(sch_file_path, "r") as f:
            content = f.read()

        for symbol_info in self._power_symbols_to_fix:
            uuid = symbol_info["uuid"]
            pos = symbol_info["position"]
            rotation = symbol_info["rotation"]
            value = symbol_info["value"]
            lib_id = symbol_info.get("lib_id", "")

            # Calculate correct Value position based on rotation AND symbol type
            offset = 5.08  # Standard KiCad offset

            # GND-type symbols point DOWN by default, so invert the offset direction
            is_gnd_type = "GND" in lib_id or "VSS" in lib_id

            if rotation == 0:
                if is_gnd_type:
                    # GND at rotation 0 points DOWN, text goes below
                    value_x, value_y = pos[0], pos[1] + offset
                else:
                    # VCC at rotation 0 points UP, text goes above
                    value_x, value_y = pos[0], pos[1] - offset
            elif rotation == 90:
                if is_gnd_type:
                    # GND at rotation 90 points LEFT, text goes right (away from symbol)
                    value_x, value_y = pos[0] + offset, pos[1]
                else:
                    # VCC at rotation 90 points RIGHT, text goes left (away from symbol)
                    value_x, value_y = pos[0] - offset, pos[1]
            elif rotation == 180:
                if is_gnd_type:
                    # GND at rotation 180 points UP, text goes above
                    value_x, value_y = pos[0], pos[1] - offset
                else:
                    # VCC at rotation 180 points DOWN, text goes below
                    value_x, value_y = pos[0], pos[1] + offset
            elif rotation == 270:
                if is_gnd_type:
                    # GND at rotation 270 points RIGHT, text goes left (away from symbol)
                    value_x, value_y = pos[0] - offset, pos[1]
                else:
                    # VCC at rotation 270 points LEFT, text goes right (away from symbol)
                    value_x, value_y = pos[0] + offset, pos[1]
            else:
                continue  # Skip non-cardinal angles

            # Find this symbol's Value property and fix the position
            # Pattern: Find the symbol with this UUID, then find its Value property
            symbol_pattern = rf'(\(symbol.*?uuid "{uuid}".*?property "Value" "{re.escape(value)}".*?\(at )[\d.]+\s+[\d.]+(\s+[\d.]+\))'

            def replace_value_position(match):
                return f"{match.group(1)}{value_x} {value_y}{match.group(2)}"

            content = re.sub(
                symbol_pattern, replace_value_position, content, flags=re.DOTALL
            )

        # Write back
        with open(sch_file_path, "w") as f:
            f.write(content)

        logger.debug(f"Fixed Value positions in {sch_file_path}")
        self._power_symbols_to_fix = []  # Clear for next use

        self._fix_rotated_field_positions(sch_file_path)

    def _fix_rotated_field_positions(self, sch_file_path: str) -> None:
        """Stack the reference and value of quarter-turned parts vertically.

        The default rules place both fields to one side of a rotated symbol,
        where a reference such as "C11" and a value such as "1uF/25V" overlap.
        A horizontal part reads best with its reference above the body and its
        value below, which is what this rewrites them to.

        Args:
            sch_file_path: The schematic file to post-process.
        """
        if not self._laid_out_fields:
            return

        import re

        content = Path(sch_file_path).read_text(encoding="utf-8")
        for reference, (x, y) in self._laid_out_fields.items():
            escaped = re.escape(reference)
            content, changed = re.subn(
                rf'(\(property "Reference" "{escaped}"\s*\n\s*\(at )[\d.-]+ [\d.-]+ [\d.-]+(\))',
                rf"\g<1>{round(x, 4)} {round(y - FIELD_OFFSET, 4)} 0\g<2>",
                content,
                count=1,
            )
            if not changed:
                continue

            # The value sits in the same symbol block, right after the
            # reference, so anchor the search there.
            anchor = content.find(f'(property "Reference" "{reference}"')
            block = content[anchor : anchor + 2000]
            fixed = re.sub(
                r'(\(property "Value" "[^"]*"\s*\n\s*\(at )[\d.-]+ [\d.-]+ [\d.-]+(\))',
                rf"\g<1>{round(x, 4)} {round(y + FIELD_OFFSET, 4)} 0\g<2>",
                block,
                count=1,
            )
            content = content[:anchor] + fixed + content[anchor + 2000 :]

        Path(sch_file_path).write_text(content, encoding="utf-8")
        logger.debug(
            "Repositioned reference and value text for %d rotated part(s)",
            len(self._laid_out_fields),
        )

    def _add_pin_level_net_labels(self, layout_plan=None):
        """
        Add local net labels or power symbols at component pins for all nets.

        Args:
            layout_plan: The wired layout plan, when one was produced. Pins it
                already connected with a wire or a power symbol are skipped, so
                a wired net is not labelled a second time.

        For power nets (is_power=True):
            - Generate KiCad power symbol components
            - Use #PWR reference prefix
            - Creates global connection (not sheet-local)

        For regular nets:
            - Generate hierarchical labels (current behavior)
            - Sheet-local connection

        Returns:
            Dict[str, List[Label]]: Mapping of component reference to list of labels created for it.
                                   Example: {"U1": [Label("RUN"), Label("USB_DP"), ...], "C1": [...]}
        """
        logger.debug(f"Adding pin-level net labels for circuit '{self.circuit.name}'.")

        # Track which labels belong to which component
        component_labels = {}  # Dict[str, List[Label]]

        # Nets exported through a declared hierarchical port are labelled with
        # the port name rather than the net name, so the same block can be
        # instantiated more than once with different nets attached to it.
        ports_by_net = self._ports_by_net()
        wired_pins = layout_plan.wired_pins if layout_plan else set()
        fully_wired = layout_plan.fully_wired_nets if layout_plan else set()

        # Every pin point on this sheet, so a label stub can be checked against
        # them before it is drawn. A stub that lands on another net's pin would
        # short the two together.
        pin_points = self._pin_point_index()
        claimed_stubs: Dict[Tuple[float, float], str] = {}

        # The router's wires occupy points too, so a stub must not run into one.
        # They are claimed under a name no net can have, which keeps any stub
        # off them.
        if layout_plan:
            for start, end in layout_plan.wires:
                for point in self._segment_points(start, end):
                    claimed_stubs.setdefault(point, "\x00routed")

        # Counter for power symbol references (#PWR01, #PWR02, etc.)
        power_symbol_counter = 1

        # Get component lookup from the API
        # Handle both dict and list forms of .nets
        circuit_nets = (
            self.circuit.nets.values()
            if isinstance(self.circuit.nets, dict)
            else self.circuit.nets
        )

        for net in circuit_nets:
            net_name = net.name
            logger.debug(
                f"Processing net '{net_name}' with {len(net.connections)} connections"
            )

            if net_name in fully_wired:
                logger.debug(f"Net '{net_name}' is fully wired, no labels needed")
                continue

            for comp_ref, pin_identifier in net.connections:
                if (comp_ref, str(pin_identifier)) in wired_pins:
                    # A wire or a power symbol already reaches this pin.
                    continue

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

                logger.debug(f"INITIAL LABEL: {actual_ref} pin {pin_identifier}")
                logger.debug(f"  pin_dict: {pin_dict}")
                logger.debug(
                    f"  component position: ({comp.position.x}, {comp.position.y})"
                )
                logger.debug(f"  component rotation: {comp.rotation}°")

                # Rotate the pin offset into schematic space. This uses the
                # same helper as the layout engine, so a label and the wire
                # drawn for the same pin always land on the same point.
                rx, ry = rotate_offset(anchor_x, anchor_y, comp.rotation)

                global_x = comp.position.x + rx
                global_y = comp.position.y + ry

                # Calculate label angle (opposite to pin orientation for correct text direction)
                # Pin orientation indicates direction pin points FROM component
                # Label needs opposite angle to point toward connection (text reads correctly)
                label_angle = (pin_angle + 180) % 360
                global_angle = (label_angle + comp.rotation) % 360

                logger.debug(f"  → label position: ({global_x}, {global_y})")
                logger.debug(f"  → label angle: {global_angle}°")

                # Hold the label off the pin with a short stub. Sitting it on
                # the connection point draws the text across the symbol body.
                # The stub is only drawn where it provably reaches nothing that
                # belongs to another net.
                stub_x, stub_y = self._safe_stub(
                    (global_x, global_y),
                    global_angle,
                    net_name,
                    pin_points,
                    claimed_stubs,
                )
                draw_stub = (stub_x, stub_y) != (global_x, global_y)

                # Check if this is a power net. An explicitly declared port
                # wins over power symbol generation: the user asked for this
                # net to leave the sheet through the hierarchy.
                port = ports_by_net.get(net_name)
                if (
                    port is None
                    and hasattr(net, "is_power")
                    and net.is_power
                    and hasattr(net, "power_symbol")
                ):
                    # Generate power symbol instead of hierarchical label
                    power_ref = f"#PWR0{power_symbol_counter:02d}"
                    power_symbol_counter += 1

                    logger.debug(
                        f"Generating power symbol {power_ref} for net {net_name} "
                        f"at component {actual_ref}.{pin_identifier}"
                    )

                    # Stand the power symbol off the pin on a short stub so its
                    # graphic does not sit on top of the symbol body. Where a
                    # part has several power pins close together, the stubs are
                    # staggered so the rail names beside them stay readable.
                    power_x, power_y = self._staggered_power_position(
                        (global_x, global_y), global_angle, self._power_positions
                    )
                    if (power_x, power_y) != (global_x, global_y):
                        self._add_wire((global_x, global_y), (power_x, power_y))

                    # DEBUG: Log power symbol placement (uncomment for debugging)
                    # logger.debug(f"POWER SYMBOL: {power_ref} for {net_name} - "
                    #             f"placing at ({power_x}, {power_y}) from pin {actual_ref}.{pin_identifier}")

                    # Power symbols use hierarchical label rotation with -90° adjustment
                    # Different power symbols have different internal pin orientations:
                    # - VCC/positive: pin at 90° (UP) - use (global_angle - 90)
                    # - GND/negative: pin at 270° (DOWN) - need +180° to flip
                    base_rotation = (global_angle - 90) % 360

                    # Check if this is a GND-type symbol (inverted)
                    if "GND" in net.power_symbol or "VSS" in net.power_symbol:
                        # GND symbols are inverted, need 180° flip
                        power_rotation = float((base_rotation + 180) % 360)
                    else:
                        power_rotation = float(base_rotation)

                    # DEBUG: Log pin angle calculation (uncomment for debugging)
                    # logger.debug(f"POWER SYMBOL ROTATION: {net_name} on {actual_ref}.{pin_identifier}")
                    # logger.debug(f"   pin_angle={pin_angle}° comp.rotation={comp.rotation}°")
                    # logger.debug(f"   label_angle={(pin_angle + 180) % 360}° global_angle={global_angle}°")
                    # logger.debug(f"   → power_rotation={power_rotation}°")

                    # Add power symbol at offset position
                    self._add_power_symbol(
                        lib_id=net.power_symbol,
                        reference=power_ref,
                        value=net_name,
                        position=(power_x, power_y),
                        rotation=power_rotation,
                    )

                    # Power symbols don't create labels - skip the rest
                    continue

                if draw_stub:
                    self._add_wire((global_x, global_y), (stub_x, stub_y))

                if port is not None:
                    # This net leaves the sheet through a declared port. Label
                    # it with the port name and the port's direction, which is
                    # what the parent's sheet pin will be called.
                    label = self._add_label(
                        text=port.name,
                        position=(stub_x, stub_y),
                        rotation=float(global_angle),
                        label_type=LabelType.HIERARCHICAL,
                        shape=port.direction.value,
                    )
                    self._ports_labelled.add(port.name)
                else:
                    # Determine label type: hierarchical if shared with parent OR used by children
                    # Local labels are ONLY for nets that are purely internal to this sheet
                    is_hierarchical = self._is_net_hierarchical(net)
                    label = self._add_label(
                        text=net_name,
                        position=(stub_x, stub_y),
                        rotation=float(global_angle),
                        label_type=(
                            LabelType.HIERARCHICAL
                            if is_hierarchical
                            else LabelType.LOCAL
                        ),
                    )

                # Track that this label belongs to this component
                if actual_ref not in component_labels:
                    component_labels[actual_ref] = []
                component_labels[actual_ref].append(label)

                label_time = (time.perf_counter() - label_start) * 1000
                if PERF_DEBUG and label_time > 5:
                    log_net_label_creation(
                        net_name, actual_ref, str(pin_identifier), label_time
                    )
                logger.debug(
                    f"Added hierarchical label for net {net_name} at component {actual_ref}.{pin_identifier}"
                )

        return component_labels

    @staticmethod
    def _split_ports_by_side(ports: List[Any]) -> Tuple[List[Any], List[Any]]:
        """Assign hierarchical ports to the left or right edge of a sheet symbol.

        Inputs go on the left and everything else on the right, which is the
        usual reading order for a block diagram.

        Args:
            ports: The child circuit's declared ports, in declaration order.

        Returns:
            A ``(left_ports, right_ports)`` tuple.
        """
        left = [p for p in ports if p.direction == PortDirection.INPUT]
        right = [p for p in ports if p.direction != PortDirection.INPUT]
        return left, right

    @staticmethod
    def _size_sheet_for_ports(
        width: float, height: float, left_ports: List[Any], right_ports: List[Any]
    ) -> Tuple[float, float]:
        """Grow a sheet symbol so its port pins and pin names fit inside it.

        Args:
            width: Proposed sheet width in mm.
            height: Proposed sheet height in mm.
            left_ports: Ports placed on the left edge.
            right_ports: Ports placed on the right edge.

        Returns:
            The ``(width, height)`` to use, snapped up to the 1.27mm grid.
        """
        rows = max(len(left_ports), len(right_ports))
        needed_height = (2 * SHEET_PORT_MARGIN) + max(0, rows - 1) * SHEET_PORT_SPACING

        def text_width(ports: List[Any]) -> float:
            return max((len(p.name) for p in ports), default=0) * PIN_NAME_CHAR_WIDTH

        needed_width = (
            text_width(left_ports) + text_width(right_ports) + 3 * SHEET_PORT_MARGIN
        )

        width = math.ceil(max(width, needed_width) / GRID_SIZE) * GRID_SIZE
        height = math.ceil(max(height, needed_height) / GRID_SIZE) * GRID_SIZE
        return width, height

    def _add_sheet_port_pins(
        self,
        sheet,
        sheet_x: float,
        sheet_y: float,
        width: float,
        height: float,
        left_ports: List[Any],
        right_ports: List[Any],
    ) -> None:
        """Add typed sheet pins for a child block and connect them in this sheet.

        Each declared port of the child becomes a sheet pin on the child's sheet
        symbol, named after the port and carrying the port's direction. A short
        wire stub runs outward from every pin to a label naming the net this
        sheet connects to it. That label is hierarchical when the current
        circuit re-exports the net through one of its own ports, which is what
        makes blocks nest to any depth, and local otherwise.

        Args:
            sheet: The Sheet the pins are added to.
            sheet_x: Left edge of the sheet symbol in mm.
            sheet_y: Top edge of the sheet symbol in mm.
            width: Sheet symbol width in mm.
            height: Sheet symbol height in mm.
            left_ports: Ports to place on the left edge.
            right_ports: Ports to place on the right edge.
        """
        own_ports_by_net = self._ports_by_net()

        for ports, on_left in ((left_ports, True), (right_ports, False)):
            edge_x = sheet_x if on_left else sheet_x + width
            stub_x = edge_x - SHEET_PORT_STUB if on_left else edge_x + SHEET_PORT_STUB
            # KiCad derives which edge a sheet pin sits on from its angle when
            # the file is read back: 0 is the right edge and 180 the left one.
            # Getting this backwards makes KiCad move the pin to the opposite
            # edge, silently disconnecting it from the wire drawn for it.
            rotation = 180.0 if on_left else 0.0

            for index, port in enumerate(ports):
                pin_y = sheet_y + SHEET_PORT_MARGIN + (index * SHEET_PORT_SPACING)
                pin_y = round(pin_y / GRID_SIZE) * GRID_SIZE

                pin = SheetPin(
                    uuid=str(uuid_module.uuid4()),
                    name=port.name,
                    position=Point(edge_x, pin_y),
                    pin_type=port.direction.value,
                )
                # Left edge pins read into the sheet, right edge pins read out
                # of it, so their text runs in opposite directions.
                pin.rotation = rotation
                pin.justify = "left" if on_left else "right"
                sheet.pins.append(pin)

                # Stub wire so the label has somewhere to attach outside the
                # sheet outline, where it stays readable.
                self._add_wire((edge_x, pin_y), (stub_x, pin_y))

                own_port = own_ports_by_net.get(port.net_name)
                if own_port is not None:
                    self._add_label(
                        text=own_port.name,
                        position=(stub_x, pin_y),
                        rotation=180.0 if on_left else 0.0,
                        label_type=LabelType.HIERARCHICAL,
                        shape=own_port.direction.value,
                    )
                    self._ports_labelled.add(own_port.name)
                else:
                    self._add_label(
                        text=port.net_name,
                        position=(stub_x, pin_y),
                        rotation=180.0 if on_left else 0.0,
                        label_type=LabelType.LOCAL,
                    )

                logger.debug(
                    f"Sheet pin '{port.name}' ({port.direction.value}) at "
                    f"({edge_x}, {pin_y}) connects net '{port.net_name}'"
                )

    def _register_sheet(self, sheet) -> None:
        """Store a sheet symbol on the schematic being built.

        Args:
            sheet: The Sheet to add, with its pins already populated.
        """
        if not hasattr(self.schematic, "_data"):
            self.schematic.sheets.append(sheet)
            return

        self.schematic._data.setdefault("sheets", []).append(
            {
                "uuid": sheet.uuid,
                "position": {"x": sheet.position.x, "y": sheet.position.y},
                # The parser expects width/height rather than a Point.
                "size": {"width": sheet.size.x, "height": sheet.size.y},
                "name": sheet.name,
                "filename": sheet.filename,
                "pins": [
                    {
                        "uuid": pin.uuid,
                        "name": pin.name,
                        "position": {"x": pin.position.x, "y": pin.position.y},
                        "pin_type": (
                            pin.pin_type.value
                            if hasattr(pin.pin_type, "value")
                            else pin.pin_type
                        ),
                        "size": pin.size,
                        "rotation": getattr(pin, "rotation", 0),
                        "justify": getattr(pin, "justify", "right"),
                    }
                    for pin in sheet.pins
                ],
                "project_name": self.project_name or "",
                "page_number": "2",  # Default page number for sub-sheets
            }
        )

    def _add_port_based_sheet(
        self,
        child_info: Dict[str, Any],
        sub_name: str,
        usage_label: str,
        child_ports: List[Any],
    ) -> None:
        """Add a sheet symbol for a child block that declares hierarchical ports.

        Unlike the net-name heuristics used for undeclared blocks, the pin set
        here comes straight from the child's declared interface, so it is exact
        and stable across instances of the same block.

        Args:
            child_info: Placement record for this child instance.
            sub_name: Name of the child circuit, which is also its file name.
            usage_label: Sheet name shown in the parent schematic.
            child_ports: The child's declared ports, in declaration order.
        """
        left_ports, right_ports = self._split_ports_by_side(child_ports)

        cx = child_info.get("x", 50.0)
        cy = child_info.get("y", 50.0)
        width = child_info.get("sheet_width", child_info.get("width", 30.0))
        height = child_info.get("sheet_height", child_info.get("height", 30.0))
        width, height = self._size_sheet_for_ports(
            width, height, left_ports, right_ports
        )

        sheet_x = round((cx - (width / 2)) / GRID_SIZE) * GRID_SIZE
        sheet_y = round((cy - (height / 2)) / GRID_SIZE) * GRID_SIZE

        sheet = Sheet(
            uuid=str(uuid_module.uuid4()),
            position=Point(sheet_x, sheet_y),
            size=Point(width, height),
            name=usage_label,
            filename=f"{sub_name}.kicad_sch",
        )
        sheet._project_name = self.project_name

        self._add_sheet_port_pins(
            sheet, sheet_x, sheet_y, width, height, left_ports, right_ports
        )
        self._register_sheet(sheet)
        self.sheet_symbol_map[sub_name] = sheet.uuid

        logger.debug(
            f"Added hierarchical block sheet '{usage_label}' -> {sheet.filename} "
            f"with {len(sheet.pins)} declared port pin(s)"
        )

    def _add_unconnected_port_labels(self) -> None:
        """Emit hierarchical labels for declared ports that got no label.

        A port normally picks up its label from a component pin or from a child
        sheet pin. A port that connects to neither would silently disappear from
        the sheet, so a free-standing label is placed for it instead, keeping
        the block's interface complete.
        """
        labelled = getattr(self, "_ports_labelled", set())
        missing = [p for p in getattr(self.circuit, "ports", []) or [] if p.name not in labelled]
        if not missing:
            return

        logger.debug(
            f"Circuit '{self.circuit.name}': {len(missing)} declared port(s) have "
            f"no connection in this sheet, placing standalone labels"
        )
        for index, port in enumerate(missing):
            self._add_label(
                text=port.name,
                position=(
                    ORPHAN_PORT_X,
                    ORPHAN_PORT_Y + index * SHEET_PORT_SPACING,
                ),
                rotation=0.0,
                label_type=LabelType.HIERARCHICAL,
                shape=port.direction.value,
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
            child_ports = list(getattr(child_circ, "ports", []) or [])

            if child_ports:
                self._add_port_based_sheet(child_info, sub_name, usage_label, child_ports)
                continue

            # Get only SHARED nets for this subcircuit to create sheet pins
            # Check which child nets have the SAME OBJECT REFERENCE as parent nets
            # (not just matching names - must be the same Net object passed from parent to child)

            shared_net_names = []
            internal_net_names = []

            # Handle both dict and list forms of .nets
            child_nets = (
                child_circ.nets.values()
                if isinstance(child_circ.nets, dict)
                else child_circ.nets
            )
            parent_nets = (
                self.circuit.nets.values()
                if isinstance(self.circuit.nets, dict)
                else self.circuit.nets
            )

            # First try object identity (works when circuits are created directly in Python)
            for child_net in child_nets:
                is_shared = False
                for parent_net in parent_nets:
                    if parent_net is child_net:  # Same object reference!
                        is_shared = True
                        break

                if is_shared:
                    shared_net_names.append(child_net.name)
                else:
                    internal_net_names.append(child_net.name)

            # If object identity found no shared nets but we have nets to check, fall back to name matching
            # (needed when circuits are loaded from JSON, which creates new Net objects)
            if not shared_net_names and list(parent_nets) and list(child_nets):
                shared_net_names = []
                internal_net_names = []

                parent_net_names_set = {n.name for n in parent_nets}
                for child_net in child_nets:
                    if child_net.name in parent_net_names_set:
                        shared_net_names.append(child_net.name)
                    else:
                        internal_net_names.append(child_net.name)

            # Special case: If parent has NO nets, infer shared nets by looking at sibling circuits
            # Nets that appear in multiple children are likely shared parameters
            if not list(parent_nets) and list(child_nets):
                shared_net_names = []
                internal_net_names = []

                # Collect nets from all sibling circuits
                sibling_net_names = set()
                for sibling_info in self.circuit.child_instances:
                    if (
                        sibling_info["sub_name"] != sub_name
                    ):  # Don't include current child
                        sibling_circ = self.all_subcircuits[sibling_info["sub_name"]]
                        sibling_nets = (
                            sibling_circ.nets.values()
                            if isinstance(sibling_circ.nets, dict)
                            else sibling_circ.nets
                        )
                        sibling_net_names.update(n.name for n in sibling_nets)

                # Nets that appear in both this child AND siblings are likely shared
                for child_net in child_nets:
                    if child_net.name in sibling_net_names:
                        shared_net_names.append(child_net.name)
                    else:
                        internal_net_names.append(child_net.name)

            pin_list = sorted(shared_net_names)

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

            # Use pre-calculated position and size from placement
            # These were set by _place_components() text-flow algorithm
            cx = child_info.get("x", 50.0)
            cy = child_info.get("y", 50.0)
            width = child_info.get("sheet_width", child_info.get("width", 30.0))
            height = child_info.get("sheet_height", child_info.get("height", 30.0))

            # Calculate sheet position (upper-left corner) and snap to grid
            # KiCad uses 50mil (1.27mm) grid
            grid_size = 1.27
            sheet_x = round((cx - (width / 2)) / grid_size) * grid_size
            sheet_y = round((cy - (height / 2)) / grid_size) * grid_size

            # Create sheet using the API
            sheet = Sheet(
                uuid=str(uuid_module.uuid4()),
                position=Point(sheet_x, sheet_y),
                size=Point(width, height),  # size is a Point, not a tuple
                name=usage_label,
                filename=f"{sub_name}.kicad_sch",
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
                    uuid=str(uuid_module.uuid4()),
                    name=net_name,
                    position=Point(pin_x - 1.27, pin_y),
                    # pin_type defaults to BIDIRECTIONAL
                    # size defaults to 1.27
                )

                sheet.pins.append(sheet_pin)
                logger.debug(
                    f"Created sheet pin '{net_name}' at position ({pin_x}, {pin_y})"
                )

                own_port = self._ports_by_net().get(net_name)
                if own_port is not None:
                    self._add_label(
                        text=own_port.name,
                        position=(pin_x, pin_y),
                        rotation=0.0,
                        label_type=LabelType.HIERARCHICAL,
                        shape=own_port.direction.value,
                    )
                    self._ports_labelled.add(own_port.name)
                elif self._uses_declared_ports():
                    # This sheet is part of a declared-port hierarchy and does
                    # not export this net, so it stays local to the sheet.
                    self._add_label(
                        text=net_name,
                        position=(pin_x, pin_y),
                        rotation=0.0,
                        label_type=LabelType.LOCAL,
                    )
                else:
                    self._add_label(
                        text=net_name,
                        position=(pin_x, pin_y),
                        rotation=0.0,
                        label_type=LabelType.HIERARCHICAL,
                    )

            # Add sheet to schematic _data directly to bypass kicad-sch-api methods
            if not hasattr(self.schematic, "_data"):
                self.schematic.sheets.append(sheet)
            else:
                if "sheets" not in self.schematic._data:
                    self.schematic._data["sheets"] = []
                # Convert Sheet to dict for storage
                sheet_dict = {
                    "uuid": sheet.uuid,
                    "position": {"x": sheet.position.x, "y": sheet.position.y},
                    "size": {
                        "width": sheet.size.x,
                        "height": sheet.size.y,
                    },  # Parser expects width/height
                    "name": sheet.name,
                    "filename": sheet.filename,
                    "pins": [
                        {
                            "uuid": pin.uuid,
                            "name": pin.name,
                            "position": {"x": pin.position.x, "y": pin.position.y},
                            "pin_type": (
                                pin.pin_type.value
                                if hasattr(pin.pin_type, "value")
                                else pin.pin_type
                            ),
                            "size": pin.size,
                        }
                        for pin in sheet.pins
                    ],
                    "project_name": self.project_name
                    or "",  # Add project name for instances
                    "page_number": "2",  # Default page number for sub-sheets
                }
                self.schematic._data["sheets"].append(sheet_dict)

            # Draw bounding box around sheet if requested
            if self.draw_bounding_boxes:
                # Get bbox dimensions (includes label extensions)
                bbox_width = child_info.get("bbox_width", width + 20)
                bbox_height = child_info.get("bbox_height", height)

                # Calculate bbox corners from center position
                bbox_min_x = cx - (bbox_width / 2)
                bbox_min_y = cy - (bbox_height / 2)
                bbox_max_x = cx + (bbox_width / 2)
                bbox_max_y = cy + (bbox_height / 2)

                # TODO: Add Rectangle graphic for sheet bbox
                # Rectangle drawing not yet supported in kicad-sch-api
                # bbox_rect = Rectangle(
                #     top_left=Point(bbox_min_x, bbox_max_y),
                #     bottom_right=Point(bbox_max_x, bbox_min_y),
                # )

                logger.debug(
                    f"  Drew sheet bbox: ({bbox_min_x:.1f}, {bbox_min_y:.1f}) to "
                    f"({bbox_max_x:.1f}, {bbox_max_y:.1f})"
                )

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

    def _create_component_units(
        self, component_labels: Dict[str, List[Label]]
    ) -> List[ComponentUnit]:
        """
        Create ComponentUnit objects for all components.

        Each ComponentUnit bundles a component with its labels and bounding box.
        The bbox is calculated once based on the component's connected labels,
        then the unit can be moved as a whole without recalculating dimensions.

        Args:
            component_labels: Mapping of component reference to its labels

        Returns:
            List of ComponentUnit objects
        """
        from .symbol_geometry import SymbolBoundingBoxCalculator

        units = []
        logger.debug(
            f"Creating ComponentUnits for {len(self.schematic.components)} components"
        )

        for comp in self.schematic.components:
            comp_ref = comp.reference
            labels = component_labels.get(comp_ref, [])

            logger.debug(
                f"  Creating ComponentUnit for {comp_ref} with {len(labels)} labels"
            )

            # 1. Get base bbox (component body + pins + labels) in local coordinates
            lib_data = SymbolLibCache.get_symbol_data(comp.lib_id)
            if not lib_data:
                logger.warning(
                    f"No symbol data for {comp_ref} ({comp.lib_id}), skipping"
                )
                continue

            base_bbox = SymbolBoundingBoxCalculator.calculate_bounding_box(
                lib_data, include_properties=True
            )

            # 2. Convert base bbox to global coordinates
            local_min_x, local_min_y, local_max_x, local_max_y = base_bbox
            global_min_x = comp.position.x + local_min_x
            global_min_y = comp.position.y + local_min_y
            global_max_x = comp.position.x + local_max_x
            global_max_y = comp.position.y + local_max_y

            # 3. Extend bbox to include this component's labels
            LABEL_CHAR_WIDTH = 1.27  # mm per character
            LABEL_PADDING = 2.54  # vertical padding around label

            logger.debug(
                f"  Base bbox (global): min=({global_min_x:.1f}, {global_min_y:.1f}), max=({global_max_x:.1f}, {global_max_y:.1f})"
            )

            for label in labels:
                label_length = len(label.text) * LABEL_CHAR_WIDTH
                logger.debug(
                    f"    Label '{label.text}' at ({label.position.x:.1f}, {label.position.y:.1f}), rotation={label.rotation}°, length={label_length:.1f}mm"
                )

                # Extend bbox based on label rotation
                # Labels extend IN THE DIRECTION the pin points (not opposite)
                if label.rotation == 0:  # Right pin → label extends RIGHT
                    old_max_x = global_max_x
                    global_max_x = max(global_max_x, label.position.x + label_length)
                    global_min_y = min(global_min_y, label.position.y - LABEL_PADDING)
                    global_max_y = max(global_max_y, label.position.y + LABEL_PADDING)
                    logger.debug(
                        f"      0° (right pin): extended max_x from {old_max_x:.1f} to {global_max_x:.1f}"
                    )

                elif label.rotation == 90:  # Up pin → label extends UP
                    old_min_y = global_min_y
                    global_min_y = min(global_min_y, label.position.y - label_length)
                    global_min_x = min(global_min_x, label.position.x - LABEL_PADDING)
                    global_max_x = max(global_max_x, label.position.x + LABEL_PADDING)
                    logger.debug(
                        f"      90° (up pin): extended min_y from {old_min_y:.1f} to {global_min_y:.1f}"
                    )

                elif label.rotation == 180:  # Left pin → label extends LEFT
                    old_min_x = global_min_x
                    global_min_x = min(global_min_x, label.position.x - label_length)
                    global_min_y = min(global_min_y, label.position.y - LABEL_PADDING)
                    global_max_y = max(global_max_y, label.position.y + LABEL_PADDING)
                    logger.debug(
                        f"      180° (left pin): extended min_x from {old_min_x:.1f} to {global_min_x:.1f}"
                    )

                elif label.rotation == 270:  # Down pin → label extends DOWN
                    old_max_y = global_max_y
                    global_max_y = max(global_max_y, label.position.y + label_length)
                    global_min_x = min(global_min_x, label.position.x - LABEL_PADDING)
                    global_max_x = max(global_max_x, label.position.x + LABEL_PADDING)
                    logger.debug(
                        f"      270° (down pin): extended max_y from {old_max_y:.1f} to {global_max_y:.1f}"
                    )

            # 4. Create ComponentUnit
            unit = ComponentUnit(
                component=comp,
                labels=labels,
                bbox_min_x=global_min_x,
                bbox_min_y=global_min_y,
                bbox_max_x=global_max_x,
                bbox_max_y=global_max_y,
                bbox_graphic=None,  # Will be created later if draw_bounding_boxes=True
            )

            units.append(unit)
            logger.debug(
                f"  Final bbox (global): min=({global_min_x:.1f}, {global_min_y:.1f}), max=({global_max_x:.1f}, {global_max_y:.1f})"
            )
            logger.debug(
                f"  Created ComponentUnit: {comp_ref} bbox={unit.width:.1f}×{unit.height:.1f}mm"
            )

        logger.info(f"Created {len(units)} ComponentUnits")
        return units

    def _draw_component_unit_bboxes(self, units: List[ComponentUnit]) -> None:
        """
        Draw bounding box rectangles for ComponentUnits.

        Creates a Rectangle graphic for each unit's bbox and adds it to the schematic.
        Much simpler than the old proximity-based approach - we already know the exact bbox!

        Args:
            units: List of ComponentUnit objects with calculated bboxes
        """
        logger.debug(f"Drawing bounding boxes for {len(units)} ComponentUnits")

        for unit in units:
            # TODO: Create Rectangle graphic from bbox coordinates
            # Rectangle drawing not yet supported in kicad-sch-api
            # bbox_rect = Rectangle(
            #     top_left=Point(unit.bbox_min_x, unit.bbox_max_y),
            #     bottom_right=Point(unit.bbox_max_x, unit.bbox_min_y),
            # )
            # unit.bbox_graphic = bbox_rect
            pass

            logger.debug(
                f"  Drew bbox for {unit.reference}: "
                f"({unit.bbox_min_x:.1f}, {unit.bbox_min_y:.1f}) to "
                f"({unit.bbox_max_x:.1f}, {unit.bbox_max_y:.1f})"
            )

        logger.info(f"Drew {len(units)} bounding box rectangles")

    def _add_component_bounding_boxes(self):
        """Add bounding box rectangles using KiCad API."""
        logger.debug(
            f"Adding bounding boxes for {len(self.schematic.components)} components"
        )

        # Check if labels are available
        import sys

        print(
            f"\n🔍 BBOX: Checking for labels in schematic", file=sys.stderr, flush=True
        )
        if hasattr(self.schematic, "labels"):
            print(
                f"🔍 BBOX: ✅ Has labels, count: {len(self.schematic.labels)}",
                file=sys.stderr,
                flush=True,
            )
            for i, label in enumerate(self.schematic.labels[:10]):
                print(f"🔍 BBOX:   Label[{i}]: {label}", file=sys.stderr, flush=True)
        else:
            print(f"🔍 BBOX: ❌ No labels attribute", file=sys.stderr, flush=True)

        # Use schematic components (with updated positions) instead of circuit components
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

                # Calculate component bbox including pin labels for accurate collision detection
                print(
                    f"\n🔍 BBOX: Calculating bbox for {comp.reference} at ({comp.position.x:.3f}, {comp.position.y:.3f})",
                    file=sys.stderr,
                    flush=True,
                )

                min_x, min_y, max_x, max_y = (
                    SymbolBoundingBoxCalculator.calculate_bounding_box(
                        lib_data, include_properties=True
                    )
                )

                print(
                    f"🔍 BBOX: Base component bbox: ({min_x:.2f}, {min_y:.2f}) to ({max_x:.2f}, {max_y:.2f})",
                    file=sys.stderr,
                    flush=True,
                )

                # Extend bbox to include all nearby hierarchical labels
                LABEL_CHAR_WIDTH = (
                    1.27  # mm per character (matches KiCad default font size)
                )
                LABEL_PROXIMITY = (
                    30.0  # Fixed proximity radius for detecting nearby labels
                )

                for label in self.schematic.labels:
                    if label.label_type.value != "hierarchical_label":
                        continue

                    # Calculate distance to component
                    dx = abs(label.position.x - comp.position.x)
                    dy = abs(label.position.y - comp.position.y)
                    dist = (dx**2 + dy**2) ** 0.5

                    if dist < LABEL_PROXIMITY:
                        # Calculate label dimensions
                        label_length = len(label.text) * LABEL_CHAR_WIDTH

                        # Extend bbox based on label rotation
                        label_rel_x = label.position.x - comp.position.x
                        label_rel_y = label.position.y - comp.position.y

                        # Horizontal label (0° or 180°)
                        if label.rotation in [0, 180]:
                            if label.rotation == 180:  # Label extends to the left
                                min_x = min(min_x, label_rel_x - label_length)
                            else:  # Label extends to the right
                                max_x = max(max_x, label_rel_x + label_length)
                            # Add small vertical padding
                            min_y = min(min_y, label_rel_y - 2.54)
                            max_y = max(max_y, label_rel_y + 2.54)
                        # Vertical label (90° or 270°)
                        else:
                            if label.rotation == 270:  # Label extends down (positive Y)
                                max_y = max(max_y, label_rel_y + label_length)
                            else:  # Label extends up (90°, negative Y)
                                min_y = min(min_y, label_rel_y - label_length)
                            # Add small horizontal padding
                            min_x = min(min_x, label_rel_x - 2.54)
                            max_x = max(max_x, label_rel_x + 2.54)

                        print(
                            f"🔍 BBOX:   Label '{label.text}' ({len(label.text)} chars, {label.rotation}°) at rel ({label_rel_x:.2f}, {label_rel_y:.2f})",
                            file=sys.stderr,
                            flush=True,
                        )

                print(
                    f"🔍 BBOX: Final bbox with labels: ({min_x:.2f}, {min_y:.2f}) to ({max_x:.2f}, {max_y:.2f})",
                    file=sys.stderr,
                    flush=True,
                )

                # TODO: Create Rectangle using API types
                # Rectangle drawing not yet supported in kicad-sch-api
                # bbox_rect = Rectangle(
                #     top_left=Point(comp.position.x + min_x, comp.position.y + max_y),
                #     bottom_right=Point(comp.position.x + max_x, comp.position.y + min_y),
                # )
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
                elif annotation_type == "Image":
                    self._add_image_annotation(annotation)
                else:
                    logger.warning(f"Unknown annotation type: {annotation_type}")

            except Exception as e:
                logger.error(f"Failed to add annotation {annotation}: {e}")

    def _add_textbox_annotation(self, textbox):
        """Add a TextBox annotation as a KiCad text_box element."""
        from kicad_sch_api.core.types import Text

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

        # Use add_text_box() method from kicad-sch-api
        import uuid as uuid_module

        # Don't escape here - kicad-sch-api should handle escaping during save
        # Passing raw text so it can be properly escaped when writing S-expressions

        textbox_uuid = self.schematic.add_text_box(
            text=text,
            position=Point(position[0], position[1]),
            size=Point(size[0], size[1]),
            rotation=rotation,
            font_size=text_size,
            margins=margins,
            exclude_from_sim=False,
        )

        logger.debug(f"Added TextBox annotation: '{text}' at {position}")

    def _add_text_annotation(self, text_prop):
        """Add a TextProperty annotation as a simple KiCad text element."""
        from kicad_sch_api.core.types import Text

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

        # Use add_text() method from kicad-sch-api with correct parameters
        text_uuid = self.schematic.add_text(
            text=text,
            position=Point(position[0], position[1]),
            rotation=rotation,
            size=size,
            exclude_from_sim=False,
        )

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

                    from kicad_sch_api.core.types import Text

                    text_element = Text(
                        uuid=f"{uuid}_{row_idx}_{col_idx}",
                        position=Point(cell_x, cell_y),
                        text=str(cell_text),
                        rotation=0.0,
                        size=text_size,
                        exclude_from_sim=False,
                    )

                    self.schematic.add_text(text_element)

    def _add_image_annotation(self, image):
        """Add an Image annotation as an embedded image in the schematic."""
        import base64
        from pathlib import Path

        # Handle both dictionary data and object data
        if isinstance(image, dict):
            image_path = image.get("image_path", "")
            position = image.get("position", (100.0, 100.0))
            scale = image.get("scale", 1.0)
            uuid = image.get("uuid", "")
        else:
            image_path = image.image_path
            position = image.position
            scale = image.scale
            uuid = image.uuid

        # Ensure position is a tuple (not a list) for kicad-sch-api
        # This can happen if the annotation was serialized/deserialized through JSON
        if isinstance(position, list):
            position = tuple(position)

        # Read and encode the image file
        try:
            image_file = Path(image_path)
            if not image_file.exists():
                logger.error(f"Image file not found: {image_path}")
                return

            # Validate file size (max 10MB to prevent bloating schematics)
            MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
            file_size = image_file.stat().st_size
            if file_size > MAX_IMAGE_SIZE:
                logger.error(
                    f"Image file too large: {file_size / (1024*1024):.2f}MB "
                    f"(max {MAX_IMAGE_SIZE / (1024*1024):.0f}MB). "
                    f"File: {image_path}"
                )
                return

            # Validate file type by checking magic bytes
            with open(image_file, "rb") as f:
                header = f.read(8)

                # Check for common image formats by magic bytes
                is_valid_image = False
                image_type = "unknown"

                if header.startswith(b"\x89PNG\r\n\x1a\n"):
                    is_valid_image = True
                    image_type = "PNG"
                elif header.startswith(b"\xff\xd8\xff"):
                    is_valid_image = True
                    image_type = "JPEG"
                elif header.startswith(b"GIF87a") or header.startswith(b"GIF89a"):
                    is_valid_image = True
                    image_type = "GIF"
                elif header.startswith(b"BM"):
                    is_valid_image = True
                    image_type = "BMP"
                elif header.startswith(b"RIFF") and header[8:12] == b"WEBP":
                    is_valid_image = True
                    image_type = "WEBP"

                if not is_valid_image:
                    logger.error(
                        f"Invalid or unsupported image file format. "
                        f"Supported formats: PNG, JPEG, GIF, BMP, WEBP. "
                        f"File: {image_path}"
                    )
                    return

                logger.debug(
                    f"Validated {image_type} image: {image_path} ({file_size / 1024:.1f}KB)"
                )

                # Read full file for encoding
                f.seek(0)
                image_data = base64.b64encode(f.read()).decode("utf-8")

            # Add image using kicad-sch-api
            image_uuid = self.schematic.add_image(
                position=position, data=image_data, scale=scale
            )

            logger.debug(
                f"Added Image annotation: '{image_path}' at {position} with scale {scale}"
            )

        except Exception as e:
            logger.error(f"Failed to add image annotation from {image_path}: {e}")

    def _add_paper_size(self, schematic_expr: list):
        """Add paper size to the schematic expression."""
        # Find the right place to insert paper size
        for i, item in enumerate(schematic_expr):
            if isinstance(item, list) and item and item[0] == Symbol("uuid"):
                # Insert paper after uuid
                schematic_expr.insert(i + 1, [Symbol("paper"), self.paper_size])
                break

    def _populate_lib_symbols(self):
        """Populate lib_symbols dict in the Schematic object."""
        # For now, just use an empty dict
        # The kicad-sch-api will handle symbol definitions automatically
        self.schematic.lib_symbols = {}
        logger.debug("Populated lib_symbols (kicad-sch-api handles definitions)")

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
        # Use schematic UUID for proper reference assignment
        path = (
            f"/{self.schematic.uuid}"
            if hasattr(self.schematic, "uuid") and self.schematic.uuid
            else "/"
        )
        sheet_instances = [
            Symbol("sheet_instances"),
            [Symbol("path"), path, [Symbol("page"), "1"]],
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


def write_schematic_file(schematic, out_path: str):
    """
    Save a kicad-sch-api Schematic object to a .kicad_sch file.

    Args:
        schematic: kicad-sch-api Schematic object
        out_path: Path to write the schematic file
    """
    from pathlib import Path

    logger.info(f"Writing schematic to {out_path}")

    try:
        # QUICK FIX: Hide all properties except Reference and Value
        # (We'll remove these properties entirely later)
        logger.debug("Hiding non-essential properties (all except Reference and Value)")
        for component in schematic.components:
            # Access the raw component data
            if hasattr(component, '_data'):
                comp_data = component._data
            else:
                comp_data = component

            # Mark all properties except Reference and Value as hidden
            if hasattr(comp_data, 'hidden_properties'):
                for prop_name in list(component.properties.keys()):
                    if prop_name not in ("Reference", "Value"):
                        comp_data.hidden_properties.add(prop_name)

        # Sync ComponentCollection to _data before writing
        if hasattr(schematic, "_sync_components_to_data"):
            logger.debug(
                f"Syncing {len(schematic._components)} components to _data before writing"
            )
            schematic._sync_components_to_data()

        file_path = Path(out_path)

        # Convert data to S-expression using kicad-sch-api's parser
        sexp_data = schematic._parser._schematic_data_to_sexp(schematic._data)

        # Format using kicad-sch-api's formatter
        content = schematic._formatter.format(sexp_data)

        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write to file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"✅ Successfully wrote schematic to {out_path}")
    except Exception as e:
        logger.error(f"❌ Failed to write schematic: {e}")
        raise
