"""
KiCad Schematic API - Component Management Module

This module provides a comprehensive API for programmatic manipulation of KiCad schematics.
It is designed to be modular and could potentially become its own repository.

Key Features:
- Component CRUD operations (Create, Read, Update, Delete)
- Automatic component placement with collision detection
- Reference designator management
- Multi-unit symbol support
- Bulk operations on multiple components
- Component search and filtering
- Wire connection preservation during moves

Main Classes:
- ComponentManager: Core component management functionality
- ReferenceManager: Unique reference designator generation
- PlacementEngine: Automatic component placement algorithms
- ComponentSearch: Search and filter components
- BulkOperations: Operations on multiple components
"""

from .bulk_operations import BulkOperations
from .component_manager import ComponentManager
from .component_search import ComponentSearch
from .exceptions import (
    ComponentError,
    ComponentNotFoundError,
    ConnectionError,
    InvalidLibraryError,
    PlacementError,
)
from .models import (
    CloneOptions,
    ComponentConnections,
    MoveOptions,
    MoveResult,
    RemovalOptions,
    RemovalResult,
    WireStyle,
)
from .placement_engine import PlacementEngine
from .reference_manager import ReferenceManager

__all__ = [
    # Core classes
    "ComponentManager",
    "ReferenceManager",
    "PlacementEngine",
    "ComponentSearch",
    "BulkOperations",
    # Exceptions
    "ComponentError",
    "ComponentNotFoundError",
    "InvalidLibraryError",
    "PlacementError",
    "ConnectionError",
    # Models
    "RemovalOptions",
    "RemovalResult",
    "MoveOptions",
    "MoveResult",
    "CloneOptions",
    "ComponentConnections",
    "WireStyle",
]

__version__ = "0.1.0"
