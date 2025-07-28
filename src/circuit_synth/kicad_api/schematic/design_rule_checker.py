"""Design rule checking for schematics."""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from ..core.types import Junction, Label, Point
from ..core.types import SchematicSymbol as Component
from ..core.types import Wire


@dataclass
class Position:
    x: float
    y: float
    angle: float


@dataclass
class NoConnect:
    at: Position
    uuid: str = ""


from .connection_tracer import ConnectionTracer
from .net_discovery import NetDiscovery


class RuleSeverity(Enum):
    """Severity levels for rule violations."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class RuleCategory(Enum):
    """Categories of design rules."""

    ELECTRICAL = "electrical"
    NAMING = "naming"
    PLACEMENT = "placement"
    CONNECTIVITY = "connectivity"
    ANNOTATION = "annotation"
    STYLE = "style"


@dataclass
class RuleViolation:
    """Represents a design rule violation."""

    rule_name: str
    severity: RuleSeverity
    category: RuleCategory
    message: str
    elements: List[Any]  # Components, wires, etc involved
    location: Optional[Position] = None
    suggestion: Optional[str] = None

    def __str__(self) -> str:
        """String representation."""
        elements_str = ", ".join(str(e) for e in self.elements[:3])
        if len(self.elements) > 3:
            elements_str += f" and {len(self.elements) - 3} more"

        result = f"[{self.severity.value.upper()}] {self.rule_name}: {self.message}"
        if elements_str:
            result += f" (Elements: {elements_str})"
        if self.suggestion:
            result += f"\n  Suggestion: {self.suggestion}"
        return result


@dataclass
class DesignRules:
    """Configuration for design rules."""

    # Electrical rules
    check_unconnected_pins: bool = True
    check_floating_nets: bool = True
    check_power_pins: bool = True
    check_duplicate_references: bool = True
    check_missing_references: bool = True

    # Naming rules
    reference_pattern: Optional[str] = r"^[A-Z]+\d+$"  # e.g., R1, C2, U3
    net_name_pattern: Optional[str] = r"^[A-Z][A-Z0-9_]*$"  # e.g., VCC, GND, DATA_BUS
    min_net_name_length: int = 2
    max_net_name_length: int = 32

    # Placement rules
    min_component_spacing: float = 2.54  # mm
    check_overlapping_components: bool = True
    check_off_grid: bool = True
    grid_size: float = 2.54  # mm

    # Connectivity rules
    max_wire_length: float = 254.0  # mm (10 inches)
    check_wire_junctions: bool = True
    check_bus_connections: bool = True

    # Annotation rules
    check_missing_values: bool = True
    check_missing_footprints: bool = True
    required_properties: List[str] = field(
        default_factory=lambda: ["Reference", "Value"]
    )

    # Style rules
    check_text_size: bool = True
    min_text_size: float = 1.0  # mm
    max_text_size: float = 5.0  # mm


class DesignRuleChecker:
    """Checks schematic against design rules."""

    def __init__(self, rules: Optional[DesignRules] = None):
        """Initialize with rules."""
        self.rules = rules or DesignRules()
        self.violations: List[RuleViolation] = []

    def check_schematic(
        self,
        components: List[Component],
        wires: List[Wire],
        junctions: List[Junction],
        labels: List[Label],
        no_connects: List[NoConnect],
    ) -> List[RuleViolation]:
        """Run all checks on schematic."""
        self.violations = []

        # Electrical checks
        if self.rules.check_unconnected_pins:
            self._check_unconnected_pins(components, wires, no_connects)

        if self.rules.check_floating_nets:
            self._check_floating_nets(components, wires, labels)

        if self.rules.check_power_pins:
            self._check_power_pins(components)

        # Reference checks
        if self.rules.check_duplicate_references:
            self._check_duplicate_references(components)

        if self.rules.check_missing_references:
            self._check_missing_references(components)

        # Naming checks
        if self.rules.reference_pattern:
            self._check_reference_naming(components)

        if self.rules.net_name_pattern:
            self._check_net_naming(labels)

        # Placement checks
        if self.rules.check_overlapping_components:
            self._check_overlapping_components(components)

        if self.rules.check_off_grid:
            self._check_off_grid(components, wires, junctions)

        # Connectivity checks
        if self.rules.max_wire_length:
            self._check_wire_length(wires)

        if self.rules.check_wire_junctions:
            self._check_wire_junctions(wires, junctions)

        # Annotation checks
        if self.rules.check_missing_values:
            self._check_missing_values(components)

        if self.rules.check_missing_footprints:
            self._check_missing_footprints(components)

        if self.rules.required_properties:
            self._check_required_properties(components)

        # Style checks
        if self.rules.check_text_size:
            self._check_text_size(components, labels)

        return self.violations

    def _add_violation(self, violation: RuleViolation):
        """Add a violation to the list."""
        self.violations.append(violation)

    def _check_unconnected_pins(
        self,
        components: List[Component],
        wires: List[Wire],
        no_connects: List[NoConnect],
    ):
        """Check for unconnected pins."""
        # Build connection map
        from ..core.types import Schematic

        temp_schematic = Schematic()
        temp_schematic.components = components
        temp_schematic.wires = wires
        tracer = ConnectionTracer(temp_schematic)
        graph = tracer.graph  # Graph is built in constructor

        # Get no-connect positions
        nc_positions = {(nc.at.x, nc.at.y) for nc in no_connects}

        # Check each component pin
        for comp in components:
            if not hasattr(comp, "pins"):
                continue

            for pin in comp.pins:
                if not hasattr(pin, "position"):
                    continue

                pin_pos = (pin.position.x, pin.position.y)

                # Skip if marked with no-connect
                if pin_pos in nc_positions:
                    continue

                # Check if connected (simplified check)
                # In a real implementation, we'd trace through the graph
                # For now, just check if there's a node at the pin position
                connected = False
                for node in graph.nodes.values():
                    if (
                        abs(node.position.x - pin_pos[0]) < 0.01
                        and abs(node.position.y - pin_pos[1]) < 0.01
                    ):
                        # Check if node has connections
                        if len(node.connected_elements) > 1:
                            connected = True
                            break

                if not connected:
                    # Special handling for power pins
                    if (
                        hasattr(pin, "electrical_type")
                        and pin.electrical_type == "power_in"
                    ):
                        severity = RuleSeverity.ERROR
                        message = f"Power pin {pin.name} is not connected"
                    else:
                        severity = RuleSeverity.WARNING
                        message = f"Pin {pin.number} ({pin.name}) is not connected"

                    self._add_violation(
                        RuleViolation(
                            rule_name="unconnected_pin",
                            severity=severity,
                            category=RuleCategory.ELECTRICAL,
                            message=message,
                            elements=[comp],
                            location=(
                                pin.position
                                if hasattr(pin, "position")
                                else comp.position
                            ),
                            suggestion="Connect pin or add no-connect symbol",
                        )
                    )

    def _check_floating_nets(
        self, components: List[Component], wires: List[Wire], labels: List[Label]
    ):
        """Check for floating nets (nets with only one connection)."""
        from ..core.types import Schematic

        temp_schematic = Schematic()
        temp_schematic.components = components
        temp_schematic.wires = wires
        temp_schematic.labels = labels
        discovery = NetDiscovery(temp_schematic)
        nets = discovery.discover_all_nets()

        for net in nets:
            # Count connections
            connection_count = len(net.component_pins)

            # Skip power/ground nets
            if net.name and net.name.upper() in ["VCC", "VDD", "GND", "VSS"]:
                continue

            if connection_count == 1:
                comp_ref, pin_num = net.component_pins[0]
                comp = next((c for c in components if c.reference == comp_ref), None)

                self._add_violation(
                    RuleViolation(
                        rule_name="floating_net",
                        severity=RuleSeverity.WARNING,
                        category=RuleCategory.ELECTRICAL,
                        message=f"Net has only one connection at {comp_ref} pin {pin_num}",
                        elements=[comp] if comp else [],
                        suggestion="Add more connections or remove if not needed",
                    )
                )

    def _check_power_pins(self, components: List[Component]):
        """Check power pin connections."""
        power_net_names = {"VCC", "VDD", "VSS", "GND", "AGND", "DGND"}

        for comp in components:
            if not hasattr(comp, "pins"):
                continue

            for pin in comp.pins:
                if not hasattr(pin, "electrical_type"):
                    continue

                # Check power pins
                if pin.electrical_type in ["power_in", "power_out"]:
                    if hasattr(pin, "net") and pin.net:
                        net_name = pin.net.upper()
                        if not any(pwr in net_name for pwr in power_net_names):
                            self._add_violation(
                                RuleViolation(
                                    rule_name="power_pin_net",
                                    severity=RuleSeverity.WARNING,
                                    category=RuleCategory.ELECTRICAL,
                                    message=f"Power pin {pin.name} connected to non-power net '{pin.net}'",
                                    elements=[comp],
                                    location=comp.position,
                                    suggestion=f"Connect to a power net like {', '.join(power_net_names)}",
                                )
                            )

    def _check_duplicate_references(self, components: List[Component]):
        """Check for duplicate reference designators."""
        ref_map: Dict[str, List[Component]] = {}

        for comp in components:
            ref = comp.reference
            if ref and ref != "?":
                if ref not in ref_map:
                    ref_map[ref] = []
                ref_map[ref].append(comp)

        for ref, comps in ref_map.items():
            if len(comps) > 1:
                self._add_violation(
                    RuleViolation(
                        rule_name="duplicate_reference",
                        severity=RuleSeverity.ERROR,
                        category=RuleCategory.ANNOTATION,
                        message=f"Reference '{ref}' used by {len(comps)} components",
                        elements=comps,
                        suggestion="Ensure each component has a unique reference",
                    )
                )

    def _check_missing_references(self, components: List[Component]):
        """Check for missing reference designators."""
        for comp in components:
            if (
                not comp.reference
                or comp.reference == "?"
                or comp.reference.endswith("?")
            ):
                self._add_violation(
                    RuleViolation(
                        rule_name="missing_reference",
                        severity=RuleSeverity.ERROR,
                        category=RuleCategory.ANNOTATION,
                        message=f"Component has missing or incomplete reference '{comp.reference}'",
                        elements=[comp],
                        location=comp.position,
                        suggestion="Annotate schematic to assign reference designators",
                    )
                )

    def _check_reference_naming(self, components: List[Component]):
        """Check reference naming convention."""
        pattern = re.compile(self.rules.reference_pattern)

        for comp in components:
            if (
                comp.reference
                and comp.reference != "?"
                and not pattern.match(comp.reference)
            ):
                self._add_violation(
                    RuleViolation(
                        rule_name="reference_naming",
                        severity=RuleSeverity.WARNING,
                        category=RuleCategory.NAMING,
                        message=f"Reference '{comp.reference}' doesn't match pattern '{self.rules.reference_pattern}'",
                        elements=[comp],
                        location=comp.position,
                        suggestion="Use standard format like R1, C2, U3",
                    )
                )

    def _check_net_naming(self, labels: List[Label]):
        """Check net naming convention."""
        if not self.rules.net_name_pattern:
            return

        pattern = re.compile(self.rules.net_name_pattern)

        for label in labels:
            net_name = label.text

            # Check pattern
            if not pattern.match(net_name):
                self._add_violation(
                    RuleViolation(
                        rule_name="net_naming_pattern",
                        severity=RuleSeverity.WARNING,
                        category=RuleCategory.NAMING,
                        message=f"Net name '{net_name}' doesn't match pattern '{self.rules.net_name_pattern}'",
                        elements=[label],
                        location=label.at,
                        suggestion="Use uppercase with underscores, e.g., DATA_BUS",
                    )
                )

            # Check length
            if len(net_name) < self.rules.min_net_name_length:
                self._add_violation(
                    RuleViolation(
                        rule_name="net_name_too_short",
                        severity=RuleSeverity.WARNING,
                        category=RuleCategory.NAMING,
                        message=f"Net name '{net_name}' is too short (min {self.rules.min_net_name_length} chars)",
                        elements=[label],
                        location=label.at,
                    )
                )

            if len(net_name) > self.rules.max_net_name_length:
                self._add_violation(
                    RuleViolation(
                        rule_name="net_name_too_long",
                        severity=RuleSeverity.WARNING,
                        category=RuleCategory.NAMING,
                        message=f"Net name '{net_name}' is too long (max {self.rules.max_net_name_length} chars)",
                        elements=[label],
                        location=label.at,
                    )
                )

    def _check_overlapping_components(self, components: List[Component]):
        """Check for overlapping components."""
        # Simple bounding box check
        for i, comp1 in enumerate(components):
            for comp2 in components[i + 1 :]:
                # Check if positions are too close
                dx = abs(comp1.position.x - comp2.position.x)
                dy = abs(comp1.position.y - comp2.position.y)

                if (
                    dx < self.rules.min_component_spacing
                    and dy < self.rules.min_component_spacing
                ):
                    self._add_violation(
                        RuleViolation(
                            rule_name="overlapping_components",
                            severity=RuleSeverity.ERROR,
                            category=RuleCategory.PLACEMENT,
                            message=f"Components {comp1.reference} and {comp2.reference} are overlapping or too close",
                            elements=[comp1, comp2],
                            location=comp1.position,
                            suggestion=f"Maintain at least {self.rules.min_component_spacing}mm spacing",
                        )
                    )

    def _check_off_grid(
        self, components: List[Component], wires: List[Wire], junctions: List[Junction]
    ):
        """Check for off-grid placement."""
        grid = self.rules.grid_size

        def is_on_grid(x: float, y: float) -> bool:
            """Check if position is on grid."""
            return abs(x % grid) < 0.01 and abs(y % grid) < 0.01

        # Check components
        for comp in components:
            if not is_on_grid(comp.position.x, comp.position.y):
                self._add_violation(
                    RuleViolation(
                        rule_name="off_grid_component",
                        severity=RuleSeverity.WARNING,
                        category=RuleCategory.PLACEMENT,
                        message=f"Component {comp.reference} is off grid at ({comp.position.x}, {comp.position.y})",
                        elements=[comp],
                        location=comp.position,
                        suggestion=f"Snap to {grid}mm grid",
                    )
                )

        # Check wire endpoints
        for wire in wires:
            if not is_on_grid(wire.points[0].x, wire.points[0].y):
                self._add_violation(
                    RuleViolation(
                        rule_name="off_grid_wire",
                        severity=RuleSeverity.WARNING,
                        category=RuleCategory.PLACEMENT,
                        message=f"Wire start point is off grid at ({wire.points[0].x}, {wire.points[0].y})",
                        elements=[wire],
                        location=wire.points[0],
                        suggestion=f"Snap to {grid}mm grid",
                    )
                )

            if not is_on_grid(wire.points[-1].x, wire.points[-1].y):
                self._add_violation(
                    RuleViolation(
                        rule_name="off_grid_wire",
                        severity=RuleSeverity.WARNING,
                        category=RuleCategory.PLACEMENT,
                        message=f"Wire end point is off grid at ({wire.points[-1].x}, {wire.points[-1].y})",
                        elements=[wire],
                        location=wire.points[-1],
                        suggestion=f"Snap to {grid}mm grid",
                    )
                )

    def _check_wire_length(self, wires: List[Wire]):
        """Check for excessively long wires."""
        max_length = self.rules.max_wire_length

        for wire in wires:
            # Calculate wire length
            dx = wire.points[-1].x - wire.points[0].x
            dy = wire.points[-1].y - wire.points[0].y
            length = (dx**2 + dy**2) ** 0.5

            if length > max_length:
                self._add_violation(
                    RuleViolation(
                        rule_name="wire_too_long",
                        severity=RuleSeverity.WARNING,
                        category=RuleCategory.CONNECTIVITY,
                        message=f"Wire is {length:.1f}mm long (max {max_length}mm)",
                        elements=[wire],
                        location=Position(
                            (wire.points[0].x + wire.points[-1].x) / 2,
                            (wire.points[0].y + wire.points[-1].y) / 2,
                            0,
                        ),
                        suggestion="Break into shorter segments or rearrange components",
                    )
                )

    def _check_wire_junctions(self, wires: List[Wire], junctions: List[Junction]):
        """Check for missing junctions at wire crossings."""
        junction_positions = {(j.at.x, j.at.y) for j in junctions}

        # Find wire intersections
        for i, wire1 in enumerate(wires):
            for wire2 in wires[i + 1 :]:
                # Check if wires cross
                intersection = self._find_wire_intersection(wire1, wire2)
                if intersection:
                    x, y = intersection
                    if (x, y) not in junction_positions:
                        self._add_violation(
                            RuleViolation(
                                rule_name="missing_junction",
                                severity=RuleSeverity.ERROR,
                                category=RuleCategory.CONNECTIVITY,
                                message=f"Wires cross without junction at ({x:.1f}, {y:.1f})",
                                elements=[wire1, wire2],
                                location=Position(x, y, 0),
                                suggestion="Add junction or reroute wires",
                            )
                        )

    def _find_wire_intersection(
        self, wire1: Wire, wire2: Wire
    ) -> Optional[Tuple[float, float]]:
        """Find intersection point of two wires."""
        # Line segment intersection algorithm
        x1, y1 = wire1.points[0].x, wire1.points[0].y
        x2, y2 = wire1.points[-1].x, wire1.points[-1].y
        x3, y3 = wire2.points[0].x, wire2.points[0].y
        x4, y4 = wire2.points[-1].x, wire2.points[-1].y

        denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(denom) < 0.001:
            return None  # Parallel lines

        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
        u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom

        if 0 <= t <= 1 and 0 <= u <= 1:
            # Intersection exists
            x = x1 + t * (x2 - x1)
            y = y1 + t * (y2 - y1)
            return (x, y)

        return None

    def _check_missing_values(self, components: List[Component]):
        """Check for missing component values."""
        for comp in components:
            if not comp.value or comp.value == "~":
                # Some components don't need values
                if comp.reference and comp.reference[0] in ["TP", "J", "P", "SW"]:
                    continue

                self._add_violation(
                    RuleViolation(
                        rule_name="missing_value",
                        severity=RuleSeverity.WARNING,
                        category=RuleCategory.ANNOTATION,
                        message=f"Component {comp.reference} has no value",
                        elements=[comp],
                        location=comp.position,
                        suggestion="Add appropriate value (e.g., 10k, 100nF)",
                    )
                )

    def _check_missing_footprints(self, components: List[Component]):
        """Check for missing footprints."""
        for comp in components:
            footprint_prop = next(
                (p for p in comp.properties if p.key == "Footprint"), None
            )

            if (
                not footprint_prop
                or not footprint_prop.value
                or footprint_prop.value == "~"
            ):
                self._add_violation(
                    RuleViolation(
                        rule_name="missing_footprint",
                        severity=RuleSeverity.ERROR,
                        category=RuleCategory.ANNOTATION,
                        message=f"Component {comp.reference} has no footprint assigned",
                        elements=[comp],
                        location=comp.position,
                        suggestion="Assign footprint for PCB layout",
                    )
                )

    def _check_required_properties(self, components: List[Component]):
        """Check for required properties."""
        for comp in components:
            existing_keys = {prop.key for prop in comp.properties}

            for required_key in self.rules.required_properties:
                if required_key not in existing_keys:
                    self._add_violation(
                        RuleViolation(
                            rule_name="missing_property",
                            severity=RuleSeverity.WARNING,
                            category=RuleCategory.ANNOTATION,
                            message=f"Component {comp.reference} missing required property '{required_key}'",
                            elements=[comp],
                            location=comp.position,
                            suggestion=f"Add '{required_key}' property",
                        )
                    )

    def _check_text_size(self, components: List[Component], labels: List[Label]):
        """Check text size constraints."""
        min_size = self.rules.min_text_size
        max_size = self.rules.max_text_size

        # Check component text
        for comp in components:
            # Skip text size checks for SchematicSymbol as properties is a simple dict
            if isinstance(comp.properties, dict):
                continue

            # Old-style properties with objects
            for prop in comp.properties:
                if (
                    hasattr(prop, "effects")
                    and prop.effects
                    and hasattr(prop.effects, "font")
                ):
                    size = (
                        prop.effects.font.size.x
                        if hasattr(prop.effects.font.size, "x")
                        else 1.27
                    )

                    if size < min_size:
                        self._add_violation(
                            RuleViolation(
                                rule_name="text_too_small",
                                severity=RuleSeverity.WARNING,
                                category=RuleCategory.STYLE,
                                message=f"Text '{prop.value}' is too small ({size}mm)",
                                elements=[comp],
                                location=(
                                    prop.at
                                    if hasattr(prop, "at") and prop.at
                                    else comp.position
                                ),
                                suggestion=f"Use text size between {min_size}mm and {max_size}mm",
                            )
                        )

                    if size > max_size:
                        self._add_violation(
                            RuleViolation(
                                rule_name="text_too_large",
                                severity=RuleSeverity.WARNING,
                                category=RuleCategory.STYLE,
                                message=f"Text '{prop.value}' is too large ({size}mm)",
                                elements=[comp],
                                location=(
                                    prop.at
                                    if hasattr(prop, "at") and prop.at
                                    else comp.position
                                ),
                                suggestion=f"Use text size between {min_size}mm and {max_size}mm",
                            )
                        )

    def get_summary(self) -> Dict[str, int]:
        """Get summary of violations by severity."""
        summary = {
            RuleSeverity.ERROR.value: 0,
            RuleSeverity.WARNING.value: 0,
            RuleSeverity.INFO.value: 0,
        }

        for violation in self.violations:
            summary[violation.severity.value] += 1

        return summary

    def get_violations_by_category(self) -> Dict[RuleCategory, List[RuleViolation]]:
        """Get violations grouped by category."""
        by_category: Dict[RuleCategory, List[RuleViolation]] = {}

        for violation in self.violations:
            if violation.category not in by_category:
                by_category[violation.category] = []
            by_category[violation.category].append(violation)

        return by_category

    def filter_violations(
        self,
        severity: Optional[RuleSeverity] = None,
        category: Optional[RuleCategory] = None,
    ) -> List[RuleViolation]:
        """Filter violations by criteria."""
        filtered = self.violations

        if severity:
            filtered = [v for v in filtered if v.severity == severity]

        if category:
            filtered = [v for v in filtered if v.category == category]

        return filtered
