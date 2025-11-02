# Test 25: Add Local Label for Net Naming

## What This Tests

**Core Question**: When you create a net connecting components on the same sheet and assign a meaningful name, does circuit-synth generate a local label in the schematic that makes the net name visible and readable within the sheet?

This tests **local label creation for readable net naming within a single sheet** - validating that nets get proper hierarchical labels that establish electrical connectivity and improve schematic readability.

## When This Situation Happens

- Developer creates a circuit with multiple components on one sheet
- Developer names a net with a descriptive name (e.g., "DATA_LINE", "CLOCK", "RESET")
- Developer expects to see that net name as a label in the schematic
- Regenerates KiCad expecting readable net labels
- **Critical**: Do local labels appear with the correct net name?

## What Should Work

1. Generate initial KiCad with R1 and R2 on the same sheet (unconnected)
2. Verify no labels in schematic (components are unconnected)
3. Modify Python to create Net("DATA_LINE") connecting R1 and R2
4. Regenerate KiCad project
5. Local labels appear in schematic with name "DATA_LINE"
6. Netlist shows R1 and R2 connected on net "DATA_LINE"
7. Component positions preserved (not moved during regeneration)

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional/25_add_local_label

# Step 1: Generate initial KiCad project (unconnected resistors)
uv run two_resistors.py
open two_resistors/two_resistors.kicad_pro
# Verify: R1 and R2 visible but NO labels (completely unconnected)

# Step 2: Edit two_resistors.py to add local label
# Change imports to:
#   from circuit_synth import circuit, Component, Net
# Add before the end of the function:
#   data_line = Net(name="DATA_LINE")
#   data_line += r1[1]
#   data_line += r2[1]

# Step 3: Regenerate KiCad project with label
uv run two_resistors.py

# Step 4: Open regenerated KiCad project
open two_resistors/two_resistors.kicad_pro
# Verify:
#   - Hierarchical labels "DATA_LINE" appear on both pins
#   - Labels establish electrical connection (no physical wire needed)
#   - R1 and R2 positions preserved (didn't move)
#   - Schematic is more readable with named net
#   - No overlap between components
```

## Expected Result

- ✅ Initial generation: R1 and R2 unconnected (no labels)
- ✅ After adding local label: hierarchical labels "DATA_LINE" appear
- ✅ Labels on both R1[1] and R2[1] pins (square flag shapes)
- ✅ NO physical wire between components
- ✅ Electrical connection established by matching label names
- ✅ Component positions preserved during regeneration
- ✅ No duplicate components
- ✅ Connection is electrically valid (netlist shows correct net name)
- ✅ Schematic is readable with meaningful net name

## Why This Is Important

**Hierarchical labels vs physical wires:**

Physical wires are NOT required for electrical connections in KiCad. Instead, you can use hierarchical labels (sheet labels) with matching names to establish connections. This is cleaner and more scalable:

```
Bad approach (physical wire):  [R1]--wire--[R2]
                              (clutters schematic)

Good approach (hierarchical label):
                               [R1] DATA_LINE flag
                               [R2] DATA_LINE flag
                              (clean, readable, electrical connection via name match)
```

**Readable circuit documentation:**

When developers look at a KiCad schematic, net names appear as labels on the schematic. A net named "DATA_LINE" with a label makes the circuit self-documenting:
- Where does DATA_LINE connect? Look for the label
- What is this net for? The name tells you (DATA = data signal, LINE = transmission)
- No need to open netlist to understand connections

**Local scope within single sheet:**

"Local labels" are hierarchical labels that establish connections within a single sheet. This is different from:
- **Power/Ground symbols** - Global symbols that connect across all sheets
- **Connector labels** - Sheet-to-sheet connections via hierarchical sheets

Within a single sheet, local hierarchical labels are the way to create readable, meaningful net names.

## Iterative Development Example

```
Circuit Evolution:
1. Start with unconnected components
   - uv run two_resistors.py
   - R1 and R2 in schematic, no connection

2. Decide they should connect
   - Add Net("DATA_LINE") in Python
   - uv run two_resistors.py
   - Labels appear, circuit documented with net name

3. Layout looks good
   - No need to move components manually
   - Positions were preserved from step 1

Result: Clean, readable, documented circuit with minimal effort
```

## Success Criteria

This test PASSES when:

- Unconnected components generate correctly initially (no labels)
- Adding local label Net() in Python creates hierarchical labels in KiCad
- Labels appear on both component pins with the net name
- NO physical wires drawn
- Component positions preserved across regeneration
- Netlist comparison shows correct net name and connectivity
- No electrical rule errors in KiCad

## Validation Approach

**Level 3 Validation** (full electrical validation):

1. **Schematic structure** - kicad-sch-api validates label presence and position
2. **Netlist comparison** - kicad-cli exports netlist, verify:
   - Net name matches (e.g., "DATA_LINE")
   - Both R1 and R2 pins are on the net
   - No unconnected pins
   - No extra unconnected nets

## Related Tests

- **Test 10** - Generate with net (creates net on first generation)
- **Test 11** - Add net to existing unconnected components (similar, but different workflow)
- **Test 20** - Change pin on net (modify existing net connection)
- **Test 18** - Rename net (change net name)

## Edge Cases

After this basic test works, validate:

1. **Net name special characters** - "DATA_LINE", "CLK_n", "VCC_3V3"
2. **Multiple local labels on same net** - More than 2 components on one net
3. **Mixed label types** - Local labels + power symbols
4. **Long net names** - "DATA_TRANSMISSION_LINE" (label placement)
5. **Component value changes** - Modify component while label exists
6. **Position preservation** - Label addition doesn't move components

## Comparison: Local Label vs Power Symbol

| Aspect | Local Label | Power Symbol |
|--------|-------------|--------------|
| Scope | Single sheet only | Global (all sheets) |
| Net name | User-defined ("DATA_LINE") | Standard ("VCC", "GND") |
| Use case | Signal naming | Power distribution |
| Typical example | DATA_LINE, CLOCK, RESET | VCC, GND, 3V3 |

This test focuses on local labels for user-defined signal names within a sheet.

## Debug Path

**If this test fails, investigate:**

1. Are labels attempted but missing? (execution issue)
2. Are labels created with wrong name? (name mapping issue)
3. Are labels created on wrong pins? (pin selection issue)
4. Are positions moved? (placement algorithm interference)
5. Does two-step process work? (add net without label, then add label)
6. Is it a hierarchical_label vs label distinction? (KiCad label type issue)

Check schematic file with: `grep -i "DATA_LINE" two_resistors/two_resistors.kicad_sch`
