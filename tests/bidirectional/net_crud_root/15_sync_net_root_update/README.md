# Test 15: Update Net Connection

## What This Tests

Validates that changing which net a pin connects to (R2[2]: CLK → DATA) preserves all other elements:
- Net connections updated
- All component positions unchanged
- Other nets (DATA) preserved
- Power symbols (VCC, GND) preserved
- CLK label still exists (C1[1] still connected to it)

## When This Situation Happens

- Developer has circuit with components on different nets
- Needs to change which net a pin connects to (merge nets or reroute)
- Modifies Python code to change pin connection
- Regenerates KiCad project
- Expects: Only specified connection changes, everything else unchanged

## What Should Work

- ✅ Initial circuit with R1, R2, C1 on DATA and CLK nets
- ✅ Python code modified to change R2[2] from CLK to DATA
- ✅ Regenerated project has R2[2] on DATA
- ✅ All component positions unchanged
- ✅ CLK label still exists (C1[1] still uses it)
- ✅ Power symbols and other nets preserved

## Manual Test Instructions

```bash
cd tests/bidirectional/net_crud_root/15_sync_net_root_update

# Step 1: Generate initial circuit (R2[2] on CLK)
uv run comprehensive_root.py
open comprehensive_root/comprehensive_root.kicad_pro
# Verify: R2[2] on CLK, C1[1] on CLK

# Step 2: Edit comprehensive_root.py
# Change line 54: r2[2] += clk  →  r2[2] += data

# Step 3: Regenerate circuit
uv run comprehensive_root.py

# Step 4: Open regenerated project
open comprehensive_root/comprehensive_root.kicad_pro

# Step 5: Verify update
#   ✅ R2[2] now on DATA (changed from CLK)
#   ✅ C1[1] still on CLK (unchanged)
#   ✅ All component positions unchanged
#   ✅ CLK label still exists
```

## Automated Test

```bash
pytest test_update.py -v
```

## Expected Result

- ✅ Initial: DATA (R1-R2), CLK (R2-C1)
- ✅ After update: DATA (R1-R2), CLK (C1 only), R2[2] moved to DATA
- ✅ All positions preserved
- ✅ Both labels still exist
- ✅ Power symbols preserved
