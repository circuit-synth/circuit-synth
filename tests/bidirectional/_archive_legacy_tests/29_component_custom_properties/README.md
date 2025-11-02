# Test 29: Custom Component Properties (DNP, MPN, Tolerance)

## What This Tests

**Core Question**: When you define custom properties on a component (DNP status, MPN, Tolerance), are those properties preserved when generating KiCad and regenerating after modifications?

This validates that **custom component properties are properly stored and synchronized** between Python and KiCad, essential for BOM generation and manufacturing workflows.

## When This Situation Happens

- Engineer creates components with manufacturing properties (MPN, Tolerance, DNP status)
- Generates KiCad project with these properties embedded in component metadata
- Later modifies properties (change MPN, toggle DNP) in Python code
- Regenerates KiCad expecting properties to update
- BOM generation requires these properties to be correct and accessible

## What Should Work

1. Generate KiCad with component having custom properties:
   - `DNP=true` (Do Not Populate)
   - `MPN="LM358"` (Manufacturer Part Number)
   - `Tolerance="1%"`
2. Verify properties exist in KiCad schematic (kicad-sch-api access)
3. Modify properties in Python code (change MPN to "LM358N", toggle DNP to false)
4. Regenerate KiCad from modified Python
5. Validate property changes reflected in KiCad
6. Validate component position preserved during modification

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth2/tests/bidirectional/29_component_custom_properties

# Step 1: Generate initial KiCad project with custom properties
uv run component_with_properties.py
# Verify: component_with_properties/component_with_properties.kicad_sch created with U1

# Step 2: Open in KiCad and inspect properties
open component_with_properties/component_with_properties.kicad_pro
# - Select U1 component
# - Open Properties panel (right-click → Properties)
# - Verify custom properties appear:
#   - DNP: true
#   - MPN: LM358
#   - Tolerance: 1%
# - Note component position
# - Close KiCad

# Step 3: Edit component_with_properties.py to modify properties
# Change:
#   - MPN from "LM358" to "LM358N"
#   - DNP from True to False
#   - Tolerance from "1%" to "2%"

# Step 4: Regenerate KiCad from modified Python
uv run component_with_properties.py

# Step 5: Open regenerated KiCad and verify property changes
open component_with_properties/component_with_properties.kicad_pro
# Verify:
#   - U1 component still present
#   - Custom properties updated:
#     - DNP: false (toggled)
#     - MPN: LM358N (updated)
#     - Tolerance: 2% (updated)
#   - Component position preserved (didn't move)
```

## Expected Result

- ✅ Initial generation: Component with custom properties created
- ✅ Properties accessible in KiCad schematic editor
- ✅ Custom properties stored correctly (DNP, MPN, Tolerance)
- ✅ Property modifications in Python reflected in regenerated KiCad
- ✅ Component position preserved across regeneration
- ✅ All properties remain accessible for BOM generation
- ✅ No duplicate components or property conflicts

## Why This Is Critical

**Manufacturing and BOM Workflow:**
1. Design circuit in Python with component properties (MPN, Tolerance, DNP)
2. Generate KiCad project with embedded properties
3. Later update properties (supplier changes, tolerance optimization)
4. Regenerate KiCad → properties must update correctly
5. BOM tools extract properties from KiCad → must be accurate

**If properties are NOT preserved:**
- Custom properties lost during generation (BOM generation fails)
- Engineers must manually re-enter properties in KiCad (error-prone)
- Circuit-synth cannot support full design workflow
- Properties not synchronized between Python and KiCad

**If properties ARE preserved:**
- Properties persist through generation and regeneration
- BOM generation can access accurate property data
- Engineers can manage properties in Python, reflect in KiCad
- Full bidirectional sync enables real manufacturing workflow

**This is THE foundation for automated BOM generation and manufacturing support.**

## Success Criteria

This test PASSES when:
- Component generates with custom properties (DNP, MPN, Tolerance)
- Properties accessible via kicad-sch-api component.properties
- Properties remain in KiCad schematic file after generation
- Modifying properties in Python updates them in regenerated KiCad
- Component position preserved across property modifications
- No data loss or property conflicts during sync
- All properties remain accessible for downstream tools (BOM generators)

## Test Pattern (Level 2 Semantic Validation)

Uses:
- kicad-sch-api to load schematic and access component properties
- Property mutation (change MPN, toggle DNP) to test modification
- Position verification to ensure UUID-based identity preserved
- Multiple regeneration cycles to test consistency
