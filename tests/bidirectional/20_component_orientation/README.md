# Test 20: Component Orientation (Rotation) Preservation

## What This Tests

**Core Question**: When you rotate a component in KiCad (e.g., R1 from 0° → 90°), does the component's position stay the same while only the rotation changes?

This validates that **component orientation changes are tracked independently from position**, so rotation doesn't unexpectedly move components during iterative development.

## When This Situation Happens

- Developer generates KiCad with R1 at 0° rotation (default)
- Opens in KiCad and rotates R1 to 90° for better board layout
- Later adds new components or regenerates from Python
- **Critical**: Is R1's position preserved while maintaining 90° rotation?
- Does rotation affect position coordinates, or are they independent?

## What Should Work

1. Generate KiCad with R1 at 0° rotation → R1 at position (x, y) with 0° angle
2. Manually rotate R1 to 90° in KiCad → R1 at same position (x, y) with 90° angle
3. Verify R1's position hasn't changed
4. Add R2 or modify circuit and regenerate
5. **R1 should maintain both**:
   - Position: (x, y) - unchanged
   - Rotation: 90° - preserved (not reset to 0°)

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth2/tests/bidirectional/20_component_orientation

# Step 1: Generate initial KiCad project with R1 at 0° rotation
uv run single_resistor.py
open single_resistor/single_resistor.kicad_pro

# Note: R1 at default 0° rotation and auto-placed position
# In KiCad schematic view, you can see component orientation

# Step 2: Rotate R1 to 90° in KiCad schematic editor
# - Select R1 component
# - Right-click → Rotate → 90° (or use Ctrl+R)
# - Save schematic (Cmd+S), close KiCad

# Step 3: Verify rotation change via kicad-sch-api
# python3 verify_rotation.py
# Should show: R1 rotation = 90 degrees

# Step 4: Add R2 to Python code and regenerate
# - Edit single_resistor.py to add R2 after R1
# - uv run single_resistor.py

# Step 5: Verify both position and rotation preserved
open single_resistor/single_resistor.kicad_pro
# Verify:
#   - R1 still at original position (not moved by rotation)
#   - R1 still at 90° rotation (not reset to 0°)
#   - R2 auto-placed without overlap
```

## Expected Result

- ✅ R1 generates at 0° rotation and auto-placed position
- ✅ R1 manually rotated to 90° in KiCad
- ✅ Position preserved after rotation (no unexpected movement)
- ✅ Rotation preserved when adding new components
- ✅ Rotation angle property (component.rotation) accessible via kicad-sch-api

## Why This Is Important

**Board Layout Considerations:**
- Component orientation affects PCB routing and layout efficiency
- Rotating components is common practice for better board design
- Users expect rotation to NOT affect component position (position is independent)

**Development Workflow:**
- If rotation resets during regeneration, manual layout work is lost
- If rotation affects position, component movement becomes unpredictable
- Orientation should be preserved alongside position during iterative development

**Validation Importance:**
- Ensures rotation property is properly tracked in schematics
- Validates kicad-sch-api can read and verify rotation angles
- Critical for future PCB layout optimization features

## Automation Test Focus

This test emphasizes **Level 2 semantic validation** using kicad-sch-api:
- Load schematic file with kicad-sch-api
- Access component.rotation property (in degrees or radians)
- Verify rotation values after manual modification
- Validate rotation persistence through regeneration cycles
