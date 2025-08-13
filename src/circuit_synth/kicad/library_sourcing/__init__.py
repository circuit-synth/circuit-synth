"""
KiCad Library Sourcing - Hybrid multi-source component discovery

This module provides a unified interface for sourcing KiCad symbols, footprints, and 3D models
from multiple sources including local libraries, HTTP libraries, and third-party APIs.
"""

from .models import ComponentSearchResult, LibrarySource, SourcePriority
from .orchestrator import LibraryOrchestrator
from .sources import (
    DigiKeyGitHubSource,
    DigiKeySource,
    HTTPLibrarySource,
    LocalKiCadSource,
    SnapEDASource,
)

__all__ = [
    "LibraryOrchestrator",
    "LocalKiCadSource",
    "DigiKeyGitHubSource",
    "HTTPLibrarySource",
    "SnapEDASource",
    "DigiKeySource",
    "ComponentSearchResult",
    "LibrarySource",
    "SourcePriority",
]
