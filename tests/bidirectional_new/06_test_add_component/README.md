# Test 06: Add Component to Existing Circuit

## What This Tests
Validates that adding a new component in Python code correctly appears in the regenerated KiCad schematic.

## When This Situation Happens
- Developer has an existing circuit with some components (R1)
- Needs to add a new component (R2) to the circuit
- Modifies Python code to include the new component
- Regenerates KiCad project to include the addition

## What Should Work
- Original circuit with R1 generates successfully
- Python code modified to add R2 component
- Regenerated KiCad project contains both R1 and R2
- Both components are properly represented in the schematic

## Manual Test Instructions
```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional_new/06_test_add_component

# Run automated test
uv run pytest test_add_component.py -v -s
```

## Expected Result
```
✅ Test 06: Add Component PASSED
   - Circuit modified to add R2
   - KiCad project regenerated
   - Component R1 exists in schematic
   - Component R2 exists in schematic
```
