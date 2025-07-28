"""
PCB component placement algorithms - Now using high-performance Rust implementations.
"""

from .base import ComponentWrapper
from .connection_centric import ConnectionCentricPlacement
from .connectivity_driven import ConnectivityDrivenPlacer
from .hierarchical_placement import HierarchicalPlacer

# Use Rust implementation for force-directed placement (Phase 3 migration)
try:
    from rust_force_directed_placement import (
        ForceDirectedPlacer as RustForceDirectedPlacer,
    )

    # Create compatibility wrapper
    ForceDirectedPlacer = RustForceDirectedPlacer

    def apply_force_directed_placement(*args, **kwargs):
        """Compatibility wrapper for Rust force-directed placement."""
        placer = RustForceDirectedPlacer()
        return placer.place(*args, **kwargs)

    RUST_PLACEMENT_AVAILABLE = True
except ImportError:
    # Fallback to Python implementation
    from .force_directed import ForceDirectedPlacer, apply_force_directed_placement

    RUST_PLACEMENT_AVAILABLE = False

__all__ = [
    "ComponentWrapper",
    "HierarchicalPlacer",
    "ForceDirectedPlacer",
    "apply_force_directed_placement",
    "ConnectivityDrivenPlacer",
    "ConnectionCentricPlacement",
    "RUST_PLACEMENT_AVAILABLE",
]
