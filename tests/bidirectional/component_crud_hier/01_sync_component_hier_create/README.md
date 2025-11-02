# Test 18: Add Component in Subcircuit

## What This Tests

Add component to hierarchical sheet

Operation: Add R3 in subcircuit

## Manual Test Instructions

```bash
cd tests/bidirectional/component_crud_hier/18_sync_component_hier_create

# Step 1: Generate initial circuit
uv run test_18.py
open test_18/test_18.kicad_pro

# Step 2: Modify circuit (see test description)

# Step 3: Regenerate
uv run test_18.py

# Step 4: Verify changes
open test_18/test_18.kicad_pro
```

## Automated Test

```bash
pytest test_sync_component_hier_create.py -v
```

## Expected Result

- ✅ Add Component in Subcircuit successful
- ✅ All other elements preserved
