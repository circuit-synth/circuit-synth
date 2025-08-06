"""
Search and discovery engine for KiCad schematics.

This module provides comprehensive search capabilities for finding components,
nets, and connections within schematics.
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from ..core.types import (
    BoundingBox,
    Junction,
    Label,
    LabelType,
    Net,
    Point,
    Schematic,
    SchematicSymbol,
    Wire,
)

logger = logging.getLogger(__name__)


class MatchType(Enum):
    """Types of pattern matching."""

    EXACT = "exact"
    CONTAINS = "contains"
    REGEX = "regex"
    WILDCARD = "wildcard"


@dataclass
class SearchCriterion:
    """Single search criterion."""

    field: str  # e.g., "reference", "value", "footprint"
    pattern: str
    match_type: MatchType = MatchType.CONTAINS
    case_sensitive: bool = False


@dataclass
class SearchQuery:
    """Complex search query with multiple criteria."""

    criteria: List[SearchCriterion] = field(default_factory=list)
    combine_with: str = "AND"  # "AND" or "OR"

    def add_criterion(
        self,
        field: str,
        pattern: str,
        match_type: MatchType = MatchType.CONTAINS,
        case_sensitive: bool = False,
    ):
        """Add a search criterion."""
        self.criteria.append(
            SearchCriterion(
                field=field,
                pattern=pattern,
                match_type=match_type,
                case_sensitive=case_sensitive,
            )
        )


@dataclass
class SearchResults:
    """Container for search results."""

    components: List[SchematicSymbol] = field(default_factory=list)
    nets: List[Net] = field(default_factory=list)
    wires: List[Wire] = field(default_factory=list)
    labels: List[Label] = field(default_factory=list)

    @property
    def total_count(self) -> int:
        """Get total number of results."""
        return (
            len(self.components) + len(self.nets) + len(self.wires) + len(self.labels)
        )

    def is_empty(self) -> bool:
        """Check if results are empty."""
        return self.total_count == 0


@dataclass
class NetStatistics:
    """Statistics about a net."""

    name: str
    component_count: int
    pin_count: int
    wire_count: int
    total_length: float
    has_power_connection: bool
    has_ground_connection: bool
    unconnected_pins: List[Tuple[str, str]]  # (component_ref, pin)


class ComponentValueParser:
    """Parse component values with units."""

    UNIT_MULTIPLIERS = {
        "p": 1e-12,
        "n": 1e-9,
        "u": 1e-6,
        "µ": 1e-6,
        "m": 1e-3,
        "k": 1e3,
        "K": 1e3,
        "M": 1e6,
        "G": 1e9,
    }

    @classmethod
    def parse_value(cls, value_str: str) -> Optional[float]:
        """
        Parse a component value string to numeric value.

        Examples:
            "10k" -> 10000.0
            "4.7µF" -> 4.7e-6
            "100nF" -> 1e-7
        """
        if not value_str:
            return None

        # Remove common suffixes
        value_str = value_str.replace("Ω", "").replace("ohm", "")
        value_str = value_str.replace("F", "").replace("H", "")

        # Extract numeric part and unit
        match = re.match(r"([\d.]+)\s*([pnuµmkKMG]?)", value_str)
        if not match:
            return None

        try:
            numeric = float(match.group(1))
            unit = match.group(2)

            if unit in cls.UNIT_MULTIPLIERS:
                return numeric * cls.UNIT_MULTIPLIERS[unit]
            return numeric

        except ValueError:
            return None


class SearchEngine:
    """
    Advanced search engine for KiCad schematics.

    Provides comprehensive search capabilities including:
    - Component search by various criteria
    - Net tracing and discovery
    - Spatial searches
    - Connection analysis
    """

    def __init__(self, schematic: Schematic):
        """
        Initialize the search engine.

        Args:
            schematic: The schematic to search
        """
        self.schematic = schematic
        self._build_indices()

    def _build_indices(self):
        """Build search indices for performance."""
        # Component indices
        self._components_by_ref = {
            comp.reference: comp for comp in self.schematic.components
        }
        self._components_by_value = {}
        for comp in self.schematic.components:
            if comp.value not in self._components_by_value:
                self._components_by_value[comp.value] = []
            self._components_by_value[comp.value].append(comp)

        # Net index (simplified - full implementation would trace connections)
        self._nets_by_name = {}
        for label in self.schematic.labels:
            if label.text not in self._nets_by_name:
                self._nets_by_name[label.text] = []
            self._nets_by_name[label.text].append(label)

    def search_components(
        self,
        query: Union[SearchQuery, str] = None,
        reference: str = None,
        value: str = None,
        footprint: str = None,
        lib_id: str = None,
        use_regex: bool = False,
    ) -> List[SchematicSymbol]:
        """
        Search for components matching criteria.

        Args:
            query: Complex search query or simple text search
            reference: Reference designator pattern
            value: Component value pattern
            footprint: Footprint pattern
            lib_id: Library ID pattern
            use_regex: Use regex matching

        Returns:
            List of matching components
        """
        results = []

        # Handle simple string query
        if isinstance(query, str):
            search_query = SearchQuery()
            search_query.add_criterion("reference", query)
            search_query.add_criterion("value", query)
            search_query.combine_with = "OR"
            query = search_query

        # Build query from individual parameters
        elif query is None:
            query = SearchQuery()
            if reference:
                query.add_criterion(
                    "reference",
                    reference,
                    MatchType.REGEX if use_regex else MatchType.CONTAINS,
                )
            if value:
                query.add_criterion(
                    "value", value, MatchType.REGEX if use_regex else MatchType.CONTAINS
                )
            if footprint:
                query.add_criterion(
                    "footprint",
                    footprint,
                    MatchType.REGEX if use_regex else MatchType.CONTAINS,
                )
            if lib_id:
                query.add_criterion(
                    "lib_id",
                    lib_id,
                    MatchType.REGEX if use_regex else MatchType.CONTAINS,
                )

        # Search all components
        for component in self.schematic.components:
            if self._matches_query(component, query):
                results.append(component)

        return results

    def _matches_query(self, component: SchematicSymbol, query: SearchQuery) -> bool:
        """Check if component matches search query."""
        if not query.criteria:
            return True

        matches = []
        for criterion in query.criteria:
            field_value = self._get_component_field(component, criterion.field)
            if field_value is None:
                matches.append(False)
                continue

            matches.append(
                self._matches_pattern(
                    field_value,
                    criterion.pattern,
                    criterion.match_type,
                    criterion.case_sensitive,
                )
            )

        if query.combine_with == "AND":
            return all(matches)
        else:  # OR
            return any(matches)

    def _get_component_field(
        self, component: SchematicSymbol, field: str
    ) -> Optional[str]:
        """Get field value from component."""
        if field == "reference":
            return component.reference
        elif field == "value":
            return component.value
        elif field == "footprint":
            return component.footprint
        elif field == "lib_id":
            return component.lib_id
        elif field in component.properties:
            return component.properties[field]
        return None

    def _matches_pattern(
        self, text: str, pattern: str, match_type: MatchType, case_sensitive: bool
    ) -> bool:
        """Check if text matches pattern."""
        if not case_sensitive:
            text = text.lower()
            pattern = pattern.lower()

        if match_type == MatchType.EXACT:
            return text == pattern
        elif match_type == MatchType.CONTAINS:
            return pattern in text
        elif match_type == MatchType.REGEX:
            try:
                return bool(re.search(pattern, text))
            except re.error:
                logger.warning(f"Invalid regex pattern: {pattern}")
                return False
        elif match_type == MatchType.WILDCARD:
            # Convert wildcard to regex
            regex_pattern = pattern.replace("*", ".*").replace("?", ".")
            return bool(re.match(f"^{regex_pattern}$", text))

        return False

    def search_nets(self, pattern: str, use_regex: bool = False) -> List[str]:
        """
        Search for nets matching pattern.

        Args:
            pattern: Search pattern
            use_regex: Use regex matching

        Returns:
            List of matching net names
        """
        results = set()

        # Search labels
        for label in self.schematic.labels:
            if use_regex:
                if re.search(pattern, label.text):
                    results.add(label.text)
            else:
                if pattern in label.text:
                    results.add(label.text)

        return sorted(list(results))

    def search_by_value(
        self, value_pattern: str, tolerance: float = None
    ) -> List[SchematicSymbol]:
        """
        Search components by value with optional tolerance.

        Args:
            value_pattern: Value to search for (e.g., "10k", "100nF")
            tolerance: Tolerance percentage (e.g., 0.1 for 10%)

        Returns:
            List of matching components
        """
        results = []

        if tolerance is not None:
            # Parse target value
            target_value = ComponentValueParser.parse_value(value_pattern)
            if target_value is None:
                return results

            # Search with tolerance
            min_value = target_value * (1 - tolerance)
            max_value = target_value * (1 + tolerance)

            for component in self.schematic.components:
                comp_value = ComponentValueParser.parse_value(component.value)
                if comp_value is not None:
                    if min_value <= comp_value <= max_value:
                        results.append(component)
        else:
            # Exact string match
            if value_pattern is not None:
                for component in self.schematic.components:
                    if component.value and value_pattern in component.value:
                        results.append(component)

        return results

    def search_by_footprint(self, footprint_pattern: str) -> List[SchematicSymbol]:
        """Search components by footprint."""
        results = []

        for component in self.schematic.components:
            if component.footprint and footprint_pattern in component.footprint:
                results.append(component)

        return results

    def find_components_in_area(self, area: BoundingBox) -> List[SchematicSymbol]:
        """Find all components within a bounding box."""
        results = []

        for component in self.schematic.components:
            if area.contains_point(component.position.x, component.position.y):
                results.append(component)

        return results

    def find_unconnected_pins(self) -> Dict[str, List[str]]:
        """
        Find components with unconnected pins.

        Returns:
            Dict mapping component reference to list of unconnected pins
        """
        unconnected = {}

        # This is a simplified implementation
        # Full implementation would need symbol library data
        # and actual connection tracing

        # For now, check if component has any wires nearby
        for component in self.schematic.components:
            # Check if any wires are near the component
            has_connection = False
            comp_bbox = component.get_bounding_box()

            for wire in self.schematic.wires:
                for point in wire.points:
                    if comp_bbox.contains_point(point.x, point.y):
                        has_connection = True
                        break
                if has_connection:
                    break

            if not has_connection:
                unconnected[component.reference] = ["all"]  # Placeholder

        return unconnected

    def find_power_nets(self) -> List[str]:
        """Find all power-related nets."""
        power_patterns = [
            r"^VCC",
            r"^VDD",
            r"^VSS",
            r"^GND",
            r"^AGND",
            r"^DGND",
            r"^\+\d+V",
            r"^-\d+V",
            r"^V\+",
            r"^V-",
        ]

        power_nets = set()

        for label in self.schematic.labels:
            for pattern in power_patterns:
                if re.match(pattern, label.text):
                    power_nets.add(label.text)
                    break

        # Check power symbols
        for component in self.schematic.components:
            if component.lib_id and "power:" in component.lib_id:
                power_nets.add(component.value)

        return sorted(list(power_nets))

    def find_duplicate_references(self) -> List[Tuple[str, List[SchematicSymbol]]]:
        """Find components with duplicate reference designators."""
        ref_map = {}

        for component in self.schematic.components:
            if component.reference:
                if component.reference not in ref_map:
                    ref_map[component.reference] = []
                ref_map[component.reference].append(component)

        duplicates = []
        for ref, components in ref_map.items():
            if len(components) > 1:
                duplicates.append((ref, components))

        return duplicates

    def trace_net(self, net_name: str) -> Optional[Net]:
        """
        Trace a complete net through the schematic.

        Args:
            net_name: Name of the net to trace

        Returns:
            Net object with all connections
        """
        # Find all labels with this net name
        labels = [l for l in self.schematic.labels if l.text == net_name]
        if not labels:
            return None

        net = Net(name=net_name)

        # This is a simplified implementation
        # Full implementation would trace through wires and components
        # to find all connected pins

        return net

    def get_net_statistics(self, net_name: str) -> Optional[NetStatistics]:
        """Get statistics about a net."""
        net = self.trace_net(net_name)
        if not net:
            return None

        # Count connected components
        component_refs = set()
        pin_count = 0

        # Count wires (simplified)
        wire_count = 0
        total_length = 0.0

        for wire in self.schematic.wires:
            # Check if wire is part of this net (simplified check)
            wire_count += 1
            # Calculate wire length
            for i in range(len(wire.points) - 1):
                p1, p2 = wire.points[i], wire.points[i + 1]
                length = ((p2.x - p1.x) ** 2 + (p2.y - p1.y) ** 2) ** 0.5
                total_length += length

        # Check power connections
        power_nets = self.find_power_nets()
        has_power = any(pwr in net_name for pwr in ["VCC", "VDD", "+"])
        has_ground = any(gnd in net_name for gnd in ["GND", "VSS"])

        return NetStatistics(
            name=net_name,
            component_count=len(component_refs),
            pin_count=pin_count,
            wire_count=wire_count,
            total_length=total_length,
            has_power_connection=has_power,
            has_ground_connection=has_ground,
            unconnected_pins=[],
        )


class SearchQueryBuilder:
    """Helper class to build complex search queries."""

    def __init__(self):
        """Initialize query builder."""
        self.query = SearchQuery()

    def with_reference(self, pattern: str, match_type: MatchType = MatchType.CONTAINS):
        """Add reference criterion."""
        self.query.add_criterion("reference", pattern, match_type)
        return self

    def with_value(self, pattern: str, match_type: MatchType = MatchType.CONTAINS):
        """Add value criterion."""
        self.query.add_criterion("value", pattern, match_type)
        return self

    def with_footprint(self, pattern: str, match_type: MatchType = MatchType.CONTAINS):
        """Add footprint criterion."""
        self.query.add_criterion("footprint", pattern, match_type)
        return self

    def with_property(
        self, name: str, pattern: str, match_type: MatchType = MatchType.CONTAINS
    ):
        """Add custom property criterion."""
        self.query.add_criterion(name, pattern, match_type)
        return self

    def combine_with_or(self):
        """Use OR combination for criteria."""
        self.query.combine_with = "OR"
        return self

    def combine_with_and(self):
        """Use AND combination for criteria."""
        self.query.combine_with = "AND"
        return self

    def build(self) -> SearchQuery:
        """Build the query."""
        return self.query
