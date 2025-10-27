# Test 17: Create Net Connection

## What This Tests
Validates that creating a connection (net) between two components in Python code correctly appears in the generated KiCad schematic.

## When This Situation Happens
- Developer has two unconnected components in circuit
- Needs to connect them electrically
- Adds Net() in Python to connect component pins
- Generates KiCad expecting connection to be present

## What Should Work
- Circuit created with two unconnected resistors (R1, R2)
- Python code adds Net connecting R1.pin2 to R2.pin1
- Generated KiCad schematic shows electrical connection
- Net is properly represented in the schematic

## Manual Test Instructions
```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional_new/17_test_create_net

# Run automated test
uv run pytest test_create_net.py -v -s
```

## Expected Result
```
✅ Test 17: Create Net Connection PASSED
   - Circuit created with R1 and R2
   - Net created connecting R1.pin2 to R2.pin1
   - KiCad project generated
   - Both components exist in schematic
   - Connection between components is present
```
