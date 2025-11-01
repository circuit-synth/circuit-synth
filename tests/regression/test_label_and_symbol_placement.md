# Regression Tests for Label and Symbol Placement

## Test Plan for Issues #457 and #458

These tests verify correct placement and orientation of hierarchical labels and power symbol text.

---

## Test 1: Hierarchical Label Orientation (Issue #457)

**Priority**: P0 - Critical
**File**: `test_hierarchical_label_orientation.py`

### Test Cases

#### 1.1: Label on Top Pin (90°)
```python
def test_label_top_pin():
    """Label should face DOWN (270°) toward top pin."""
    r1 = Component(symbol="Device:R", ref="R1", value="10k")
    data = Net("DATA")
    r1[2] += data  # Top pin

    # Generate and verify:
    # - Hierarchical label "DATA" exists
    # - Label angle = 270° (pointing down toward pin)
    # - Label positioned above R1 pin 2
```

#### 1.2: Label on Bottom Pin (270°)
```python
def test_label_bottom_pin():
    """Label should face UP (90°) toward bottom pin."""
    r1 = Component(symbol="Device:R", ref="R1", value="10k")
    data = Net("DATA")
    r1[1] += data  # Bottom pin

    # Verify:
    # - Label angle = 90° (pointing up toward pin)
    # - Label positioned below R1 pin 1
```

#### 1.3: Label on Left Pin (180°)
```python
def test_label_left_pin():
    """Label should face RIGHT (0°) toward left pin."""
    # Use IC with left-side pins
    u1 = Component(symbol="74xx:74HC00", ref="U1", value="74HC00")
    data = Net("DATA")
    u1[1] += data  # Left pin

    # Verify:
    # - Label angle = 0° (pointing right toward pin)
    # - Label positioned left of U1 pin 1
```

#### 1.4: Label on Right Pin (0°)
```python
def test_label_right_pin():
    """Label should face LEFT (180°) toward right pin."""
    u1 = Component(symbol="74xx:74HC00", ref="U1", value="74HC00")
    data = Net("DATA")
    u1[3] += data  # Right pin

    # Verify:
    # - Label angle = 180° (pointing left toward pin)
    # - Label positioned right of U1 pin 3
```

### Verification Method

Use `kicad-sch-api` to load generated schematic:
```python
from kicad_sch_api import Schematic

sch = Schematic.load("test_circuit.kicad_sch")

# Find hierarchical label
label = next(l for l in sch.hierarchical_labels if l.text == "DATA")

# Verify orientation
assert label.angle == expected_angle, \
    f"Label angle {label.angle}° should be {expected_angle}°"

# Verify position relative to pin
pin_pos = get_pin_position(component, pin_number)
assert label_faces_toward_pin(label.position, label.angle, pin_pos), \
    "Label should face toward connected pin"
```

---

## Test 2: Power Symbol Text Placement (Issue #458)

**Priority**: P1 - High
**File**: `test_power_symbol_text_placement.py`

### Test Cases

#### 2.1: VCC Symbol
```python
def test_vcc_text_placement():
    """VCC text should be properly positioned near symbol."""
    r1 = Component(symbol="Device:R", ref="R1", value="10k")
    vcc = Net(name="VCC")
    r1[2] += vcc

    # Verify:
    # - Power symbol reference starts with #PWR
    # - Value = "VCC"
    # - Text positioned at correct offset from symbol graphic
    # - Text readable and not overlapping symbol
```

#### 2.2: GND Symbol
```python
def test_gnd_text_placement():
    """GND text should be properly positioned near symbol."""
    r1 = Component(symbol="Device:R", ref="R1", value="10k")
    gnd = Net(name="GND")
    r1[1] += gnd

    # Verify:
    # - Power symbol for GND created
    # - Text positioned correctly relative to GND symbol
```

#### 2.3: Multiple Power Domains
```python
def test_multiple_power_symbols():
    """Test various power symbols in same circuit."""
    vcc = Net(name="VCC")
    vdd = Net(name="+5V")
    gnd = Net(name="GND")

    # Connect to multiple components
    # Verify each power symbol text is correctly placed
```

### Verification Method

```python
from kicad_sch_api import Schematic

sch = Schematic.load("test_circuit.kicad_sch")

# Find power symbol
power_symbols = [c for c in sch.components if c.reference.startswith("#PWR")]
vcc_symbol = next(p for p in power_symbols if p.value == "VCC")

# Verify text position
symbol_bbox = calculate_symbol_bounds(vcc_symbol)
text_pos = vcc_symbol.properties["Value"].position

assert text_near_symbol(text_pos, symbol_bbox), \
    "Power symbol text should be near symbol graphic"
assert not text_overlaps_symbol(text_pos, symbol_bbox), \
    "Power symbol text should not overlap symbol graphic"
```

---

## Implementation Notes

### Helper Functions Needed

```python
def get_pin_position(component, pin_number):
    """Get absolute position of component pin."""
    pass

def label_faces_toward_pin(label_pos, label_angle, pin_pos):
    """Verify label orientation points toward pin."""
    # Calculate vector from label to pin
    # Verify label angle aligns with this vector
    pass

def calculate_symbol_bounds(component):
    """Calculate bounding box of symbol graphic."""
    pass

def text_near_symbol(text_pos, symbol_bbox, max_distance=5.0):
    """Check if text is within acceptable distance of symbol."""
    pass

def text_overlaps_symbol(text_pos, symbol_bbox):
    """Check if text overlaps symbol graphic."""
    pass
```

### Test Organization

```
tests/regression/
  test_hierarchical_label_orientation.py  # Issue #457
  test_power_symbol_text_placement.py     # Issue #458
  helpers/
    label_verification.py
    symbol_verification.py
```

---

## Success Criteria

### Issue #457 (Hierarchical Labels)
- ✅ All 4 orientation tests pass (top, bottom, left, right pins)
- ✅ Labels face toward connected pins in all cases
- ✅ No regression in existing label functionality

### Issue #458 (Power Symbols)
- ✅ All common power symbols (VCC, GND, +5V, +3V3) have correct text placement
- ✅ Text readable and properly positioned relative to symbol
- ✅ No overlapping between text and symbol graphics
- ✅ Follows KiCad conventions

---

## Related Issues

- #457: Hierarchical label orientation incorrect
- #458: Power symbol text labels incorrectly positioned

**Created**: 2025-11-01
**Test Priority**: Should be implemented before next release
