# Test 35: Bulk Component Remove (Python Loop Advantage)

## What This Tests

Validates that removing multiple components using Python loops correctly removes them all from the regenerated KiCad schematic, while preserving the positions of remaining components.

**Python Loop Advantage:** Change ONE number instead of manually deleting 5 component definitions!

## When This Situation Happens

- Developer has a circuit with 10 resistors (R1-R10) with varying values
- Decides 5 components are no longer needed (R6-R10)
- Changes loop range from `range(1, 11)` to `range(1, 6)` in Python
- Regenerates KiCad project to reflect the deletions
- Expects remaining 5 components (R1-R5) to stay at their original positions

## What Should Work

- Circuit created with all 10 resistors (R1-R10) using Python loop
- Python code modified: `range(1, 11)` → `range(1, 6)` removes R6-R10
- Regenerated KiCad project contains only R1-R5
- Deleted components (R6-R10) are completely removed from the schematic
- Remaining components (R1-R5) preserve their original positions
- No orphaned connections or references to deleted components

**Python Advantage:** Changed ONE number (11 → 6) instead of deleting 5 component definitions (25 lines of code)!

## Manual Test Instructions

```bash
cd tests/bidirectional/35_bulk_component_remove

# Step 1: Generate initial KiCad project with all 10 resistors
uv run ten_resistors_for_removal.py

# Step 2: Open KiCad and verify all 10 resistors present
open ten_resistors_for_removal/ten_resistors_for_removal.kicad_pro
# Verify: schematic has R1 (10k), R2 (4.7k), R3 (2.2k), R4 (1k), R5 (100),
#         R6 (220), R7 (470), R8 (680), R9 (1.5k), R10 (3.3k)

# Step 3: Edit ten_resistors_for_removal.py to remove R6-R10
# Change: for i in range(1, 11):  # Original - creates R1-R10
#      to: for i in range(1, 6):   # Modified - creates only R1-R5
# This demonstrates the Python loop advantage!

# Step 4: Regenerate KiCad project (without R6-R10)
uv run ten_resistors_for_removal.py

# Step 5: Open regenerated KiCad project
open ten_resistors_for_removal/ten_resistors_for_removal.kicad_pro

# Step 6: Verify R6-R10 are removed and R1-R5 preserved
#   - R1, R2, R3, R4, R5 - all present, positions preserved
#   - R6, R7, R8, R9, R10 - completely removed from schematic
#   - Check synchronization logs for "Remove: R6, R7, R8, R9, R10"
```

## Expected Result

- ✅ Initial KiCad project has all 10 resistors (R1-R10)
- ✅ After changing `range(1, 11)` to `range(1, 6)`, KiCad has only 5 resistors
- ✅ Remaining components (R1-R5) positions preserved
- ✅ Deleted components (R6-R10) are completely removed
- ✅ No orphaned connections or references to deleted components
- ✅ Synchronization logs show "Remove: R6, R7, R8, R9, R10"

**Python Loop Advantage:**
- Changed ONE number (11 → 6) instead of deleting 5 component definitions
- 1 character change vs. deleting 25 lines of code
- This is the power of circuit-synth!
