# Test 50: Component Footprint Change

## What This Tests
Validates that changing component footprints in Python correctly updates KiCad while preserving:
1. **Component position** - Moved positions are preserved through footprint changes
2. **Component symbol** - Symbol remains unchanged (still a resistor)
3. **Component reference** - Reference stays the same (R1)
4. **Netlist footprint field** - Footprint field updated in netlist
5. **Connections** - All net connections preserved

Tests two types of footprint changes:
1. **SMD to SMD** - 0603 → 0805 (surface mount)
2. **SMD to THT** - 0805 → Through-hole (mount type change)

## Why This Test Matters
Footprint changes are common during design iteration:
- Designer realizes 0603 is too small for hand soldering → switch to 0805
- Designer wants through-hole for easier prototyping → switch from SMD to THT
- Different package available or in stock → switch to compatible footprint

**Critical:** Footprint changes should NOT require re-placing components or re-routing connections.

## Difference from Related Tests
- **Test 30 (missing footprint)**: Tests adding footprints when none exists
- **Test 19 (swap component type)**: Tests changing symbol type (R→C), not just footprint
- **Test 50 (this test)**: Tests only footprint changes, symbol stays same

## When This Situation Happens
- Developer generates circuit from Python (R1 with 0603 footprint)
- Opens KiCad and manually positions R1 at specific location
- Realizes 0603 is too small for manual assembly
- Changes footprint in Python: 0603 → 0805
- Regenerates KiCad - R1 should stay at same position with new footprint
- Later changes to through-hole for easier prototyping
- Regenerates again - R1 still at same position with THT footprint

## What Should Work

### Phase 1: SMD to SMD (0603 → 0805)
1. Generate KiCad with R1 (0603 footprint) at default position
2. Move R1 to specific position (100, 50) in KiCad
3. Change footprint in Python: 0603 → 0805
4. Regenerate KiCad from Python
5. Validate:
   - R1 still at position (100, 50) ✓
   - Footprint changed to 0805 ✓
   - Symbol still shows resistor ✓
   - Reference still R1 ✓
   - Netlist footprint field updated ✓

### Phase 2: SMD to THT (0805 → Through-hole)
6. Change footprint in Python: 0805 → THT (Resistor_THT:R_Axial_DIN0207)
7. Regenerate KiCad from Python
8. Validate:
   - R1 still at position (100, 50) ✓
   - Footprint changed to THT ✓
   - Symbol still shows resistor ✓
   - Reference still R1 ✓
   - Netlist footprint field updated ✓
   - Mount type changed from SMD to THT ✓

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth2/tests/bidirectional/50_component_footprint_change

# Step 1: Generate initial KiCad project (R1, 0603)
uv run resistor_footprints.py
open resistor_footprints/resistor_footprints.kicad_pro

# Step 2: In KiCad schematic editor:
#   - Move R1 to specific position (e.g., x=100mm, y=50mm)
#   - Save (Cmd+S)
#   - Note the position where you moved it
# Close KiCad

# Step 3: Change footprint in Python (0603 → 0805)
# Edit resistor_footprints.py:
#   Change: footprint="Resistor_SMD:R_0603_1608Metric"
#   To:     footprint="Resistor_SMD:R_0805_2012Metric"

# Step 4: Regenerate KiCad with new footprint
uv run resistor_footprints.py

# Step 5: Open regenerated KiCad and verify
open resistor_footprints/resistor_footprints.kicad_pro
# Verify:
#   - Reference still R1 (not changed)
#   - Value still 10k (not changed)
#   - Footprint changed to 0805 (from 0603)
#   - Position preserved (same x=100, y=50 you set in step 2)
#   - Symbol still shows resistor (not changed)

# Step 6: Change to through-hole footprint (0805 → THT)
# Edit resistor_footprints.py:
#   Change: footprint="Resistor_SMD:R_0805_2012Metric"
#   To:     footprint="Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal"

# Step 7: Regenerate KiCad with THT footprint
uv run resistor_footprints.py

# Step 8: Open regenerated KiCad and verify
open resistor_footprints/resistor_footprints.kicad_pro
# Verify:
#   - Reference still R1
#   - Value still 10k
#   - Footprint changed to THT (from 0805)
#   - Position still preserved (x=100, y=50)
#   - Symbol still shows resistor
#   - Mount type changed from SMD to THT
```

## Expected Result

### Phase 1: SMD to SMD
- Initial KiCad has R1 with 0603 footprint at default position
- After moving R1 in KiCad, position is (100, 50)
- After changing to 0805 in Python and regenerating:
  - R1 stays at (100, 50) ✓
  - Footprint shows 0805 ✓
  - Symbol unchanged (resistor) ✓
  - Reference unchanged (R1) ✓

### Phase 2: SMD to THT
- After changing to THT in Python and regenerating:
  - R1 still at (100, 50) ✓
  - Footprint shows THT ✓
  - Symbol unchanged (resistor) ✓
  - Reference unchanged (R1) ✓
  - Mount type changed to through-hole ✓

## Validation Levels

### Level 1: Text Pattern Matching (Not Used)
- Not sufficient for footprint validation

### Level 2: Semantic Validation (Used)
- **kicad-sch-api**: Parse schematic and validate:
  - Component reference (R1)
  - Component footprint property (0603 → 0805 → THT)
  - Component position (100, 50) preserved
  - Component symbol (Device:R) unchanged
  - Component UUID preserved (same component, not removed/added)

### Level 3: Netlist Validation (Used)
- Parse netlist and validate:
  - Component footprint field matches expected value
  - Footprint changes reflected in netlist

## Implementation Notes

This test demonstrates that footprint changes are handled correctly by:
1. **UUID-based matching** - Synchronizer matches R1 by UUID, not footprint
2. **Property updates** - Footprint property updated in-place
3. **Position preservation** - Position is canonical and preserved
4. **Symbol stability** - Symbol (Device:R) unchanged, only footprint changes

The test validates that changing footprints does NOT trigger component removal/re-addition, which would break position preservation.
