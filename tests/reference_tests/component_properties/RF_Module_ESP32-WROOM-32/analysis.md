# Component Property Analysis: RF_Module:ESP32-WROOM-32

## Component Position and Rotation
- **Position**: `(95.25, 74.93)` mm
- **Rotation**: `0` degrees
- **Unit**: `1`
- **Size**: Large module (40.6×113.3mm, 38 pins)

## Property Text Positioning

### Reference Property (U1)
- **Position**: `(at 97.3933 36.83 0)`
- **Offset from component**: X: +2.1433mm, Y: -38.10mm
- **Calculation**: (97.3933 - 95.25, 36.83 - 74.93) = (+2.1433, -38.10)
- **Justification**: `(justify left)`
- **Font size**: `1.27 1.27`

### Value Property (ESP32-WROOM-32)
- **Position**: `(at 97.3933 39.37 0)`
- **Offset from component**: X: +2.1433mm, Y: -35.56mm
- **Calculation**: (97.3933 - 95.25, 39.37 - 74.93) = (+2.1433, -35.56)
- **Justification**: `(justify left)`
- **Font size**: `1.27 1.27`

### Footprint Property (RF_Module:ESP32-WROOM-32)
- **Position**: `(at 95.25 113.03 0)`
- **Offset from component**: X: 0mm, Y: +38.10mm
- **Calculation**: (95.25 - 95.25, 113.03 - 74.93) = (0, +38.10)
- **Rotation**: `0` degrees
- **Font size**: `1.27 1.27`
- **Hidden**: `yes`

## Text Positioning Pattern

**For large IC modules (ESP32):**
- Reference: ABOVE component, slightly to the right (+2.14mm, -38.10mm)
- Value: ABOVE component, slightly to the right, below Reference (+2.14mm, -35.56mm)
- Footprint: BELOW component, centered (0mm, +38.10mm)

**Spacing:**
- Reference to Value: 2.54mm vertical spacing
- Very large vertical offset (±38.10mm) due to component height

## Comparison with kicad-sch-api Rules

Checking `kicad-sch-api/kicad_sch_api/core/property_positioning.py`:

The ESP32-WROOM-32 is not explicitly defined in the positioning rules, so it likely uses a default pattern or falls back to a generic IC rule.

**Pattern observed matches large IC behavior:**
- Properties positioned ABOVE the component (negative Y offset)
- Slight right offset for readability
- Footprint below component

## Status

✅ **TEXT POSITIONING APPEARS CORRECT**

The properties are positioned logically for a large IC:
- Reference and Value are clearly visible ABOVE the component
- Proper spacing between text elements (2.54mm)
- Footprint hidden below component
- All text is left-justified and readable

## Additional Properties Found

**Manual KiCad includes:**
- ✅ Datasheet property with actual URL
- ✅ Description property with full component description

**These match the standard properties we've seen on other components.**

## Next Component to Test

Continue with: **74xx:74LS245** (20-pin wide IC)
