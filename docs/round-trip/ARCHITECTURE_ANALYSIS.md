# Round-Trip Schematic Update Architecture Analysis

**Date**: 2025-10-12
**Branch**: `feature/perfect-roundtrip`
**Status**: Architecture Analysis Complete

## Executive Summary

✅ **Good News**: The differential update architecture ALREADY EXISTS and is largely functional!
❌ **The Problem**: Format preservation issues in the GENERATION path, not the UPDATE path.

## Current Architecture

### Two Distinct Code Paths

#### 1. GENERATION Path (Fresh Projects)
```
generate_kicad_project()
  └─> _prepare_blank_project()
  └─> _collision_place_all_circuits()
  └─> SchematicWriter.generate_s_expr()
  └─> write_schematic_file()
```

**Used when**: No existing .kicad_pro or .kicad_sch files exist
**Result**: Creates brand new schematic from scratch

#### 2. UPDATE Path (Existing Projects)
```
generate_kicad_project()
  └─> _check_existing_project()  # Returns True
  └─> _update_existing_project()
      └─> HierarchicalSynchronizer (for hierarchical projects)
          OR SyncAdapter (for flat projects)
              └─> APISynchronizer
                  ├─> _match_components() (3 strategies)
                  ├─> _process_matches() (update values/footprints)
                  ├─> _process_unmatched() (add/remove/preserve)
                  └─> _save_schematic()
```

**Used when**: Existing .kicad_pro AND .kicad_sch files detected
**Result**: Merges changes while preserving user edits

### Automatic Mode Switching

From `main_generator.py:628-643`:
```python
if project_exists and not force_regenerate:
    logger.info("🔄 Automatically switching to update mode to preserve your work")
    try:
        return self._update_existing_project(json_file, draw_bounding_boxes)
    except Exception as e:
        logger.error("❌ Update failed: {e}")
        # Fall through to regeneration
```

**Key Point**: Users don't manually choose modes - the system automatically detects existing projects!

## What WORKS (Already Implemented)

### ✅ Component Matching (APISynchronizer)

Three sophisticated matching strategies:

1. **ReferenceMatchStrategy**: Match by reference designator (R1 → R1)
2. **ConnectionMatchStrategy**: Match by net connections (what's connected to what)
3. **ValueFootprintStrategy**: Match by component value and footprint

### ✅ Component Position Preservation

From `main_generator.py:1140-1221`:
```python
# Check if existing schematic file exists
existing_sch_path = self.project_dir / f"{c_name}.kicad_sch"
if existing_sch_path.exists():
    # Use canonical matching to find corresponding components
    # Extract positions for matched components
    for existing_ref, new_ref in matches.items():
        existing_positions[new_ref] = (x, y)
```

**Result**: Matched components keep their manual positions!

### ✅ Component Operations

- **Add new components**: Placed at edge using collision-free placement
- **Modify existing components**: Update value/footprint while preserving position
- **Preserve user components**: Optional flag to keep manually-added components
- **Remove deleted components**: When `preserve_user_components=False`

### ✅ Hierarchical Support

- `HierarchicalSynchronizer` handles multi-sheet projects
- `SyncAdapter` handles flat projects
- Automatic detection and appropriate synchronizer selection

## What DOESN'T WORK (Needs Fixing)

### ❌ Format Preservation Issues

**Problem**: 9 failing tests in `test_against_references.py`

**Root Cause**: The GENERATION path (SchematicWriter/Formatter) doesn't produce byte-perfect KiCad output.

**Specific Issues Identified**:

1. **Paper Format Quoting Bug**:
   ```
   Generated: (paper A4)        # Wrong
   Expected:  (paper "A4")      # Correct
   ```
   This is in kicad-sch-api's formatter

2. **UUID Normalization Not Working**:
   ```python
   # Test tries to normalize UUIDs but fails
   gen_normalized = self._normalize_for_comparison(generated)
   ref_normalized = self._normalize_for_comparison(reference)
   ```
   The normalization function isn't properly stripping UUIDs

### ❓ Wire/Label Preservation (Unknown Status)

**Observation**: `APISynchronizer` loads wires and labels from existing schematics but unclear if they're preserved during updates.

**Code Evidence**:
```python
# From synchronizer.py:139-144
for wire in sheet_schematic.wires:
    schematic.add_wire(wire)  # Loads wires

for label in sheet_schematic.labels:
    schematic.add_label(label)  # Loads labels
```

**Question**: Are these preserved in `_save_schematic()` or regenerated?

**Action Required**: Test wire/label preservation explicitly

### ❓ Annotation Preservation (Unknown Status)

**Observation**: No explicit code for preserving user annotations (text boxes, notes, etc.)

**Action Required**: Verify what happens to annotations during update

## Why Tests Are Failing

### The Key Insight

The failing tests are testing **GENERATION**, not **UPDATE**!

```python
def test_single_resistor(self):
    # Generates into a FRESH temp directory
    success, output, generated_path = self._run_test_script(script_path)

    # Compares generated output to reference
    is_identical, diff = self._compare_schematics(generated_path, reference_path)
```

**Test Flow**:
1. Create blank temp directory
2. Run Python circuit script
3. Generate fresh KiCad project (GENERATION path)
4. Compare to manually-created reference KiCad file
5. ❌ FAIL: Format doesn't match exactly

**What's NOT Being Tested**: The UPDATE path that preserves manual edits!

## What Needs to Be Done

### Priority 1: Fix Format Preservation in kicad-sch-api

**Location**: `kicad-sch-api/kicad_sch_api/core/formatter.py`

**Issues**:
1. Add quotes around paper size strings
2. Ensure consistent S-expression formatting
3. Fix any other format differences

**Acceptance Criteria**: All 9 failing tests in `test_against_references.py` pass

### Priority 2: Fix Test UUID Normalization

**Location**: `kicad-sch-api/tests/reference_tests/test_against_references.py`

**Issue**: `_normalize_for_comparison()` doesn't properly strip UUIDs

**Fix**: Improve regex pattern for UUID stripping

### Priority 3: Verify Wire/Label Preservation

**Action**: Create explicit tests for:
1. Generate project with wires
2. Manually add more wires in KiCad
3. Re-run Python script
4. Verify manually-added wires are preserved

### Priority 4: Test Complete Round-Trip

**Test Scenario**:
```
1. Generate project from Python
2. Open in KiCad and make edits:
   - Move components around
   - Route some wires manually
   - Add text annotations
   - Add power symbols
3. Modify Python script (add component, change value)
4. Re-run Python script
5. Verify:
   ✓ Manual positions preserved
   ✓ Manual wires preserved
   ✓ Annotations preserved
   ✓ New component added
   ✓ Modified value updated
```

## Architectural Strengths

1. **Automatic Mode Detection**: Users don't need to know about generation vs update
2. **Fallback on Error**: If update fails, falls back to regeneration
3. **Multiple Matching Strategies**: Robust component matching
4. **Modular Design**: Clean separation of concerns
5. **API-Based**: Uses kicad-sch-api for proper KiCad integration

## Architectural Gaps

1. **Wire/Label Handling**: Unclear if preserved during updates
2. **Annotation Support**: No explicit handling of user annotations
3. **Format Preservation**: Generation path doesn't match KiCad exactly
4. **Test Coverage**: No tests for the UPDATE path specifically

## Recommended Next Steps

1. ✅ Complete this architecture analysis (DONE)
2. 🔧 Fix paper format quoting in kicad-sch-api formatter
3. 🔧 Fix UUID normalization in tests
4. ✅ Run tests again - should pass after fixes
5. 🧪 Create wire/label preservation tests
6. 🧪 Create complete round-trip integration test
7. 📚 Document user-facing behavior and force_regenerate flag

## Code Locations Reference

### circuit-synth
- `src/circuit_synth/kicad/sch_gen/main_generator.py`
  - Lines 381-410: `_check_existing_project()`
  - Lines 412-478: `_update_existing_project()`
  - Lines 604-992: `generate_project()`
  - Lines 1080-1436: `_collision_place_all_circuits()` (position preservation)

### kicad-sch-api
- `kicad_sch_api/core/schematic.py`: Main Schematic class
- `kicad_sch_api/core/formatter.py`: S-expression formatting (NEEDS FIX)
- `tests/reference_tests/test_against_references.py`: Failing tests
- `circuit_synth/kicad/schematic/synchronizer.py`: APISynchronizer
- `circuit_synth/kicad/schematic/sync_adapter.py`: SyncAdapter
- `circuit_synth/kicad/schematic/hierarchical_synchronizer.py`: Hierarchical support

## Conclusion

The round-trip update system is **90% implemented** and the architecture is sound. The remaining 10% is:
- Fixing format preservation bugs (paper quoting)
- Verifying wire/label preservation works
- Adding comprehensive round-trip tests

The good news: Users can already benefit from position preservation in the update path. The bad news: Initial generation doesn't produce byte-perfect output, which makes testing harder.

**Focus areas for next 2 weeks**:
1. Fix kicad-sch-api format preservation (1 week)
2. Verify and test wire/label/annotation preservation (1 week)
