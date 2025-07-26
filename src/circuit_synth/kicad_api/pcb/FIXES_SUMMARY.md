# ComponentWrapper API Fixes Summary

## Overview
Fixed the ComponentWrapper API to unblock placement algorithms and ensure all tests pass.

## Issues Fixed

### 1. ComponentWrapper Initialization
**Problem**: ComponentWrapper expected a Footprint object but tests were passing individual parameters.

**Solution**: Modified `__init__` to accept multiple initialization styles:
- Single Footprint object: `ComponentWrapper(footprint)`
- Positional arguments: `ComponentWrapper(ref, footprint, value, position, pads)`
- Keyword arguments: `ComponentWrapper(reference="R1", footprint="R_0603", ...)`

### 2. Missing Properties
**Problem**: Tests expected `position` and `value` properties on ComponentWrapper.

**Solution**: Added properties to expose underlying footprint attributes:
```python
@property
def position(self) -> Point:
    return self.footprint.position

@property
def value(self) -> str:
    return self.footprint.value
```

### 3. Hierarchical Path Processing
**Problem**: The `hierarchical_path` property was stripping slashes from paths.

**Solution**: Simplified to return the path as-is from the footprint.

### 4. Locked Components in Force-Directed Placement
**Problem**: Force-directed placer was using `locked_refs` from kwargs instead of component's `is_locked` property.

**Solution**: Modified to use `comp.is_locked` property directly when adding components.

### 5. Nested ComponentGroups
**Problem**: ComponentGroup's `move` method assumed all items had a `footprint` attribute, but nested groups don't.

**Solution**: Added type checking to handle both ComponentWrapper and nested ComponentGroup instances:
```python
if isinstance(component, ComponentGroup):
    component.move(dx, dy)  # Recursive move
elif hasattr(component, 'is_locked') and not component.is_locked:
    # Move individual components
```

### 6. Read-Only Property Assignment
**Problem**: Test tried to modify the read-only `hierarchical_path` property.

**Solution**: Modified test to create new components with desired hierarchical paths instead of modifying existing ones.

## Test Results
All placement algorithm tests now pass:
- ✅ Hierarchical Placement
- ✅ Force-Directed Placement  
- ✅ Connectivity-Driven Placement
- ✅ Edge Cases

## Files Modified
1. `src/circuit_synth/kicad_api/pcb/placement/base.py` - ComponentWrapper fixes
2. `src/circuit_synth/kicad_api/pcb/placement/force_directed.py` - Locked component handling
3. `src/circuit_synth/kicad_api/pcb/placement/grouping.py` - Nested group support
4. `src/circuit_synth/kicad_api/examples/test_placement_algorithms.py` - Test improvements