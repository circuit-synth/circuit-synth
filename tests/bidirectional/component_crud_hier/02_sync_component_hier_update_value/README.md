# Test 19: Update Component Value in Subcircuit

## What This Tests

Update component value in hierarchical sheet

Operation: Update subcircuit R1: 10k → 47k

## Manual Test Instructions

```bash
cd tests/bidirectional/component_crud_hier/19_sync_component_hier_update_value

# Step 1: Generate initial circuit
uv run test_19.py
open test_19/test_19.kicad_pro

# Step 2: Modify circuit (see test description)

# Step 3: Regenerate
uv run test_19.py

# Step 4: Verify changes
open test_19/test_19.kicad_pro
```

## Automated Test

```bash
pytest test_sync_component_hier_update_value.py -v
```

## Expected Result

- ✅ Update Component Value in Subcircuit successful
- ✅ All other elements preserved
