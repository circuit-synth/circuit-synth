# Test 27: Change Pin on Existing Net

## What This Tests

**Core Question**: When you change which pins are connected on the same net (R1[1]-R2[1] → R1[2]-R2[2]), do the hierarchical labels move to the new pins when regenerating?

This tests **bidirectional sync for pin-level net topology changes** - moving labels between pins on the same components.

## When This Situation Happens

- Developer has R1[1]-R2[1] connected via NET1
- Realizes connection should be on pin 2 instead
- Changes Python code: `net1 += r1[1]` → `net1 += r1[2]`
- Regenerates KiCad expecting labels to move from pin 1 to pin 2

## What Should Work

1. Generate initial KiCad with R1[1]-R2[1] on NET1 (labels on pin 1)
2. Edit Python to change connections to pin 2
3. Regenerate KiCad project
4. Labels disappear from pin 1
5. Labels appear on pin 2
6. Same net name (NET1), same components, different pins

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional/27_change_pin_on_net

# Step 1: Generate initial KiCad project (pin 1 connections)
uv run two_resistors_pin_change.py
open two_resistors_pin_change/two_resistors_pin_change.kicad_pro
# Verify: R1 pin 1 and R2 pin 1 both have "NET1" hierarchical labels

# Step 2: Edit two_resistors_pin_change.py to change pins
# Change lines:
#   net1 += r1[1]
#   net1 += r2[1]
# To:
#   net1 += r1[2]
#   net1 += r2[2]

# Step 3: Regenerate KiCad project
uv run two_resistors_pin_change.py

# Step 4: Open regenerated KiCad project
open two_resistors_pin_change/two_resistors_pin_change.kicad_pro
# Verify:
#   - R1 pin 1: NO label (removed)
#   - R2 pin 1: NO label (removed)
#   - R1 pin 2: "NET1" label (added)
#   - R2 pin 2: "NET1" label (added)
#   - Components still exist at same positions
```

## Expected Result

- ✅ Initial generation: Labels on R1[1] and R2[1]
- ✅ After pin change: Labels removed from pin 1
- ✅ After pin change: Labels added to pin 2
- ✅ Same net name (NET1)
- ✅ Component positions preserved
- ✅ No duplicate labels

**Expected sync summary:**
```
Actions:
   ✅ Keep: R1, R2 (match Python)
   🔌 Update net: NET1 (topology changed - different pins)
   🗑️  Remove label: NET1 from R1 pin 1
   🗑️  Remove label: NET1 from R2 pin 1
   ➕ Add label: NET1 to R1 pin 2
   ➕ Add label: NET1 to R2 pin 2
```

## Likely Actual Result (Based on #344, #345)

**Prediction:** Labels won't move - will see duplicates or no update

- ❌ Labels remain on pin 1 (not removed)
- ❌ Labels don't appear on pin 2
- ❌ OR both pins have labels (duplicates)
- ❌ Sync won't detect pin-level topology change

## Why This Is Important

**Common during circuit refinement:**
- Fixing pin assignment errors
- Swapping differential pairs
- Optimizing PCB routing (use different pins)
- Correcting datasheet misreads

If labels don't move:
- Schematic shows wrong connections
- PCB layout uses wrong pins
- Hardware will be incorrectly wired
- Critical functional error

## Success Criteria

This test PASSES when:
- Labels removed from old pins (pin 1)
- Labels added to new pins (pin 2)
- Sync summary shows label removal and addition
- No labels on wrong pins
- Electrical connection correct in KiCad

## Related Tests

- **Test 24** - Remove component from net (related: removing labels)
- **Test 11** - Add component to net (related: adding labels)
- **Test 28** - Split net (changes topology, but creates new net)

## Related Issues

- **#344** - Net sync doesn't add labels
- **#345** - New component on net doesn't get labels
- **#336** - Component deletion doesn't work (similar sync execution issue)
- **#338** - Rename treated as delete+add (may happen for pin changes too)

## Edge Cases to Consider

**After this basic test works:**
- Change pin on one component, not the other
- Change to non-existent pin number
- Swap pins (pin 1 ↔ pin 2)
- Multi-pin components (change from pin 1 to pin 5)
