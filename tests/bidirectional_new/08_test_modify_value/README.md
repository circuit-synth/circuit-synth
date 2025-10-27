# Test 08: Modify Component Value

## What This Tests
Validates that changing a component's value in Python code correctly updates the value in the regenerated KiCad schematic and survives round-trip.

## When This Situation Happens
- Developer has a circuit with a resistor (R1=10k)
- Design requirements change, needs different value (R1=20k)
- Updates the value in Python code
- Regenerates KiCad and verifies value persists through import/export cycle

## What Should Work
- Original circuit has R1 with value 10k
- Python code modified to change R1 value to 20k
- Regenerated KiCad shows R1=20k
- Round-trip import back to Python preserves the 20k value

## Manual Test Instructions
```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional_new/08_test_modify_value

# Run automated test
uv run pytest test_modify_value.py -v -s
```

## Expected Result
```
✅ Test 08: Modify Component Value PASSED
   - R1 value changed from 10k to 20k
   - KiCad project regenerated
   - R1 value is 20k in KiCad
   - R1 value is 20k after round-trip import
```
