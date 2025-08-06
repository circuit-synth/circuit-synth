# Implementation Notes - Bidirectional Update

## Simple Implementation Approach - START HERE

### Phase 1: Minimal Working Implementation (Current Focus)

#### Step 1: Basic Component Matching
Start with the simplest case - match components by reference designator only:
```python
def find_matching_component(python_comp, kicad_components):
    """Find KiCad component matching Python component - v1 simple."""
    for kicad_comp in kicad_components:
        if python_comp.ref == kicad_comp.ref:
            return kicad_comp
    return None
```

#### Step 2: Position Extraction from KiCad
Read existing component positions from .kicad_sch:
```python
def extract_component_positions(kicad_sch_path):
    """Extract (x, y) positions of all components."""
    positions = {}
    # Parse .kicad_sch S-expressions
    # Find (symbol) blocks with (lib_id ...)
    # Extract (at x y angle) from each
    return positions  # {"R1": (50.8, 76.2), "R2": (50.8, 88.9)}
```

#### Step 3: Minimal Update Logic
Update KiCad preserving positions:
```python
def update_kicad_preserving_positions(python_circuit, kicad_project_path):
    """Simplest possible update - preserve positions, update values."""
    # 1. Load existing positions
    positions = extract_component_positions(kicad_project_path)
    
    # 2. Generate new KiCad project in temp
    temp_project = python_circuit.generate_kicad_project("temp")
    
    # 3. For each component in temp, restore position if exists
    for comp in temp_project.components:
        if comp.ref in positions:
            comp.position = positions[comp.ref]
    
    # 4. Write back to original location
    save_project(temp_project, kicad_project_path)
```

### Phase 2: Improved Matching (After Phase 1 Works)

#### Canonical Matching (symbol + value + footprint)
```python
def canonical_id(component):
    """Create canonical ID for matching."""
    return (component.symbol, component.value, component.footprint)

def match_components_canonical(python_comp, kicad_components):
    """Match using canonical ID instead of reference."""
    python_id = canonical_id(python_comp)
    for kicad_comp in kicad_components:
        if canonical_id(kicad_comp) == python_id:
            return kicad_comp
    return None
```

### Phase 3: Smart Placement (After Phase 2 Works)

#### New Component Placement
```python
def find_empty_space(existing_positions):
    """Find space for new component."""
    # Simple: place to the right of rightmost component
    if not existing_positions:
        return (50, 50)  # Default starting position
    max_x = max(pos[0] for pos in existing_positions.values())
    return (max_x + 20, 50)  # 20 units to the right
```

### Core Principles (Keep Simple!)
1. **Keep it simple** - No complex conflict resolution
2. **Trust the source** - Python or KiCad is always right
3. **Preserve manual work** - Never destroy user edits
4. **Fail gracefully** - Handle errors without corruption

## Implementation Steps

### Step 1: Fix Quote Escaping Bug
Location: KiCad S-expression generator (likely in Rust module)
```python
# Before: "Power symbol creates a global label with name "GND" , ground"
# After:  "Power symbol creates a global label with name \"GND\" , ground"
# Or:     "Power symbol creates a global label with name 'GND' , ground"
```

### Step 2: Add Preservation Check
```python
def generate_kicad_project(self, project_name, force_regenerate=False):
    project_path = Path(project_name)
    
    if not force_regenerate and project_path.exists():
        # Preservation mode
        return update_existing_project(self, project_path)
    else:
        # Full regeneration
        return generate_new_project(self, project_path)
```

### Step 3: Implement update_existing_project
```python
def update_existing_project(circuit, project_path):
    """Update existing KiCad project preserving manual edits."""
    
    # 1. Extract current state
    sch_file = project_path / f"{project_path.name}.kicad_sch"
    positions = extract_component_positions(sch_file)
    wires = extract_wire_segments(sch_file)
    annotations = extract_text_annotations(sch_file)
    
    # 2. Generate fresh project in temp
    temp_path = Path(tempfile.mkdtemp())
    circuit.generate_kicad_project(temp_path / "temp", force_regenerate=True)
    
    # 3. Apply preserved state
    temp_sch = temp_path / "temp" / "temp.kicad_sch"
    apply_positions(temp_sch, positions)
    apply_wires(temp_sch, wires)
    apply_annotations(temp_sch, annotations)
    
    # 4. Replace original with updated
    shutil.copy(temp_sch, sch_file)
    
    # 5. Clean up temp
    shutil.rmtree(temp_path)
```

## Current Blockers

1. **Quote Escaping Bug** - Prevents KiCad from opening generated files
2. **force_regenerate Not Implemented** - Parameter exists but logic missing
3. **No Preservation Infrastructure** - Need to build extraction/application functions

## Next Implementation Tasks

1. [ ] Fix quote escaping in S-expression generator
2. [ ] Implement basic preservation check in generate_kicad_project
3. [ ] Create position extraction/application functions
4. [ ] Test with simple_voltage_divider
5. [ ] Add wire preservation
6. [ ] Add annotation preservation
7. [ ] Handle component addition/removal
8. [ ] Implement canonical matching
9. [ ] Add smart placement for new components
10. [ ] Create comprehensive test suite