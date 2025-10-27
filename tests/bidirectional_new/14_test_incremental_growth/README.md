# Test 14: Incremental Growth (Multiple Round-Trips)

## What This Tests
Validates circuit stability through realistic development workflow - multiple cycles of edit, generate, import, edit without loss or corruption.

## When This Situation Happens
- Day 1: Developer creates basic circuit with R1, R2
- Day 2: Adds capacitor to circuit
- Day 3: Adds IC chip
- Day 4: Adds power regulation components
- Each step involves round-trips between Python and KiCad
- Circuit must accumulate components correctly without corruption

## What Should Work
- Starting circuit with 2 resistors generates correctly
- Round-trip 1: Adding capacitor preserves existing components
- Round-trip 2: Adding another resistor preserves all previous components
- Round-trip 3: Adding connections maintains component integrity
- Round-trip 4: Modifying values doesn't corrupt other properties
- All changes accumulate correctly without loss

## Manual Test Instructions
```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional_new/14_test_incremental_growth

# Run automated test
uv run pytest test_incremental_growth.py -v -s
```

## Expected Result
```
✅ Test 14: Incremental Growth PASSED
   - Round-trip 1: Initial components present
   - Round-trip 2: New components added, old preserved
   - Round-trip 3: Connections added correctly
   - Round-trip 4: Value modifications successful
   - All components and properties intact after multiple cycles
```
