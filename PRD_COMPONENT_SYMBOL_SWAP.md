# PRD: Component Symbol Type Change Support

**Issue:** Test 19 failing - Changing component symbol (Device:R → Device:C) in Python doesn't update the KiCad schematic
**Branch:** `fix/component-symbol-swap-not-working`
**Date:** 2025-10-28

---

## Problem Statement

### Current Behavior
When a user changes a component's symbol type in Python code (e.g., `symbol="Device:R"` → `symbol="Device:C"`), regenerating the KiCad project does NOT update the component symbol in the schematic. The component retains its original symbol (resistor) even though the Python code specifies a different symbol (capacitor).

### Observed Logs
```
Synchronization Summary:
   ✅ Keep: R1 (matches Python)
```

The synchronizer reports "Keep: R1" indicating it found a match and kept the existing component without checking if the symbol changed.

### Root Cause
The `_needs_update()` method in `synchronizer.py:1075-1091` only checks:
1. `value` changes
2. `footprint` changes
3. BOM/board inclusion flags

It does **NOT** check for `lib_id` (symbol type) changes:
```python
def _needs_update(self, circuit_comp: Dict, kicad_comp: SchematicSymbol) -> bool:
    """Check if a component needs updating."""
    if circuit_comp["value"] != kicad_comp.value:
        return True
    if (
        circuit_comp.get("footprint")
        and circuit_comp["footprint"] != kicad_comp.footprint
    ):
        return True
    # ... BOM flags check ...
    return False
    # ❌ NO lib_id check!
```

---

## Expected Behavior

### User Workflow
1. Generate circuit with R1 as Device:R (resistor)
2. Open in KiCad, component appears at position (100, 50)
3. Change Python code: `symbol="Device:R"` → `symbol="Device:C"`
4. Regenerate KiCad project
5. **Expected:** Component at (100, 50) now shows capacitor symbol (Device:C)
6. **Expected:** Reference remains "R1", position preserved

### Test Validation (Test 19)
```python
# After regeneration with changed symbol:
assert c1.reference == "R1"  # Reference preserved
assert "C" in str(c1.lib_id)  # Symbol changed to capacitor
assert c1.position.x == 100.0  # Position preserved
assert c1.uuid == original_uuid  # UUID preserved
```

---

## Technical Analysis

### Symbol Change Complexity

**Key Challenge:** Changing a symbol in KiCad is NOT a simple property update. It requires:
1. Removing the old component instance
2. Creating a new component with the new symbol
3. Preserving position, reference, UUID, and all connections

**Why this is difficult:**
- Different symbols have different pin configurations (resistor has pins 1,2; transistor has B,C,E)
- Pin positions and orientations differ between symbols
- Net connections must be re-established with new pins
- UUID must be preserved for position tracking

### Current Synchronizer Architecture

The synchronizer uses three operations for components:
1. **KEEP** - Component matched, properties may be updated
2. **ADD** - New component from Python
3. **REMOVE** - Component exists in KiCad but not in Python

For symbol changes, we need a **REPLACE** operation:
1. Detect symbol mismatch
2. Remove old component (preserving metadata)
3. Add new component with new symbol
4. Restore position, reference, UUID
5. Re-establish net connections

---

## Proposed Solution

### Approach 1: Add Symbol Check to _needs_update() ✅ RECOMMENDED

**Pros:**
- Minimal code changes
- Leverages existing update infrastructure
- Clear and simple logic

**Cons:**
- May not handle all edge cases (pin count mismatch)
- Requires `component_manager.update_component()` to support `lib_id` changes

**Implementation:**
```python
def _needs_update(self, circuit_comp: Dict, kicad_comp: SchematicSymbol) -> bool:
    """Check if a component needs updating."""
    # Existing checks...
    if circuit_comp["value"] != kicad_comp.value:
        return True
    if circuit_comp.get("footprint") and circuit_comp["footprint"] != kicad_comp.footprint:
        return True

    # NEW: Check for symbol change
    circuit_symbol = circuit_comp.get("symbol")
    if circuit_symbol and circuit_symbol != str(kicad_comp.lib_id):
        logger.info(f"Symbol change detected for {kicad_comp.reference}: {kicad_comp.lib_id} → {circuit_symbol}")
        return True

    # BOM flags check...
    return False
```

Then enhance `component_manager.update_component()` to handle `lib_id` changes:
```python
def update_component(self, reference, value=None, footprint=None, lib_id=None):
    """Update component properties including symbol type."""
    comp = self._find_component(reference)
    if not comp:
        return False

    if value is not None:
        comp.value = value
    if footprint is not None:
        comp.footprint = footprint
    if lib_id is not None:
        # This is the KEY change - update lib_id
        comp.lib_id = lib_id

    self.schematic._modified = True
    return True
```

### Approach 2: Detect and Replace Component

**Pros:**
- More explicit control over the replacement process
- Can handle pin configuration changes
- Clear separation of concerns

**Cons:**
- More complex implementation
- Risk of breaking UUID/position preservation
- More code to maintain

**Implementation:**
```python
def _process_matches(self, circuit_components, kicad_components, matches, report):
    for circuit_id, kicad_ref in matches.items():
        circuit_comp = circuit_components[circuit_id]
        kicad_comp = kicad_components[kicad_ref]

        # NEW: Check for symbol change (requires replace, not update)
        if self._symbol_changed(circuit_comp, kicad_comp):
            logger.info(f"Symbol change detected for {kicad_ref} - replacing component")
            self._replace_component(circuit_comp, kicad_comp, report)
            continue

        # Existing rename and update logic...
```

---

## Risk Assessment

### High Risk Areas
1. **Pin Connection Loss**: When replacing component, connections to nets must be preserved
2. **UUID Preservation**: UUID matching relies on UUID staying the same
3. **Position Drift**: Component position must be exactly preserved
4. **Multi-sheet Circuits**: Symbol changes in hierarchical sheets

### Medium Risk Areas
1. **Reference Collision**: New symbol might conflict with existing references
2. **Footprint Compatibility**: New symbol might require different footprint
3. **Value Semantics**: Resistor "10k" vs Capacitor "10k" have different meanings

### Low Risk Areas
1. **BOM Impact**: Symbol change shouldn't affect BOM
2. **Wire Routing**: Wires might need repositioning but should stay connected

---

## Implementation Plan

### Phase 1: Detection (Quick Win)
**Effort:** 15 minutes

1. Add symbol check to `_needs_update()`:
   ```python
   circuit_symbol = circuit_comp.get("symbol")
   if circuit_symbol and circuit_symbol != str(kicad_comp.lib_id):
       return True
   ```

2. Test if `kicad-sch-api` allows direct `lib_id` updates:
   ```python
   comp.lib_id = "Device:C"  # Does this work?
   ```

3. Run test 19 to see if detection works

### Phase 2: Simple Update (If lib_id is mutable)
**Effort:** 30 minutes

1. Enhance `component_manager.update_component()` to accept `lib_id` parameter
2. Update the component's `lib_id` property
3. Test with simple cases (R→C, C→R)
4. Verify position, reference, UUID preserved

### Phase 3: Replace Strategy (If lib_id is immutable)
**Effort:** 2 hours

1. Implement `_replace_component()` method:
   - Store old component metadata (position, reference, UUID, value, footprint)
   - Remove old component
   - Add new component with new symbol
   - Restore all metadata
   - Re-establish net connections

2. Add pin mapping logic for connection preservation

3. Test with multiple symbol types

### Phase 4: Edge Case Handling
**Effort:** 1 hour

1. Handle pin count mismatches (e.g., resistor → transistor)
2. Handle orientation differences
3. Test with power symbols (#PWR components)
4. Test with hierarchical sheets

---

## Test Strategy

### Unit Tests
1. Test `_needs_update()` detects symbol changes
2. Test `update_component()` with `lib_id` parameter
3. Test symbol string comparison logic

### Integration Tests (Test 19)
```python
# Test 19 workflow:
1. Generate with Device:R
2. Move to (100, 50)
3. Change to Device:C
4. Regenerate
5. Assert:
   - Symbol changed: Device:C ✓
   - Reference preserved: R1 ✓
   - Position preserved: (100, 50) ✓
   - UUID preserved ✓
```

### Edge Case Tests
1. Symbol change with net connections
2. Symbol change in hierarchical sheet
3. Symbol change with power symbols
4. Multiple symbol changes in one regeneration

---

## Success Criteria

### Minimal Success (Phase 1-2)
- Test 19 passes
- Device:R → Device:C works
- Position and reference preserved
- No regression in other tests

### Full Success (Phase 3-4)
- All symbol type changes work (R, C, L, diodes, transistors, etc.)
- Pin connections preserved
- Works in hierarchical circuits
- Clear error messages for impossible changes

---

## Open Questions

1. **Can `kicad-sch-api` update `lib_id` directly?**
   - Need to test: `component.lib_id = "Device:C"`
   - If yes → Simple update approach (Phase 2)
   - If no → Replace approach needed (Phase 3)

2. **How to handle pin configuration changes?**
   - Resistor (pins 1,2) → Transistor (pins B,C,E)
   - Need intelligent pin mapping or user guidance

3. **Should we support all symbol changes or limit to same-pin-count symbols?**
   - Conservative: Only allow changes with matching pin count
   - Aggressive: Allow all changes, warn about connection loss

4. **What about footprint compatibility?**
   - Should we validate that new symbol supports the existing footprint?
   - Or trust the user to update footprint separately?

---

## Next Steps

1. **Investigation (10 min):**
   - Check if `kicad-sch-api` allows `lib_id` mutation
   - Look for existing `lib_id` update code

2. **Quick Fix (Phase 1-2, 30 min):**
   - Add symbol check to `_needs_update()`
   - Try simple `lib_id` update
   - Run test 19

3. **Decision Point:**
   - If simple update works → Ship it! ✅
   - If not → Plan Phase 3 implementation

4. **Create GitHub Issue:**
   - Document the limitation
   - Link to this PRD
   - Track implementation progress

---

## Related Work

- **Test 18 (Power Symbol Replacement):** Recently fixed power symbol replacement when nets change - similar "replace not update" pattern
- **Component Manager:** Existing `update_component()` method handles value/footprint
- **UUID Matching:** Relies on UUID persistence for position preservation

---

## References

- Test file: `/Users/shanemattner/Desktop/circuit-synth2/tests/bidirectional/19_swap_component_type/test_19_swap_component_type.py`
- Synchronizer: `/Users/shanemattner/Desktop/circuit-synth2/src/circuit_synth/kicad/schematic/synchronizer.py:1075-1091`
- Component Manager: `/Users/shanemattner/Desktop/circuit-synth2/src/circuit_synth/kicad/schematic/component_manager.py`

---

**Status:** PRD Complete - Ready for investigation phase
**Priority:** Medium (Test 19 marked xfail, but users likely expect this to work)
**Complexity:** Low-Medium (depends on kicad-sch-api mutability)
