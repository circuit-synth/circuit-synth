# Test 03: Position Preservation - Component Layout Stability

**Priority:** P0 (CRITICAL) ⚠️
**Category:** Foundation - Layout Stability
**Tests:** 6 total
**Status:** In Development

## Overview

CRITICAL tests validating that component positions on the schematic are preserved through bidirectional sync cycles.

This test suite validates that:
- Component X,Y coordinates extracted from KiCad schematic files
- Position information preserved when re-exporting to KiCad
- Manual position changes in KiCad survive import→export cycle
- Multiple components maintain correct relative positions
- No spurious position drift on repeated cycles
- Position data survives round-trip with <0.1mm tolerance

**Why P0 CRITICAL:** Position preservation is essential for:
- Maintaining user-intentional manual routing/layout
- Preventing layout chaos on re-generation
- Supporting interactive workflows where user arranges components
- Ensuring professional schematics remain clean

## Test Cases

### Test 3.1: Extract Component Position from KiCad
**What:** Import KiCad schematic and extract R1's X,Y coordinates
**Validates:**
- Position coordinates correctly extracted from .kicad_sch file
- Coordinates match manual placement in KiCad
- Coordinate format preserved (millimeters, exact precision)
- Position data includes rotation angle

### Test 3.2: Preserve Position on Export
**What:** KiCad → Python → KiCad preserves component position
**Validates:**
- Extracted position exported back to KiCad format
- Position remains within tolerance (<0.1mm deviation)
- No spurious position movement on cycle
- Rotation preserved (if component rotated)

### Test 3.3: Multiple Component Position Stability
**What:** 3+ components with different positions maintain relative layout
**Validates:**
- All component positions extracted correctly
- Relative positions preserved (distance between components stable)
- No components drift into unexpected coordinates
- Layout integrity maintained

### Test 3.4: Manual Position Changes Survive Round-Trip
**What:** User manually moves component in KiCad, imports, position preserved
**Validates:**
- Manual position changes preserved through import
- Not overwritten by generation algorithm
- User intent respected in round-trip
- Position retained exactly (not approximated)

### Test 3.5: Position Stability on Repeated Cycles
**What:** Multiple round-trip cycles don't cause position drift
**Validates:**
- Position remains stable after 1st round-trip
- No further drift on 2nd, 3rd round-trips
- Cumulative drift less than 0.01mm after 3 cycles
- Idempotent position preservation

### Test 3.6: Rotated Component Position
**What:** Component with rotation preserved through round-trip
**Validates:**
- Rotation angle extracted from KiCad
- Rotation preserved when re-exporting
- Position + rotation maintained together
- No interaction between position and rotation

## Test Fixtures

Required files in `03_kicad_ref/`:
- `03_kicad_ref.kicad_pro` - KiCad project with positioned components
- `03_kicad_ref.kicad_sch` - Schematic with R1 at specific coordinates
- `03_kicad_ref.kicad_prl` - Project-local settings

**Fixture Setup:**
- R1 (10k) positioned at X=30mm, Y=40mm, rotation=0°
- Single component to isolate position behavior

## Manual Setup Required

You must create a KiCad project with a positioned resistor:

1. Open KiCad
2. Create new project: `03_kicad_ref`
3. In schematic editor:
   - Add symbol: Device → R (Resistor)
   - Set reference: R1
   - Set value: 10k
   - Save schematic
4. Manually move component:
   - Click and drag R1 to position X=30mm, Y=40mm
   - Verify position in Properties panel
5. Save schematic
6. Copy project files to `03_kicad_ref/` directory

## Implementation Notes

- Uses same cleanup/preservation pattern as previous tests
- Generates to `positioned_resistor/` directory (test cleans before/after)
- Position validation uses regex to extract (at X Y rotation) from .kicad_sch
- Tolerance check: abs(extracted - original) < 0.1mm for X and Y
- Tests may need position parsing from KiCad's internal coordinate format

## Position Data Format

KiCad schematic uses this format for component position:
```
(symbol (lib_id "Device:R")
    (at 30.48 35.56 0)  ← X, Y coordinates in mm, rotation in degrees
    (unit 1)
```

Parser should extract:
- X coordinate: 30.48 (float, mm)
- Y coordinate: 35.56 (float, mm)
- Rotation: 0 (int, degrees: 0, 90, 180, 270)

## Related Tests

- **Previous:** 02_single_component (basic CRUD)
- **Next:** 06_round_trip (full cycle validation)
- **Parallel:** 07_user_content_preservation (annotations)
- **Critical Set:** Tests 03, 06, 07, 08 must all pass for release

## Critical Success Criteria

For this test suite to pass:
1. All 6 tests must pass
2. Position drift must be < 0.01mm after 3 cycles
3. Relative positions between components must be preserved exactly
4. Manual position changes must not be overwritten
5. Rotation angle must be preserved with position
