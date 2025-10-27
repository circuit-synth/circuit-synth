# Test 18: Add Component in Python, Update Existing KiCad

## What This Tests

Adding a component in Python code and regenerating to update existing KiCad project.

## When This Situation Happens

- User has existing KiCad project
- Adds new component in Python
- Wants to update KiCad schematic with new component while preserving existing work

## What Should Work

1. Start with KiCad project (has R1)
2. Import to Python
3. Add R2 in Python code
4. Regenerate KiCad - R1 and R2 both present

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional/18_add_component_update_kicad

# Step 1: Import existing KiCad with R1
uv run kicad-to-python existing_kicad/single_resistor.kicad_pro circuit.py

# Step 2: Edit circuit.py to add R2
# Add this after R1:
#     r2 = Component(
#         symbol="Device:R",
#         ref="R2",
#         value="20k",
#         footprint="Resistor_SMD:R_0603_1608Metric"
#     )

# Step 3: Regenerate KiCad
uv run circuit.py

# Step 4: Verify both R1 and R2 exist
open circuit/circuit.kicad_pro
# Should show both R1 (10k) and R2 (20k)
```

## Expected Result

- Both R1 and R2 appear in schematic
- Original R1 properties preserved
- New R2 added successfully
