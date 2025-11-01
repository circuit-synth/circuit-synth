# Test 16: Rename Net

## What This Tests

Rename net while preserving connections

Operation: Rename DATA → SIG

## Manual Test Instructions

```bash
cd tests/bidirectional/net_crud_root/16_sync_net_root_rename

# Step 1: Generate initial circuit
uv run test_16.py
open test_16/test_16.kicad_pro

# Step 2: Modify circuit (see test description)

# Step 3: Regenerate
uv run test_16.py

# Step 4: Verify changes
open test_16/test_16.kicad_pro
```

## Automated Test

```bash
pytest test_sync_net_root_rename.py -v
```

## Expected Result

- ✅ Rename Net successful
- ✅ All other elements preserved
