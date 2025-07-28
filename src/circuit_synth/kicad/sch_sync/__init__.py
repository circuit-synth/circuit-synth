"""
KiCad Schematic Synchronization Module

This module provides functionality for synchronizing Circuit Synth JSON definitions
with existing KiCad schematic files, enabling bidirectional workflow between
Python circuit definitions and KiCad projects.

Key Components:
- SchematicSynchronizer: Main synchronization class
- ComponentMatcher: Component matching logic with configurable criteria
- SchematicUpdater: Updates KiCad schematics while preserving user placement
"""

from .component_matcher import ComponentMatcher, MatchResult
from .schematic_updater import ComponentUpdate, PlacementInfo, SchematicUpdater
from .synchronizer import SchematicSynchronizer, SyncReport

__all__ = [
    "SchematicSynchronizer",
    "SyncReport",
    "ComponentMatcher",
    "MatchResult",
    "SchematicUpdater",
    "ComponentUpdate",
    "PlacementInfo",
]
