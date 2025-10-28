# Test 24: Add Global Label for Cross-Sheet Connections

## What This Tests

**Core Question**: When you have unconnected components in a KiCad schematic and add a net with global label scope in Python code, do the global labels appear when regenerating? Can global labels enable cross-sheet connectivity for future hierarchical designs?

This tests **bidirectional sync for global label creation** - adding electrical connections via global labels (as an alternative to hierarchical labels) to establish connections that can work across sheets.

## When This Situation Happens

- Developer generates circuit with unconnected components (R1, R2)
- Later decides components should be electrically connected
- Adds `Net("GLOBAL_NET")` in Python code connecting the pins
- Marks the net for global labeling (if supported)
- Regenerates KiCad expecting global labels to appear
- Global labels enable same net name to connect components on different sheets (future feature)

## What Should Work

1. Generate initial KiCad with R1 and R2 (no connection, no labels)
2. Manually verify components are unconnected in KiCad (no labels visible)
3. Edit Python to add Net connecting R1[1] to R2[1] with global scope
4. Regenerate KiCad project
5. Global labels "GLOBAL_NET" appear on both component pins, establishing electrical connection
6. Component positions preserved during regeneration

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth2/tests/bidirectional/24_add_global_label

# Step 1: Generate initial KiCad project (no connection)
uv run two_resistors.py
open two_resistors/two_resistors.kicad_pro
# Verify: R1 and R2 visible but NO global labels (completely unconnected)

# Step 2: Edit two_resistors.py to add global label net
# Change import line to:
#   from circuit_synth import circuit, Component, Net
# Add before the end of the function (after r2 definition):
#   global_net = Net(name="GLOBAL_NET")
#   global_net += r1[1]
#   global_net += r2[1]

# Step 3: Regenerate KiCad project with connection
uv run two_resistors.py

# Step 4: Open regenerated KiCad project
open two_resistors/two_resistors.kicad_pro
# Verify:
#   - Global labels "GLOBAL_NET" now appear on R1[1] and R2[1]
#   - NO physical wire between components
#   - Electrical connection established by matching label names
#   - R1 and R2 positions preserved (didn't move)
#   - Components still no overlap
```

## Expected Result

- ✅ Initial generation: R1 and R2 unconnected (no labels)
- ✅ After adding Net in Python: global labels "GLOBAL_NET" appear
- ✅ Labels on both R1[1] and R2[1] pins (circle/globe shapes)
- ✅ NO physical wire between components
- ✅ Electrical connection established by matching label names
- ✅ Component positions preserved during regeneration
- ✅ No duplicate components
- ✅ Connection is electrically valid (no ERC errors)

**Note**: Uses `global_label` format - labels create electrical connection without wires. Global labels enable same net name to connect on different sheets (future feature).

## Why This Is Important

**Iterative circuit development workflow with hierarchical expansion:**
1. Generate initial circuit structure with components on root sheet
2. Connect components using global labels (can work same-sheet or cross-sheet)
3. Review component placement in KiCad
4. Add hierarchical sheets later with same global net names
5. Cross-sheet connections automatically established by matching label names

If this doesn't work:
- Users must use hierarchical labels (sheet-local) on same sheet
- Cannot easily transition to hierarchical designs
- Global labels are essential for future cross-sheet expansion
- Code-based design becomes less flexible

## Success Criteria

This test PASSES when:
- Unconnected components generate correctly initially (no labels)
- Adding Net() in Python creates global labels in KiCad
- Labels appear on both component pins with matching names
- NO physical wires drawn
- Component positions preserved across regeneration
- No electrical rule errors in KiCad
- Can validate presence of "global_label" in schematic file

## Validation Level

**Level 3 (Netlist Comparison)**: Validates electrical connectivity via netlist comparison
- Uses kicad-cli to export netlist
- Compares component connectivity
- Verifies R1 and R2 are electrically connected via GLOBAL_NET
- Confirms positions preserved

## Related Tests

- **Test 11** - Add hierarchical labels to same-sheet components (local scope)
- **Test 22** - Add subcircuit sheet (for future cross-sheet with global labels)
- **Test 23** - Multiple nets per component (single sheet, multiple connections)

## Design Notes

**Global labels vs. Hierarchical labels:**
- **Hierarchical labels**: Sheet-local, cannot connect across sheets
- **Global labels**: Can connect same sheet or different sheets with same name
- On single sheet: functionally identical in appearance
- In hierarchical designs: global labels enable cross-sheet connections
- KiCad visually distinguishes them (hierarchical = flag, global = circle)

## Expected Schematic Differences

**Initial (no labels):**
```
R1 ----  (unconnected)
R2 ----  (unconnected)
```

**After adding global labels:**
```
R1 --o GLOBAL_NET
R2 --o GLOBAL_NET
```

Where `o` represents global label (circle shape in KiCad).

