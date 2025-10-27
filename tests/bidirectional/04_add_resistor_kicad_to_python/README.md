# Test 04: Add Resistor in KiCad → Update Python

## What This Tests

Adding a resistor in KiCad schematic and re-importing to update existing Python code.

## When This Situation Happens

- User has Python file with circuit (e.g., main.py with R1)
- Opens KiCad project, adds another component (R2) manually
- Re-imports from KiCad to update Python code with new component
- Python code should now have both R1 and R2

## What Should Work

1. Start with Python file (main.py) that has R1 from previous import
2. Open KiCad project (kicad_ref/)
3. Add R2 resistor in KiCad schematic manually
4. Re-import to update main.py
5. Python code updated with R2 component added
6. Properties preserved (value, footprint, reference)

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional/04_add_resistor_kicad_to_python

# Step 1: Check initial Python code (has R1 from previous import)
cat main.py
# Should show R1 component

# Step 2: Open KiCad project to add R2
open kicad_ref/single_resistor.kicad_pro

# Step 3: In KiCad schematic editor:
#   - Add another resistor (R2)
#   - Set value to "4.7k"
#   - Set footprint to R_0603_1608Metric
#   - Save schematic (Cmd+S)
#   - Close KiCad

# Step 4: Re-import KiCad to update Python
uv run kicad-to-python kicad_ref/single_resistor.kicad_pro -o main.py

# Step 5: Check Python now has both resistors
cat main.py

# Should show:
# - R1 component (ref="R1", value="10k")
# - R2 component (ref="R2", value="4.7k") - NEWLY ADDED
```

## Expected Result

- ✅ Python file updated (not created fresh)
- ✅ R1 component still present
- ✅ R2 component added with correct properties
- ✅ Properties correct for both: R1 (10k), R2 (4.7k)
- ✅ Valid Python syntax
