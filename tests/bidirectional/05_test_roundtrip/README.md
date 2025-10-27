# Test 05: Simple Round-Trip Cycle

## What This Tests
Validates that a complete round-trip cycle (Python to KiCad to Python to KiCad) preserves circuit components without loss.

## When This Situation Happens
- Developer creates circuit in Python and generates KiCad project
- Opens KiCad project to view or verify the design
- Imports the KiCad project back to Python for further modifications
- Regenerates KiCad from the imported Python code

## What Should Work
- Original Python circuit generates valid KiCad project with R1 component
- KiCad project can be imported back to Python without errors
- Imported Python code regenerates KiCad successfully
- Both the original and round-trip KiCad projects contain the same component (R1)

## Manual Test Instructions
```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional_new/05_test_roundtrip

# Run automated test
uv run pytest test_roundtrip.py -v -s
```

## Expected Result
```
✅ Test 05: Simple Round-Trip Cycle PASSED
   - Original KiCad project created with R1
   - KiCad imported to Python successfully
   - Round-trip KiCad project created with R1
   - Component R1 exists in both original and round-trip KiCad
```
