# Component Property Analysis: Regulator_Linear:AMS1117-3.3

## Component Position and Rotation
- **Position**: `(59.69, 45.72)` mm
- **Rotation**: `0` degrees
- **Package**: SOT-223-3_TabPin2 (LDO voltage regulator)

## Property Text Positioning

### Reference Property (U1)
- **Position**: `(59.69, 39.37, 0)`
- **Offset from component**: X: 0mm, Y: -6.35mm
- **Justification**: `(justify left)`
- **Font size**: `1.27 1.27`

### Value Property (AMS1117-3.3)
- **Position**: `(59.69, 41.91, 0)`
- **Offset from component**: X: 0mm, Y: -3.81mm
- **Justification**: `(justify left)`
- **Font size**: `1.27 1.27`

### Footprint Property
- **Position**: `(59.69, 40.64, 0)`
- **Offset from component**: X: 0mm, Y: -5.08mm
- **Hidden**: `yes`

## Text Positioning Pattern

**For SOT-223 regulators (AMS1117):**
- Reference: CENTERED horizontally, ABOVE component (0, -6.35)
- Value: CENTERED horizontally, ABOVE component, below reference (0, -3.81)
- Footprint: CENTERED horizontally, ABOVE component (0, -5.08)

**Spacing:**
- Reference to Value: 2.54mm vertical spacing
- **X offset is 0mm** - properties are centered above the component

## Pattern Recognition

### SOT-223 Regulators Use Centered Text:
Unlike SOIC packages (+2.14mm offset) or transistors (+6.35mm offset), the AMS1117 regulator has:
- **X offset: 0mm (centered)**
- All properties stacked vertically ABOVE the component
- Standard 2.54mm spacing between properties

This makes sense for SOT-223 packages which have a tab and may benefit from centered text for readability.

## Status

✅ **TEXT POSITIONING APPEARS CORRECT**

The centered positioning pattern is appropriate for this package type.

## Comparison with kicad-sch-api Rules

This pattern should be checked against positioning rules for voltage regulators in the SOT-223 package.
