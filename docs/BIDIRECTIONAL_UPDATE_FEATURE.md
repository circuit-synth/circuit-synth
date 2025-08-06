# Bidirectional Update Feature

*Circuit-Synth's seamless Python ↔ KiCad synchronization system*

## Overview

The Bidirectional Update Feature enables seamless synchronization between Python circuit definitions and KiCad projects, allowing users to work fluidly between both domains without losing manual work or circuit logic changes.

### Core Vision

**Preserve the best of both worlds:**
- **Python**: Programmable circuit generation, version control, parametric designs
- **KiCad**: Professional PCB layout, component positioning, routing, manufacturing preparation

**Primary Workflows:**

**Workflow 1: Legacy Project Integration**
```
Existing KiCad Project → Import to Python → Modify Circuit Logic → Re-export to KiCad
```

**Workflow 2: New Project Development**
```
New Circuit-Synth Project → Export to KiCad → Manual Edits → Import to Python → 
Python Edits → Export to KiCad → Manual Edits → Repeat...
```

## Feature Capabilities

### What It Can Do

✅ **Round-trip Synchronization**
- Import existing KiCad projects to Python circuit representations
- Export Python circuits to KiCad projects with full schematic generation
- Maintain circuit integrity through multiple sync cycles

✅ **Manual Work Preservation**
- Preserve component positions set by users in KiCad
- Maintain wire routing and trace layouts
- Keep text annotations, labels, and documentation
- Preserve hierarchical sheet arrangements and organization

✅ **Trust-Based Synchronization**
- Python-to-KiCad: Python circuit definition is authoritative for circuit logic
- KiCad-to-Python: KiCad project is authoritative for circuit structure
- No conflict resolution dialogs - source domain is always correct

✅ **Intelligent Component Placement**
- Add new Python-generated components off to the side without overlapping
- Preserve existing component positions and manual routing
- Maintain schematic organization and readability

✅ **Hierarchical Project Support**
- Handle multi-level hierarchical schematics
- Preserve subcircuit relationships and connections
- Support complex project structures with multiple sheets

### What It Cannot Do (Current Limitations)

❌ **Real-time Synchronization** - Manual sync process required
❌ **PCB Layout Synchronization** - Focus is on schematic-level changes
❌ **Component Library Management** - Users must ensure consistent libraries
❌ **Bidirectional Conflict Detection** - Source domain is always authoritative

## Technical Implementation

### Core Components

**1. KiCadToPythonSyncer**
- Parses KiCad project files (.kicad_pro, .kicad_sch)
- Extracts circuit structure, components, nets, and connections
- Generates Python circuit-synth code that recreates the circuit

**2. Python-to-KiCad Export Pipeline**
- Converts circuit-synth Python circuits to KiCad S-expression format
- Generates complete KiCad project files with proper UUIDs and metadata
- Handles hierarchical structures and subcircuits

**3. Canonical Component Matching**
- Matches components between domains using symbol + value + footprint
- Preserves user positioning even when reference designators change
- Handles component property updates without losing placement

**4. Smart Update System**
- Maintains sync metadata to track component placement and user modifications
- Identifies existing vs. new components for placement decisions
- Preserves manual work while applying source domain changes

### Data Flow Architecture

```
┌─────────────────┐    Import     ┌─────────────────┐
│   KiCad Project │ ───────────→  │ Python Circuit  │
│   (.kicad_sch)  │               │ (circuit-synth) │
└─────────────────┘               └─────────────────┘
         │                                 │
         │                                 │ Modify Logic
         │ Preserve                        │ Add Components
         │ Manual Work                     │ Change Values
         │                                 │
         ▼                                 ▼
┌─────────────────┐    Export     ┌─────────────────┐
│ Updated KiCad   │ ◄─────────── │ Modified Python │
│ Project         │               │ Circuit         │
└─────────────────┘               └─────────────────┘
```

### Sync Metadata Format

The system maintains a `.circuit_synth_sync.json` file alongside KiCad projects:

```json
{
  "last_sync_timestamp": "2025-01-27T10:30:00Z",
  "python_source_hash": "abc123...",
  "kicad_components": {
    "R1": {
      "uuid": "component-uuid-here",
      "position": {"x": 50, "y": 60},
      "user_modified": true,
      "properties": {"value": "1k", "footprint": "..."}
    }
  },
  "sync_version": "1.0"
}
```

## Trust-Based Update Strategy

### Core Principle: Source Domain Authority

**Python-to-KiCad Updates:**
- Python circuit definition is authoritative for all circuit logic
- Component properties, values, connections: Python wins
- Component positions, routing, annotations: KiCad preserved
- New components: Placed off to the side to avoid overlaps

**KiCad-to-Python Updates:**
- KiCad project is authoritative for circuit structure
- Import exactly what exists in KiCad schematic
- Generate Python code that matches KiCad circuit definition

### Update Behaviors

**1. Component Updates (Python → KiCad)**
- **Existing components**: Update properties, preserve position
- **New components**: Place in available space off to the side
- **Deleted components**: Remove from circuit, preserve routing for manual cleanup

**2. Property Updates**
- **Values**: Apply Python values to existing components
- **Footprints**: Update footprint assignments from Python
- **References**: Maintain canonical matching, preserve KiCad references if desired

**3. Net Updates**
- **New nets**: Create with Python-defined connections
- **Modified nets**: Update connections according to Python logic
- **Existing routing**: Preserve manual wire routing and placement

**4. Placement Strategy**
- **Collision avoidance**: Place new components where they don't overlap existing work
- **Side placement**: Add components to right/bottom of existing schematic area
- **Grid alignment**: Maintain KiCad's standard grid alignment for new components

### No-Conflict Philosophy

Users understand that:
- When running Python → KiCad sync: Python circuit logic takes precedence
- When running KiCad → Python sync: KiCad structure takes precedence
- Manual positioning and routing work is always preserved
- No dialogs, prompts, or user intervention required

## Current Implementation Status

### Completed Features ✅

**Core Synchronization Pipeline**
- KiCad → Python import working
- Python → KiCad export working  
- Round-trip preservation validated
- Hierarchical project support implemented

**Component Matching System**
- Canonical component identification
- Position preservation across syncs
- Reference designator independence

**Test Infrastructure**
- 3/15 planned bidirectional tests passing
- Round-trip validation working
- Real project integration tests

### In Development 🚧

**Python-to-KiCad Smooth Updates (TOP PRIORITY)**
- Preserve all existing KiCad manual work during Python updates
- Smart component placement without overlaps
- Maintain schematic organization and routing

**Enhanced Placement System**
- Collision detection for component placement
- Intelligent side-placement algorithms
- Grid alignment for professional appearance

### Planned Features 📋

**User Experience Improvements**
- Visual diff preview before sync
- Undo/rollback capability for sync operations
- Better feedback during sync operations

**Advanced Synchronization**
- Partial sync (specific components/nets only)
- Integration with KiCad's native backup system
- Performance optimization for large circuits

## Test Coverage Status

### Completed Tests

| Test | Description | Status | Coverage |
|------|-------------|--------|----------|
| 01 | Basic Python→KiCad Generation | ✅ | Core export |
| 02 | KiCad→Python Import | ✅ | Core import |
| 03 | Round-Trip Verification | ✅ | Full cycle |
| 04 | Hierarchical Structures | ⚠️ | Partial |

### Test Coverage Gaps

**Missing Test Scenarios:**
- Python-to-KiCad smooth updates without disruption
- Component placement collision avoidance
- Manual component addition preservation in KiCad
- Complex hierarchy restructuring
- Large circuit stress testing

**Integration Test Issues:**
- KiCad schematic format compatibility
- Netlist generation failures
- LLM-generated code variability

### Test Strategy

**Current Approach:**
- Unit tests for core synchronization functions
- Integration tests with real KiCad projects
- Round-trip validation with structure comparison
- Manual inspection with `PRESERVE_FILES=1` flag

**Planned Improvements:**
- Automated placement collision testing
- Visual diff testing for schematic changes
- Performance benchmarks for large circuits
- Trust-based workflow simulation tests

## Usage Examples

### Basic Import Workflow

```python
# Import existing KiCad project
from circuit_synth.tools.kicad_to_python_sync import KiCadToPythonSyncer

syncer = KiCadToPythonSyncer(
    kicad_project="my_circuit.kicad_pro",
    python_file="./python_output/",
    preview_only=False
)

success = syncer.sync()
```

### Modify and Re-export

```python
# Load the imported circuit
from my_circuit import main_circuit
from circuit_synth import Component, Net

@circuit
def enhanced_circuit():
    # Use the imported circuit as base
    base = main_circuit()
    
    # Add new components
    filter_cap = Component("Device:C", ref="C", value="100nF", 
                          footprint="Capacitor_SMD:C_0603_1608Metric")
    
    # Export back to KiCad with conflict detection
    return circuit

# Generate KiCad project with trust-based sync
circuit = enhanced_circuit()
circuit.generate_kicad_project("enhanced_circuit", 
                               force_regenerate=False)  # Preserve manual work
```

### Trust-Based Sync

```python
# Simple, reliable sync - no user interaction required
from circuit_synth import Circuit

# Python is authoritative - updates KiCad project
circuit = my_enhanced_circuit()
circuit.generate_kicad_project("my_project", 
                               force_regenerate=False)  # Preserves manual work

# KiCad is authoritative - updates Python code
from circuit_synth.tools.kicad_to_python_sync import KiCadToPythonSyncer

syncer = KiCadToPythonSyncer("my_project.kicad_pro", "./python_output/")
syncer.sync()  # Generates Python code from KiCad state
```

## Future Roadmap

### Phase 1: Smooth Python-to-KiCad Updates (Current)
- Perfect preservation of manual KiCad work during Python updates
- Smart component placement without overlaps
- Comprehensive testing of update scenarios

### Phase 2: Advanced Features
- Visual diff preview system
- Partial synchronization capabilities
- Enhanced metadata tracking

### Phase 3: Integration & Polish
- Git integration for change tracking
- KiCad plugin for seamless workflow
- Performance optimization for large circuits

### Phase 4: Ecosystem Integration
- Integration with other PCB tools
- Cloud-based synchronization options
- Collaborative design features

## Technical Requirements

### System Requirements
- KiCad 9.0+ installed and accessible
- Python 3.8+ with circuit-synth package
- Sufficient disk space for project files and metadata

### Dependencies
- `circuit-synth` core library
- KiCad command-line tools (`kicad-cli`)
- Standard library modules: `json`, `pathlib`, `shutil`

### Performance Characteristics
- **Small circuits** (< 50 components): ~1-2 seconds sync time
- **Medium circuits** (50-200 components): ~3-5 seconds sync time  
- **Large circuits** (200+ components): ~5-15 seconds sync time
- **Memory usage**: Typically < 100MB for most circuits

## Contributing

### Development Setup
1. Install circuit-synth development environment
2. Run bidirectional test suite: `./scripts/run_all_tests.sh --bidirectional`
3. Use `PRESERVE_FILES=1` for manual test inspection
4. Follow TDD approach for new conflict resolution features

### Testing Guidelines
- All conflict resolution scenarios must have automated tests
- Use real KiCad projects for integration testing
- Validate both directions of synchronization
- Test with hierarchical and flat project structures

---

*This document represents the current state and future vision of the Bidirectional Update Feature. As implementation progresses, this document will be updated to reflect new capabilities and refinements.*