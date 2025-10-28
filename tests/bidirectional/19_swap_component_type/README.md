# Test 27: Swap Component Type (Resistor → Capacitor)

## What This Tests

**Core Question**: When you change a component's symbol type in Python code (Device:R → Device:C) while keeping the same reference (R1), does the regenerated KiCad schematic show the new component type while preserving position and reference?

This validates **symbol type changes during iterative design** - a common scenario when refining circuit behavior.

## When This Situation Happens

- Developer creates R1 (resistor) in Python and generates KiCad
- Manually positions it and routes connections
- Later decides R1 should be a capacitor for filtering instead
- Changes Python from `Device:R` to `Device:C` but keeps reference as "R1"
- Regenerates KiCad expecting:
  - Capacitor symbol shown (not resistor)
  - Position preserved
  - Reference still "R1"
  - UUID-based matching preserves the component

## What Should Work

1. Generate KiCad with R1 (resistor) at default position
2. Manually move R1 to specific position (100, 50)
3. Change Python symbol from Device:R to Device:C, keep reference "R1"
4. Regenerate KiCad project
5. Validate:
   - KiCad shows capacitor symbol (not resistor)
   - Reference still "R1" (not changed)
   - Position preserved at (100, 50)
   - UUID-based matching worked (single component, not Remove+Add)

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth2/tests/bidirectional/27_swap_component_type

# Step 1: Generate initial KiCad project with R1 (resistor)
uv run single_resistor.py
open single_resistor/single_resistor.kicad_pro
# Verify: schematic shows resistor symbol labeled R1

# Step 2: Manually move R1 to specific position in KiCad
# - Select R1 component
# - Drag to position (e.g., center of page)
# - Save schematic (Cmd+S)

# Step 3: Edit single_resistor.py to change component type
# Change from:
#   symbol="Device:R"  (resistor)
# To:
#   symbol="Device:C"  (capacitor)
# Keep reference as "R1"

# Step 4: Regenerate KiCad from modified Python
uv run single_resistor.py

# Step 5: Open regenerated KiCad project and verify
open single_resistor/single_resistor.kicad_pro
# Verify:
#   - Capacitor symbol shown (not resistor) ✓
#   - Reference still "R1" ✓
#   - Position preserved (where you moved it) ✓
#   - Single component (UUID matching worked) ✓
```

## Expected Result

- ✅ Initial circuit created with R1 (Device:R - resistor)
- ✅ R1 manually moved to position (100, 50)
- ✅ Component symbol changed to Device:C (capacitor) in Python
- ✅ Regenerated KiCad shows capacitor symbol (not resistor)
- ✅ Reference still "R1" (unchanged)
- ✅ Position preserved at (100, 50) - UUID matching worked
- ✅ Single component (no Remove/Add, just symbol change)
- ✅ Symbol change successful through bidirectional sync

## Why This Is Important

**Common design iteration:**
- Prototyping with multiple component choices
- Changing component type during refinement
- Swapping resistor ↔ capacitor for filtering/timing
- Trying different component families

**If symbol type changes DON'T work:**
- Developer forced to delete and re-add components
- All position information lost
- All connections must be re-created
- Very tedious workflow

**If symbol type changes DO work:**
- Change symbol in Python
- Position and connections preserved
- UUID matching handles identity
- Smooth design iteration

## Success Criteria

This test PASSES when:
- KiCad schematic shows capacitor symbol (not resistor)
- Reference is still "R1" (not changed)
- Position preserved at (100, 50)
- UUID is unchanged (same component, not Remove+Add)
- Sync output shows single Update (or similar), not Remove/Add pair
- No electrical rule errors in KiCad

## Validation Level

**Level 2 Semantic Validation** using kicad-sch-api:
- Verify component.symbol property shows "C" (capacitor)
- Verify component.reference is "R1"
- Verify component.position at (100, 50)
- Verify component.uuid unchanged

No electrical connectivity test needed - focus is on symbol type and identity preservation.

## Related Tests

- **Test 13** - Component rename (reference change with UUID matching)
- **Test 09** - Position preservation (position preservation during regeneration)
- **Test 08** - Value modification (property change on same component)

## Related Issues

- Symbol type changes during design iteration
- UUID-based matching for component identity
- Position preservation during symbol changes
