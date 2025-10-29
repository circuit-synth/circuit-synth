# Test 07: Round-Trip Regeneration

## What This Tests

Complete round-trip workflow with multiple regeneration cycles combining both manual PCB adjustments and Python code modifications.

## When This Situation Happens

This is the **REAL WORLD PCB DESIGN WORKFLOW**:

1. Design starts with schematic → generates PCB v1
2. Designer manually places components and traces in KiCad (hours of work)
3. Design review: "Add decoupling capacitors" → update Python, regenerate PCB v2
4. Manually adjust newly added components in PCB → save
5. Engineering: "Change R1 footprint for rework" → update Python, regenerate PCB v3
6. Manually adjust component positions again → save
7. Repeat for 10-20 cycles until design is complete

## What Should Work

**The complete bidirectional workflow across multiple regeneration cycles:**

1. Generate PCB v1 with R1, R2
2. Manually move R1 to (40, 50) in PCB
3. Add R3 in Python, regenerate PCB v2
4. Verify: R1 still at (40, 50) - placement PRESERVED
5. Verify: R3 auto-placed
6. Manually rotate R2 to 90° in PCB
7. Modify R1 footprint in Python (0603 → 0805), regenerate PCB v3
8. Verify: R1 at (40, 50) with new footprint
9. Verify: R2 rotation preserved at 90°
10. Verify: R3 exists and position preserved
11. No data loss through all cycles

## Why This Matters

### The Real Problem Without This

Real PCB design without round-trip support becomes impossible:

```
Scenario: Multi-cycle PCB design
Time: 0h   - Designer lays out PCB (4 hours) - saves manual work
Time: 4h   - Update Python with new component
         → Regenerate... ALL MANUAL WORK IS LOST!
         → Designer has to redo placement manually
Time: 8h   - Manually place components again (4 hours)
Time: 8h   - Update Python with field changes
         → Regenerate... ALL MANUAL WORK IS LOST AGAIN!
Time: 12h  - Manually place components AGAIN (4 hours)

Result: Tool is UNUSABLE - takes 3x longer than doing PCB manually!
```

### With Proper Round-Trip Support

```
Scenario: Multi-cycle PCB design with round-trip support
Time: 0h   - Designer lays out PCB (4 hours) - saves manual work
Time: 4h   - Update Python with new component
         → Regenerate... placement PRESERVED!
         → Only manually place new component (5 min)
Time: 4.1h - Adjust new component slightly (5 min)
Time: 4.2h - Update Python with field changes
         → Regenerate... all adjustments PRESERVED!
         → No manual re-work needed
Time: 4.3h - Done! Design ready

Result: Iterative design is VIABLE and EFFICIENT!
```

This is **THE KILLER FEATURE** that makes circuit-synth viable for real PCB design.

## The Workflow

### Round 1: Initial Generation and Manual Adjustment

```
1. Generate PCB v1 (R1, R2 auto-placed)
2. Designer manually moves R1 to (40, 50)
   - This represents hours of manual placement work
   - Save PCB with manual changes
```

### Round 2: Python Change with Placement Preservation

```
3. Add R3 in Python code
4. Regenerate PCB v2
5. Designer expects:
   - R1 STILL at (40, 50) - manual work PRESERVED ✓
   - R2 STILL at original position ✓
   - R3 auto-placed at new location ✓
6. Designer manually rotates R2 to 90° for better routing
7. Save PCB with manual changes
```

### Round 3: Footprint Change with All Manual Changes Preserved

```
8. Change R1 footprint (0603 → 0805) in Python
9. Regenerate PCB v3
10. Designer expects:
    - R1 at (40, 50) - manual position STILL PRESERVED ✓
    - R1 footprint updated to 0805 ✓
    - R2 rotation still 90° - manual rotation PRESERVED ✓
    - R3 still exists at same position ✓
```

## Validation Approach

**Level 2: kicad-pcb-api Structural Validation with State Tracking**

```python
from kicad_pcb_api import PCBBoard

# Round 1: Generate and manually adjust
pcb1 = PCBBoard.load(pcb_file)
r1 = next(fp for fp in pcb1.footprints if fp.reference == "R1")
r1.position = (40.0, 50.0)  # Manual adjustment
pcb1.save(pcb_file)

# Round 2: Add component, verify preservation, manually adjust
# (Update Python, regenerate)
pcb2 = PCBBoard.load(pcb_file)
r1_2 = next(fp for fp in pcb2.footprints if fp.reference == "R1")
assert r1_2.position == (40.0, 50.0)  # PRESERVED ✓
r2_2 = next(fp for fp in pcb2.footprints if fp.reference == "R2")
r2_2.rotation = 90.0  # Manual adjustment
pcb2.save(pcb_file)

# Round 3: Change footprint, verify all preservation
# (Update Python, regenerate)
pcb3 = PCBBoard.load(pcb_file)
r1_3 = next(fp for fp in pcb3.footprints if fp.reference == "R1")
assert r1_3.position == (40.0, 50.0)  # STILL PRESERVED ✓
assert r1_3.footprint_name == "R_0805"  # Updated ✓
r2_3 = next(fp for fp in pcb3.footprints if fp.reference == "R2")
assert r2_3.rotation == 90.0  # PRESERVED ✓
```

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth3/tests/pcb_generation/07_round_trip_regeneration

# ============ ROUND 1 ============
# Generate initial PCB
uv run fixture.py

# Open in KiCad
open round_trip_test/round_trip_test.kicad_pro

# Manually move R1 to position (40, 50)
# - Select R1
# - Drag to approximate position (40mm, 50mm)
# - Save PCB (Ctrl+S or File → Save)

# ============ ROUND 2 ============
# Edit fixture.py: Add R3 component
# In the "# ADD R3 HERE" section, add:
#   r3 = Component(
#       symbol="Device:R",
#       ref="R3",
#       value="47k",
#       footprint="Resistor_SMD:R_0603_1608Metric",
#   )

# Regenerate PCB
uv run fixture.py

# Verify in KiCad:
# - R1 is STILL at (40, 50) - manual placement preserved!
# - R3 is auto-placed
open round_trip_test/round_trip_test.kicad_pro

# Manually rotate R2 to 90°
# - Select R2
# - Press R (rotate in KiCad)
# - Save PCB

# ============ ROUND 3 ============
# Edit fixture.py: Change R1 footprint
# Change from: footprint="Resistor_SMD:R_0603_1608Metric"
# Change to:   footprint="Resistor_SMD:R_0805_2012Metric"

# Regenerate PCB
uv run fixture.py

# Verify in KiCad:
# - R1 is STILL at (40, 50) - manual placement preserved!
# - R1 is larger now (0805 instead of 0603)
# - R2 is still rotated 90°
# - R3 is still present
open round_trip_test/round_trip_test.kicad_pro
```

## Expected Result

### Round 1
- ✅ PCB v1 generated with R1, R2
- ✅ R1 manually moved to (40, 50) and saved

### Round 2
- ✅ PCB v2 regenerated with R1, R2, R3
- ✅ R1 still at (40, 50) - PLACEMENT PRESERVED
- ✅ R2 still at original position
- ✅ R3 auto-placed
- ✅ R2 manually rotated to 90° and saved

### Round 3
- ✅ PCB v3 regenerated with R1, R2, R3
- ✅ R1 still at (40, 50) - PLACEMENT PRESERVED
- ✅ R1 footprint updated to 0805
- ✅ R2 still rotated 90° - ROTATION PRESERVED
- ✅ R2 position unchanged
- ✅ R3 exists at same position - PRESERVED
- ✅ No data loss or corruption

## Test Output Example

```
======================================================================
ROUND 1: Generate PCB v1 with R1, R2
======================================================================
✅ Round 1: Generated PCB v1 (R1, R2)

======================================================================
ROUND 1: Manually adjust R1 position to (40, 50)
======================================================================
✅ Round 1: R1 manually moved to (40.0, 50.0)

======================================================================
ROUND 2: Add R3 in Python and regenerate PCB v2
======================================================================
✅ Round 2: PCB v2 regenerated with R3

======================================================================
ROUND 2: Validate R1 position preserved from manual change
======================================================================
✅ Round 2: Placement preservation verified
   - R1 PRESERVED at (40.0, 50.0) ✓
   - R2 PRESERVED at (20.0, 30.0) ✓
   - R3 auto-placed at (60.0, 70.0) ✓

======================================================================
ROUND 2: Manually rotate R2 to 90°
======================================================================
✅ Round 2: R2 manually rotated to 90°

======================================================================
ROUND 3: Modify R1 footprint and regenerate PCB v3
======================================================================
✅ Round 3: PCB v3 regenerated with R1 footprint update

======================================================================
ROUND 3: Validate complete round-trip workflow
======================================================================
✅ Validation 1: R1 position preserved through all 3 rounds
   - R1 at (40.0, 50.0) (set in Round 1, preserved in Rounds 2-3) ✓

✅ Validation 2: R2 rotation preserved through regeneration
   - R2 rotation at 90.0° (set in Round 2, preserved in Round 3) ✓

✅ Validation 3: R2 position unchanged
   - R2 at (20.0, 30.0) (same as v2) ✓

✅ Validation 4: R3 exists and position preserved
   - R3 at (60.0, 70.0) (same as v2) ✓

✅ Validation 5: R1 footprint updated
   - R1 footprint: Resistor_SMD:R_0805_2012Metric (updated to R_0805) ✓

======================================================================
🎉 TEST PASSED: COMPLETE ROUND-TRIP WORKFLOW VERIFIED!
======================================================================

Round-Trip Summary:

  Round 1: Generate v1 (R1, R2)
    - Generated PCB with auto-placement
    - Manually adjusted R1 to (40, 50)

  Round 2: Add R3 and regenerate v2
    - R1 position PRESERVED at (40, 50) ✓
    - R3 added and auto-placed ✓
    - Manually rotated R2 to 90° ✓

  Round 3: Modify R1 footprint and regenerate v3
    - R1 position still at (40, 50) ✓✓✓
    - R1 footprint updated ✓
    - R2 rotation preserved at 90° ✓
    - R3 position preserved ✓

  ✅ All manual changes preserved through all cycles
  ✅ All Python changes applied correctly
  ✅ No data loss or corruption

🏆 COMPLETE ROUND-TRIP WORKFLOW WORKS!
   Real iterative PCB design with mixed manual/programmatic changes!
   Multiple regeneration cycles without data loss!
   THIS IS THE KILLER FEATURE FOR COMPLEX PCB WORKFLOWS!
```

## Key Validation Points

| Aspect | Round 1 | Round 2 | Round 3 |
|--------|---------|---------|---------|
| **R1 Position** | Initial | (40, 50) | (40, 50) PRESERVED ✓ |
| **R1 Footprint** | 0603 | 0603 | 0805 Updated ✓ |
| **R2 Position** | Initial | Initial | Initial PRESERVED ✓ |
| **R2 Rotation** | 0° | 90° Manual | 90° PRESERVED ✓ |
| **R3 Status** | — | Added | Exists PRESERVED ✓ |
| **Manual Changes** | Preserved | Preserved | Preserved ✓ |
| **Python Changes** | — | Applied (R3) | Applied (Footprint) ✓ |

## Test Classification

- **Category**: Complete Workflow / Round-Trip Regeneration
- **Priority**: CRITICAL - Foundation of real PCB design workflows
- **Validation Level**: Level 2 (kicad-pcb-api structural validation with state tracking)
- **Complexity**: High (3 regeneration cycles, multiple validations, mixed changes)
- **Execution Time**: ~15 seconds
- **Depends On**: Tests 01-06 (all previous PCB tests should pass first)

## Why This Test is Critical

This is the **definitive test** for whether circuit-synth can handle real PCB workflows:

1. **Real designers don't work in a single cycle** - they iterate 10-20+ times
2. **Designers mix manual and programmatic changes** - not pure Python or pure KiCad
3. **Each cycle must preserve previous work** - otherwise the tool adds burden instead of helping
4. **Data integrity is critical** - losing work is career-ending for designers
5. **This test proves the tool works for real workflows** - not just toy examples

Without this test passing, circuit-synth is not viable for real PCB design. With it, the tool becomes genuinely useful.

## Related Tests

- **Test 01**: Blank PCB Generation (foundation)
- **Test 02**: Placement Preservation (position tracking)
- **Test 03**: Add Component (adding components)
- **Test 04**: Delete Component (removing components)
- **Test 05**: Modify Component Fields (field updates)
- **Test 06**: Component Rotation (rotation handling)
- **Test 07**: Round-Trip Regeneration (COMPLETE WORKFLOW) ← YOU ARE HERE

## Notes

- This test is the most comprehensive PCB test
- It validates all features working together
- Multiple regeneration cycles with mixed changes
- Complete state tracking through all cycles
- Real-world workflow representation
- This is the "system integration test" for PCB workflows

## Debugging Tips

If test fails:

1. **Manual changes lost?**: Check preservation logic at each regeneration
2. **Python changes not applied?**: Verify code modification and regeneration
3. **Data corruption?**: Inspect PCB files at each round
4. **Position/rotation errors?**: Trace through each cycle's state
5. **Component missing?**: Check addition/deletion logic

Use `--keep-output` flag to inspect all 3 generations:
```bash
pytest tests/pcb_generation/07_round_trip_regeneration/test_07_round_trip_regeneration.py --keep-output
```

Then examine `round_trip_test/` directory to see v1, v2, v3 states (you'll need to check the files manually or regenerate with timestamps).

## The Ultimate Test

This test represents the complete PCB design workflow:
- Multiple cycles with mixed manual and programmatic changes
- No data loss between cycles
- All features working together
- Real-world representative workflow
- If this passes, circuit-synth is ready for real PCB design

**If Test 07 passes, the PCB bidirectional workflow is proven viable.**
