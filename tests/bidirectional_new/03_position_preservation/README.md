# Test 03: Position Preservation

## Purpose

🔴 **CRITICAL TEST** - Validates that component positions in KiCad are preserved when Python scripts are re-run.

## Why This is Critical

**User Workflow**: Users spend significant time arranging components in KiCad for readability and routing. If positions reset every time they update Python code, the tool becomes unusable.

**Expected Behavior**:
- User places R1 at (50, 50) in KiCad
- User updates Python to change R1 value from 10k → 22k
- User re-runs script
- R1 stays at (50, 50) with new value 22k

## What This Tests

### Position Stability
- Component moved in KiCad → position preserved on Python update
- New component added in Python → doesn't disturb existing positions
- Component deleted in Python → remaining components don't move
- Multiple components rearranged → all positions preserved

### Auto-Placement
- New component in Python → auto-placed in empty space
- New component doesn't overlap existing components
- Auto-placement is deterministic (same position each run)

## Test Cases

### Test 3.1: Move Resistor → Rerun Script → Position Preserved
```python
# Setup:
# 1. Generate KiCad from Python (R1 auto-placed at X, Y)
# 2. Open KiCad, move R1 to (100, 100)
# 3. Modify Python (change value 10k → 22k)
# 4. Rerun script

# Expected:
# - R1 at (100, 100) ✓
# - R1 value now 22k ✓
# - Position DID NOT reset to auto-placement ✓
```

**Validates**: Core position preservation

### Test 3.2: Add Component → Existing Components Don't Move
```python
# Setup:
# 1. R1 at (50, 50), R2 at (100, 50) in KiCad
# 2. Add R3 in Python
# 3. Rerun script

# Expected:
# - R1 still at (50, 50) ✓
# - R2 still at (100, 50) ✓
# - R3 auto-placed somewhere else (e.g., 150, 50) ✓
```

**Validates**: Adding components doesn't disturb existing

### Test 3.3: Delete Component → Remaining Components Don't Move
```python
# Setup:
# 1. R1 at (50, 50), R2 at (100, 50), R3 at (150, 50)
# 2. Remove R2 from Python
# 3. Rerun script

# Expected:
# - R1 still at (50, 50) ✓
# - R2 removed ✓
# - R3 still at (150, 50) (didn't shift left!) ✓
```

**Validates**: Deletion doesn't trigger re-layout

### Test 3.4: Rearrange 5 Components → All Positions Preserved
```python
# Setup:
# 1. R1-R5 auto-placed in a row
# 2. User rearranges to a 2x3 grid in KiCad
# 3. Modify Python (change one value)
# 4. Rerun script

# Expected:
# - All 5 components in their manually-placed positions ✓
# - No components reverted to auto-placement ✓
```

**Validates**: Bulk rearrangement preserved

### Test 3.5: Auto-Placement is Deterministic
```python
# Setup:
# 1. Fresh circuit with R1, R2, R3 (no KiCad file yet)
# 2. Generate KiCad (auto-placement)
# 3. Delete KiCad files
# 4. Generate again (auto-placement)

# Expected:
# - R1, R2, R3 in same positions both times ✓
# - Deterministic placement algorithm ✓
```

**Validates**: Auto-placement is stable

### Test 3.6: Mixed: Some Positioned, Some New
```python
# Setup:
# 1. R1, R2 positioned manually in KiCad
# 2. Add R3, R4, R5 in Python
# 3. Rerun script

# Expected:
# - R1, R2 at manual positions ✓
# - R3, R4, R5 auto-placed around them ✓
# - No overlaps ✓
```

**Validates**: Hybrid manual + auto placement

## Implementation Notes

### How Position Preservation Works

**Storage**: Component positions stored in `.kicad_sch` file
```
(symbol (lib_id "Device:R") (at 100 100 0)
  (property "Reference" "R1" ...)
  ...
)
```

**Sync Logic**:
1. Python script runs
2. Syncer reads existing `.kicad_sch`
3. For each component in Python:
   - If component exists in KiCad → **preserve position**
   - If component is new → **auto-place**
4. Write updated `.kicad_sch` with preserved positions

**Key Code**:
- `kicad_integration/kicad_to_python_sync.py` - reads positions
- `kicad/schematic/placement.py` - auto-placement logic
- Position comparison uses tolerance (~0.1mm) for floating-point stability

## Files

### Manual Setup Required

1. **`fixtures/single_resistor/positioned_resistor.py`**
   ```python
   @circuit
   def positioned_resistor():
       r1 = Device_R()(value="10k")
   ```

2. **`fixtures/single_resistor/positioned_resistor.kicad_pro`**
   - Create in KiCad
   - Add R1, manually place at (100, 100)

### Test Files
- `test_move_resistor_position_preserved.py` - Test 3.1
- `test_add_component_no_movement.py` - Test 3.2
- `test_delete_component_no_movement.py` - Test 3.3
- `test_rearrange_multiple_preserved.py` - Test 3.4
- `test_auto_placement_deterministic.py` - Test 3.5
- `test_mixed_manual_auto_placement.py` - Test 3.6

## Expected Output

```
test_move_resistor_position_preserved PASSED
  ✓ R1 position: (100.0, 100.0) preserved
  ✓ R1 value updated: 10k → 22k
  ✓ No auto-placement triggered

test_add_component_no_movement PASSED
  ✓ R1 position unchanged: (50.0, 50.0)
  ✓ R2 position unchanged: (100.0, 50.0)
  ✓ R3 auto-placed: (150.0, 50.0)
  ✓ No overlaps detected
```

## Debugging

### Position Resets to Auto-Placement:
- Check if existing `.kicad_sch` is being read
- Verify component reference matches (R1 vs r1)
- Look for position read/write errors in logs

### Positions Slightly Different:
- Check tolerance in comparison (use ~0.1mm tolerance)
- Floating-point rounding may cause tiny differences
- Verify KiCad grid settings

### New Components Overlap Existing:
- Check auto-placement algorithm
- Verify bounding box calculation
- Look for geometry calculation errors

## Success Criteria

- ✅ All 6 tests passing
- ✅ Manual positions preserved 100% of the time
- ✅ Auto-placement never overlaps
- ✅ Users can confidently rearrange without losing work

## Dependencies

- `kicad_integration/kicad_to_python_sync.py`
- `kicad/schematic/placement.py`
- Position tolerance: 0.1mm

---

**Status**: 🚧 Manual setup required
**Priority**: P0 🔴 CRITICAL
**Estimated Setup Time**: 20 minutes

## Related Issues

- If this test fails, bidirectional sync is not production-ready
- Users will lose manually-arranged layouts
- Tool becomes frustrating and unusable for real work
