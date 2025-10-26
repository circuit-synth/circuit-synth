# Test 02: Single Component

## Purpose

Validates basic component operations: add, remove, modify properties.

## What This Tests

### Component Lifecycle
- Add single component in Python → appears in KiCad
- Add single component in KiCad → appears in Python
- Modify component value → change reflected
- Delete component → removed from output

### Component Properties
- Reference (R1, C1, etc.)
- Value (10k, 100nF, etc.)
- Footprint (Resistor_SMD:R_0603, etc.)
- Component type preservation

## Test Cases

### Test 2.1: Add Resistor in Python → Generate KiCad
```python
# Input: single_resistor.py
@circuit
def single_resistor():
    r1 = Device_R()(value="10k", footprint="R_0603")
    GND = Net("GND")
    r1[1] & GND

# Expected: R1 appears in KiCad schematic with value 10k, footprint R_0603
```

**Validates**:
- Component creation
- Properties transferred
- Basic net connection

### Test 2.2: Add Resistor in KiCad → Import to Python
```python
# Input: KiCad schematic with R1 (10k, R_0603)

# Expected Output in Python:
r1 = Device_R()(value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
```

**Validates**:
- Component extraction from KiCad
- Property parsing
- Python code generation

### Test 2.3: Modify Value in Python → Update KiCad
```python
# Start: R1 = 10k in KiCad
# Change Python: value="22k"
# Update KiCad
# Expected: R1 now shows 22k in KiCad
```

**Validates**:
- Property updates work
- Existing component modified (not replaced)
- Reference preserved

### Test 2.4: Modify Value in KiCad → Import to Python
```python
# Start: r1 value="10k" in Python
# Change KiCad: R1 value to 22k
# Import to Python
# Expected: r1 = Device_R()(value="22k", ...)
```

**Validates**:
- KiCad changes detected
- Python code updated
- Variable name preserved

### Test 2.5: Delete Component in Python → Update KiCad
```python
# Start: R1 exists in KiCad
# Python: Remove r1 definition
# Update KiCad
# Expected: R1 removed from schematic
```

**Validates**:
- Component deletion works
- No orphaned data in KiCad

### Test 2.6: Delete Component in KiCad → Import to Python
```python
# Start: r1 exists in Python
# KiCad: Delete R1
# Import to Python
# Expected: r1 line removed
```

**Validates**:
- Deletion detected
- Python code cleaned up

### Test 2.7: Component with Custom Reference
```python
# Python: r5 = Device_R()(value="10k")
# Expected KiCad: R5 (not R1)
```

**Validates**:
- Custom references preserved
- No auto-renaming

### Test 2.8: Different Component Types
```python
# Test with:
# - Resistor (R)
# - Capacitor (C)
# - LED (D)
# - Connector (J)
```

**Validates**:
- Multiple component types supported
- Type-specific properties handled

## Files

### Manual Setup Required

1. **`fixtures/single_resistor/single_resistor.py`**
   ```python
   from circuit_synth import circuit, Net
   from circuit_synth.components.passives import Device_R

   @circuit
   def single_resistor():
       r1 = Device_R()(value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
       GND = Net("GND")
       r1[1] & GND  # Pin 1 to GND
       r1[2] & GND  # Pin 2 to GND (simple termination)
   ```

2. **`fixtures/single_resistor/single_resistor.kicad_pro`** (create in KiCad)
   - Add one resistor R1
   - Value: 10k
   - Footprint: Resistor_SMD:R_0603_1608Metric
   - Connect both pins to GND

### Test Files
- `test_add_resistor_python_to_kicad.py` - Test 2.1
- `test_add_resistor_kicad_to_python.py` - Test 2.2
- `test_modify_value_python_to_kicad.py` - Test 2.3
- `test_modify_value_kicad_to_python.py` - Test 2.4
- `test_delete_component_python_to_kicad.py` - Test 2.5
- `test_delete_component_kicad_to_python.py` - Test 2.6
- `test_custom_reference.py` - Test 2.7
- `test_different_component_types.py` - Test 2.8

## Expected Output

```
test_add_resistor_python_to_kicad PASSED
  ✓ R1 exists in KiCad schematic
  ✓ Value is 10k
  ✓ Footprint is R_0603

test_modify_value_python_to_kicad PASSED
  ✓ Value updated from 10k to 22k
  ✓ Reference R1 unchanged
  ✓ Position preserved

test_delete_component_python_to_kicad PASSED
  ✓ R1 removed from schematic
  ✓ No orphaned nets
```

## Debugging

### Component Not Appearing:
- Check component class is imported correctly
- Verify footprint exists in KiCad library
- Check reference is valid (R1, not 1R)

### Value Not Updating:
- Verify component reference matches
- Check sync logic detects changes
- Look for cached data

### Deletion Not Working:
- Check if component is actually removed from Python
- Verify KiCad schematic is being updated
- Look for lingering references

## Success Criteria

- ✅ All 8 tests passing
- ✅ Component CRUD operations work both directions
- ✅ Properties preserved through sync
- ✅ No phantom components

## Dependencies

- `circuit_synth.components.passives` (Device_R, Device_C, etc.)
- KiCad symbol libraries
- Valid footprint libraries

---

**Status**: 🚧 Manual setup required
**Priority**: P0 (Critical)
**Estimated Setup Time**: 15 minutes
