# Test 24: Remove Component from Existing Net

## What This Tests

**Core Question**: When you remove a component (R3) from an existing net (NET1) with multiple components, does its hierarchical label disappear when regenerating?

This tests **bidirectional sync for net removal** - removing connections from existing components.

## When This Situation Happens

- Developer has circuit with R1-R2-R3 all on NET1
- Decides R3 should not be connected (or connect to different net)
- Removes `net1 += r3[1]` from Python code
- Regenerates KiCad expecting R3's NET1 label to disappear

## What Should Work

1. Generate initial KiCad with R1-R2-R3 on NET1 (all three have labels)
2. Edit Python to remove R3 from NET1
3. Regenerate KiCad project
4. R3's "NET1" hierarchical label should disappear
5. R1 and R2 keep their "NET1" labels (still connected)

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional/24_remove_from_net

# Step 1: Generate initial KiCad project (all three on NET1)
uv run three_resistors_on_net.py
open three_resistors_on_net/three_resistors_on_net.kicad_pro
# Verify: R1, R2, R3 all have "NET1" hierarchical labels

# Step 2: Edit three_resistors_on_net.py to remove R3 from net
# Comment out or delete the line:
#   net1 += r3[1]

# Step 3: Regenerate KiCad project
uv run three_resistors_on_net.py

# Step 4: Open regenerated KiCad project
open three_resistors_on_net/three_resistors_on_net.kicad_pro
# Verify:
#   - R1 still has "NET1" label
#   - R2 still has "NET1" label
#   - R3 has NO "NET1" label (removed)
#   - R3 component still exists (not deleted)
#   - All three components present in schematic
```

## Expected Result

- ✅ Initial generation: R1, R2, R3 all have "NET1" labels
- ✅ After removing R3 from net: R3's label disappears
- ✅ R1 and R2 still have "NET1" labels (net still exists)
- ✅ R3 component still exists in schematic (only label removed)
- ✅ Component positions preserved
- ✅ No duplicate components

**Expected sync summary:**
```
Actions:
   ✅ Keep: R1, R2, R3 (all match Python)
   🔌 Update net: NET1 (R3[1] removed from net)
   🗑️  Remove label: NET1 from R3 pin 1
```

## Likely Actual Result (Based on #344, #345)

**Prediction:** Label will NOT be removed

- ❌ R3 will still have "NET1" label after regeneration
- ❌ Sync won't detect net topology change
- ❌ Label removal won't execute

## Why This Is Important

**Common refactoring operation:**
- Reorganizing circuit connections
- Moving component to different net
- Isolating component for testing
- Removing component from power rail

If labels don't disappear:
- Schematic shows incorrect connections
- Electrical design doesn't match code
- Misleading for PCB layout and debugging

## Success Criteria

This test PASSES when:
- R3's "NET1" hierarchical label disappears
- R1 and R2 still have "NET1" labels
- Sync summary shows net update operation
- Sync summary shows label removal
- No electrical rule errors in KiCad

## Related Tests

- **Test 12** - Add component to net (inverse operation)
- **Test 11** - Add net to components
- **Test 26** - Delete entire net (removes all labels)

## Related Issues

- **#344** - Net sync doesn't add labels (likely same for removal)
- **#345** - New component on net doesn't get labels
- **#336** - Component deletion doesn't work (similar execution issue)
