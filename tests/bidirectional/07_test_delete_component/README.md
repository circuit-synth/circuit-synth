# Test 07: Delete Component from Circuit

## What This Tests
Validates that removing a component from Python code correctly removes it from the regenerated KiCad schematic.

## When This Situation Happens
- Developer has a circuit with multiple components (R1 and R2)
- Decides a component is no longer needed (R2)
- Removes the component from Python code
- Regenerates KiCad project to reflect the deletion

## What Should Work
- Circuit created with both R1 and R2
- Python code modified to remove R2
- Regenerated KiCad project contains only R1
- R2 is completely removed from the schematic

## Manual Test Instructions
```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional_new/07_test_delete_component

# Run automated test
uv run pytest test_delete_component.py -v -s
```

## Expected Result
```
✅ Test 07: Delete Component PASSED
   - Circuit created with R1 and R2
   - Circuit modified to remove R2
   - KiCad project regenerated
   - Component R1 exists in schematic
   - Component R2 does NOT exist in schematic
```
