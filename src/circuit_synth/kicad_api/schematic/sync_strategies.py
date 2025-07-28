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
