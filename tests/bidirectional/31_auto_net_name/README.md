# Test 31: Auto-Generated Net Name

## What This Tests

**Core Question**: When you create a Net with `name=None` (or no name parameter), does circuit-synth auto-generate a net name and apply hierarchical labels correctly during bidirectional sync?

This tests **bidirectional sync with auto-generated net names** - ensuring automatic naming works correctly and survives regeneration cycles.

## When This Situation Happens

- Developer connects components but doesn't specify net name
- Uses `Net(name=None)` or `Net()` without name parameter
- Expects circuit-synth to auto-generate sensible name
- Common during prototyping or quick testing

## What Should Work

1. Generate initial KiCad with `Net(name=None)`
2. Circuit-synth auto-generates net name (e.g., "Net-R1-Pad1")
3. Hierarchical labels use auto-generated name
4. Regenerate - auto-generated name persists
5. Can manually rename auto-generated name later

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional/31_auto_net_name

# Step 1: Generate initial KiCad project (auto-generated name)
uv run two_resistors_auto_net.py
open two_resistors_auto_net/two_resistors_auto_net.kicad_pro
# Verify:
#   - R1 pin 1 and R2 pin 1 have hierarchical labels
#   - Labels show auto-generated name (e.g., "Net-R1-Pad1" or similar)
#   - Note the auto-generated name for next steps

# Step 2: Regenerate without changes
uv run two_resistors_auto_net.py

# Step 3: Open regenerated KiCad project
open two_resistors_auto_net/two_resistors_auto_net.kicad_pro
# Verify:
#   - Labels still present on same pins
#   - Net name unchanged (same auto-generated name)
#   - No duplicate or missing labels

# Step 4: Edit two_resistors_auto_net.py to specify name
# Change line:
#   net1 = Net(name=None)
# To:
#   net1 = Net(name="SIGNAL_BUS")

# Step 5: Regenerate with new name
uv run two_resistors_auto_net.py
open two_resistors_auto_net/two_resistors_auto_net.kicad_pro
# Verify:
#   - Labels changed from auto-generated name to "SIGNAL_BUS"
#   - No old labels remain
```

## Expected Result

- ✅ Initial generation: Auto-generates reasonable net name
- ✅ Labels use auto-generated name
- ✅ Regeneration: Same auto-generated name persists
- ✅ Can rename from auto-generated to explicit name
- ✅ No label conflicts or duplicates

**Expected sync summary (initial):**
```
Actions:
   ➕ Add: R1, R2
   ➕ Add net: Net-R1-Pad1 (auto-generated)
   ➕ Add label: Net-R1-Pad1 to R1 pin 1
   ➕ Add label: Net-R1-Pad1 to R2 pin 1
```

**Expected sync summary (rename to explicit):**
```
Actions:
   ✅ Keep: R1, R2
   🔄 Rename net: Net-R1-Pad1 → SIGNAL_BUS
   🏷️  Update label: Net-R1-Pad1 → SIGNAL_BUS on R1 pin 1
   🏷️  Update label: Net-R1-Pad1 → SIGNAL_BUS on R2 pin 1
```

## Likely Actual Result (Based on #344, #345)

**Prediction:** Auto-generation may work initially, but regeneration may fail

- ❌ Auto-generated name may change each regeneration (instability)
- ❌ Labels may not appear with auto-generated names
- ❌ Renaming from auto to explicit may not work
- ❌ Sync may not recognize auto-generated nets
- ⚠️  OR auto-generation may not be implemented at all

## Why This Is Important

**Common during development workflow:**
- Quick prototyping without naming everything
- Temporary test circuits
- Automatic naming for internal connections
- Reducing boilerplate code

If auto-generation doesn't work:
- Developer must manually name every net
- Increases code verbosity
- Slows down prototyping
- Poor developer experience

If auto-generated names unstable:
- Regeneration creates different names
- Labels change every time
- Sync treats as different nets
- Breaks bidirectional sync

## Success Criteria

This test PASSES when:
- Auto-generates reasonable net name (readable, deterministic)
- Labels use auto-generated name correctly
- Same auto-generated name persists across regenerations
- Can rename from auto-generated to explicit name
- Sync correctly detects rename operation
- No duplicate or missing labels

## Related Tests

- **Test 25** - Rename net (similar label updates, but explicit→explicit)
- **Test 28** - Split net (auto-generated names for split nets?)
- **Test 11** - Add net (explicit name case)

## Related Issues

- **#344** - Net sync doesn't add labels (may affect auto-generated nets)
- **#345** - New component on net doesn't get labels
- **#338** - Rename operations (auto→explicit rename)

## Auto-Generation Naming Strategies

**Good auto-generation approaches:**
- `Net-R1-Pad1` - Based on first component and pin
- `Net-0001` - Sequential numbering
- `unconnected-R1.1` - Descriptive of state

**Bad approaches:**
- Random names - Changes every regeneration
- Empty string - Causes conflicts
- Non-deterministic - Breaks sync

## Edge Cases to Consider

**After this basic test works:**
- Multiple auto-generated nets in same circuit
- Auto-generated name conflicts with existing explicit name
- Rename auto-generated net to another auto-generated format
- Auto-generated net with complex topology (3+ components)
- Auto-generated net in hierarchical sheets
- Power nets with auto-generated names (special handling?)

## Design Questions

**Should be tested/validated:**
1. What naming scheme is used for auto-generation?
2. Is auto-generated name deterministic (same every time)?
3. Can user override auto-generated name later?
4. How does sync detect "same net but different name"?
5. Are auto-generated names unique within circuit?
