"""
PCB component placement algorithms.

This module provides various algorithms for automatic component placement
on PCB boards, including:

- ForceDirectedPlacer: Basic physics-based placement
- EnhancedForceDirectedPlacer: Advanced placement with net weighting and grouping
- ConnectivityDrivenPlacer: Placement based on connectivity analysis
- HierarchicalPlacer: Hierarchical placement for complex circuits
- ConnectionCentricPlacement: Connection-focused placement
"""

from .base import ComponentWrapper
from .connection_centric import ConnectionCentricPlacement
from .connectivity_driven import ConnectivityDrivenPlacer

# Python implementation
from .force_directed import ForceDirectedPlacer
from .force_directed_enhanced import EnhancedForceDirectedPlacer, NetInfo
from .hierarchical_placement import HierarchicalPlacer


def apply_force_directed_placement(*args, **kwargs):
    """Compatibility wrapper for force-directed placement with fallback."""
    placer = ForceDirectedPlacer()
    return placer.place(*args, **kwargs)


__all__ = [
    "ComponentWrapper",
    "HierarchicalPlacer",
    "ForceDirectedPlacer",
    "EnhancedForceDirectedPlacer",
    "NetInfo",
    "apply_force_directed_placement",
    "ConnectivityDrivenPlacer",
    "ConnectionCentricPlacement",
]
