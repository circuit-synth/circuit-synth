# Test 16: Add Power Symbol Connection to Component

## What This Tests

**Core Question**: When you have an unconnected component (R1) in Python and add a VCC power symbol connection, does the component properly connect to the power net when regenerating?

This tests **power symbol connectivity** - adding power rails to existing components in Python and validating that the electrical connection appears in the generated KiCad schematic.

## When This Situation Happens

- Developer generates circuit with unconnected components (R1)
- Later decides component should be powered by VCC rail
- Adds `r1[1] += Net("VCC")` in Python code
- Regenerates KiCad expecting power symbol connection to appear
- Power nets have special handling in KiCad (global connection semantics)

## What Should Work

1. Generate initial KiCad with R1 (no power connection, no labels)
2. Manually verify R1 in KiCad is unconnected (no labels on pin 1)
3. Edit Python to add VCC power symbol connection: `r1[1] += Net("VCC")`
4. Regenerate KiCad project
5. Validate VCC power symbol (or hierarchical label) appears on R1 pin 1
6. Verify netlist shows R1 pin 1 connected to VCC net (Level 3 electrical validation)
7. Validate R1 position preserved (didn't move during regeneration)

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth2/tests/bidirectional/16_add_power_symbol

# Step 1: Generate initial KiCad project (unconnected resistor)
uv run resistor_with_power.py
open resistor_with_power/resistor_with_power.kicad_pro

# Verify in KiCad:
#   - R1 visible on schematic
#   - No hierarchical labels on R1 pin 1 (completely unconnected)
#   - No power symbols connected to R1

# Step 2: Edit resistor_with_power.py to add VCC power connection
# Modify the function to uncomment the VCC net section:
#   # Uncomment these lines to add power connection:
#   # vcc = Net(name="VCC")
#   # vcc += r1[1]

# Step 3: Regenerate KiCad project with power connection
uv run resistor_with_power.py

# Step 4: Open regenerated KiCad project
open resistor_with_power/resistor_with_power.kicad_pro

# Critical verification:
#   - Hierarchical label "VCC" or power symbol now appears on R1 pin 1
#   - R1 position preserved (didn't move)
#   - No duplicate components
#   - Components still properly spaced (no overlap)
```

## Expected Result

- ✅ Initial generation: R1 unconnected (no labels)
- ✅ After adding VCC Net in Python: hierarchical label "VCC" appears on R1[1]
- ✅ R1 position preserved during regeneration
- ✅ Netlist shows R1 pin 1 connected to VCC net (Level 3 validation)
- ✅ No electrical rule errors in KiCad
- ✅ VCC is recognized as power net (global connection semantics)

**Note**: Power nets like VCC have special handling - they establish global connections without needing physical wires. The hierarchical label approach creates electrical connectivity by matching names.

## Why This Is Important

**Power connectivity in iterative circuit development:**
1. Generate component structure (R1)
2. Review placement in KiCad
3. Add power connections in Python (VCC, GND nets)
4. Regenerate - hierarchical labels appear, establishing connections without losing layout

If this doesn't work:
- Users must define all power connections upfront
- Can't add power connections during iterative refinement
- Manual KiCad editing required after each regeneration
- Power symbols don't reflect Python intent

## Success Criteria

This test PASSES when:
- Unconnected component generates correctly initially (no labels)
- Adding Net("VCC") in Python creates hierarchical label in KiCad
- Label appears on component pin with name "VCC"
- Component position preserved across regeneration
- Netlist validation (kicad-cli) confirms electrical connectivity
- No electrical rule errors in KiCad
- Power net recognized as special (global connection)

## Critical Differences: Power Symbols vs Hierarchical Labels

**Circuit-synth approach (hierarchical labels):**
- Generates text labels with names like "VCC", "GND"
- Local to hierarchy - needs matching label names
- Connection by name within scope
- Standard circuit-synth approach for all nets

**KiCad power symbols approach:**
- Actual symbol icons (⏚ ground, +V arrows, etc.)
- Global/universal connection across entire project
- Semantic meaning: this is a power rail
- What experienced KiCad users prefer

Both should work electrically, but power symbols are more "correct" KiCad style for power nets.

## Automated Test Validation

The automated test (`test_16_add_power_symbol.py`) validates:

**Level 1 - File generation:**
- ✅ Initial circuit generates without errors
- ✅ Schematic file created

**Level 2 - Schematic structure:**
- ✅ Components present (R1)
- ✅ Initially: no hierarchical labels
- ✅ After power connection: labels appear

**Level 3 - Electrical validation:**
- ✅ kicad-cli netlist export succeeds
- ✅ Netlist parsing shows VCC net
- ✅ R1 pin 1 connected to VCC
- ✅ Position preserved

**Level 4 - Integration:**
- ✅ Round-trip consistency
- ✅ No ERC errors generated

## Related Tests

- **Test 09** - Position preservation (reference pattern)
- **Test 11** - Add net to components (pattern for net operations)
- **Test 26** - Power symbol replacement (power symbol handling)

## Implementation Notes

**Fixture strategy:**
- Start with single resistor (R1)
- Initially unconnected (no power net in code)
- Python code shows VCC net in commented section
- Test uncomments it to add connection

**Validation approach:**
- Parse netlist using regex (similar to test 11)
- Extract net connections
- Verify R1 pin 1 in VCC net
- Compare positions before/after

**Power net handling:**
- VCC is a known power net name
- Should generate hierarchical label (circuit-synth standard)
- KiCad recognizes as power by context
- Global connection semantics for all VCC references
