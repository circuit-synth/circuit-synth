# Test 27: Add Junction (Connection Dot) on T-Connection

## What This Tests

**Core Question**: When you have a T-connection (three nets meeting at one point: R2's pin splits to connect both R1 and R3), does KiCad properly add junction dots at the connection point to clarify electrical connections?

This tests **junction placement validation** - ensuring connection dots (junctions) appear where multiple nets meet at a single point.

## When This Situation Happens

- Developer generates circuit with three resistors in a T-connection configuration
- One resistor (R2) has its pin connected to both R1 and R3 pins at a single point
- KiCad should automatically add a junction (small dot) at the connection point
- Later developer modifies circuit to remove junction or change connection topology
- Regenerates expecting junction count to change correctly

## What Should Work

1. Generate initial KiCad with R1-R2-R3 in T-connection (three nets meet at one point)
2. Verify junction exists at connection point (search for `(junction` in .kicad_sch)
3. Modify Python to create Y-connection instead (separate nets, no junction needed)
4. Regenerate KiCad project
5. Validate junction count changed correctly
6. Validate component positions preserved

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth2/tests/bidirectional/27_add_junction

# Step 1: Generate initial KiCad with T-connection (junction needed)
uv run three_resistors.py
open three_resistors/three_resistors.kicad_pro
# Verify: R1, R2, R3 visible with junction dot at connection point
# Schematic shows clear connection topology with visual junction

# Step 2: Search schematic for junction elements
grep "(junction" three_resistors/three_resistors.kicad_sch
# Should see at least 1 junction element

# Step 3: Edit three_resistors.py to create Y-connection
# Change the net connection section to:
#   net1 = Net(name="NET1")
#   net1 += r1[1]
#   net1 += r2[1]
#
#   net2 = Net(name="NET2")
#   net2 += r3[1]

# Step 4: Regenerate KiCad project with Y-connection
uv run three_resistors.py

# Step 5: Open regenerated KiCad project
open three_resistors/three_resistors.kicad_pro
# Verify:
#   - R1 connected to R2 via NET1 (labeled connection)
#   - R3 isolated on NET2 (labeled connection, no physical wire)
#   - No junction needed (connections are label-based, not physical wires)
#   - R1, R2, R3 positions preserved
#   - No component overlap

# Step 6: Verify junction disappeared
grep "(junction" three_resistors/three_resistors.kicad_sch || echo "No junctions (expected for Y-connection)"
```

## Expected Result

- ✅ Initial generation: T-connection with junction dot at connection point
- ✅ Junction element appears in .kicad_sch file: `(junction`
- ✅ After modifying to Y-connection: junction removed or count changes
- ✅ Component positions preserved between generations
- ✅ No duplicate components
- ✅ Electrical connectivity matches circuit definition

## Why This Is Important

**Visual and electrical clarity in circuits:**
1. T-connections (three wires meeting at one point) require junction dots for clarity
2. Y-connections (label-based, no physical wire) don't need junctions
3. KiCad must automatically manage junctions based on connection topology
4. Visual representation must match electrical reality

If this doesn't work:
- Circuit topology becomes ambiguous in KiCad (unclear which nets are connected)
- Electrical Rule Checker (ERC) may flag false errors
- Users see confusing schematic with unclear connections
- Circuit-synth integration with KiCad becomes unreliable

## Success Criteria

This test PASSES when:
- Initial circuit generates with junction elements for T-connection
- Schematic contains `(junction` entries corresponding to connection points
- After changing to Y-connection, junction count changes appropriately
- Component positions preserved from initial generation
- No component overlap
- Electrical connectivity via netlists matches Python definition
- Level 2 validation: kicad-sch-api + text search for junction elements

## Level 2 Validation Details

This test uses **Level 2 (kicad-sch-api + text search)** validation:

1. **Schematic Structure** - kicad-sch-api validates components and nets exist
2. **Junction Search** - Text search finds `(junction` entries in .kicad_sch file
3. **Junction Count** - Validates junction count changes appropriately
4. **Position Validation** - Verifies component positions haven't changed between steps
5. **Topology Verification** - Confirms net connectivity matches Python definition

This multi-step validation ensures junctions are correctly placed for connection clarity.
