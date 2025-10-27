# Test 13: Component Rename Consistency

## What This Tests
Validates that renaming a component in KiCad maintains consistency when imported back to Python and used in further development.

## When This Situation Happens
- Developer creates R1 in Python and generates KiCad
- Opens in KiCad and renames R1 to R_PULLUP for better clarity
- Imports modified KiCad back to Python
- Adds connections using the renamed reference
- Regenerates KiCad and expects consistency across tools

## What Should Work
- Initial circuit with R1 generates successfully
- KiCad component renamed from R1 to R_PULLUP (simulated)
- Reimport to Python recognizes the new reference name
- Python code can use R_PULLUP reference for connections
- Regenerated KiCad maintains the renamed reference consistently

## Manual Test Instructions
```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional_new/13_test_component_rename

# Run automated test
uv run pytest test_component_rename.py -v -s
```

## Expected Result
```
✅ Test 13: Component Rename Consistency PASSED
   - Original circuit created with R1
   - Component renamed to R_PULLUP in KiCad
   - Reimported to Python with new name
   - Connections added using R_PULLUP reference
   - KiCad regenerated with consistent naming
```
