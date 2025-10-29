# PRD: Fix Hierarchical Label Orientation Bug in Synchronizer

## Problem Statement

When the synchronizer adds hierarchical labels to component pins (during bidirectional sync operations like changing pin connections), the labels are placed with incorrect orientations. This causes visual inconsistency where labels on similar components point in opposite directions.

### Visual Evidence

In test `12_change_pin_connection`, when NET1 is moved from R2 pin 1 to R2 pin 2:
- R1 pin 1 label (NET1): orientation 90° (pointing UP)
- R2 pin 2 label (NET1): orientation 270° (pointing DOWN)

Both resistors are oriented identically (0° rotation), but their labels point in opposite directions, creating visual confusion.

## Root Cause Analysis

### Investigation Process (8 Cycles)

**Cycle 1-2: Understanding the Issue**
- Examined screenshot showing opposite label orientations on R1 and R2
- Located synchronizer code that adds hierarchical labels
- Found that synchronizer uses `GeometryUtils.calculate_pin_label_position_from_dict()`

**Cycle 3-5: Comparing Implementations**
- Initial placement code (schematic_writer.py:1252-1253):
  ```python
  pin_angle = float(pin_dict.get("orientation", 0.0))
  label_angle = (pin_angle + 180) % 360
  global_angle = (label_angle + comp.rotation) % 360
  ```

- Synchronizer code (synchronizer.py:582):
  ```python
  pin_dict = {
      "x": float(pin_position.x),
      "y": float(pin_position.y),
      "orientation": float(pin.rotation if hasattr(pin, 'rotation') else 0.0),  # BUG!
  }
  ```

**Cycle 6-8: Root Cause Identified**

The bug is on line 582 of `synchronizer.py`. The code uses:
```python
pin.rotation if hasattr(pin, 'rotation') else 0.0
```

However, `SchematicPin` objects (from kicad-sch-api) use the attribute `rotation`, NOT `orientation`. The attribute name is correct, but the **fallback to 0.0 is being triggered** because the code is checking for the existence of `rotation` attribute, finding it, but then the actual pin orientation value might not be set correctly.

**Actually, let me re-examine this more carefully:**

Looking at `kicad_sch_api/core/types.py:148`:
```python
rotation: float = 0.0  # Rotation in degrees
```

The `SchematicPin` class DOES have a `rotation` attribute. So the issue might be:

1. **Data source mismatch**:
   - Initial placement uses `SymbolLibCache.get_symbol_data()` → returns dict with "orientation" key
   - Synchronizer uses `symbol_cache.get_symbol()` → returns `SchematicPin` object with `rotation` attribute

2. **Semantic confusion**: The symbol library data uses "orientation" to mean the pin's directional angle (0°, 90°, 180°, 270°), while `SchematicPin.rotation` might mean something different, or the data isn't being populated correctly.

### Verification Needed

The synchronizer gets pin data from:
```python
symbol_cache = get_symbol_cache()
symbol_def = symbol_cache.get_symbol(kicad_component.lib_id)
pin = [p for p in symbol_def.pins if str(p.number) == str(pin_number)][0]
```

We need to verify what value `pin.rotation` contains for Device:R pins.

## Expected Behavior

For Device:R symbol (vertical resistor at 0° component rotation):
- Pin 1 is at (0, -3.81) with orientation 90° (points UP)
- Pin 2 is at (0, 3.81) with orientation 270° (points DOWN)

When the synchronizer adds labels, it should use the EXACT same calculation as initial placement:
```python
label_angle = (pin_orientation + 180) % 360
global_angle = (label_angle + component_rotation) % 360
```

For R1 pin 1:
- pin_orientation = 90°
- label_angle = (90 + 180) % 360 = 270°
- global_angle = (270 + 0) % 360 = 270°

For R2 pin 2:
- pin_orientation = 270°
- label_angle = (270 + 180) % 360 = 90°
- global_angle = (90 + 0) % 360 = 90°

This calculation is CORRECT - labels should point opposite to pins. The issue is that the synchronizer is NOT getting the correct pin orientation values.

## Solution

### Option 1: Use the Same Data Source (Recommended)

Change the synchronizer to use `SymbolLibCache.get_symbol_data()` instead of `symbol_cache.get_symbol()`:

```python
# In synchronizer.py:_add_pin_label()

# OLD CODE (lines 555-583):
symbol_cache = get_symbol_cache()
symbol_def = symbol_cache.get_symbol(kicad_component.lib_id)
if not symbol_def or not hasattr(symbol_def, 'pins'):
    logger.error(f"No pin data for {kicad_component.reference}")
    return False

# Find the pin
pin = None
for p in symbol_def.pins:
    if str(p.number) == str(pin_number):
        pin = p
        break

if not pin:
    logger.warning(f"Pin {pin_number} not found on {kicad_component.reference}")
    return False

# SchematicPin uses 'position' (Point) and 'rotation' instead of x/y/orientation
pin_position = pin.position if hasattr(pin, 'position') else Point(0, 0)
pin_dict = {
    "x": float(pin_position.x),
    "y": float(pin_position.y),
    "orientation": float(pin.rotation if hasattr(pin, 'rotation') else 0.0),  # BUG
}

# NEW CODE:
from ..sch_gen.symbol_geometry import SymbolLibCache, find_pin_by_identifier

lib_data = SymbolLibCache.get_symbol_data(kicad_component.lib_id)
if not lib_data or "pins" not in lib_data:
    logger.error(f"No pin data for {kicad_component.reference}")
    return False

pin_dict = find_pin_by_identifier(lib_data["pins"], pin_number)
if not pin_dict:
    logger.warning(f"Pin {pin_number} not found on {kicad_component.reference}")
    return False

# pin_dict already has correct format: {"x": ..., "y": ..., "orientation": ...}
```

### Option 2: Debug the SchematicPin.rotation Value

Add logging to understand what value `pin.rotation` actually contains:

```python
logger.debug(f"🔍 Pin object type: {type(pin)}")
logger.debug(f"🔍 Pin attributes: {dir(pin)}")
logger.debug(f"🔍 Pin.rotation value: {pin.rotation}")
logger.debug(f"🔍 Pin.position value: {pin.position}")
```

Then fix based on findings.

## Testing

### Test Case: test_12_change_pin_connection.py

1. Run the test with the fix applied
2. Verify that both labels have correct orientations:
   - R1 pin 1 label: 270° (pointing down, opposite of pin pointing up)
   - R2 pin 2 label: 90° (pointing up, opposite of pin pointing down)
3. Open in KiCad and verify visual consistency

### Regression Tests

Run full regression suite to ensure the fix doesn't break existing label placement:
```bash
./tools/testing/run_full_regression_tests.py
```

## Implementation Plan

1. **Add debug logs** to synchronizer to observe actual pin.rotation values
2. **Run test** with logs to see what data we're actually getting
3. **Choose solution** based on findings:
   - If `pin.rotation` is always 0.0 → use Option 1 (SymbolLibCache)
   - If `pin.rotation` has wrong values → investigate data population
4. **Implement fix**
5. **Verify with test**
6. **Run regression tests**
7. **Commit with issue reference**

## Files to Modify

- `/Users/shanemattner/Desktop/circuit-synth2/src/circuit_synth/kicad/schematic/synchronizer.py` (lines 555-583)

## Related Issues

- #380: Synchronizer does not remove old hierarchical labels when pin connections change
- Test case: `tests/bidirectional/12_change_pin_connection/`

## Notes

- The label orientation calculation formula `(pin_angle + 180) % 360` is CORRECT and proven
- Both initial placement and synchronizer use the exact same formula via `GeometryUtils`
- The bug is in DATA RETRIEVAL, not in the calculation logic
- We need to ensure both code paths use the same source of pin orientation data

## Success Criteria

✅ Labels on similar components (same type, same rotation) point in consistent directions
✅ Label orientation matches initial placement behavior
✅ No regression in existing tests
✅ Visual inspection in KiCad confirms correct appearance
