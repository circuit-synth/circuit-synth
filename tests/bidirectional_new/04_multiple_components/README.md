# Test 04: Multiple Components

## Purpose

Validates handling of circuits with multiple components and their interconnections.

## Test Cases

### Test 4.1: Resistor Divider (2 Components)
- R1, R2 connected in series
- VIN → R1 → VOUT → R2 → GND
- Python → KiCad → verify both components + connections

### Test 4.2: Three Different Component Types
- Resistor (R1), Capacitor (C1), LED (D1)
- All connected to common net
- Verify type-specific properties

### Test 4.3: Ten Resistors (Scaling Test)
- R1-R10 with different values
- Various connections
- Test performance with moderate component count

### Test 4.4: Series Chain (R1-R2-R3)
- Three resistors in series
- VIN → R1 → MID1 → R2 → MID2 → R3 → GND
- Verify all intermediate nets

### Test 4.5: Parallel Resistors
- R1 || R2 || R3
- All share same two nets (VIN, GND)
- Verify parallel connections

### Test 4.6: Add Third Component to Existing Pair
- Start with R1-R2 divider
- Add C1 decoupling cap to VOUT
- Verify new component + connection added

### Test 4.7: Remove Middle Component from Chain
- Start with R1-R2-R3 chain
- Remove R2
- Verify R1-R3 now directly connected (or disconnected - TBD behavior)

## Manual Setup

**Fixtures needed:**
- `resistor_divider/` - R1, R2 classic divider
- `three_types/` - R, C, LED mix
- `series_chain/` - R1-R2-R3 chain

## Success Criteria

- ✅ Multiple components generated/imported correctly
- ✅ Connections between components preserved
- ✅ Component properties maintained
- ✅ No missing or extra components

---

**Status**: 🚧 Setup required
**Priority**: P1
**Time**: 30 min
