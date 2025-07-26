"""
Component placement package for handling geometry, placement and wire routing.

Provides geometry utilities, automated placement algorithms,
and wire routing functionality for KiCad schematics.
"""

from .geometry import (
    PinLocation,
    ComponentDimensions,
    ComponentGeometryHandler,
    ResistorGeometryHandler,
    PowerSymbolGeometryHandler,
    create_geometry_handler,
)

from .placement import (
    PlacementNode,
    ComponentPlacer,
)

from .wire_routing import (
    WireSegment,
    WireRouter,
)

from .force_directed_layout import (
    ForceVector,
    ForceDirectedLayout,
)


__all__ = [
    "PinLocation",
    "ComponentDimensions",
    "ComponentGeometryHandler",
    "ResistorGeometryHandler",
    "PowerSymbolGeometryHandler",
    "create_geometry_handler",
    "PlacementNode",
    "ComponentPlacer",
    "WireSegment",
    "WireRouter",
    "ForceVector",
    "ForceDirectedLayout",
]