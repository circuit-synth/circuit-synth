# Component Property Analysis: Interface_UART:MAX3485

## Cycle 1 Log: Initial Data Extraction

**Component Position:** `(71.12, 71.12)` mm
**Rotation:** 0°
**Package:** SOIC-8 (30.5×66.1mm calculated size)

### Property Positions (Raw Data)

| Property | Position | Hidden |
|----------|----------|--------|
| Reference | (73.2633, 53.34, 0) | no |
| Value | (73.2633, 55.88, 0) | no |
| Footprint | (71.12, 93.98, 0) | yes |
| Datasheet | (71.12, 69.85, 0) | yes |
| Description | (71.12, 71.12, 0) | yes |

## Cycle 2 Log: Offset Calculations

### Reference Property (U1)
- **Position**: (73.2633, 53.34, 0)
- **Component center**: (71.12, 71.12)
- **Offset calculation**:
  - X: 73.2633 - 71.12 = **+2.1433 mm**
  - Y: 53.34 - 71.12 = **-17.78 mm**
- **Offset**: (+2.1433, -17.78)

### Value Property (MAX3485)
- **Position**: (73.2633, 55.88, 0)
- **Offset calculation**:
  - X: 73.2633 - 71.12 = **+2.1433 mm**
  - Y: 55.88 - 71.12 = **-15.24 mm**
- **Offset**: (+2.1433, -15.24)

### Footprint Property
- **Position**: (71.12, 93.98, 0)
- **Offset calculation**:
  - X: 71.12 - 71.12 = **0 mm**
  - Y: 93.98 - 71.12 = **+22.86 mm**
- **Offset**: (0, +22.86)

### Property Spacing
- **Reference to Value**: 55.88 - 53.34 = **2.54 mm** (standard KiCad spacing)

## Cycle 3 Log: Pattern Recognition

### Observed Pattern for SOIC-8 (MAX3485):
```
Reference: (+2.1433, -17.78, 0)
Value:     (+2.1433, -15.24, 0)
Footprint: (0, +22.86, 0)
```

### Comparison with 74LS245 (SOIC-20):
```
74LS245:
Reference: (+2.1433, -20.32, 0)
Value:     (+2.1433, -17.78, 0)
Footprint: (0, 0, 0)
```

### Key Observations:
1. **X offset is IDENTICAL**: +2.1433mm for both SOIC-8 and SOIC-20
2. **Y offset pattern**: Both have properties ABOVE component
3. **Footprint varies**: SOIC-8 has footprint below (+22.86), SOIC-20 at center (0)
4. **Consistent spacing**: 2.54mm between Reference and Value

## Status

✅ **TEXT POSITIONING IS CORRECT**

The MAX3485 follows the same horizontal offset pattern (+2.1433mm) as other SOIC packages.

## Next: Generate remaining ICs for comparison
