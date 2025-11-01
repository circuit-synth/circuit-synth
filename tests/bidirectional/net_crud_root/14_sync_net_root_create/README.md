# Test 14: Add Net

## What This Tests

Validates that adding a new net (CLK) connecting previously isolated components preserves all other elements:
- New CLK hierarchical label created
- R2 and C1 now connected via CLK
- R1, R2, C1 positions unchanged
- Existing DATA net preserved
- Power symbols (VCC, GND) preserved

## When This Situation Happens

- Developer has circuit with some isolated components
- Needs to connect R2 and C1 with a new CLK signal
- Adds CLK net in Python code
- Regenerates KiCad project
- Expects: CLK added, everything else unchanged

## What Should Work

- ✅ Initial circuit with R1, R2, C1 (R2, C1 isolated from signals)
- ✅ Python code modified to add CLK net connecting R2-C1
- ✅ Regenerated project has CLK label
- ✅ R2-C1 connected via CLK
- ✅ All component positions unchanged
- ✅ Existing DATA net preserved

## Manual Test Instructions

```bash
cd tests/bidirectional/net_crud_root/14_sync_net_root_create

# Step 1: Generate initial circuit (no CLK)
uv run comprehensive_root.py
open comprehensive_root/comprehensive_root.kicad_pro
# Verify: Only DATA label, R2 and C1 not connected

# Step 2: Edit comprehensive_root.py
# Uncomment line 50: clk = Net("CLK")
# Uncomment lines 58, 63: r2[2] += clk, c1[1] += clk

# Step 3: Regenerate circuit
uv run comprehensive_root.py

# Step 4: Open regenerated project
open comprehensive_root/comprehensive_root.kicad_pro

# Step 5: Verify addition
#   ✅ CLK label now present
#   ✅ R2[2] and C1[1] connected via CLK
#   ✅ DATA label still present
#   ✅ All component positions unchanged
```

## Automated Test

```bash
pytest test_add_net.py -v
```

## Expected Result

- ✅ Initial: DATA label only, R2 and C1 isolated
- ✅ After adding CLK: DATA and CLK labels
- ✅ R2-C1 connected via CLK
- ✅ All positions preserved
- ✅ Power symbols preserved
