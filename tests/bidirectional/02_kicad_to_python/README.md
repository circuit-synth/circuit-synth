# Test 02: Blank KiCad → Blank Python

## What This Tests

Importing a blank KiCad project (no components) to Python.

## When This Situation Happens

- User has empty KiCad template
- Converting blank project to circuit-synth workflow
- Starting point for adding components in Python

## What Should Work

1. Import blank KiCad project using `kicad-to-python`
2. Python file generated with circuit decorator
3. Circuit function has no components
4. Python is valid and executable

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional/02_kicad_to_python

# Import blank KiCad to Python
uv run kicad-to-python blank_kicad_ref/blank.kicad_pro -o imported_blank.py

# Check Python file - should be empty circuit
cat imported_blank.py

# Should show circuit decorator with no components inside
```

## Expected Result

- ✅ Python file created
- ✅ Has circuit decorator
- ✅ Circuit function is empty (no components)
- ✅ Valid Python syntax
