# Circuit-Synth Architecture

## Overview

Circuit-synth is built around a **JSON-centric architecture** where JSON serves as the canonical intermediate representation for all circuit data. This design enables seamless interoperability between Python circuit definitions and KiCad projects while maintaining full round-trip fidelity.

## Core Data Flow

```
┌─────────────┐      ┌──────────┐      ┌─────────────┐
│   Python    │ ───► │   JSON   │ ───► │   KiCad     │
│  Circuit    │      │ (Central │      │   Files     │
│   Code      │ ◄─── │  Format) │ ◄─── │ (.kicad_*)  │
└─────────────┘      └──────────┘      └─────────────┘
```

### Python → JSON → KiCad

1. **Python Circuit Definition**: Engineers write circuit designs using Python classes (`Circuit`, `Component`, `Net`)
2. **JSON Serialization**: The `Circuit.to_dict()` method converts the circuit hierarchy to JSON
3. **KiCad Generation**: JSON is processed to generate KiCad schematic and PCB files

### KiCad → JSON → Python

1. **KiCad Import**: Parser reads `.kicad_pro` and `.kicad_sch` files
2. **JSON Conversion**: Circuit structure is extracted into circuit-synth JSON format
3. **Python Generation**: `json_to_python_project` creates Python code from JSON

## JSON as Canonical Format

JSON serves as the single source of truth for circuit data:

- **Hierarchical Structure**: Preserves full circuit hierarchy with subcircuits
- **Complete Fidelity**: All circuit information is maintained during conversions
- **Version Control Friendly**: Human-readable text format ideal for Git
- **Language Agnostic**: Can be consumed by any tool or language

## JSON Structure

The JSON format represents circuits as nested hierarchies:

```json
{
  "name": "Main_Circuit",
  "description": "Top-level circuit",
  "components": {
    "U1": {
      "symbol": "MCU_Module:Arduino_UNO_R3",
      "footprint": "Module:Arduino_UNO_R3",
      "pins": [
        {"pin_id": 0, "name": "~IOREF", "num": "1"},
        {"pin_id": 1, "name": "~Reset", "num": "2"}
      ]
    }
  },
  "nets": {
    "VCC": [
      {"component": "U1", "pin_id": 3},
      {"component": "R1", "pin_id": 0}
    ]
  },
  "subcircuits": [
    {
      "name": "Power_Supply",
      "description": "5V to 3.3V regulation",
      "components": {},
      "nets": {}
    }
  ]
}
```

### Key Elements

- **Components**: Dictionary of components with symbols, footprints, and pins
- **Nets**: Connectivity information mapping net names to component pins
- **Subcircuits**: Nested circuit hierarchies for modular design
- **Metadata**: Descriptions, annotations, and design intent

## Implementation Details

### Core Classes

1. **NetlistExporter** (`core/netlist_exporter.py`)
   - Handles `to_dict()` conversion from Circuit objects
   - Manages hierarchical traversal
   - Generates both JSON and KiCad netlists

2. **JSON Loader** (`io/json_loader.py`)
   - `load_circuit_from_json_file()`: Reads JSON files
   - `load_circuit_from_dict()`: Reconstructs Circuit objects
   - Handles net connectivity and pin mappings

3. **JSON Encoder** (`core/json_encoder.py`)
   - Custom encoder for circuit-synth types
   - Handles Enum serialization
   - Supports objects with `to_dict()` methods

### Workflow Integration

1. **Direct JSON Export**:
   ```python
   circuit.generate_json_netlist("my_circuit.json")
   ```

2. **KiCad Project Generation** (uses JSON internally):
   ```python
   circuit.generate_kicad_project("my_project")
   ```

3. **Round-trip Conversion**:
   ```python
   # Import from KiCad
   circuit = load_circuit_from_kicad("project.kicad_pro")
   
   # Modify in Python
   circuit.add_component(...)
   
   # Export back to KiCad
   circuit.generate_kicad_project("project_updated")
   ```

## Performance Optimization



## Benefits

1. **Single Source of Truth**: JSON serves as the definitive circuit representation
2. **Tool Agnostic**: Any tool can read/write the JSON format
3. **Version Control**: Text-based format works perfectly with Git
4. **Extensibility**: Easy to add new fields without breaking compatibility
5. **Debugging**: Human-readable format simplifies troubleshooting

## Schema Documentation

For detailed JSON schema documentation including field descriptions, data types, and examples, see [JSON_SCHEMA.md](JSON_SCHEMA.md).

## Future Considerations

- **Schema Validation**: Implement JSON Schema validation using the documented schema
- **Streaming Support**: Handle very large circuits efficiently
- **Binary Format**: Optional binary encoding for performance
- **API Versioning**: Maintain compatibility as format evolves