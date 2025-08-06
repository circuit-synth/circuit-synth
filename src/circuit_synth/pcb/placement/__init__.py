"""
PCB component placement algorithms - Now using high-performance Rust implementations.
"""

from .base import ComponentWrapper
from .connection_centric import ConnectionCentricPlacement
from .connectivity_driven import ConnectivityDrivenPlacer
from .hierarchical_placement import HierarchicalPlacer

# Use Rust implementation for force-directed placement with Python fallback
try:
    from rust_force_directed_placement import (
        ForceDirectedPlacer as RustForceDirectedPlacer,
    )

    ForceDirectedPlacer = RustForceDirectedPlacer
    PCB_RUST_PLACEMENT_AVAILABLE = True
except ImportError:
    # Python fallback for placement
    from .force_directed import ForceDirectedPlacer

    PCB_RUST_PLACEMENT_AVAILABLE = False


def apply_force_directed_placement(*args, **kwargs):
    """Compatibility wrapper for force-directed placement with fallback."""
    placer = ForceDirectedPlacer()
    return placer.place(*args, **kwargs)


RUST_PLACEMENT_AVAILABLE = PCB_RUST_PLACEMENT_AVAILABLE

__all__ = [
    "ComponentWrapper",
    "HierarchicalPlacer",
    "ForceDirectedPlacer",
    "apply_force_directed_placement",
    "ConnectivityDrivenPlacer",
    "ConnectionCentricPlacement",
    "RUST_PLACEMENT_AVAILABLE",
]
