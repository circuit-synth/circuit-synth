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
# Verify: schematic has R1 at default position
# Note: Record R1's position coordinates (shown in KiCad properties)

# Step 2: Manually move R1 in KiCad schematic editor
# Open single_resistor/single_resistor.kicad_sch in KiCad
# Select R1 and move it to a new position (e.g., drag 50mm to the right)
# Save the schematic in KiCad
# Note: Record R1's new position coordinates

# Step 3: Import the manually-edited KiCad back to Python
uv run kicad-to-python single_resistor -o imported_with_moved_r1.py

# Step 4: Verify imported Python captured the manual position
# Open imported_with_moved_r1.py
# Check that R1 has position coordinates matching the manual edit

# Step 5: Add R2 component to the imported Python
# Edit imported_with_moved_r1.py to add:
#   r2 = Component(symbol="Device:R", ref="R2", value="4.7k",
#                  footprint="Resistor_SMD:R_0603_1608Metric")

# Step 6: Regenerate KiCad from modified Python
uv run imported_with_moved_r1.py

# Step 7: Open regenerated KiCad project
# Open the KiCad project generated from imported_with_moved_r1.py
# Verify:
#   - R1 is still at the manually-positioned location (not default)
#   - R2 appears at a new auto-generated position
#   - R1's manual position was preserved through the cycle
```

## Expected Result

- ✅ Original KiCad generated with R1 at default position
- ✅ R1 manually moved in KiCad schematic editor
- ✅ Manual position captured when importing to Python
- ✅ R2 added in Python code
- ✅ Regenerated KiCad preserves R1's manual position
- ✅ R2 placed at new position without overlapping R1
- ✅ Manual layout work is NOT lost during regeneration

## Why This Is Critical

This is the killer feature that makes circuit-synth usable for real development. If manual positioning work is lost on every regeneration, developers won't use the tool. This test validates that the workflow truly supports iterative development: code in Python, arrange in KiCad, add more in Python, without losing your layout work.
