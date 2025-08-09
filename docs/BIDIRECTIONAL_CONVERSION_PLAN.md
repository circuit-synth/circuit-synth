# Bidirectional Python ↔ KiCad Conversion Plan

## Overview

This document outlines the complete implementation plan for bidirectional conversion between Python circuit-synth code and KiCad schematics. The system enables users to work seamlessly in either Python or KiCad with frequent back-and-forth updates while preserving manual edits.

### Supersedes Previous Approach
This plan supersedes the approach documented in BIDIRECTIONAL_UPDATE_INVESTIGATION.md. Key differences:
- **New**: Surgical S-expression manipulation instead of using existing APISynchronizer
- **New**: Hierarchical labels only (no wire generation)
- **New**: Components matched by symbol+value+topology (footprints excluded)
- **New**: Complete bidirectional implementation from scratch

## Core Requirements

### Workflow Support
- Users can work in Python or KiCad and update bidirectionally
- Frequent back-and-forth updates without data loss
- Source of truth depends on update direction (KiCad→Python means KiCad is truth)

### Scope
- **In Scope**: Circuit components and hierarchical labels (net connections) only
- **Preserved but Untouched**: User graphics, text annotations, images, positioning, wires
- **Auto-generated**: Power flags, no-connect flags as needed
- **NOT Generated**: Wire connections between components (only hierarchical labels for nets)

### Technical Constraints
- KiCad version 9+ only
- JSON as the sole intermediate format
- Support hundreds of components across multiple subcircuits
- Hierarchical sheets map directly to Python subcircuits

## Architecture

### Data Flow
```
Python Circuit ←→ JSON (Canonical Format) ←→ KiCad Schematic
```

### Core Components

#### 1. KiCadSchematicSurgeon
Precisely manipulates KiCad schematic files without touching non-circuit elements.

```python
class KiCadSchematicSurgeon:
    """Surgical manipulation of KiCad schematics"""
    
    def remove_component(self, sch_file: Path, component_id: str):
        """Remove specific component and its connections"""
        # 1. Parse S-expressions
        # 2. Find component by canonical ID
        # 3. Remove component node
        # 4. Remove orphaned wire segments
        # 5. Write back preserving all other content
        
    def add_component(self, sch_file: Path, component: Component):
        """Add new component to schematic"""
        # 1. Parse S-expressions
        # 2. Generate KiCad UUID
        # 3. Find clear space for placement
        # 4. Insert component node
        # 5. Add wire connections
```

#### 2. Canonical Component Matching
Components are matched using symbol + value + topology, not reference designators or footprints.
Note: Footprints are PCB-specific and not part of schematic identity.

```python
class ComponentMatcher:
    """Match components using canonical identification"""
    
    def get_canonical_id(self, component: Component) -> str:
        """Generate unique ID from properties + topology"""
        # Primary: symbol + value (NOT footprint - that's PCB-specific)
        base_id = f"{component.symbol}:{component.value}"
        
        # Secondary: electrical topology signature
        topology = self.get_topology_signature(component)
        
        return hash(base_id + topology)
        
    def get_topology_signature(self, component: Component) -> str:
        """Generate signature from electrical connections"""
        # Captures what the component connects to
        # E.g., "R between VCC and LED_ANODE"
```

#### 3. Update Report System
Tracks all changes during synchronization for user visibility.

```python
@dataclass
class UpdateReport:
    """Track all changes during bidirectional sync"""
    
    timestamp: datetime
    direction: str  # "kicad_to_python" or "python_to_kicad"
    
    # Component tracking
    components_added: List[ComponentInfo]
    components_removed: List[ComponentInfo]
    components_modified: List[ComponentChange]
    
    # Net tracking
    nets_added: List[str]
    nets_removed: List[str]
    connections_changed: List[ConnectionChange]
    
    # Warnings
    ambiguous_matches: List[str]
    orphaned_nets: List[str]
    
    def generate_report(self) -> str:
        """Generate human-readable report"""
```

Example report output:
```
=== Update Report ===
Direction: Python → KiCad
Timestamp: 2024-01-15 10:30:00

Components Added (3):
- R_10k_0603 between VCC and GPIO1
- C_100n_0603 between VCC and GND
- U_STM32F4 with 48 connections

Components Removed (1):
- R_1k_0603 (was between LED+ and GND)

Components Modified (2):
- R1: value changed 10k → 100k
- C1: footprint changed 0603 → 0805

Warnings:
- Ambiguous match: Two R_10k_0603 with identical topology
```

## Current State Investigation Needed

### Existing Infrastructure Status
The previous investigation suggests some infrastructure may already exist:
- `APISynchronizer` class that updates component properties without touching positions
- `HierarchicalSynchronizer` for handling subcircuits
- Default `force_regenerate=False` mode

### Key Questions to Investigate
1. **Does position preservation already work?** Previous doc claims it does via `APISynchronizer`
2. **What's the actual limitation with adding components?** Doc mentions hierarchical labels aren't created
3. **Is the existing synchronizer sufficient or do we need surgical S-expression manipulation?**
4. **What's the current state of KiCad→Python import?**

### Decision: New Implementation
Based on requirements, we will:
- Build new `KiCadSchematicSurgeon` for precise S-expression manipulation
- Create hierarchical labels (not wires) for net connections
- Match components by symbol+value+topology (not footprints)
- Implement proper bidirectional conversion with full round-trip fidelity

## Implementation Details

### S-Expression Handling
- Parse KiCad schematic files while preserving formatting
- Maintain exact indentation and structure
- Only modify component and net nodes
- Preserve all graphics, text, and other elements

### Component Placement Strategy
When adding new components from Python:
1. Analyze existing component positions
2. Find clear area (typically right side or bottom)
3. Place in grid-aligned position
4. Avoid overlapping existing elements

### Connection Management
- **Hierarchical Labels Only**: Generate hierarchical labels for net connections
- **No Wire Generation**: Do not create or modify wire segments
- **When removing components**: Remove associated hierarchical labels
- **When adding components**: Create hierarchical labels at pins for net connections
- **Preserve user's manual wire routing**: Never touch existing wires

### UUID Handling
- Generate KiCad-compatible UUIDs for new components
- Preserve existing UUIDs for matched components
- Track UUID mapping in conversion metadata

## Test Plan

### 1. Position Preservation Tests

#### test_component_position_preserved_after_move
- Create R1 (10k) in Python at default position
- Export to KiCad
- Move R1 to position (100, 50) in KiCad
- Change R1 value to 20k in Python
- Export to KiCad again
- **Verify**: R1 is 20k AND still at (100, 50)

#### test_multiple_components_position_preserved
- Create R1, R2, C1 in Python
- Export to KiCad
- Arrange components nicely in KiCad
- Add R3 in Python
- Export to KiCad
- **Verify**: R1, R2, C1 positions unchanged, R3 appears off to side

### 2. User Annotation Preservation Tests

#### test_text_box_preserved
- Create resistor in Python, export to KiCad
- Add text box "Design Rev A" in KiCad
- Change resistor value in Python
- Export to KiCad
- **Verify**: Text box still exists with same content and position

#### test_image_preserved
- Create circuit in Python, export to KiCad
- Add company logo image in KiCad
- Add new component in Python
- Export to KiCad
- **Verify**: Image still present, same position/size

#### test_graphic_lines_preserved
- Create circuit in Python
- Draw box around power section in KiCad
- Modify power section in Python
- Export to KiCad
- **Verify**: Box still exists around modified components

### 3. Bidirectional Component Addition Tests

#### test_component_added_in_kicad_appears_in_python
- Create R1 in Python, export to KiCad
- Add R2 manually in KiCad schematic editor
- Import KiCad to Python
- **Verify**: Python now has both R1 and R2
- **Verify**: Can modify R2 in Python and export back

#### test_component_added_in_python_appears_in_kicad
- Create R1 in Python, export to KiCad
- Move R1 to nice position in KiCad
- Add R2 in Python (connected to R1)
- Export to KiCad
- **Verify**: R2 appears near R1 but not overlapping

### 4. Component Removal Tests

#### test_component_removed_in_kicad_removed_from_python
- Create R1, R2, C1 in Python
- Export to KiCad
- Delete R2 in KiCad
- Import to Python
- **Verify**: Python only has R1 and C1

#### test_component_removed_in_python_removed_from_kicad
- Create R1, R2, C1 in Python, export
- Add text annotation near R2 in KiCad
- Remove R2 from Python
- Export to KiCad
- **Verify**: R2 gone, text annotation still there

#### test_remove_component_with_complex_routing
- Create resistor divider in Python
- Export to KiCad
- Route wires nicely with bends in KiCad
- Remove middle resistor in Python
- Export to KiCad
- **Verify**: Component gone, orphaned wires cleaned up

### 5. Value/Property Change Tests

#### test_value_changed_in_kicad_syncs_to_python
- Create R1=10k in Python, export
- Change R1 to 100k in KiCad property editor
- Import to Python
- **Verify**: Python shows R1=100k

#### test_footprint_changed_in_kicad_syncs_to_python
- Create R1 with 0603 footprint in Python
- Export to KiCad
- Change to 0805 footprint in KiCad
- Import to Python
- **Verify**: Python shows 0805 footprint

#### test_value_changed_in_python_updates_kicad
- Create C1=100nF in Python, export
- Move C1 to nice position in KiCad
- Change to C1=1uF in Python
- Export to KiCad
- **Verify**: C1 shows 1uF at same position

### 6. Net Connection Tests

#### test_net_renamed_in_python_updates_kicad
- Create circuit with VCC net in Python
- Export to KiCad
- Add text label "3.3V Power" near VCC in KiCad
- Rename VCC to VCC_3V3 in Python
- Export to KiCad
- **Verify**: Net renamed, text label still there

#### test_connection_changed_in_python
- R1 connected to VCC in Python, export
- Add decorative graphics in KiCad
- Connect R1 to VDD instead in Python
- Export to KiCad
- **Verify**: R1 now connected to VDD, graphics unchanged

### 7. Hierarchical Design Tests

#### test_subcircuit_added_in_python
- Create main circuit in Python, export
- Add graphics to main sheet in KiCad
- Add power_supply subcircuit in Python
- Export to KiCad
- **Verify**: New sheet created, main sheet graphics preserved

#### test_sheet_instance_modified_in_kicad
- Create hierarchical design in Python
- Export to KiCad
- Move sheet box, resize it in KiCad
- Add component to subcircuit in Python
- Export to KiCad
- **Verify**: Sheet box position/size preserved

### 8. Edge Case Tests

#### test_identical_components_different_positions
- Create two R=10k in Python at different nets
- Export to KiCad
- Move them to different positions
- Change one to 20k in Python
- Export to KiCad
- **Verify**: Correct resistor changed, positions preserved

#### test_component_with_no_connections
- Add mounting hole in Python (no connections)
- Export to KiCad
- Position it nicely in KiCad
- Add another mounting hole in Python
- Export to KiCad
- **Verify**: First hole position preserved

#### test_duplicate_net_names_handled
- Create net "SIGNAL" in Python, export
- Manually add different "SIGNAL" net in KiCad
- Import to Python
- **Verify**: Conflict detected and reported

### 9. Real-World Workflow Tests

#### test_iterative_design_workflow
Simulates real design iteration:
1. Create initial ESP32 + power circuit in Python
2. Export to KiCad
3. Arrange components nicely, add section labels in KiCad
4. Add sensor subcircuit in Python
5. Export to KiCad (verify layout preserved)
6. Fix sensor connections in KiCad
7. Import to Python (verify changes captured)
8. Add filtering caps in Python
9. Export to KiCad (verify everything preserved)

#### test_team_collaboration_workflow
Simulates two people working:
1. Person A: Creates MCU circuit in Python
2. Person B: Imports to KiCad, arranges nicely
3. Person A: Adds power management in Python
4. Person B: Pulls update, sees new components off to side
5. Person B: Arranges new components, adds notes
6. Person A: Imports back, continues development

### 10. Update Report Tests

#### test_update_report_shows_additions
- Create circuit, export to KiCad
- Add R1, C1 in Python
- Export with report generation
- **Verify** report shows: "Added: R1 (10k), C1 (100nF)"

#### test_update_report_shows_conflicts
- Create two identical resistors
- Export to KiCad
- Change one in KiCad
- Import to Python with report
- **Verify** report shows: "Warning: Ambiguous match for R_10k_0603"

## Test Organization

```
tests/bidirectional/
├── fixtures/
│   ├── simple_circuits/
│   ├── complex_circuits/
│   └── edge_cases/
├── test_position_preservation.py
├── test_annotation_preservation.py
├── test_component_operations.py
├── test_value_changes.py
├── test_net_operations.py
├── test_hierarchical.py
├── test_edge_cases.py
├── test_workflows.py
└── test_update_reports.py
```

## Implementation Timeline

### Phase 1: Core Infrastructure
- [ ] S-expression parser with preservation
- [ ] KiCadSchematicSurgeon implementation
- [ ] Canonical component matcher
- [ ] Basic update report

### Phase 2: Bidirectional Operations
- [ ] Python → KiCad with preservation
- [ ] KiCad → Python import
- [ ] Component add/remove/modify
- [ ] Net operations

### Phase 3: Test Implementation
- [ ] Position preservation tests
- [ ] Annotation preservation tests
- [ ] Component operation tests
- [ ] Workflow tests

### Phase 4: Polish & Documentation
- [ ] Enhanced update reports
- [ ] Performance optimization
- [ ] User documentation
- [ ] API finalization

## Success Criteria

1. **Zero Data Loss**: All user annotations, graphics, and positioning preserved
2. **Surgical Precision**: Only components/nets modified, nothing else touched
3. **Canonical Matching**: Components matched correctly regardless of reference changes
4. **Clear Reports**: Users understand exactly what changed
5. **Performance**: < 5 seconds for 500+ component circuits
6. **Reliability**: 100% round-trip fidelity for circuit topology