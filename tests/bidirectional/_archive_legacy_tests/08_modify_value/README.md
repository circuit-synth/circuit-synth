# Test 08: Modify Component Attributes + Position Preservation

## What This Tests
Validates that changing component attributes (value, footprint, reference) in KiCad
correctly syncs to Python while preserving the component's position (canonical position).

Tests both:
1. **Attribute synchronization** - value, footprint, reference changes sync to Python
2. **Position preservation** - manually moved position in KiCad is preserved

## When This Situation Happens
- Developer generates circuit from Python (R1 at default position)
- Opens KiCad and manually moves R1 to better location
- Changes R1 attributes in KiCad (value: 10k→4.7k, footprint: 0603→0805, ref: R1→R10)
- Re-imports to Python to sync changes
- Regenerates KiCad - position should be preserved, attributes should match

## What Should Work
1. Generate KiCad with R1 (10k, 0603, R1) at default position
2. In KiCad: move R1 to new position (e.g., x=100, y=50)
3. In KiCad: change R1 attributes (value→4.7k, footprint→0805, ref→R10)
4. Import KiCad back to Python (sync changes)
5. Regenerate KiCad from updated Python
6. Verify: R10 at preserved position with new attributes

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional/08_modify_value

# Step 1: Generate initial KiCad project (R1, 10k, 0603)
uv run single_resistor.py
open single_resistor/single_resistor.kicad_pro

# Step 2: In KiCad schematic editor:
#   - Move R1 to new position (e.g., x=100mm, y=50mm)
#   - Change value: 10k → 4.7k
#   - Change footprint: R_0603_1608Metric → R_0805_2012Metric
#   - Change reference: R1 → R10
#   - Save (Cmd+S)
#   - Note the position where you moved it
# Close KiCad

# Step 3: Import KiCad back to Python (sync changes)
uv run kicad-to-python single_resistor single_resistor.py

# Step 4: Verify Python code updated
cat single_resistor.py
# Should show: ref="R10", value="4.7k", footprint="R_0805_2012Metric"

# Step 5: Regenerate KiCad from updated Python
uv run single_resistor.py

# Step 6: Open regenerated KiCad and verify
open single_resistor/single_resistor.kicad_pro
# Verify:
#   - Reference is R10 (not R1)
#   - Value is 4.7k (not 10k)
#   - Footprint is 0805 (not 0603)
#   - Position is preserved (same x=100, y=50 you set in step 2)
```

## Expected Result

- ✅ Initial KiCad has R1 with value 10k, footprint 0603, at default position
- ✅ After moving and changing attributes in KiCad, import updates Python code
- ✅ Python code shows: ref="R10", value="4.7k", footprint="0805"
- ✅ Regenerating from Python preserves the moved position
- ✅ Regenerated KiCad has R10 at same position with all new attributes
- ✅ Tests both attribute sync AND position preservation (canonical)
