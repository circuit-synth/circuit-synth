# Test 11: Add Net to Existing Unconnected Components

## What This Tests

**Core Question**: When you have unconnected components in a KiCad schematic and add a net connection in Python code, does the wire appear when regenerating?

This tests **bidirectional sync for net creation** - adding electrical connections to existing components.

## When This Situation Happens

- Developer generates circuit with unconnected components (R1, R2)
- Later decides components should be electrically connected
- Adds `Net("NET1")` in Python code connecting the pins
- Regenerates KiCad expecting wire to appear

## What Should Work

1. Generate initial KiCad with R1 and R2 (no connection)
2. Manually verify components are unconnected in KiCad
3. Edit Python to add Net connecting R1[1] to R2[1]
4. Regenerate KiCad project
5. Wire appears connecting the components with net label

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional/11_add_net_to_components

# Step 1: Generate initial KiCad project (no connection)
uv run two_resistors.py
open two_resistors/two_resistors.kicad_pro
# Verify: R1 and R2 visible but NO wire between them

# Step 2: Edit two_resistors.py to add net connection
# Change import line to:
#   from circuit_synth import circuit, Component, Net
# Add before the end of the function (after r2 definition):
#   net1 = Net(name="NET1")
#   net1 += r1[1]
#   net1 += r2[1]

# Step 3: Regenerate KiCad project with connection
uv run two_resistors.py

# Step 4: Open regenerated KiCad project
open two_resistors/two_resistors.kicad_pro
# Verify:
#   - Wire now connects R1[1] to R2[1]
#   - Hierarchical label "NET1" visible (square flag shape)
#   - R1 and R2 positions preserved (didn't move)
#   - Components still no overlap
```

## Expected Result

- ✅ Initial generation: R1 and R2 unconnected
- ✅ After adding Net in Python: wire appears in KiCad
- ✅ Hierarchical label "NET1" visible on connection
- ✅ Component positions preserved during regeneration
- ✅ No duplicate components
- ✅ Connection is electrically valid (no ERC errors)

**Note**: Uses `hierarchical_label` format (same as test 10)

## Why This Is Important

**Iterative circuit development workflow:**
1. Generate initial circuit structure (components only)
2. Review component placement in KiCad
3. Add electrical connections in Python
4. Regenerate - connections appear without losing layout

If this doesn't work, users must define all nets upfront or manually wire in KiCad (defeating the purpose of code-based design).

## Success Criteria

This test PASSES when:
- Unconnected components generate correctly initially
- Adding Net() in Python creates wire in KiCad
- Hierarchical label appears and is readable
- Component positions preserved across regeneration
- No electrical rule errors in KiCad
