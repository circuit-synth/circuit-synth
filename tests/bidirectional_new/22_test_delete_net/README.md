# Test 22: Delete Net Connection

## What This Tests
Validates that removing a connection (net) between components in Python code correctly removes it from the regenerated KiCad schematic.

## When This Situation Happens
- Developer has two connected components in circuit
- Decides the connection is no longer needed
- Removes Net() from Python code
- Regenerates KiCad expecting connection to be removed while components remain

## What Should Work
- Circuit can be created with disconnected components
- Components exist in KiCad without connections
- Removing a net doesn't remove the components themselves
- Regenerated KiCad shows components but no connection

## Manual Test Instructions
```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional_new/22_test_delete_net

# Run automated test
uv run pytest test_delete_net.py -v -s
```

## Expected Result
```
✅ Test 22: Delete Net Connection PASSED
   - Circuit created with R1 and R2
   - No net connection created (simulating deletion)
   - KiCad project generated
   - Component R1 exists in schematic
   - Component R2 exists in schematic
   - No connection between components
```
