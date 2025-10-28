"""
Matching strategies for component synchronization.
"""

import re
from abc import ABC, abstractmethod
from typing import Any, Dict

from .net_matcher import NetMatcher
from .search_engine import MatchType, SearchEngine


class SyncStrategy(ABC):
    """Base class for component matching strategies."""

    @abstractmethod
    def match_components(
        self, circuit_components: Dict[str, Dict], kicad_components: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Match circuit components to KiCad components.

        Returns:
            Dictionary mapping circuit_id -> kicad_reference
        """
        pass


class UUIDMatchStrategy(SyncStrategy):
    """
    Match components by UUID - most reliable identifier.

    UUIDs provide stable component identity across reference changes,
    position changes, and property modifications. This strategy should
    be tried first as it's the most reliable matching method.
    """

    def __init__(self, search_engine: SearchEngine):
        self.search_engine = search_engine

    def match_components(
        self, circuit_components: Dict[str, Dict], kicad_components: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Match components by UUID.

        Args:
            circuit_components: Dict mapping circuit_id -> component dict with 'uuid' key
            kicad_components: Dict mapping reference -> SchematicSymbol with uuid attribute

        Returns:
            Dict mapping circuit_id -> kicad_reference for matched components
        """
        matches = {}

        for circuit_id, circuit_comp in circuit_components.items():
            circuit_uuid = circuit_comp.get("uuid")
            if not circuit_uuid:
                continue

            # Find KiCad component with matching UUID
            for kicad_ref, kicad_comp in kicad_components.items():
                if hasattr(kicad_comp, "uuid") and kicad_comp.uuid == circuit_uuid:
                    matches[circuit_id] = kicad_ref
                    break

        return matches


class ReferenceMatchStrategy(SyncStrategy):
    """Match components by reference designator."""

    def __init__(self, search_engine: SearchEngine):
        self.search_engine = search_engine

    def match_components(
        self, circuit_components: Dict[str, Dict], kicad_components: Dict[str, Any]
    ) -> Dict[str, str]:
        matches = {}

        for circuit_id, circuit_comp in circuit_components.items():
            ref = circuit_comp["reference"]

            # Try exact match first using search_components
            results = self.search_engine.search_components(reference=ref)

            # Filter for exact matches
            exact_matches = [r for r in results if r.reference == ref]

            if exact_matches and len(exact_matches) == 1:
                kicad_ref = exact_matches[0].reference
                if kicad_ref not in matches.values():
                    matches[circuit_id] = kicad_ref

        return matches


class ValueFootprintStrategy(SyncStrategy):
    """Match components by value and footprint."""

    def __init__(self, search_engine: SearchEngine):
        self.search_engine = search_engine

    def match_components(
        self, circuit_components: Dict[str, Dict], kicad_components: Dict[str, Any]
    ) -> Dict[str, str]:
        matches = {}
        used_refs = set()

        for circuit_id, circuit_comp in circuit_components.items():
            if circuit_id in matches:
                continue

            # Search by value
            value = circuit_comp["value"]
            candidates = self.search_engine.search_by_value(value)

            # Filter by footprint if available
            footprint = circuit_comp.get("footprint")
            if footprint and candidates:
                candidates = [c for c in candidates if c.footprint == footprint]

            # Take first available match
            for candidate in candidates:
                if candidate.reference not in used_refs:
                    matches[circuit_id] = candidate.reference
                    used_refs.add(candidate.reference)
                    break

        return matches


class ConnectionMatchStrategy(SyncStrategy):
    """Match components by their connections."""

    def __init__(self, net_matcher: NetMatcher):
        self.net_matcher = net_matcher

    def match_components(
        self, circuit_components: Dict[str, Dict], kicad_components: Dict[str, Any]
    ) -> Dict[str, str]:
        matches = {}
        used_refs = set()

        # Convert kicad_components to list format for net_matcher
        kicad_list = [
            {"reference": ref, "component": comp}
            for ref, comp in kicad_components.items()
        ]

        for circuit_id, circuit_comp in circuit_components.items():
            if circuit_id in matches:
                continue

            # Get matches by connection
            connection_matches = self.net_matcher.match_by_connections(
                circuit_comp, kicad_list
            )

            # Take best match with high confidence
            for kicad_ref, confidence in connection_matches:
                if confidence > 0.7 and kicad_ref not in used_refs:
                    matches[circuit_id] = kicad_ref
                    used_refs.add(kicad_ref)
                    break

        return matches


class PositionRenameStrategy(SyncStrategy):
    """
    Match components by position to detect renames.

    This strategy identifies when a component has been renamed by matching on
    position + properties but different reference. It runs before ValueFootprintStrategy
    to prevent incorrectly matching renamed components by value/footprint alone.

    Logic: If a KiCad component matches a Python component on:
    - Position (within tolerance)
    - Symbol (lib_id)
    - Value
    - Footprint
    But has DIFFERENT reference → This is a RENAME
    """

    def __init__(self, search_engine: SearchEngine):
        self.search_engine = search_engine
        self.position_tolerance = 2.54  # mm (one KiCad grid unit)

    def match_components(
        self, circuit_components: Dict[str, Dict], kicad_components: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Match components by position to detect renames.

        Args:
            circuit_components: Dict mapping circuit_id -> component dict with keys:
                - reference: component reference (e.g., "R2")
                - position: Point with x, y coordinates
                - symbol: lib_id (e.g., "Device:R")
                - value: component value (e.g., "10k")
                - footprint: footprint string (e.g., "R_0603_1608Metric")
            kicad_components: Dict mapping reference -> SchematicSymbol

        Returns:
            Dict mapping circuit_id -> kicad_reference for matched components
        """
        matches = {}
        used_refs = set()

        for circuit_id, circuit_comp in circuit_components.items():
            circuit_ref = circuit_comp["reference"]

            # Skip if already matched by reference
            # (ReferenceMatchStrategy already handled exact matches)
            if circuit_ref in kicad_components:
                continue

            # Get position from circuit component
            circuit_pos = circuit_comp.get("position")
            if not circuit_pos:
                continue

            # Search for KiCad components at same position with matching properties
            for kicad_ref, kicad_comp in kicad_components.items():
                if kicad_ref in used_refs:
                    continue

                # Check position match (within tolerance)
                if not self._positions_match(circuit_pos, kicad_comp.position):
                    continue

                # Check properties match (symbol, value, footprint)
                if not self._properties_match(circuit_comp, kicad_comp):
                    continue

                # Found match at same position with same properties but different reference
                # This is a RENAME!
                matches[circuit_id] = kicad_ref
                used_refs.add(kicad_ref)
                break

        return matches

    def _positions_match(self, pos1: Any, pos2: Any) -> bool:
        """
        Check if positions match within tolerance.

        Args:
            pos1: Position from circuit component (Point object)
            pos2: Position from KiCad component (Point object)

        Returns:
            True if positions are within tolerance, False otherwise
        """
        dx = abs(pos1.x - pos2.x)
        dy = abs(pos1.y - pos2.y)
        return dx < self.position_tolerance and dy < self.position_tolerance

    def _properties_match(self, circuit_comp: Dict, kicad_comp: Any) -> bool:
        """
        Check if electrical properties match.

        Args:
            circuit_comp: Circuit component dict
            kicad_comp: KiCad SchematicSymbol

        Returns:
            True if properties match, False otherwise
        """
        # Compare symbol (lib_id)
        if circuit_comp.get("symbol") != kicad_comp.lib_id:
            return False

        # Compare value
        if circuit_comp.get("value") != kicad_comp.value:
            return False

        # Compare footprint (if present)
        circuit_footprint = circuit_comp.get("footprint")
        if circuit_footprint and circuit_footprint != kicad_comp.footprint:
            return False

        return True
