# Test 13: Component Rename Consistency

## What This Tests

Validates that renaming a component in KiCad maintains consistency when imported back to Python and used in further development.

## When This Situation Happens

- Developer creates R1 in Python and generates KiCad
- Opens in KiCad and renames R1 to R_PULLUP for better clarity
- Imports modified KiCad back to Python
- Adds connections using the renamed reference
- Regenerates KiCad and expects consistency across tools

## What Should Work

- Initial circuit with R1 generates successfully
- KiCad component renamed from R1 to R_PULLUP (simulated)
- Reimport to Python recognizes the new reference name
- Python code can use R_PULLUP reference for connections
- Regenerated KiCad maintains the renamed reference consistently

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional/13_rename_component

# Step 1: Generate initial KiCad project with R1
uv run single_resistor.py
# Creates: single_resistor/single_resistor.kicad_pro with R1

# Step 2: Open KiCad and rename R1 to R_PULLUP
open single_resistor/single_resistor.kicad_pro
# In KiCad schematic editor:
#   - Select R1 component
#   - Edit properties, change reference from "R1" to "R_PULLUP"
#   - Save schematic

# Step 3: Import modified KiCad back to Python
uv run kicad-to-python single_resistor imported.py

# Step 4: Verify imported.py contains R_PULLUP
# Open imported.py - should show component with ref="R_PULLUP"

# Step 5: Add connections using renamed reference
# Edit imported.py to add another component and connection:
#   - Add R2 component
#   - Connect R_PULLUP to R2
# The code should reference R_PULLUP (not R1)

# Step 6: Regenerate KiCad from modified Python
uv run imported.py

# Step 7: Open regenerated KiCad project
# Verify:
#   - Component still named R_PULLUP (not reverted to R1)
#   - New component R2 present
#   - Connection between R_PULLUP and R2 exists
#   - Naming consistency maintained through cycle
```

## Expected Result

- ✅ Original circuit created with R1
- ✅ Component successfully renamed to R_PULLUP in KiCad
- ✅ Imported Python (imported.py) contains R_PULLUP reference
- ✅ Python code can use R_PULLUP for new connections
- ✅ Regenerated KiCad maintains R_PULLUP name (no reversion to R1)
- ✅ Naming consistency maintained through complete cycle

## Why This Is Important

Component renaming in KiCad for clarity and meaning is common practice. The bidirectional sync must preserve user-chosen names through import/export cycles, not revert to original programmatic names.
