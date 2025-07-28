"""
Component Search for KiCad Schematic API.

Provides advanced search and filtering capabilities for components in a schematic.
"""

import logging
import re
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional, Union

from ..sch_editor.schematic_reader import Schematic, SchematicSymbol
from .models import SearchCriteria

logger = logging.getLogger(__name__)


class ComponentSearch:
    """
    Search and filter components in a schematic.

    This class provides various methods to find components based on
    different criteria such as value, reference, properties, and connections.
    """

    def __init__(self, schematic: Schematic):
        """
        Initialize the search engine with a schematic.

        Args:
            schematic: The Schematic object to search
        """
        self.schematic = schematic
        self._build_indices()

    def _build_indices(self) -> None:
        """Build search indices for faster lookups."""
        # Index by reference
        self._ref_index = {comp.reference: comp for comp in self.schematic.components}

        # Index by library ID
        self._lib_id_index = defaultdict(list)
        for comp in self.schematic.components:
            self._lib_id_index[comp.lib_id].append(comp)

        # Index by value
        self._value_index = defaultdict(list)
        for comp in self.schematic.components:
            if comp.value:
                self._value_index[comp.value].append(comp)

    def find_by_reference(self, reference: str) -> Optional[SchematicSymbol]:
        """
        Find a component by exact reference designator.

        Args:
            reference: The reference designator (e.g., "R1", "U2")

        Returns:
            The component or None if not found
        """
        return self._ref_index.get(reference)

    def find_by_reference_pattern(
        self, pattern: str, use_regex: bool = False
    ) -> List[SchematicSymbol]:
        """
        Find components matching a reference pattern.

        Args:
            pattern: The pattern to match (glob or regex)
            use_regex: Whether to use regex matching

        Returns:
            List of matching components
        """
        if use_regex:
            try:
                regex = re.compile(pattern)
                return [
                    comp
                    for comp in self.schematic.components
                    if regex.match(comp.reference)
                ]
            except re.error as e:
                logger.error(f"Invalid regex pattern: {pattern} - {e}")
                return []
        else:
            # Simple glob-style matching
            import fnmatch

            return [
                comp
                for comp in self.schematic.components
                if fnmatch.fnmatch(comp.reference, pattern)
            ]

    def find_by_value(
        self, value_pattern: str, use_regex: bool = False, case_sensitive: bool = True
    ) -> List[SchematicSymbol]:
        """
        Find components matching a value pattern.

        Args:
            value_pattern: The pattern to match
            use_regex: Whether to use regex matching
            case_sensitive: Whether the match is case-sensitive

        Returns:
            List of matching components
        """
        results = []

        if use_regex:
            try:
                flags = 0 if case_sensitive else re.IGNORECASE
                regex = re.compile(value_pattern, flags)

                for comp in self.schematic.components:
                    if comp.value and regex.search(comp.value):
                        results.append(comp)
            except re.error as e:
                logger.error(f"Invalid regex pattern: {value_pattern} - {e}")
        else:
            # Simple substring matching
            if not case_sensitive:
                value_pattern = value_pattern.lower()

            for comp in self.schematic.components:
                if comp.value:
                    comp_value = comp.value if case_sensitive else comp.value.lower()
                    if value_pattern in comp_value:
                        results.append(comp)

        return results

    def find_by_property(
        self,
        property_name: str,
        property_value: Optional[str] = None,
        use_regex: bool = False,
    ) -> List[SchematicSymbol]:
        """
        Find components with a specific property.

        Args:
            property_name: The property name to search for
            property_value: Optional value to match (None means any value)
            use_regex: Whether to use regex for value matching

        Returns:
            List of components with the property
        """
        results = []

        for component in self.schematic.components:
            if property_name in component.properties:
                if property_value is None:
                    # Just check for property existence
                    results.append(component)
                else:
                    # Check value match
                    actual_value = component.properties[property_name]

                    if use_regex:
                        try:
                            if re.match(property_value, actual_value):
                                results.append(component)
                        except re.error:
                            logger.error(f"Invalid regex: {property_value}")
                    else:
                        if actual_value == property_value:
                            results.append(component)

        return results

    def find_by_footprint(
        self, footprint_pattern: str, use_regex: bool = False
    ) -> List[SchematicSymbol]:
        """
        Find components matching a footprint pattern.

        Args:
            footprint_pattern: The pattern to match
            use_regex: Whether to use regex matching

        Returns:
            List of matching components
        """
        results = []

        for comp in self.schematic.components:
            if not comp.footprint:
                continue

            if use_regex:
                try:
                    if re.match(footprint_pattern, comp.footprint):
                        results.append(comp)
                except re.error:
                    logger.error(f"Invalid regex: {footprint_pattern}")
            else:
                if footprint_pattern in comp.footprint:
                    results.append(comp)

        return results

    def find_by_lib_id(
        self, lib_id_pattern: str, exact_match: bool = False
    ) -> List[SchematicSymbol]:
        """
        Find components by library ID.

        Args:
            lib_id_pattern: The library ID pattern
            exact_match: Whether to match exactly or use prefix matching

        Returns:
            List of matching components
        """
        if exact_match:
            return list(self._lib_id_index.get(lib_id_pattern, []))
        else:
            # Prefix matching
            results = []
            for lib_id, components in self._lib_id_index.items():
                if lib_id.startswith(lib_id_pattern):
                    results.extend(components)
            return results

    def find_unconnected_components(self) -> List[SchematicSymbol]:
        """
        Find components with unconnected pins.

        Returns:
            List of components with at least one unconnected pin
        """
        unconnected = []

        for component in self.schematic.components:
            if self._has_unconnected_pins(component):
                unconnected.append(component)

        return unconnected

    def find_by_criteria(self, criteria: SearchCriteria) -> List[SchematicSymbol]:
        """
        Find components matching multiple criteria.

        Args:
            criteria: SearchCriteria object with multiple filters

        Returns:
            List of components matching ALL criteria (AND operation)
        """
        # Start with all components
        results = set(self.schematic.components)

        # Apply reference filter
        if criteria.reference_pattern:
            ref_matches = set(
                self.find_by_reference_pattern(
                    criteria.reference_pattern, criteria.use_regex
                )
            )
            results &= ref_matches

        # Apply value filter
        if criteria.value_pattern:
            value_matches = set(
                self.find_by_value(
                    criteria.value_pattern, criteria.use_regex, criteria.case_sensitive
                )
            )
            results &= value_matches

        # Apply footprint filter
        if criteria.footprint_pattern:
            footprint_matches = set(
                self.find_by_footprint(criteria.footprint_pattern, criteria.use_regex)
            )
            results &= footprint_matches

        # Apply lib_id filter
        if criteria.lib_id_pattern:
            lib_matches = set(self.find_by_lib_id(criteria.lib_id_pattern))
            results &= lib_matches

        # Apply property filters
        for prop_name, prop_value in criteria.property_filters.items():
            prop_matches = set(
                self.find_by_property(prop_name, prop_value, criteria.use_regex)
            )
            results &= prop_matches

        return list(results)

    def find_by_custom_filter(
        self, filter_func: Callable[[SchematicSymbol], bool]
    ) -> List[SchematicSymbol]:
        """
        Find components using a custom filter function.

        Args:
            filter_func: Function that takes a component and returns True to include it

        Returns:
            List of components for which filter_func returns True
        """
        return [comp for comp in self.schematic.components if filter_func(comp)]

    def group_by_type(self) -> Dict[str, List[SchematicSymbol]]:
        """
        Group components by their type (reference prefix).

        Returns:
            Dictionary mapping reference prefixes to component lists
        """
        groups = defaultdict(list)

        for comp in self.schematic.components:
            prefix = self._get_reference_prefix(comp.reference)
            groups[prefix].append(comp)

        return dict(groups)

    def group_by_value(self) -> Dict[str, List[SchematicSymbol]]:
        """
        Group components by their value.

        Returns:
            Dictionary mapping values to component lists
        """
        return dict(self._value_index)

    def group_by_lib_id(self) -> Dict[str, List[SchematicSymbol]]:
        """
        Group components by their library ID.

        Returns:
            Dictionary mapping library IDs to component lists
        """
        return dict(self._lib_id_index)

    def find_duplicates(self) -> Dict[str, List[SchematicSymbol]]:
        """
        Find components with duplicate values within the same type.

        Returns:
            Dictionary mapping "type:value" to lists of duplicate components
        """
        duplicates = {}
        type_value_map = defaultdict(list)

        # Group by type and value
        for comp in self.schematic.components:
            if comp.value:
                prefix = self._get_reference_prefix(comp.reference)
                key = f"{prefix}:{comp.value}"
                type_value_map[key].append(comp)

        # Find duplicates
        for key, components in type_value_map.items():
            if len(components) > 1:
                duplicates[key] = components

        return duplicates

    def find_in_area(
        self, x1: float, y1: float, x2: float, y2: float
    ) -> List[SchematicSymbol]:
        """
        Find components within a rectangular area.

        Args:
            x1, y1: Top-left corner coordinates
            x2, y2: Bottom-right corner coordinates

        Returns:
            List of components within the area
        """
        # Ensure x1 < x2 and y1 < y2
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1

        results = []
        for comp in self.schematic.components:
            if comp.position:
                x, y = comp.position[0], comp.position[1]
                if x1 <= x <= x2 and y1 <= y <= y2:
                    results.append(comp)

        return results

    def find_nearest(
        self, x: float, y: float, max_distance: Optional[float] = None, count: int = 1
    ) -> List[SchematicSymbol]:
        """
        Find the nearest components to a given point.

        Args:
            x, y: Reference point coordinates
            max_distance: Maximum distance to consider (None for unlimited)
            count: Number of nearest components to return

        Returns:
            List of nearest components, sorted by distance
        """
        # Calculate distances
        distances = []
        for comp in self.schematic.components:
            if comp.position:
                cx, cy = comp.position[0], comp.position[1]
                distance = ((cx - x) ** 2 + (cy - y) ** 2) ** 0.5

                if max_distance is None or distance <= max_distance:
                    distances.append((distance, comp))

        # Sort by distance and return requested count
        distances.sort(key=lambda x: x[0])
        return [comp for _, comp in distances[:count]]

    def _has_unconnected_pins(self, component: SchematicSymbol) -> bool:
        """Check if a component has unconnected pins."""
        # This is a simplified check - in practice would need to
        # cross-reference with nets and wires
        for pin in component.pins:
            if not pin.net_name:
                # Skip power pins and no-connect pins
                if pin.type not in ["power_in", "power_out", "no_connect"]:
                    return True
        return False

    def _get_reference_prefix(self, reference: str) -> str:
        """Extract the prefix from a reference designator."""
        match = re.match(r"^([A-Z]+)\d*", reference)
        return match.group(1) if match else ""

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the components in the schematic.

        Returns:
            Dictionary with various statistics
        """
        stats = {
            "total_components": len(self.schematic.components),
            "components_by_type": {},
            "unique_values": len(self._value_index),
            "unique_lib_ids": len(self._lib_id_index),
            "unconnected_components": len(self.find_unconnected_components()),
        }

        # Count by type
        type_groups = self.group_by_type()
        for prefix, components in type_groups.items():
            stats["components_by_type"][prefix] = len(components)

        return stats
