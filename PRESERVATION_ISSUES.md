# KiCad Preservation Mode Issues

## Issue 1: Subcircuit Components Not Matched

### Description
When running in update mode (`force_regenerate=False`), the synchronizer only matches top-level components and fails to properly match components within subcircuits.

### Test Case
Using the hierarchical_resistors_test example:
- Main circuit has: J1, J2, J3, C2, C3 (5 components)
- Subcircuits have: R1-R11 (11 resistors across multiple hierarchical levels)

### Current Behavior
```
=== MATCHING RESULTS ===
  Total circuit components: 5
  Total KiCad components: 10
  Total matches found: 5
    MATCHED: J1 -> J1
    MATCHED: J2 -> J2
    MATCHED: J3 -> J3
    MATCHED: C2 -> C2
    MATCHED: C3 -> C3
```

The resistors R1, R2, R9, R10, R11 are treated as "unmatched" and preserved, but the synchronizer doesn't look into subcircuits to find their corresponding definitions.

### Expected Behavior
The synchronizer should:
1. Recursively traverse all hierarchical sheets
2. Match components at all levels of the hierarchy
3. Properly update subcircuit components while preserving manual edits

### Root Cause Analysis
Looking at the logs:
```
Loading hierarchical sheet: power_input from power_input.kicad_sch
Loading hierarchical sheet: signal_processing from signal_processing.kicad_sch  
Loading hierarchical sheet: output_stage from output_stage.kicad_sch
```

The synchronizer loads the hierarchical sheets but only extracts components from the main circuit:
```python
# Step 2: Extract circuit components
circuit_components = self._extract_circuit_components(circuit)
```

This suggests `_extract_circuit_components` is not recursively extracting components from subcircuits.

## Issue 2: Missing Instance Information Warning

### Description
When preserving components, the system warns about missing instance information:
```
WARNING: Symbol R1 has no instances information - creating minimal instances
```

This happens for all preserved resistors (R1, R2, R9, R10, R11).

### Impact
This could lead to loss of:
- Component UUIDs
- Hierarchical path information
- Sheet-specific properties

## Issue 3: Incorrect Component Count

### Description
The synchronizer reports:
- Total circuit components: 5 (should be 16 - all components across all sheets)
- Total KiCad components: 10 (incomplete - not counting components in subcircuits)

This confirms the synchronizer is not properly handling hierarchical designs.

## Root Cause Confirmed

The synchronizer operates on a single schematic file at a time, not the entire hierarchical project:

1. `SyncAdapter` finds and loads only the main schematic file
2. `APISynchronizer` works with this single file
3. Hierarchical sheets are mentioned but not processed for component matching
4. Only top-level components in the main sheet are matched

## Proposed Solutions

### Solution 1: Fix Component Extraction
Modify `_extract_circuit_components` to recursively extract components from all subcircuits.

### Solution 2: Implement Hierarchical Project Synchronization
Create a new synchronizer that:
- Loads all .kicad_sch files in the project
- Builds a hierarchical tree matching the circuit structure
- Synchronizes each sheet with its corresponding subcircuit
- Maintains parent-child relationships

### Solution 3: Improve Hierarchical Matching
Implement hierarchical path-aware matching that considers:
- Component reference within its sheet context
- Full hierarchical path for unique identification
- Sheet-specific component properties

### Solution 4: Preserve Instance Information
Ensure that when preserving components, all metadata (instances, UUIDs, paths) is maintained.

## Next Steps

1. Investigate `_extract_circuit_components` implementation
2. Add recursive subcircuit traversal
3. Implement hierarchical path matching
4. Test with multi-level hierarchical designs
5. Ensure manual edits at all levels are preserved