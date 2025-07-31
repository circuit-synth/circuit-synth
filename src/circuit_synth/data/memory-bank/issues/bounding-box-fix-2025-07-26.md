# Bounding Box Calculation Fix - 2025-07-26

## Issue Summary
Components in generated KiCad schematics were overlapping due to failed bounding box calculations, preventing proper collision detection and component spacing.

## Root Cause
The `SymbolBoundingBoxCalculator` class was looking for a `shapes` key in symbol data, but the actual KiCad symbol cache data uses a `graphics` key instead.

## Files Changed
- `src/circuit_synth/kicad/sch_gen/symbol_geometry.py` - Fixed data structure handling
- `src/circuit_synth/core/circuit.py` - Added `draw_bounding_boxes` parameter to API

## Technical Details

### Symbol Data Structure Issue
```python
# Before (broken)
shapes = symbol_data.get('shapes', [])

# After (fixed) 
shapes = symbol_data.get('shapes', []) or symbol_data.get('graphics', [])
```

The KiCad symbol cache actually stores graphical elements under the `graphics` key, not `shapes`. This caused the bounding box calculator to find no geometry and fail to calculate proper dimensions.

### API Enhancement
Added `draw_bounding_boxes` parameter to enable visual debugging:

```python
# New API usage
circuit.generate_kicad_project("project_name", draw_bounding_boxes=True)
```

## Verification
- ✅ Bounding box calculations now work: `Device:C: 10.00mm x 32.02mm`
- ✅ Components are properly spaced with no overlaps
- ✅ Visual bounding boxes can be enabled for debugging
- ✅ Collision detection functions correctly

## Impact
- Resolves component overlap issues in all generated schematics
- Enables proper component spacing and collision detection
- Provides visual debugging capability for placement algorithms
- Improves overall quality of generated KiCad projects

## Testing
Verified with the `example_kicad_project.py` circuit showing proper component spacing and optional visual bounding boxes.