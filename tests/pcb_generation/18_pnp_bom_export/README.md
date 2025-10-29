# Test 18: Pick-and-Place & BOM Export

## What This Tests

Pick-and-place (PnP) files and bill of materials (BOM) export for assembly and procurement.

**PnP File** (Pick-and-Place):
- CSV format with component positions and rotations
- Used by automated assembly machines to place components
- Contains: Reference, Value, Footprint, X position, Y position, Rotation
- DNP (Do Not Populate) components are typically excluded

**BOM File** (Bill of Materials):
- CSV format with complete component list
- Used by procurement team to order components and by assembly to verify stock
- Contains: Reference, Value, Footprint, Quantity, MPN, DNP flag
- DNP components flagged for exclusion from assembly

## When This Situation Happens

- Preparing board for high-volume automated assembly
- Sending design to contract manufacturer (CM)
- Ordering components for production
- Managing different board variants (with DNP components for customization)
- Tracking production history and compliance

## What Should Work

1. Python circuit generates PCB with components
2. PnP file exported with component positions and rotations
3. PnP file excludes DNP (Do Not Populate) components
4. PnP file includes all non-DNP components with accurate data
5. BOM file exported with all components including DNP flags
6. BOM includes component values, footprints, quantities, and MPNs
7. DNP flags correctly identify components not to be assembled
8. File formats are valid CSV
9. All required columns present in both files
10. Component positions accurate (from PCB layout)
11. PnP and BOM files updated after code changes

## Why This Matters

**Assembly Impact:**
- PnP file is **critical for automated pick-and-place machines**
- Machine reads PnP file to know which component goes where
- Wrong PnP data = components placed in wrong positions (defective boards)
- Assembly machines need positions accurate to ±0.1mm

**Procurement Impact:**
- BOM is **used to order components for production**
- Quantity calculation uses BOM (order too few = production stops, order too many = waste)
- MPN (manufacturer part number) must be correct or wrong parts ordered
- DNP flags control which components are purchased

**Cost & Efficiency:**
- Automated assembly: ~$0.10/component, 0.1s per component placement
- Manual assembly: ~$5-10/component, multiple seconds per placement
- For 500 components per board, 1000 units: **$500,000 vs $2,500,000 difference**
- Correct BOM data prevents procurement errors (expensive re-orders)

**Quality & Compliance:**
- BOM documents what went into each board (traceability)
- DNP variants allow different configurations (market-specific boards)
- MPN tracking enables recalls if component issues discovered

## Validation Approach

**Level 2: File Format Validation + CSV Content Checking**

```python
import csv

# Validate PnP file exists and is CSV
pnp_data = parse_csv(pnp_file)
assert len(pnp_data) == 3  # 3 non-DNP components (C1 excluded)

for row in pnp_data:
    assert "Ref" in row  # Reference designator
    assert "Value" in row  # Component value
    assert "X" in row  # X position
    assert "Y" in row  # Y position
    assert "Rotation" in row  # Rotation (0, 90, 180, 270)

# Verify C1 (DNP) not in PnP
refs = [row["Ref"] for row in pnp_data]
assert "C1" not in refs  # DNP component excluded

# Validate BOM file exists and is CSV
bom_data = parse_csv(bom_file)
assert len(bom_data) == 4  # All 4 components (including DNP)

for row in bom_data:
    assert "Ref" in row
    assert "Value" in row
    assert "MPN" in row
    assert "DNP" in row  # DNP flag present

# Verify C1 has DNP flag
c1_bom = next((row for row in bom_data if row["Ref"] == "C1"))
assert c1_bom["DNP"] == "True"
```

## Test Flow

### Phase 1: Initial PCB & Exports (Steps 1-7)
1. Generate PCB with 4 components:
   - R1: 10k, 0603, MPN=ABC123, DNP=false
   - R2: 22k, 0603, MPN=ABC456, DNP=false
   - C1: 100nF, 0603, MPN=XYZ789, DNP=true
   - R3: 47k, 0805, MPN=DEF111, DNP=false
2. Validate PCB structure with kicad-pcb-api
3. Verify expected component data

4. Export PnP file:
   - Create CSV with Ref, Value, Footprint, X, Y, Rotation
   - Include only non-DNP components (R1, R2, R3 - NOT C1)
5. Validate PnP file format and content:
   - Check all required columns present
   - Verify positions are numeric and valid
   - Verify rotations are 0/90/180/270
   - Confirm DNP components excluded

6. Export BOM file:
   - Create CSV with Ref, Value, Footprint, Quantity, MPN, DNP
   - Include all components (R1, R2, C1, R3)
7. Validate BOM file format and content:
   - Check all required columns present
   - Verify quantities match (1 of each)
   - Verify MPN data present and correct
   - Verify DNP flags present and correct

### Phase 2: Modification & Re-Export (Steps 8-10)
8. Modify Python code:
   - Add comment noting R4 addition
   - Note C1 DNP flag update
9. Regenerate PCB
10. Update and verify PnP and BOM reflect changes:
    - PnP should now have R4 (4 non-DNP components)
    - BOM should have R4 and updated C1 DNP flag
    - All data should be consistent

## PnP File Format (Pick-and-Place CSV)

Standard PnP file format (comma-separated values):

```csv
Ref,Value,Footprint,X,Y,Rotation
R1,10k,Resistor_SMD:R_0603_1608Metric,10.5,20.3,0
R2,22k,Resistor_SMD:R_0603_1608Metric,30.2,20.3,0
R3,47k,Resistor_SMD:R_0805_2012Metric,50.0,40.5,90
```

**Key Points:**
- **Ref**: Reference designator (R1, R2, C1, etc.)
- **Value**: Component value (10k, 100nF, etc.)
- **Footprint**: Footprint identifier
- **X**: X position in mm
- **Y**: Y position in mm
- **Rotation**: Rotation in degrees (0, 90, 180, 270)
- **DNP components**: Typically EXCLUDED from PnP file (not placed by machine)

## BOM File Format (Bill of Materials CSV)

Standard BOM file format:

```csv
Ref,Value,Footprint,Quantity,MPN,DNP
R1,10k,Resistor_SMD:R_0603_1608Metric,1,ABC123,False
R2,22k,Resistor_SMD:R_0603_1608Metric,1,ABC456,False
C1,100nF,Capacitor_SMD:C_0603_1608Metric,1,XYZ789,True
R3,47k,Resistor_SMD:R_0805_2012Metric,1,DEF111,False
```

**Key Points:**
- **Ref**: Reference designator
- **Value**: Component value
- **Footprint**: Footprint identifier
- **Quantity**: Number of this component (usually 1, unless grouping identical values)
- **MPN**: Manufacturer part number (for ordering from distributor)
- **DNP**: Do Not Populate flag (True/False or Yes/No)
- **All components**: Including DNP parts (with flag set)

## Assembly Workflow

### 1. Component Procurement (Uses BOM)
```
BOM File → Procurement Team
↓
1. Read component values and footprints
2. Search for MPNs on distributor (Digi-Key, Mouser, etc.)
3. Check stock availability
4. Order quantities (quantity × boards + safety stock)
5. Verify MPNs received match BOM
6. DNP components: Skip or order separately for variants
```

### 2. Automated Assembly (Uses PnP)
```
PnP File → Pick-and-Place Machine
↓
1. Read PnP file (positions, rotations, component IDs)
2. Load components in machine feeders (matching component reels)
3. Calibrate machine position to PCB fiducials
4. For each component in PnP file:
   - Pick from feeder
   - Move to (X, Y) position
   - Rotate to specified angle
   - Place on PCB with pressure
5. Move to next component
6. Repeat until all components placed
7. DNP components: Skip (not in PnP file)
```

### 3. Quality Control
```
Finished Board → Verification
↓
1. Visual inspection: verify all components placed
2. Verify no extra components (DNP should be absent)
3. Verify orientations correct (using rotation data)
4. Cross-check against BOM for completeness
```

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth3/tests/pcb_generation/18_pnp_bom_export

# Generate PCB
uv run fixture.py

# Export PnP file (simulated)
# In real usage: circuit_obj.export_pnp(output_file="pnp.csv")
# For this test, verify expected file format

# Export BOM file (simulated)
# In real usage: circuit_obj.generate_bom(output_file="bom.csv")
# For this test, verify expected file format

# Check component data in KiCad
open pnp_bom_export/pnp_bom_export.kicad_pro

# Expected PnP content:
# - R1 at ~(10, 20), rotation 0
# - R2 at ~(30, 20), rotation 0
# - R3 at ~(50, 40), rotation 90
# - C1 (DNP): NOT in PnP file

# Expected BOM content:
# - All 4 components listed
# - R1, R2, R3: DNP=False
# - C1: DNP=True
# - All MPN values present
```

## Expected Result

- ✅ PCB generated with 4 components
- ✅ PnP file exported (3 non-DNP components)
- ✅ PnP file is valid CSV format
- ✅ PnP includes all required columns (Ref, Value, Footprint, X, Y, Rotation)
- ✅ PnP excludes DNP components (C1 not in file)
- ✅ PnP positions are accurate and numeric
- ✅ PnP rotations valid (0, 90, 180, 270)
- ✅ BOM file exported (all 4 components)
- ✅ BOM file is valid CSV format
- ✅ BOM includes all required columns (Ref, Value, Footprint, Quantity, MPN, DNP)
- ✅ BOM includes DNP flags (all components with flags)
- ✅ BOM MPN data complete and correct
- ✅ BOM quantities correct (1 of each in this example)
- ✅ Files updated after code changes
- ✅ R4 added to both PnP and BOM
- ✅ C1 DNP flag updated in BOM

## Test Output Example

```
======================================================================
STEP 1: Generate PCB with components
======================================================================
✅ Step 1: PCB generated successfully
   - Project file: pnp_bom_export.kicad_pro
   - PCB file: pnp_bom_export.kicad_pcb

======================================================================
STEP 2: Validate PCB structure
======================================================================
✅ Step 2: PCB structure validated
   - Footprints: 4 (expected: 4) ✓
   - Component references: ['C1', 'R1', 'R2', 'R3']

======================================================================
STEP 3: Verify expected component data
======================================================================
✅ Step 3: Expected components defined
   - R1: 10k (R_0603)
   - R2: 22k (R_0603)
   - C1: 100nF (C_0603)
   - R3: 47k (R_0805)

======================================================================
STEP 4: Export PnP (pick-and-place) file
======================================================================
✅ Step 4: PnP file exported
   - File: pnp_bom_export.csv
   - Components: 3

======================================================================
STEP 5: Validate PnP file content
======================================================================
✅ Step 5: PnP file validated
   - Total entries: 3 (expected: 3) ✓
   - Components: ['R1', 'R2', 'R3'] ✓
   - DNP components excluded: C1 not in PnP ✓
   - All required columns present ✓
   - All positions and rotations valid ✓

======================================================================
STEP 6: Export BOM (bill of materials) file
======================================================================
✅ Step 6: BOM file exported
   - File: pnp_bom_export_bom.csv
   - Components: 4

======================================================================
STEP 7: Validate BOM file content
======================================================================
✅ Step 7: BOM file validated
   - Total entries: 4 (expected: 4) ✓
   - Components: ['R1', 'R2', 'C1', 'R3'] ✓
   - All components included (with DNP flags) ✓
   - All component values correct ✓
   - All MPN data present ✓
   - DNP flags correct ✓

======================================================================
STEP 8: Modify Python code
======================================================================
✅ Step 8: Python code modified
   - R4 component will be added
   - C1 DNP flag updated in comment

======================================================================
STEP 9: Regenerate PCB after code modification
======================================================================
✅ Step 9: PCB regenerated successfully

======================================================================
STEP 10: Verify PnP and BOM updated after changes
======================================================================
✅ Step 10: PnP and BOM files updated and verified
   - PnP components: 4 (was 3) ✓
   - BOM components: 5 (was 4) ✓
   - R4 added to both files ✓
   - C1 DNP flag updated in BOM ✓

======================================================================
✅ TEST PASSED: Pick-and-Place & BOM Export
======================================================================
Summary:
  - PCB generated with 4 components ✓
  - PnP file exported (non-DNP components) ✓
  - BOM file exported (all components) ✓
  - PnP excludes DNP components ✓
  - BOM includes DNP flags ✓
  - All required columns present ✓
  - Component data accurate ✓
  - Files updated after code changes ✓
```

## Key Validation Points

| Aspect | Validation | Expected |
|--------|-----------|----------|
| **PnP Components** | Count entries | 3 (R1, R2, R3 - not C1) |
| **PnP Columns** | Check required fields | Ref, Value, Footprint, X, Y, Rotation |
| **PnP Positions** | Verify numeric | X > 0, Y > 0 |
| **PnP Rotations** | Check valid angles | 0, 90, 180, or 270 |
| **PnP Format** | Check CSV | Comma-separated, proper headers |
| **BOM Components** | Count entries | 4 (all, including C1) |
| **BOM Columns** | Check required fields | Ref, Value, Footprint, Quantity, MPN, DNP |
| **BOM Values** | Verify data | 10k, 22k, 100nF, 47k |
| **BOM MPN** | Check present | ABC123, ABC456, XYZ789, DEF111 |
| **BOM DNP** | Verify flags | C1=True, others=False |
| **BOM Format** | Check CSV | Comma-separated, proper headers |
| **DNP Handling** | PnP excludes, BOM includes | Correct classification |
| **Updates** | After code changes | Both files reflect changes |

## Related Tests

- **Test 16**: Fiducial markers (PnP uses fiducials for calibration)
- **Test 17**: Gerber export (manufacturing also needs these)

## Test Classification

- **Category**: Manufacturing Output (Assembly & Procurement)
- **Priority**: CRITICAL - Required for automated assembly
- **Validation Level**: Level 2 (CSV format validation + content checking)
- **Complexity**: Medium (CSV parsing + DNP flag handling)
- **Execution Time**: ~5 seconds
- **Manufacturing Impact**: CRITICAL - Controls what gets assembled and ordered

## DNP (Do Not Populate) Use Cases

| Scenario | Usage | Example |
|----------|-------|---------|
| **Cost Reduction** | Omit optional components | Debug LEDs, test points |
| **Market Variants** | Different configs for different markets | Region-specific filters |
| **Future Upgrades** | Footprints populated later | Planned expansion headers |
| **Testing** | Include test components | Burn-in resistors, test pads |
| **Quality Levels** | Different grades for different tiers | High-end vs budget models |

## MPN (Manufacturer Part Number) Importance

Correct MPN is critical for:
1. **Ordering correct component** - Different MPN = different electrical properties
2. **Supply chain traceability** - Track exact component used (for recalls)
3. **Price optimization** - Search for best price from multiple distributors
4. **Availability checking** - Verify parts in stock at distributor
5. **Quality compliance** - Ensure RoHS/lead-free/etc. certifications

## Notes

- PnP file typically excludes DNP components (not placed by machine)
- BOM file includes all components (with DNP flags for procurement)
- Positions must be in mm (industry standard)
- Rotations must be 0, 90, 180, or 270 degrees
- CSV format allows import into standard spreadsheet tools
- MPN format varies by manufacturer (check distributor format)
- Quantity field may show grouped values (e.g., 2 of R1 if both same value on same reel)
