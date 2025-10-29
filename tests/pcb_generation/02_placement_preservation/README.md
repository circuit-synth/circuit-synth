# Test 02: Placement Preservation - THE KILLER FEATURE FOR PCB

## What This Tests

**Manual component placement survives Python changes to the circuit.**

This is THE most critical feature for PCB design workflows. Without it, the tool is unusable.

## When This Situation Happens

- Making iterative changes to circuit (adding/removing components)
- Optimizing footprints (0805 → 0603)
- Adding decoupling caps or test points
- Fixing bugs in the schematic
- Any scenario where you need to regenerate PCB while preserving manual layout work

## What Should Work

1. Generate initial PCB with R1, R2
2. Manually move R1 to specific position (50mm, 30mm) in KiCad
3. Add R3 in Python code
4. Regenerate PCB
5. **CRITICAL: R1 stays at (50mm, 30mm) - manual placement PRESERVED!**
6. R2 stays in original position
7. R3 is auto-placed without collisions

## Why This Matters

**Component placement is the most time-consuming part of PCB design.**

Real-world workflow:
- Generate initial PCB with auto-placement (30 minutes)
- Manually optimize component placement in KiCad (2-4 hours!)
- Route traces in KiCad (4-8 hours)
- Realize need to add 4 decoupling caps
- **Modify circuit Python, regenerate PCB**
- **Without placement preservation**: All 2-4 hours of placement work is LOST!
- **With placement preservation**: Add caps, optimize placement for new caps, continue

**THIS TEST PROVES PRESERVATION WORKS** - making circuit-synth viable for real PCB design.

## Validation Approach

**Level 2: kicad-pcb-api Structural Validation**

```python
from kicad_pcb_api import PCBBoard

# Step 1: Generate initial PCB
pcb = PCBBoard.load(str(pcb_file))
assert len(pcb.footprints) == 2  # R1, R2

# Step 2: Manually move R1
r1 = next(fp for fp in pcb.footprints if fp.reference == "R1")
r1.position = (50.0, 30.0)
pcb.save(str(pcb_file))

# Step 3: Add R3 in Python and regenerate

# Step 4: Load regenerated PCB and validate preservation
pcb_final = PCBBoard.load(str(pcb_file))

# CRITICAL VALIDATION
r1_final = next(fp for fp in pcb_final.footprints if fp.reference == "R1")
r2_final = next(fp for fp in pcb_final.footprints if fp.reference == "R2")
r3_final = next(fp for fp in pcb_final.footprints if fp.reference == "R3")

# THE KILLER FEATURE
assert r1_final.position == (50.0, 30.0)  # PLACEMENT PRESERVED!
assert r2_final.position == r2_initial_pos  # PLACEMENT PRESERVED!
assert r3_final.position != (0.0, 0.0)  # Smart auto-placement
```

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth3/tests/pcb_generation/02_placement_preservation

# Step 1: Generate initial PCB
uv run fixture.py

# Step 2: Open in KiCad and manually move R1
open two_resistors/two_resistors.kicad_pro

# In KiCad:
# - Select R1 component
# - Move to position (50mm, 30mm)
# - Save PCB (Ctrl+S)

# Step 3: Modify fixture.py - uncomment R3 section

# Step 4: Regenerate from Python
uv run fixture.py

# Step 5: Open in KiCad again
open two_resistors/two_resistors.kicad_pro

# Verify: R1 should still be at (50, 30) - placement preserved!
```

## Expected Result

- ✅ Initial PCB generated with R1, R2
- ✅ R1 can be manually moved to (50, 30)
- ✅ R3 added in Python code
- ✅ PCB regenerated successfully
- ✅ **R1 STILL AT (50, 30) - PLACEMENT PRESERVED** ✓✓✓
- ✅ **R2 STILL AT ORIGINAL POSITION - PLACEMENT PRESERVED** ✓✓✓
- ✅ R3 auto-placed without collisions
- ✅ No components at origin (0, 0)
- ✅ All components within reasonable board boundaries

## Test Output Example

```
======================================================================
STEP 1: Generate initial PCB with R1, R2
======================================================================
✅ Step 1: Initial PCB generated

======================================================================
STEP 2: Validate initial PCB structure
======================================================================
✅ Step 2: Initial PCB validated
   - R1 initial position: (25.4, 15.2)
   - R2 initial position: (35.6, 25.4)

======================================================================
STEP 3: Manually move R1 to (50, 30)
======================================================================
✅ Step 3: R1 manually moved
   - R1 now at: (50.0, 30.0)

======================================================================
STEP 4: Add R3 to Python code
======================================================================
✅ Step 4: R3 added to Python code

======================================================================
STEP 5: Regenerate PCB with R3
======================================================================
✅ Step 5: PCB regenerated with R3

======================================================================
STEP 6: VALIDATE PLACEMENT PRESERVATION
======================================================================
✅ Step 6: PLACEMENT PRESERVATION VERIFIED!
   - R1 PRESERVED at (50.0, 30.0) ✓✓✓
   - R2 PRESERVED at (35.6, 25.4) ✓✓✓
   - R3 auto-placed at (65.2, 40.6) ✓

======================================================================
STEP 7: Validate R3 auto-placement
======================================================================
✅ Step 7: R3 auto-placement validated
   - No collisions with existing components ✓
   - R3 positioned at reasonable location ✓

======================================================================
🎉 TEST PASSED: PLACEMENT PRESERVATION VERIFIED!
======================================================================

Summary:
  ✅ Manual placement preserved:
     - R1 stayed at (50.0, 30.0)
     - R2 stayed at (35.6, 25.4)
  ✅ New component auto-placed:
     - R3 placed at (65.2, 40.6)
  ✅ No collisions detected

🏆 THE KILLER FEATURE WORKS FOR PCB!
   Manual PCB layout work is NOT lost when regenerating!
   Tool is viable for real PCB development workflows!
```

## Key Validation Points

| Aspect | Validation | Expected |
|--------|-----------|----------|
| **Initial PCB** | Generate with R1, R2 | 2 components |
| **Manual Move** | Move R1 to (50, 30) | Position saved in file |
| **Add Component** | Add R3 in Python | Python code modified |
| **Regenerate** | Run fixture.py | New PCB file created |
| **R1 Preserved** | `r1.position == (50.0, 30.0)` | **EXACT MATCH** ✓✓✓ |
| **R2 Preserved** | `r2.position == r2_initial` | **EXACT MATCH** ✓✓✓ |
| **R3 Exists** | `r3 is not None` | True |
| **R3 Not at Origin** | `r3.position != (0, 0)` | True |
| **No Collisions** | Distance between all pairs ≥ 5mm | True |

## Test Classification

- **Category**: Core Placement Test
- **Priority**: CRITICAL - THE KILLER FEATURE
- **Validation Level**: Level 2 (kicad-pcb-api structural validation)
- **Complexity**: Medium (involves Python modification + multi-step workflow)
- **Execution Time**: ~5 seconds

## Comparison to Schematic Tests

This test mirrors **schematic test 09 (position_preservation)** but for PCB:

| Aspect | Schematic Test 09 | PCB Test 02 |
|--------|-------------------|-----------|
| **File Type** | .kicad_sch | .kicad_pcb |
| **Components** | Symbols | Footprints |
| **Position Type** | Symbol position | Footprint position |
| **Validation** | kicad-sch-api | kicad-pcb-api |
| **Killer Feature** | Position preserved | Placement preserved |
| **Real Impact** | Circuit layout preserved | Manual PCB layout preserved |

Both test the same core principle: **manual work survives Python changes**.

## Notes

- Position preservation is the *foundation* for iterative PCB development
- Without this, tool cannot be used for real designs
- With this working, users can:
  - Place components optimally in KiCad
  - Make changes to circuit in Python
  - Regenerate with placement preserved
  - Only need to re-route affected traces (expected)
- This test validates the complete workflow is viable

## Related Tests

- **Test 01**: Blank PCB (foundation)
- **Test 03**: Add component with collision avoidance
- **Test 04**: Delete component preservation
- **Test 05**: Modify component fields (with placement preservation)
- **Test 06**: Component rotation (with placement preservation)
- **Test 07**: Round-trip regeneration (full workflow)

All these tests depend on the core principle proven by Test 02.
