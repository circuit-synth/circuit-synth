"""
Component placement package for handling geometry, placement and wire routing.

Provides geometry utilities, automated placement algorithms,
and wire routing functionality for KiCad schematics.
"""

from .force_directed_layout import ForceDirectedLayout, ForceVector
from .geometry import (
    ComponentDimensions,
    ComponentGeometryHandler,
    PinLocation,
    PowerSymbolGeometryHandler,
    ResistorGeometryHandler,
    create_geometry_handler,
)
from .placement import ComponentPlacer, PlacementNode
from .wire_routing import WireRouter, WireSegment

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
