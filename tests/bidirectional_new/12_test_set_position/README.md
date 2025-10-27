# Test 12: Set Component Position in Python

## What This Tests
Validates that explicitly setting component positions in Python code (x, y, rotation) correctly appears in the generated KiCad schematic.

## When This Situation Happens
- Developer wants precise component placement for organized schematics
- Sets explicit positions using at=(x, y, rotation) in Python code
- Generates KiCad project
- Expects components to appear at specified coordinates with correct rotation

## What Should Work
- Python code specifies R1 at position (100, 100, 0)
- Python code specifies R2 at position (150, 100, 90)
- Generated KiCad schematic places components at exact coordinates
- Component rotation angles match specified values

## Manual Test Instructions
```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional_new/12_test_set_position

# Run automated test
uv run pytest test_set_position.py -v -s
```

## Expected Result
```
✅ Test 12: Set Component Position PASSED
   - R1 positioned at (100.0, 100.0, 0°)
   - R2 positioned at (150.0, 100.0, 90°)
   - KiCad project generated
   - R1 appears at correct position and rotation
   - R2 appears at correct position and rotation
```
