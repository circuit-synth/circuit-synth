# Component Property Analysis: Regulator_Switching:TPS54202DDC

## Component Position and Rotation
- **Position**: `(77.47, 45.72)` mm
- **Rotation**: `0` degrees
- **Package**: SOT-23-6 (buck converter)

## Property Text Positioning

### Reference Property (U1)
- **Position**: `(77.47, 35.56, 0)`
- **Offset from component**: X: 0mm, Y: -10.16mm
- **Justification**: `(justify left)`
- **Font size**: `1.27 1.27`

### Value Property (TPS54202DDC)
- **Position**: `(77.47, 38.10, 0)`
- **Offset from component**: X: 0mm, Y: -7.62mm
- **Justification**: `(justify left)`
- **Font size**: `1.27 1.27`

### Footprint Property
- **Position**: `(78.74, 54.61, 0)`
- **Offset from component**: X: +1.27mm, Y: +8.89mm
- **Hidden**: `yes`

## Text Positioning Pattern

**For SOT-23-6 regulators (TPS54202):**
- Reference: CENTERED horizontally, ABOVE component (0, -10.16)
- Value: CENTERED horizontally, ABOVE component, below reference (0, -7.62)
- Footprint: Slightly right, BELOW component (+1.27, +8.89)

**Spacing:**
- Reference to Value: 2.54mm vertical spacing
- **X offset is 0mm** for Reference and Value - centered above component
- Footprint is offset slightly

## Pattern Recognition

### SOT-23-6 Regulators Use Centered Text:
Like the SOT-223 (AMS1117), the SOT-23-6 buck converter uses:
- **X offset: 0mm (centered)** for Reference and Value
- Properties stacked vertically ABOVE the component
- Larger Y offset (-10.16mm) than SOT-223 (-6.35mm) due to package size
- Standard 2.54mm spacing between properties

**Regulators pattern:**
Both voltage regulators (linear and switching) use centered text positioning regardless of package type.

## Status

✅ **TEXT POSITIONING APPEARS CORRECT**

The centered positioning pattern is consistent across voltage regulator components.

## Comparison with Other Regulators

| Component | Package | X Offset | Y Offset (Ref) |
|-----------|---------|----------|----------------|
| AMS1117-3.3 | SOT-223 | 0mm | -6.35mm |
| TPS54202DDC | SOT-23-6 | 0mm | -10.16mm |

Both regulators center their text horizontally but vary the vertical offset based on package size.
