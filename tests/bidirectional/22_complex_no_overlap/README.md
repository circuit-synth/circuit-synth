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

```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional/22_complex_no_overlap

# Step 1: Generate full circuit (regulator + LED)
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
#   Components may be close but should not:
#   - Have overlapping symbols
#   - Have overlapping text (reference designators, values)
#   - Share the exact same position

# Step 4: Check component spacing
#   - Zoom in on each component
#   - Verify readable spacing between components
#   - All reference designators should be visible (not hidden under symbols)
```

## Expected Result

- ✅ All 5 components present: C1, U1, C2, R1, D1
- ✅ No overlapping component symbols
- ✅ No overlapping text labels
- ✅ Reasonable spacing between components (at least 5.1mm default spacing)
- ✅ All reference designators visible
- ✅ Circuit is readable and professional-looking

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
