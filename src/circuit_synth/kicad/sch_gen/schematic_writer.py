# -*- coding: utf-8 -*-
#
# schematic_writer.py
#
# KiCad API Phase 2 Integration - Direct usage of KiCad API
# This version replaces custom placement and reference management with the KiCad API
#
# Writes a .kicad_sch file from in-memory circuit data using the new KiCad API
#

import datetime
import logging
import math
import os
import time
import uuid as uuid_module
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Configure logging for this module
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

from sexpdata import Symbol, dumps

from circuit_synth.kicad_api.core.s_expression import SExpressionParser

# Add performance timing
try:
    from ...core.performance_profiler import quick_time
except ImportError:
    # Fallback if profiler not available
    def quick_time(name):
        def decorator(func):
            return func

        return decorator


# Use optimized symbol cache from core.component for better performance,
# but keep Python fallback for graphics data
from circuit_synth.core.component import SymbolLibCache

# Import Python symbol cache specifically for graphics data
from circuit_synth.kicad.kicad_symbol_cache import (
    SymbolLibCache as PythonSymbolLibCache,
)

# Import from KiCad API
from circuit_synth.kicad_api.core.types import (
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
from circuit_synth.kicad_api.schematic.component_manager import ComponentManager
from circuit_synth.kicad_api.schematic.placement import (
    PlacementEngine,
    PlacementStrategy,
)

from .collision_manager import SHEET_MARGIN

# Import existing dependencies
from .data_structures import Circuit
from .integrated_reference_manager import IntegratedReferenceManager
from .kicad_formatter import format_kicad_schematic
from .shape_drawer import arc_s_expr, circle_s_expr, polyline_s_expr, rectangle_s_expr

# Import automatic Rust acceleration
try:
    from circuit_synth.core.rust_integration import (
        generate_component_sexp,
        get_acceleration_status,
    )

    _rust_status = get_acceleration_status()
    _RUST_COMPONENT_ACCELERATION = _rust_status["rust_available"]

    if _RUST_COMPONENT_ACCELERATION:
        logging.getLogger(__name__).info(
            f"Rust component acceleration enabled for SchematicWriter"
        )
        logging.getLogger(__name__).info(
            "RUST_COMPONENT_ACCELERATION: Expected 6x component generation speedup"
        )
    else:
        logging.getLogger(__name__).info(
            f"RUST_COMPONENT_ACCELERATION: Using Python fallback"
        )
except ImportError as e:
    _RUST_COMPONENT_ACCELERATION = False
    logging.getLogger(__name__).info(
        f"RUST_COMPONENT_ACCELERATION: Not available ({e}), using Python implementation"
    )
except Exception as e:
    _RUST_COMPONENT_ACCELERATION = False
    logging.getLogger(__name__).warning(
        f"RUST_COMPONENT_ACCELERATION: Error loading: {e}"
    )

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
    ):
        """
        :param circuit: The Circuit object (subcircuit or top-level) to be written.
        :param circuit_dict: Dict of all subcircuits keyed by subcircuit name -> Circuit
        :param instance_naming_map: For advanced usage (unused here).
        :param paper_size: Paper size to use for the schematic (e.g., "A4", "A3")
        :param project_name: The actual KiCad project name (for instances block)
        :param hierarchical_path: List of UUIDs representing the full path from root
        :param reference_manager: Optional shared reference manager for global uniqueness
        """
        self.circuit = circuit
        self.all_subcircuits = circuit_dict
        self.instance_naming_map = instance_naming_map
        self.uuid_top = str(uuid_module.uuid4())
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
            logger.debug(f"  - Created new reference manager")

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

        PERFORMANCE MONITORING: Times each major operation and reports Rust acceleration status.
        """
        start_time = time.perf_counter()
        # Schematic generation details removed for clean output

        # Add components using the new API - time this critical operation
        comp_start = time.perf_counter()
        # Step logging removed for performance
        self._add_components()
        comp_time = time.perf_counter() - comp_start
        # Timing details removed for performance

        # Place components using the placement engine
        place_start = time.perf_counter()
        # Step logging removed for performance
        self._place_components()
        place_time = time.perf_counter() - place_start
        # Timing details removed for performance

        # Add pin-level net labels
        labels_start = time.perf_counter()
        # Step logging removed for performance
        self._add_pin_level_net_labels()
        labels_time = time.perf_counter() - labels_start
        # Timing details removed for performance

        # Add subcircuit sheets if needed
        sheets_start = time.perf_counter()
        subcircuit_count = (
            len(self.circuit.child_instances) if self.circuit.child_instances else 0
        )
        # Step logging removed for performance
        self._add_subcircuit_sheets()
        sheets_time = time.perf_counter() - sheets_start
        # Timing details removed for performance

        # Add bounding boxes if enabled
        bbox_start = time.perf_counter()
        if self.draw_bounding_boxes:
            # Step logging removed for performance
            self._add_component_bounding_boxes()
            bbox_time = time.perf_counter() - bbox_start
            # Timing details removed for performance
        else:
            logger.debug("Bounding boxes disabled, skipping")
            bbox_time = 0

        # Add text annotations (TextBox, TextProperty, etc.)
        self._add_annotations()

        # Convert to S-expression format using the parser - CRITICAL RUST ACCELERATION POINT
        sexpr_start = time.perf_counter()
        # Step logging removed for performance
        schematic_sexpr = self.parser.from_schematic(self.schematic)
        sexpr_time = time.perf_counter() - sexpr_start
        # Timing details removed for performance

        # Add additional sections
        sections_start = time.perf_counter()
        # Step logging removed for performance

        # Add paper size (not in the API types yet)
        paper_start = time.perf_counter()
        self._add_paper_size(schematic_sexpr)
        paper_time = time.perf_counter() - paper_start

        # Add lib_symbols section
        libsym_start = time.perf_counter()
        self._add_symbol_definitions(schematic_sexpr)
        libsym_time = time.perf_counter() - libsym_start

        # Add sheet_instances section
        sheetinst_start = time.perf_counter()
        self._add_sheet_instances(schematic_sexpr)
        sheetinst_time = time.perf_counter() - sheetinst_start

        sections_time = time.perf_counter() - sections_start
        # Timing details removed for performance

        # Add symbol_instances section - DISABLED for new KiCad format (20250114+)
        # The new format uses instances within each symbol instead
        # self._add_symbol_instances_table(schematic_sexpr)

        total_time = time.perf_counter() - start_time
        expr_size = len(str(schematic_sexpr)) if schematic_sexpr else 0

        # Generation completion details removed for clean output

        # Performance breakdown removed for clean output
        logger.debug(
            f"  S-expression: {sexpr_time*1000:.2f}ms ({sexpr_time/total_time*100:.1f}%)"
        )
        logger.debug(
            f"  Sections: {sections_time*1000:.2f}ms ({sections_time/total_time*100:.1f}%)"
        )

        if _RUST_COMPONENT_ACCELERATION:
            estimated_rust_total = total_time / 6.0  # Expected 6x improvement
            logger.debug(
                f"RUST_PROJECTION: Estimated total time with full Rust: {estimated_rust_total*1000:.2f}ms"
            )
            logger.debug(
                f"RUST_PROJECTION: Potential time saved: {(total_time - estimated_rust_total)*1000:.2f}ms"
            )

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
                    # Root sheet - just "/"
                    instance_path = "/"
                    logger.debug(f"  Creating ROOT SHEET instance with path: /")

                # Create the instance
                instance = SymbolInstance(
                    project=self.project_name,
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
        Use the PlacementEngine to arrange components with Rust acceleration when available.

        PERFORMANCE OPTIMIZATION: Attempts Rust force-directed placement for 40-60% speedup.
        """
        if not self.schematic.components:
            logger.debug("No components to place")
            return

        start_time = time.perf_counter()
        logger.debug(
            f"PLACE_COMPONENTS: Starting placement of {len(self.schematic.components)} components"
        )
        logger.debug(
            f"Component placement acceleration available: {_RUST_COMPONENT_ACCELERATION}"
        )

        # Check if components need repositioning (have default positions)
        components_needing_placement = []
        for comp in self.schematic.components:
            # If component is at origin or has no meaningful position, it needs placement
            if (
                comp.position.x <= 25.4 and comp.position.y <= 25.4
            ):  # Within 1 inch of origin
                components_needing_placement.append(comp)

        if not components_needing_placement:
            logger.debug(
                "All components already have valid positions, skipping placement"
            )
            return

        logger.debug(
            f"PLACE_COMPONENTS: {len(components_needing_placement)} components need placement"
        )

        # Use the PlacementEngine with Rust acceleration
        try:
            placement_start = time.perf_counter()

            # Try Rust force-directed placement first for optimal results
            if (
                len(components_needing_placement) >= 3
            ):  # Force-directed works best with multiple components
                logger.debug(
                    "Using force-directed placement for optimal component arrangement"
                )
                self.placement_engine.arrange_components(
                    components_needing_placement,
                    arrangement="force_directed",
                    use_rust_acceleration=True,
                )
            else:
                # For few components, use grid placement
                logger.debug(
                    "PLACE_COMPONENTS: Using grid placement for few components"
                )
                self.placement_engine.arrange_components(
                    components_needing_placement, arrangement="grid"
                )

            placement_time = time.perf_counter() - placement_start
            logger.debug(
                f"Component placement completed in {placement_time*1000:.2f}ms"
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
            logger.warning("Using fallback grid placement")

            # Fallback to simple grid placement
            try:
                self.placement_engine._arrange_grid(components_needing_placement)
                logger.debug("Fallback grid placement completed")
            except Exception as fallback_error:
                logger.error(
                    f"❌ PLACE_COMPONENTS: Even fallback placement failed: {fallback_error}"
                )
                # Leave components at their current positions

        total_time = time.perf_counter() - start_time
        logger.debug(f"Component placement complete in {total_time*1000:.2f}ms")

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
                # Don't use reference mapping here - net connections have already been updated
                actual_ref = comp_ref

                # Find component using the API
                comp = self.component_manager.find_component(actual_ref)

                if not comp:
                    logger.debug(f"Component {actual_ref} not found for net {net_name}")
                    continue

                # Get pin position from library data
                lib_data = SymbolLibCache.get_symbol_data(comp.lib_id)
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
            pin_list = sorted([n.name for n in child_circ.nets])

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
        from circuit_synth.kicad_api.core.types import Text

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
        from circuit_synth.kicad_api.core.types import Text

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

                    from circuit_synth.kicad_api.core.types import Text

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
                break

        if not lib_symbols_block:
            lib_symbols_block = [Symbol("lib_symbols")]
            # Insert after paper
            for i, item in enumerate(schematic_expr):
                if isinstance(item, list) and item and item[0] == Symbol("paper"):
                    schematic_expr.insert(i + 1, lib_symbols_block)
                    break

        # Clear any existing symbols in the lib_symbols block
        # Keep only the first element which is the Symbol("lib_symbols")
        if lib_symbols_block and len(lib_symbols_block) > 1:
            lib_symbols_block[:] = [lib_symbols_block[0]]

        # Gather all lib_ids
        symbol_ids = set()
        for comp in self.schematic.components:
            symbol_ids.add(comp.lib_id)

        for sym_id in sorted(symbol_ids):
            lib_data = SymbolLibCache.get_symbol_data(sym_id)
            if not lib_data:
                logger.warning(
                    "No symbol library data found for '%s'. Skipping definition.",
                    sym_id,
                )
                continue

            # Check if graphics data is missing from Rust cache - if so, use Python fallback
            if "graphics" not in lib_data or not lib_data["graphics"]:
                logger.info(
                    f"Graphics data missing for {sym_id}, using Python fallback"
                )
                try:
                    python_lib_data = PythonSymbolLibCache.get_symbol_data(sym_id)
                    if python_lib_data and "graphics" in python_lib_data:
                        # Merge graphics data from Python cache into Rust cache data
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
                lib_symbols_block.append(lib_data)
            else:
                # Build from JSON-based library data
                new_sym_def = self._create_symbol_definition(sym_id, lib_data)
                if new_sym_def:
                    if isinstance(new_sym_def[0], Symbol):
                        lib_symbols_block.append(new_sym_def)
                    else:
                        lib_symbols_block.extend(new_sym_def)

    def _create_symbol_definition(self, lib_id: str, lib_data: dict):
        """
        Build a full KiCad (symbol ...) block from the library JSON data.
        """
        base_name = lib_id.split(":")[-1]

        symbol_block = [
            Symbol("symbol"),
            lib_id,
            [Symbol("pin_numbers"), Symbol("hide")],
            [Symbol("pin_names"), [Symbol("offset"), 0.254]],
            [Symbol("exclude_from_sim"), Symbol("no")],
            [Symbol("in_bom"), Symbol("yes")],
            [Symbol("on_board"), Symbol("yes")],
        ]

        # Properties
        props = lib_data.get("properties", {})
        for prop_name, prop_value in props.items():
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
                    str(prop_value),
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
        """Add sheet_instances section."""
        sheet_instances = [
            Symbol("sheet_instances"),
            [Symbol("path"), "/", [Symbol("page"), "1"]],
        ]

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

    PERFORMANCE OPTIMIZATION: Uses Rust-accelerated formatting when available.
    This is the final step where the Rust S-expression formatter provides maximum benefit.
    """
    start_time = time.perf_counter()
    expr_size = len(str(schematic_expr)) if schematic_expr else 0

    logger.debug(f"Starting file write to {out_path}")
    logger.debug(f"Input S-expression size: {expr_size:,} characters")
    logger.debug(f"Rust formatting available: {_RUST_COMPONENT_ACCELERATION}")

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
        f"WRITE_SCHEMATIC_FILE: Debug analysis completed in {debug_time*1000:.2f}ms, found {sheet_pin_count} sheet pins"
    )

    # Use the kicad_api's S-expression parser to write the file
    # This now uses the Rust-accelerated format_kicad_schematic function internally
    parser_start = time.perf_counter()
    logger.debug("Starting S-expression parsing and formatting")

    from circuit_synth.kicad_api.core.s_expression import SExpressionParser

    parser = SExpressionParser()
    parser.write_file(schematic_expr, out_path)

    parser_time = time.perf_counter() - parser_start
    logger.debug(
        f"S-expression parsing and formatting completed in {parser_time*1000:.2f}ms"
    )

    # Analyze the output file
    file_analysis_start = time.perf_counter()
    with open(out_path, "r", encoding="utf-8") as f:
        content = f.read()
    file_analysis_time = time.perf_counter() - file_analysis_start

    total_time = time.perf_counter() - start_time
    throughput = len(content) / (total_time * 1000) if total_time > 0 else 0

    logger.debug(f"File write complete")
    logger.debug(f"WRITE_SCHEMATIC_FILE: Total time: {total_time*1000:.2f}ms")
    logger.debug(f"Output file size: {len(content):,} characters")
    logger.debug(f"WRITE_SCHEMATIC_FILE: Output file: {out_path}")
    logger.debug(
        f"Write throughput: {throughput:.1f} chars/ms ({throughput*1000:.0f} chars/sec)"
    )

    # Performance breakdown
    logger.debug("Performance breakdown:")
    logger.debug(
        f"  Debug analysis: {debug_time*1000:.2f}ms ({debug_time/total_time*100:.1f}%)"
    )
    logger.debug(
        f"  S-expression formatting: {parser_time*1000:.2f}ms ({parser_time/total_time*100:.1f}%)"
    )
    logger.debug(
        f"  File analysis: {file_analysis_time*1000:.2f}ms ({file_analysis_time/total_time*100:.1f}%)"
    )

    # Compression ratio analysis
    compression_ratio = len(content) / expr_size if expr_size > 0 else 1.0
    logger.debug(
        f"Size change: {expr_size:,} → {len(content):,} chars ({compression_ratio:.2f}x)"
    )

    if _RUST_COMPONENT_ACCELERATION:
        estimated_rust_time = total_time / 6.0  # Expected 6x improvement
        logger.debug(
            f"RUST_PROJECTION: Estimated time with full Rust: {estimated_rust_time*1000:.2f}ms"
        )
        logger.debug(
            f"RUST_PROJECTION: Potential time saved: {(total_time - estimated_rust_time)*1000:.2f}ms"
        )

    logger.debug(f"Successfully wrote {len(content):,} characters to {out_path}")

    # Log the file size
    with open(out_path, "r", encoding="utf-8") as f:
        content = f.read()
    logger.debug(f"Schematic written. Length = {len(content)} chars.")
