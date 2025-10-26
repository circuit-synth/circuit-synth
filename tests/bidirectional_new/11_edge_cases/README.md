# Test 11: Edge Cases & Error Recovery

## Purpose

Validates handling of invalid data, missing values, and error conditions.

## Test Cases

### Missing Data

**Test 11.1: Component Without Value**
```python
r1 = Device_R()()  # No value specified
# Expected: Default value or clear error message
```

**Test 11.2: Component Without Footprint**
```python
r1 = Device_R()(value="10k")  # No footprint
# Expected: Auto-select footprint or error
```

**Test 11.3: Net Without Name**
```python
r1[1] & r2[1]  # Implicit net
# Expected: Auto-generated name (e.g., "Net-1")
```

**Test 11.4: Empty Subcircuit**
```python
@circuit
def empty_sub():
    pass  # No components

# Expected: Valid but empty subcircuit
```

### Invalid Data

**Test 11.5: Invalid Component Reference**
```python
r1 = Device_R()(value="10k")
# But user manually edits to: "123" = Device_R()(value="10k")
# Expected: Error or auto-rename to valid reference
```

**Test 11.6: Duplicate Component References**
```python
r1 = Device_R()(value="10k")
r1 = Device_R()(value="22k")  # Duplicate!
# Expected: Error or auto-rename second to r1_1
```

**Test 11.7: Circular Subcircuit Dependency**
```python
# main.py imports sub.py
# sub.py imports main.py (circular!)
# Expected: Detection and error
```

**Test 11.8: Missing Subcircuit File**
```python
# main.py imports subcircuit.py
# But subcircuit.py doesn't exist
# Expected: Clear error message
```

### Partial Updates

**Test 11.9: Python Has 3 Components, KiCad Has 5**
```python
# Python: R1, R2, R3
# KiCad: R1, R2, R3, R4, R5
# Sync: What happens?
# Expected: TBD - preserve R4, R5 or remove them?
```

**Test 11.10: KiCad Has Extra Nets**
```python
# Python: VCC, GND
# KiCad: VCC, GND, UNUSED_NET
# Expected: Preserve or remove UNUSED_NET?
```

**Test 11.11: Conflicting Changes**
```python
# Python: R1 = 10k
# KiCad: R1 = 22k
# Both modified since last sync
# Expected: Which takes precedence? Error?
```

### Component Libraries

**Test 11.12: Footprint Not Found**
```python
r1 = Device_R()(footprint="NonexistentFootprint")
# Expected: Error with helpful message
```

**Test 11.13: Symbol Not Found**
```python
# KiCad has component with unknown symbol
# Expected: Import with placeholder or error
```

**Test 11.14: Multi-Unit Symbol**
```python
# Op-amp with 4 units
# Expected: All units handled correctly
```

## Error Message Quality

Tests also validate that error messages are:
- Clear and actionable
- Point to specific file/line
- Suggest fixes when possible
- Don't crash silently

## Success Criteria

- ✅ Invalid data detected and reported
- ✅ Error messages are helpful
- ✅ No silent failures
- ✅ Graceful degradation where possible

---

**Status**: 🚧 Setup required
**Priority**: P1
**Time**: 30 min
