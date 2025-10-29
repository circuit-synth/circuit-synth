# Test 16: Fiducial Markers

## What This Tests

Fiducial markers for automated pick-and-place (PnP) assembly.

Fiducials are critical registration marks that:
- Allow **pick-and-place machines to calibrate** board position and orientation
- **Prevent assembly errors** (wrong position, wrong rotation, wrong board)
- Enable **high-volume automated assembly** (batch processing)
- Provide **cost savings** through eliminating manual positioning
- Are **industry standard** for modern manufacturing

## When This Situation Happens

- Preparing boards for high-volume manufacturing
- Setting up for automated pick-and-place assembly
- Designing multi-layer boards requiring precise component placement
- Optimizing manufacturing costs for production runs
- Ensuring assembly machine compatibility

## What Should Work

1. Python circuit generates PCB with component placement
2. Fiducial markers can be added at standard positions (3 minimum: corners + center)
3. Fiducials are 1.5mm round copper pads on F.Cu (top copper) layer
4. Fiducials positioned at corners and board center for optimal registration
5. No copper on silkscreen for fiducials (copper only, assembly requirement)
6. Fiducial positions validate within manufacturing tolerance (±1mm)
7. Fiducials survive PCB regeneration
8. Additional fiducials can be added (4th fiducial, more if needed)

## Why This Matters

**Manufacturing Critical:**
- Pick-and-place machines **require fiducials** to calibrate
- Without fiducials, machine can't accurately position components
- Assembly errors = defective boards = scrapped batch
- One fiducial design error = thousands of defective boards

**Cost Impact:**
- **Automated assembly** (with fiducials): $0.10/board
- **Manual placement** (without fiducials): $5+/board
- For 1,000 unit batch: **$4,900 difference**
- For 10,000 unit batch: **$49,000 difference**

**Industry Standard:**
- All commercial PCB manufacturers expect fiducials
- IPC-A-600 standard specifies fiducial positioning
- Missing fiducials = machines can't operate correctly
- Production hold-up until fiducials added (board rework)

## Validation Approach

**Level 2: kicad-pcb-api Structural Validation + File Parsing**

```python
from kicad_pcb_api import PCBBoard

pcb = PCBBoard.load(str(pcb_file))
assert pcb is not None  # PCB loads without errors

# Extract fiducial pads
fiducials = extract_fiducial_pads(pcb_file)
assert len(fiducials) >= 3  # Minimum 3 fiducials

# Validate each fiducial
for fid in fiducials:
    assert fid["size_x"] == 1.5  # Standard size
    assert fid["layer"] == "F.Cu"  # Copper only
    assert fid["type"] == "smd"  # SMD pads

# Validate positions (3-point registration)
assert (5, 5) in positions  # Top-left
assert (195, 5) in positions  # Top-right
assert (100, 145) in positions  # Bottom-center
```

## Test Flow

### Phase 1: Initial PCB with 3 Fiducials (Steps 1-7)
1. Generate PCB with 3 components (R1, R2, C1)
2. Add 3 fiducials at standard positions:
   - FID1 at (5, 5) - top-left corner
   - FID2 at (195, 5) - top-right corner
   - FID3 at (100, 145) - bottom center
3. Validate PCB loads successfully
4. Extract fiducial pad information
5. Verify 3 fiducials present with correct positions
6. Verify fiducial size 1.5mm (±0.1mm tolerance)
7. Verify fiducials on F.Cu layer (copper), NOT silkscreen
8. Verify no other pads have wrong layer assignments

### Phase 2: Addition & Regeneration (Steps 8-10)
9. Modify Python code (comment change)
10. Regenerate PCB
11. Add 4th fiducial at (50, 75) - center-left
12. Verify all 4 fiducials present
13. Validate all 4 fiducials with correct properties
14. Confirm fiducials preserved across regeneration

## Fiducial Best Practices

**IPC-A-600 Standard (Industry Specification):**
- **Minimum**: 3 fiducials for single-sided, 3+ for double-sided
- **Position**: At board corners and center for triangulation
- **Size**: 1.5mm ± 0.1mm diameter (standard)
- **Copper**: Bare copper (not solder masked)
- **Contrast**: Dark copper on light board (for optical detection)
- **Spacing**: At least 20mm from any component or board edge

**Standard 4-Fiducial Pattern (Industry Preferred):**
- FID1: Top-left corner
- FID2: Top-right corner
- FID3: Bottom-left corner
- FID4: Bottom-right corner
(Or 3-fiducial for cost-sensitive designs)

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth3/tests/pcb_generation/16_fiducial_markers

# Generate PCB with fiducial markers
uv run fixture.py

# Check files created
ls -la fiducial_markers/

# Open in KiCad - should see round copper pads (fiducials) at corners
open fiducial_markers/fiducial_markers.kicad_pro

# Expected in KiCad:
# - 1.5mm round copper pads at (5,5), (195,5), (100,145)
# - Labeled FID1, FID2, FID3
# - On F.Cu (top copper) layer
# - No silkscreen
# - Visible as bare copper (no solder mask)
```

## Expected Result

- ✅ KiCad project generated (.kicad_pro)
- ✅ PCB file generated (.kicad_pcb)
- ✅ PCB opens successfully in KiCad
- ✅ 3 fiducial pads visible (round copper circles)
- ✅ Fiducials at correct positions (5,5), (195,5), (100,145)
- ✅ Fiducial size 1.5mm (±0.1mm tolerance)
- ✅ Fiducials on F.Cu layer (copper)
- ✅ No fiducials on silkscreen (copper only)
- ✅ Components placed (R1, R2, C1)
- ✅ Fiducials preserved after PCB regeneration
- ✅ 4th fiducial successfully added
- ✅ All 4 fiducials with correct properties
- ✅ kicad-pcb-api can load PCB without errors

## Test Output Example

```
======================================================================
STEP 1: Generate PCB with components
======================================================================
✅ Step 1: PCB generated successfully
   - Project file: fiducial_markers.kicad_pro
   - PCB file: fiducial_markers.kicad_pcb

======================================================================
STEP 2: Add 3 fiducials to PCB (standard positions)
======================================================================
✅ Step 2: 3 fiducials added to PCB file
   - FID1 at (5, 5) - top-left
   - FID2 at (195, 5) - top-right
   - FID3 at (100, 145) - bottom-center

======================================================================
STEP 3: Validate PCB structure with kicad-pcb-api
======================================================================
✅ Step 3: PCB structure validated
   - Footprints: 3 (expected: 3) ✓
   - Component references: ['R1', 'R2', 'C1']

======================================================================
STEP 4: Validate fiducials in PCB
======================================================================
✅ Step 4: Fiducials found and validated
   - Total fiducials: 3 (expected: 3) ✓
   - FID1 at (5.0, 5.0), size 1.50mm, type=smd
   - FID2 at (195.0, 5.0), size 1.50mm, type=smd
   - FID3 at (100.0, 145.0), size 1.50mm, type=smd

======================================================================
STEP 5: Validate fiducial positions
======================================================================
✅ Step 5: Fiducial positions validated
   - FID1 at (5, 5) ✓
   - FID2 at (195, 5) ✓
   - FID3 at (100, 145) ✓

======================================================================
STEP 6: Validate fiducial pad properties
======================================================================
✅ Step 6: Fiducial properties validated
   - All fiducials are 1.5mm SMD circles ✓
   - All on F.Cu layer ✓
   - Size within spec (1.5mm ± 0.1mm) ✓

======================================================================
STEP 7: Verify fiducials NOT on silkscreen (assembly requirement)
======================================================================
✅ Step 7: Fiducials properly on F.Cu, not silkscreen ✓

======================================================================
STEP 8: Modify Python code
======================================================================
✅ Step 8: Python code modified (comment added)

======================================================================
STEP 9: Regenerate PCB after code modification
======================================================================
✅ Step 9: PCB regenerated successfully after code modification

======================================================================
STEP 10: Add 4th fiducial and validate all fiducials preserved
======================================================================
✅ Step 10: All 4 fiducials present and validated
   - FID1 at (5.0, 5.0) ✓
   - FID2 at (195.0, 5.0) ✓
   - FID3 at (100.0, 145.0) ✓
   - FID4 at (50.0, 75.0) ✓

======================================================================
✅ TEST PASSED: Fiducial Markers
======================================================================
Summary:
  - 3 initial fiducials added ✓
  - Fiducial positions accurate (±1mm) ✓
  - Fiducial size correct (1.5mm) ✓
  - All fiducials on F.Cu layer ✓
  - No fiducials on silkscreen ✓
  - Fiducials preserved after regeneration ✓
  - 4th fiducial successfully added ✓
  - All 4 fiducials with correct properties ✓
```

## Key Validation Points

| Aspect | Validation | Expected |
|--------|-----------|----------|
| **Fiducial Count** | Count FID pads | Min 3, standard 3-4 |
| **Fiducial Positions** | Check (x,y) coordinates | (5,5), (195,5), (100,145) |
| **Fiducial Size** | Measure diameter | 1.5mm ± 0.1mm |
| **Fiducial Type** | Check SMD vs TH | SMD (surface mount) |
| **Fiducial Shape** | Check geometry | Circle |
| **Copper Layer** | Check layer assignment | F.Cu (top copper) |
| **No Silkscreen** | Verify NOT on silkscreen | Copper only |
| **Tolerance** | Position accuracy | ±1mm (assembly requirement) |
| **Preservation** | After regeneration | Preserved |

## Manufacturing Integration

**PCB Manufacturer Workflow:**
1. Design received with fiducials
2. Image fiducials with camera
3. Calculate board position and rotation
4. Align PCB precisely on assembly machine table
5. Pick and place components using fiducial calibration
6. All components placed within 0.1mm accuracy

**Without Fiducials:**
1. Board placed manually (±3mm tolerance)
2. First few components manually aligned
3. Assembly takes 10x longer
4. Error rate higher (wrong components, orientation)
5. Not viable for high-volume production

## Assembly Cost Example (1,000 units)

| Method | Cost/Unit | Setup | Total |
|--------|-----------|-------|-------|
| **Automated + Fiducials** | $0.10 | $200 | $300 |
| **Manual (no fiducials)** | $5.00 | $0 | $5,000 |
| **Savings per 1,000 units** | - | - | **$4,700** |

## Related Tests

- **Test 15**: Silkscreen features (documentation)
- **Test 17**: Gerber export (fiducials exported in Gerbers)
- **Test 18**: Pick-and-place export (assembly machines use fiducials)

## Test Classification

- **Category**: Board Features (Assembly & Manufacturing)
- **Priority**: CRITICAL - Essential for high-volume manufacturing
- **Validation Level**: Level 2 (kicad-pcb-api + file parsing)
- **Complexity**: Medium (pad detection + position validation)
- **Execution Time**: ~4 seconds
- **Manufacturing Impact**: CRITICAL - Cannot manufacture without fiducials

## Notes

- Standard fiducial size: 1.5mm ± 0.1mm
- Minimum fiducials: 3 (corners + center)
- Preferred fiducials: 4 (all corners) - better for large boards
- Fiducials must be bare copper (no solder mask)
- Optical detection works best on high-contrast (dark copper on light board)
- Fiducial positioning must be within manufacturing tolerance
- IPC-A-600 standard covers detailed fiducial specifications
