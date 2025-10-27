# Test 15: Move Component to New Position

## What This Tests
Validates that changing a component's position in Python code correctly updates the position in the regenerated KiCad schematic.

## When This Situation Happens
- Developer has positioned component at specific coordinates
- Decides to reorganize schematic layout
- Modifies position coordinates in Python code
- Regenerates KiCad expecting component at new location

## What Should Work
- Original component positioned at (100, 100, 0)
- Python code modified to move component to (200, 150, 45)
- Regenerated KiCad shows component at new coordinates
- Rotation angle updated correctly to 45 degrees

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional/15_move_component

# Step 1: Generate initial circuit with positioned resistors
uv run positioned_resistor.py
open positioned_resistor/positioned_resistor.kicad_pro
# Verify: R1 at (100.0, 100.0, 0°), R2 at (150.0, 100.0, 90°)

# Step 2: Import to Python
uv run kicad-to-python positioned_resistor imported.py

# Step 3: Edit imported.py to modify R1 position
# Change: at=(100.0, 100.0, 0) → at=(200.0, 150.0, 45)

# Step 4: Regenerate KiCad from modified Python
uv run imported.py

# Step 5: Open regenerated KiCad project
open positioned_resistor/positioned_resistor.kicad_pro
# Verify:
#   - R1 now at (200.0, 150.0, 45°) - NEW position
#   - R2 still at (150.0, 100.0, 90°) - UNCHANGED
#   - Both components have correct values and footprints
```

## Expected Result

- ✅ Initial KiCad project has R1 at (100.0, 100.0, 0°)
- ✅ Python import successful (imported.py created)
- ✅ Modified position in Python: R1 at=(200.0, 150.0, 45)
- ✅ Regenerated KiCad shows R1 at new position (200.0, 150.0, 45°)
- ✅ R1 rotation angle correctly updated to 45 degrees
- ✅ R2 position unchanged (150.0, 100.0, 90°)
- ✅ Component properties (value, footprint) preserved

## Why This Is Important

Developers need to programmatically control component placement. Modifying position coordinates in Python should reliably update the KiCad schematic layout without affecting other component properties.
