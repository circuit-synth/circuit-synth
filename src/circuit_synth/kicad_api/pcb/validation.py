"""
PCB validation module for checking design rules and constraints.

This module provides comprehensive validation of PCB designs including:
- Component placement validation
- Board outline checks
- Net connectivity verification
- Spacing and clearance checks
"""

import logging
import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from .placement.bbox import BoundingBox
from .types import Footprint, Pad, Point, Track, Via, Zone

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """Represents a single validation issue."""

    severity: ValidationSeverity
    category: str
    message: str
    location: Optional[Point] = None
    affected_items: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        """String representation of the issue."""
        loc_str = (
            f" at ({self.location.x:.2f}, {self.location.y:.2f})"
            if self.location
            else ""
        )
        items_str = (
            f" [{', '.join(self.affected_items)}]" if self.affected_items else ""
        )
        return f"{self.severity.value.upper()}: {self.category} - {self.message}{loc_str}{items_str}"


@dataclass
class ValidationResult:
    """Results of PCB validation."""

    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """Check if there are no errors."""
        return not any(
            issue.severity == ValidationSeverity.ERROR for issue in self.issues
        )

    @property
    def error_count(self) -> int:
        """Count of error-level issues."""
        return sum(
            1 for issue in self.issues if issue.severity == ValidationSeverity.ERROR
        )

    @property
    def warning_count(self) -> int:
        """Count of warning-level issues."""
        return sum(
            1 for issue in self.issues if issue.severity == ValidationSeverity.WARNING
        )

    @property
    def info_count(self) -> int:
        """Count of info-level issues."""
        return sum(
            1 for issue in self.issues if issue.severity == ValidationSeverity.INFO
        )

    def add_error(
        self,
        category: str,
        message: str,
        location: Optional[Point] = None,
        affected_items: Optional[List[str]] = None,
    ):
        """Add an error-level issue."""
        self.issues.append(
            ValidationIssue(
                ValidationSeverity.ERROR,
                category,
                message,
                location,
                affected_items or [],
            )
        )

    def add_warning(
        self,
        category: str,
        message: str,
        location: Optional[Point] = None,
        affected_items: Optional[List[str]] = None,
    ):
        """Add a warning-level issue."""
        self.issues.append(
            ValidationIssue(
                ValidationSeverity.WARNING,
                category,
                message,
                location,
                affected_items or [],
            )
        )

    def add_info(
        self,
        category: str,
        message: str,
        location: Optional[Point] = None,
        affected_items: Optional[List[str]] = None,
    ):
        """Add an info-level issue."""
        self.issues.append(
            ValidationIssue(
                ValidationSeverity.INFO,
                category,
                message,
                location,
                affected_items or [],
            )
        )

    def print_summary(self):
        """Print a summary of validation results."""
        logger.info("VALIDATION", "Validation Summary:")
        logger.info(
            "VALIDATION", f"Errors: {self.error_count}", error_count=self.error_count
        )
        logger.info(
            "VALIDATION",
            f"Warnings: {self.warning_count}",
            warning_count=self.warning_count,
        )
        logger.info(
            "VALIDATION", f"Info: {self.info_count}", info_count=self.info_count
        )
        logger.info(
            "VALIDATION",
            f"Valid: {'Yes' if self.is_valid else 'No'}",
            is_valid=self.is_valid,
        )

        if self.issues:
            logger.info("VALIDATION", "Issues:")
            for issue in self.issues:
                logger.info("VALIDATION", f"{issue}", issue=str(issue))


class PCBValidator:
    """Validates PCB design rules and constraints."""

    def __init__(
        self,
        min_trace_width: float = 0.15,
        min_via_diameter: float = 0.3,
        min_via_drill: float = 0.2,
        min_clearance: float = 0.2,
        min_component_spacing: float = 0.5,
    ):
        """
        Initialize validator with design rules.

        Args:
            min_trace_width: Minimum track width in mm
            min_via_diameter: Minimum via diameter in mm
            min_via_drill: Minimum via drill size in mm
            min_clearance: Minimum clearance between copper features in mm
            min_component_spacing: Minimum spacing between components in mm
        """
        self.min_trace_width = min_trace_width
        self.min_via_diameter = min_via_diameter
        self.min_via_drill = min_via_drill
        self.min_clearance = min_clearance
        self.min_component_spacing = min_component_spacing

    def validate_board(self, pcb_board) -> ValidationResult:
        """
        Perform comprehensive validation of the PCB.

        Args:
            pcb_board: PCBBoard instance to validate

        Returns:
            ValidationResult with all found issues
        """
        result = ValidationResult()

        # Run all validation checks
        self._validate_board_outline(pcb_board, result)
        self._validate_component_placement(pcb_board, result)
        self._validate_overlapping_footprints(pcb_board, result)
        self._validate_net_connectivity(pcb_board, result)
        self._validate_tracks(pcb_board, result)
        self._validate_vias(pcb_board, result)
        self._validate_zones(pcb_board, result)
        self._validate_isolated_copper(pcb_board, result)

        return result

    def _validate_board_outline(self, pcb_board, result: ValidationResult):
        """Check if board outline is defined and valid."""
        outline = pcb_board.get_board_outline()

        if not outline:
            result.add_error("Board Outline", "No board outline defined")
            return

        # Check if outline forms a closed shape
        if "polygon" in outline:
            points = outline["polygon"]
            if len(points) < 3:
                result.add_error(
                    "Board Outline", "Polygon outline has less than 3 points"
                )
            elif points[0] != points[-1]:
                # Check if first and last points are close enough to be considered closed
                first = points[0]
                last = points[-1]
                dist = math.sqrt((first[0] - last[0]) ** 2 + (first[1] - last[1]) ** 2)
                if dist > 0.01:  # 0.01mm tolerance
                    result.add_warning("Board Outline", "Polygon outline is not closed")

    def _validate_component_placement(self, pcb_board, result: ValidationResult):
        """Check if all components are within board outline."""
        outline = pcb_board.get_board_outline()
        if not outline:
            return  # Can't check without outline

        # Get board bounds
        if "rect" in outline:
            rect = outline["rect"]
            board_min_x = rect["x"]
            board_min_y = rect["y"]
            board_max_x = rect["x"] + rect["width"]
            board_max_y = rect["y"] + rect["height"]
        elif "polygon" in outline:
            points = outline["polygon"]
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            board_min_x = min(xs)
            board_min_y = min(ys)
            board_max_x = max(xs)
            board_max_y = max(ys)
        else:
            return

        # Check each footprint
        for footprint in pcb_board.footprints:
            # Get footprint bounding box
            bbox = self._get_footprint_bbox(footprint)

            # Check if footprint is within board
            if (
                bbox.min_x < board_min_x
                or bbox.max_x > board_max_x
                or bbox.min_y < board_min_y
                or bbox.max_y > board_max_y
            ):
                result.add_error(
                    "Component Placement",
                    f"Component {footprint.reference} extends outside board outline",
                    footprint.position,
                    [footprint.reference],
                )

            # Check if footprint is too close to board edge
            edge_clearance = 1.0  # 1mm clearance from edge
            if (
                bbox.min_x < board_min_x + edge_clearance
                or bbox.max_x > board_max_x - edge_clearance
                or bbox.min_y < board_min_y + edge_clearance
                or bbox.max_y > board_max_y - edge_clearance
            ):
                result.add_warning(
                    "Component Placement",
                    f"Component {footprint.reference} is within {edge_clearance}mm of board edge",
                    footprint.position,
                    [footprint.reference],
                )

    def _validate_overlapping_footprints(self, pcb_board, result: ValidationResult):
        """Check for overlapping components."""
        footprints = pcb_board.footprints

        for i, fp1 in enumerate(footprints):
            bbox1 = self._get_footprint_bbox(fp1)

            for fp2 in footprints[i + 1 :]:
                bbox2 = self._get_footprint_bbox(fp2)

                # Check for overlap
                if bbox1.intersects(bbox2):
                    result.add_error(
                        "Component Overlap",
                        f"Components {fp1.reference} and {fp2.reference} overlap",
                        Point(
                            (fp1.position.x + fp2.position.x) / 2,
                            (fp1.position.y + fp2.position.y) / 2,
                        ),
                        [fp1.reference, fp2.reference],
                    )
                else:
                    # Check spacing
                    spacing = self._bbox_spacing(bbox1, bbox2)
                    if spacing < self.min_component_spacing:
                        result.add_warning(
                            "Component Spacing",
                            f"Components {fp1.reference} and {fp2.reference} are only {spacing:.2f}mm apart",
                            Point(
                                (fp1.position.x + fp2.position.x) / 2,
                                (fp1.position.y + fp2.position.y) / 2,
                            ),
                            [fp1.reference, fp2.reference],
                        )

    def _validate_net_connectivity(self, pcb_board, result: ValidationResult):
        """Validate net connectivity and check for unconnected pads."""
        # Get all nets
        nets = pcb_board.pcb_data.get("nets", [])
        net_map = {net.number: net for net in nets}

        # Check each footprint's pads
        connected_pads = set()
        for net in nets:
            for pad_ref in net.pads:
                connected_pads.add(pad_ref)

        # Find unconnected pads
        for footprint in pcb_board.footprints:
            for pad in footprint.pads:
                pad_ref = f"{footprint.reference}.{pad.number}"
                if pad_ref not in connected_pads and pad.type != "np_thru_hole":
                    # Some pads are intentionally unconnected (like mounting holes)
                    if not pad.number.startswith("MP") and pad.number != "":
                        result.add_warning(
                            "Connectivity",
                            f"Pad {pad_ref} is not connected to any net",
                            Point(
                                footprint.position.x + pad.position.x,
                                footprint.position.y + pad.position.y,
                            ),
                            [pad_ref],
                        )

        # Check for single-pad nets (usually an error)
        for net in nets:
            if len(net.pads) == 1 and net.name not in ["GND", "VCC", "+3V3", "+5V"]:
                result.add_warning(
                    "Connectivity",
                    f"Net '{net.name}' has only one connection",
                    None,
                    net.pads,
                )

    def _validate_tracks(self, pcb_board, result: ValidationResult):
        """Validate track width and clearances."""
        tracks = pcb_board.pcb_data.get("tracks", [])

        for track in tracks:
            # Check track width
            if track.width < self.min_trace_width:
                result.add_error(
                    "Track Width",
                    f"Track width {track.width}mm is below minimum {self.min_trace_width}mm",
                    Point(
                        (track.start.x + track.end.x) / 2,
                        (track.start.y + track.end.y) / 2,
                    ),
                )

            # TODO: Check track clearances (requires spatial indexing for efficiency)

    def _validate_vias(self, pcb_board, result: ValidationResult):
        """Validate via dimensions."""
        vias = pcb_board.pcb_data.get("vias", [])

        for via in vias:
            # Check via diameter
            if via.size < self.min_via_diameter:
                result.add_error(
                    "Via Size",
                    f"Via diameter {via.size}mm is below minimum {self.min_via_diameter}mm",
                    via.position,
                )

            # Check drill size
            if via.drill < self.min_via_drill:
                result.add_error(
                    "Via Drill",
                    f"Via drill {via.drill}mm is below minimum {self.min_via_drill}mm",
                    via.position,
                )

            # Check annular ring
            annular_ring = (via.size - via.drill) / 2
            min_annular_ring = 0.05  # 0.05mm minimum
            if annular_ring < min_annular_ring:
                result.add_error(
                    "Via Annular Ring",
                    f"Via annular ring {annular_ring:.3f}mm is below minimum {min_annular_ring}mm",
                    via.position,
                )

    def _validate_zones(self, pcb_board, result: ValidationResult):
        """Validate zone definitions."""
        zones = pcb_board.pcb_data.get("zones", [])

        for zone in zones:
            # Check if zone has valid polygon
            if not zone.polygon or len(zone.polygon) < 3:
                result.add_error(
                    "Zone Definition",
                    f"Zone on layer {zone.layer} has invalid polygon",
                    None,
                )

            # Check if zone is connected to a net (unless it's a keepout)
            if not zone.net_name and not zone.keepout:
                result.add_warning(
                    "Zone Connectivity",
                    f"Zone on layer {zone.layer} is not connected to any net",
                    None,
                )

    def _validate_isolated_copper(self, pcb_board, result: ValidationResult):
        """Check for isolated copper islands."""
        # This is a complex check that would require flood-fill algorithms
        # For now, just add an info message
        zones = pcb_board.pcb_data.get("zones", [])
        if zones:
            result.add_info(
                "Isolated Copper",
                "Isolated copper check requires running KiCad DRC for accurate results",
                None,
            )

    def _get_footprint_bbox(self, footprint: Footprint) -> BoundingBox:
        """Calculate bounding box for a footprint including all pads."""
        bbox = BoundingBox()

        # Add footprint position as center
        bbox.add_point(footprint.position.x, footprint.position.y)

        # Add all pad positions
        for pad in footprint.pads:
            # Pad position is relative to footprint
            pad_x = footprint.position.x + pad.position.x
            pad_y = footprint.position.y + pad.position.y

            # Add pad corners based on size
            if hasattr(pad, "size") and len(pad.size) >= 2:
                half_width = pad.size[0] / 2
                half_height = pad.size[1] / 2
                bbox.add_point(pad_x - half_width, pad_y - half_height)
                bbox.add_point(pad_x + half_width, pad_y + half_height)
            else:
                bbox.add_point(pad_x, pad_y)

        # Add some margin for courtyard
        margin = 0.5  # 0.5mm margin
        bbox.min_x -= margin
        bbox.min_y -= margin
        bbox.max_x += margin
        bbox.max_y += margin

        return bbox

    def _bbox_spacing(self, bbox1: BoundingBox, bbox2: BoundingBox) -> float:
        """Calculate minimum spacing between two bounding boxes."""
        # Calculate gaps in each direction
        x_gap = max(0, max(bbox1.min_x, bbox2.min_x) - min(bbox1.max_x, bbox2.max_x))
        y_gap = max(0, max(bbox1.min_y, bbox2.min_y) - min(bbox1.max_y, bbox2.max_y))

        # Return minimum gap
        if x_gap > 0 and y_gap > 0:
            # Diagonal separation
            return math.sqrt(x_gap**2 + y_gap**2)
        else:
            # Direct separation
            return max(x_gap, y_gap)


def validate_pcb(pcb_board, **kwargs) -> ValidationResult:
    """
    Convenience function to validate a PCB board.

    Args:
        pcb_board: PCBBoard instance to validate
        **kwargs: Optional design rule parameters

    Returns:
        ValidationResult with all found issues
    """
    validator = PCBValidator(**kwargs)
    return validator.validate_board(pcb_board)
