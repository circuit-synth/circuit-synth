# Test 12: Add Component to Existing Net

## What This Tests
Validates that adding a third component to an existing connection between two components works correctly in KiCad.

## When This Situation Happens
- Developer has two components connected via a named net (R1-R2 on NET1)
- Needs to add another component to the same connection (R3)
- Modifies Python to connect R3 to the existing NET1
- Regenerates KiCad expecting all three components on the same net

## What Should Work
- Initial circuit with R1-R2 connected via NET1 generates correctly
- Python modified to add R3 connected to same NET1
- Regenerated KiCad shows all three components on the same net
- Net connections are properly maintained across all components

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional/12_add_to_net

# Step 1: Generate initial KiCad project (R1 and R2 on NET1)
uv run two_resistors_on_net.py
open two_resistors_on_net/two_resistors_on_net.kicad_pro
# Verify: schematic shows R1 and R2 connected via NET1
# Check: NET1 hierarchical labels appear on the connections

# Step 2: Edit two_resistors_on_net.py to add R3
# Add after R2 definition:
#   r3 = Component(symbol="Device:R", ref="R3", value="2.2k",
#                  footprint="Resistor_SMD:R_0603_1608Metric")
# Add after net1 += r2[1]:
#   net1 += r3[1]

# Step 3: Regenerate KiCad with R3 added to NET1
uv run two_resistors_on_net.py
open two_resistors_on_net/two_resistors_on_net.kicad_pro
# Verify in KiCad schematic:
#   - R1, R2, R3 all present
#   - All three connected to NET1
#   - NET1 hierarchical labels appear on connections
#   - No orphaned nets or connections
#   - R1 and R2 positions preserved (not moved)
#   - R3 placed without overlapping existing components
```

## Expected Result

- ✅ Initial KiCad project has R1 and R2 with "NET1" hierarchical labels
- ✅ After adding R3 and regenerating, all three resistors have "NET1" labels
- ✅ Three hierarchical labels "NET1" visible (one on each component pin)
- ✅ NO physical wires between components
- ✅ Electrical connection established by matching label names
- ✅ R1 and R2 positions preserved (not moved)
- ✅ R3 placed in available space
- ✅ No duplicate nets or connection issues
- ✅ KiCad schematic shows clear NET1 labels on all three components

**Note**: Hierarchical labels with matching names create multi-point electrical connection

## Why This Is Important

Real circuits often require adding components to existing connections. This test validates that the net system correctly handles growing connections and maintains proper electrical relationships across multiple components.
