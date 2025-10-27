# Test 04: Add Resistor in KiCad → Update Python

## What This Tests

Adding a resistor in KiCad schematic and importing to update Python code.

## When This Situation Happens

- User has KiCad project (generated from Python or created manually)
- Adds component (R1) in KiCad schematic
- Re-imports to Python to update code with new component

## What Should Work

1. Start with KiCad project (with or without components)
2. Add R1 resistor in KiCad schematic manually
3. Import to Python
4. Python code updated with R1 component
5. Properties preserved (value, footprint, reference)

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional/04_add_resistor_kicad_to_python

# Step 1: Open existing KiCad project (already has R1)
open kicad_ref/single_resistor.kicad_pro

# Step 2: Import KiCad to Python
uv run kicad-to-python kicad_ref/single_resistor.kicad_pro -o imported_circuit.py

# Step 3: Check Python has R1
cat imported_circuit.py

# Should show:
# - Component with ref="R1"
# - value="10k"
# - footprint for 0603 resistor
```

## Expected Result

- ✅ Python file created/updated
- ✅ R1 component in Python code
- ✅ Properties correct: ref=R1, value=10k, footprint=R_0603_1608Metric
- ✅ Valid Python syntax
