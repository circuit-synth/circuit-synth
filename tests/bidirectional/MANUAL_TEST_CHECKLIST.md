# Manual Test Verification Checklist

Use this checklist to manually verify each bidirectional test works correctly.

## How to Use This Checklist

For each test:
1. Navigate to the test folder
2. Run `uv run comprehensive_root.py` (or test circuit file)
3. Open the generated KiCad project
4. Verify the test behavior manually in KiCad
5. Check the box when verified ✅

---

## Component CRUD - Root Sheet (Tests 10-13)

### ☐ Test 10: Add Component to Root Sheet
- **Folder**: `tests/bidirectional/component_crud_root/10_sync_component_root_create/`
- **Operation**: Add R2 component while preserving R1, C1
- **Verification**:
  - [ ] Initial: R1, C1 present (no R2)
  - [ ] Uncomment R2 in code
  - [ ] Regenerate: R1, C1, R2 all present
  - [ ] R1, C1 positions unchanged
  - [ ] Automated test passes: `pytest test_add_component.py -v`

### ☐ Test 11: Update Component Value
- **Folder**: `tests/bidirectional/component_crud_root/11_sync_component_root_update_value/`
- **Operation**: Change R1 value from 10k to 47k
- **Verification**:
  - [ ] Initial: R1 = 10k
  - [ ] Modify code: R1 = 47k
  - [ ] Regenerate: R1 = 47k
  - [ ] R1 position unchanged
  - [ ] R2, C1 completely unchanged
  - [ ] Automated test passes: `pytest test_update_value.py -v`

### ☐ Test 12: Rename Component
- **Folder**: `tests/bidirectional/component_crud_root/12_sync_component_root_update_ref/`
- **Operation**: Rename R1 → R100
- **Verification**:
  - [ ] Initial: R1 present
  - [ ] Modify code: ref="R100"
  - [ ] Regenerate: R100 present (R1 gone)
  - [ ] R100 has same value, position as old R1
  - [ ] R2, C1 unchanged
  - [ ] Automated test passes: `pytest test_update_ref.py -v`

### ☐ Test 13: Delete Component
- **Folder**: `tests/bidirectional/component_crud_root/13_sync_component_root_delete/`
- **Operation**: Delete R2 component
- **Verification**:
  - [ ] Initial: R1, R2, C1 present
  - [ ] Comment out R2 in code
  - [ ] Regenerate: R1, C1 present (R2 gone)
  - [ ] R1, C1 positions unchanged
  - [ ] Component count: 3 → 2
  - [ ] Automated test passes: `pytest test_delete_component.py -v`

---

## Net CRUD - Root Sheet (Tests 14-17)

### ☐ Test 14: Add Net
- **Folder**: `tests/bidirectional/net_crud_root/14_sync_net_root_create/`
- **Operation**: Add CLK net connecting R2-C1
- **Verification**:
  - [ ] Initial: DATA label only
  - [ ] Uncomment CLK net in code
  - [ ] Regenerate: DATA and CLK labels present
  - [ ] R2-C1 connected via CLK
  - [ ] All positions unchanged
  - [ ] Automated test passes: `pytest test_add_net.py -v`

### ☐ Test 15: Update Net Connection
- **Folder**: `tests/bidirectional/net_crud_root/15_sync_net_root_update/`
- **Operation**: Change R2[2] from CLK to DATA
- **Verification**:
  - [ ] Initial: R2[2] on CLK
  - [ ] Modify code: r2[2] += data
  - [ ] Regenerate: R2[2] on DATA
  - [ ] CLK still exists (C1[1] still connected)
  - [ ] All positions unchanged
  - [ ] Automated test passes: `pytest test_update.py -v`

### ☐ Test 16: Rename Net
- **Folder**: `tests/bidirectional/net_crud_root/16_sync_net_root_rename/`
- **Operation**: Rename DATA → SIG
- **Verification**:
  - [ ] Initial: DATA label exists
  - [ ] Modify code: Net("SIG")
  - [ ] Regenerate: SIG label exists (DATA gone)
  - [ ] Connections preserved on SIG net
  - [ ] All positions unchanged
  - [ ] Automated test passes: `pytest test_rename.py -v`

### ☐ Test 17: Delete Net
- **Folder**: `tests/bidirectional/net_crud_root/17_sync_net_root_delete/`
- **Operation**: Delete CLK net
- **Verification**:
  - [ ] Initial: DATA, CLK labels exist
  - [ ] Comment out CLK net in code
  - [ ] Regenerate: Only DATA label exists
  - [ ] DATA connections preserved
  - [ ] All positions unchanged
  - [ ] Automated test passes: `pytest test_delete.py -v`

---

## Component CRUD - Hierarchical Sheets (Tests 18-21)

### ☐ Test 18: Add Component in Subcircuit
- **Folder**: `tests/bidirectional/component_crud_hier/18_sync_component_hier_create/`
- **Operation**: Add R3 to subcircuit
- **Status**: ⏳ Scaffold only - needs implementation

### ☐ Test 19: Update Component Value in Subcircuit
- **Folder**: `tests/bidirectional/component_crud_hier/19_sync_component_hier_update_value/`
- **Operation**: Update R1 in subcircuit: 10k → 47k
- **Status**: ⏳ Scaffold only - needs implementation

### ☐ Test 20: Rename Component in Subcircuit
- **Folder**: `tests/bidirectional/component_crud_hier/20_sync_component_hier_update_ref/`
- **Operation**: Rename R1 → R100 in subcircuit
- **Status**: ⏳ Scaffold only - needs implementation

### ☐ Test 21: Delete Component in Subcircuit
- **Folder**: `tests/bidirectional/component_crud_hier/21_sync_component_hier_delete/`
- **Operation**: Delete R2 from subcircuit
- **Status**: ⏳ Scaffold only - needs implementation

---

## Net CRUD - Hierarchical Sheets (Tests 22-25)

### ☐ Test 22: Add Net in Subcircuit
- **Status**: 📋 Not yet created

### ☐ Test 23: Update Net in Subcircuit
- **Status**: 📋 Not yet created

### ☐ Test 24: Rename Net in Subcircuit
- **Status**: 📋 Not yet created

### ☐ Test 25: Delete Net in Subcircuit
- **Status**: 📋 Not yet created

---

## Sheet CRUD Operations (Tests 26-29)

### ☐ Test 26: Add Hierarchical Sheet
- **Status**: 📋 Not yet created

### ☐ Test 27: Update Sheet Properties
- **Status**: 📋 Not yet created

### ☐ Test 28: Rename Sheet
- **Status**: 📋 Not yet created

### ☐ Test 29: Delete Sheet
- **Status**: 📋 Not yet created

---

## Label CRUD Operations (Tests 30-33)

### ☐ Test 30: Add Hierarchical Label
- **Status**: 📋 Not yet created

### ☐ Test 31: Update Label Properties
- **Status**: 📋 Not yet created

### ☐ Test 32: Rename Label
- **Status**: 📋 Not yet created

### ☐ Test 33: Delete Label
- **Status**: 📋 Not yet created

---

## Power Symbol CRUD (Tests 34-37)

### ☐ Test 34: Add Power Symbol
- **Status**: 📋 Not yet created

### ☐ Test 35: Change Power Symbol Type
- **Status**: 📋 Not yet created

### ☐ Test 36: Rename Power Net
- **Status**: 📋 Not yet created

### ☐ Test 37: Delete Power Symbol
- **Status**: 📋 Not yet created

---

## Cross-Hierarchy Operations (Tests 38-41)

### ☐ Test 38: Connect Across Sheets
- **Status**: 📋 Not yet created

### ☐ Test 39: Modify Cross-Sheet Connection
- **Status**: 📋 Not yet created

### ☐ Test 40: Move Component Between Sheets
- **Status**: 📋 Not yet created

### ☐ Test 41: Propagate Changes Up/Down Hierarchy
- **Status**: 📋 Not yet created

---

## Bulk Operations (Tests 42-45)

### ☐ Test 42: Add Multiple Components
- **Status**: 📋 Not yet created

### ☐ Test 43: Update Multiple Components
- **Status**: 📋 Not yet created

### ☐ Test 44: Delete Multiple Components
- **Status**: 📋 Not yet created

### ☐ Test 45: Complex Multi-Operation Workflow
- **Status**: 📋 Not yet created

---

## Overall Progress

**Completed & Ready for Manual Verification**: 6/45 (13%)
- Tests 10-15: ✅ Fully implemented

**Scaffolded (Needs Implementation)**: 7/45 (16%)
- Tests 16-21: ⏳ Structure created, needs code

**Not Yet Created**: 32/45 (71%)
- Tests 22-45: 📋 Planned but not generated

---

## Notes

- **✅ = Ready for manual testing**
- **⏳ = Scaffold exists, needs implementation**
- **📋 = Not yet created**

## Quick Test Commands

Run all implemented tests:
```bash
cd tests/bidirectional
pytest component_crud_root/*/test_*.py net_crud_root/14_*/test_*.py net_crud_root/15_*/test_*.py -v
```

Run specific test:
```bash
cd tests/bidirectional/component_crud_root/10_sync_component_root_create
pytest test_add_component.py -v
```

Keep test outputs for inspection:
```bash
pytest test_add_component.py -v --keep-output
```

---

**Last Updated**: 2025-11-01
**Branch**: test/bidirectional-phase1-component-crud
