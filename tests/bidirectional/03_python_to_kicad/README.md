# Test 02: Generate KiCad from Python

## What This Tests

Python → KiCad generation with a single component (resistor).

Tests ONLY generation direction, not import or round-trip.

## When This Situation Happens

- User writes Python circuit and generates KiCad project for the first time
- Adding first component to a new design
- Basic component generation workflow

## What Should Work

1. Python circuit with single resistor generates KiCad project
2. Component appears in schematic with correct reference (R1)
3. Component has correct value (10k)
4. All KiCad files created with valid syntax

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional_new/02_test_generate

# Run fixture manually to see generation
uv run python ../fixtures/single_resistor.py

# Check generated files
ls -la single_resistor/
cat single_resistor/single_resistor.json

# Run automated test
uv run pytest test_generate.py -v -s
```

## Expected Result

```
✅ Generation completed (exit code: 0)
✅ KiCad project found
✅ Component R1 found in schematic
```

KiCad project in `generated/02_generate/single_resistor/` with R1 component visible.
