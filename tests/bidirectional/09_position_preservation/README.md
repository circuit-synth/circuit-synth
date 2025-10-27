# Test 09: Manual Position Preservation (CRITICAL)

## What This Tests
Validates that manual position changes made in KiCad survive Python regeneration. This is THE killer feature for real-world usability.

## When This Situation Happens
- Developer generates KiCad from Python
- Manually arranges components in KiCad schematic editor for better layout
- Adds a new component in Python code
- Regenerates KiCad and expects manual layout work to be preserved
- If manual edits are lost, the tool becomes unusable for iterative development

## What Should Work
- Initial KiCad generation creates schematic with default positions
- Manual position edits in KiCad are detected when reimporting
- Adding new components in Python and regenerating preserves manual positions
- Only the new component gets auto-positioned; existing components stay put

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional/09_position_preservation

# Step 1: Generate initial KiCad project with R1
uv run single_resistor.py
open single_resistor/single_resistor.kicad_pro
# Note R1's default auto-placed position in KiCad

# Step 2: Manually move R1 in KiCad schematic editor
# In KiCad: Select R1 and drag to new position (e.g., center of page)
# Save schematic (Cmd+S), close KiCad

# Step 3: Edit single_resistor.py to add R2
# Add after R1 definition:
#   r2 = Component(symbol="Device:R", ref="R2", value="4.7k",
#                  footprint="Resistor_SMD:R_0603_1608Metric")

# Step 4: Regenerate KiCad from modified Python
uv run single_resistor.py

# Step 5: Open regenerated KiCad and verify position preservation
open single_resistor/single_resistor.kicad_pro
# Verify:
#   - R1 is still at manually-moved position (NOT at default)
#   - R2 appears at new auto-placed position
#   - Manual layout work preserved
```

## Expected Result

- ✅ Original KiCad generated with R1 at default position
- ✅ R1 manually moved in KiCad schematic editor
- ✅ R2 added in Python code
- ✅ Regenerated KiCad preserves R1's manual position
- ✅ R2 auto-placed without overlapping R1
- ✅ Manual layout work is NOT lost during regeneration

## Why This Is Critical

This is the killer feature that makes circuit-synth usable for real development. If manual positioning work is lost on every regeneration, developers won't use the tool. This test validates that the workflow truly supports iterative development: code in Python, arrange in KiCad, add more in Python, without losing your layout work.
