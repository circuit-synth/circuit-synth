# Circuit-Synth Debugging and Testing Guide

## Overview

This guide describes the debug-test-inspect cycle for developing and testing circuit-synth features, especially schematic generation and placement logic.

## The Debug Cycle

### 1. Add Debug Logs

Add strategic debug prints/logs to understand what your code is doing:

```python
# Example: Debugging bounding box calculations
print(f"DEBUG: Component {ref} at position {pos}")
print(f"DEBUG: Calculated bbox: {bbox}")
print(f"DEBUG: Pin labels: {pin_labels}")
```

**Best Practices:**
- Prefix debug output with `DEBUG:` for easy identification
- Include component references and positions
- Log intermediate calculation values
- Use structured output (avoid single-line dumps)
- Remove or reduce frequency of logs after feature is working

**Logging Cleanup:**
- Remove verbose debug logs after feature works correctly
- Keep critical warning/error logs
- Reduce log frequency in hot loops
- Convert debug prints to proper logging with appropriate levels

### 2. Run Logic

Execute your test circuit or schematic generation:

```python
# Example test circuit
from circuit_synth import *

@circuit(name="Debug Test")
def test_circuit():
    vcc = Net("VCC")
    gnd = Net("GND")

    r1 = Component(symbol="Device:R", ref="R1", value="10k")
    r1["1"] += vcc
    r1["2"] += gnd

    return circuit()

# Generate schematic
circ = test_circuit()
circ.generate_schematic(
    output_dir="test_output",
    draw_bounding_boxes=True  # Visual debugging aid
)
```

### 3. Generate PDF

Use kicad-cli to generate a PDF for visual inspection:

```bash
# Generate PDF from schematic
kicad-cli sch export pdf \
  --output test_output/schematic.pdf \
  test_output/schematic.kicad_sch

# Open PDF for inspection (macOS)
open test_output/schematic.pdf

# Linux
xdg-open test_output/schematic.pdf
```

**Automated Script:**
```bash
#!/bin/bash
# debug_test.sh - Generate schematic and open PDF

OUTPUT_DIR="test_output"
SCHEMATIC="$OUTPUT_DIR/schematic.kicad_sch"
PDF="$OUTPUT_DIR/schematic.pdf"

# Run your test
python test_placement.py

# Generate PDF
kicad-cli sch export pdf --output "$PDF" "$SCHEMATIC"

# Open PDF
open "$PDF"  # macOS
# xdg-open "$PDF"  # Linux
```

### 4. Inspect Results

**Visual Inspection:**
- Are bounding boxes accurate?
- Do components overlap?
- Are pin labels positioned correctly?
- Are designators readable and well-placed?
- Does the schematic look professional?

**Log Analysis:**
- Compare calculated values with visual results
- Check for unexpected values or edge cases
- Verify calculations match expected formulas
- Look for patterns in failures

### 5. Iterate

Based on inspection:
- Adjust calculations in code
- Add more targeted debug logs
- Test edge cases (large/small components, long labels)
- Repeat cycle until feature works correctly

## Testing Strategies

### Visual Testing

Use `draw_bounding_boxes=True` to see calculated boundaries:

```python
circ.generate_schematic(
    output_dir="test_output",
    draw_bounding_boxes=True  # Shows calculated bboxes
)
```

This helps verify:
- Bounding box accuracy
- Spacing between components
- Label placement within bounds
- Collision detection areas

### Formal Tests

Create pytest tests for critical functionality:

```python
# tests/test_symbol_geometry.py
import pytest
from circuit_synth.kicad.sch_gen.symbol_geometry import SymbolBoundingBoxCalculator

def test_pin_label_width():
    """Test pin label width calculation with 0.65 ratio."""
    calc = SymbolBoundingBoxCalculator()

    # Test short label
    width = calc.calculate_pin_label_width("VCC")
    expected = 3 * calc.DEFAULT_TEXT_HEIGHT * calc.DEFAULT_PIN_TEXT_WIDTH_RATIO
    assert abs(width - expected) < 0.01

    # Test long label
    width = calc.calculate_pin_label_width("VERY_LONG_PIN_NAME")
    expected = 18 * calc.DEFAULT_TEXT_HEIGHT * calc.DEFAULT_PIN_TEXT_WIDTH_RATIO
    assert abs(width - expected) < 0.01

def test_bounding_box_includes_pins():
    """Verify bounding box includes all pin labels."""
    # Load test symbol
    symbol = load_test_symbol("Device:R")
    bbox = calc.calculate_bounding_box(symbol, position=(0, 0))

    # Verify all pins are within bounds
    for pin in symbol.pins:
        pin_pos = calculate_pin_position(pin)
        assert bbox.contains(pin_pos)
```

### Integration Tests

Test complete circuits end-to-end:

```python
def test_mixed_component_circuit():
    """Test circuit with small, medium, and large components."""
    @circuit(name="Mixed Components")
    def mixed_circuit():
        # Small
        r1 = Component(symbol="Device:R", ref="R1", value="10k")

        # Medium
        conn = Component(symbol="Connector:Conn_01x04", ref="J1", value="Connector")

        # Large
        mcu = Component(symbol="MCU_ST_STM32F4:STM32F407VGTx", ref="U1", value="MCU")

        # Connect and verify no overlaps
        # ...

        return circuit()

    circ = mixed_circuit()
    circ.generate_schematic(output_dir="test_output")

    # Verify no component overlaps
    assert no_overlaps(circ)
```

## KiCad CLI Reference

### Export Commands

```bash
# Export to PDF
kicad-cli sch export pdf --output output.pdf schematic.kicad_sch

# Export to SVG
kicad-cli sch export svg --output output.svg schematic.kicad_sch

# Export to PNG (with DPI control)
kicad-cli sch export png --output output.png --dpi 300 schematic.kicad_sch

# Export netlist
kicad-cli sch export netlist --output output.net schematic.kicad_sch
```

### Validation

```bash
# Check schematic for errors
kicad-cli sch erc --output erc_report.txt schematic.kicad_sch
```

## Common Debug Scenarios

### Scenario 1: Pin Labels Extending Beyond Bounds

**Symptoms:**
- Bounding boxes too small
- Labels overlap other components
- Collision detection fails

**Debug Approach:**
1. Add debug logs for pin label width calculations
2. Print calculated bbox vs actual pin label extents
3. Generate PDF with `draw_bounding_boxes=True`
4. Compare visual extent with calculated bbox
5. Adjust `DEFAULT_PIN_TEXT_WIDTH_RATIO` if needed

### Scenario 2: Component Overlaps

**Symptoms:**
- Components placed on top of each other
- Bounding boxes overlap visually

**Debug Approach:**
1. Log each component's position and bbox
2. Log collision detection results
3. Generate PDF to see actual overlap
4. Check if placement algorithm respects bboxes
5. Verify bbox calculation includes all elements

### Scenario 3: Designator Misplacement

**Symptoms:**
- Designators too close/far from component
- Designators overlap component body

**Debug Approach:**
1. Log designator position calculations
2. Log component height/width values
3. Compare visual position with calculated position
4. Adjust spacing formula if needed

## Performance Testing

For large circuits, profile performance:

```python
import cProfile
import pstats

# Profile schematic generation
cProfile.run('circ.generate_schematic()', 'profile_stats')

# Analyze results
stats = pstats.Stats('profile_stats')
stats.sort_stats('cumulative')
stats.print_stats(20)  # Top 20 slowest functions
```

## Best Practices

1. **Start Simple:** Test with minimal circuits first (1-2 components)
2. **Add Complexity:** Gradually add more components and connections
3. **Test Edge Cases:** Long labels, large components, dense circuits
4. **Visual Verification:** Always generate and inspect PDFs
5. **Automate:** Create scripts for common debug cycles
6. **Clean Up:** Remove debug logs after feature works
7. **Document:** Add comments explaining complex calculations
8. **Regression Test:** Ensure fixes don't break existing circuits

## Tools

- **kicad-cli:** Command-line KiCad operations
- **pytest:** Formal testing framework
- **PDF viewer:** Visual inspection
- **cProfile:** Performance profiling
- **git diff:** Compare schematic changes

## Example Complete Debug Session

```bash
# 1. Run test with debug logs
python test_placement.py > debug.log 2>&1

# 2. Generate PDF
kicad-cli sch export pdf \
  --output test_output/schematic.pdf \
  test_output/schematic.kicad_sch

# 3. Inspect results
open test_output/schematic.pdf
less debug.log

# 4. If issues found, add more targeted logs and repeat
# 5. Once working, run formal tests
pytest tests/test_placement.py -v

# 6. Clean up debug logs in source code
# 7. Commit working version
git add src/circuit_synth/kicad/sch_gen/symbol_geometry.py
git commit -m "Fix pin label width calculation"
```

## Troubleshooting

**KiCad CLI not found:**
```bash
# macOS
export PATH="/Applications/KiCad/KiCad.app/Contents/MacOS:$PATH"

# Linux
export PATH="/usr/local/bin:$PATH"
```

**PDF not generating:**
- Check schematic file exists and is valid
- Verify KiCad version supports CLI (7.0+)
- Check for KiCad ERC errors first

**Tests passing but visual issues:**
- Formal tests may not catch all visual problems
- Always supplement with PDF inspection
- Create reference schematics for comparison

---

**Remember:** The debug-test-inspect cycle is iterative. Don't expect perfection on first try. Use logs, visual inspection, and systematic testing to converge on correct behavior.
