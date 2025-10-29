# Test 30: Component Missing Footprint Assignment (GRACEFUL HANDLING)

## What This Tests

**Core Question**: When a component is defined WITHOUT a footprint assignment (footprint=""), does circuit-synth handle it gracefully, allowing the component to be added to the schematic and later assigned a footprint without losing position or causing errors?

This validates **graceful handling of incomplete components** - a very common scenario during early circuit design when footprints aren't yet chosen.

## When This Situation Happens

- Developer starts circuit design with component structure (symbols only)
- Doesn't yet know which footprint to use (evaluating options)
- Defines components with `footprint=""` or `footprint=None` as placeholder
- Later decides on footprint and adds it to Python code
- Regenerates KiCad expecting component to show footprint assignment

## What Should Work

1. Generate KiCad with component having no footprint (footprint="")
2. Verify component appears in schematic correctly (just no footprint field)
3. Component position is assigned and can be manually adjusted
4. Edit Python to add footprint assignment
5. Regenerate KiCad project
6. Verify footprint now appears in KiCad schematic
7. Verify position was preserved during footprint addition

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth2/tests/bidirectional/30_component_missing_footprint

# Step 1: Generate initial KiCad project (no footprint)
uv run component_no_footprint.py
open component_no_footprint/component_no_footprint.kicad_pro
# Verify: R1 component visible but NO footprint field assigned
# Note the auto-placed position

# Step 2: Manually move R1 in KiCad (optional but good verification)
# In KiCad: Select R1 and drag to new position
# Save schematic (Cmd+S), close KiCad

# Step 3: Edit component_no_footprint.py to add footprint
# Change: footprint=""
# To: footprint="Resistor_SMD:R_0603_1608Metric"
# Save file

# Step 4: Regenerate KiCad project with footprint
uv run component_no_footprint.py

# Step 5: Open regenerated KiCad project
open component_no_footprint/component_no_footprint.kicad_pro
# Verify:
#   - Component still visible at same position (or manual position if moved)
#   - Footprint field now populated with "Resistor_SMD:R_0603_1608Metric"
#   - No errors or warnings
#   - Component can be used in PCB design
```

## Expected Result

- ✅ Initial generation: Component appears without footprint assignment
- ✅ No errors or warnings when footprint is missing
- ✅ Component position auto-assigned and can be adjusted manually
- ✅ After adding footprint in Python: footprint field appears in schematic
- ✅ Position preserved when footprint is added
- ✅ Footprint field shows correct value (Resistor_SMD:R_0603_1608Metric)
- ✅ No duplicate components created
- ✅ Component is usable for PCB design with footprint assigned

**Note**: Uses `kicad-sch-api` to verify `.footprint` property exists and has correct value

## Why This Is Important

**Common Real-World Development Scenario:**

1. Start circuit design with symbol layout (no footprints yet)
   - Just checking if circuit topology works
   - Don't want to commit to specific footprints
   - Want flexibility to try different options

2. Review and refine circuit in KiCad
   - Manually arrange components
   - Verify electrical connections
   - Adjust layout

3. Add footprint information when manufacturing details are decided
   - Choose specific SMD package (0603 vs 0805)
   - Update Python code with footprint
   - Regenerate KiCad

**If missing footprints cause errors:**
- Developers can't start with symbol-only designs
- Must have all metadata upfront
- Makes iterative design workflow impossible
- Tool becomes unusable for real development

**If missing footprints are handled gracefully:**
- Start with symbols, add details later
- Component placement not blocked by missing footprint
- Layout work is preserved when footprint added
- Matches real design workflow perfectly
- Makes circuit-synth suitable for professional design

**This test validates that circuit-synth supports real design workflows**, not just ideal scenarios with complete metadata.

## Success Criteria

This test PASSES when:
- Component with footprint="" generates without errors
- Component appears in schematic with placeholder or empty footprint field
- Component can be positioned/moved manually in KiCad
- Adding footprint in Python code is accepted
- Regenerated KiCad shows footprint field populated
- Position preserved when footprint is added
- No duplicate components or sync errors
- Component is valid for PCB manufacturing after footprint added
