# Test 12: Update Component Reference (Rename)

## What This Tests

Validates that renaming a component (R1 → R100) preserves all other schematic elements:
- R100 (formerly R1) value, footprint, rotation, position unchanged
- R2 and C1 completely unchanged
- Power symbols (VCC, GND) preserved
- Net labels (DATA) preserved

## When This Situation Happens

- Developer has existing circuit with component R1
- Needs to rename R1 to R100 (e.g., for better organization)
- Modifies Python code to change reference
- Regenerates KiCad project
- Expects: Only reference changes, all properties preserved

## What Should Work

- ✅ Initial circuit with R1, R2, C1 generates
- ✅ Python code modified to rename R1 → R100
- ✅ Regenerated project has R100 instead of R1
- ✅ R100 has same value, position, footprint as old R1
- ✅ R2 and C1 unchanged
- ✅ Power symbols and net labels preserved

## Manual Test Instructions

```bash
cd tests/bidirectional/component_crud_root/12_sync_component_root_update_ref

# Step 1: Generate initial circuit (R1, R2, C1)
uv run comprehensive_root.py
open comprehensive_root/comprehensive_root.kicad_pro
# Verify: Components R1, R2, C1 present

# Step 2: Edit comprehensive_root.py
# Change line 24: ref="R1" → ref="R100"

# Step 3: Regenerate circuit
uv run comprehensive_root.py

# Step 4: Open regenerated project
open comprehensive_root/comprehensive_root.kicad_pro

# Step 5: Verify preservation
#   ✅ R100 exists (R1 renamed)
#   ✅ R1 no longer exists
#   ✅ R100 has same value (10k), position, footprint as old R1
#   ✅ R2 still 4.7k at same position
#   ✅ C1 still 100nF at same position
```

## Automated Test

```bash
pytest test_update_ref.py -v
```

## Expected Result

- ✅ Initial: R1(10k), R2(4.7k), C1(100nF)
- ✅ After rename: R100(10k), R2(4.7k), C1(100nF)
- ✅ R100 position same as old R1 (preserved)
- ✅ R100 properties same as old R1
- ✅ R2 and C1 unchanged
- ✅ Power symbols and labels preserved
