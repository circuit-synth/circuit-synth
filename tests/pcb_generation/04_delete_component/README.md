# Test 04: Delete Component from PCB

## What This Tests

Removal of a component from Python code with validation that remaining components are preserved.

## When This Situation Happens

- Iterative PCB design: removing unnecessary components (test points, debug headers)
- Simplifying designs: removing prototyping components before production
- Fixing mistakes: removing components added in error
- Design evolution: component no longer needed

## What Should Work

1. Python circuit with 3 resistors generates valid KiCad PCB
2. Remove one component (R2) from Python code
3. Regenerate PCB
4. Remaining components (R1, R3) exist at their original positions
5. Deleted component (R2) is completely gone from PCB
6. No placement corruption or component loss from deletion

## Why This Matters

This validates a critical workflow for iterative PCB design:
- Designers need to remove components during development
- Without proper deletion handling, the tool breaks or loses work
- **Position preservation is crucial**: Deleting R2 should NOT move R1 or R3
- Without this, designers lose hours of manual placement work
- Deletion workflow must be as safe as addition workflow (Test 03)

## Validation Approach

**Level 2: kicad-pcb-api Structural Validation**

```python
from kicad_pcb_api import PCBBoard

# Generate PCB with R1, R2, R3
pcb = PCBBoard.load(pcb_file)
assert len(pcb.footprints) == 3

# Store positions
r1_pos = next(fp for fp in pcb.footprints if fp.reference == "R1").position
r3_pos = next(fp for fp in pcb.footprints if fp.reference == "R3").position

# Remove R2 from Python, regenerate

# Validate deletion
pcb_final = PCBBoard.load(pcb_file)
assert len(pcb_final.footprints) == 2  # Only R1 and R3 remain
r2 = next((fp for fp in pcb_final.footprints if fp.reference == "R2"), None)
assert r2 is None  # R2 is gone

# Validate preservation
r1_final = next(fp for fp in pcb_final.footprints if fp.reference == "R1")
r3_final = next(fp for fp in pcb_final.footprints if fp.reference == "R3")
assert r1_final.position == r1_pos  # Position preserved!
assert r3_final.position == r3_pos  # Position preserved!
```

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth3/tests/pcb_generation/04_delete_component

# Generate initial PCB with R1, R2, R3
uv run fixture.py

# Verify 3 components in KiCad
open three_resistors/three_resistors.kicad_pro

# Edit fixture.py: remove R2 component definition
# Save fixture.py

# Regenerate PCB
uv run fixture.py

# Verify only R1, R3 remain in KiCad
# Verify positions of R1 and R3 haven't changed
open three_resistors/three_resistors.kicad_pro
```

## Expected Result

- ✅ Initial PCB has 3 components (R1, R2, R3)
- ✅ After removing R2 from Python, PCB has 2 components (R1, R3)
- ✅ R2 is completely gone from PCB
- ✅ R1 and R3 stay at their original positions
- ✅ No ghost components or orphaned references
- ✅ kicad-pcb-api can load final PCB without errors

## Test Output Example

```
======================================================================
STEP 1: Generate initial PCB with R1, R2, R3
======================================================================
✅ Step 1: Initial PCB generated

======================================================================
STEP 2: Validate initial PCB structure (R1, R2, R3)
======================================================================
✅ Step 2: Initial PCB validated
   - R1 initial position: (10.0, 20.0)
   - R2 initial position: (30.0, 40.0)
   - R3 initial position: (50.0, 60.0)

======================================================================
STEP 3: Remove R2 from Python code
======================================================================
✅ Step 3: R2 removed from Python code

======================================================================
STEP 4: Regenerate PCB without R2
======================================================================
✅ Step 4: PCB regenerated without R2

======================================================================
STEP 5: Validate deletion and placement preservation
======================================================================
✅ Validation 1: R2 successfully deleted
   - R2 is gone from PCB ✓

✅ Validation 2: R1 position PRESERVED
   - R1 stayed at (10.0, 20.0) ✓

✅ Validation 3: R3 position PRESERVED
   - R3 stayed at (50.0, 60.0) ✓

======================================================================
✅ TEST PASSED: Component Deletion with Placement Preservation
======================================================================

Summary:
  ✅ Component deletion works:
     - R2 successfully removed from PCB
  ✅ Remaining components preserved:
     - R1 stayed at (10.0, 20.0)
     - R3 stayed at (50.0, 60.0)
  ✅ No placement corruption from deletion

🏆 Component deletion is safe and reliable!
   Iterative design with component removal is viable!
```

## Key Validation Points

| Aspect | Validation | Expected |
|--------|-----------|----------|
| **Initial Component Count** | `len(pcb.footprints)` | 3 (R1, R2, R3) |
| **Final Component Count** | `len(pcb_final.footprints)` | 2 (R1, R3 only) |
| **Deleted Component** | `r2_final is None` | True (R2 gone) |
| **R1 Position Preserved** | `r1_final.position == r1_initial_pos` | True |
| **R3 Position Preserved** | `r3_final.position == r3_initial_pos` | True |
| **PCB Valid** | `PCBBoard.load()` | Loads without error |
| **No Ghost Components** | All references in PCB | Only R1, R3 present |

## Test Classification

- **Category**: Component Lifecycle Management
- **Priority**: HIGH - Required for iterative PCB design
- **Validation Level**: Level 2 (kicad-pcb-api structural validation)
- **Complexity**: Moderate (component removal, position tracking)
- **Execution Time**: ~5 seconds
- **Depends On**: Test 01 (basic generation), Test 02 (placement preservation)

## Related Tests

- **Test 01**: Blank PCB Generation (foundation)
- **Test 02**: Placement Preservation (position tracking)
- **Test 03**: Add Component (adding components)
- **Test 04**: Delete Component (removing components) ← YOU ARE HERE
- **Test 05**: Modify Component Fields (field updates)
- **Test 06**: Component Rotation (rotation handling)
- **Test 07**: Round-Trip Regeneration (full workflow)

## Notes

- Deletion removes the component completely from PCB
- Remaining components must NOT move (position preservation critical)
- PCB file should remain valid and loadable after deletion
- No orphaned references or broken linkages
- Supports iterative design workflow where components are frequently added/removed

## Debugging Tips

If test fails:

1. **R2 not deleted?**: Check that component removal code is correct
2. **R1 or R3 moved?**: Check that auto-placement doesn't run for existing components
3. **PCB corruption?**: Validate PCB file is syntactically correct
4. **Missing components?**: Verify all footprints are properly saved

Use `--keep-output` flag to inspect PCB files:
```bash
pytest tests/pcb_generation/04_delete_component/test_04_delete_component.py --keep-output
```
