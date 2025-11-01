# Test 09: Position Preservation When Adding Components (CRITICAL)

## What This Tests

**Core Question**: When you add a second component (R2) to Python code and regenerate KiCad, does the first component (R1) stay at its manually-positioned location, or does it get moved back to a default position?

This validates that **existing component positions are preserved** when adding new components during iterative development.

## When This Situation Happens

- Developer generates KiCad with R1 from Python
- Manually moves R1 to a better position in KiCad (e.g., center of page)
- Later adds R2 to the Python code
- Regenerates KiCad from Python
- **Critical**: Does R1 stay where it was manually placed, or does it move?

## What Should Work

1. Generate KiCad with R1 → R1 appears at auto-generated position
2. Manually move R1 in KiCad → R1 now at new position
3. Add R2 to Python code → regenerate
4. **R1 stays at manually-moved position** (not reset to default!)
5. R2 auto-placed in available space (doesn't overlap R1)

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

**The Iterative Development Workflow:**
1. Write circuit in Python → generate KiCad
2. Arrange components nicely in KiCad (spend 10 minutes on layout)
3. Add more components in Python → regenerate

**If positions are NOT preserved:**
- All your layout work is lost (R1 moves back to default)
- You have to re-arrange components after every regeneration
- The tool becomes unusable for real development
- Users won't adopt circuit-synth

**If positions ARE preserved:**
- R1 stays where you put it
- Only new R2 gets auto-placed
- Layout work is incremental, not repetitive
- The tool becomes a joy to use

**This is THE killer feature** that makes bidirectional sync valuable.
