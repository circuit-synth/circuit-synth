# Test 21: Position Preservation After Manual Move

## What This Tests

When a user manually moves a component in KiCad and then regenerates from Python, the manual position should be preserved (not reset to auto-generated position).

## When This Situation Happens

- User generates KiCad from Python
- Opens KiCad and manually repositions component to desired location
- Makes changes to Python code (adds components, changes values, etc.)
- Regenerates KiCad from Python
- Expects manually-positioned component to stay in same location

## What Should Work

1. Generate initial KiCad project from Python
2. Open KiCad, manually move R1 to new position
3. Save and close KiCad
4. Regenerate from Python (same or modified circuit)
5. Open KiCad again
6. R1 should still be at manually-moved position (NOT reset to default)

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional/21_position_preservation_move

# Step 1: Generate initial KiCad project
uv run resistor_with_position.py

# Step 2: Open in KiCad and note R1's initial position
open resistor_with_position/resistor_with_position.kicad_pro
# Note: R1 will be at auto-generated position (e.g., x=40.6, y=55.9)

# Step 3: In KiCad schematic editor:
#   - Click and drag R1 to a new position (e.g., move to center of page)
#   - Note the new position coordinates in the status bar
#   - Save the schematic (Cmd+S)
#   - Close KiCad

# Step 4: Regenerate from Python (simulates making changes)
uv run resistor_with_position.py

# Step 5: Open KiCad again
open resistor_with_position/resistor_with_position.kicad_pro

# Step 6: Verify R1 is at the manually-moved position
#   - R1 should be where you moved it in Step 3
#   - R1 should NOT be back at the auto-generated position
```

## Expected Result

- ✅ R1 initially placed at auto-generated position (e.g., x=40.6, y=55.9)
- ✅ After manual move, R1 at new position (e.g., x=100, y=100)
- ✅ After regeneration, R1 still at manually-moved position
- ✅ Manual layout work is preserved across Python regenerations

## Why This Is Critical

Users spend time laying out components in KiCad. If regenerating from Python resets all positions, users lose their layout work. This makes the bidirectional workflow unusable for real projects.

## Related

This is the core feature that enables non-destructive Python → KiCad updates.
