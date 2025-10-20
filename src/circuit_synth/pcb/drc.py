"""
Enhanced Design Rule Check (DRC) module for PCB layout validation.

This module extends the basic validation with comprehensive DRC checks including:
- Via placement validation (no shorts to pads/traces)
- Minimum clearance validation between all copper features
- Trace width compliance
- Copper on edge cuts detection
- Drill size validation
- Auto-fix suggestions for common issues

The module integrates with both KiCad's DRC engine and provides Python-based checks
for faster iteration during layout generation.
"""

import logging
import math
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from .placement.bbox import BoundingBox
from .types import Footprint, Pad, Point, Track, Via, Zone
from .validation import ValidationResult, ValidationSeverity, ValidationIssue

logger = logging.getLogger(__name__)


class DRCCategory(Enum):
    """Categories of DRC violations."""

    VIA_PLACEMENT = "via_placement"
    CLEARANCE = "clearance"
    TRACE_WIDTH = "trace_width"
    COPPER_EDGE = "copper_edge"
    DRILL_SIZE = "drill_size"
    SHORT_CIRCUIT = "short_circuit"
    ANNULAR_RING = "annular_ring"
    CONNECTIVITY = "connectivity"


@dataclass
class DRCRule:
    """Design rule definition."""

    name: str
    description: str
    enabled: bool = True
    auto_fix_available: bool = False

    # Rule parameters (mm unless noted)
    min_trace_width: float = 0.15
    min_trace_spacing: float = 0.15
    min_via_diameter: float = 0.4
    min_via_drill: float = 0.2
    min_via_annular_ring: float = 0.05
    min_clearance: float = 0.2
    min_drill_size: float = 0.15
    max_drill_size: float = 6.3
    edge_clearance: float = 0.5  # Clearance from edge cuts

    # Layer-specific rules (can be extended)
    layer_rules: Dict[str, Dict[str, float]] = field(default_factory=dict)


@dataclass
class DRCFix:
    """Suggested fix for a DRC violation."""

    issue_id: str
    fix_type: str
    description: str
    apply_function: Optional[callable] = None
    parameters: Dict[str, Any] = field(default_factory=dict)


class EnhancedDRCValidator:
    """
    Enhanced DRC validator with comprehensive checks and auto-fix capabilities.

    This validator extends the basic validation with specific checks required for
    automated PCB generation, including via placement, clearances, and manufacturing
    constraints.
    """

    def __init__(self, rules: Optional[DRCRule] = None):
        """
        Initialize the DRC validator with design rules.

        Args:
            rules: DRCRule object with design rules. If None, uses defaults.
        """
        self.rules = rules or DRCRule(
            name="default",
            description="Default design rules for automated PCB generation"
        )
        self.fixes: List[DRCFix] = []

    def validate_pcb(self, pcb_board) -> ValidationResult:
        """
        Perform comprehensive DRC validation on the PCB.

        Args:
            pcb_board: PCBBoard instance to validate

        Returns:
            ValidationResult with all found issues and suggested fixes
        """
        result = ValidationResult()
        self.fixes = []

        logger.info("Starting enhanced DRC validation...")

        # Run all DRC checks
        self._check_via_placement(pcb_board, result)
        self._check_clearances(pcb_board, result)
        self._check_trace_widths(pcb_board, result)
        self._check_copper_on_edge_cuts(pcb_board, result)
        self._check_drill_sizes(pcb_board, result)
        self._check_via_annular_rings(pcb_board, result)
        self._check_short_circuits(pcb_board, result)

        logger.info(f"DRC validation complete: {result.error_count} errors, "
                   f"{result.warning_count} warnings, {len(self.fixes)} fixes available")

        return result

    def _check_via_placement(self, pcb_board, result: ValidationResult):
        """
        Check that vias don't short to pads or traces they shouldn't connect to.

        Requirements from issue #225:
        - Via placement doesn't short to pads/traces
        - Via placement respects minimum clearances
        """
        vias = pcb_board.pcb_data.get("vias", [])
        footprints = pcb_board.pcb_data.get("footprints", [])
        tracks = pcb_board.pcb_data.get("tracks", [])

        logger.debug(f"Checking {len(vias)} vias for placement issues...")

        for via in vias:
            via_net = via.net if hasattr(via, "net") else None
            via_pos = via.position
            via_radius = via.size / 2 if hasattr(via, "size") else 0.3

            # Check clearance to pads on different nets
            for footprint in footprints:
                for pad in footprint.pads:
                    pad_net = pad.net if hasattr(pad, "net") else None

                    # Skip if same net (intentional connection)
                    if via_net is not None and pad_net is not None and via_net == pad_net:
                        continue

                    # Calculate pad position (relative to footprint)
                    pad_x = footprint.position.x + pad.position.x
                    pad_y = footprint.position.y + pad.position.y

                    # Calculate distance
                    distance = math.sqrt(
                        (via_pos.x - pad_x)**2 + (via_pos.y - pad_y)**2
                    )

                    # Get pad size
                    pad_radius = 0
                    if hasattr(pad, "size") and len(pad.size) >= 2:
                        # Use maximum dimension for circular approximation
                        pad_radius = max(pad.size[0], pad.size[1]) / 2

                    # Check clearance
                    required_clearance = via_radius + pad_radius + self.rules.min_clearance

                    if distance < required_clearance:
                        clearance_deficit = required_clearance - distance
                        result.add_error(
                            DRCCategory.VIA_PLACEMENT.value,
                            f"Via at ({via_pos.x:.2f}, {via_pos.y:.2f}) violates clearance "
                            f"to pad {footprint.reference}.{pad.number} by {clearance_deficit:.3f}mm",
                            via_pos,
                            [f"Via@{via_pos.x:.2f},{via_pos.y:.2f}",
                             f"{footprint.reference}.{pad.number}"]
                        )

                        # Suggest fix: move via
                        self.fixes.append(DRCFix(
                            issue_id=f"via_pad_clearance_{len(self.fixes)}",
                            fix_type="move_via",
                            description=f"Move via away from {footprint.reference}.{pad.number}",
                            parameters={
                                "via_position": (via_pos.x, via_pos.y),
                                "required_distance": clearance_deficit + 0.1  # 0.1mm margin
                            }
                        ))

            # Check clearance to traces on different nets
            for track in tracks:
                track_net = track.net if hasattr(track, "net") else None

                # Skip if same net
                if via_net is not None and track_net is not None and via_net == track_net:
                    continue

                # Calculate distance from via to track
                distance = self._point_to_line_distance(
                    via_pos,
                    track.start,
                    track.end
                )

                track_half_width = track.width / 2 if hasattr(track, "width") else 0.1
                required_clearance = via_radius + track_half_width + self.rules.min_clearance

                if distance < required_clearance:
                    clearance_deficit = required_clearance - distance
                    result.add_error(
                        DRCCategory.VIA_PLACEMENT.value,
                        f"Via at ({via_pos.x:.2f}, {via_pos.y:.2f}) violates clearance "
                        f"to track by {clearance_deficit:.3f}mm",
                        via_pos,
                        [f"Via@{via_pos.x:.2f},{via_pos.y:.2f}"]
                    )

    def _check_clearances(self, pcb_board, result: ValidationResult):
        """
        Validate minimum clearances between all copper features.

        Requirements from issue #225:
        - Validate minimum clearances between copper features
        """
        logger.debug("Checking copper clearances...")

        # Check pad-to-pad clearances
        self._check_pad_clearances(pcb_board, result)

        # Check track-to-track clearances
        self._check_track_clearances(pcb_board, result)

        # Check pad-to-track clearances
        self._check_pad_track_clearances(pcb_board, result)

    def _check_pad_clearances(self, pcb_board, result: ValidationResult):
        """Check clearances between pads on different nets."""
        footprints = pcb_board.pcb_data.get("footprints", [])

        # Build list of all pads with their global positions
        pads_info = []
        for footprint in footprints:
            for pad in footprint.pads:
                pad_x = footprint.position.x + pad.position.x
                pad_y = footprint.position.y + pad.position.y
                pad_net = pad.net if hasattr(pad, "net") else None

                pads_info.append({
                    "reference": f"{footprint.reference}.{pad.number}",
                    "position": Point(pad_x, pad_y),
                    "size": pad.size if hasattr(pad, "size") else (1.0, 1.0),
                    "net": pad_net,
                    "footprint_ref": footprint.reference
                })

        # Check all pad pairs
        for i, pad1 in enumerate(pads_info):
            for pad2 in pads_info[i+1:]:
                # Skip if same net
                if pad1["net"] is not None and pad2["net"] is not None and pad1["net"] == pad2["net"]:
                    continue

                # Calculate distance
                distance = math.sqrt(
                    (pad1["position"].x - pad2["position"].x)**2 +
                    (pad1["position"].y - pad2["position"].y)**2
                )

                # Calculate required clearance
                pad1_radius = max(pad1["size"][0], pad1["size"][1]) / 2
                pad2_radius = max(pad2["size"][0], pad2["size"][1]) / 2
                required_clearance = pad1_radius + pad2_radius + self.rules.min_clearance

                if distance < required_clearance:
                    clearance_deficit = required_clearance - distance
                    result.add_error(
                        DRCCategory.CLEARANCE.value,
                        f"Pad clearance violation: {pad1['reference']} to {pad2['reference']} "
                        f"(deficit: {clearance_deficit:.3f}mm)",
                        Point(
                            (pad1["position"].x + pad2["position"].x) / 2,
                            (pad1["position"].y + pad2["position"].y) / 2
                        ),
                        [pad1["reference"], pad2["reference"]]
                    )

    def _check_track_clearances(self, pcb_board, result: ValidationResult):
        """Check clearances between tracks on different nets."""
        tracks = pcb_board.pcb_data.get("tracks", [])

        for i, track1 in enumerate(tracks):
            track1_net = track1.net if hasattr(track1, "net") else None
            track1_width = track1.width if hasattr(track1, "width") else 0.15

            for track2 in tracks[i+1:]:
                track2_net = track2.net if hasattr(track2, "net") else None

                # Skip if same net
                if track1_net is not None and track2_net is not None and track1_net == track2_net:
                    continue

                # Calculate minimum distance between track segments
                distance = self._segment_to_segment_distance(
                    track1.start, track1.end,
                    track2.start, track2.end
                )

                track2_width = track2.width if hasattr(track2, "width") else 0.15
                required_clearance = (track1_width + track2_width) / 2 + self.rules.min_clearance

                if distance < required_clearance:
                    clearance_deficit = required_clearance - distance
                    result.add_error(
                        DRCCategory.CLEARANCE.value,
                        f"Track clearance violation (deficit: {clearance_deficit:.3f}mm)",
                        Point(
                            (track1.start.x + track2.start.x) / 2,
                            (track1.start.y + track2.start.y) / 2
                        )
                    )

    def _check_pad_track_clearances(self, pcb_board, result: ValidationResult):
        """Check clearances between pads and tracks on different nets."""
        footprints = pcb_board.pcb_data.get("footprints", [])
        tracks = pcb_board.pcb_data.get("tracks", [])

        for footprint in footprints:
            for pad in footprint.pads:
                pad_net = pad.net if hasattr(pad, "net") else None
                pad_x = footprint.position.x + pad.position.x
                pad_y = footprint.position.y + pad.position.y
                pad_pos = Point(pad_x, pad_y)

                for track in tracks:
                    track_net = track.net if hasattr(track, "net") else None

                    # Skip if same net
                    if pad_net is not None and track_net is not None and pad_net == track_net:
                        continue

                    # Calculate distance from pad to track
                    distance = self._point_to_line_distance(
                        pad_pos,
                        track.start,
                        track.end
                    )

                    pad_radius = max(pad.size[0], pad.size[1]) / 2 if hasattr(pad, "size") else 0.5
                    track_half_width = track.width / 2 if hasattr(track, "width") else 0.075
                    required_clearance = pad_radius + track_half_width + self.rules.min_clearance

                    if distance < required_clearance:
                        clearance_deficit = required_clearance - distance
                        result.add_error(
                            DRCCategory.CLEARANCE.value,
                            f"Pad-track clearance violation: {footprint.reference}.{pad.number} "
                            f"to track (deficit: {clearance_deficit:.3f}mm)",
                            pad_pos,
                            [f"{footprint.reference}.{pad.number}"]
                        )

    def _check_trace_widths(self, pcb_board, result: ValidationResult):
        """
        Check that all traces meet minimum width requirements.

        Requirements from issue #225:
        - Check trace width compliance
        """
        tracks = pcb_board.pcb_data.get("tracks", [])

        logger.debug(f"Checking {len(tracks)} tracks for width compliance...")

        for track in tracks:
            if not hasattr(track, "width"):
                result.add_error(
                    DRCCategory.TRACE_WIDTH.value,
                    f"Track at ({track.start.x:.2f}, {track.start.y:.2f}) has no width defined",
                    track.start
                )
                continue

            if track.width < self.rules.min_trace_width:
                width_deficit = self.rules.min_trace_width - track.width
                result.add_error(
                    DRCCategory.TRACE_WIDTH.value,
                    f"Track width {track.width:.3f}mm below minimum {self.rules.min_trace_width:.3f}mm "
                    f"(deficit: {width_deficit:.3f}mm)",
                    Point(
                        (track.start.x + track.end.x) / 2,
                        (track.start.y + track.end.y) / 2
                    )
                )

                # Suggest fix: increase track width
                self.fixes.append(DRCFix(
                    issue_id=f"track_width_{len(self.fixes)}",
                    fix_type="adjust_track_width",
                    description=f"Increase track width to {self.rules.min_trace_width}mm",
                    parameters={
                        "track_start": (track.start.x, track.start.y),
                        "track_end": (track.end.x, track.end.y),
                        "new_width": self.rules.min_trace_width
                    }
                ))

    def _check_copper_on_edge_cuts(self, pcb_board, result: ValidationResult):
        """
        Verify no copper features are on the edge cuts layer.

        Requirements from issue #225:
        - Verify no copper on edge cuts
        """
        logger.debug("Checking for copper on Edge.Cuts layer...")

        # Check footprints for pads on Edge.Cuts
        footprints = pcb_board.pcb_data.get("footprints", [])
        for footprint in footprints:
            for pad in footprint.pads:
                if hasattr(pad, "layers") and "Edge.Cuts" in pad.layers:
                    pad_x = footprint.position.x + pad.position.x
                    pad_y = footprint.position.y + pad.position.y
                    result.add_error(
                        DRCCategory.COPPER_EDGE.value,
                        f"Pad {footprint.reference}.{pad.number} has copper on Edge.Cuts layer",
                        Point(pad_x, pad_y),
                        [f"{footprint.reference}.{pad.number}"]
                    )

        # Check tracks on Edge.Cuts
        tracks = pcb_board.pcb_data.get("tracks", [])
        for track in tracks:
            if hasattr(track, "layer") and track.layer == "Edge.Cuts":
                result.add_error(
                    DRCCategory.COPPER_EDGE.value,
                    "Track found on Edge.Cuts layer",
                    Point(
                        (track.start.x + track.end.x) / 2,
                        (track.start.y + track.end.y) / 2
                    )
                )

        # Check clearance from edge cuts
        graphics = pcb_board.pcb_data.get("graphics", [])
        edge_cuts = [g for g in graphics if hasattr(g, "layer") and g.layer == "Edge.Cuts"]

        if edge_cuts:
            self._check_edge_clearances(pcb_board, edge_cuts, result)

    def _check_edge_clearances(self, pcb_board, edge_cuts, result: ValidationResult):
        """Check that copper features maintain clearance from board edges."""
        # This is a simplified check - full implementation would trace edge cut geometry

        # Get board outline bounds
        outline = pcb_board.get_board_outline()
        if not outline:
            return

        if "rect" in outline:
            board_min_x = outline["rect"]["x"]
            board_min_y = outline["rect"]["y"]
            board_max_x = outline["rect"]["x"] + outline["rect"]["width"]
            board_max_y = outline["rect"]["y"] + outline["rect"]["height"]
        else:
            return  # Complex outline, skip for now

        # Check footprints near edges
        footprints = pcb_board.pcb_data.get("footprints", [])
        for footprint in footprints:
            for pad in footprint.pads:
                pad_x = footprint.position.x + pad.position.x
                pad_y = footprint.position.y + pad.position.y

                # Calculate distance to nearest edge
                dist_to_edge = min(
                    abs(pad_x - board_min_x),
                    abs(pad_x - board_max_x),
                    abs(pad_y - board_min_y),
                    abs(pad_y - board_max_y)
                )

                if dist_to_edge < self.rules.edge_clearance:
                    result.add_warning(
                        DRCCategory.COPPER_EDGE.value,
                        f"Pad {footprint.reference}.{pad.number} within {dist_to_edge:.3f}mm "
                        f"of board edge (recommended: {self.rules.edge_clearance}mm)",
                        Point(pad_x, pad_y),
                        [f"{footprint.reference}.{pad.number}"]
                    )

    def _check_drill_sizes(self, pcb_board, result: ValidationResult):
        """
        Validate drill sizes are within manufacturing limits.

        Requirements from issue #225:
        - Validate drill sizes
        """
        logger.debug("Checking drill sizes...")

        # Check via drill sizes
        vias = pcb_board.pcb_data.get("vias", [])
        for via in vias:
            if hasattr(via, "drill"):
                if via.drill < self.rules.min_drill_size:
                    result.add_error(
                        DRCCategory.DRILL_SIZE.value,
                        f"Via drill size {via.drill:.3f}mm below minimum {self.rules.min_drill_size:.3f}mm",
                        via.position
                    )
                elif via.drill > self.rules.max_drill_size:
                    result.add_error(
                        DRCCategory.DRILL_SIZE.value,
                        f"Via drill size {via.drill:.3f}mm exceeds maximum {self.rules.max_drill_size:.3f}mm",
                        via.position
                    )

        # Check pad drill sizes (for through-hole pads)
        footprints = pcb_board.pcb_data.get("footprints", [])
        for footprint in footprints:
            for pad in footprint.pads:
                if hasattr(pad, "drill") and pad.drill is not None:
                    if pad.drill < self.rules.min_drill_size:
                        pad_x = footprint.position.x + pad.position.x
                        pad_y = footprint.position.y + pad.position.y
                        result.add_error(
                            DRCCategory.DRILL_SIZE.value,
                            f"Pad {footprint.reference}.{pad.number} drill size {pad.drill:.3f}mm "
                            f"below minimum {self.rules.min_drill_size:.3f}mm",
                            Point(pad_x, pad_y),
                            [f"{footprint.reference}.{pad.number}"]
                        )
                    elif pad.drill > self.rules.max_drill_size:
                        pad_x = footprint.position.x + pad.position.x
                        pad_y = footprint.position.y + pad.position.y
                        result.add_error(
                            DRCCategory.DRILL_SIZE.value,
                            f"Pad {footprint.reference}.{pad.number} drill size {pad.drill:.3f}mm "
                            f"exceeds maximum {self.rules.max_drill_size:.3f}mm",
                            Point(pad_x, pad_y),
                            [f"{footprint.reference}.{pad.number}"]
                        )

    def _check_via_annular_rings(self, pcb_board, result: ValidationResult):
        """Check that vias have sufficient annular ring (copper around drill)."""
        vias = pcb_board.pcb_data.get("vias", [])

        for via in vias:
            if hasattr(via, "size") and hasattr(via, "drill"):
                annular_ring = (via.size - via.drill) / 2

                if annular_ring < self.rules.min_via_annular_ring:
                    result.add_error(
                        DRCCategory.ANNULAR_RING.value,
                        f"Via annular ring {annular_ring:.3f}mm below minimum "
                        f"{self.rules.min_via_annular_ring:.3f}mm",
                        via.position
                    )

                    # Suggest fix: increase via size
                    new_size = via.drill + 2 * self.rules.min_via_annular_ring
                    self.fixes.append(DRCFix(
                        issue_id=f"via_annular_{len(self.fixes)}",
                        fix_type="adjust_via_size",
                        description=f"Increase via diameter to {new_size:.3f}mm",
                        parameters={
                            "via_position": (via.position.x, via.position.y),
                            "new_size": new_size
                        }
                    ))

    def _check_short_circuits(self, pcb_board, result: ValidationResult):
        """
        Check for potential short circuits (copper touching on different nets).
        This is a basic check - full verification requires DRC from KiCad.
        """
        logger.debug("Checking for potential short circuits...")

        # This would be implemented with more sophisticated algorithms
        # For now, we rely on the clearance checks above
        # KiCad's DRC is more comprehensive for actual short circuit detection

        result.add_info(
            DRCCategory.SHORT_CIRCUIT.value,
            "Short circuit detection requires full KiCad DRC for comprehensive results. "
            "Run pcb.run_drc() for complete validation."
        )

    # Utility methods for geometric calculations

    def _point_to_line_distance(self, point: Point, line_start: Point, line_end: Point) -> float:
        """Calculate minimum distance from a point to a line segment."""
        # Vector from line_start to line_end
        dx = line_end.x - line_start.x
        dy = line_end.y - line_start.y

        # Line segment length squared
        length_sq = dx*dx + dy*dy

        if length_sq == 0:
            # Line is actually a point
            return math.sqrt(
                (point.x - line_start.x)**2 + (point.y - line_start.y)**2
            )

        # Parameter t represents position along line (0 = start, 1 = end)
        t = max(0, min(1, (
            (point.x - line_start.x) * dx + (point.y - line_start.y) * dy
        ) / length_sq))

        # Find closest point on line segment
        closest_x = line_start.x + t * dx
        closest_y = line_start.y + t * dy

        # Return distance to closest point
        return math.sqrt(
            (point.x - closest_x)**2 + (point.y - closest_y)**2
        )

    def _segment_to_segment_distance(
        self,
        seg1_start: Point, seg1_end: Point,
        seg2_start: Point, seg2_end: Point
    ) -> float:
        """Calculate minimum distance between two line segments."""
        # Check all endpoint-to-segment distances
        distances = [
            self._point_to_line_distance(seg1_start, seg2_start, seg2_end),
            self._point_to_line_distance(seg1_end, seg2_start, seg2_end),
            self._point_to_line_distance(seg2_start, seg1_start, seg1_end),
            self._point_to_line_distance(seg2_end, seg1_start, seg1_end),
        ]

        return min(distances)

    def get_suggested_fixes(self) -> List[DRCFix]:
        """
        Get list of suggested fixes for found violations.

        Returns:
            List of DRCFix objects with suggested corrections
        """
        return self.fixes

    def apply_fix(self, pcb_board, fix: DRCFix) -> bool:
        """
        Apply a suggested fix to the PCB.

        Args:
            pcb_board: PCBBoard instance
            fix: DRCFix object to apply

        Returns:
            True if fix was applied successfully
        """
        if not fix.apply_function:
            logger.warning(f"No apply function for fix: {fix.description}")
            return False

        try:
            fix.apply_function(pcb_board, **fix.parameters)
            logger.info(f"Applied fix: {fix.description}")
            return True
        except Exception as e:
            logger.error(f"Failed to apply fix: {e}")
            return False


def run_enhanced_drc(pcb_board, rules: Optional[DRCRule] = None) -> Tuple[ValidationResult, List[DRCFix]]:
    """
    Convenience function to run enhanced DRC validation.

    Args:
        pcb_board: PCBBoard instance to validate
        rules: Optional DRCRule object with custom design rules

    Returns:
        Tuple of (ValidationResult, List of suggested fixes)
    """
    validator = EnhancedDRCValidator(rules)
    result = validator.validate_pcb(pcb_board)
    fixes = validator.get_suggested_fixes()

    return result, fixes
