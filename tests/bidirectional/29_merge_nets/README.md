# Test 29: Merge Nets

## What This Tests

**Core Question**: When you merge two separate nets into one (NET1: R1-R2, NET2: R3-R4 → NET1: R1-R2-R3-R4), do all hierarchical labels update to show the merged net name?

This tests **bidirectional sync for net merging** - combining two independent electrical connections into one.

**Note:** This is the inverse of Test 28 (split net).

## When This Situation Happens

- Developer has R1-R2 on NET1, R3-R4 on NET2 (separate connections)
- Realizes all components should be electrically connected
- Merges connections: all move to NET1, delete NET2
- Regenerates KiCad expecting all labels to show NET1

## What Should Work

1. Generate initial KiCad with R1-R2 on NET1, R3-R4 on NET2 (different labels)
2. Edit Python to merge all onto NET1
3. Regenerate KiCad project
4. R1 and R2 keep "NET1" labels (unchanged)
5. R3 and R4 change from "NET2" to "NET1" labels
6. Single electrical connection for all four components

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional/29_merge_nets

# Step 1: Generate initial KiCad project (two separate nets)
uv run four_resistors_two_nets.py
open four_resistors_two_nets/four_resistors_two_nets.kicad_pro
# Verify:
#   - R1, R2 have "NET1" labels
#   - R3, R4 have "NET2" labels

# Step 2: Edit four_resistors_two_nets.py to merge nets
# Change from:
#   net1 = Net(name="NET1")
#   net1 += r1[1]
#   net1 += r2[1]
#
#   net2 = Net(name="NET2")
#   net2 += r3[1]
#   net2 += r4[1]
#
# To:
#   net1 = Net(name="NET1")
#   net1 += r1[1]
#   net1 += r2[1]
#   net1 += r3[1]
#   net1 += r4[1]

# Step 3: Regenerate KiCad project
uv run four_resistors_two_nets.py

# Step 4: Open regenerated KiCad project
open four_resistors_two_nets/four_resistors_two_nets.kicad_pro
# Verify:
#   - R1: "NET1" label (unchanged)
#   - R2: "NET1" label (unchanged)
#   - R3: "NET1" label (changed from NET2)
#   - R4: "NET1" label (changed from NET2)
#   - NO "NET2" labels anywhere
#   - All components electrically connected
```

## Expected Result

- ✅ Initial generation: R1-R2 have "NET1", R3-R4 have "NET2"
- ✅ After merge: All four have "NET1" labels
- ✅ No "NET2" labels remain (deleted)
- ✅ Single electrical connection for all components
- ✅ Component positions preserved

**Expected sync summary:**
```
Actions:
   ✅ Keep: R1, R2, R3, R4 (all match Python)
   🔌 Update net: NET1 (now includes R3-R4)
   🗑️  Delete net: NET2 (merged into NET1)
   🗑️  Remove label: NET2 from R3 pin 1
   🗑️  Remove label: NET2 from R4 pin 1
   ➕ Add label: NET1 to R3 pin 1
   ➕ Add label: NET1 to R4 pin 1
```

## Likely Actual Result (Based on #344, #345)

**Prediction:** Labels won't update - will see mixed or incorrect labels

- ❌ R3-R4 keep "NET2" labels (not updated)
- ❌ R3-R4 don't get "NET1" labels
- ❌ OR both labels appear (NET1 and NET2 together)
- ❌ Schematic shows separate nets instead of merged
- ❌ Sync won't detect net merge operation

## Why This Is Important

**Common circuit evolution operation:**
- Connecting previously isolated sections
- Joining power domains (unify 3.3V rails)
- Combining signal groups (merge I2C buses)
- Simplifying circuit topology
- Fixing design mistakes (separate nets should be connected)

If labels don't update:
- Schematic shows disconnected sections
- PCB netlist won't connect merged components
- Electrical circuit incomplete
- Critical functional failure

## Success Criteria

This test PASSES when:
- All four components have "NET1" labels only
- No "NET2" labels remain
- Sync summary shows net deletion (NET2)
- Sync summary shows label updates (NET2 → NET1)
- Electrical connections correct in KiCad (single net)
- No electrical rule errors

## Related Tests

- **Test 28** - Split net (inverse operation: one net → two nets)
- **Test 26** - Delete net (removes all labels vs merge changes labels)
- **Test 11** - Add component to net (similar: adding to existing net)
- **Test 24** - Remove from net (opposite: removing vs merging)

## Related Issues

- **#344** - Net sync doesn't add labels (NET1 labels likely won't appear on R3-R4)
- **#345** - New component on net doesn't get labels
- **#336** - Component deletion doesn't work (NET2 deletion may fail)
- **#338** - Rename treated as delete+add (may affect merge detection)

## Edge Cases to Consider

**After this basic test works:**
- Merge three or more nets into one
- Merge into new net name (NET1+NET2 → NET3)
- Merge with different component counts (2+5 components)
- Merge with overlapping component references
- Merge with auto-generated net names
- Bidirectional merge (A→B vs B→A)

## Comparison to Related Tests

**Test 28 (Split)** vs **Test 29 (Merge)**

| Aspect | Test 28: Split | Test 29: Merge |
|--------|---------------|----------------|
| Starting state | One net (NET1) | Two nets (NET1, NET2) |
| Ending state | Two nets (NET1, NET2) | One net (NET1) |
| Label changes | Some stay, some change | Some stay, some change |
| Net count | Increases (1→2) | Decreases (2→1) |
| Operation type | Additive (create NET2) | Reductive (delete NET2) |

Both test topology changes but in opposite directions.
