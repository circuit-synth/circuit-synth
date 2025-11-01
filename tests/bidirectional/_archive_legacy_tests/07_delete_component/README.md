# Test 07: Delete Component from Circuit

## What This Tests
Validates that removing a component from Python code correctly removes it from the regenerated KiCad schematic.

## When This Situation Happens
- Developer has a circuit with multiple components (R1 and R2)
- Decides a component is no longer needed (R2)
- Removes the component from Python code
- Regenerates KiCad project to reflect the deletion

## What Should Work
- Circuit created with both R1 and R2
- Python code modified to remove R2
- Regenerated KiCad project contains only R1
- R2 is completely removed from the schematic

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional/07_delete_component

# Step 1: Generate initial KiCad project with both R1 and R2
uv run two_resistors.py

# Step 2: Open KiCad and verify both resistors present
open two_resistors/two_resistors.kicad_pro
# Verify: schematic has both R1 (10k) and R2 (4.7k)

# Step 3: Edit two_resistors.py to remove R2
# Delete or comment out the R2 component definition:
#   r2 = Component(...)

# Step 4: Regenerate KiCad project (without R2)
uv run two_resistors.py

# Step 5: Open regenerated KiCad project
open two_resistors/two_resistors.kicad_pro

# Step 6: Verify R2 is removed from schematic
#   - R1 (10k) - still present, position preserved
#   - R2 - completely removed from schematic
```

## Expected Result

- ✅ Initial KiCad project has both R1 and R2
- ✅ After removing R2 from Python and regenerating, KiCad has only R1
- ✅ R1 position preserved (not moved)
- ✅ R2 is completely removed from the schematic
- ✅ No orphaned connections or references to R2
