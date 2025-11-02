# Test 20: Rename Component in Subcircuit

## What This Tests

Rename component in hierarchical sheet

Operation: Rename subcircuit R1 → R100

## Manual Test Instructions

```bash
cd tests/bidirectional/component_crud_hier/20_sync_component_hier_update_ref

# Step 1: Generate initial circuit
uv run test_20.py
open test_20/test_20.kicad_pro

# Step 2: Modify circuit (see test description)

# Step 3: Regenerate
uv run test_20.py

# Step 4: Verify changes
open test_20/test_20.kicad_pro
```

## Automated Test

```bash
pytest test_sync_component_hier_update_ref.py -v
```

## Expected Result

- ✅ Rename Component in Subcircuit successful
- ✅ All other elements preserved
