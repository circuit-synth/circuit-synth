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

    def to_circuit_synth_json(self) -> Dict[str, Any]:
        """
        Export to circuit-synth JSON format.

        This converts the internal Circuit representation to the format
        expected by circuit-synth JSON schema. Key transformations:

        1. Components: List[Component] → Dict[ref, component_dict]
        2. Nets: List[Net] → Dict[name, connections_list]
        3. Add required fields: description, tstamps, source_file, etc.

        Returns:
            Dictionary matching circuit-synth JSON schema
        """
        # Transform components: list → dict keyed by reference
        components_dict = {}
        for comp in self.components:
            comp_dict = {
                "symbol": comp.lib_id,  # lib_id → symbol
                "ref": comp.reference,  # reference → ref
                "value": comp.value,
                "footprint": comp.footprint,
                "datasheet": "",  # Default
                "description": "",  # Default
                "properties": {},  # Default
                "tstamps": "",  # Default
                "pins": [],  # Default - could be populated from schematic
            }
            components_dict[comp.reference] = comp_dict

        # Transform nets: list → dict keyed by name
        nets_dict = {}
        for net in self.nets:
            connections = []
            for ref, pin_num in net.connections:
                connection = {
                    "component": ref,
                    "pin": {
                        "number": str(pin_num),  # Ensure string
                        "name": "~",  # Default - could lookup from component
                        "type": "passive",  # Default
                    },
                }
                connections.append(connection)
            nets_dict[net.name] = connections

        # Build final JSON structure matching circuit-synth schema
        return {
            "name": self.name,
            "description": "",
            "tstamps": "",
            "source_file": self.schematic_file,
            "components": components_dict,
            "nets": nets_dict,
            "subcircuits": [],  # TODO: Handle hierarchical circuits if needed
            "annotations": [],
        }
