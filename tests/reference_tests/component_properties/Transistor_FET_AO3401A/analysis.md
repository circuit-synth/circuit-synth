# Component Property Analysis: Transistor_FET:AO3401A

## Component Position and Rotation
- **Position**: `(55.88, 45.72)` mm
- **Rotation**: `0` degrees
- **Package**: SOT-23 (3-pin transistor)

## Property Text Positioning

### Reference Property (Q1)
- **Position**: `(62.23, 44.4499, 0)`
- **Offset from component**: X: +6.35mm, Y: -1.27mm
- **Justification**: `(justify left)`
- **Font size**: `1.27 1.27`

### Value Property (AO3401A)
- **Position**: `(62.23, 46.9899, 0)`
- **Offset from component**: X: +6.35mm, Y: +1.27mm
- **Justification**: `(justify left)`
- **Font size**: `1.27 1.27`

### Footprint Property
- **Position**: `(60.96, 47.625, 0)`
- **Offset from component**: X: +5.08mm, Y: +1.905mm
- **Hidden**: `yes`

## Text Positioning Pattern

**For SOT-23 transistors (AO3401A):**
- Reference: RIGHT side, slightly above center (+6.35, -1.27)
- Value: RIGHT side, slightly below center (+6.35, +1.27)
- Footprint: RIGHT side, below value (+5.08, +1.905)

**Spacing:**
- Reference to Value: 2.54mm vertical spacing
- Larger horizontal offset than SOIC packages (+6.35 vs +2.14)

## Pattern Recognition

### Unique to Transistors:
The +6.35mm horizontal offset is **DIFFERENT** from the SOIC pattern (+2.1433mm).

This suggests different component families have different positioning rules:
- **SOIC ICs**: +2.1433mm horizontal offset
- **SOT-23 Transistors**: +6.35mm horizontal offset
- **Regulators (SOT-223, SOT-23-6)**: 0mm horizontal offset (centered)

## Status

✅ **TEXT POSITIONING APPEARS CORRECT**

The transistor uses a different positioning pattern than ICs, which makes sense as it's a smaller 3-pin package with different pin spacing.

## Comparison with kicad-sch-api Rules

Need to check if there's a specific rule for transistors in the positioning rules file.
