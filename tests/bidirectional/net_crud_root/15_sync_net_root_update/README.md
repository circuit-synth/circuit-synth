# Test 15: Update Net Connection

## What This Tests

Modify which pins a net connects to

Operation: Change R2[2] from CLK to DATA

## Manual Test Instructions

```bash
cd tests/bidirectional/net_crud_root/15_sync_net_root_update

# Step 1: Generate initial circuit
uv run test_15.py
open test_15/test_15.kicad_pro

# Step 2: Modify circuit (see test description)

# Step 3: Regenerate
uv run test_15.py

# Step 4: Verify changes
open test_15/test_15.kicad_pro
```

## Automated Test

```bash
pytest test_sync_net_root_update.py -v
```

## Expected Result

- ✅ Update Net Connection successful
- ✅ All other elements preserved
