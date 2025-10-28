# Test 35: Bulk Component Remove

## What This Tests

Validates that removing multiple components from Python code correctly removes them all from the regenerated KiCad schematic, while preserving the positions of remaining components.

## When This Situation Happens

- Developer has a circuit with 10 resistors (R1-R10)
- Decides 3 components are no longer needed (R3, R5, R7)
- Removes those components from Python code
- Regenerates KiCad project to reflect the deletions
- Expects remaining 7 components to stay at their original positions

## What Should Work

- Circuit created with all 10 resistors (R1-R10)
- Python code modified to remove R3, R5, R7
- Regenerated KiCad project contains only R1, R2, R4, R6, R8, R9, R10
- Deleted components are completely removed from the schematic
- Remaining components preserve their original positions
- No orphaned connections or references to deleted components

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth2/tests/bidirectional/35_bulk_component_remove

# Step 1: Generate initial KiCad project with all 10 resistors
uv run ten_resistors_for_removal.py

# Step 2: Open KiCad and verify all 10 resistors present
open ten_resistors_for_removal/ten_resistors_for_removal.kicad_pro
# Verify: schematic has R1 (10k), R2 (4.7k), R3 (2.2k), R4 (1k), R5 (100),
#         R6 (220), R7 (470), R8 (680), R9 (1.5k), R10 (3.3k)

# Step 3: Edit ten_resistors_for_removal.py to remove R3, R5, R7
# Delete or comment out the R3, R5, R7 component definitions

# Step 4: Regenerate KiCad project (without R3, R5, R7)
uv run ten_resistors_for_removal.py

# Step 5: Open regenerated KiCad project
open ten_resistors_for_removal/ten_resistors_for_removal.kicad_pro

# Step 6: Verify R3, R5, R7 are removed and others preserved
#   - R1, R2, R4, R6, R8, R9, R10 - all present, positions preserved
#   - R3, R5, R7 - completely removed from schematic
```

## Expected Result

- ✅ Initial KiCad project has all 10 resistors
- ✅ After removing R3, R5, R7 from Python and regenerating, KiCad has only 7
- ✅ Remaining components (R1, R2, R4, R6, R8, R9, R10) positions preserved
- ✅ Deleted components (R3, R5, R7) are completely removed
- ✅ No orphaned connections or references to deleted components
- ✅ Synchronization logs show "Remove: R3", "Remove: R5", "Remove: R7"
