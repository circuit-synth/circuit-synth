# Test 38: Empty Subcircuit

## What This Tests

**Core Question**: When you generate a hierarchical circuit with an empty subcircuit (no components), does KiCad handle the empty sheet correctly? Can you then add components in Python and sync to KiCad?

This tests **empty hierarchical sheet handling** - generating an empty child sheet, then syncing component additions from Python to KiCad.

## When This Situation Happens

- Developer generates hierarchical circuit structure (organization) before adding components
- Some subsystems are initially placeholders (empty subcircuits)
- Components are added to subcircuits iteratively in Python
- Need to verify empty sheets don't break KiCad generation and sync correctly when populated

## What Should Work

1. **Generate** KiCad from Python with R1 on root sheet and empty subcircuit
2. Verify root sheet contains R1
3. Verify subcircuit sheet exists but has no components
4. Edit Python to add R2 to empty subcircuit
5. **Sync** Python→KiCad (regenerate, preserving positions)
6. Verify R2 now exists in subcircuit
7. Edit Python to remove R2 from subcircuit
8. **Sync** Python→KiCad again
9. Verify subcircuit is empty again

## Manual Test Instructions

```bash
cd tests/bidirectional/38_empty_subcircuit

# Step 1: Generate initial KiCad project (R1 on root, empty subcircuit)
uv run empty_subcircuit.py
open empty_subcircuit/empty_subcircuit.kicad_pro
# Verify: Root sheet has R1
# Verify: Child sheet "placeholder_subcircuit_1" exists but is empty

# Step 2: Edit Python to add R2 to subcircuit
# In empty_subcircuit.py, in the placeholder_subcircuit() function,
# uncomment the R2 component (lines 23-28):
#   Change from:
#     # r2 = Component(
#     #     symbol="Device:R",
#   To:
#     r2 = Component(
#         symbol="Device:R",

# Step 3: Sync Python→KiCad (regenerate)
uv run empty_subcircuit.py

# Step 4: Verify R2 synced to KiCad
open empty_subcircuit/empty_subcircuit.kicad_pro
# Verify:
#   - Root sheet still has R1 (position preserved)
#   - Child sheet "placeholder_subcircuit_1" now contains R2
#   - R1 position unchanged (sync preserved existing component)

# Step 5: Edit Python to remove R2 from subcircuit
# Re-comment the R2 component (lines 23-28)

# Step 6: Sync Python→KiCad again
uv run empty_subcircuit.py

# Step 7: Verify subcircuit is empty again
open empty_subcircuit/empty_subcircuit.kicad_pro
# Verify:
#   - Root sheet still has R1 (position preserved)
#   - Child sheet "placeholder_subcircuit_1" is empty again
#   - Sheet symbol remains on root sheet
```

## Expected Result

- ✅ Initial generation: Root sheet has R1, subcircuit sheet exists but empty
- ✅ After adding R2 in Python and syncing: R2 appears in KiCad subcircuit
- ✅ After removing R2 in Python and syncing: Subcircuit becomes empty again in KiCad
- ✅ Root sheet R1 position preserved across all syncs
- ✅ No errors during generation or sync
- ✅ No ERC errors in KiCad project
- ✅ Empty sheets handled gracefully without breaking project

## Why This Is Important

**Edge case handling for hierarchical design:**
1. Developers may generate hierarchical structure (empty subsystems) before populating
2. Empty sheets should not cause errors or corruption during generation
3. Dynamic component addition/removal in Python must sync reliably to KiCad
4. Organization structure should be separable from component content

If this doesn't work, users cannot:
- Generate project structure before implementation
- Dynamically populate subsystems and sync to KiCad
- Keep empty placeholder sheets in complex projects
- Add/remove components from subcircuits iteratively

## Success Criteria

This test PASSES when:
- Root sheet is generated with R1
- Empty subcircuit sheet is generated without error
- Subcircuit sheet has zero components initially
- Adding R2 in Python and syncing creates it in KiCad subcircuit
- Removing R2 in Python and syncing makes subcircuit empty again in KiCad
- Root sheet R1 position preserved across all syncs
- No error messages during generation or sync
- No ERC errors in KiCad project
- KiCad project remains valid after each sync operation

## Validation Level

**Level 2 (kicad-sch-api)**: Validates schematic structure using kicad-sch-api library
- Checks that schematic files exist
- Verifies component presence/absence on sheets
- Confirms hierarchy relationship
- Validates empty sheet handling

## Notes

- This tests the edge case of empty hierarchical sheets
- Tests Python→KiCad sync workflow specifically
- Simplified hierarchical structure (no cross-sheet connections)
- Uses modern @circuit decorator syntax
- Two circuit functions: main() (parent) and placeholder_subcircuit() (child)
- Calling placeholder_subcircuit() generates hierarchical sheet symbol on parent
- Each subcircuit becomes a separate .kicad_sch file (placeholder_subcircuit_1.kicad_sch)
- Emphasizes dynamic component addition/removal in Python syncing to KiCad
