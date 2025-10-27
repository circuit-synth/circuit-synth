# Test 19: Add Component in KiCad, Update Existing Python

## What This Tests

Adding a component in KiCad schematic and re-importing to update Python code.

## When This Situation Happens

- User has Python circuit code
- Adds component in KiCad schematic manually
- Wants to update Python code to reflect KiCad changes

## What Should Work

1. Start with Python circuit (has R1)
2. Generate KiCad
3. Add R2 in KiCad schematic manually
4. Re-import to Python - R1 and R2 both in code

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional/19_add_component_update_python

# Step 1: Generate KiCad from starting Python
uv run starting_circuit.py

# Step 2: Open KiCad and add R2 manually
open starting_circuit/starting_circuit.kicad_pro
# In KiCad: Add R2 (20k) resistor manually, save

# Step 3: Re-import to Python
uv run kicad-to-python starting_circuit/starting_circuit.kicad_pro updated_circuit.py

# Step 4: Check Python has both components
cat updated_circuit.py
# Should show both R1 and R2
```

## Expected Result

- Python code updated with both R1 and R2
- Manual KiCad changes preserved in Python import
- Component properties correct
