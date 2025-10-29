# Test 09: Board Outline Definition

## What This Tests

Custom board outline definition - the ability to define non-rectangular PCB shapes (L-shaped, T-shaped, or other custom forms) in Python, generate them, and modify them while preserving component placement.

## When This Situation Happens

- Designing boards that must fit specific enclosures (phone, camera, GPS)
- Creating modular interface boards with custom shapes
- Optimizing PCB size for mechanical constraints
- Designing antenna boards with specific geometries
- Creating sensor boards that fit specific application form factors
- Panelization planning (outline affects manufacturing costs)

## What Should Work

1. Board outline can be defined as list of (x, y) coordinate points
2. PCB generation respects custom outline geometry
3. Edge.Cuts layer contains correct outline geometry
4. Outline coordinates can be extracted and verified
5. Outline can be modified in Python code
6. PCB regeneration applies new outline shape
7. Component placement is preserved despite outline changes
8. Multiple shape types work (L-shape, T-shape, rounded corners)

## Why This Matters

**Custom form factors are essential for real-world design:**
- **Cost optimization**: Board outline affects panelization and routing costs
- **Enclosure constraints**: Board must physically fit the product case
- **Mechanical assembly**: Outline defines mounting points and edge connectors
- **Manufacturing planning**: Complex outlines may require extra panelization setup
- **Design flexibility**: Ability to iterate on outline without losing component placement

Without custom outlines, tool only works for rectangular boards - severely limiting real applications.

## Validation Approach

**Level 2: kicad-pcb-api Structural Validation**

```python
from kicad_pcb_api import PCBBoard

# Initial PCB with L-shaped outline
pcb = PCBBoard.load(str(pcb_file))

# Validate Edge.Cuts layer has outline
assert len(pcb.edges) > 0  # Outline exists

# Extract outline coordinates from PCB file
import re
pattern = r'\(gr_line\s+\(start\s+([\d.-]+)\s+([\d.-]+)\)\s+\(end\s+([\d.-]+)\s+([\d.-]+)\).*?Edge\.Cuts'
segments = []
for match in re.finditer(pattern, content):
    x1, y1, x2, y2 = map(float, match.groups())
    segments.append(((x1, y1), (x2, y2)))

assert len(segments) >= 5  # L-shape has 6 points = at least 5 segments

# Modify outline to T-shape
# Regenerate PCB
# Verify new outline has different geometry
pcb_updated = PCBBoard.load(str(pcb_file))
new_segments = extract_outline_segments(pcb_file)
assert len(new_segments) != len(segments)  # Geometry changed
```

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth3/tests/pcb_generation/09_board_outline_definition

# Generate PCB with L-shaped outline
uv run fixture.py

# Check files created
ls -la custom_outline_pcb/

# Open in KiCad - should show L-shaped board
open custom_outline_pcb/custom_outline_pcb.kicad_pro

# In KiCad PCB editor:
# - View → Show layers → Enable Edge.Cuts
# - Should see L-shaped outline
# - Can zoom and measure outline
```

## Expected Result

- ✅ KiCad project generated (.kicad_pro)
- ✅ PCB file generated (.kicad_pcb)
- ✅ PCB opens successfully in KiCad
- ✅ Board outline visible:
  - Initial outline: L-shaped (100x40mm horizontal + 40x50mm vertical)
  - After modification: T-shaped or other custom form
- ✅ Edge.Cuts layer contains outline geometry
- ✅ Coordinates can be extracted and verified
- ✅ Multiple shape modifications work
- ✅ Component placement preserved through outline changes

## Test Output Example

```
======================================================================
STEP 1: Generate PCB with L-shaped outline
======================================================================
✅ Step 1: PCB with L-shaped outline generated

======================================================================
STEP 2: Validate Edge.Cuts outline geometry
======================================================================
✅ Step 2: Edge.Cuts outline geometry validated
   - Found 6 lines + 0 curves

======================================================================
STEP 3: Extract outline coordinates
======================================================================
✅ Step 3: Outline extracted from PCB file
   - Found 6 edge segments
   - First segment: ((0.0, 0.0), (100.0, 0.0))
   - Last segment: ((0.0, 90.0), (0.0, 0.0))

======================================================================
STEP 4: Verify outline geometry
======================================================================
✅ Step 4: Outline geometry verified
   - Expected 6 points for L-shape
   - Found 6 segments ✓

======================================================================
STEP 5: Modify board outline to T-shape
======================================================================
✅ Step 5: Board outline modified to T-shape

======================================================================
STEP 6: Regenerate PCB with T-shaped outline
======================================================================
✅ Step 6: PCB regenerated with T-shaped outline

======================================================================
STEP 7: Validate T-shaped outline
======================================================================
✅ Step 7: New outline validated
   - T-shape has 12 segments
   - Outline successfully modified and regenerated ✓

======================================================================
✅ TEST PASSED: Board Outline Definition
======================================================================
```

## Key Validation Points

| Aspect | Validation | Expected |
|--------|-----------|----------|
| **Outline Definition** | Board outline points in Python | List of (x, y) tuples |
| **PCB File Valid** | kicad-pcb-api.load() | Loads without error |
| **Edge.Cuts Present** | Edge.Cuts layer exists | Found in PCB file |
| **Segment Count** | L-shape outline segments | ≥5 segments (6 points) |
| **Coordinate Extraction** | Extract points from PCB | Matches original definition |
| **Outline Modification** | Change outline shape | T-shape generated correctly |
| **Geometry Change** | New shape has different geometry | Segment count or points differ |
| **Component Preservation** | Components survive outline change | Positions preserved |

## Test Classification

- **Category**: Board Management Test
- **Priority**: HIGH - Custom form factors essential for real designs
- **Validation Level**: Level 2 (kicad-pcb-api structural validation)
- **Complexity**: Medium (outline geometry, shape modification)
- **Execution Time**: ~5 seconds

## Common PCB Shapes

### L-Shaped
```
┌─────────┐
│    A    │
└────┐    │
     │  B │
     └────┘
```
- Horizontal section (A): Main electronics
- Vertical section (B): Interface connector

### T-Shaped
```
  ┌──────┐
  │  A   │
┌─┴──────┴─┐
│    B     │
└───────────┘
```
- Horizontal bar (A): Top electronics
- Vertical stem (B): Bottom connector or display

### Custom Shapes
- Rounded corners (for enclosure fit)
- Notches (for connector cutouts)
- Irregular shapes (for mechanical alignment)

## Manufacturing Implications

### Outline Complexity Impact on Cost

| Complexity | Features | Cost Impact | Typical Use |
|-----------|----------|-----------|-----------|
| **Minimal** | Simple rectangle | Baseline | Reference designs |
| **Low** | Small notch or rounded corner | +5-10% | Consumer electronics |
| **Medium** | L-shape or T-shape | +15-25% | Modular boards |
| **High** | Complex custom shape | +30-50% | Specialized applications |

### Panelization

- Simple rectangular boards: High panelization density
- Custom shapes: Lower density, more material waste
- Panelization costs depend on shape complexity
- Outline affects V-score placement for separation

## Design Best Practices

1. **Minimize complexity** - Simpler outlines = lower cost
2. **Round external corners** - Safer for users, easier manufacturing
3. **Plan notches early** - For connectors, displays, antennas
4. **Consider panelization** - Talk to manufacturer about your outline
5. **Add fiducials** - Reference marks for manufacturing
6. **Plan test points** - In non-blocked areas
7. **Document outline** - Clear specification for manufacturer

## Notes

- Outline defined as list of (x, y) points in mm
- Points should form closed polygon
- Edge.Cuts layer is standard KiCad layer for board outline
- Some manufacturers may charge extra for complex shapes
- Panelization planning affects final cost significantly
- Prototype boards may support shapes mass production cannot
