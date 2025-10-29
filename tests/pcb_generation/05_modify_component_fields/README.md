# Test 05: Modify All Component Fields (CANONICAL UPDATE)

## What This Tests

Modification of component fields (value, footprint, description, MPN, DNP) with validation that position is preserved.

## When This Situation Happens

- **Design iteration**: Change resistor value from 10k → 22k (tolerance refinement)
- **Footprint upgrades**: Switch from 0603 → 0805 (better availability, easier rework)
- **Adding metadata**: Add manufacturer part number for procurement
- **Production requirements**: Set DNP (Do Not Populate) for prototype-only components
- **Documentation**: Add description for design notes
- **The most common PCB workflow**: Field-only changes are constant during design

## What Should Work

1. Generate PCB with 1 resistor (R1: 10k, 0603 footprint)
2. Store R1 position
3. Modify all R1 fields in Python: value→22k, footprint→0805, add description, MPN, DNP=true
4. Regenerate PCB
5. **CRITICAL**: R1 position is UNCHANGED
6. All fields are updated correctly in PCB
7. No field corruption or data loss

## Why This Matters

This is the **CANONICAL UPDATE** pattern - the foundation of PCB design workflows.

### The Problem Without This

Without position preservation on field-only changes:
- Changing a resistor value loses all manual placement work
- Designer spends 4 hours laying out PCB
- Changes tolerance: 10k → 22k
- All placement work is lost
- Tool becomes completely unusable

### The Solution (CANONICAL UPDATE)

**Field-only changes should NOT affect position:**
```
Python code change:  value="10k" → value="22k"
PCB result:          R1 position UNCHANGED
Manual work:         NOT lost
Designer experience: ✅ Works as expected
```

This is what makes circuit-synth viable for real PCB design - the ability to make field changes without losing placement work.

## Validation Approach

**Level 2: kicad-pcb-api Structural Validation**

```python
from kicad_pcb_api import PCBBoard

# Generate initial PCB
pcb = PCBBoard.load(pcb_file)
r1 = next(fp for fp in pcb.footprints if fp.reference == "R1")
r1_pos = r1.position  # Store position

# Modify fields in Python (value, footprint, description, MPN, DNP)
# Regenerate

# Validate CANONICAL UPDATE
pcb_final = PCBBoard.load(pcb_file)
r1_final = next(fp for fp in pcb_final.footprints if fp.reference == "R1")

# CRITICAL: Position must be preserved!
assert r1_final.position == r1_pos, "Position changed on field update!"

# Verify fields updated
assert r1_final.value == "22k", "Value not updated"
assert r1_final.footprint_name == "R_0805", "Footprint not updated"
# ... validate other fields ...
```

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth3/tests/pcb_generation/05_modify_component_fields

# Generate initial PCB with R1 (10k, 0603)
uv run fixture.py

# Open in KiCad - note R1 position
open single_resistor/single_resistor.kicad_pro

# Edit fixture.py: modify R1 component definition
# Change:
#   value="10k" → value="22k"
#   footprint="Resistor_SMD:R_0603_1608Metric" → "Resistor_SMD:R_0805_2012Metric"
# Add new fields:
#   description="Thick Film Resistor"
#   mpn="R_0805_22k"
#   dnp=True

# Save fixture.py

# Regenerate PCB
uv run fixture.py

# Verify in KiCad:
# - R1 still at same position (CRITICAL!)
# - Value/footprint updated
# - New fields present
open single_resistor/single_resistor.kicad_pro
```

## Expected Result

- ✅ Initial PCB has R1 at specific position (e.g., 10.5mm, 20.3mm)
- ✅ After modifying fields, R1 position is UNCHANGED
- ✅ Value updated: 10k → 22k
- ✅ Footprint updated: 0603 → 0805
- ✅ Description added: "Thick Film Resistor"
- ✅ MPN added: "R_0805_22k"
- ✅ DNP flag set: true
- ✅ No field corruption or garbage values
- ✅ kicad-pcb-api can load final PCB without errors

## Test Output Example

```
======================================================================
STEP 1: Generate initial PCB with R1 (10k, 0603)
======================================================================
✅ Step 1: Initial PCB generated

======================================================================
STEP 2: Validate initial PCB and store R1 position
======================================================================
✅ Step 2: Initial PCB validated
   - R1 position: (15.5, 25.3)
   - R1 value: 10k
   - R1 footprint: Resistor_SMD:R_0603_1608Metric

======================================================================
STEP 3: Modify R1 fields (value, footprint, description, MPN, DNP)
======================================================================
✅ Step 3: R1 fields modified in Python code
   - Value: 10k → 22k
   - Footprint: R_0603 → R_0805
   - Added description: 'Thick Film Resistor'
   - Added MPN: 'R_0805_22k'
   - Set DNP: true

======================================================================
STEP 4: Regenerate PCB with modified R1 fields
======================================================================
✅ Step 4: PCB regenerated with modified R1 fields

======================================================================
STEP 5: Validate CANONICAL UPDATE (fields changed, position preserved)
======================================================================
✅ Validation 1: Position PRESERVED (CANONICAL UPDATE!)
   - R1 stayed at (15.5, 25.3) ✓✓✓
   - Field-only changes do NOT affect placement ✓✓✓

✅ Validation 2: Field updates
   - R1 value: 10k → 22k
   - R1 footprint: Resistor_SMD:R_0603_1608Metric → Resistor_SMD:R_0805_2012Metric

✅ Validation 3: No field corruption
   - Reference valid: R1 ✓
   - No field leakage detected ✓

✅ Validation 4: Component count unchanged
   - Still 1 component (R1) ✓

======================================================================
🎉 TEST PASSED: CANONICAL UPDATE VERIFIED!
======================================================================

Summary:
  ✅ Canonical update works (field-only changes):
     - Value updated: 10k → 22k
     - Footprint updated: 0603 → 0805
     - Description added
     - MPN added
     - DNP flag set
  ✅ Position PRESERVED:
     - R1 stayed at (15.5, 25.3)
  ✅ No field corruption detected

🏆 CANONICAL UPDATE IS THE FOUNDATION OF PCB DESIGN!
   Field changes without placement loss enables iterative design!
   This is essential for real-world PCB workflows!
```

## Key Validation Points

| Aspect | Validation | Expected |
|--------|-----------|----------|
| **Initial Position** | Store from initial PCB | (X, Y) coordinates |
| **Final Position** | Load from final PCB | SAME as initial |
| **Position Preserved** | `r1_final.position == r1_initial_pos` | True (CRITICAL!) |
| **Value Updated** | `r1_final.value` | "22k" |
| **Footprint Updated** | `r1_final.footprint_name` | "R_0805" or similar |
| **Description Added** | `r1_final.description` | "Thick Film Resistor" |
| **MPN Added** | `r1_final.mpn` | "R_0805_22k" |
| **DNP Flag Set** | `r1_final.dnp` | True |
| **No Corruption** | All fields valid | No garbage values |
| **Component Count** | `len(pcb_final.footprints)` | 1 (unchanged) |

## Test Classification

- **Category**: Component Field Management / Canonical Update
- **Priority**: CRITICAL - Foundation of PCB design workflows
- **Validation Level**: Level 2 (kicad-pcb-api structural validation)
- **Complexity**: Moderate (multiple field modifications, position preservation)
- **Execution Time**: ~5 seconds
- **Depends On**: Test 01 (basic generation), Test 02 (placement preservation)

## Why "Canonical Update"?

A **canonical update** is a field-only change that should not affect other properties:
- Change value → position preserved
- Change footprint → position preserved
- Add description → position preserved
- Add MPN → position preserved
- Set DNP → position preserved

This pattern is canonical (standard, expected, fundamental) to PCB design workflows. Every time a designer makes a field change, they expect positions to be preserved. Without this, the tool is unusable.

## Related Tests

- **Test 01**: Blank PCB Generation (foundation)
- **Test 02**: Placement Preservation (position tracking)
- **Test 03**: Add Component (adding components)
- **Test 04**: Delete Component (removing components)
- **Test 05**: Modify Component Fields (CANONICAL UPDATE) ← YOU ARE HERE
- **Test 06**: Component Rotation (rotation handling)
- **Test 07**: Round-Trip Regeneration (full workflow)

## Notes

- This test modifies multiple fields simultaneously to be thorough
- Position must be preserved exactly (bit-for-bit equality)
- Fields modified: value, footprint, description, MPN, DNP
- All modifications happen in a single regeneration cycle
- No position re-calculation should occur for field-only updates
- PCB file should be valid and loadable after update

## Debugging Tips

If test fails:

1. **Position changed?**: Check that position is NOT recalculated on field update
2. **Fields not updated?**: Verify field mapping in PCB generation
3. **Field corruption?**: Check for data type mismatches or format errors
4. **DNP not set?**: Verify DNP flag is correctly handled in PCB export
5. **MPN/Description missing?**: Check that custom fields are exported to PCB

Use `--keep-output` flag to inspect PCB files:
```bash
pytest tests/pcb_generation/05_modify_component_fields/test_05_modify_component_fields.py --keep-output
```

Then examine the generated KiCad files to verify field updates.
