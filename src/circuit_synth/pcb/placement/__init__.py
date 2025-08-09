""" """

from .base import ComponentWrapper
from .connection_centric import ConnectionCentricPlacement
from .connectivity_driven import ConnectivityDrivenPlacer

# Python implementation
from .force_directed import ForceDirectedPlacer
from .hierarchical_placement import HierarchicalPlacer


def apply_force_directed_placement(*args, **kwargs):
    """Compatibility wrapper for force-directed placement with fallback."""
    placer = ForceDirectedPlacer()
    return placer.place(*args, **kwargs)


__all__ = [
    "ComponentWrapper",
    "HierarchicalPlacer",
    "ForceDirectedPlacer",
    "apply_force_directed_placement",
    "ConnectivityDrivenPlacer",
    "ConnectionCentricPlacement",
]
