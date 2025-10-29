# Test 38: Empty Subcircuit

## What This Tests

**Core Question**: When you create a hierarchical circuit with an empty subcircuit (no components), does KiCad generation handle the empty sheet correctly? And can you add components to the empty sheet and regenerate?

This tests **empty hierarchical sheet handling** - creating a child sheet that contains no components initially, then dynamically adding components to it.

## When This Situation Happens

- Developer creates hierarchical circuit structure (organization) before adding components
- Some subsystems are initially placeholders (empty subcircuits)
- Components are added to subcircuits iteratively during development
- Need to verify empty sheets don't break KiCad generation and can be populated later

## What Should Work

1. Generate KiCad with R1 on root sheet and empty Subcircuit
2. Verify root sheet contains R1
3. Verify subcircuit sheet exists but has no components
4. Edit Python to add R2 to empty subcircuit
5. Regenerate KiCad project
6. Verify R2 now exists in subcircuit
7. Edit Python to remove R2 from subcircuit
8. Regenerate
9. Verify subcircuit is empty again

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth2/tests/bidirectional/38_empty_subcircuit

# Step 1: Generate initial KiCad project (R1 on root, empty subcircuit)
uv run empty_subcircuit.py
open empty_subcircuit/empty_subcircuit.kicad_pro
# Verify: Root sheet has R1
# Verify: Subcircuit sheet exists but is empty

# Step 2: Edit empty_subcircuit.py to add R2 to subcircuit
# Uncomment or add:
#   r2 = Component(symbol="Device:R", ref="R2", value="4.7k",
#                  footprint="Resistor_SMD:R_0603_1608Metric")
#   subcircuit.add_component(r2)

# Step 3: Regenerate KiCad project
uv run empty_subcircuit.py

# Step 4: Open regenerated KiCad project
open empty_subcircuit/empty_subcircuit.kicad_pro
# Verify:
#   - Root sheet still has R1
#   - Subcircuit sheet now contains R2
#   - Both sheets have correct components

# Step 5: Edit empty_subcircuit.py to remove R2 from subcircuit
# Comment out or remove:
#   r2 = Component(...)
#   subcircuit.add_component(r2)

# Step 6: Regenerate KiCad project
uv run empty_subcircuit.py

# Step 7: Open regenerated KiCad project
open empty_subcircuit/empty_subcircuit.kicad_pro
# Verify:
#   - Root sheet still has R1
#   - Subcircuit sheet is now empty again
```

## Expected Result

- ✅ Initial generation: Root sheet has R1, subcircuit sheet exists but empty
- ✅ After adding R2 to subcircuit: R2 appears in subcircuit
- ✅ After removing R2: Subcircuit becomes empty again
- ✅ Root sheet R1 preserved across all regenerations
- ✅ No errors during any generation
- ✅ No ERC errors in KiCad project
- ✅ Empty sheets handled gracefully without breaking project

## Why This Is Important

**Edge case handling for hierarchical design:**
1. Developers may create hierarchical structure (empty subsystems) before populating
2. Empty sheets should not cause errors or corruption
3. Dynamic component addition/removal to subcircuits must work reliably
4. Organization structure should be separable from component content

If this doesn't work, users cannot:
- Create project structure before implementation
- Dynamically populate subsystems
- Keep empty placeholder sheets in complex projects
- Refactor circuits without regenerating from scratch

## Success Criteria

This test PASSES when:
- Root sheet is generated with R1
- Empty subcircuit sheet is created without error
- Subcircuit sheet has zero components
- Adding R2 to subcircuit creates it in the sheet
- Removing R2 makes subcircuit empty again
- Root sheet R1 position preserved across all regenerations
- No error messages during any generation
- No ERC errors in KiCad project
- KiCad project remains valid after each generation

## Validation Level

**Level 2 (kicad-sch-api)**: Validates schematic structure using kicad-sch-api library
- Checks that schematic files exist
- Verifies component presence/absence on sheets
- Confirms hierarchy relationship
- Validates empty sheet handling

## Notes

- This tests the edge case of empty hierarchical sheets
- Simplified hierarchical structure (no cross-sheet connections)
- Uses Circuit.add_subcircuit() API for organization
- Each subcircuit becomes a separate .kicad_sch file in KiCad
- Emphasizes dynamic component addition/removal capability
