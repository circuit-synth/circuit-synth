# Test 01: Blank Circuit

## What This Tests

Generation of a blank circuit (no components, no nets) from Python to KiCad.

## When This Situation Happens

- Starting a new circuit design with an empty template
- Testing minimal circuit generation infrastructure
- Verifying basic KiCad project structure

## What Should Work

1. Python circuit with no components generates KiCad project
2. All required KiCad files are created (.kicad_pro, .kicad_sch, .kicad_pcb, .net, .json)
3. JSON metadata has correct circuit name (not hardcoded "main")

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional_new/01_test_blank

# Run automated test
uv run pytest test_blank.py -v -s

# The test will:
# 1. Create a blank.py circuit file
# 2. Generate KiCad project
# 3. Verify all files exist
# 4. Check JSON has correct name
```

## Expected Result

```
✅ Blank circuit works
```

All KiCad files created in `generated/01_blank/blank/` with correct naming.
