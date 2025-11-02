# Test 21: Delete Component in Subcircuit

## What This Tests

Delete component from hierarchical sheet

Operation: Delete subcircuit R2

## Manual Test Instructions

```bash
cd tests/bidirectional/component_crud_hier/21_sync_component_hier_delete

# Step 1: Generate initial circuit
uv run test_21.py
open test_21/test_21.kicad_pro

# Step 2: Modify circuit (see test description)

# Step 3: Regenerate
uv run test_21.py

# Step 4: Verify changes
open test_21/test_21.kicad_pro
```

## Automated Test

```bash
pytest test_sync_component_hier_delete.py -v
```

## Expected Result

- ✅ Delete Component in Subcircuit successful
- ✅ All other elements preserved
