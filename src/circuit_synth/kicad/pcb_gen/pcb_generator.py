"""
PCB Generator for Circuit Synth.

This module generates PCB files from circuit definitions, extracting component
information from schematics and applying hierarchical placement algorithms.
"""

import json
import logging
import re
import tempfile
import uuid
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from circuit_synth.core.circuit import Circuit
from circuit_synth.kicad.core.s_expression import SExpressionParser
from circuit_synth.pcb import PCBBoard

# Removed duplicate PCB API imports - using single implementation
from circuit_synth.pcb.simple_ratsnest import add_ratsnest_to_pcb

logger = logging.getLogger(__name__)


class PCBGenerator:
    """
    Generates PCB files from circuit definitions with hierarchical placement.

    This class integrates with the schematic generation workflow to create
    PCB files with components placed according to their hierarchical structure.
    """

    def __init__(self, project_dir: Path, project_name: str):
        """
        Initialize the PCB generator.

        Args:
            project_dir: Directory containing the KiCad project
            project_name: Name of the project
        """
        self.project_dir = Path(project_dir)
        self.project_name = project_name
        self.pcb_path = self.project_dir / f"{project_name}.kicad_pcb"

    def _calculate_initial_board_size(
        self, pcb: "PCBBoard", component_spacing: float = 5.0, margin: float = 10.0
    ) -> Tuple[float, float]:
        """
        Calculate initial board size based on component footprints.

        Args:
            pcb: PCB board with components loaded
            component_spacing: Spacing between components in mm
            margin: Board edge margin in mm

        Returns:
            Tuple of (width, height) in mm
        """
        if not pcb.footprints:
            return 100.0, 100.0  # Default if no components

        # Calculate total area needed for all components
        total_area = 0.0
        max_width = 0.0
        max_height = 0.0
        component_count = 0

        for fp in pcb.footprints.values():
            # Combine library and name for full footprint identifier
            fp_full_name = f"{fp.library}:{fp.name}"

            # Estimate footprint size based on type
            if "QFP" in fp_full_name or "LQFP" in fp_full_name:
                fp_width = fp_height = 10.0  # Typical QFP size
            elif "SOT" in fp_full_name:
                fp_width = 7.0
                fp_height = 4.0
            elif "USB" in fp_full_name:
                fp_width = 15.0
                fp_height = 10.0
            elif "ESP" in fp_full_name or "RF_Module" in fp_full_name:
                fp_width = 20.0
                fp_height = 15.0
            elif "LGA" in fp_full_name:
                fp_width = 3.5
                fp_height = 3.0
            elif "Crystal" in fp_full_name:
                fp_width = 5.0
                fp_height = 3.2
            elif "IDC" in fp_full_name or "Header" in fp_full_name:
                fp_width = 10.0
                fp_height = 8.0
            elif "0603" in fp_full_name:
                fp_width = 1.6
                fp_height = 0.8
            elif "0805" in fp_full_name:
                fp_width = 2.0
                fp_height = 1.25
            elif "LED" in fp_full_name:
                fp_width = 1.6
                fp_height = 0.8
            elif "SOD" in fp_full_name:
                fp_width = 2.0
                fp_height = 1.2
            else:
                fp_width = 5.0  # Default size
                fp_height = 5.0

            # Add spacing around each component
            fp_width += component_spacing * 2
            fp_height += component_spacing * 2

            total_area += fp_width * fp_height
            max_width = max(max_width, fp_width)
            max_height = max(max_height, fp_height)
            component_count += 1

        # Estimate board dimensions based on total area
        # Use different overhead factors based on component count
        # Increased overhead to give force-directed algorithm more room
        if component_count < 10:
            overhead_factor = 2.5  # 150% overhead for small boards
        elif component_count < 20:
            overhead_factor = 2.0  # 100% overhead for medium boards
        else:
            overhead_factor = 1.8  # 80% overhead for larger boards

        area_with_overhead = total_area * overhead_factor
        side_length = area_with_overhead**0.5

        # Ensure board is at least large enough for biggest component
        width = max(side_length, max_width + margin * 2)
        height = max(side_length, max_height + margin * 2)

        # Round up to nearest 10mm
        width = ((width + 9) // 10) * 10
        height = ((height + 9) // 10) * 10

        # Apply reasonable limits
        width = max(50.0, min(width, 200.0))  # Reduced max from 300 to 200
        height = max(50.0, min(height, 200.0))

        logger.debug(
            f"Calculated initial board size: {width}x{height}mm based on {component_count} components"
        )
        return width, height

    def generate_pcb(
        self,
        circuit_dict: Optional[Dict[str, Circuit]] = None,
        placement_algorithm: str = "spiral",  # Changed default to spiral
        board_width: Optional[float] = None,  # Made optional
        board_height: Optional[float] = None,  # Made optional
        component_spacing: float = 5.0,  # Increased from 2.0 to account for courtyards
        group_spacing: float = 10.0,  # Increased from 5.0
        spiral_step: float = 1.0,  # Step size for spiral search
        max_spiral_radius: float = 30.0,  # Maximum search radius
        max_board_size: float = 500.0,  # Maximum allowed board dimension
        board_size_increment: float = 25.0,  # Reduced from 50.0
        auto_route: bool = False,  # Disable auto-routing by default (can be slow)
        routing_passes: int = 4,  # Number of routing passes
        routing_effort: float = 1.0,  # Routing effort level
        generate_ratsnest: bool = True,
    ) -> bool:  # Generate ratsnest connections
        """
        Generate a PCB file from the schematic files in the project.

        Args:
            circuit_dict: Optional dictionary of circuits (if not provided, reads from schematics)
            placement_algorithm: Algorithm to use for placement ("hierarchical", "force_directed", etc.)
            board_width: Initial board width in mm (if None, auto-calculated)
            board_height: Initial board height in mm (if None, auto-calculated)
            component_spacing: Spacing between components in mm
            group_spacing: Spacing between hierarchical groups in mm
            spiral_step: Step size for spiral search
            max_spiral_radius: Maximum search radius
            max_board_size: Maximum allowed board dimension in mm
            board_size_increment: Size increase per retry in mm
            auto_route: If True, automatically route the PCB using Freerouting (default: False)
            routing_passes: Number of routing passes for Freerouting (1-99)
            routing_effort: Routing effort level (0.0-2.0, where 2.0 is maximum)
            generate_ratsnest: If True, generate ratsnest connections (default: True)

        Returns:
            True if successful, False otherwise
        """
        retry_count = 0
        max_retries = 10
        pcb = None

        try:
            logger.debug(f"Starting PCB generation for project: {self.project_name}")

            # Create PCB board
            pcb = PCBBoard()

            # Extract components from schematics
            components = self._extract_components_from_schematics()
            if not components:
                logger.warning("No components found in schematics")
                return False

            logger.debug(f"Found {len(components)} components to place")

            # Add components to PCB (only once, before retry loop)
            for comp_info in components:
                # First try to use the footprint from the component data
                footprint = comp_info.get("footprint")

                # Only proceed if footprint is specified in component data
                if footprint:
                    # Component-specific debugging removed

                    # Add footprint from library to get full graphics including courtyard
                    fp = pcb.add_footprint_from_library(
                        footprint_id=footprint,
                        reference=comp_info["reference"],
                        x=50,  # Initial position (will be updated by placement)
                        y=50,
                        rotation=0,
                        value=comp_info.get("value", ""),
                    )

                    # Component-specific debugging removed

                    # Store hierarchical path in footprint
                    if fp and comp_info.get("hierarchical_path"):
                        fp.path = comp_info["hierarchical_path"]
                        logger.debug(
                            f"Added {comp_info['reference']} with footprint: {footprint} (from {'component' if comp_info.get('footprint') else 'symbol mapping'})"
                        )
                else:
                    logger.warning(
                        f"No footprint found for {comp_info['reference']} ({comp_info['lib_id']})"
                    )

            # Calculate initial board size if not provided
            if board_width is None or board_height is None:
                current_width, current_height = self._calculate_initial_board_size(
                    pcb, component_spacing
                )
            else:
                current_width = board_width
                current_height = board_height

            # Extract connections from schematics
            connections = self._extract_connections_from_schematics()
            logger.debug(f"Found {len(connections)} connections")

            # Apply placement algorithm
            # Use spiral placement if we have connections, otherwise use hierarchical
            if connections and placement_algorithm == "hierarchical":
                logger.info(
                    "Found connections, switching to spiral placement for better results"
                )
                placement_algorithm = "spiral"

            logger.debug(f"Applying {placement_algorithm} placement algorithm")
            logger.debug(
                f"Component spacing: {component_spacing}mm, Group spacing: {group_spacing}mm"
            )

            # Retry loop for placement with increasing board size
            placement_successful = False
            while retry_count < max_retries and not placement_successful:
                try:
                    # Set/update board outline
                    pcb.set_board_outline_rect(0, 0, current_width, current_height)
                    logger.debug(
                        f"Attempting placement with board size: {current_width}x{current_height}mm (attempt {retry_count + 1})"
                    )

                    # Reset component positions before retry
                    if retry_count > 0:
                        for fp in pcb.footprints.values():
                            fp.position.x = 50
                            fp.position.y = 50

                    # Debug: List components before placement
                    if retry_count == 0:
                        footprints_before = pcb.list_footprints()
                        logger.debug(
                            f"Components before placement: {len(footprints_before)}"
                        )
                        for ref, footprint_lib, x, y in footprints_before[
                            :5
                        ]:  # Show first 5
                            logger.debug(f"  {ref} at ({x}, {y})")

                    # Call placement algorithm with appropriate parameters
                    if placement_algorithm == "force_directed":
                        # Use tighter parameters for force-directed placement
                        result = pcb.auto_place_components(
                            algorithm=placement_algorithm,
                            component_spacing=component_spacing,
                            group_spacing=group_spacing,
                            board_width=current_width,
                            board_height=current_height,
                            connections=connections,
                            attraction_strength=1.0,  # High attraction
                            repulsion_strength=10.0,  # Low repulsion
                            iterations_per_level=150,  # More iterations
                        )
                    else:
                        logger.error(f"🔥🔥🔥 PCB GENERATOR: About to call auto_place_components 🔥🔥🔥")
                        logger.error(f"🔥 PCB GENERATOR: placement_algorithm = '{placement_algorithm}'")
                        logger.error(f"🔥 PCB GENERATOR: board size = {current_width}x{current_height}")
                        logger.error(f"🔥 PCB GENERATOR: component count = {len(pcb.footprints)}")
                        
                        result = pcb.auto_place_components(
                            algorithm=placement_algorithm,
                            component_spacing=component_spacing,
                            group_spacing=group_spacing,
                            board_width=current_width,
                            board_height=current_height,
                            spiral_step=spiral_step,
                            max_spiral_radius=max_spiral_radius,
                            connections=(
                                connections
                                if placement_algorithm
                                in ["spiral", "force_directed", "connection_centric", "external"]
                                else None
                            ),
                        )
                        
                        logger.error(f"🔥🔥🔥 PCB GENERATOR: auto_place_components RETURNED 🔥🔥🔥")
                        logger.error(f"🔥 PCB GENERATOR: result = {result}")
                        logger.error(f"🔥 PCB GENERATOR: Component positions after auto_place_components:")
                        for ref, footprint in pcb.footprints.items():
                            logger.error(f"🔥   {ref}: ({footprint.position.x}, {footprint.position.y})")

                    # If we get here, placement was successful
                    placement_successful = True
                    logger.debug(
                        f"✓ Placement successful with board size: {current_width}x{current_height}mm"
                    )

                    # Calculate actual board size needed based on placement
                    logger.error(f"🔥🔥🔥 PCB GENERATOR: Starting bounding box calculation 🔥🔥🔥")
                    logger.error(f"🔥 PCB GENERATOR: placement_algorithm = '{placement_algorithm}'")
                    
                    # Simplified placement calculation
                    def calculate_placement_bbox(footprints, margin=10.0):
                        if not footprints:
                            logger.error(f"🔥 BBOX: No footprints, returning default bbox")
                            return -margin, -margin, margin, margin
                        # Simple bounding box calculation
                        logger.error(f"🔥 BBOX: Calculating bbox for {len(footprints)} footprints")
                        for fp in footprints[:3]:  # Log first 3
                            logger.error(f"🔥 BBOX:   {fp.reference}: ({fp.position.x}, {fp.position.y})")
                        min_x = min(fp.position.x for fp in footprints) - margin
                        min_y = min(fp.position.y for fp in footprints) - margin
                        max_x = max(fp.position.x for fp in footprints) + margin
                        max_y = max(fp.position.y for fp in footprints) + margin
                        logger.error(f"🔥 BBOX: Calculated bbox: ({min_x}, {min_y}) to ({max_x}, {max_y})")
                        return min_x, min_y, max_x, max_y

                    footprints = list(pcb.footprints.values())
                    min_x, min_y, max_x, max_y = calculate_placement_bbox(
                        footprints, margin=10.0
                    )

                    # Round up to nearest 5mm for cleaner dimensions
                    actual_width = ((max_x - min_x + 4) // 5) * 5
                    actual_height = ((max_y - min_y + 4) // 5) * 5
                    logger.error(f"🔥 PCB GENERATOR: Calculated board dimensions: {actual_width}x{actual_height}mm")

                    # Update board outline to actual size needed (skip for external placement)
                    if placement_algorithm != "external":
                        logger.error(f"🔥 PCB GENERATOR: NOT external - updating board outline to {actual_width}x{actual_height}")
                        pcb.set_board_outline_rect(0, 0, actual_width, actual_height)
                        logger.debug(
                            f"✓ Adjusted board size to actual needs: {actual_width}x{actual_height}mm"
                        )
                    else:
                        logger.error(f"🔥 PCB GENERATOR: EXTERNAL PLACEMENT - preserving cutout rectangle")
                        logger.debug("Skipping board outline recalculation for external placement to preserve cutout")

                    # Debug: Check result and list components after placement
                    logger.error(f"🔥🔥🔥 PCB GENERATOR: Final placement check 🔥🔥🔥")
                    logger.debug(f"Placement result: {result}")
                    footprints_after = pcb.list_footprints()
                    logger.debug(f"Components after placement: {len(footprints_after)}")
                    logger.error(f"🔥 PCB GENERATOR: Components after ALL processing:")
                    for ref, footprint_lib, x, y in footprints_after:  # Show ALL components
                        logger.error(f"🔥   {ref} at ({x}, {y}) - {footprint_lib}")
                    
                    logger.error(f"🔥🔥🔥 PCB GENERATOR: About to write PCB file 🔥🔥🔥")

                except ValueError as e:
                    if "Could not find valid position" in str(e):
                        # Increase board size
                        retry_count += 1
                        current_width += board_size_increment
                        current_height += board_size_increment

                        # Check if we've exceeded maximum size
                        if (
                            current_width > max_board_size
                            or current_height > max_board_size
                        ):
                            logger.error(
                                f"Maximum board size ({max_board_size}mm) exceeded"
                            )
                            raise ValueError(
                                f"Cannot place all components even with {max_board_size}x{max_board_size}mm board"
                            )

                        logger.warning(f"Placement failed: {e}")
                        logger.debug(
                            f"Increasing board size to {current_width}x{current_height}mm for next attempt"
                        )
                    else:
                        # Re-raise other errors
                        raise

            if not placement_successful:
                logger.error("Failed to place components after all retries")
                return False

            # Apply netlist to PCB
            logger.debug("Applying netlist to PCB...")
            netlist_applied = self._apply_netlist_to_pcb(pcb)
            if netlist_applied:
                logger.info("✓ Netlist successfully applied to PCB")
            else:
                logger.warning("⚠ No netlist found or netlist application failed")

            # Auto-route if requested
            if auto_route:
                logger.info("Starting auto-routing process...")
                routing_success = self._auto_route_pcb(
                    pcb, passes=routing_passes, effort=routing_effort
                )
                if routing_success:
                    logger.info("✓ Auto-routing completed successfully")
                else:
                    logger.warning("⚠ Auto-routing failed, saving unrouted PCB")

            # Save PCB file
            pcb.save(self.pcb_path)
            logger.debug(f"PCB file saved to: {self.pcb_path}")

            # Generate ratsnest connections if requested (AFTER PCB save)
            if generate_ratsnest:
                logger.info(
                    "Skipping ratsnest generation - KiCad generates ratsnest dynamically"
                )
                # KiCad generates ratsnest connections dynamically based on net connectivity
                # No need to add explicit ratsnest tokens to the PCB file
                logger.info(
                    "✓ PCB nets are properly defined for dynamic ratsnest generation"
                )

            # Update project file to include PCB
            self._update_project_file()

            return True

        except Exception as e:
            logger.error(f"Error generating PCB: {e}", exc_info=True)
            return False

    def _extract_components_from_schematics(self) -> List[Dict[str, Any]]:
        """
        Extract component information from all schematic files.

        Returns:
            List of component dictionaries with reference, lib_id, value, and hierarchical_path
        """
        components = []

        # Read all schematic files
        sch_files = list(self.project_dir.glob("*.kicad_sch"))
        logger.debug(f"Found {len(sch_files)} schematic files")

        # Track component references to detect duplicates
        seen_references = set()

        for sch_file in sch_files:
            try:
                logger.debug(f"Reading schematic: {sch_file}")
                parser = SExpressionParser()
                schematic = parser.parse_file(str(sch_file))

                # Get components from this schematic
                for comp in schematic.components:
                    # CRITICAL FIX: Extract hierarchical path to match netlist format
                    # This must match the hierarchical paths generated by the netlist exporter
                    if sch_file.stem == self.project_name:
                        # This is the root schematic
                        hierarchical_path = "/"
                    else:
                        # This is a sub-sheet, use format that matches netlist generation
                        hierarchical_path = f"/{sch_file.stem}/"

                    comp_info = {
                        "reference": comp.reference,
                        "lib_id": comp.lib_id,
                        "value": comp.value,
                        "footprint": comp.footprint,  # Extract footprint from component
                        "hierarchical_path": hierarchical_path,
                        "schematic": sch_file.stem,
                    }

                    # Only add components with valid references
                    if comp_info["reference"] and not comp_info["reference"].startswith(
                        "#"
                    ):
                        # Check for duplicate references
                        if comp_info["reference"] in seen_references:
                            logger.warning(
                                f"Duplicate component reference found: {comp_info['reference']} in {sch_file.stem}"
                            )
                            logger.warning(
                                f"  Previous hierarchical path may be overwritten"
                            )
                        seen_references.add(comp_info["reference"])

                        components.append(comp_info)
                        logger.debug(
                            f"Found component: {comp_info['reference']} ({comp_info['lib_id']}) from {sch_file.stem}"
                        )
                        logger.debug(
                            f"  Hierarchical path: {comp_info['hierarchical_path']}"
                        )
                        logger.debug(
                            f"  Footprint: {comp_info.get('footprint', 'None')}"
                        )

            except Exception as e:
                logger.error(f"Error reading schematic {sch_file}: {e}")
                continue

        return components

    def _extract_connections_from_schematics(self) -> List[Tuple[str, str]]:
        """
        Extract net connections between components from schematics.

        Returns:
            List of (ref1, ref2) tuples representing connections
        """
        connections = []
        nets = {}  # Map net names to connected components

        # Read the netlist file if it exists
        # First check in project directory, then in parent directory
        netlist_path = self.project_dir / f"{self.project_name}.net"
        if not netlist_path.exists():
            # Check in parent directory with circuit_synth_ prefix
            netlist_path = (
                self.project_dir.parent.parent
                / f"circuit_synth_{self.project_name}.net"
            )

        if netlist_path.exists():
            logger.info(f"Reading netlist from {netlist_path}")
            try:
                # Parse the netlist to extract connections
                with open(netlist_path, "r") as f:
                    content = f.read()

                # Simple netlist parsing - look for net sections
                import re

                # Updated pattern to handle multi-line net definitions
                net_pattern = r'\(net\s+\(code\s+"?\d+"?\)\s+\(name\s+"([^"]+)"\)(.*?)(?=\(net\s+\(code|$)'
                net_matches = re.findall(net_pattern, content, re.DOTALL)

                for net_name, net_content in net_matches:
                    # Skip power nets and unconnected nets
                    # Check both simple names and hierarchical names
                    base_name = net_name.split("/")[-1] if "/" in net_name else net_name
                    if base_name in [
                        "GND",
                        "3V3",
                        "5V",
                        "VCC",
                        "VDD",
                        "VSS",
                        "",
                    ] or net_name.startswith("Net-("):
                        continue

                    # Extract component references from this net
                    # Updated pattern to handle hierarchical references
                    node_pattern = r'\(node\s+\(ref\s+"([^"]+)"\)\s+\(pin\s+"[^"]+"\)'
                    nodes = re.findall(node_pattern, net_content)

                    if len(nodes) >= 2:
                        # Extract just the component reference (last part after /)
                        clean_nodes = []
                        for node in nodes:
                            # Handle hierarchical references like "regulator/U2"
                            ref = node.split("/")[-1] if "/" in node else node

                            # Handle subcircuit prefixes - map "subcircuit_R1" back to "R1"
                            if ref.startswith("subcircuit_"):
                                original_ref = ref[len("subcircuit_") :]
                                print(
                                    f"🔧 SUBCIRCUIT MAPPING (early): {ref} -> {original_ref}"
                                )
                                logger.info(
                                    f"🔧 SUBCIRCUIT MAPPING (early): {ref} -> {original_ref}"
                                )
                                ref = original_ref

                            clean_nodes.append(ref)

                        if net_name not in nets:
                            nets[net_name] = set()
                        for ref in clean_nodes:
                            nets[net_name].add(ref)

                        logger.debug(f"Net {net_name}: {clean_nodes}")

                logger.debug(f"Extracted {len(nets)} nets from netlist")

            except Exception as e:
                logger.error(f"Error reading netlist: {e}")
                # Fall back to schematic-based extraction

        # If no netlist or netlist parsing failed, try schematic-based extraction
        if not nets:
            logger.info("Attempting schematic-based connection extraction")
            sch_files = list(self.project_dir.glob("*.kicad_sch"))

            for sch_file in sch_files:
                try:
                    parser = SExpressionParser()
                    schematic = parser.parse_file(str(sch_file))

                    # Extract nets from schematic
                    for net in schematic.nets:
                        if len(net.nodes) >= 2:
                            net_name = net.name
                            # Skip power nets
                            if net_name in ["GND", "3V3", "5V", "VCC", "VDD", "VSS"]:
                                continue

                            if net_name not in nets:
                                nets[net_name] = set()

                            for node in net.nodes:
                                nets[net_name].add(node.component_ref)

                except Exception as e:
                    logger.error(f"Error extracting connections from {sch_file}: {e}")
                    continue

        # Convert nets to connection pairs
        logger.info(f"Found {len(nets)} nets with connections")
        for net_name, connected_refs in nets.items():
            connected_list = list(connected_refs)
            # Create connections between all components on the same net
            for i in range(len(connected_list)):
                for j in range(i + 1, len(connected_list)):
                    connections.append((connected_list[i], connected_list[j]))
                    logger.debug(
                        f"Connection: {connected_list[i]} <-> {connected_list[j]} (net: {net_name})"
                    )

        logger.info(f"Extracted {len(connections)} connections total")
        return connections

    def _extract_hierarchical_path(self, component) -> str:
        """
        Extract hierarchical path from component properties.

        Args:
            component: SchematicSymbol object from schematic reader

        Returns:
            Hierarchical path string (e.g., "/power/regulator")
        """
        # Look for hierarchical path in component properties
        if hasattr(component, "properties") and component.properties:
            # Check for explicit path property
            if "path" in component.properties:
                return component.properties["path"]

            # Check for sheet path property
            if "Sheetfile" in component.properties:
                return component.properties["Sheetfile"]

        # Try to extract from uuid or other attributes
        # For now, default to root
        return "/"

    def _update_project_file(self):
        """Update the .kicad_pro file to include the PCB file."""
        pro_path = self.project_dir / f"{self.project_name}.kicad_pro"

        if not pro_path.exists():
            logger.warning("Project file not found, skipping update")
            return

        try:
            with open(pro_path, "r") as f:
                pro_data = json.load(f)

            # Add PCB to boards list if not already present
            pcb_filename = f"{self.project_name}.kicad_pcb"
            if pcb_filename not in pro_data.get("boards", []):
                if "boards" not in pro_data:
                    pro_data["boards"] = []
                pro_data["boards"].append(pcb_filename)

                with open(pro_path, "w") as f:
                    json.dump(pro_data, f, indent=2)

                logger.info(f"Updated project file to include PCB: {pcb_filename}")

        except Exception as e:
            logger.error(f"Error updating project file: {e}")

    def _apply_netlist_to_pcb(self, pcb) -> bool:
        """
        Apply netlist information to the PCB by creating nets and assigning pads.
        This method properly handles hierarchical designs by flattening nets.

        Args:
            pcb: PCBBoard instance

        Returns:
            True if netlist was applied, False otherwise
        """
        # Find netlist file - check multiple locations
        netlist_path = self.project_dir / f"{self.project_name}.net"
        if not netlist_path.exists():
            # Check in parent directory where it's commonly generated
            netlist_path = self.project_dir.parent / f"{self.project_name}.net"
        if not netlist_path.exists():
            # Check in parent directory with circuit_synth_ prefix
            netlist_path = (
                self.project_dir.parent / f"circuit_synth_{self.project_name}.net"
            )
        if not netlist_path.exists():
            # Check in grandparent directory
            netlist_path = self.project_dir.parent.parent / f"{self.project_name}.net"

        if not netlist_path.exists():
            logger.warning(f"No netlist file found for {self.project_name}")
            logger.warning(f"  Searched in: {self.project_dir}")
            logger.warning(f"  Searched in: {self.project_dir.parent}")
            logger.warning(f"  Searched in: {self.project_dir.parent.parent}")
            return False

        logger.info(f"Parsing netlist from {netlist_path}")

        try:
            # Parse netlist file
            with open(netlist_path, "r") as f:
                content = f.read()

            # Pattern to match net definitions with multi-line support
            net_pattern = r'\(net\s+\(code\s+"?\d+"?\)\s+\(name\s+"([^"]+)"\)(.*?)(?=\(net\s+\(code|$)'
            net_matches = re.findall(net_pattern, content, re.DOTALL)

            # Track assigned pads and net mapping
            assigned_pads = set()
            nets_created = 0
            net_mapping = {}  # Maps hierarchical net names to flattened net names

            # Dynamic net merging based on actual netlist content
            # Group nets by their base name (last part after hierarchy separator)
            net_groups = defaultdict(list)
            net_mapping = {}

            # First pass: group nets by base name
            for net_name, net_content in net_matches:
                if "/" in net_name:
                    # This is a hierarchical net
                    base_name = net_name.split("/")[-1]
                    net_groups[base_name].append((net_name, net_content))
                else:
                    # Non-hierarchical net
                    net_groups[net_name].append((net_name, net_content))

            # Second pass: determine which nets should be merged
            # Nets with the same base name across different hierarchies should be merged
            for base_name, net_list in net_groups.items():
                if len(net_list) > 1:
                    # Multiple nets with same base name - these should be merged
                    logger.info(
                        f"Found {len(net_list)} nets with base name '{base_name}' to merge:"
                    )

                    # Use the shortest net name (usually the global one) as the target
                    target_net = min([net[0] for net in net_list], key=len)

                    # If all are hierarchical, use just the base name
                    if all("/" in net[0] for net in net_list):
                        target_net = base_name

                    for net_name, _ in net_list:
                        net_mapping[net_name] = target_net
                        if net_name != target_net:
                            logger.debug(f"  Mapping '{net_name}' -> '{target_net}'")
                else:
                    # Single net, use as-is
                    net_name = net_list[0][0]
                    net_mapping[net_name] = net_name

            # Second pass: create nets and assign pads
            for net_name, net_content in net_matches:
                # Get the flattened net name
                flattened_net_name = net_mapping.get(net_name, net_name)

                # Extract component references and pad numbers from this net
                node_pattern = r'\(node\s+\(ref\s+"([^"]+)"\)\s+\(pin\s+"([^"]+)"\)'
                nodes = re.findall(node_pattern, net_content)

                if not nodes:
                    continue

                # Clean up hierarchical references (e.g., "regulator/U2" -> "U2")
                # AND handle subcircuit prefixes (e.g., "subcircuit_R1" -> "R1")
                clean_nodes = []
                for ref, pin in nodes:
                    # Handle hierarchical path prefixes (e.g., "regulator/U2" -> "U2")
                    clean_ref = ref.split("/")[-1] if "/" in ref else ref

                    clean_nodes.append((clean_ref, pin))

                # Check if net already exists (using flattened name)
                existing_net = pcb.get_net_by_name(flattened_net_name)
                if existing_net:
                    net_num = existing_net.number
                else:
                    # Create new net with flattened name
                    net_num = pcb.add_net(flattened_net_name)
                    nets_created += 1
                    logger.debug(
                        f"Created net {net_num}: '{flattened_net_name}'"
                        + (
                            f" (flattened from '{net_name}')"
                            if net_name != flattened_net_name
                            else ""
                        )
                    )

                # Assign all pads in this net
                for ref, pad_num in clean_nodes:
                    # Get the footprint
                    logger.debug(f"Looking up footprint for reference: {ref}")
                    footprint = pcb.get_footprint(ref)
                    if not footprint:
                        logger.warning(
                            f"Footprint {ref} not found, skipping pad assignment for net '{flattened_net_name}'"
                        )
                        # List available footprints for debugging
                        available_refs = [
                            fp.reference for fp in pcb.pcb_data["footprints"]
                        ]
                        logger.debug(
                            f"Available footprint references: {available_refs}"
                        )
                        continue

                    # Find ALL pads with this number (e.g., SOT-223 has two pads numbered "2")
                    pads_found = 0
                    for pad in footprint.pads:
                        if pad.number == pad_num:
                            # Assign the net to this pad
                            pad.net = net_num
                            pad.net_name = flattened_net_name
                            pads_found += 1
                            logger.debug(
                                f"Assigned {ref} pad {pad_num} (instance {pads_found}) to net {net_num} ('{flattened_net_name}')"
                            )

                    if pads_found > 0:
                        assigned_pads.add((ref, pad_num))
                        if pads_found > 1:
                            logger.info(
                                f"Note: {ref} has {pads_found} pads numbered '{pad_num}', assigned all to net {net_num}"
                            )

            logger.info(
                f"Created {nets_created} nets, assigned {len(assigned_pads)} pads to nets"
            )

            # Third pass: create unique nets for unconnected pads
            # KiCad convention is to give each unconnected pad its own net with a descriptive name
            unconnected_count = 0
            for footprint in pcb.pcb_data["footprints"]:
                for pad in footprint.pads:
                    # If pad wasn't assigned a net from the netlist
                    if (footprint.reference, pad.number) not in assigned_pads:
                        # Create a unique net for this unconnected pad
                        if pad.net is None:
                            # Get pin name if available (from pad type or default to pad number)
                            pin_name = getattr(pad, "pin_name", f"Pad{pad.number}")

                            # Create net name following KiCad convention: "unconnected-(RefDes-PinName-PadNumber)"
                            unconnected_net_name = f"unconnected-({footprint.reference}-{pin_name}-Pad{pad.number})"

                            # Create new net
                            net_num = len(pcb.pcb_data["nets"])
                            # Simplified - create basic net structure
                            from circuit_synth.pcb.types import Net

                            new_net = Net(number=net_num, name=unconnected_net_name)
                            pcb.pcb_data["nets"].append(new_net)

                            # Assign pad to this net
                            pad.net = net_num
                            pad.net_name = unconnected_net_name
                            unconnected_count += 1

                            logger.debug(
                                f"Created net {net_num} for unconnected pad: {footprint.reference} pad {pad.number}"
                            )

            if unconnected_count > 0:
                logger.info(
                    f"Created {unconnected_count} unique nets for unconnected pads"
                )

            # Log net summary
            logger.info("Net summary:")
            for i, net in enumerate(pcb.pcb_data["nets"][:10]):  # Show first 10 nets
                if hasattr(net, "name"):
                    logger.info(f"  Net {net.number}: '{net.name}'")
            if len(pcb.pcb_data["nets"]) > 10:
                logger.info(f"  ... and {len(pcb.pcb_data['nets']) - 10} more nets")

            return True

        except Exception as e:
            logger.error(f"Error applying netlist: {e}", exc_info=True)
            return False

    def _auto_route_pcb(
        self, pcb: PCBBoard, passes: int = 4, effort: float = 1.0
    ) -> bool:
        """
        Automatically route the PCB using Freerouting.

        Args:
            pcb: The PCB board object
            passes: Number of routing passes (1-99)
            effort: Routing effort level (0.0-2.0)

        Returns:
            True if routing was successful, False otherwise
        """
        logger.info("=" * 60)
        logger.info("AUTO-ROUTING PROCESS STARTING")
        logger.info("=" * 60)

        try:
            # Create temporary directory for routing files
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                logger.info(f"Created temp directory: {temp_path}")

                # Save current PCB to temporary file
                temp_pcb_file = temp_path / "temp_pcb.kicad_pcb"
                logger.info(f"Saving PCB to temp file: {temp_pcb_file}")

                # Log PCB state before saving
                logger.info(f"PCB state before saving:")
                logger.info(
                    f"  - Footprints: {len(pcb.pcb_data.get('footprints', []))}"
                )
                logger.info(f"  - Nets: {len(pcb.pcb_data.get('nets', []))}")
                logger.info(f"  - Tracks: {len(pcb.pcb_data.get('tracks', []))}")

                pcb.save(str(temp_pcb_file))

                # Check file was saved
                if not temp_pcb_file.exists():
                    logger.error("Failed to save temporary PCB file!")
                    return False

                logger.info(
                    f"✓ Temp PCB saved, size: {temp_pcb_file.stat().st_size} bytes"
                )

                # Verify PCB content
                with open(temp_pcb_file, "r") as f:
                    pcb_content = f.read()
                    footprint_count = pcb_content.count("(footprint ")
                    net_count = pcb_content.count("(net ")
                    logger.info(f"Temp PCB file contains:")
                    logger.info(f"  - {footprint_count} footprints")
                    logger.info(f"  - {net_count} nets")

                # Export to DSN
                dsn_file = temp_path / "temp_pcb.dsn"
                logger.info("Exporting PCB to DSN format...")
                logger.info(f"DSN file will be: {dsn_file}")

                try:
                    export_pcb_to_dsn(str(temp_pcb_file), str(dsn_file))
                except Exception as e:
                    logger.error(f"DSN export failed: {e}")
                    return False

                if not dsn_file.exists():
                    logger.error("DSN file was not created!")
                    return False

                logger.info(
                    f"✓ DSN export complete, size: {dsn_file.stat().st_size} bytes"
                )

                # Check DSN content
                with open(dsn_file, "r") as f:
                    dsn_content = f.read()
                    logger.info(f"DSN content analysis:")
                    logger.info(f"  - Total size: {len(dsn_content)} characters")
                    logger.info(f"  - Networks: {dsn_content.count('(net ')} nets")
                    logger.info(
                        f"  - Components: {dsn_content.count('(component ')} components"
                    )
                    logger.info(f"  - Placement section: {'(placement' in dsn_content}")
                    logger.info(f"  - Network section: {'(network' in dsn_content}")
                    logger.info(f"  - Library section: {'(library' in dsn_content}")

                    # Log first few lines for debugging
                    lines = dsn_content.split("\n")[:10]
                    logger.debug("First 10 lines of DSN:")
                    for i, line in enumerate(lines, 1):
                        logger.debug(f"  {i}: {line}")

                # Run Freerouting
                ses_file = temp_path / "temp_pcb.ses"
                logger.info(f"Running Freerouting...")
                logger.info(f"  - Input DSN: {dsn_file}")
                logger.info(f"  - Output SES: {ses_file}")
                logger.info(f"  - Passes: {passes}")
                logger.info(f"  - Effort: {effort}")

                # Convert effort level to string
                effort_str = "medium"
                if effort <= 0.5:
                    effort_str = "fast"
                elif effort >= 1.5:
                    effort_str = "high"
                logger.info(f"  - Effort string: {effort_str}")

                # Use Docker-based Freerouting
                logger.info("Using Docker-based Freerouting...")

                success, result_file = route_pcb_docker(
                    str(dsn_file),
                    str(ses_file),
                    optimization_passes=passes,
                    timeout_seconds=300,  # 5 minute timeout
                )

                logger.info(
                    f"Freerouting result: success={success}, result_file={result_file}"
                )

                if not success:
                    logger.error(f"Freerouting failed: {result_file}")
                    return False

                # Check if SES file was created
                if not ses_file.exists():
                    logger.error(f"SES file not created at: {ses_file}")
                    return False

                logger.info(
                    f"✓ Freerouting completed, SES size: {ses_file.stat().st_size} bytes"
                )

                # Check SES content
                with open(ses_file, "r") as f:
                    ses_content = f.read()
                    logger.info(f"SES has {len(ses_content)} characters")
                    logger.info(f"SES has {ses_content.count('wire ')} wires")
                    logger.info(f"SES has {ses_content.count('via ')} vias")

                # Import SES back to PCB
                logger.info("Importing routing results...")
                try:
                    import_ses_to_pcb(
                        str(temp_pcb_file), str(ses_file), str(temp_pcb_file)
                    )
                except Exception as e:
                    logger.error(f"SES import failed: {e}")
                    return False

                logger.info("✓ Routing import complete")

                # Check the routed PCB
                with open(temp_pcb_file, "r") as f:
                    routed_content = f.read()
                    # Check for segments without space after opening paren
                    track_count = routed_content.count("(segment")
                    via_count = routed_content.count("(via")
                    logger.info(
                        f"Routed PCB has {track_count} tracks and {via_count} vias"
                    )

                # Reload the routed PCB
                from circuit_synth.pcb import PCBParser

                parser = PCBParser()
                routed_data = parser.parse_file(str(temp_pcb_file))

                # Update the PCB object with routed data
                # This preserves the PCB object reference while updating its content
                pcb.pcb_data = routed_data

                logger.info("=" * 60)
                logger.info("AUTO-ROUTING PROCESS COMPLETE")
                logger.info("=" * 60)

                return True

        except Exception as e:
            logger.error(f"Auto-routing failed with exception: {e}", exc_info=True)
            logger.info("=" * 60)
            logger.info("AUTO-ROUTING PROCESS FAILED")
            logger.info("=" * 60)
            return False
