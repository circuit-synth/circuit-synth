"""
DSN (Specctra) format exporter for KiCad PCB files.

This module converts KiCad PCB format (.kicad_pcb) to Specctra DSN format (.dsn)
for use with Freerouting auto-router.

The DSN format includes:
- Board outline (edge cuts)
- Components with their pads
- Netlist connections
- Design rules (track width, clearances)
"""

import logging
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from ..pcb_board import PCBBoard
from ..types import Arc, Footprint, Layer, Line, Net, Pad, Point

logger = logging.getLogger(__name__)


@dataclass
class DSNLayer:
    """Represents a layer in DSN format."""

    name: str
    type: str  # "signal", "power", etc.
    direction: str  # "horizontal", "vertical", "orthogonal"


@dataclass
class DSNPad:
    """Represents a pad in DSN format."""

    name: str  # e.g., "R1-1"
    number: str  # e.g., "1", "A1", etc.
    x: float
    y: float
    shape: str  # "circle", "rect", etc.
    size: Tuple[float, float]
    rotation: float = 0.0
    drill: Optional[float] = None


@dataclass
class DSNComponent:
    """Represents a component in DSN format."""

    name: str  # e.g., "R1"
    footprint_name: str  # e.g., "R_0603_1608Metric"
    x: float
    y: float
    rotation: float
    side: str  # "front" or "back"
    pads: List[DSNPad]


class DSNExporter:
    """
    Exports KiCad PCB files to Specctra DSN format for auto-routing.
    """

    # KiCad to DSN layer mapping
    LAYER_MAP = {
        "F.Cu": "front",
        "B.Cu": "back",
        "In1.Cu": "inner1",
        "In2.Cu": "inner2",
        "In3.Cu": "inner3",
        "In4.Cu": "inner4",
    }

    # Default design rules (in mm)
    DEFAULT_TRACK_WIDTH = 0.25  # 10 mil
    DEFAULT_CLEARANCE = 0.2  # 8 mil
    DEFAULT_VIA_SIZE = 0.8  # 31.5 mil
    DEFAULT_VIA_DRILL = 0.4  # 15.7 mil

    def __init__(self, pcb_board: PCBBoard):
        """
        Initialize the DSN exporter.

        Args:
            pcb_board: The PCBBoard instance to export
        """
        self.board = pcb_board
        self.components: List[DSNComponent] = []
        self.nets: Dict[str, List[str]] = {}  # net_name -> list of pad names
        self.board_outline: List[Tuple[float, float]] = []
        self.layers: List[DSNLayer] = []

    def export(self, output_path: Path) -> None:
        """
        Export the PCB to DSN format.

        Args:
            output_path: Path where the DSN file will be saved
        """
        # Convert to Path if string
        if isinstance(output_path, str):
            output_path = Path(output_path)

        logger.info(f"Exporting PCB to DSN format: {output_path}")

        # Extract data from PCB
        self._extract_board_outline()
        self._extract_layers()
        self._extract_components()
        self._extract_nets()

        # Generate DSN content
        dsn_content = self._generate_dsn()

        # Write to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(dsn_content)

        logger.info(f"DSN export completed: {output_path}")

    def _extract_board_outline(self) -> None:
        """Extract the board outline from Edge.Cuts layer."""
        edge_cuts = []

        # Get all graphics on Edge.Cuts layer
        for footprint in self.board.pcb_data.get("footprints", []):
            for line in footprint.lines:
                if line.layer == "Edge.Cuts":
                    edge_cuts.append(line)

        # Also check for board-level graphics (not in footprints)
        if "graphics" in self.board.pcb_data:
            for graphic in self.board.pcb_data["graphics"]:
                if isinstance(graphic, Line) and graphic.layer == "Edge.Cuts":
                    edge_cuts.append(graphic)

        # Convert lines to outline points
        # For now, assume a simple rectangular board
        if not edge_cuts:
            # Default 100x100mm board if no outline found
            logger.warning("No board outline found, using default 100x100mm")
            self.board_outline = [
                (0.0, 0.0),
                (100.0, 0.0),
                (100.0, 100.0),
                (0.0, 100.0),
                (0.0, 0.0),
            ]
        else:
            # Extract min/max coordinates from edge cuts
            min_x = min_y = float("inf")
            max_x = max_y = float("-inf")

            for line in edge_cuts:
                min_x = min(min_x, line.start.x, line.end.x)
                max_x = max(max_x, line.start.x, line.end.x)
                min_y = min(min_y, line.start.y, line.end.y)
                max_y = max(max_y, line.start.y, line.end.y)

            # Create rectangular outline
            self.board_outline = [
                (min_x, min_y),
                (max_x, min_y),
                (max_x, max_y),
                (min_x, max_y),
                (min_x, min_y),
            ]

    def _extract_layers(self) -> None:
        """Extract layer information from the PCB."""
        # For 2-layer boards, we have front and back
        self.layers = [
            DSNLayer("front", "signal", "horizontal"),
            DSNLayer("back", "signal", "vertical"),
        ]

        # Check if there are inner layers
        pcb_layers = self.board.pcb_data.get("layers", [])
        inner_count = 0

        for layer in pcb_layers:
            if layer.get("canonical_name", "").startswith("In"):
                inner_count += 1
                layer_name = f"inner{inner_count}"
                # Alternate routing direction for inner layers
                direction = "horizontal" if inner_count % 2 == 1 else "vertical"
                self.layers.insert(-1, DSNLayer(layer_name, "signal", direction))

    def _extract_components(self) -> None:
        """Extract component information from the PCB."""
        logger.info("=== Starting component extraction ===")

        # First check what's available
        logger.debug(
            f"board.footprints keys: {list(self.board.footprints.keys()) if hasattr(self.board, 'footprints') else 'N/A'}"
        )
        logger.debug(
            f"pcb_data footprints count: {len(self.board.pcb_data.get('footprints', []))}"
        )

        # Use board.footprints if available, otherwise fall back to pcb_data
        if hasattr(self.board, "footprints") and self.board.footprints:
            logger.info("Using board.footprints dictionary")
            for ref, footprint in self.board.footprints.items():
                logger.info(f"Processing component {ref} ({footprint.name})")

                # Determine which side the component is on
                side = "front" if footprint.layer == "F.Cu" else "back"
                logger.debug(
                    f"  Side: {side}, Position: ({footprint.position.x}, {footprint.position.y})"
                )

                # Extract pads
                dsn_pads = []
                logger.debug(f"  Processing {len(footprint.pads)} pads")
                for pad in footprint.pads:
                    logger.debug(
                        f"    Pad {pad.number}: net={pad.net}, type={pad.type}, layers={pad.layers}"
                    )

                    # Calculate absolute pad position
                    pad_x = footprint.position.x + pad.position.x
                    pad_y = footprint.position.y + pad.position.y

                    # Apply rotation if needed
                    if footprint.rotation != 0:
                        pad_x, pad_y = self._rotate_point(
                            pad_x,
                            pad_y,
                            footprint.position.x,
                            footprint.position.y,
                            footprint.rotation,
                        )

                    # Determine pad shape for DSN
                    dsn_shape = self._convert_pad_shape(pad.shape)

                    # Skip pads with empty numbers (e.g., mounting holes)
                    if not pad.number or str(pad.number).strip() == "":
                        continue

                    dsn_pad = DSNPad(
                        name=f"{ref}-{pad.number}",
                        number=str(pad.number),  # Store pad number separately
                        x=pad_x,
                        y=pad_y,
                        shape=dsn_shape,
                        size=pad.size,
                        rotation=footprint.rotation,
                        drill=(
                            pad.drill if isinstance(pad.drill, (int, float)) else None
                        ),
                    )
                    dsn_pads.append(dsn_pad)

                # Create DSN component
                dsn_component = DSNComponent(
                    name=ref,
                    footprint_name=footprint.name,
                    x=footprint.position.x,
                    y=footprint.position.y,
                    rotation=footprint.rotation,
                    side=side,
                    pads=dsn_pads,
                )
                self.components.append(dsn_component)
                logger.info(f"  Added component {ref} with {len(dsn_pads)} pads")
        else:
            logger.info("Using pcb_data footprints (fallback)")
            for footprint in self.board.pcb_data.get("footprints", []):
                # Determine which side the component is on
                side = "front" if footprint.layer == "F.Cu" else "back"

                # Extract pads
                dsn_pads = []
                for pad in footprint.pads:
                    # Calculate absolute pad position
                    pad_x = footprint.position.x + pad.position.x
                    pad_y = footprint.position.y + pad.position.y

                    # Apply rotation if needed
                    if footprint.rotation != 0:
                        pad_x, pad_y = self._rotate_point(
                            pad_x,
                            pad_y,
                            footprint.position.x,
                            footprint.position.y,
                            footprint.rotation,
                        )

                    # Determine pad shape for DSN
                    dsn_shape = self._convert_pad_shape(pad.shape)

                    # Skip pads with empty numbers (e.g., mounting holes)
                    if not pad.number or str(pad.number).strip() == "":
                        continue

                    dsn_pad = DSNPad(
                        name=f"{footprint.reference}-{pad.number}",
                        number=str(pad.number),  # Store pad number separately
                        x=pad_x,
                        y=pad_y,
                        shape=dsn_shape,
                        size=pad.size,
                        rotation=footprint.rotation,
                        drill=(
                            pad.drill if isinstance(pad.drill, (int, float)) else None
                        ),
                    )
                    dsn_pads.append(dsn_pad)

            # Create DSN component
            dsn_component = DSNComponent(
                name=footprint.reference,
                footprint_name=footprint.name,
                x=footprint.position.x,
                y=footprint.position.y,
                rotation=footprint.rotation,
                side=side,
                pads=dsn_pads,
            )
            self.components.append(dsn_component)

    def _extract_nets(self) -> None:
        """Extract net connectivity information."""
        logger.info("=== Starting net extraction ===")

        # First, log all available nets in the PCB
        logger.info("Available nets in PCB:")
        for net in self.board.pcb_data.get("nets", []):
            logger.info(f"  Net {net.number}: {net.name}")

        # Build net dictionary from component pads
        for component in self.components:
            logger.debug(f"Processing component {component.name}")
            for pad in component.pads:
                # Get net information from the original PCB data
                pad_num = pad.name.split("-")[1]
                net_name = self._get_pad_net(component.name, pad_num)
                logger.debug(
                    f"  Pad {pad.name} (component {component.name}, pad {pad_num}): net_name = {net_name}"
                )

                if net_name and net_name != "":
                    if net_name not in self.nets:
                        self.nets[net_name] = []
                        logger.info(f"Created new net list for: {net_name}")
                    self.nets[net_name].append(pad.name)
                    logger.info(f"Added pad {pad.name} to net {net_name}")
                else:
                    logger.warning(f"Pad {pad.name} has no net assignment!")

        # Log final net summary
        logger.info("=== Net extraction complete ===")
        logger.info(f"Total nets found: {len(self.nets)}")
        for net_name, pads in self.nets.items():
            logger.info(f"  Net '{net_name}': {len(pads)} pads - {', '.join(pads)}")

    def _get_pad_net(self, ref: str, pad_num: str) -> Optional[str]:
        """Get the net name for a specific pad."""
        logger.debug(f"_get_pad_net: Looking for {ref} pad {pad_num}")

        # Find the footprint in the board's footprints dictionary
        if ref in self.board.footprints:
            footprint = self.board.footprints[ref]
            logger.debug(f"  Found footprint {ref} with {len(footprint.pads)} pads")

            # Find the pad
            for pad in footprint.pads:
                logger.debug(
                    f"    Checking pad {pad.number} (net={pad.net}, net_name={getattr(pad, 'net_name', 'N/A')})"
                )
                if str(pad.number) == str(pad_num):
                    logger.debug(f"    Found matching pad!")

                    # Get net name from net number
                    if pad.net is not None and pad.net > 0:
                        logger.debug(f"    Pad has net number: {pad.net}")
                        # Look up net name in the parsed nets
                        for net in self.board.pcb_data.get("nets", []):
                            if net.number == pad.net:
                                logger.info(
                                    f"    Found net name for {ref}-{pad_num}: {net.name} (net {net.number})"
                                )
                                return net.name
                        logger.warning(
                            f"    Could not find net {pad.net} in pcb_data nets!"
                        )
                    # Fallback to net_name if available
                    elif hasattr(pad, "net_name") and pad.net_name:
                        logger.info(
                            f"    Using net_name attribute for {ref}-{pad_num}: {pad.net_name}"
                        )
                        return pad.net_name
                    else:
                        logger.warning(
                            f"    Pad {ref}-{pad_num} has no net assignment (net={pad.net})"
                        )
        else:
            logger.error(f"  Footprint {ref} not found in board.footprints!")
            logger.debug(
                f"  Available footprints: {list(self.board.footprints.keys())}"
            )

        return None

    def _rotate_point(
        self, x: float, y: float, cx: float, cy: float, angle_deg: float
    ) -> Tuple[float, float]:
        """Rotate a point around a center point."""
        angle_rad = math.radians(angle_deg)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)

        # Translate to origin
        x -= cx
        y -= cy

        # Rotate
        new_x = x * cos_a - y * sin_a
        new_y = x * sin_a + y * cos_a

        # Translate back
        return new_x + cx, new_y + cy

    def _convert_pad_shape(self, kicad_shape: str) -> str:
        """Convert KiCad pad shape to DSN shape."""
        shape_map = {
            "circle": "circle",
            "rect": "rect",
            "roundrect": "rect",  # DSN doesn't support rounded rectangles
            "oval": "oval",
            "trapezoid": "rect",  # Simplify to rectangle
            "custom": "rect",  # Simplify custom shapes
        }
        return shape_map.get(kicad_shape, "rect")

    def _generate_dsn(self) -> str:
        """Generate the complete DSN file content."""
        lines = []

        # Header
        lines.append("(pcb circuit_synth_pcb")
        lines.append("  (parser")
        lines.append('    (string_quote ")')
        lines.append("    (space_in_quoted_tokens on)")
        lines.append('    (host_cad "KiCad\'s Pcbnew")')
        lines.append(f'    (host_version "{self._get_kicad_version()}")')
        lines.append("  )")
        lines.append("")

        # Resolution and unit
        lines.append("  (resolution mm 10)")
        lines.append("  (unit mm)")
        lines.append("")

        # Structure
        lines.append("  (structure")

        # Layers - flat structure that Freerouting expects
        for layer in self.layers:
            lines.append(f"    (layer {layer.name} (type {layer.type}))")

        # Boundary (board outline)
        lines.append("    (boundary")
        lines.append("      (path pcb 0")
        for x, y in self.board_outline:
            lines.append(f"        {x:.3f} {y:.3f}")
        lines.append("      )")
        lines.append("    )")

        # Via definitions
        lines.append("    (via")
        lines.append(
            f'      "Via[0-{len(self.layers)-1}]_'
            f'{self.DEFAULT_VIA_SIZE}:{self.DEFAULT_VIA_DRILL}_um"'
        )
        lines.append("    )")

        # Rules
        lines.append("    (rule")
        lines.append(f"      (width {self.DEFAULT_TRACK_WIDTH})")
        lines.append(f"      (clearance {self.DEFAULT_CLEARANCE})")
        lines.append("      (clearance 0.1 (type smd_to_turn_gap))")
        lines.append("      (clearance 0.2 (type default_smd))")
        lines.append("    )")

        lines.append("  )")  # end structure
        lines.append("")

        # Placement
        lines.append("  (placement")
        for component in self.components:
            lines.append(
                f"    (component {component.footprint_name} (place {component.name} {component.x:.3f} {component.y:.3f} {component.side} {component.rotation:.1f}))"
            )
        lines.append("  )")
        lines.append("")

        # Library
        lines.append("  (library")

        # Add padstack and image definitions
        self._add_padstack_definitions(lines)
        self._add_footprint_definitions(lines)

        lines.append("  )")  # end library
        lines.append("")

        # Network
        lines.append("  (network")

        logger.info("=== Writing network section to DSN ===")

        # Nets
        for net_name, pads in self.nets.items():
            logger.info(f"Processing net '{net_name}' with {len(pads)} pads")
            if len(pads) > 1:  # Only include nets with multiple connections
                sanitized_name = self._sanitize_net_name(net_name)
                logger.info(
                    f"  Writing net '{sanitized_name}' (original: '{net_name}') with pads: {pads}"
                )
                lines.append(f'    (net "{sanitized_name}"')
                lines.append("      (pins")
                for pad in pads:
                    lines.append(f"        {pad}")
                lines.append("      )")
                lines.append("    )")
            else:
                logger.warning(
                    f"  Skipping net '{net_name}' - only has {len(pads)} pad(s): {pads}"
                )

        lines.append("  )")  # end network

        logger.info("=== Network section complete ===")

        # Wiring (empty for unrouted board)
        lines.append("  (wiring")
        lines.append("  )")

        lines.append(")")  # end pcb

        return "\n".join(lines)

    def _add_padstack_definitions(self, lines: List[str]) -> None:
        """Add padstack (pad shape) definitions."""
        # First, add via padstack definitions
        via_name = f"Via[0-{len(self.layers)-1}]_{self.DEFAULT_VIA_SIZE}:{self.DEFAULT_VIA_DRILL}_um"
        lines.append(f'    (padstack "{via_name}"')
        # Via appears on all layers
        for layer in self.layers:
            lines.append(
                f"      (shape (circle {layer.name} {self.DEFAULT_VIA_SIZE:.3f} 0 0))"
            )
        lines.append("      (attach off)")
        lines.append("    )")

        # Collect unique pad types
        pad_types = set()

        for component in self.components:
            for pad in component.pads:
                if pad.drill:
                    # Through-hole pad
                    pad_type = f"Round[A]Pad_{pad.size[0]:.0f}_um"
                else:
                    # SMD pad
                    if pad.shape == "circle":
                        pad_type = f"Round[T]Pad_{pad.size[0]:.0f}_um"
                    else:
                        # Ensure minimum dimensions for pad type name
                        width = max(pad.size[0], 0.1)
                        height = max(pad.size[1], 0.1)
                        pad_type = f"Rect[T]Pad_{width:.0f}x{height:.0f}_um"
                pad_types.add(pad_type)

        # Define each unique pad type as a separate padstack
        for pad_type in sorted(pad_types):
            lines.append(f"    (padstack {pad_type}")

            if "Round[A]" in pad_type:
                # Through-hole round pad - use layer names
                size = float(pad_type.split("_")[1])
                for layer in self.layers:
                    lines.append(f"      (shape (circle {layer.name} {size:.3f} 0 0))")
                lines.append("      (attach off)")
            elif "Round[T]" in pad_type:
                # SMD round pad - only on front layer
                size = float(pad_type.split("_")[1])
                lines.append(f"      (shape (circle front {size:.3f} 0 0))")
                lines.append("      (attach off)")
            elif "Rect[T]" in pad_type:
                # SMD rectangular pad - only on front layer
                parts = pad_type.split("_")[1].split("x")
                width = float(parts[0])
                height = float(parts[1])
                # Ensure minimum dimensions to avoid zero-area pads
                width = max(width, 0.1)  # Minimum 0.1mm width
                height = max(height, 0.1)  # Minimum 0.1mm height
                lines.append(
                    f"      (shape (rect front -{width/2:.3f} -{height/2:.3f} "
                    f"{width/2:.3f} {height/2:.3f}))"
                )
                lines.append("      (attach off)")

            lines.append("    )")

    def _add_footprint_definitions(self, lines: List[str]) -> None:
        """Add footprint (image) definitions."""
        # Group components by footprint type
        footprint_types: Dict[str, List[DSNComponent]] = {}

        for component in self.components:
            if component.footprint_name not in footprint_types:
                footprint_types[component.footprint_name] = []
            footprint_types[component.footprint_name].append(component)

        # Define each unique footprint type as a separate image
        for fp_id, components in footprint_types.items():
            # Use the first component as reference
            ref_component = components[0]

            lines.append(f"    (image {fp_id}")

            # Add outline (simplified as bounding box)
            bbox = self._calculate_footprint_bbox(ref_component)
            if bbox:
                lines.append("      (outline")
                lines.append(
                    f"        (rect front {bbox[0]:.3f} {bbox[1]:.3f} "
                    f"{bbox[2]:.3f} {bbox[3]:.3f})"
                )
                lines.append("      )")

            # Add pins
            for pad in ref_component.pads:
                # Determine padstack name
                if pad.drill:
                    padstack = f"Round[A]Pad_{pad.size[0]:.0f}_um"
                else:
                    if pad.shape == "circle":
                        padstack = f"Round[T]Pad_{pad.size[0]:.0f}_um"
                    else:
                        # Ensure minimum dimensions for pad reference
                        width = max(pad.size[0], 0.1)
                        height = max(pad.size[1], 0.1)
                        padstack = f"Rect[T]Pad_{width:.0f}x{height:.0f}_um"

                # Calculate relative position
                rel_x = pad.x - ref_component.x
                rel_y = pad.y - ref_component.y

                lines.append(
                    f"      (pin {padstack} {pad.number} " f"{rel_x:.3f} {rel_y:.3f})"
                )

            lines.append("    )")

    def _get_footprint_id(self, component: DSNComponent) -> str:
        """Generate a unique footprint identifier."""
        return component.footprint_name

    def _calculate_footprint_bbox(
        self, component: DSNComponent
    ) -> Optional[Tuple[float, float, float, float]]:
        """Calculate bounding box for a footprint."""
        if not component.pads:
            return None

        min_x = min_y = float("inf")
        max_x = max_y = float("-inf")

        for pad in component.pads:
            # Calculate pad bounds
            pad_min_x = pad.x - pad.size[0] / 2
            pad_max_x = pad.x + pad.size[0] / 2
            pad_min_y = pad.y - pad.size[1] / 2
            pad_max_y = pad.y + pad.size[1] / 2

            # Update bounds
            min_x = min(min_x, pad_min_x)
            max_x = max(max_x, pad_max_x)
            min_y = min(min_y, pad_min_y)
            max_y = max(max_y, pad_max_y)

        # Add some margin
        margin = 0.5
        return (min_x - margin, min_y - margin, max_x + margin, max_y + margin)

    def _sanitize_net_name(self, net_name: str) -> str:
        """Sanitize net name for DSN format."""
        # Replace special characters that might cause issues
        replacements = {
            "/": "_",
            "\\": "_",
            " ": "_",
            "-": "_",
            "+": "plus",
            "(": "",
            ")": "",
            "[": "",
            "]": "",
            "{": "",
            "}": "",
        }

        sanitized = net_name
        for old, new in replacements.items():
            sanitized = sanitized.replace(old, new)

        return sanitized

    def _get_kicad_version(self) -> str:
        """Get KiCad version string."""
        # Extract from PCB data if available
        if "generator_version" in self.board.pcb_data:
            return self.board.pcb_data["generator_version"]
        return "9.0"


def export_pcb_to_dsn(pcb_path: Path, dsn_path: Path) -> None:
    """
    Convenience function to export a KiCad PCB file to DSN format.

    Args:
        pcb_path: Path to the input .kicad_pcb file (str or Path)
        dsn_path: Path where the .dsn file will be saved (str or Path)
    """
    # Convert to Path objects if needed
    if isinstance(pcb_path, str):
        pcb_path = Path(pcb_path)
    if isinstance(dsn_path, str):
        dsn_path = Path(dsn_path)

    # Load the PCB
    board = PCBBoard(pcb_path)

    # Create exporter and export
    exporter = DSNExporter(board)
    exporter.export(dsn_path)
