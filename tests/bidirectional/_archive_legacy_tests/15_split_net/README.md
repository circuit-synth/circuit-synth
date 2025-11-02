# Test 15: Split One Net Into Two by Removing Connection

## What This Tests

**Core Question**: When you have multiple components connected via a single net and remove one connection, does the netlist correctly split into two separate nets with proper electrical isolation?

This tests **bidirectional net splitting** - removing a connection from a multi-component net to create separate nets.

## When This Situation Happens

- Developer generates circuit with 3 resistors all connected via a single net (NET1: R1-R2-R3)
- Later decides to isolate one component from the group
- Removes the connection between R2 and R3 (removes R3 from NET1)
- Regenerates KiCad expecting NET1 to now connect only R1-R2, and R3 to be on a separate NET2
- Expects component positions to be preserved

## What Should Work

1. Generate initial KiCad with R1, R2, R3 all on NET1 (single net with 3 components)
2. Verify netlist shows 1 net: NET1 with all 3 component pins
3. Edit Python to remove R3 from NET1 (create separate NET2 for R3)
4. Regenerate KiCad project
5. Validate netlist shows 2 nets:
   - NET1: R1[1] and R2[1]
   - NET2: R3[1]
6. Validate component positions preserved from initial generation

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth2/tests/bidirectional/15_split_net

# Step 1: Generate initial KiCad with all three resistors on NET1
uv run three_resistors.py
open three_resistors/three_resistors.kicad_pro
# Verify: R1, R2, R3 visible with hierarchical label "NET1" on all three
# Netlist shows: NET1 with 3 pins

# Step 2: Edit three_resistors.py to split the net
# Change the net creation section to:
#   net1 = Net(name="NET1")
#   net1 += r1[1]
#   net1 += r2[1]
#
#   net2 = Net(name="NET2")
#   net2 += r3[1]

# Step 3: Regenerate KiCad project with split nets
uv run three_resistors.py

# Step 4: Open regenerated KiCad project
open three_resistors/three_resistors.kicad_pro
# Verify:
#   - Hierarchical label "NET1" appears on R1[1] and R2[1]
#   - Hierarchical label "NET2" appears on R3[1]
#   - NO physical wire between R1-R2 or to R3
#   - Electrical separation confirmed (R3 isolated from R1-R2)
#   - R1, R2, R3 positions preserved
#   - No component overlap
```

## Expected Result

- ✅ Initial generation: R1, R2, R3 all on NET1 (1 net, 3 pins)
- ✅ Netlist parsed correctly: `NET1: [('R1', '1'), ('R2', '1'), ('R3', '1')]`
- ✅ After splitting: R3 removed from NET1, placed on NET2
- ✅ Hierarchical label "NET1" on R1[1] and R2[1] only
- ✅ Hierarchical label "NET2" appears on R3[1]
- ✅ Netlist shows 2 separate nets:
  - `NET1: [('R1', '1'), ('R2', '1')]`
  - `NET2: [('R3', '1')]`
- ✅ Component positions preserved from initial generation
- ✅ No duplicate components
- ✅ Electrical isolation confirmed (no cross-connection)

## Why This Is Important

**Net management workflow:**
1. Design circuits with groups of connected components
2. Later refine connections when requirements change
3. Split nets to isolate components without losing layout
4. Verify electrical isolation through netlist validation

If this doesn't work, users cannot iteratively refine net connections or must manually edit netlists in KiCad (defeating the purpose of code-based design).

## Success Criteria

This test PASSES when:
- Initial circuit generates with all 3 resistors on single NET1
- Netlist correctly shows NET1 with 3 pins: R1[1], R2[1], R3[1]
- After splitting, NET1 has only 2 pins: R1[1], R2[1]
- After splitting, NET2 has 1 pin: R3[1]
- Component positions preserved from initial generation
- No component overlap
- Hierarchical labels correctly placed (NET1 on R1, R2; NET2 on R3)
- Level 3 validation: netlist comparison confirms electrical separation

## Level 3 Validation Details

This test uses **Level 3 (netlist comparison via kicad-cli)** validation:

1. **Schematic Structure** - kicad-sch-api validates components and labels exist
2. **Netlist Export** - kicad-cli exports netlist from KiCad schematic
3. **Netlist Parser** - Custom parser extracts net structure from both circuit-synth and KiCad netlists
4. **Electrical Verification** - Confirms netlists match (same nets with same pins)
5. **Position Validation** - Verifies component positions haven't changed between steps

This multi-step validation ensures actual electrical behavior, not just visual elements.
