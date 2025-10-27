# Test 03: Import Python from KiCad

## What This Tests

KiCad → Python import with a single component (resistor).

Tests ONLY import direction, not generation or round-trip.

## When This Situation Happens

- User has existing KiCad project and wants to generate Python code
- Converting legacy KiCad designs to circuit-synth workflow
- Starting from hand-drawn schematic in KiCad

## What Should Work

1. Import KiCad project to Python using `kicad-to-python` command
2. Python file created with circuit decorator
3. Component R1 appears in Python with correct reference
4. Python file is valid and executable

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional_new/03_test_import

# Import KiCad project manually
uv run kicad-to-python ../24_single_component/02_kicad_ref/02_kicad_ref.kicad_pro -o imported_resistor.py

# Check generated Python file
cat imported_resistor.py

# Run automated test
uv run pytest test_import.py -v -s
```

## Expected Result

```
✅ Import completed (exit code: 0)
✅ Python file created
✅ Component R1 found in Python file
```

Python file in `generated/03_import/imported_resistor.py` with R1 component visible.
