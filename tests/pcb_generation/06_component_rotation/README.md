# Test 06: Component Rotation

## What This Tests

Modification of component rotation angle with validation that position is preserved.

## When This Situation Happens

- **Layout optimization**: Rotating components for better routing density
- **Trace routing**: Rotating resistors/capacitors to ease wire paths
- **Aesthetic improvements**: Aligning components for cleaner appearance
- **Design evolution**: Changing rotation after initial placement
- **Footprint variations**: Some footprints work better at different angles

## What Should Work

1. Generate PCB with 2 resistors (R1, R2) with default 0° rotation
2. Store R1 and R2 initial rotations and positions
3. Modify R1 rotation to 90° in Python code
4. Regenerate PCB
5. **CRITICAL**: R1 position is UNCHANGED (only angle changes)
6. R1 rotation is updated to 90°
7. R2 rotation and position remain unchanged
8. No placement corruption

## Why This Matters

Rotation is a **canonical update** - similar to value/footprint changes:
- Change rotation → position should NOT change
- Rotation is a property of the component's angle, not its location
- Manual placement work must be preserved through rotation changes
- Rotation is one of the most common PCB layout adjustments

### Design Workflow Impact

Without rotation preservation:
- Designer places all 100 components (4 hours of work)
- Realizes one component needs rotation for better routing
- Rotation causes re-placement, all work is lost
- Tool is unusable

With rotation preservation:
- Designer can adjust rotation without affecting placement
- Layout work is preserved
- Tool is viable for real design workflows

## Validation Approach

**Level 2: kicad-pcb-api Structural Validation**

```python
from kicad_pcb_api import PCBBoard

# Generate initial PCB
pcb = PCBBoard.load(pcb_file)
r1 = next(fp for fp in pcb.footprints if fp.reference == "R1")
r1_pos = r1.position
r1_rot = r1.rotation  # 0°

# Modify R1 rotation to 90° in Python, regenerate

# Validate rotation change
pcb_final = PCBBoard.load(pcb_file)
r1_final = next(fp for fp in pcb_final.footprints if fp.reference == "R1")

# CRITICAL: Position must be preserved!
assert r1_final.position == r1_pos, "Position changed on rotation!"

# Verify rotation updated
assert r1_final.rotation != 0.0, "Rotation not applied"

# Verify other components unaffected
r2_final = next(fp for fp in pcb_final.footprints if fp.reference == "R2")
assert r2_final.rotation == 0.0, "R2 rotation should not change"
```

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth3/tests/pcb_generation/06_component_rotation

# Generate initial PCB with R1 (0°), R2 (0°)
uv run fixture.py

# Open in KiCad - note R1 position and rotation
open rotation_test/rotation_test.kicad_pro

# Edit fixture.py: add rotation to R1
# Change R1 component definition:
#   Add: rotation=90.0
# (R2 stays unchanged)

# Save fixture.py

# Regenerate PCB
uv run fixture.py

# Verify in KiCad:
# - R1 is rotated 90° (visually rotated)
# - R1 position is SAME as before (CRITICAL!)
# - R2 position and rotation unchanged
open rotation_test/rotation_test.kicad_pro
```

## Expected Result

- ✅ Initial PCB has R1 at 0° rotation, specific position
- ✅ Initial PCB has R2 at 0° rotation, specific position
- ✅ After modifying R1 rotation to 90°:
  - R1 is rotated 90° in PCB
  - R1 position UNCHANGED (same location)
  - R2 position UNCHANGED
  - R2 rotation UNCHANGED
- ✅ No component corruption or displacement
- ✅ kicad-pcb-api can load final PCB without errors

## Test Output Example

```
======================================================================
STEP 1: Generate initial PCB with R1, R2 (default 0° rotation)
======================================================================
✅ Step 1: Initial PCB generated

======================================================================
STEP 2: Validate initial state and store R1, R2 properties
======================================================================
✅ Step 2: Initial state validated
   - R1 position: (20.0, 30.0), rotation: 0.0°
   - R2 position: (40.0, 50.0), rotation: 0.0°

======================================================================
STEP 3: Modify R1 rotation to 90°
======================================================================
✅ Step 3: R1 rotation modified to 90°

======================================================================
STEP 4: Regenerate PCB with R1 rotation changed to 90°
======================================================================
✅ Step 4: PCB regenerated with R1 rotation

======================================================================
STEP 5: Validate rotation update and position preservation
======================================================================
✅ Validation 1: R1 position PRESERVED
   - R1 stayed at (20.0, 30.0) ✓
   - Rotation-only changes do NOT affect placement ✓

✅ Validation 2: R1 rotation updated
   - R1 rotation changed from 0.0° to 90.0° ✓

✅ Validation 3: R2 unchanged
   - R2 position: (40.0, 50.0) (unchanged) ✓
   - R2 rotation: 0.0° (unchanged) ✓

======================================================================
✅ TEST PASSED: Component Rotation with Position Preservation
======================================================================

Summary:
  ✅ Rotation modification works:
     - R1 rotated from 0.0° to 90.0°
  ✅ Position PRESERVED:
     - R1 stayed at (20.0, 30.0)
  ✅ Other components unaffected:
     - R2 position and rotation unchanged

🏆 Component rotation works without affecting placement!
   Rotation-aware placement density improvements are viable!
```

## Key Validation Points

| Aspect | Validation | Expected |
|--------|-----------|----------|
| **Initial Rotation** | R1 and R2 at 0° | Both at 0.0° |
| **Modified Rotation** | R1 updated to 90° | 90.0° or equivalent |
| **R1 Position Preserved** | `r1_final.position == r1_initial_pos` | True (CRITICAL!) |
| **R1 Rotation Changed** | `r1_final.rotation != r1_initial_rotation` | True |
| **R2 Position Unchanged** | `r2_final.position == r2_initial_pos` | True |
| **R2 Rotation Unchanged** | `r2_final.rotation == r2_initial_rotation` | True |
| **Component Count** | `len(pcb_final.footprints)` | 2 (unchanged) |
| **PCB Valid** | `PCBBoard.load()` | Loads without error |

## Test Classification

- **Category**: Component Attribute Management
- **Priority**: HIGH - Common layout adjustment
- **Validation Level**: Level 2 (kicad-pcb-api structural validation)
- **Complexity**: Moderate (rotation modification, position tracking)
- **Execution Time**: ~5 seconds
- **Depends On**: Test 01 (basic generation), Test 02 (placement preservation)

## Why Rotation Matters for PCB Design

### Placement Density

Components at different rotations can sometimes fit together more efficiently:
- Resistor at 0° occupies width=1.6mm, height=0.8mm
- Same resistor at 90° occupies width=0.8mm, height=1.6mm
- Strategic rotation can reduce overall board footprint

### Trace Routing

Rotated components can ease trace routing:
- Some routes are impossible with original orientation
- Rotating 90° might allow cleaner traces
- Critical for high-density boards

### Visual Aesthetics

PCB aesthetics matter for professional appearance:
- Aligning components in rows often requires different rotations
- Consistent rotation improves visual organization

## Related Tests

- **Test 01**: Blank PCB Generation (foundation)
- **Test 02**: Placement Preservation (position tracking)
- **Test 03**: Add Component (adding components)
- **Test 04**: Delete Component (removing components)
- **Test 05**: Modify Component Fields (field updates)
- **Test 06**: Component Rotation (rotation handling) ← YOU ARE HERE
- **Test 07**: Round-Trip Regeneration (full workflow)

## Notes

- Rotation can be expressed in different ways (0°, 90°, 180°, 270° or normalized variations)
- KiCad may normalize rotations (e.g., 270° = -90°)
- Test accepts both actual and normalized rotations
- Position preservation is the critical requirement
- Rotation should not affect component location, only its angle

## Debugging Tips

If test fails:

1. **Position changed?**: Check that position is NOT recalculated on rotation update
2. **Rotation not applied?**: Verify rotation attribute is correctly mapped to PCB
3. **Other components affected?**: Check that modification is isolated to target component
4. **Rotation format issue?**: KiCad uses different rotation representations

Use `--keep-output` flag to inspect PCB files:
```bash
pytest tests/pcb_generation/06_component_rotation/test_06_component_rotation.py --keep-output
```

Then open the generated KiCad files to visually verify rotations and positions.
