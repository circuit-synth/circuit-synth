# Test 13: Reference Change Position Preservation (Issue #369 FIX)

## What This Tests

**Core Question**: When you change a component's reference in Python code (R1 → R2) and regenerate KiCad, does the component stay at its manually-positioned location, or is it treated as a Remove+Add (losing position)?

This validates **UUID-based matching for reference changes** - the critical Issue #369 fix that makes component renaming work correctly without losing manual layout work.

## When This Situation Happens

- Developer generates KiCad with R1 from Python
- Manually moves R1 to a specific position in KiCad (e.g., coordinates 100, 50)
- Later decides to rename R1 to R2 in Python code (better naming)
- Regenerates KiCad from Python
- **Critical**: Does R1/R2 stay where it was manually placed, or does it move?

Before Issue #369 fix:
- Reference change treated as Remove R1 + Add R2
- Component position would be lost
- Sync would show "Remove: R1" and "Add: R2"

After Issue #369 fix (UUID matching):
- Reference change treated as Update (same component, different reference)
- Position preserved via UUID matching
- Component stays at manually-placed location

## What Should Work

1. Generate KiCad with R1 → R1 appears at auto-generated position
2. Manually move R1 to (100, 50) in KiCad schematic editor
3. Change reference in Python code: R1 → R2 → regenerate
4. **R1/R2 stays at (100, 50)** - position preserved via UUID matching (not Remove+Add)
5. Component reference successfully updated to R2
6. UUID-based matching recognizes it's the same component, just renamed

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth2/tests/bidirectional/13_rename_component

# Step 1: Generate initial KiCad project with R1
uv run single_resistor.py
# Verify: single_resistor/single_resistor.kicad_sch created with R1

# Step 2: Manually move R1 to specific position in KiCad
# Open schematic in KiCad:
open single_resistor/single_resistor.kicad_pro
# - Select R1 component
# - Note its default auto-placed position
# - Drag R1 to position (100, 50) - any visible position change
# - Save schematic (Cmd+S), close KiCad

# Step 3: Edit single_resistor.py to change reference
# Change: ref="R1" to ref="R2"
# Save file

# Step 4: Regenerate KiCad from modified Python
uv run single_resistor.py

# Step 5: Open regenerated KiCad and verify position preservation
open single_resistor/single_resistor.kicad_pro
# Verify:
#   - Component is now named R2 (reference updated)
#   - Component is still at (100, 50) - position NOT reset!
#   - UUID-based matching worked (same component, renamed)
```

## Expected Result

- ✅ Original KiCad generated with R1 at default position
- ✅ R1 manually moved to (100, 50) in KiCad schematic editor
- ✅ Reference changed R1 → R2 in Python code
- ✅ Regenerated KiCad updates reference to R2
- ✅ **Position preserved at (100, 50)** - NOT reset to default!
- ✅ UUID-based matching recognized it's the same component
- ✅ No "Remove R1 + Add R2" behavior (that would lose position)

## Why This Is Critical

**The Iterative Development Workflow:**
1. Write circuit in Python → generate KiCad
2. Arrange components nicely in KiCad (spend time on layout)
3. Realize component naming needs improvement → rename in Python
4. Regenerate KiCad

**If positions are NOT preserved (before Issue #369 fix):**
- All your layout work is lost (component moves back to default)
- Reference change treated as Remove+Add instead of Update
- Component appears to move when only reference changed
- Users can't rename components mid-development without losing layout

**If positions ARE preserved (after Issue #369 fix via UUID matching):**
- Component stays where you manually placed it
- Only the reference is updated
- Layout work is preserved across reference changes
- Users can refactor naming without re-doing layout
- Bidirectional sync becomes truly usable for real development

**This is THE fix that makes component renaming work correctly in bidirectional sync.**

## Success Criteria

This test PASSES when:
- Component generates with auto-placed position
- Manual position change in KiCad is preserved in file (100, 50)
- Reference change in Python (R1 → R2) is accepted
- Regenerated KiCad shows: new reference (R2) at original manual position (100, 50)
- UUID-based matching works (not Remove+Add)
- No position loss during reference change
