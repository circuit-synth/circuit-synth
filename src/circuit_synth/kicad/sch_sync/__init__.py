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

from .synchronizer import SchematicSynchronizer, SyncReport
from .component_matcher import ComponentMatcher, MatchResult
from .schematic_updater import SchematicUpdater, ComponentUpdate, PlacementInfo

__all__ = [
    'SchematicSynchronizer',
    'SyncReport',
    'ComponentMatcher',
    'MatchResult',
    'SchematicUpdater',
    'ComponentUpdate',
    'PlacementInfo'
]