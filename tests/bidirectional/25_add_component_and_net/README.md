# Test 32: Add Component AND Net Simultaneously

## What This Tests

**Core Question**: When you add a new component (R2) and immediately connect it to an existing component (R1) via a new net (NET1) in the same regeneration, does sync handle the combined operation correctly?

This tests **bidirectional sync for combined component+net addition** - ensuring atomic multi-object operations work without ordering dependencies.

## When This Situation Happens

- Developer starts with single component R1 (unconnected)
- Adds new component R2
- Immediately creates net connecting R1-R2
- Single regeneration handles both additions
- Tests if sync can handle dependencies between new objects

## What Should Work

1. Generate initial KiCad with only R1 (no nets)
2. Edit Python to add R2 and NET1 connecting R1-R2
3. Regenerate KiCad project
4. Both R1 and R2 exist
5. Both have "NET1" hierarchical labels
6. Single operation, correct result

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional/32_add_component_and_net

# Step 1: Generate initial KiCad project (only R1, no nets)
uv run single_resistor.py
open single_resistor/single_resistor.kicad_pro
# Verify: R1 exists, no labels, no other components

# Step 2: Edit single_resistor.py to add R2 and NET1
# Add after R1 definition:
#   r2 = Component(
#       symbol="Device:R",
#       ref="R2",
#       value="4.7k",
#       footprint="Resistor_SMD:R_0603_1608Metric",
#   )
#
#   net1 = Net(name="NET1")
#   net1 += r1[1]
#   net1 += r2[1]

# Step 3: Regenerate KiCad project
uv run single_resistor.py

# Step 4: Open regenerated KiCad project
open single_resistor/single_resistor.kicad_pro
# Verify:
#   - R1 exists (kept from previous)
#   - R2 exists (newly added)
#   - R1 pin 1 has "NET1" label (newly added)
#   - R2 pin 1 has "NET1" label (newly added)
#   - Both components electrically connected
#   - No missing labels or components
```

## Expected Result

- ✅ Initial generation: R1 only, no nets
- ✅ After adding R2+NET1: Both components exist
- ✅ Both components have "NET1" labels
- ✅ Electrical connection correct
- ✅ Single regeneration handles both additions
- ✅ No ordering issues or missing elements

**Expected sync summary:**
```
Actions:
   ✅ Keep: R1 (matches Python)
   ➕ Add: R2 (new component)
   ➕ Add net: NET1 (new net)
   ➕ Add label: NET1 to R1 pin 1 (new label on existing component)
   ➕ Add label: NET1 to R2 pin 1 (new label on new component)
```

## Likely Actual Result (Based on #344, #345, #336)

**Prediction:** Likely fails with ordering or dependency issues

- ❌ R2 added but labels missing (#345)
- ❌ NET1 created but not applied to components (#344)
- ❌ R1 label missing (existing component, new net)
- ❌ R2 label missing (new component, new net)
- ❌ Sync may process in wrong order (components before nets)
- ❌ OR sync may require separate regenerations for each operation

## Why This Is Important

**Extremely common development pattern:**
- Adding components while building circuit
- Natural workflow: "add R2 and connect it to R1"
- Should work in single operation, not require two steps
- Tests sync's ability to handle dependencies

If this doesn't work:
- Developer must add component first, regenerate
- Then add net, regenerate again
- Two-step process for natural single operation
- Poor developer experience
- Breaks iterative development flow

## Success Criteria

This test PASSES when:
- Both R1 and R2 exist in schematic
- Both have "NET1" labels on correct pins
- Sync summary shows all operations (keep R1, add R2, add NET1, add labels)
- Single regeneration succeeds
- Electrical connection correct

## Comparison to Incremental Operations

**Single-step (this test)** vs **Multi-step (other tests)**

| Approach | Operations | Regenerations | Tests |
|----------|-----------|---------------|--------|
| Single-step | Add R2 + Add NET1 | 1 | This test |
| Multi-step | Add R2, then Add NET1 | 2 | Tests 06 + 11 |

Both should work, but single-step is more natural.

## Related Tests

- **Test 06** - Add component (only component, no net)
- **Test 11** - Add net to existing components
- **Test 12** - Add component to existing net (inverse: net exists first)
- **Test 19** - Add component and update Python (similar combined operation)

## Related Issues

- **#344** - Net sync doesn't add labels (affects NET1 labels)
- **#345** - New component on net doesn't get labels (affects R2 label)
- **#336** - Component operations may fail
- **#338** - Operation ordering and dependencies

## Edge Cases to Consider

**After this basic test works:**
- Add two components and one net (R2, R3, NET1)
- Add one component and two nets (R2 on NET1 and NET2)
- Add component, net, and modify existing component value
- Add with auto-generated net name
- Add to circuit with existing components and nets
- Add multiple components on multiple new nets

## Sync Dependency Analysis

**Dependency chain for this operation:**

```
1. Keep R1 (no dependencies)
2. Add R2 (no dependencies)
3. Add NET1 (depends on: R1 existing, R2 existing)
4. Add label to R1 (depends on: R1 existing, NET1 existing)
5. Add label to R2 (depends on: R2 existing, NET1 existing)
```

**Sync must handle these dependencies correctly:**
- Process components before nets that reference them
- Process nets before labels that reference them
- OR handle circular references gracefully

## Debug Investigation Path

**If this test fails, investigate:**
1. What order does sync process operations? (components first? nets first?)
2. Does sync detect all three operations? (keep R1, add R2, add NET1)
3. Are labels attempted but fail? (execution issue)
4. Are labels not attempted? (detection issue)
5. Does two-step process work? (add R2, regen, add NET1, regen)
