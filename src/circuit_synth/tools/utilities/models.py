#!/usr/bin/env python3
"""
Data models for KiCad to Python synchronization tool.

This module defines the core data structures used for representing
circuits, components, and nets during the synchronization process.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class Component:
    """Simple component representation"""

    reference: str
    lib_id: str
    value: str
    position: tuple = (0.0, 0.0)
    footprint: str = ""

    def to_dict(self):
        return {
            "reference": self.reference,
            "lib_id": self.lib_id,
            "value": self.value,
            "position": self.position,
            "footprint": self.footprint,
        }


@dataclass
class Net:
    """Net representation with actual pin connections"""

    name: str
    connections: List[Tuple[str, str]]  # List of (component_ref, pin) tuples

    def to_dict(self):
        return {"name": self.name, "connections": self.connections}


@dataclass
class Circuit:
    """Circuit representation with real netlist data"""

    name: str
    components: List[Component]
    nets: List[Net]
    schematic_file: str = ""
    is_hierarchical_sheet: bool = False
    hierarchical_tree: Optional[Dict[str, List[str]]] = (
        None  # Parent-child relationships
    )

    def to_dict(self):
        return {
            "name": self.name,
            "components": [c.to_dict() for c in self.components],
            "nets": [n.to_dict() for n in self.nets],
            "schematic_file": self.schematic_file,
            "is_hierarchical_sheet": self.is_hierarchical_sheet,
            "hierarchical_tree": self.hierarchical_tree,
        }
