# Test 17: Delete Net

## What This Tests

Remove net while preserving other nets

Operation: Delete CLK net

## Manual Test Instructions

```bash
cd tests/bidirectional/net_crud_root/17_sync_net_root_delete

# Step 1: Generate initial circuit
uv run test_17.py
open test_17/test_17.kicad_pro

# Step 2: Modify circuit (see test description)

# Step 3: Regenerate
uv run test_17.py

# Step 4: Verify changes
open test_17/test_17.kicad_pro
```

## Automated Test

```bash
pytest test_sync_net_root_delete.py -v
```

## Expected Result

- ✅ Delete Net successful
- ✅ All other elements preserved
