# KiCad API - Comprehensive KiCad Manipulation Library

A production-ready library for programmatic manipulation of KiCad schematics, designed to be modular and suitable for eventual open-source release.

## Overview

The KiCad API provides a high-level interface for:
- Reading and writing KiCad schematic files (.kicad_sch)
- Component management (add, remove, move, clone)
- Wire creation and routing
- Label and annotation management
- Spatial search and discovery
- Connection tracing
- Hierarchical design support

## Current Status

### Phase 1: Foundation ✅ COMPLETE
- Created modular directory structure
- Implemented core data types
- Built S-expression parser using sexpdata library
- Created symbol library cache with common components
- Basic schematic to/from S-expression conversion

### Phase 2: Component Management (In Progress)
- Will migrate existing component management from `sch_api/`
- Add enhanced placement algorithms
- Implement collision detection

### Phase 3: Wire Management (Planned)
- Wire creation and routing
- Pin-to-pin connections
- Junction management

### Phase 4: Search and Discovery (Planned)
- Spatial search with geometric shapes
- Connection tracing
- Property-based search

## Directory Structure

```
kicad_api/
├── __init__.py              # Main module initialization
├── README.md                # This file
├── core/                    # Core functionality
│   ├── __init__.py
│   ├── types.py            # Data structures
│   ├── s_expression.py     # S-expression parser
│   └── symbol_cache.py     # Symbol library cache
├── schematic/              # Schematic operations (planned)
│   ├── components.py       # Component management
│   ├── wires.py           # Wire management
│   ├── search.py          # Search functionality
│   └── connections.py     # Connection discovery
├── netlist/               # Netlist operations (planned)
├── utils/                 # Utility functions (planned)
└── examples/              # Example scripts
    └── test_basic_setup.py # Basic functionality test
```

## Quick Start

```python
from circuit_synth.kicad_api.core import (
    Schematic, SchematicSymbol, Wire, Label, Point,
    SExpressionParser, get_symbol_cache
)

# Create a new schematic
schematic = Schematic()
schematic.title = "My Circuit"

# Add a resistor
resistor = SchematicSymbol(
    reference="R1",
    value="10k",
    lib_id="Device:R",
    position=Point(50.0, 50.0)
)
schematic.add_component(resistor)

# Add a wire
wire = Wire(points=[
    Point(0, 0),
    Point(50, 0)
])
schematic.add_wire(wire)

# Save to file
parser = SExpressionParser()
sexp = parser.from_schematic(schematic)
parser.write_file(sexp, "my_circuit.kicad_sch")
```

## Core Components

### Data Types (`core/types.py`)
- `Point`: 2D coordinate
- `BoundingBox`: Rectangular area
- `SchematicSymbol`: Component representation
- `Wire`: Electrical connection
- `Label`: Text annotation
- `Junction`: Wire connection point
- `Schematic`: Complete schematic

### S-Expression Parser (`core/s_expression.py`)
- Uses `sexpdata` library for parsing
- Converts between KiCad format and internal structures
- Handles all KiCad schematic elements

### Symbol Cache (`core/symbol_cache.py`)
- Caches common component definitions
- Provides pin information
- Manages reference prefixes

## Dependencies

- `sexpdata`: S-expression parsing
- Python 3.8+

## Testing

Run the basic test suite:
```bash
python src/circuit_synth/kicad_api/examples/test_basic_setup.py
```

## Future Enhancements

1. **Component Management**
   - Auto-placement algorithms
   - Collision detection
   - Bulk operations

2. **Wire Management**
   - Routing algorithms (Manhattan, direct, diagonal)
   - Junction management
   - Wire manipulation

3. **Search and Discovery**
   - Spatial indexing with R-tree
   - Connection graph traversal
   - Complex query support

4. **Integration**
   - Merge with existing Circuit Synth infrastructure
   - Migration path for current users
   - Standalone package preparation

## Design Principles

1. **Modularity**: Each component is self-contained
2. **Extensibility**: Easy to add new features
3. **Compatibility**: Maintains KiCad file format integrity
4. **Performance**: Efficient operations on large schematics
5. **Usability**: Clean, intuitive API

## Contributing

This module is part of Circuit Synth but designed for eventual standalone release. When contributing:
- Follow existing patterns
- Add comprehensive tests
- Update documentation
- Ensure KiCad compatibility

## License

Part of the Circuit Synth project. Future standalone release will be under MIT or similar permissive license.