# Current Architecture Overview

## High-Level Architecture

Circuit-synth is structured as a multi-layered Python framework with Rust performance modules and KiCad integration.

```
┌─────────────────────────────────────────────────────────────────┐
│                     User API Layer                             │
│  @circuit decorators, Circuit.generate_kicad_project()         │
└─────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│                     Core Framework                             │
│  Circuit, Component, Net, Pin classes                          │
└─────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│                  KiCad Integration                             │
│  Schematic/PCB generation, Symbol caching                      │
└─────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│                 Performance Modules (Rust)                     │
│  Placement algorithms, Symbol search, Netlist processing       │
└─────────────────────────────────────────────────────────────────┘
```

## Directory Structure

### Core Framework (`src/circuit_synth/`)

#### `core/`
- **circuit.py**: Main Circuit class with simplified `generate_kicad_project()` API
- **component.py**: Component class with symbol/footprint management
- **net.py**: Electrical net connections
- **pin.py**: Component pin definitions
- **decorators.py**: `@circuit` decorator for circuit definition functions

#### `kicad/`
Multi-layered KiCad integration:
- **unified_kicad_integration.py**: Main entry point via `create_unified_kicad_integration()`
- **sch_gen/**: Schematic generation with placement algorithms
- **sch_api/**: High-level schematic API operations  
- **sch_editor/**: Direct schematic file manipulation

#### `kicad_api/`
Lower-level KiCad file format handling:
- **schematic/**: Schematic-specific operations and utilities
- **pcb/**: PCB layout operations including placement algorithms
- **pcb/placement/**: Various placement strategies (force-directed, hierarchical, spiral)
- **pcb/routing/**: Routing support including Freerouting integration

#### `pcb/`
PCB-specific functionality and utilities:
- **ratsnest_generator.py**: Comprehensive ratsnest generation with MST/star topologies
- **simple_ratsnest.py**: Efficient netlist-to-ratsnest converter for PCB airwire visualization

#### `interfaces/`
Abstract interfaces for extensibility:
- **IKiCadIntegration**: KiCad integration contract
- **ICircuitModel**: Circuit modeling interface

### Performance Modules (`rust_modules/`)

Performance-critical operations implemented in Rust with Python bindings:

- **rust_core_circuit_engine/**: Core circuit data structures and operations
- **rust_force_directed_placement/**: Force-directed component placement
- **rust_netlist_processor/**: High-performance netlist processing  
- **rust_symbol_cache/**: Symbol library caching and search
- **rust_kicad_schematic_writer/**: Optimized KiCad file writing
- **rust_reference_manager/**: Reference generation and validation
- **rust_symbol_search/**: Fast symbol search with fuzzy matching

### Testing Infrastructure (`tests/`)

Comprehensive testing system added in recent merge:

- **functional_tests/**: End-to-end workflow testing
- **integration/**: KiCad sync integration tests
- **kicad/**: KiCad-specific functionality tests
- **unit/**: Unit tests for core components
- **test_data/**: KiCad 9 symbol libraries and test circuits
- **cache/**: Cache system testing and monitoring

## Key Design Patterns

### Circuit Definition Pattern
```python
@circuit
def my_circuit():
    # Define components, nets, and connections
    return Circuit("My Circuit")
```

### KiCad Generation Pattern  
```python
circuit = my_circuit()
circuit.generate_kicad_project(
    "project_name",  # Simplified API
    generate_ratsnest=True  # Add visual airwire connections (default: True)
)
```

### Component Placement
Multiple algorithms available in `kicad_api/pcb/placement/`:
- **Force-directed**: Organic layouts using physical simulation
- **Hierarchical**: Structured designs respecting circuit hierarchy
- **Spiral**: Compact arrangements for space-constrained designs
- **Connection-aware**: Default algorithm optimizing for connectivity

### Ratsnest Generation
Visual airwire connections showing unrouted net connections in PCB designs:
- **MST Topology**: Minimum spanning tree for optimal total wire length using Prim's algorithm
- **Star Topology**: Simple radial connections where all pads connect to first pad
- **KiCad Integration**: Generates dashed lines on technical layers for visualization
- **Pipeline Integration**: Automatically runs after PCB generation and file save
- **Netlist Parsing**: Efficient extraction of connections from KiCad netlist files

## Containerization Architecture

### Docker Infrastructure
Circuit-Synth supports containerized development and deployment through multiple Docker configurations:

- **Basic Container** (`Dockerfile`): Core Circuit-Synth functionality in lightweight container
- **KiCad Integration** (`docker/Dockerfile.kicad-integrated`): Multi-stage build with KiCad nightly
- **Cross-Platform** (`docker/Dockerfile.kicad-emulated`): Platform emulation for ARM64 compatibility
- **Production Ready** (`docker/Dockerfile.kicad-production`): Robust deployment with fallbacks

### Container Orchestration
- **Docker Compose**: Multiple configurations for different deployment scenarios
- **Architecture Detection**: `scripts/docker-kicad-modern.sh` for automatic platform detection
- **Library Management**: Volume mounting for KiCad symbol and footprint libraries
- **Environment Configuration**: Proper environment variables for KiCad library paths

### Development Workflow
```bash
# Build basic container
docker build -t circuit-synth:simple -f Dockerfile .

# Run with KiCad libraries
docker run --rm \
  -v "$(pwd)/examples":/app/examples \
  -v "$(pwd)/output":/app/output \
  -v "$(pwd)/kicad-libraries/symbols":/usr/share/kicad/symbols:ro \
  -v "$(pwd)/kicad-libraries/footprints":/usr/share/kicad/footprints:ro \
  -e KICAD_SYMBOL_DIR=/usr/share/kicad/symbols \
  -e KICAD_FOOTPRINT_DIR=/usr/share/kicad/footprints \
  circuit-synth:simple python examples/example_kicad_project.py
```

## Integration Architecture

### Symbol and Footprint Management
- **Symbol caching**: Rust-based high-performance caching via `rust_symbol_cache`
- **KiCad library parsing**: Integration with KiCad symbol libraries
- **Footprint management**: PCB footprint library handling for layout generation

### LLM Integration
- **Deprecated**: LLM-based placement removed for performance optimization
- **Future**: May reintegrate with lightweight local models
- **Current**: Using optimized collision-based placement algorithms

### Logging and Debugging
Comprehensive logging system in `core/logging/`:
- **Unified logging**: Across Python and Rust components
- **Performance monitoring**: Database logging and metrics
- **Context-aware logging**: Circuit generation operation tracking

## Agent System Architecture

### Agent Workflow Pattern
```
User Request → orchestrator → architect → code → Result
```

- **orchestrator**: Entry point, coordinates multi-step projects
- **architect**: Planning and analysis, breaks down complex tasks  
- **code**: Implementation using SOLID/KISS/YAGNI/DRY principles

### Development Workflow
1. Start with orchestrator for complex tasks
2. Use architect for planning and requirements analysis
3. Use code agent for implementation and reviews
4. Let orchestrator coordinate handoffs and integration

## Data Flow

### Circuit to KiCad Flow
1. **Circuit Definition**: User defines circuit with `@circuit` decorator
2. **Reference Finalization**: Auto-assign component references
3. **Temporary Serialization**: Create temporary JSON representation
4. **KiCad Generation**: Use SchematicGenerator with placement algorithms
5. **File Output**: Generate `.kicad_sch`, `.kicad_pcb`, `.kicad_pro` files
6. **Ratsnest Generation**: Add visual airwire connections to PCB (if enabled)
7. **Cleanup**: Remove temporary files

### Bidirectional Sync (Future)
- **KiCad → Python**: Import existing KiCad projects to circuit objects
- **Python → KiCad**: Export circuit changes back to KiCad files
- **Sync Scripts**: Available in `src/circuit_synth/scripts/`

## Performance Characteristics

### Rust Integration Benefits
- **Symbol search**: 10-100x faster than pure Python
- **Placement algorithms**: Efficient force-directed and hierarchical placement
- **Netlist processing**: High-performance circuit analysis
- **Memory efficiency**: Lower memory usage for large circuits

### Caching Strategy
- **Symbol caching**: Persistent symbol library caches
- **Reference management**: Efficient component reference generation
- **Footprint caching**: PCB footprint library optimization

## Current Limitations

### Intelligence Gaps
- **Component placement**: Functional but not optimized for professional layouts
- **Schematic arrangement**: Parts placed without logical grouping
- **Signal integrity**: Limited awareness of high-speed design considerations

### Technical Debt
- **JSON intermediates**: Still uses temporary JSON files for KiCad generation
- **Legacy API compatibility**: Some inconsistency between old and new APIs
- **Directory handling**: Some nested directory creation in legacy paths

### Integration Challenges
- **KiCad version support**: Primarily focused on KiCad 9
- **Symbol library management**: Complex integration with KiCad libraries
- **Cross-platform**: Some platform-specific behavior in file handling