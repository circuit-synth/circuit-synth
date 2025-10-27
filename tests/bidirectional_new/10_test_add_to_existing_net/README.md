# Test 10: Add Component to Existing Net

## What This Tests
Validates that adding a third component to an existing connection between two components works correctly in KiCad.

## When This Situation Happens
- Developer has two components connected via a named net (R1-R2 on NET1)
- Needs to add another component to the same connection (R3)
- Modifies Python to connect R3 to the existing NET1
- Regenerates KiCad expecting all three components on the same net

## What Should Work
- Initial circuit with R1-R2 connected via NET1 generates correctly
- Python modified to add R3 connected to same NET1
- Regenerated KiCad shows all three components on the same net
- Net connections are properly maintained across all components

## Manual Test Instructions
```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional_new/10_test_add_to_existing_net

# Run automated test
uv run pytest test_add_to_existing_net.py -v -s
```

## Expected Result
```
✅ Test 10: Add Component to Existing Net PASSED
   - Circuit created with R1, R2, R3 all on NET1
   - KiCad project generated
   - All three components exist in schematic
   - All three components connected to same net
```
