# Test 12: Change Pin Connection on Existing Net

## What This Tests

**Core Question**: When you move a net connection from one component pin to another (R1[1] → R1[2]), do the hierarchical labels move to the new pin when regenerating?

This tests **bidirectional sync for pin-level connection changes** - reassigning which pin a net connects to on the same component.

## When This Situation Happens

- Developer has R1[1] and R2[1] connected via NET1
- Realizes NET1 should connect to R1[2] instead (e.g., wrong pin assignment, component swap, error correction)
- Changes Python code: `r1[1] += net1` → `r1[2] += net1`
- Regenerates KiCad expecting hierarchical label to move from R1 pin 1 to R1 pin 2
- Critical during design iteration when pin assignments change

## What Should Work

1. Generate initial KiCad with NET1: R1[1] ← NET1 → R2[1] (labels on pin 1)
2. Edit Python to change: R1[2] ← NET1 → R2[1]
3. Regenerate KiCad project
4. Hierarchical label "NET1" disappears from R1 pin 1
5. Hierarchical label "NET1" appears on R1 pin 2
6. R2 connection unchanged (still on pin 1)
7. Component positions preserved

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth2/tests/bidirectional/12_change_pin_connection

# Step 1: Generate initial KiCad project (R1[1] connection)
uv run two_resistors_initial.py
open two_resistors_pin_test/two_resistors_pin_test.kicad_pro
# Verify: R1 pin 1 and R2 pin 1 both have "NET1" hierarchical labels

# Step 2: Edit two_resistors_initial.py to change R1 pin connection
# Change lines:
#   # Connect R1 pin 1 to R2 pin 1
#   net1 = Net("NET1")
#   r1[1] += net1
#   r2[1] += net1
# To:
#   # Connect R1 pin 2 to R2 pin 1 (changed from pin 1)
#   net1 = Net("NET1")
#   r1[2] += net1  # Changed from r1[1]
#   r2[1] += net1

# Step 3: Regenerate KiCad project
uv run two_resistors_initial.py

# Step 4: Open regenerated KiCad project
open two_resistors_pin_test/two_resistors_pin_test.kicad_pro
# Verify:
#   - R1 pin 1: NO label (removed)
#   - R2 pin 1: "NET1" label (unchanged)
#   - R1 pin 2: "NET1" label (added)
#   - Components at same positions
```

## Expected Result

**Expected behavior (once Issue #380 is fixed):**

- ✅ Initial generation: Labels on R1[1] and R2[1]
- ✅ After pin change: Label removed from R1 pin 1
- ✅ After pin change: Label added to R1 pin 2
- ✅ R2 pin 1 label unchanged (NET1 still there)
- ✅ Component positions preserved
- ✅ Electrical connection correct: (R1, pin 2) ← NET1 → (R2, pin 1)

**Expected sync summary:**
```
Actions:
   ✅ Keep: R1, R2 (match Python)
   🔌 Update net: NET1 (topology changed - different pins)
   🗑️  Remove label: NET1 from R1 pin 1
   ➕ Add label: NET1 to R1 pin 2
```

## Known Limitation (Issue #380)

**Current behavior:** The synchronizer does NOT remove old hierarchical labels when pin connections change. This results in:

- ❌ Label remains on R1 pin 1 (not removed)
- ❌ Label also appears on R1 pin 2 (new pin)
- ❌ NET1 connects to BOTH R1 pin 1 AND R1 pin 2
- ❌ Wrong electrical connectivity

**Impact:**
- Schematic shows incorrect wiring (multiple pins on same component)
- PCB layout will use wrong pins
- Hardware will be incorrectly wired

**Workaround:** Manually remove old hierarchical labels in KiCad when changing pin assignments.

## Why This Is Critical

**Pin-level accuracy is essential for correct circuit operation:**

1. **Design iteration** - Changing pin assignments during prototyping
2. **Component swaps** - Replacing component with different pin configuration
3. **Routing optimization** - Using different pins to improve PCB layout
4. **Error correction** - Fixing datasheet misreads or schematic mistakes
5. **Signal integrity** - Moving high-speed signals to better pins

If pins aren't updated correctly:
- Physical wiring doesn't match design intent
- Hardware fails or behaves unexpectedly
- PCB layout uses wrong pins
- Signal integrity issues on wrong traces

## Success Criteria

This test PASSES when:

- Initial circuit generates with labels on correct pins
- After pin change regeneration, netlist shows new pin connection
- Electrical connectivity reflects the changed pin (e.g., (R1, 2) instead of (R1, 1))
- Component positions preserved across regeneration
- ⚠️ Note: Test currently documents Issue #380 behavior (both pins connected)

## Related Tests

- **Test 10** - Generate circuit with named net (foundation for net tests)
- **Test 11** - Add net to existing components (adding connections)
- **Test 20** - Change pin on existing net (similar: moving connections between pins)

## Related Issues

- **#374** - Hierarchical labels not removed when pin connections change
- **#344** - Net sync doesn't add labels properly
- **#345** - New components on net don't get labels
- **#346** - Power symbol rotation issues (related: component/net sync)
