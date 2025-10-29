# Test 17: Gerber & Drill Export

## What This Tests

Gerber and drill file export for PCB manufacturing.

Gerber files are the **industry standard** for communicating PCB designs to manufacturers:
- RS-274X format (vector graphics for manufacturing)
- One file per layer (copper, silkscreen, solder mask, etc.)
- Submitted directly to manufacturers (JLCPCB, PCBWay, Oshpark, etc.)
- Unambiguous specifications for fabrication

Drill files specify where to drill holes:
- Excellon format (standard)
- XY positions with tool sizes
- Guides drilling machine on hole locations and sizes

## When This Situation Happens

- Preparing board for fabrication at external manufacturer
- Submitting design to JLCPCB, PCBWay, Oshpark, or other service
- Archiving design for compliance or documentation
- Sharing design with PCB shop
- Preparing for production manufacturing

## What Should Work

1. Python circuit generates PCB with components and board outline
2. Gerber files exported for all layers (F.Cu, B.Cu, F.Silkscreen, etc.)
3. Drill file exported with mounting hole positions and sizes
4. All exported files are valid RS-274X (Gerbers) and Excellon (drill) format
5. All copper layers present (front + back for 2-layer board)
6. Board outline (Edge.Cuts) included for manufacturing
7. Silkscreen layer included for assembly documentation
8. All components appear in Gerber exports
9. All holes appear in drill file
10. Files can be submitted directly to manufacturers

## Why This Matters

**Manufacturing Critical:**
- Manufacturers **ONLY accept Gerber format** (RS-274X)
- Without proper Gerber export, boards cannot be manufactured
- Incorrect Gerber format = boards built incorrectly or rejected
- Drill file must be accurate or holes drilled in wrong locations

**Cost & Time:**
- Correct Gerber export = board built as designed, on first try
- Incorrect export = board rejected by manufacturer, schedule delay
- Manual Gerber generation = hours of work, error-prone
- Automated export = 30 seconds, no errors

**Quality:**
- RS-274X is unambiguous (exactly what to manufacture)
- Excellon drill format is industry standard (all machines understand it)
- Other formats may be interpreted differently by different manufacturers
- Standardized export = consistent results

## Validation Approach

**Level 2: File Format Validation + Structure Checking**

```python
# Validate Gerber files exist and are RS-274X format
gerber_files = [f for f in gerber_dir.glob("*.gbr")]
assert len(gerber_files) > 0  # At least one Gerber

for gerber_file in gerber_files:
    content = open(gerber_file).read()
    assert "%FS" in content  # RS-274X format declaration
    assert "%ADD" in content  # Aperture definitions
    assert "M02*" in content  # End of file marker

# Validate drill file exists and is Excellon format
drill_file = gerber_dir / "*.drl"
assert drill_file.exists()

content = open(drill_file).read()
assert "M48" in content  # Header
assert "M30" in content  # End marker
assert any("X" in line and "Y" in line for line in content)  # Coordinates
```

## Test Flow

### Phase 1: PCB Generation (Steps 1-2)
1. Generate PCB with 3 components (R1, R2, C1)
2. Validate PCB structure with kicad-pcb-api

### Phase 2: Gerber Export (Steps 3-5)
3. Export Gerber files using kicad-cli
4. Export drill files using kicad-cli
5. Validate exported files exist in gerber directory

### Phase 3: Format Validation (Steps 6-8)
6. Validate Gerber files are RS-274X format:
   - Check for %FS (format statement)
   - Check for %ADD (aperture definitions)
   - Check for M02* (end of file)
7. Validate drill file is Excellon format:
   - Check for M48 (start of file)
   - Check for M30 (end of file)
   - Check for coordinate data (X/Y)
8. Validate layer coverage:
   - Front copper (F.Cu)
   - Back copper (B.Cu)
   - Front silkscreen
   - Board outline (Edge.Cuts)

### Phase 4: Manufacturing Readiness (Step 9)
9. Verify manufacturing ready:
   - All copper layers present
   - Board outline present
   - Drill file present

## Gerber File Format (RS-274X)

RS-274X is the standard format for PCB manufacturing:

```
%FSLAX23Y23*%         # Format statement
%MOIN*%               # Units (inches)
G01*                  # Linear interpolation
%ADD10C,0.010*%       # Define aperture 10 as 0.010" circle
%ADD11R,0.020X0.010*% # Define aperture 11 as 0.020"x0.010" rectangle
D10*                  # Select aperture 10
X1000Y2000D02*        # Move to (1000, 2000)
X3000Y4000D01*        # Draw line to (3000, 4000)
M02*                  # End of file
```

**Key Elements:**
- `%FS...%` - Format specification
- `%ADD...%` - Aperture definitions (tool sizes, shapes)
- `D##*` - Select aperture (tool)
- `X#Y#D##*` - Coordinate command (position + action)
- `M02*` - End of file marker

## Drill File Format (Excellon)

Excellon is the standard format for drill files:

```
M48           # Start of file header
INCH,TZ       # Units (inches) and trailing zeros
T01C0.015     # Tool 01 = 0.015" drill
T02C0.030
%
T01           # Select tool 01
X1000Y2000    # Drill hole at (1000, 2000) - 0.015"
X3000Y4000
T02           # Select tool 02
X5000Y6000    # Drill hole at (5000, 6000) - 0.030"
M30           # End of program
```

**Key Elements:**
- `M48` - Start of header
- `INCH,TZ` - Units and format
- `T##C####` - Tool definition (size in inches)
- `T##` - Select tool
- `X#Y#` - Drill position
- `M30` - End of program

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth3/tests/pcb_generation/17_gerber_drill_export

# Generate PCB
uv run fixture.py

# Export Gerber files (requires kicad-cli)
kicad-cli pcb export gerbers --output ./gerber_drill_export/gerbers \
  ./gerber_drill_export/gerber_drill_export.kicad_pcb

# Export drill files
kicad-cli pcb export drill --output ./gerber_drill_export/gerbers/drill.drl \
  ./gerber_drill_export/gerber_drill_export.kicad_pcb

# Check exported files
ls -la gerber_drill_export/gerbers/

# Inspect Gerber file
head gerber_drill_export/gerbers/*F_Cu.gbr

# Inspect drill file
head gerber_drill_export/gerbers/*.drl

# Upload to JLCPCB or PCBWay
# - Zip gerber files and drill file
# - Upload to manufacturer
# - Confirm design preview matches expectations
```

## Expected Result

- ✅ PCB generated (.kicad_pcb)
- ✅ Gerber files exported (*.gbr)
- ✅ Drill files exported (*.drl or *.xln)
- ✅ Gerber files are valid RS-274X format
- ✅ Drill files are valid Excellon format
- ✅ All copper layers present (F.Cu, B.Cu)
- ✅ Silkscreen layer present (F.Silkscreen)
- ✅ Board outline present (Edge.Cuts)
- ✅ All components appear in Gerbers
- ✅ All holes appear in drill file
- ✅ Files ready for manufacturer submission

## Test Output Example

```
======================================================================
STEP 1: Generate PCB with components
======================================================================
✅ Step 1: PCB generated successfully
   - Project file: gerber_drill_export.kicad_pro
   - PCB file: gerber_drill_export.kicad_pcb

======================================================================
STEP 2: Validate PCB structure
======================================================================
✅ Step 2: PCB structure validated
   - Footprints: 3 (expected: 3) ✓
   - Component references: ['R1', 'R2', 'C1']

======================================================================
STEP 3: Export Gerber files for manufacturing
======================================================================
✅ Step 3: Gerber export successful
   - Gerber directory: gerber_drill_export/gerbers

======================================================================
STEP 4: Export drill files
======================================================================
✅ Step 4: Drill file export successful
   - Drill file: gerber_drill_export.drl

======================================================================
STEP 5: Validate exported files
======================================================================
✅ Step 5: Exported files validated
   - Gerber files found: 7
     - F_Cu.gbr
     - B_Cu.gbr
     - F_Silkscreen.gbr
     - B_Silkscreen.gbr
     - F_Mask.gbr
     - B_Mask.gbr
     - Edge_Cuts.gbr

======================================================================
STEP 6: Validate Gerber file format (RS-274X)
======================================================================
   ✓ F_Cu.gbr - Valid RS-274X format
   ✓ B_Cu.gbr - Valid RS-274X format
   ✓ F_Silkscreen.gbr - Valid RS-274X format
   ✓ Edge_Cuts.gbr - Valid RS-274X format
✅ Step 6: 7/7 files valid RS-274X

======================================================================
STEP 7: Validate drill file format (Excellon)
======================================================================
✅ Step 7: gerber_drill_export.drl - Valid Excellon format ✓
   - Total holes: 12
   - Sample hole: X=10.23, Y=15.45

======================================================================
STEP 8: Validate layer coverage
======================================================================
✅ Step 8: Exported layers found:
   ✓ F.Cu                (Front copper)
   ✓ B.Cu                (Back copper)
   ✓ F.Silkscreen        (Front silkscreen)
   ✓ Edge.Cuts           (Board outline)

======================================================================
STEP 9: Validate manufacturing readiness
======================================================================
✅ Step 9: Manufacturing readiness check
   - Copper layers present: ✓
   - Board outline present: ✓
   - Drill file present: ✓
   - Ready for manufacturing: ✓

======================================================================
✅ TEST PASSED: Gerber & Drill Export
======================================================================
Summary:
  - PCB generated successfully ✓
  - Gerber files exported ✓
  - Drill files exported ✓
  - Gerber format validated ✓
  - Drill format validated ✓
  - Layer coverage checked ✓
  - Manufacturing ready ✓
```

## Key Validation Points

| Aspect | Validation | Expected |
|--------|-----------|----------|
| **Gerber Files** | File exists | *.gbr files in gerber directory |
| **Gerber Format** | RS-274X header | %FS...%, %ADD...%, M02* |
| **Drill File** | File exists | *.drl or *.xln file |
| **Drill Format** | Excellon format | M48, M30, X/Y coordinates |
| **Copper Layers** | F.Cu, B.Cu present | Both files exist |
| **Silkscreen** | F.Silkscreen present | Gerber file present |
| **Outline** | Edge.Cuts present | Board outline in Gerber |
| **All Holes** | Drill file coverage | All holes in *.drl |
| **Component Placement** | Positions correct | Components appear at correct XY |

## Manufacturer Workflow

**JLCPCB, PCBWay, Oshpark (Online Services):**
1. Zip Gerber files + drill file
2. Upload to manufacturer website
3. System automatically parses files
4. Displays preview of board design
5. Confirms all layers and components
6. Approves design for fabrication

**Expected Files for Typical 2-Layer Board:**
- `*.GBR` or `*.gbr` - Gerber files
  - `F_Cu.gbr` - Front copper layer
  - `B_Cu.gbr` - Back copper layer
  - `F_Silkscreen.gbr` - Front label
  - `B_Silkscreen.gbr` - Back label
  - `F_Mask.gbr` - Front solder mask
  - `B_Mask.gbr` - Back solder mask
  - `Edge_Cuts.gbr` - Board outline
- `*.drl` or `*.xln` - Drill file (holes)
- `*.GTO`, `*.GTS` - (Optional) Other manufacturing specs

## Related Tests

- **Test 15**: Silkscreen features (included in Gerber export)
- **Test 16**: Fiducial markers (included in Gerber export)
- **Test 18**: Pick-and-place export (separate from Gerber)

## Test Classification

- **Category**: Manufacturing Output
- **Priority**: CRITICAL - Required for board fabrication
- **Validation Level**: Level 2 (file format validation)
- **Complexity**: Medium (file parsing + format checking)
- **Execution Time**: ~10 seconds
- **Manufacturing Impact**: CRITICAL - Manufacturers require these files

## Gerber File Layers Explanation

| Layer | File | Purpose | Required |
|-------|------|---------|----------|
| **Front Copper** | F_Cu.gbr | Component placement and traces | ✓ Yes |
| **Back Copper** | B_Cu.gbr | Back side traces (2-layer) | ✓ Yes |
| **Front Silk** | F_Silkscreen.gbr | Assembly labels (R1, R2, etc.) | ✓ Yes |
| **Back Silk** | B_Silkscreen.gbr | Back side labels (optional) | ✗ Optional |
| **Front Mask** | F_Mask.gbr | Solder mask (protects copper) | ✓ Yes |
| **Back Mask** | B_Mask.gbr | Solder mask back (optional) | ✗ Optional |
| **Outline** | Edge_Cuts.gbr | Board edge for milling | ✓ Yes |
| **Drill** | .drl/.xln | Hole positions and sizes | ✓ Yes |

## Notes

- RS-274X is the ONLY format accepted by professional PCB manufacturers
- Excellon is the ONLY format accepted by drilling machines
- Some manufacturers accept Gerber X2 (extended format with more metadata)
- Always verify manufacturer's required file format before export
- Gerber and drill files are complete manufacturing specification
- No proprietary KiCad files needed by manufacturer
- Test with manufacturer preview before final order
