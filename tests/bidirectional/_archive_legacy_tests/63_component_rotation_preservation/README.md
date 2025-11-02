# Test 63: Component Rotation Preservation

**Priority:** Priority 2 (Nice-to-have - Aesthetic feature)

**Status:** Not yet implemented

## Purpose

Test comprehensive rotation preservation for multiple components at different angles during bidirectional synchronization.

## Test Scenario

This test validates that component rotation angles are preserved through bidirectional sync cycles, even when components are modified or new components are added.

### Workflow

1. **Initial Generation**
   - Create circuit with 4 resistors (R1, R2, R3, R4)
   - Generate to KiCad with default rotations (all at 0°)

2. **Manual Rotation in KiCad**
   - R1: 0° (horizontal - unchanged)
   - R2: 90° (vertical)
   - R3: 180° (horizontal reversed)
   - R4: 270° (vertical reversed)

3. **Synchronize Back**
   - Read KiCad schematic
   - Capture all rotation angles in Python circuit object

4. **Modify in Python**
   - Change R2 value from 10k to 22k
   - Regenerate to KiCad

5. **Validate Rotation Preservation**
   - R1 still at 0°
   - R2 still at 90° (despite value change)
   - R3 still at 180°
   - R4 still at 270°
   - All rotations preserved independently of component modifications

6. **Add New Component**
   - Add R5 with value 100k
   - Regenerate to KiCad

7. **Final Validation**
   - R1-R4 rotations still preserved at original angles
   - R5 at default rotation (0° or auto-placed)
   - Existing rotations not affected by new component addition

## Validation Levels

### Level 2: Semantic Validation (kicad-sch-api)
- Load schematic with `Schematic.load()`
- Access `component.rotation` property for each resistor
- Verify rotation values match expected angles:
  - R1: 0°
  - R2: 90°
  - R3: 180°
  - R4: 270°
  - R5: 0° (default)

### Visual Inspection
- Open in KiCad
- Confirm visual orientation matches rotation values
- R2 and R4 should be vertical
- R1, R3, and R5 should be horizontal

## Expected Behavior

**SHOULD PASS:**
- Rotation is part of "position preservation" feature
- Synchronizer captures rotation along with position
- Rotation preserved independently of value changes
- New components don't affect existing rotations

## Key Requirements

1. **Rotation Independence**
   - Rotation changes don't affect position
   - Value changes don't affect rotation
   - Component additions don't reset rotations

2. **All Angles Supported**
   - 0°, 90°, 180°, 270° (cardinal directions)
   - Arbitrary angles if supported by KiCad format

3. **Preservation Through Sync**
   - KiCad → Python: Capture rotation
   - Python → KiCad: Restore rotation
   - Modifications: Maintain rotation

## Files

- `README.md` - This file
- `rotated_components.py` - Python circuit definition (4 resistors)
- `test_63_rotation.py` - Automated test script

## Related Tests

- Test 09: Position preservation
- Test 20: Component orientation (basic rotation)
- Test 64: Complex multi-step workflow

## Notes

- Rotation angles in KiCad are typically stored in degrees (0-360)
- kicad-sch-api exposes rotation as a numeric property
- Some components may have restricted rotation angles (e.g., polarized parts)
- This test focuses on passive components (resistors) with full rotation freedom

## Implementation Strategy

1. Use regex to modify `(at X Y ANGLE)` in .kicad_sch file
2. Extract rotation from schematic using kicad-sch-api
3. Compare rotation values before/after regeneration
4. Validate rotation preservation is decoupled from other properties
