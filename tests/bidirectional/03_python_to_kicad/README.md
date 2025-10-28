# Test 03: Add Resistor in Python → Update KiCad

## What This Tests

Adding a resistor to Python code and regenerating to update existing KiCad project.

## When This Situation Happens

- User has existing KiCad project (maybe blank or with other components)
- Adds new component (R1) in Python code
- Regenerates KiCad to add new component to schematic

## What Should Work

1. Start with blank or existing circuit in Python
2. Add R1 resistor to Python code
3. Generate/regenerate KiCad
4. R1 appears in KiCad schematic
5. Other components preserved (if any)

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional/03_python_to_kicad

# Step 1: Look at Python code - has R1 defined
cat single_resistor.py

# Step 2: Generate KiCad (or regenerate if exists)
uv run single_resistor.py

# Step 3: Open in KiCad
open blank_kicad_ref/blank.kicad_pro

# Verify:
# - R1 resistor visible on schematic
# - Value is 10k
# - Footprint is 0603
```

## Expected Result

- ✅ KiCad project generated/updated
- ✅ R1 component added to schematic
- ✅ Value: 10k
- ✅ Footprint: R_0603_1608Metric
- ✅ Existing components preserved (if any)
