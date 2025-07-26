# KiCad Schematic Editor Module

This module provides functionality for parsing and selectively editing KiCad schematic (.kicad_sch) files while preserving user layout choices. It focuses on:

1. Reading existing schematics to extract component and connection information
2. Comparing with Circuit Synth's circuit model to identify changes
3. Applying changes while preserving component positions and layout
4. Adding new components at schematic edges with hierarchical labels

## Module Structure

- `__init__.py`: Module initialization and exports
- `s_expression.py`: Parser and writer for KiCad's S-expression format
- `schematic_reader.py`: Parses .kicad_sch files into internal representation
- `schematic_comparer.py`: Identifies differences between circuit models
- `schematic_editor.py`: Applies changes while preserving layout
- `schematic_exporter.py`: Writes modified schematics back to files

## Key Components

### SchematicReader

Parses KiCad schematic files and extracts:
- Components (symbols) with properties and pins
- Nets (connections) between components
- Hierarchical sheets and their pins

### SchematicComparer

Compares a parsed schematic with a Circuit Synth circuit model to identify:
- Components to add, modify, or remove
- Net changes (new connections, disconnections)
- Sheet hierarchy changes

### SchematicEditor

Applies identified changes while preserving existing layout:
- Updates properties of existing components
- Adds new components at schematic edges
- Creates hierarchical labels for connections
- Maintains sheet hierarchy

### SchematicExporter

Handles writing modified schematics back to KiCad format:
- Validates schematic structure
- Ensures required sections are present
- Maintains proper formatting
- Preserves KiCad compatibility

## Usage Example

```python
from circuit_synth.kicad.sch_editor import (
    SchematicReader,
    SchematicComparer,
    SchematicEditor,
    SchematicExporter
)

# Read existing schematic
reader = SchematicReader()
reader.read_file("input.kicad_sch")

# Compare with circuit model
comparer = SchematicComparer(reader.symbols, reader.nets, reader.sheets)
changes = comparer.compare_with_circuit(circuit)

# Apply changes
editor = SchematicEditor(reader.data)
modified_data = editor.apply_changes(changes)

# Export modified schematic
exporter = SchematicExporter()
exporter.write_file(modified_data, "output.kicad_sch")
```

See `examples/edit_kicad_schematic.py` for a complete example.

## Testing

Unit tests are provided in `tests/test_schematic_editor.py`. Run with:

```bash
python -m unittest tests/test_schematic_editor.py
```

A sample test schematic is provided in `tests/test_data/test_circuit.kicad_sch`.