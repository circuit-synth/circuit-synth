# Test 18: Add Component in Python, Update Existing KiCad

## What This Tests
Adding a component in Python code and regenerating to update existing KiCad project.

## When This Situation Happens
- User has existing KiCad project
- Adds new component in Python
- Wants to update KiCad schematic with new component while preserving existing work

## What Should Work
- Start with KiCad project (has R1)
- Import to Python
- Add R2 in Python code
- Regenerate KiCad - R1 and R2 both present

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional/18_add_component_update_kicad

# Step 1: Generate initial KiCad project with R1
uv run single_resistor.py
open single_resistor/single_resistor.kicad_pro
# Verify: schematic has R1 only

# Step 2: Edit single_resistor.py to add R2
# Add after r1 definition:
#   r2 = Component(
#       symbol="Device:R",
#       ref="R2",
#       value="20k",
#       footprint="Resistor_SMD:R_0603_1608Metric",
#   )

# Step 3: Regenerate KiCad project
uv run single_resistor.py

# Step 4: Open and verify both components exist
open single_resistor/single_resistor.kicad_pro
# Verify: both R1 (10k) and R2 (20k) present in schematic
```

## Expected Result

- ✅ Both R1 and R2 appear in schematic
- ✅ Original R1 properties preserved
- ✅ New R2 added successfully with correct value
