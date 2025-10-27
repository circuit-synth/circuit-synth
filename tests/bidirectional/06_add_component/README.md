# Test 06: Add Component to Existing Circuit

## What This Tests
Validates that adding a new component in Python code correctly appears in the regenerated KiCad schematic.

## When This Situation Happens
- Developer has an existing circuit with some components (R1)
- Needs to add a new component (R2) to the circuit
- Modifies Python code to include the new component
- Regenerates KiCad project to include the addition

## What Should Work
- Original circuit with R1 generates successfully
- Python code modified to add R2 component
- Regenerated KiCad project contains both R1 and R2
- Both components are properly represented in the schematic

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional/06_add_component

# Step 1: Generate initial KiCad project with R1
uv run single_resistor.py
open single_resistor/single_resistor.kicad_pro
# Verify: schematic has R1 only

# Step 2: Edit single_resistor.py to add R2
# Add after R1 definition:
#   r2 = Component(symbol="Device:R", ref="R2", value="4.7k",
#                  footprint="Resistor_SMD:R_0603_1608Metric")

# Step 3: Regenerate KiCad project
uv run single_resistor.py

# Step 4: Open regenerated KiCad project
open single_resistor/single_resistor.kicad_pro

# Step 5: Verify schematic has both components
#   - R1 (10k) - original component, position preserved
#   - R2 (4.7k) - new component, placed without overlapping R1
```

## Expected Result

- ✅ Initial KiCad project has R1 only
- ✅ After editing Python and regenerating, KiCad has both R1 and R2
- ✅ R1 position preserved (not moved)
- ✅ R2 placed in available space (no overlap)
- ✅ Both components have correct values
