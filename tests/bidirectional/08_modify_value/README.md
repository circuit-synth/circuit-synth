# Test 08: Modify Component Value

## What This Tests
Validates that changing a component's value in Python code correctly updates the value in the regenerated KiCad schematic and survives round-trip.

## When This Situation Happens
- Developer has a circuit with a resistor (R1=10k)
- Design requirements change, needs different value (R1=20k)
- Updates the value in Python code
- Regenerates KiCad and verifies value persists through import/export cycle

## What Should Work
- Original circuit has R1 with value 10k
- Python code modified to change R1 value to 20k
- Regenerated KiCad shows R1=20k
- Round-trip import back to Python preserves the 20k value

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional/08_modify_value

# Step 1: Generate initial KiCad project (R1=10k)
uv run single_resistor.py
open single_resistor/single_resistor.kicad_pro
# Verify: schematic shows R1 with value 10k

# Step 2: Edit single_resistor.py to change R1 value
# Change: value="10k" → value="20k"

# Step 3: Regenerate KiCad with modified value
uv run single_resistor.py

# Step 4: Open regenerated KiCad project
open single_resistor/single_resistor.kicad_pro
# Verify: schematic now shows R1 with value 20k, position preserved

# Step 5: Test round-trip - import back to Python
uv run kicad-to-python single_resistor imported.py
# Verify: imported.py contains R1 with value="20k"

# Step 6: Generate KiCad from imported Python (round-trip test)
uv run imported.py
# Verify: round-trip project has R1=20k
```

## Expected Result

- ✅ Initial KiCad project has R1 with value 10k
- ✅ After changing to 20k in Python and regenerating, KiCad shows R1=20k
- ✅ R1 position preserved (not moved)
- ✅ Value update is the only change
- ✅ Round-trip import preserves R1=20k
- ✅ KiCad generated from imported Python shows R1=20k
