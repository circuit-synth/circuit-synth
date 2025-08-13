# PRD: Modular S-Expression API for Bi-Directional KiCad Sync

**Document Version:** 1.0  
**Date:** 2025-01-12  
**Author:** Circuit-Synth Development Team  

## Executive Summary

This PRD defines a comprehensive modular S-expression API for circuit-synth that enables precise, atomic operations on KiCad schematic files. The API will support bi-directional synchronization between Python circuit descriptions and KiCad schematics, allowing AI agents to make granular modifications like "add a linear voltage regulator" or "remove the unnecessary capacitor."

## Goals & Objectives

### Primary Goals
1. **Atomic Operations**: Enable precise addition/removal of individual schematic elements
2. **Bi-Directional Sync**: Support loading, modifying, and saving existing KiCad schematics
3. **AI Agent Integration**: Provide granular APIs for AI-powered incremental modifications
4. **Preservation**: Maintain original file formatting and structure during modifications
5. **Performance**: Support efficient operations for large schematics

### Success Metrics
- AI agents can successfully add/remove components with single function calls
- Original schematic formatting preserved in 100% of cases
- Zero data loss during load/modify/save operations
- API supports all KiCad schematic element types
- Performance scales to schematics with 1000+ components

## Current State Analysis

### Existing Architecture
- **S-Expression Parser** (`s_expression.py`): Handles parsing/writing KiCad files
- **Type System** (`types.py`): Clean dataclass-based types for schematic elements
- **Manager Classes**: `ComponentManager`, `WireManager` for specific elements
- **Project Generator**: Creates complete KiCad projects from circuit descriptions

### Pain Points
1. **All-or-nothing generation**: Cannot modify existing schematics incrementally
2. **Coupled operations**: File I/O mixed with schematic building logic
3. **No state tracking**: Cannot determine what's already in a schematic
4. **Limited precision**: Cannot make targeted changes without regenerating everything

### Inspiration from kicad-skip
The kicad-skip library provides excellent patterns we can adapt:
- **Atomic element operations**: `schem.symbol.R1.delete()`, `schem.wire.new()`
- **State queries**: `schem.symbol.R1.property.MPN.value`
- **Named attribute access**: `schem.symbol.U1`, `schem.label.VCC`
- **Preservation**: Original file structure maintained during save
- **Search capabilities**: `reference_matches()`, `within_circle()`

## Detailed Requirements

### 1. Core API Structure

#### 1.1 SchematicBuilder (New)
```python
class SchematicBuilder:
    @staticmethod
    def create_blank(name: Optional[str] = None) -> ModularSchematic:
        """Create minimal .kicad_sch structure with required sections"""
        
    @staticmethod
    def load_from_file(filepath: str) -> ModularSchematic:
        """Load existing schematic preserving all original content"""
        
    @staticmethod
    def from_circuit_synth_circuit(circuit) -> ModularSchematic:
        """Convert circuit-synth Circuit object to modular schematic"""
```

#### 1.2 ModularSchematic (New)
```python
class ModularSchematic:
    # State Management
    def has_lib_symbol(self, lib_id: str) -> bool
    def has_component_by_reference(self, reference: str) -> bool
    def get_component_by_uuid(self, uuid: str) -> Optional[SchematicSymbol]
    
    # Atomic Operations
    def add_lib_symbol_definition(self, lib_id: str) -> bool
    def add_symbol(self, component: SchematicSymbol) -> str  # Returns UUID
    def remove_symbol_by_uuid(self, uuid: str) -> bool
    def update_symbol_by_uuid(self, uuid: str, **kwargs) -> bool
    
    # File Operations (Separated)
    def to_sexp(self) -> List  # Generate S-expression data
    def write_to_file(self, filepath: str) -> None
    def save(self) -> None  # Overwrite original file
```

### 2. Atomic Element Operations

#### 2.1 Component Operations
```python
# Add component with automatic lib_symbol handling
uuid = schematic.add_symbol(SchematicSymbol(
    reference="R1",
    value="10k", 
    lib_id="Device:R",
    position=Point(50, 100),
    footprint="Resistor_SMD:R_0603_1608Metric"
))

# Query before adding
if not schematic.has_lib_symbol("Device:R"):
    schematic.add_lib_symbol_definition("Device:R")

# Update existing component
schematic.update_symbol_by_uuid(uuid, position=Point(75, 100))

# Remove component
schematic.remove_symbol_by_uuid(uuid)
```

#### 2.2 Component Search & Listing
```python
# Find all components (inspired by kicad-skip)
components = schematic.find_components()
resistors = schematic.find_components_by_reference_pattern(r"R\d+")
specific_value = schematic.find_components_by_value("10k")

# Get component by reference (most common case)
component = schematic.get_component_by_reference("R1")
```

#### 2.3 State Tracking
```python
# Explicit state queries
defined_libs = schematic.get_defined_lib_symbols()
all_references = schematic.get_all_references()
uuid_mapping = schematic.get_uuid_to_reference_mapping()

# Validation
issues = schematic.validate_consistency()  # Returns list of issues
```

### 3. Load/Modify/Save Workflow

#### 3.1 File Preservation Strategy
- **Preserve**: Original formatting, comments, order of elements, UUIDs
- **Modify**: Only the specific elements being changed
- **Track**: What was modified for potential rollback

```python
# Load with full preservation
schematic = SchematicBuilder.load_from_file("existing.kicad_sch")

# Track modifications
with schematic.modification_tracker() as tracker:
    uuid = schematic.add_symbol(new_component)
    schematic.remove_symbol_by_uuid(old_uuid)
    
    # Can rollback if needed
    if validation_fails:
        tracker.rollback()

# Save with preservation
schematic.save()  # Only modified elements change, rest preserved
```

#### 3.2 Error Handling
Since validation requires opening in KiCad, focus on prevention:
```python
# Preventive measures - each operation validates itself
uuid = schematic.add_symbol(component)  # Validates lib_symbol exists
schematic.remove_symbol_by_uuid(uuid)   # Validates UUID exists

# Simple error handling - let operations fail cleanly
try:
    uuid = schematic.add_symbol(component)
except LibSymbolNotFoundError:
    # Log error and continue with next operation
    logger.error(f"Symbol {component.lib_id} not found")
```

### 4. Integration with Circuit-Synth

#### 4.1 User API Unchanged
The existing user syntax remains identical:
```python
from circuit_synth import *

@circuit(name="USB_Port")
def usb_port(vbus_out, gnd, usb_dp, usb_dm):
    usb_conn = Component(symbol="Connector:USB_C_Receptacle_USB2.0_16P", ...)
    # ... existing code works unchanged
```

#### 4.2 Internal Conversion
```python
# Internal circuit-synth logic uses modular API
def generate_kicad_project(circuit, project_name):
    # Convert to modular schematic
    schematic = SchematicBuilder.from_circuit_synth_circuit(circuit)
    
    # Use atomic operations for hierarchical sheets
    for subcircuit in circuit._subcircuits:
        sub_schematic = SchematicBuilder.from_circuit_synth_circuit(subcircuit)
        schematic.add_hierarchical_sheet(sub_schematic)
    
    # Write files
    schematic.write_to_file(f"{project_name}.kicad_sch")
```

### 5. AI Agent Integration

#### 5.1 Natural Language to Operations
```python
# AI agent receives: "add a linear voltage regulator"
regulator = Component(
    symbol="Regulator_Linear:AMS1117-3.3",
    ref="U",
    footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2"
)

# Agent uses atomic API
schematic = SchematicBuilder.load_from_file("board.kicad_sch")
uuid = schematic.add_symbol(regulator)  # Handles lib_symbols automatically
schematic.save()

# AI agent receives: "remove the unnecessary capacitor C5"
c5_component = schematic.get_component_by_reference("C5")
if c5_component:
    schematic.remove_symbol_by_uuid(c5_component.uuid)
    schematic.save()
```

#### 5.2 Sequential Operations
```python
# Agents make individual atomic changes
schematic = SchematicBuilder.load_from_file("board.kicad_sch")

# Add components one by one
for component in new_components:
    uuid = schematic.add_symbol(component)  # Each operation is atomic
    
# Remove components individually  
for reference in ["C5", "R10", "U3"]:
    component = schematic.get_component_by_reference(reference)
    if component:
        schematic.remove_symbol_by_uuid(component.uuid)

schematic.save()  # Save all changes
```

## Implementation Phases

### Phase 1: Core Infrastructure
- [ ] `ModularSchematic` class with basic operations
- [ ] `SchematicBuilder.create_blank()` 
- [ ] Atomic `add_symbol()` with lib_symbol handling
- [ ] Basic state queries (`has_lib_symbol`, etc.)
- [ ] Separate S-expression generation from file I/O

### Phase 2: Load/Modify/Save
- [ ] `SchematicBuilder.load_from_file()` with preservation
- [ ] `remove_symbol_by_uuid()` and `update_symbol_by_uuid()`
- [ ] Component search/listing functions
- [ ] Modification tracking for rollback

### Phase 3: Integration & Polish  
- [ ] Integration with existing circuit-synth generators
- [ ] Performance optimization for large schematics
- [ ] Comprehensive test suite
- [ ] AI agent helper functions

### Phase 4: Extended Elements
- [ ] Atomic operations for wires, labels, junctions
- [ ] Hierarchical sheet operations
- [ ] Text and annotation operations
- [ ] PCB integration (future)

## Technical Architecture

### File Structure
```
src/circuit_synth/kicad/modular/
├── __init__.py
├── schematic_builder.py     # SchematicBuilder class
├── modular_schematic.py     # ModularSchematic class  
├── element_operations.py    # Atomic operations for each element type
├── state_tracker.py         # State management and validation
├── preservation.py          # File preservation strategies
└── conversion.py            # Circuit-synth to modular conversion
```

### Dependencies
- Existing `s_expression.py` for low-level parsing
- Existing `types.py` for data structures
- `symbol_cache.py` for library symbol management
- Consider integration with kicad-skip patterns

### Performance Considerations
- Lazy loading of lib_symbols (only load when needed)
- Efficient UUID-based lookups with internal indexing
- Individual atomic operations (no batching complexity)
- Incremental validation rather than full validation

## Success Criteria

### Functional Requirements
✅ **Atomic Operations**: Single function calls for add/remove/update  
✅ **State Tracking**: Always know what's in the schematic  
✅ **File Preservation**: Original formatting maintained  
✅ **Bi-directional Sync**: Load → Modify → Save workflow  
✅ **AI Integration**: Natural language to precise modifications  

### Non-Functional Requirements
✅ **Performance**: Handle 1000+ component schematics efficiently  
✅ **Reliability**: Zero data loss during operations  
✅ **Maintainability**: Clean separation of concerns  
✅ **Extensibility**: Easy to add new element types  
✅ **Compatibility**: Works with all KiCad versions we support  

## Risks & Mitigations

### Technical Risks
1. **KiCad Format Changes**: Mitigate by comprehensive testing across versions
2. **Performance with Large Files**: Mitigate by lazy loading and efficient indexing  
3. **File Corruption**: Mitigate by atomic writes and backup strategies
4. **Memory Usage**: Mitigate by streaming large files and efficient data structures

### Integration Risks  
1. **Breaking Existing Code**: Mitigate by maintaining existing APIs unchanged
2. **AI Agent Complexity**: Mitigate by providing simple, high-level helper functions
3. **Testing Coverage**: Mitigate by comprehensive test schematics and edge cases

## Next Steps

1. **Create GitHub Issues** for each Phase 1 task
2. **Set up Development Environment** with test schematics
3. **Design Review** with stakeholders before implementation
4. **Prototype** `ModularSchematic` with basic operations
5. **Integrate** with existing circuit-synth workflow

---

This PRD provides the foundation for creating a world-class modular S-expression API that will enable precise, AI-powered modifications to KiCad schematics while maintaining full compatibility with existing circuit-synth workflows.