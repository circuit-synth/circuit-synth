# Test 36: Copy-Paste Component

## What This Tests
Validates that duplicating components in Python code (copy-paste pattern) preserves electrical connectivity and correctly generates in KiCad schematic. Tests the component duplication workflow with proper net management.

## When This Situation Happens
- Developer has an existing circuit with components and nets (e.g., R1-R2 resistor divider)
- Needs to duplicate the entire component group (copy-paste pattern)
- Creates new component instances with similar connectivity patterns
- Regenerates KiCad project with all components and nets intact

## What Should Work
- Initial circuit with R1-R2 divider and 3 nets (VCC, junction, GND)
- Python code modified to add R3-R4 as copies of R1-R2
- New nets created to mirror the R1-R2 connectivity pattern
- Regenerated KiCad project contains all 4 resistors
- Both divider chains have correct electrical connectivity (Level 3 netlist validation)
- Net names and component references are unique

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth2/tests/bidirectional/36_copy_paste_component

# Step 1: Generate initial KiCad project with R1-R2 divider
uv run resistor_divider_for_copy.py
open resistor_divider_for_copy/resistor_divider_for_copy.kicad_pro
# Verify: schematic has R1 and R2 in series with nets: VCC, Net1, GND

# Step 2: Edit resistor_divider_for_copy.py to add R3-R4 as copies
# Add after R2 definition:
#   r3 = Component(symbol="Device:R", ref="R3", value="10k",
#                  footprint="Resistor_SMD:R_0603_1608Metric")
#   r4 = Component(symbol="Device:R", ref="R4", value="10k",
#                  footprint="Resistor_SMD:R_0603_1608Metric")
#   net4 = Net(name="VCC_copy")
#   net4 += r3[1]
#   net5 = Net(name="Net2")
#   net5 += r3[2]
#   net5 += r4[1]
#   net6 = Net(name="GND_copy")
#   net6 += r4[2]

# Step 3: Regenerate KiCad project
uv run resistor_divider_for_copy.py

# Step 4: Open regenerated KiCad project
open resistor_divider_for_copy/resistor_divider_for_copy.kicad_pro

# Step 5: Verify schematic has all components
#   - R1 (10k) - original component, position preserved
#   - R2 (10k) - original component, position preserved
#   - R3 (10k) - new copy, placed without overlapping
#   - R4 (10k) - new copy, placed without overlapping
#   - All nets present: VCC, Net1, GND, VCC_copy, Net2, GND_copy
```

## Expected Result

- ✅ Initial KiCad project has R1-R2 divider only (2 components, 3 nets)
- ✅ After editing Python and regenerating, KiCad has 4 resistors
- ✅ R1-R2 positions preserved (not moved)
- ✅ R3-R4 placed in available space (no overlap)
- ✅ All 4 components have correct values (10k)
- ✅ All 6 nets present: VCC, Net1, GND, VCC_copy, Net2, GND_copy
- ✅ Netlist validation shows correct electrical connectivity for both dividers
- ✅ No unconnected pins (Level 3 netlist validation)
