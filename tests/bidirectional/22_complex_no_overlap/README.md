# Test 22: Complex Circuit - No Component Overlap

## What This Tests

When adding new components to an existing circuit with positioned components, the placement algorithm must not place new components on top of existing ones.

## When This Situation Happens

- User has circuit with multiple components already positioned in KiCad
- User adds new components in Python code
- Regenerates KiCad project
- New components should be placed in available space, not overlapping existing ones

## What Should Work

1. Circuit has voltage regulator with capacitors (C1, U1, C2)
2. Components initially auto-placed or manually positioned
3. User adds LED circuit (R1, D1) in Python
4. Regenerates KiCad
5. New components (R1, D1) placed without overlapping C1, U1, or C2

## Manual Test Instructions

### Phase 1: Initial Circuit (Small Components)

```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional/22_complex_no_overlap

# Step 1: Generate initial circuit (regulator + LED only)
uv run voltage_regulator_led.py

# Step 2: Open in KiCad
open voltage_regulator_led/voltage_regulator_led.kicad_pro

# Step 3: Visual inspection in schematic editor
#   Check that NO components overlap:
#   - C1 (input cap) should have clear space around it
#   - U1 (LM7805) should have clear space around it
#   - C2 (output cap) should have clear space around it
#   - R1 (LED resistor) should have clear space around it
#   - D1 (LED) should have clear space around it
#
#   Total: 5 components (C1, U1, C2, R1, D1)
```

### Phase 2: Add Large Components (Test Overlap Avoidance)

```bash
# Step 4: Edit voltage_regulator_led.py
# Uncomment the line: # add_large_components()
# (Around line 168)

# Step 5: Regenerate with additional large components
uv run voltage_regulator_led.py

# Step 6: Open updated KiCad project
open voltage_regulator_led/voltage_regulator_led.kicad_pro

# Step 7: Visual inspection - now with 13 total components
#   Original components (should be in same positions):
#   - C1, U1, C2, R1, D1
#
#   New large components (should NOT overlap originals):
#   - C3, C4 (large electrolytic caps - 10mm and 8mm diameter)
#   - J1, J2 (screw terminal connectors - large footprints)
#   - U2 (comparator IC)
#   - L1 (inductor)
#   - R2, R3 (voltage divider resistors)
#
#   Critical checks:
#   - NO overlapping symbols
#   - Large components placed in available space
#   - Original component positions preserved
#   - All 13 reference designators visible
```

### Phase 3: Advanced Testing (Optional)

```bash
# Step 8: Manually move some components in KiCad
#   - Open schematic editor
#   - Move C1 to a specific position
#   - Move U1 to center of page
#   - Save schematic

# Step 9: Regenerate (tests position preservation + overlap avoidance)
uv run voltage_regulator_led.py

# Step 10: Verify in KiCad
#   - Manually moved components (C1, U1) stay in their positions
#   - Other components avoid the manually positioned ones
#   - No overlaps anywhere
```

## Expected Result

### Phase 1 (Initial Circuit):
- ✅ All 5 components present: C1, U1, C2, R1, D1
- ✅ No overlapping component symbols
- ✅ No overlapping text labels
- ✅ Reasonable spacing between components
- ✅ All reference designators visible

### Phase 2 (With Large Components):
- ✅ All 13 components present (original 5 + 8 new large ones)
- ✅ Original component positions preserved
- ✅ Large components (C3, C4, J1, J2) placed in available space
- ✅ NO overlaps between any components
- ✅ Large footprints don't obscure small components
- ✅ Circuit remains readable despite complexity

### Phase 3 (Manual Positioning):
- ✅ Manually moved components stay in their positions
- ✅ Auto-placed components avoid manually positioned ones
- ✅ No overlaps after regeneration

## Why This Is Critical

Component overlap makes schematics unreadable and unprofessional. The placement algorithm must detect existing component positions and place new components in available space. This is essential for:

- Adding components to existing designs
- Iterative circuit development
- Maintaining schematic readability
- Professional documentation

## Test Variations

To test different scenarios, you can modify the Python code:

1. **Comment out LED circuit** → Generate → Uncomment LED → Regenerate
   - Tests adding components after initial generation

2. **Manually reposition components in KiCad** → Add more components in Python → Regenerate
   - Tests respecting manual layout while adding new parts

3. **Add more components** (e.g., more capacitors, more LEDs)
   - Tests placement with higher component density

## Related

- Test 21: Position preservation (tests NOT moving existing components)
- This test: Collision detection (tests NOT overlapping when adding new ones)
