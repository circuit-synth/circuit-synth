# Test 15: Move Component to New Position

## What This Tests
Validates that changing a component's position in Python code correctly updates the position in the regenerated KiCad schematic.

## When This Situation Happens
- Developer has positioned component at specific coordinates
- Decides to reorganize schematic layout
- Modifies position coordinates in Python code
- Regenerates KiCad expecting component at new location

## What Should Work
- Original component positioned at (100, 100, 0)
- Python code modified to move component to (200, 150, 45)
- Regenerated KiCad shows component at new coordinates
- Rotation angle updated correctly to 45 degrees

## Manual Test Instructions
```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional_new/15_test_move_component

# Run automated test
uv run pytest test_move_component.py -v -s
```

## Expected Result
```
✅ Test 15: Move Component PASSED
   - Original position: (100.0, 100.0, 0°)
   - Position modified to: (200.0, 150.0, 45°)
   - KiCad project regenerated
   - Component appears at new position
   - Component has correct rotation angle
```
