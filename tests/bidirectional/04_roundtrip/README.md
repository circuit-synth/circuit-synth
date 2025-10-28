# Test 04: Simple Round-Trip Cycle

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
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional/04_roundtrip

# Step 1: Generate KiCad from Python (first generation)
uv run single_resistor.py
# Creates: single_resistor/single_resistor.kicad_pro with R1

# Step 2: Import KiCad back to Python (overwrites single_resistor.py)
uv run kicad-to-python single_resistor single_resistor.py

# Step 3: Verify single_resistor.py still contains R1 component
# Component properties should be preserved from import

# Step 4: Generate KiCad again from imported Python (completes round-trip)
uv run single_resistor.py

# Step 5: Verify schematic still has R1 with same properties
#   - ref="R1"
#   - value="10k"
#   - footprint="R_0603_1608Metric"

# The same single_resistor.py file is used throughout:
#   Python → KiCad → Python (overwrites same file) → KiCad
```

## Expected Result

- ✅ Original KiCad project created with R1
- ✅ KiCad imported back to Python successfully (overwrites single_resistor.py)
- ✅ single_resistor.py contains R1 component definition after import
- ✅ Round-trip KiCad project created from same single_resistor.py
- ✅ Schematic has identical R1 component after round-trip
- ✅ No data loss through the round-trip cycle using single Python file

## Why This Is Important

Round-trip cycles test the fidelity of bidirectional sync. Users should be able to move between Python and KiCad repeatedly without losing circuit information.
