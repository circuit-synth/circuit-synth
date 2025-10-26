# Test 07: User Content Preservation

## Purpose

🔴 **CRITICAL TEST** - Validates that user-added content (comments, annotations) survives sync operations.

## Why This is Critical

**User Trust**: If users add documentation, comments, or notes and they disappear on the next sync, users will not trust the tool. This is a dealbreaker.

## Test Cases

### Test 7.1: Python Comments Preserved Through KiCad Sync
```python
# Input: circuit.py
@circuit
def my_circuit():
    # This is my voltage divider
    r1 = Device_R()(value="10k")  # Upper resistor

    # Output voltage calculation:
    # Vout = Vin * R2 / (R1 + R2)
    r2 = Device_R()(value="10k")  # Lower resistor
```

**Operation**:
1. Generate KiCad
2. Modify component value in KiCad (R1: 10k → 22k)
3. Import back to Python

**Expected**:
```python
@circuit
def my_circuit():
    # This is my voltage divider
    r1 = Device_R()(value="22k")  # Upper resistor  ← VALUE CHANGED

    # Output voltage calculation:  ← COMMENT PRESERVED
    # Vout = Vin * R2 / (R1 + R2)  ← COMMENT PRESERVED
    r2 = Device_R()(value="10k")  # Lower resistor  ← COMMENT PRESERVED
```

### Test 7.2: Python Docstrings Preserved
```python
@circuit
def my_circuit():
    """
    Voltage divider circuit for 3.3V → 1.65V conversion.

    Used in ADC input circuit.
    """
    r1 = Device_R()(value="10k")
```

**Expected**: Docstring survives KiCad sync

### Test 7.3: KiCad Text Annotations Preserved
- Add text note on KiCad schematic: "High-speed section"
- Update Python (add component)
- Regenerate KiCad
- Expected: Text note still present

### Test 7.4: Blank Lines Preserved
```python
@circuit
def my_circuit():
    r1 = Device_R()(value="10k")

    # Section 2: Output stage

    r2 = Device_R()(value="10k")
```

**Expected**: Blank lines preserved (no accumulation)

### Test 7.5: Mixed Edits (Python Comment + KiCad Position)
- User adds comment in Python
- User moves component in KiCad
- Sync both directions
- Expected: Both changes preserved

### Test 7.6: Component-Level Comments Preserved
```python
r1 = Device_R()(
    value="10k",  # Chosen for 1mA current
    footprint="R_0603"  # Standard 0603
)
```

**Expected**: Inline comments preserved

### Test 7.7: After-Function Content Preserved
```python
@circuit
def my_circuit():
    r1 = Device_R()(value="10k")

# Helper functions below
def calculate_divider_ratio(r1, r2):
    return r2 / (r1 + r2)
```

**Expected**: Helper functions preserved

## Implementation Details

Uses `comment_extractor.py`:
- Extracts comments from original Python
- Merges with generated Python
- Preserves user content while updating components

## Success Criteria

- ✅ All Python comments preserved
- ✅ Docstrings preserved
- ✅ Blank lines maintained (no accumulation)
- ✅ KiCad annotations preserved (if supported)
- ✅ Mixed edits work correctly

## Known Limitations

**KiCad Annotations**: Text notes on schematics may not be fully supported yet. This will be documented.

---

**Status**: 🚧 Setup required
**Priority**: P0 🔴 CRITICAL
**Time**: 25 min
