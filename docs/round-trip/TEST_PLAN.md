# Round-Trip Update - Comprehensive Test Plan

## Overview
This document outlines the complete test coverage for round-trip schematic updates, ensuring professional workflows are fully supported.

## Test Categories

### 1. Component Manipulation Tests

#### 1.1 Position & Orientation
- [x] **Move component** - Change (x,y) position
- [ ] **Rotate component** - 0°, 90°, 180°, 270°
- [ ] **Mirror component** - Horizontal/vertical flip
- [ ] **Move multiple components** - Batch position changes
- [ ] **Component outside bounds** - Component near edge of sheet

#### 1.2 Component Properties
- [x] **Update value** - Change resistor 10k → 22k
- [ ] **Update footprint** - Change 0603 → 0805
- [ ] **Update reference** - Renumber components (R1 → R10)
- [ ] **Custom properties** - Add/modify custom fields
- [ ] **DNP flag** - Mark as Do Not Populate
- [ ] **Exclude from BOM** - in_bom flag
- [ ] **Field visibility** - Show/hide value/reference

#### 1.3 Component Lifecycle
- [x] **Add component in Python** - Generate → Update → Verify
- [ ] **Add component in KiCad** - Manual addition → Import to Python
- [ ] **Remove component in Python** - Generate → Update → Component gone
- [ ] **Remove component in KiCad** - Manual removal → Import to Python
- [ ] **Replace component** - Change symbol type (R → Potentiometer)

### 2. Wiring & Connection Tests

#### 2.1 Manual Routing
- [x] **Manual wire** - Add wire in KiCad → Verify preserved
- [ ] **Manual bus** - Add bus in KiCad → Verify preserved
- [x] **Junction** - Add junction → Verify preserved
- [ ] **No-connect** - Add no-connect flag → Verify preserved
- [ ] **Complex routing** - Multi-segment wires

#### 2.2 Net Labels & Power
- [x] **Local label** - Add label → Verify preserved
- [ ] **Global label** - Add global label → Verify preserved
- [ ] **Hierarchical label** - Add hierarchical pin → Verify preserved
- [ ] **Power symbols** - Add VCC, GND symbols → Verify preserved
- [ ] **Net name change** - Rename net in KiCad

### 3. Annotation & Documentation Tests

#### 3.1 Text & Graphics
- [ ] **Text box** - Add text box with notes → Verify preserved
- [ ] **Plain text** - Add text annotation → Verify preserved
- [ ] **Graphic line** - Add line → Verify preserved
- [ ] **Graphic rectangle** - Add box → Verify preserved
- [ ] **Graphic circle** - Add circle → Verify preserved
- [ ] **Unicode text** - Add text with special characters

#### 3.2 Design Notes
- [ ] **Review comments** - Add design review notes
- [ ] **Test points** - Mark test points in schematic
- [ ] **BOM notes** - Add assembly notes
- [ ] **Change markers** - Track design changes

### 4. Hierarchical Design Tests

#### 4.1 Sheet Management
- [ ] **Move sheet** - Change sheet position in project
- [ ] **Rename sheet** - Change sheet filename/title
- [ ] **Add sheet** - Create new hierarchical sheet manually
- [ ] **Remove sheet** - Delete hierarchical sheet
- [ ] **Nested sheets** - Multi-level hierarchy (sheet in sheet)

#### 4.2 Sheet Contents
- [ ] **Move component between sheets** - Drag from one sheet to another
- [ ] **Sheet-local labels** - Labels within sheet
- [ ] **Sheet pins** - Hierarchical connections
- [ ] **Sheet properties** - Custom sheet metadata

#### 4.3 Cross-Sheet Features
- [ ] **Hierarchical labels** - Sheet-to-sheet connections
- [ ] **Global labels across sheets** - Net spanning multiple sheets
- [ ] **Repeated instances** - Same sheet instantiated multiple times

### 5. Mixed Workflow Tests

#### 5.1 Python + Manual Hybrid
- [x] **Add components and import** - KiCad additions → Python sync
- [ ] **Manual + Generated coexistence** - Some components from Python, some manual
- [ ] **Partial regeneration** - Update only some subcircuits
- [ ] **Incremental design** - Add to existing manual design

#### 5.2 Team Collaboration
- [ ] **Concurrent edits** - Engineer A (Python) + Engineer B (KiCad manual)
- [ ] **Review workflow** - Generate → Review → Annotate → Re-generate
- [ ] **Version control integration** - Git merge scenarios

### 6. Edge Cases & Stress Tests

#### 6.1 Boundary Conditions
- [ ] **Empty schematic** - Generate into blank file
- [ ] **Very large schematic** - 100+ components
- [ ] **Very small schematic** - Single component
- [ ] **No changes** - Re-generate without modifications

#### 6.2 Data Integrity
- [ ] **Special characters** - Component names with unicode
- [ ] **Long strings** - Very long text in labels
- [ ] **Duplicate references** - Handle R1 collision
- [ ] **Invalid net names** - Special characters in nets

#### 6.3 Performance
- [ ] **Large update** - 100+ component position changes
- [ ] **Rapid iteration** - 10 consecutive generate cycles
- [ ] **Complex hierarchy** - 5+ levels deep

### 7. Format Preservation Tests

#### 7.1 KiCad Compatibility
- [ ] **Exact format match** - S-expression byte-for-byte
- [ ] **KiCad version** - Test with KiCad 7.x, 8.x, 9.x
- [ ] **Symbol library** - Preserve lib_symbols section
- [ ] **Formatting whitespace** - Preserve indentation

#### 7.2 Metadata Preservation
- [ ] **UUIDs** - Preserve component UUIDs
- [ ] **Timestamps** - Handle file metadata
- [ ] **Sheet instances** - Preserve instance paths
- [ ] **Paper size** - Preserve paper format (A4, A3, etc.)

## Priority Levels

### P0 - Critical (Must Have)
These are essential for basic round-trip functionality:
- ✅ Move component position
- ✅ Update component value
- ✅ Manual wire preservation
- ✅ Manual label preservation
- [ ] Rotate component
- [ ] Update footprint
- [ ] Add/remove components
- [ ] Hierarchical sheet support

### P1 - Important (Should Have)
These support common professional workflows:
- [ ] Custom properties
- [ ] DNP/BOM flags
- [ ] Text boxes/annotations
- [ ] Power symbols
- [ ] Global labels
- [ ] No-connect flags
- [ ] Sheet renaming
- [ ] Component rotation

### P2 - Nice to Have (Could Have)
These support advanced workflows:
- [ ] Graphic elements
- [ ] Complex multi-sheet hierarchy
- [ ] Net name changes
- [ ] Mirror/flip components
- [ ] Partial regeneration

## Test Implementation Status

### Implemented Tests
**Location:** `tests/integration/test_roundtrip_preservation.py`

1. ✅ `test_component_position_preservation` - Basic position preservation
2. ✅ `test_value_update_with_position_preservation` - Value update + position
3. ✅ `test_wire_preservation` - Manual wire preservation
4. ✅ `test_label_preservation` - Manual label preservation

### Needed Tests (Next Priority)

#### Component Tests
```python
def test_component_rotation_preservation()
def test_component_footprint_update()
def test_component_reference_change()
def test_add_component_via_python()
def test_remove_component_via_python()
def test_dnp_flag_preservation()
```

#### Hierarchical Tests
```python
def test_sheet_rename_preservation()
def test_sheet_move_preservation()
def test_nested_hierarchy_preservation()
def test_hierarchical_labels()
```

#### Workflow Tests
```python
def test_manual_component_addition()
def test_manual_plus_generated_coexistence()
def test_power_symbol_preservation()
def test_text_box_preservation()
def test_global_label_preservation()
```

#### Edge Cases
```python
def test_empty_schematic_generation()
def test_large_schematic_100_components()
def test_unicode_in_labels()
def test_rapid_iteration_10_cycles()
```

## Real-World Workflow Test Scenarios

### Scenario 1: Initial Design to Production
1. Generate voltage regulator circuit
2. Open in KiCad, arrange for readability
3. Add decoupling caps manually (not in Python)
4. Add power symbols (VCC, GND)
5. Add text box: "Rev A - Initial prototype"
6. Update regulator value in Python (3.3V → 5V)
7. Re-generate → Verify all manual work preserved

### Scenario 2: Design Review Iteration
1. Generate initial circuit
2. Reviewer adds text boxes with comments
3. Reviewer marks R5 with DNP flag
4. Designer fixes issues in Python
5. Re-generate → Comments and DNP flags preserved

### Scenario 3: Hierarchical Refactoring
1. Generate flat design
2. Manually create power supply sheet
3. Move components to power sheet
4. Rename sheets for clarity
5. Continue developing main circuit in Python
6. Re-generate → Sheet structure preserved

### Scenario 4: Team Collaboration
1. Engineer A: Generates MCU circuit in Python
2. Engineer B: Opens KiCad, adds USB connector manually
3. Engineer B: Routes USB differential pairs
4. Engineer B: Adds impedance notes
5. Engineer A: Updates MCU pin assignments
6. Re-generate → B's USB work fully preserved

## Test Automation Strategy

### Unit Tests (Fast, Isolated)
- Individual component operations
- Single feature tests
- Mock KiCad file operations
- Location: `tests/unit/test_roundtrip_*.py`

### Integration Tests (Comprehensive)
- Full generate → modify → regenerate cycle
- Real KiCad file I/O
- kicad-sch-api integration
- Location: `tests/integration/test_roundtrip_*.py`

### Manual Tests (Visual Verification)
- Open in KiCad GUI
- Visual inspection of layout
- Complex real-world scenarios
- Location: `tests/manual/roundtrip_demos/`

## Success Criteria

A test passes if:
1. ✅ Manual edits are byte-for-byte preserved
2. ✅ Python-defined changes are applied
3. ✅ KiCad can open file without errors
4. ✅ No warnings in kicad-sch-api
5. ✅ UUIDs remain stable
6. ✅ Performance < 1s for typical circuit

## Future Enhancements

- [ ] Dry-run mode (preview changes before applying)
- [ ] Change report (diff of what changed)
- [ ] Conflict detection (warn on risky changes)
- [ ] Selective update (update only certain components)
- [ ] Undo/rollback support
