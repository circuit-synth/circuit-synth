# Test 10: Hierarchical Restructuring

## Purpose

Validates moving components between subcircuits (advanced hierarchy operations).

## Test Cases

### Test 10.1: Move Component from Subcircuit to Main
- Start: R1 in subcircuit.py
- Move: R1 to main.py
- Expected: R1 in main.kicad_sch, removed from subcircuit.kicad_sch

### Test 10.2: Move Component Between Subcircuits
- Start: R1 in subcircuit1.py
- Move: R1 to subcircuit2.py
- Expected: R1 in subcircuit2.kicad_sch, removed from subcircuit1

### Test 10.3: Move Group of Components
- Move R1, R2, C1 from sub1 to sub2
- Verify all moved correctly
- Verify connections preserved

### Test 10.4: Extract Components to New Subcircuit
- Start: R1, R2, R3 in main.py
- Extract: Create new power_supply.py with R1, R2, R3
- Expected: New subcircuit file created

### Test 10.5: Flatten Subcircuit into Main
- Start: main.py with subcircuit.py
- Flatten: Move all subcircuit components to main
- Expected: Single-level circuit

## Implementation Challenges

**Reference Updates**: Component references must be updated
**Net Connections**: Nets crossing hierarchy boundaries must be handled
**Port Mapping**: Hierarchical ports must be adjusted

## Status

⚠️ **Not Yet Implemented** - This is advanced functionality

Tests will be marked with `pytest.mark.skip` until feature is implemented.

---

**Status**: 🚧 Future feature
**Priority**: P3
**Time**: N/A (not implemented)
