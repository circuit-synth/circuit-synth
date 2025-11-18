# Component Property Analysis: 74xx:74LS245

## Component Position and Rotation
- **Position**: `(48.26, 64.77)` mm
- **Rotation**: `0` degrees
- **Unit**: `1`
- **Size**: Wide IC (30.5×71.2mm, 20 pins)

## Property Text Positioning

### Reference Property (U1)
- **Position**: `(at 50.4033 44.45 0)`
- **Offset from component**: X: +2.1433mm, Y: -20.32mm
- **Calculation**: (50.4033 - 48.26, 44.45 - 64.77) = (+2.1433, -20.32)
- **Justification**: `(justify left)`
- **Font size**: `1.27 1.27`

### Value Property (74LS245)
- **Position**: `(at 50.4033 46.99 0)`
- **Offset from component**: X: +2.1433mm, Y: -17.78mm
- **Calculation**: (50.4033 - 48.26, 46.99 - 64.77) = (+2.1433, -17.78)
- **Justification**: `(justify left)`
- **Font size**: `1.27 1.27`

### Footprint Property (empty in this case)
- **Position**: `(at 48.26 64.77 0)`
- **Offset from component**: X: 0mm, Y: 0mm
- **Calculation**: (48.26 - 48.26, 64.77 - 64.77) = (0, 0)
- **Rotation**: `0` degrees
- **Font size**: `1.27 1.27`
- **Hidden**: `yes`

## Text Positioning Pattern

**For wide ICs (74LS245):**
- Reference: ABOVE component, slightly to the right (+2.14mm, -20.32mm)
- Value: ABOVE component, slightly to the right, below Reference (+2.14mm, -17.78mm)
- Footprint: At component center (0mm, 0mm)

**Spacing:**
- Reference to Value: 2.54mm vertical spacing
- Large vertical offset to clear the IC body

## Comparison with kicad-sch-api Rules

Checking `kicad-sch-api/kicad_sch_api/core/property_positioning.py`:

```python
"74xx:74HC595": ComponentPositioningRule(
    reference_offset=PropertyOffset(x=2.1433, y=-17.78, rotation=0),
    value_offset=PropertyOffset(x=2.1433, y=-15.24, rotation=0),
    footprint_offset=PropertyOffset(x=0, y=0, rotation=0),
),
```

**Observed for 74LS245:**
- reference_offset: (+2.1433, -20.32)
- value_offset: (+2.1433, -17.78)
- footprint_offset: (0, 0)

**The X offset matches exactly (+2.1433mm)!**

The Y offsets are slightly different because the 74LS245 is taller than the 74HC595, so properties need more clearance above the component.

## Status

✅ **TEXT POSITIONING IS CORRECT**

The properties are positioned logically for a wide IC:
- Reference and Value ABOVE the component with proper spacing
- Slight right offset for readability (+2.14mm matches kicad-sch-api pattern)
- Footprint hidden at center
- Spacing between Reference and Value is 2.54mm (standard)

## Pattern Confirmation

The +2.1433mm horizontal offset appears to be the standard for wide logic ICs in the 74xx series. This matches the positioning rules in kicad-sch-api.

## Next Component to Test

Continue with: **Interface_UART:MAX3485** (SOIC-8 package)
