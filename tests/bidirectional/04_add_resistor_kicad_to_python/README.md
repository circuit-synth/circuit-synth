# Test 04: Add Resistor in KiCad → Update Python

## What This Tests

Generating KiCad from Python, manually adding a component in KiCad, then importing back to Python to update the code.

## When This Situation Happens

- User generates KiCad project from Python code
- Opens KiCad and manually adds a component to the schematic
- Re-imports from KiCad to sync the new component back to Python
- Python code should be updated with the new component

## What Should Work

1. Generate KiCad project from Python (has R1)
2. Open KiCad, manually add R2 to schematic
3. Import KiCad back to Python
4. Python code now has both R1 and R2
5. Component properties preserved (value, footprint, reference)

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional/04_add_resistor_kicad_to_python

# Step 1: Check initial Python code (starts with R1 only)
cat main.py
# Should show single R1 component

# Step 2: Generate KiCad project from Python
uv run main.py

# Step 3: Open KiCad project
open main/main.kicad_pro

# Step 4: In KiCad schematic editor:
#   - Add another resistor (R2)
#   - Set value to "4.7k"
#   - Set footprint to R_0603_1608Metric
#   - Save schematic (Cmd+S)
#   - Close KiCad

# Step 5: Import KiCad back to Python to sync changes
uv run kicad-to-python main main.py

# Step 6: Check Python now has both resistors
cat main.py

# Should show:
# - R1 component (ref="R1", value="10k") - ORIGINAL
# - R2 component (ref="R2", value="4.7k") - NEWLY ADDED
```

## Expected Result

- ✅ KiCad project generated successfully (main/)
- ✅ R2 added manually in KiCad schematic
- ✅ Python file updated with R2 after import
- ✅ Both R1 and R2 present in Python code
- ✅ Properties correct: R1 (10k), R2 (4.7k)
- ✅ Valid Python syntax

## Why This Is Important

This tests the **KiCad → Python** direction of bidirectional sync. Users can make changes in KiCad (add components, change values, etc.) and sync those changes back to their Python code.
