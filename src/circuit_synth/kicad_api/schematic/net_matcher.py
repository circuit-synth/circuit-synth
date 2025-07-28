"""
Net-based component matching using connection tracing.
"""

import logging
from collections import defaultdict
from typing import Dict, List, Set, Tuple

from .connection_tracer import ConnectionTracer

logger = logging.getLogger(__name__)


class NetMatcher:
    """
    Matches components based on their net connections.
    """

    def __init__(self, connection_tracer: ConnectionTracer):
        """Initialize with connection tracer."""
        self.tracer = connection_tracer
        self._net_signatures = {}

    def match_by_connections(
        self, circuit_component: Dict, kicad_components: List[Dict]
    ) -> List[Tuple[str, float]]:
        """
        Match a circuit component to KiCad components by net connections.

        Returns:
            List of (kicad_ref, confidence) tuples sorted by confidence
        """
        # Get net signature for circuit component
        circuit_nets = set(circuit_component.get("pins", {}).values())
        if not circuit_nets:
            return []

        matches = []
        for kicad_comp in kicad_components:
            # Get nets for KiCad component
            kicad_nets = self._get_component_nets(kicad_comp["reference"])

            # Calculate similarity
            similarity = self._calculate_net_similarity(circuit_nets, kicad_nets)
            if similarity > 0:
                matches.append((kicad_comp["reference"], similarity))

        # Sort by confidence
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches

    def _get_component_nets(self, reference: str) -> Set[str]:
        """Get all nets connected to a component."""
        if reference in self._net_signatures:
            return self._net_signatures[reference]

        nets = set()
        # Use find_all_connections which is the actual method in ConnectionTracer
        connections = self.tracer.find_all_connections(reference)

        for trace in connections:
            if trace.net_name:
                nets.add(trace.net_name)

        self._net_signatures[reference] = nets
        return nets

    def _calculate_net_similarity(self, nets1: Set[str], nets2: Set[str]) -> float:
        """Calculate similarity between two sets of nets."""
        if not nets1 or not nets2:
            return 0.0

        intersection = nets1.intersection(nets2)
        union = nets1.union(nets2)

        if not union:
            return 0.0

        return len(intersection) / len(union)
