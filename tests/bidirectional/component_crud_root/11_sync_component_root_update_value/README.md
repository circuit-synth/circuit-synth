# Test 11: Update Component Value

## What This Tests

Validates that updating a component value (R1: 10k → 47k) preserves all other schematic elements:
- R1 position, footprint, rotation unchanged
- R2 and C1 completely unchanged
- Power symbols (VCC, GND) preserved
- Net labels (DATA) preserved

## When This Situation Happens

- Developer has existing circuit with component R1 (10k)
- Needs to change R1 value to 47k
- Modifies Python code to update value
- Regenerates KiCad project
- Expects: Only R1 value changes, everything else identical

## What Should Work

- ✅ Initial circuit with R1(10k), R2(4.7k), C1(100nF) generates
- ✅ Python code modified to change R1 value to 47k
- ✅ Regenerated project has R1=47k
- ✅ R1 position, footprint, rotation unchanged
- ✅ R2 and C1 values, positions, properties unchanged
- ✅ Power symbols and net labels preserved

## Manual Test Instructions

```bash
cd tests/bidirectional/component_crud_root/11_sync_component_root_update_value

# Step 1: Generate initial circuit (R1=10k)
uv run comprehensive_root.py
open comprehensive_root/comprehensive_root.kicad_pro
# Verify: R1 value is 10k

# Step 2: Edit comprehensive_root.py
# Change line 25: value="10k" → value="47k"

# Step 3: Regenerate circuit
uv run comprehensive_root.py

# Step 4: Open regenerated project
open comprehensive_root/comprehensive_root.kicad_pro

# Step 5: Verify preservation
#   ✅ R1 value now 47k
#   ✅ R1 position unchanged (not moved)
#   ✅ R2 still 4.7k at same position
#   ✅ C1 still 100nF at same position
#   ✅ VCC and GND power symbols present
```

## Automated Test

```bash
pytest test_update_value.py -v
```

## Expected Result

- ✅ Initial: R1(10k), R2(4.7k), C1(100nF), VCC, GND, DATA
- ✅ After update: R1(47k), R2(4.7k), C1(100nF), VCC, GND, DATA
- ✅ R1 position preserved (not moved)
- ✅ R2 and C1 positions preserved
- ✅ Power symbols and labels preserved
