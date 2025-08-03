# KiCad ↔ Python Bidirectional Architecture

## Current Architecture Analysis

### KiCad → Python Pipeline
```
KiCad Project → kicad-cli netlist → KiCadNetlistParser → CircuitData → PythonCodeGenerator → Python File
```

**Status**: ✅ Working but has reference designator bug

### Python → KiCad Pipeline  
```
Python File → Circuit Object → KiCadSchematicWriter → KiCad Files
```

**Status**: ✅ Working completely

### Missing: Selective Update Pipeline
```
Existing Python + KiCad Changes → CanonicalAnalysis → SelectiveUpdate → Updated Python
```

**Status**: ❌ Not implemented

## Key Components Discovered

### Available Synchronizer Classes
- `circuit_synth.kicad.sch_sync.synchronizer.SchematicSynchronizer`
- `circuit_synth.kicad.sch_sync.synchronizer.CircuitMatcher`  
- `circuit_synth.kicad.sch_sync.synchronizer.ComponentMatcher`

**Status**: Classes exist but require project paths and canonical analysis

### Command Structure
```bash
uv run kicad-to-python <kicad_project> <python_file> [--backup] [--verbose]
```

**Behavior**: 
- If `python_file` is directory: creates `main.py` inside
- If `python_file` is file: overwrites completely (no selective update)
- `--backup` creates `.backup` file before overwriting

## Required Architecture for True Bidirectional

### 1. Detection Logic
```python
if os.path.exists(python_file) and is_circuit_synth_file(python_file):
    mode = "selective_update"
else:
    mode = "full_generation"
```

### 2. Canonical Comparison Engine
```python
canonical_kicad = CanonicalCircuit.from_kicad_project(kicad_path)
canonical_python = CanonicalCircuit.from_python_file(python_path)  
changes = canonical_kicad.compare(canonical_python)
```

### 3. Selective Update Engine
```python
for change in changes:
    if change.type == "component_added":
        insert_component_in_python(change.component)
    elif change.type == "component_modified":  
        update_component_in_python(change.component)
    elif change.type == "net_changed":
        update_connections_in_python(change.nets)
    # Preserve everything else unchanged
```

## Implementation Strategy

### Phase 1: Fix Reference Bug
- Investigate `kicad_netlist_parser.py` 
- Ensure proper reference designator extraction
- Test with existing workflow

### Phase 2: Canonical Analysis  
- Implement missing `circuit_synth.kicad.canonical` module
- Enable structural circuit comparison
- Test component matching logic

### Phase 3: Selective Updates
- Build update engine that preserves user modifications
- Handle conflicts between Python and KiCad changes
- Maintain file structure and formatting

## Testing Strategy
Use existing `bidirectional_update_test/` framework with step-by-step validation to verify each component works correctly.