# Test 25: Rename Net

## What This Tests

**Core Question**: When you rename a net from NET1 to NET2 in Python code, do the hierarchical labels update to show the new name when regenerating?

This tests **bidirectional sync for net renaming** - updating net names across all connected components.

## When This Situation Happens

- Developer has circuit with R1-R2 on NET1
- Decides to rename for clarity (NET1 → SIGNAL_BUS, or NET1 → DATA_LINE)
- Changes `Net(name="NET1")` to `Net(name="NET2")` in Python
- Regenerates KiCad expecting labels to update

## What Should Work

1. Generate initial KiCad with R1-R2 on NET1 (labels show "NET1")
2. Edit Python to rename net: NET1 → NET2
3. Regenerate KiCad project
4. All hierarchical labels update from "NET1" to "NET2"
5. Electrical connection maintained (same components connected)

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional/25_rename_net

# Step 1: Generate initial KiCad project (NET1)
uv run two_resistors_net1.py
open two_resistors_net1/two_resistors_net1.kicad_pro
# Verify: R1[1] and R2[1] both have "NET1" hierarchical labels

# Step 2: Edit two_resistors_net1.py to rename net
# Change line:
#   net1 = Net(name="NET1")
# To:
#   net1 = Net(name="NET2")

# Step 3: Regenerate KiCad project
uv run two_resistors_net1.py

# Step 4: Open regenerated KiCad project
open two_resistors_net1/two_resistors_net1.kicad_pro
# Verify:
#   - R1[1] has "NET2" label (updated from NET1)
#   - R2[1] has "NET2" label (updated from NET1)
#   - NO "NET1" labels remaining
#   - Components still connected (electrically)
#   - Component positions preserved
```

## Expected Result

- ✅ Initial generation: Labels show "NET1"
- ✅ After renaming: Labels show "NET2"
- ✅ No "NET1" labels remaining
- ✅ Electrical connection maintained
- ✅ Component positions preserved
- ✅ No duplicate labels or nets

**Expected sync summary:**
```
Actions:
   ✅ Keep: R1, R2 (match Python)
   🔄 Rename net: NET1 → NET2
   🏷️  Update label: NET1 → NET2 on R1 pin 1
   🏷️  Update label: NET1 → NET2 on R2 pin 1
```

## Likely Actual Result (Based on #344, #345)

**Prediction:** Labels will NOT update

- ❌ Labels will still show "NET1" after regeneration
- ❌ Sync won't detect net name change
- ❌ May see both "NET1" and "NET2" labels (duplicate)
- ❌ Or NET2 might be ignored entirely

## Why This Is Important

**Very common refactoring operation:**
- Improving signal name clarity (NET1 → DATA_BUS)
- Following naming conventions (n1 → SPI_MOSI)
- Organizing complex circuits (NET5 → POWER_3V3)
- Documentation and readability

If labels don't update:
- Schematic shows wrong net names
- Confusion between code and KiCad
- PCB netlist has incorrect names
- Debugging becomes difficult

## Success Criteria

This test PASSES when:
- All "NET1" labels change to "NET2"
- No "NET1" labels remain in schematic
- Sync summary shows rename operation
- Electrical connection maintained
- No electrical rule errors in KiCad

## Related Tests

- **Test 23** - Rename component (similar rename operation, different object)
- **Test 26** - Delete net (complete removal vs rename)
- **Test 28** - Split net (one net becomes two, different from rename)

## Related Issues

- **#344** - Net sync doesn't add labels
- **#345** - Net sync doesn't update labels on new components
- **#338** - Component rename treated as delete+add (may happen for nets too)

## Edge Cases to Consider

**After this basic test works:**
- Rename to existing net name (NET1 → NET2 when NET2 already exists)
- Rename with special characters (NET1 → DATA/CLK)
- Rename to very long name (truncation?)
- Rename to empty string or None
