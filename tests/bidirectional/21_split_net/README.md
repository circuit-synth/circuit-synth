# Test 28: Split Net

## What This Tests

**Core Question**: When you split one net into two separate nets (NET1: R1-R2-R3-R4 → NET1: R1-R2, NET2: R3-R4), do the hierarchical labels update to reflect the new net topology?

This tests **bidirectional sync for net splitting** - dividing one electrical connection into two independent connections.

## When This Situation Happens

- Developer has four components all connected via NET1
- Realizes two groups should be electrically separate
- Splits connections: R1-R2 stay on NET1, R3-R4 move to new NET2
- Regenerates KiCad expecting labels to update

## What Should Work

1. Generate initial KiCad with R1-R2-R3-R4 all on NET1 (all have "NET1" labels)
2. Edit Python to split into two nets
3. Regenerate KiCad project
4. R1 and R2 keep "NET1" labels
5. R3 and R4 get "NET2" labels (updated from NET1)
6. Two separate electrical connections

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional/28_split_net

# Step 1: Generate initial KiCad project (all on NET1)
uv run four_resistors_one_net.py
open four_resistors_one_net/four_resistors_one_net.kicad_pro
# Verify: R1, R2, R3, R4 all have "NET1" hierarchical labels

# Step 2: Edit four_resistors_one_net.py to split net
# Change from:
#   net1 = Net(name="NET1")
#   net1 += r1[1]
#   net1 += r2[1]
#   net1 += r3[1]
#   net1 += r4[1]
#
# To:
#   net1 = Net(name="NET1")
#   net1 += r1[1]
#   net1 += r2[1]
#
#   net2 = Net(name="NET2")
#   net2 += r3[1]
#   net2 += r4[1]

# Step 3: Regenerate KiCad project
uv run four_resistors_one_net.py

# Step 4: Open regenerated KiCad project
open four_resistors_one_net/four_resistors_one_net.kicad_pro
# Verify:
#   - R1: "NET1" label (unchanged)
#   - R2: "NET1" label (unchanged)
#   - R3: "NET2" label (changed from NET1)
#   - R4: "NET2" label (changed from NET1)
#   - NO "NET1" labels on R3 or R4
#   - All components present at same positions
```

## Expected Result

- ✅ Initial generation: All four have "NET1" labels
- ✅ After split: R1-R2 have "NET1" labels
- ✅ After split: R3-R4 have "NET2" labels
- ✅ No "NET1" labels on R3-R4 (cleaned up)
- ✅ Two separate electrical connections
- ✅ Component positions preserved

**Expected sync summary:**
```
Actions:
   ✅ Keep: R1, R2, R3, R4 (all match Python)
   🔌 Update net: NET1 (now only R1-R2)
   ➕ Add net: NET2 (new net for R3-R4)
   🗑️  Remove label: NET1 from R3 pin 1
   🗑️  Remove label: NET1 from R4 pin 1
   ➕ Add label: NET2 to R3 pin 1
   ➕ Add label: NET2 to R4 pin 1
```

## Likely Actual Result (Based on #344, #345)

**Prediction:** Labels won't update - will see incorrect topology

- ❌ R3-R4 keep "NET1" labels (not updated)
- ❌ R3-R4 don't get "NET2" labels
- ❌ OR both labels appear (NET1 and NET2)
- ❌ Schematic shows incorrect electrical connections
- ❌ Sync won't detect net split operation

## Why This Is Important

**Very common circuit refactoring:**
- Separating power domains (3.3V and 5V were combined by mistake)
- Isolating signal groups (split I2C buses)
- Creating independent test points
- Fixing incorrect electrical connections

If labels don't update:
- Schematic shows all components connected
- PCB netlist incorrectly connects separate groups
- Electrical shorts or incorrect operation
- Critical design error

## Success Criteria

This test PASSES when:
- R1-R2 keep "NET1" labels only
- R3-R4 have "NET2" labels only
- No "NET1" labels on R3-R4
- Sync summary shows net update and new net creation
- Sync summary shows label removals and additions
- Electrical connections correct in KiCad (two separate nets)

## Related Tests

- **Test 29** - Merge nets (inverse operation: two nets → one net)
- **Test 25** - Rename net (changes label text, not topology)
- **Test 11** - Add net (creates new net, similar to NET2 creation)
- **Test 24** - Remove from net (partial removal vs split)

## Related Issues

- **#344** - Net sync doesn't add labels (NET2 labels likely won't appear)
- **#345** - New component on net doesn't get labels
- **#336** - Component deletion doesn't work
- **#338** - Rename treated as delete+add (may affect net split detection)

## Edge Cases to Consider

**After this basic test works:**
- Split into three or more nets
- Split unevenly (1 component vs 3 components)
- Split with overlapping names (NET1 → NET1A, NET1B)
- Split while also renaming (NET1 → NET2, NET3)
- Split with auto-generated net names
