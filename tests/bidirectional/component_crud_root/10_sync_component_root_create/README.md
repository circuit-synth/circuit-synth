# Test 10: Add Component to Root Sheet

## What This Tests

Validates that adding a new component (R2) preserves all existing circuit elements:
- Existing components (R1, C1) with positions, values, footprints
- Power symbols (VCC, GND)
- Net labels (DATA)

## When This Situation Happens

- Developer has an existing circuit with components (R1, C1)
- Needs to add a new component (R2)
- Modifies Python code to include R2
- Regenerates KiCad project
- Expects: Only R2 added, everything else unchanged

## What Should Work

- ✅ Initial circuit with R1, C1 generates successfully
- ✅ Python code modified to add R2
- ✅ Regenerated project contains R1, R2, C1
- ✅ R1 and C1 unchanged (value, footprint, position)
- ✅ Power symbols and net labels preserved

## Manual Test Instructions

```bash
cd tests/bidirectional/component_crud_root/10_sync_component_root_create

# Step 1: Generate initial KiCad project (R1, C1 only)
uv run comprehensive_root.py
open comprehensive_root/comprehensive_root.kicad_pro
# Verify: R1 (10k) and C1 (100nF) present, no R2

# Step 2: Edit comprehensive_root.py
# Uncomment lines 28-33 to enable R2

# Step 3: Regenerate KiCad project
uv run comprehensive_root.py

# Step 4: Open regenerated project
open comprehensive_root/comprehensive_root.kicad_pro

# Step 5: Verify all three components present, R1 and C1 unchanged
```

## Automated Test

```bash
pytest test_add_component.py -v
```

## Expected Result

- ✅ Initial: R1 (10k), C1 (100nF), VCC, GND, DATA
- ✅ After adding R2: All above preserved + R2 (4.7k) added
- ✅ R1 and C1 positions not moved
- ✅ R2 placed without overlapping existing components
