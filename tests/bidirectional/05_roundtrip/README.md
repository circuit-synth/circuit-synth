# Test 05: Simple Round-Trip Cycle

## What This Tests

Validates that a complete round-trip cycle (Python → KiCad → Python → KiCad) preserves circuit components without loss.

## When This Situation Happens

- Developer creates circuit in Python and generates KiCad project
- Imports the KiCad project back to Python for modifications
- Regenerates KiCad from the imported Python code
- Expects the circuit to remain identical through the cycle

## What Should Work

1. Original Python circuit generates valid KiCad project with R1
2. KiCad project imports back to Python without errors
3. Imported Python code regenerates KiCad successfully
4. Round-trip KiCad project contains same component (R1)
5. Component properties preserved (ref, value, footprint)

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional/05_roundtrip

# Step 1: Generate KiCad from original Python
uv run single_resistor.py
# Creates: single_resistor/single_resistor.kicad_pro with R1

# Step 2: Import KiCad back to Python
uv run kicad-to-python single_resistor imported.py

# Step 3: Verify imported.py contains R1 component
# Open imported.py - should show R1 component definition

# Step 4: Generate KiCad from imported Python (round-trip)
uv run imported.py

# Step 5: Open both KiCad projects and compare
open single_resistor/single_resistor.kicad_pro
# Then open the project generated from imported.py

# Step 6: Verify both schematics have R1 with same properties
#   - ref="R1"
#   - value="10k"
#   - footprint="R_0603_1608Metric"
```

## Expected Result

- ✅ Original KiCad project created with R1
- ✅ KiCad imported to Python successfully (imported.py)
- ✅ imported.py contains R1 component definition
- ✅ Round-trip KiCad project created from imported.py
- ✅ Both KiCad projects have identical R1 component
- ✅ No data loss through the round-trip cycle

## Why This Is Important

Round-trip cycles test the fidelity of bidirectional sync. Users should be able to move between Python and KiCad repeatedly without losing circuit information.
