# Test 26: Delete Net

## What This Tests

**Core Question**: When you completely remove a Net() from Python code, do all its hierarchical labels disappear from the KiCad schematic when regenerating?

This tests **bidirectional sync for net deletion** - complete removal of electrical connections.

**Note:** This is the inverse of Test 11 (add net to components).

## When This Situation Happens

- Developer has circuit with R1-R2 connected via NET1
- Decides components should be unconnected
- Removes entire `Net("NET1")` definition and connections from Python
- Regenerates KiCad expecting all NET1 labels to disappear

## What Should Work

1. Generate initial KiCad with R1-R2 on NET1 (both have labels)
2. Edit Python to remove entire Net definition
3. Regenerate KiCad project
4. All "NET1" hierarchical labels disappear
5. R1 and R2 remain but are now unconnected

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional/26_delete_net

# Step 1: Generate initial KiCad project (with NET1)
uv run two_resistors_on_net.py
open two_resistors_on_net/two_resistors_on_net.kicad_pro
# Verify: R1[1] and R2[1] both have "NET1" hierarchical labels

# Step 2: Edit two_resistors_on_net.py to remove net
# Delete or comment out these lines:
#   net1 = Net(name="NET1")
#   net1 += r1[1]
#   net1 += r2[1]

# Step 3: Regenerate KiCad project
uv run two_resistors_on_net.py

# Step 4: Open regenerated KiCad project
open two_resistors_on_net/two_resistors_on_net.kicad_pro
# Verify:
#   - R1 and R2 still exist (components not deleted)
#   - NO "NET1" labels on any pins
#   - Components are completely unconnected
#   - Component positions preserved
```

## Expected Result

- ✅ Initial generation: R1 and R2 have "NET1" labels
- ✅ After deleting net: NO labels remain
- ✅ R1 and R2 components still exist (only net removed)
- ✅ Components are electrically disconnected
- ✅ Component positions preserved
- ✅ No orphaned labels

**Expected sync summary:**
```
Actions:
   ✅ Keep: R1, R2 (match Python)
   🗑️  Delete net: NET1 (not in Python code)
   🗑️  Remove label: NET1 from R1 pin 1
   🗑️  Remove label: NET1 from R2 pin 1
```

## Likely Actual Result (Based on #344, #345, #336)

**Prediction:** Labels will NOT be removed

- ❌ "NET1" labels will remain after regeneration
- ❌ Sync won't detect net deletion
- ❌ Components show as connected when they shouldn't be
- ❌ Similar to component deletion issue (#336)

## Why This Is Important

**Common during circuit iteration:**
- Testing components in isolation
- Removing incorrect connections
- Simplifying circuit for debugging
- Reorganizing circuit topology

If labels don't disappear:
- Schematic shows false connections
- Electrical design incorrect
- PCB netlist has phantom nets
- Very confusing for development

## Success Criteria

This test PASSES when:
- All "NET1" hierarchical labels disappear
- R1 and R2 components still exist
- Sync summary shows net deletion
- Sync summary shows label removals
- No electrical connection between R1 and R2
- No electrical rule errors in KiCad

## Comparison to Related Tests

**Test 11 (Add Net)** - Inverse operation
- Start: unconnected components
- End: connected with labels
- Currently fails (#344)

**Test 26 (Delete Net)** - This test
- Start: connected components with labels
- End: unconnected, no labels
- Likely fails (same sync system)

**Test 24 (Remove from Net)**
- Similar but partial removal (R3 from NET1)
- Net still exists for R1-R2
- This test: complete net removal

## Related Tests

- **Test 11** - Add net (inverse operation)
- **Test 24** - Remove component from net (partial removal)
- **Test 07** - Delete component (#336)

## Related Issues

- **#344** - Net sync doesn't add labels
- **#345** - Net sync doesn't update new component labels
- **#336** - Component deletion doesn't work (similar execution failure)

**Pattern:** Sync detection vs execution - may detect deletion but not execute it.
