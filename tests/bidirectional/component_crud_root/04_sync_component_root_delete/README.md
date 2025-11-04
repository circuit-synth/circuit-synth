# Test 13: Delete Component

## What This Tests

Validates that deleting a component (R2) preserves all other schematic elements:
- R1 and C1 completely unchanged (value, position, footprint)
- Power symbols (VCC, GND) preserved
- Net labels (DATA) preserved
- Component count decreases correctly (3 → 2)

## When This Situation Happens

- Developer has existing circuit with R1, R2, C1
- Needs to remove R2 from circuit
- Comments out or deletes R2 from Python code
- Regenerates KiCad project
- Expects: R2 removed, everything else unchanged

## What Should Work

- ✅ Initial circuit with R1, R2, C1 generates
- ✅ Python code modified to remove R2
- ✅ Regenerated project has only R1 and C1
- ✅ R1 value, position, footprint unchanged
- ✅ C1 value, position, footprint unchanged
- ✅ Power symbols and net labels preserved

## Manual Test Instructions

```bash
cd tests/bidirectional/component_crud_root/13_sync_component_root_delete

# Step 1: Generate initial circuit (R1, R2, C1)
uv run comprehensive_root.py
open comprehensive_root/comprehensive_root.kicad_pro
# Verify: Components R1, R2, C1 present

# Step 2: Edit comprehensive_root.py
# Comment out lines 29-35 (R2 definition)
# Comment out lines 52-53 (R2 connections)

# Step 3: Regenerate circuit
uv run comprehensive_root.py

# Step 4: Open regenerated project
open comprehensive_root/comprehensive_root.kicad_pro

# Step 5: Verify preservation
#   ✅ R2 no longer present
#   ✅ R1 still 10k at same position
#   ✅ C1 still 100nF at same position
#   ✅ VCC and GND power symbols present
#   ✅ DATA label present
```

## Automated Tests

```bash
# Test basic deletion
pytest test_delete_component.py::test_13_delete_component -v

# Test deletion with moved components (position preservation)
pytest test_delete_component.py::test_13b_delete_with_moved_components -v

# Run all tests
pytest test_delete_component.py -v
```

## Expected Results

### Test 13: Basic Deletion
- ✅ Initial: R1(10k), R2(4.7k), C1(100nF)
- ✅ After delete: R1(10k), C1(100nF)
- ✅ R1 position unchanged
- ✅ C1 position unchanged
- ✅ Power symbols and labels preserved
- ✅ Component count: 3 → 2

### Test 13b: Deletion with Moved Components
- ✅ Initial: R1, R2, C1 at default positions
- ✅ Move R1 to (50.8, 50.8) and C1 to (100.0, 60.0)
- ✅ Delete R2 in Python code
- ✅ Regenerate circuit
- ✅ **CRITICAL**: R1 and C1 remain at their MOVED positions
- ✅ Position preservation works correctly!

**Note:** Rotation preservation not tested here due to known issues (#517, #518).
Only position (X,Y) changes are tested, which work correctly.
