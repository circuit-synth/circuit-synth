# Rust KiCad Integration Report

## Executive Summary

This report analyzes the current state of the circuit-synth codebase and proposes a plan to integrate the new Rust KiCad schematic generation module to replace the existing Python implementation.

## Current State Analysis

### 1. What is Working Now (Python Implementation)

The current Python implementation uses the following workflow:

1. **Entry Point**: `Circuit.generate_kicad_project()` in `src/circuit_synth/core/circuit.py`
2. **Schematic Generation**: `SchematicGenerator` in `src/circuit_synth/kicad/sch_gen/main_generator.py`
3. **Schematic Writing**: `SchematicWriter` in `src/circuit_synth/kicad/sch_gen/schematic_writer.py`
4. **Component Management**: Uses `ComponentManager` and `PlacementEngine`
5. **S-expression Generation**: Uses Python `sexpdata` library for formatting

**Key Features:**
- Hierarchical circuit support via subcircuits
- Component placement algorithms (collision-aware, connection-aware)
- Symbol library caching
- Reference management (U1, U2, R1, R2, etc.)
- Wire and net generation
- JSON as intermediate format

### 2. New Rust Implementation

The Rust module (`rust_modules/rust_kicad_integration`) provides:

**Core Capabilities:**
- `PyRustSchematicWriter`: Main schematic writer class
- `create_minimal_schematic()`: Create empty schematics
- `add_component_to_schematic()`: Add components to existing schematics
- `remove_component_from_schematic()`: Remove components
- `add_hierarchical_label_to_schematic()`: Add hierarchical labels
- `generate_schematic_from_python()`: Complete schematic generation

**Key Features:**
- Fast S-expression generation using `lexpr`
- Hierarchical label generation
- Component and net management
- Direct Python bindings via PyO3
- Schematic editing capabilities

**Available Python Functions:**
```python
rust_kicad_schematic_writer.PyRustSchematicWriter
rust_kicad_schematic_writer.create_minimal_schematic()
rust_kicad_schematic_writer.add_component_to_schematic()
rust_kicad_schematic_writer.remove_component_from_schematic()
rust_kicad_schematic_writer.add_hierarchical_label_to_schematic()
rust_kicad_schematic_writer.generate_schematic_from_python()
```

## Integration Plan

### Phase 1: Replace Core Schematic Generation

**Goal**: Replace the Python S-expression generation with Rust while keeping the same API.

**Changes Required:**

1. **Modify `SchematicWriter` class** (`src/circuit_synth/kicad/sch_gen/schematic_writer.py`):
   - Replace S-expression generation with Rust calls
   - Keep existing placement logic
   - Maintain component management

2. **Update `SchematicGenerator`** (`src/circuit_synth/kicad/sch_gen/main_generator.py`):
   - Use Rust writer for final output
   - Convert circuit data to Rust-compatible format

3. **Create adapter layer**:
   - Convert Python Circuit objects to Rust CircuitData format
   - Handle hierarchical circuits (flattening for Rust)
   - Map component and net data structures

### Phase 2: Integration Implementation

**File Structure Changes:**

```python
# src/circuit_synth/kicad/rust_adapter.py (NEW)
import rust_kicad_schematic_writer
import logging

class RustSchematicAdapter:
    """Adapter to use Rust schematic generation from Python."""
    
    def __init__(self, circuit):
        self.circuit = circuit
        self.rust_writer = None
        
    def convert_to_rust_format(self):
        """Convert Python circuit to Rust-compatible format."""
        circuit_data = {
            "name": self.circuit.name,
            "components": self._convert_components(),
            "nets": self._convert_nets(),
            "subcircuits": self._convert_subcircuits()
        }
        return circuit_data
        
    def generate_schematic(self, output_path):
        """Generate schematic using Rust backend."""
        circuit_data = self.convert_to_rust_format()
        config = {"paper_size": "A4", "generator": "rust_kicad_schematic_writer"}
        
        # Use Rust to generate schematic
        schematic_content = rust_kicad_schematic_writer.generate_schematic_from_python(
            circuit_data, config
        )
        
        # Write to file
        with open(output_path, 'w') as f:
            f.write(schematic_content)
```

**Modified workflow:**

```python
# In SchematicGenerator.generate()
def generate(self, json_file, **kwargs):
    # ... existing setup code ...
    
    # NEW: Use Rust for schematic generation
    if USE_RUST_BACKEND:
        from circuit_synth.kicad.rust_adapter import RustSchematicAdapter
        adapter = RustSchematicAdapter(circuit)
        adapter.generate_schematic(schematic_path)
    else:
        # Existing Python implementation
        self._generate_schematic_python(circuit, schematic_path)
```

### Phase 3: Testing Strategy

1. **Unit Tests**:
   - Test Rust adapter conversion functions
   - Verify data structure mappings
   - Test individual Rust functions

2. **Integration Test**:
   - Run `ESP32_C6_Dev_Board_python/main.py`
   - Compare output with reference schematic
   - Verify component placement

3. **Visual Verification**:
   - Generate PDF using `kicad-cli`
   - Confirm components are placed correctly
   - Check hierarchical labels

## Implementation Steps

1. **Create new branch**: `feature/rust-kicad-integration`
2. **Add logging**: Extensive debug logging for data flow
3. **Create adapter**: `rust_adapter.py` with conversion logic
4. **Modify generator**: Update `SchematicGenerator` to use Rust
5. **Test incrementally**: Start with simple circuits, then hierarchical
6. **Remove old code**: Once validated, remove Python S-expression generation

## Risk Mitigation

1. **Keep Python fallback**: Use feature flag to switch between implementations
2. **Incremental replacement**: Replace one function at a time
3. **Extensive logging**: Debug data conversion issues
4. **Parallel testing**: Run both implementations and compare outputs

## Success Criteria

- ✅ ESP32_C6_Dev_Board_python/main.py generates valid KiCad files
- ✅ Components appear in correct positions
- ✅ Hierarchical circuits are handled correctly
- ✅ Performance improvement (target: 5x faster)
- ✅ All existing tests pass
- ✅ PDF output shows correct schematic

## Next Steps

1. Create feature branch
2. Implement Rust adapter layer
3. Add comprehensive logging
4. Test with simple circuit first
5. Progress to hierarchical ESP32 example
6. Generate PDF for visual verification