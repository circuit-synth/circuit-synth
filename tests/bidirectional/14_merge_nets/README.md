# Test 14: Merge Nets (Two Separate Nets into One)

## What This Tests

**Core Question**: When you merge two separate nets into one (NET1: R1-R2, NET2: R3-R4 → NET1: R1-R2-R3-R4), do all hierarchical labels update to show the merged net name?

This tests **bidirectional sync for net merging** - combining two independent electrical connections into one.

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
cd /Users/shanemattner/Desktop/circuit-synth2/tests/bidirectional/14_merge_nets

# Step 1: Generate initial KiCad project (two separate nets)
uv run four_resistors.py
open four_resistors/four_resistors.kicad_pro
# Verify:
#   - R1, R2 have "NET1" labels
#   - R3, R4 have "NET2" labels

# Step 2: Edit four_resistors.py to merge nets
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
uv run four_resistors.py

# Step 4: Open regenerated KiCad project
open four_resistors/four_resistors.kicad_pro
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
- Netlist shows single NET1 with all four pins
- Component positions preserved
- No electrical rule errors in KiCad

## Related Tests

- **Test 21** - Split net (inverse operation: one net → two nets)
- **Test 19** - Delete net (removes all labels vs merge changes labels)
- **Test 11** - Add component to net (similar: adding to existing net)
- **Test 12** - Add to net (similar operation)
