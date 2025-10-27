# Test 04: Component Properties Preserved

## What This Tests

Component properties (reference, value, footprint) survive Python → KiCad → Python round-trip.

## When This Situation Happens

- User defines component with specific properties in Python
- Generates KiCad project
- Later imports back to Python
- Properties must remain identical

## What Should Work

1. Original Python: `Component(ref="R1", value="10k", footprint="R_0603")`
2. After generation and import: same properties preserved
3. No data loss during round-trip

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional_new/04_test_properties

# Generate KiCad from fixture
uv run python ../fixtures/single_resistor.py
ls single_resistor/

# Import back to Python
uv run kicad-to-python single_resistor/single_resistor.kicad_pro -o imported_circuit.py

# Compare properties
cat ../fixtures/single_resistor.py
cat imported_circuit.py

# Run automated test
uv run pytest test_properties.py -v -s
```

## Expected Result

```
✅ Generation completed
✅ Import completed
✅ Properties match: ref=R1, value=10k, footprint contains 0603
```
