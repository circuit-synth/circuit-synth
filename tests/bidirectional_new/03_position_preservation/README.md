# Test 03: Position Preservation - Component Layout Stability

**Priority:** P0 (CRITICAL) ⚠️
**Category:** Foundation - Layout Stability
**Tests:** 6 total
**Status:** In Development

## Overview

CRITICAL tests validating that component positions on the schematic AND PCB are preserved through bidirectional sync cycles.

This test suite validates that:
- Component X,Y coordinates extracted from KiCad schematic and PCB files
- Position information preserved when re-exporting to KiCad (both schematic and PCB)
- Manual position changes in KiCad survive import→export cycle
- Multiple components maintain correct relative positions
- No spurious position drift on repeated cycles
- Position data (schematic + PCB footprint) survives round-trip with <0.1mm tolerance
- Footprint placement on PCB matches schematic positioning

**Why P0 CRITICAL:** Position preservation is essential for:
- Maintaining user-intentional manual routing/layout
- Preventing layout chaos on re-generation
- Supporting interactive workflows where user arranges components
- Ensuring professional schematics remain clean

## Test Cases

### Test 3.1: Extract Component Position from KiCad
**What:** Import KiCad schematic and PCB, extract R1's X,Y coordinates and footprint placement
**Validates:**
- Position coordinates correctly extracted from .kicad_sch file
- Footprint coordinates correctly extracted from .kicad_pcb file
- Coordinates match manual placement in KiCad
- Coordinate format preserved (millimeters, exact precision)
- Position data includes rotation angle
- Schematic position and PCB placement match

### Test 3.2: Preserve Position on Export
**What:** KiCad → Python → KiCad (schematic + PCB) preserves component position and footprint placement
**Validates:**
- Extracted schematic position exported back to KiCad schematic format
- Extracted PCB footprint placement exported back to PCB format
- Position remains within tolerance (<0.1mm deviation)
- No spurious position movement on cycle
- Rotation preserved (if component rotated) in both files
- Footprint placement matches schematic after round-trip

### Test 3.3: Multiple Component Position Stability
**What:** 3+ components with different positions on schematic and PCB maintain relative layout
**Validates:**
- All component positions extracted correctly from schematic
- All footprint placements extracted correctly from PCB
- Relative positions preserved (distance between components stable)
- No components drift into unexpected coordinates
- Layout integrity maintained in both schematic and PCB
- Footprint spacing matches schematic spacing

### Test 3.4: Manual Position Changes Survive Round-Trip
**What:** User manually moves component in KiCad schematic and PCB, imports, position preserved
**Validates:**
- Manual schematic position changes preserved through import
- Manual PCB footprint placement changes preserved through import
- Not overwritten by generation algorithm
- User intent respected in round-trip
- Position retained exactly (not approximated)
- Schematic and PCB positions remain synchronized

### Test 3.5: Position Stability on Repeated Cycles
**What:** Multiple round-trip cycles (schematic + PCB) don't cause position drift
**Validates:**
- Position remains stable after 1st round-trip (schematic + PCB)
- No further drift on 2nd, 3rd round-trips
- Cumulative drift less than 0.01mm after 3 cycles (both files)
- Idempotent position preservation
- Footprint placement stable across cycles
- No rounding errors accumulating

### Test 3.6: Rotated Component Position
**What:** Component with rotation (schematic + PCB footprint) preserved through round-trip
**Validates:**
- Rotation angle extracted from KiCad schematic
- Footprint rotation extracted from KiCad PCB
- Rotation preserved when re-exporting (both files)
- Position + rotation maintained together
- No interaction between position and rotation
- Footprint rotation matches schematic after round-trip

## Test Fixtures

Required files in `03_kicad_ref/`:
- `03_kicad_ref.kicad_pro` - KiCad project with positioned components
- `03_kicad_ref.kicad_sch` - Schematic with R1 at specific coordinates
- `03_kicad_ref.kicad_pcb` - PCB with footprint placed at matching coordinates
- `03_kicad_ref.kicad_prl` - Project-local settings

**Fixture Setup:**
- R1 (10k) positioned at X=30mm, Y=40mm, rotation=0° in schematic
- R1 footprint placed at X=30mm, Y=40mm on PCB (must match schematic)
- Single component to isolate position behavior
- Both schematic and PCB must have synchronized positioning

## Manual Setup Required

You must create a KiCad project with a positioned resistor in both schematic and PCB:

1. Open KiCad
2. Create new project: `03_kicad_ref`
3. In schematic editor:
   - Add symbol: Device → R (Resistor)
   - Set reference: R1
   - Set value: 10k
   - Manually move component to position X=30mm, Y=40mm
   - Verify position in Properties panel
   - Save schematic
4. In PCB editor:
   - Tools → Update PCB from Schematic (to create footprint)
   - Place footprint at X=30mm, Y=40mm (must match schematic)
   - Verify footprint position matches schematic in Properties panel
   - Save PCB
5. Copy project files to `03_kicad_ref/` directory:
   - Verify all files present: .kicad_pro, .kicad_sch, .kicad_pcb, .kicad_prl

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
