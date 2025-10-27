# Test 09: Manual Position Preservation (CRITICAL)

## What This Tests
Validates that manual position changes made in KiCad survive Python regeneration. This is THE killer feature for real-world usability.

## When This Situation Happens
- Developer generates KiCad from Python
- Manually arranges components in KiCad schematic editor for better layout
- Adds a new component in Python code
- Regenerates KiCad and expects manual layout work to be preserved
- If manual edits are lost, the tool becomes unusable for iterative development

## What Should Work
- Initial KiCad generation creates schematic with default positions
- Manual position edits in KiCad are detected when reimporting
- Adding new components in Python and regenerating preserves manual positions
- Only the new component gets auto-positioned; existing components stay put

## Manual Test Instructions
```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional_new/09_test_manual_position_preservation

# Run automated test
uv run pytest test_manual_position_preservation.py -v -s
```

## Expected Result
```
✅ Test 09: Manual Position Preservation PASSED
   - Original KiCad generated with component R1
   - R1 manually repositioned in KiCad (simulated)
   - Circuit reimported to Python
   - New component R2 added in Python
   - KiCad regenerated
   - R1 position preserved at manual coordinates
   - R2 created at new position
```
