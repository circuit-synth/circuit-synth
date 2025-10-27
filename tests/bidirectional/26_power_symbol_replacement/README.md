# Test 33: Power Symbol Replacement (Manual KiCad Edit)

## What This Tests

**Core Question**: When a user manually replaces circuit-synth generated hierarchical labels (GND) with KiCad power symbols in the schematic editor, what happens during regeneration?

This tests **power symbol preservation** and **hierarchical label vs power symbol semantics**.

## The Critical Difference

**Hierarchical Labels** (what circuit-synth generates):
- Text labels that say "GND"
- Connection by matching names within hierarchical context
- Generated from `Net(name="GND")`

**Power Symbols** (what users want):
- Actual KiCad power port symbols (⏚ ground symbol, +V arrow, etc.)
- **GLOBAL/UNIVERSAL CONNECTION** - all GND symbols connect everywhere
- Added manually in KiCad or from symbol library
- Semantic meaning: this is a power net

## Why This Matters (CRITICAL)

**KiCad treats these VERY differently:**

1. **Hierarchical labels**: Local to hierarchy, need matching names
2. **Power symbols**: Global across entire project, universal connection

**User expectation:**
- GND should be a global power net
- All GND connections should be universal
- Power symbols are the "correct" KiCad way

**Circuit-synth current behavior:**
- Generates hierarchical labels for ALL nets (including power)
- May not preserve power symbols
- May not recognize power symbol semantics

## When This Situation Happens

**Real-world workflow:**
1. User generates circuit from Python with `Net(name="GND")`
2. Circuit-synth creates hierarchical labels "GND"
3. User opens KiCad and thinks "this should be a power symbol"
4. User manually deletes hierarchical labels
5. User adds KiCad power symbols (Place → Power Port → GND)
6. User saves schematic
7. Later adds more components in Python connected to GND
8. Regenerates expecting power symbols preserved

## What Should Work (Ideal Behavior)

1. Generate circuit with GND hierarchical labels
2. User manually replaces with power symbols in KiCad
3. Regenerate (no Python changes)
4. **Power symbols should be preserved** (not reverted to labels)
5. Add new component with GND in Python
6. Regenerate
7. **New component should get power symbol** (not hierarchical label)
8. All GND symbols globally connected

## Manual Test Instructions

### Phase 1: Initial Generation

```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional/33_power_symbol_replacement

# Step 1: Generate initial circuit with GND hierarchical labels
uv run three_resistors_gnd.py
open three_resistors_gnd/three_resistors_gnd.kicad_pro

# Verify in KiCad:
#   - R1[2], R2[2], R3[2] all have "GND" hierarchical labels (square flags)
#   - NO power symbols (ground symbol ⏚)
#   - Labels connect components
```

### Phase 2: Manual Power Symbol Replacement

```bash
# Step 2: In KiCad schematic editor, manually replace labels with power symbols

# For each resistor (R1, R2, R3):
#   1. Select and delete the "GND" hierarchical label
#   2. Place → Power Port → GND (or Add Power Symbol from toolbar)
#   3. Connect power symbol to component pin
#   4. Repeat for all three components

# Verify:
#   - All three resistors connected to power symbol GND (⏚)
#   - NO hierarchical labels remaining
#   - Power symbols show ground symbol icon

# Step 3: Save schematic (Cmd+S)
# Close KiCad
```

### Phase 3: Regeneration Without Changes

```bash
# Step 4: Regenerate without Python changes (test preservation)
uv run three_resistors_gnd.py

# Step 5: Open regenerated schematic
open three_resistors_gnd/three_resistors_gnd.kicad_pro

# Critical verification:
#   - Are power symbols still present?
#   - Or did they revert to hierarchical labels?
#   - Are components still connected?
```

### Phase 4: Add Component After Replacement

```bash
# Step 6: Edit three_resistors_gnd.py to add R4
# Add after R3 definition:
#   r4 = Component(symbol="Device:R", ref="R4", value="1k",
#                  footprint="Resistor_SMD:R_0603_1608Metric")
# Add after gnd += r3[2]:
#   gnd += r4[2]

# Step 7: Regenerate with new component
uv run three_resistors_gnd.py

# Step 8: Open and verify
open three_resistors_gnd/three_resistors_gnd.kicad_pro

# Critical verification:
#   - Does R4 get power symbol or hierarchical label?
#   - Are R1-R3 power symbols preserved?
#   - Is R4 connected to same GND net?
```

## Expected Result (Ideal)

**Phase 1 - Initial generation:**
- ✅ Three hierarchical labels "GND"

**Phase 2 - Manual replacement:**
- ✅ User successfully adds power symbols
- ✅ Power symbols connect all three resistors

**Phase 3 - Regeneration without changes:**
- ✅ Power symbols preserved (NOT reverted to labels)
- ✅ Connections maintained
- ✅ No hierarchical labels reappear

**Phase 4 - Add new component:**
- ✅ R4 gets power symbol (matches existing style)
- ✅ R1-R3 power symbols preserved
- ✅ All four connected via global GND

## Likely Actual Result (Predictions)

**Prediction 1 - Power symbols lost during regeneration:**
- ❌ Phase 3: Power symbols revert to hierarchical labels
- ❌ User's manual work is lost
- ❌ Must manually re-add power symbols after every regeneration

**Prediction 2 - Mixed symbols and labels:**
- ❌ Phase 4: R4 gets hierarchical label
- ❌ R1-R3 have power symbols (if preserved)
- ❌ Inconsistent representation
- ⚠️  May or may not be electrically connected (KiCad may treat differently)

**Prediction 3 - Sync doesn't recognize power symbols:**
- ❌ Circuit-synth reads schematic, ignores power symbols
- ❌ Sees "missing" connections
- ❌ Re-adds hierarchical labels alongside power symbols
- ❌ Duplicate connection representations

## Why This Is CRITICAL

**This affects every circuit with power nets:**
- GND, VCC, +3.3V, +5V, etc. are in EVERY real circuit
- Users expect power symbols (KiCad standard practice)
- Hierarchical labels for power are incorrect semantics

**If power symbols aren't preserved:**
- Users must manually fix power connections after every regeneration
- Defeats the purpose of bidirectional sync
- Power nets don't have global semantics
- Schematic doesn't follow KiCad best practices

**Semantic difference matters:**
- Hierarchical label "GND" on sheet A doesn't connect to "GND" on sheet B
- Power symbol "GND" connects globally across ALL sheets
- For multi-sheet designs, this is a critical difference

## Success Criteria

This test PASSES when:
- User can replace hierarchical labels with power symbols
- Power symbols are preserved during regeneration
- New components added to power nets get power symbols (not labels)
- Global power symbol semantics maintained
- No manual re-work needed after regeneration

## Potential Solutions to Investigate

1. **Detect power nets by name pattern:**
   - If net name is "GND", "VCC", "+5V", "+3.3V", etc. → generate power symbol
   - Add configurable list of power net names

2. **Explicit Python API:**
   ```python
   gnd = PowerNet(name="GND")  # or
   gnd = Net(name="GND", type="power")
   ```

3. **Preserve user intent:**
   - If schematic has power symbol, keep it
   - Don't replace power symbols with hierarchical labels
   - Match existing connection style when adding components

4. **Bidirectional detection:**
   - Read KiCad schematic, detect power symbols
   - Import as PowerNet in Python
   - Generate power symbols when exporting

## Related Tests

- **Test 10-12** - Basic net operations (all use hierarchical labels)
- **Test 34** - Add component after power symbol replacement (future)
- **Test 35** - Generate power symbols from Python (future)

## Related Issues

- **#346** - Power symbol handling investigation (to be created)
- **#344** - Net sync doesn't add labels (also affects power symbols)
- **#345** - New component on net doesn't get labels

## Notes

**This test documents current behavior** - we don't know what will happen yet!

The test is designed to discover:
1. Does circuit-synth preserve user-added power symbols?
2. Does it recognize power symbols as part of a net?
3. What happens when mixing symbols and labels?
4. Is this a critical blocker for real-world usage?

## Edge Cases to Explore Later

- Multiple power nets (GND + VCC + +3.3V)
- Power flags vs power symbols
- PWR_FLAG symbols
- Hidden power pins on ICs
- Global labels vs power symbols
- Multi-sheet hierarchical designs
