"""
KiCad schematic editor module.

This module provides functionality for parsing and selectively editing KiCad schematic
(.kicad_sch) files while preserving user layout choices. It focuses on:

1. Reading existing schematics to extract component and connection information
2. Comparing with Circuit Synth's circuit model to identify changes
3. Applying changes while preserving component positions and layout
4. Adding new components at schematic edges with hierarchical labels

Key components:
- SchematicReader: Parses .kicad_sch files into internal representation
- SchematicComparer: Identifies differences between circuit models
- SchematicEditor: Applies changes while preserving layout
- SchematicExporter: Writes modified schematics back to files
"""

from .schematic_comparer import SchematicComparer
from .schematic_editor import SchematicEditor
from .schematic_exporter import SchematicExporter
from .schematic_reader import SchematicReader

# S-expression parser is now imported from kicad_api.core

__all__ = [
    "SchematicReader",
    "SchematicComparer",
    "SchematicEditor",
    "SchematicExporter",
    "SExpressionParser",
    "SExpressionWriter",
]
