# Bidirectional Test Suite - Manual Test Checklist

**Last Updated:** 2025-11-02
**Total Tests:** 71 comprehensive bidirectional tests
**Test Pattern:** One-folder-per-test with automated + manual verification
**Numbering:** Category-relative (each category starts at 01)

---

## 📋 How to Use This Checklist

1. **Run automated test** to generate KiCad files
2. **Open in KiCad GUI** and visually verify correctness
3. **Perform manual operations** as described in test README
4. **Verify position preservation** - the killer feature!
5. **Check the box** ✅ when verified

---

## ✅ Manual Testing Progress

### Component CRUD - Root Sheet (4 tests)

- [x] **Test 01**: Create component on root sheet - `component_crud_root/01_sync_component_root_create/` ✅ **Verified 2025-11-02** - R2 added with correct instance data (#479), labels, and power symbols (#489)
- [ ] **Test 02**: Update component value on root sheet - `component_crud_root/02_sync_component_root_update_value/`
- [ ] **Test 03**: Update component reference on root sheet - `component_crud_root/03_sync_component_root_update_ref/`
- [ ] **Test 04**: Delete component from root sheet - `component_crud_root/04_sync_component_root_delete/`

### Net CRUD - Root Sheet (4 tests)

- [ ] **Test 01**: Create net on root sheet - `net_crud_root/01_sync_net_root_create/`
- [ ] **Test 02**: Update net connection on root sheet - `net_crud_root/02_sync_net_root_update/`
- [ ] **Test 03**: Rename net on root sheet - `net_crud_root/03_sync_net_root_rename/`
- [ ] **Test 04**: Delete net from root sheet - `net_crud_root/04_sync_net_root_delete/`

### Component CRUD - Hierarchical (4 tests)

- [ ] **Test 01**: Create component in subcircuit - `component_crud_hier/01_sync_component_hier_create/`
- [ ] **Test 02**: Update component value in subcircuit - `component_crud_hier/02_sync_component_hier_update_value/`
- [ ] **Test 03**: Update component reference in subcircuit - `component_crud_hier/03_sync_component_hier_update_ref/`
- [ ] **Test 04**: Delete component from subcircuit - `component_crud_hier/04_sync_component_hier_delete/`

### Net CRUD - Hierarchical (4 tests)

- [ ] **Test 01**: Create net in subcircuit - `net_crud_hier/01_sync_net_hier_create/`
- [ ] **Test 02**: Update net connection in subcircuit - `net_crud_hier/02_sync_net_hier_update/`
- [ ] **Test 03**: Rename net in subcircuit - `net_crud_hier/03_sync_net_hier_rename/`
- [ ] **Test 04**: Delete net from subcircuit - `net_crud_hier/04_sync_net_hier_delete/`

### Sheet Operations (4 tests)

- [ ] **Test 01**: Create hierarchical sheet - `sheet_crud/01_sync_sheet_create/`
- [ ] **Test 02**: Update sheet properties - `sheet_crud/02_sync_sheet_update/`
- [ ] **Test 03**: Rename sheet - `sheet_crud/03_sync_sheet_rename/`
- [ ] **Test 04**: Delete sheet - `sheet_crud/04_sync_sheet_delete/`

### Label Operations (4 tests)

- [ ] **Test 01**: Create local label - `label_crud/01_sync_label_create/`
- [ ] **Test 02**: Update label text - `label_crud/02_sync_label_update/`
- [ ] **Test 03**: Rename label - `label_crud/03_sync_label_rename/`
- [ ] **Test 04**: Delete label - `label_crud/04_sync_label_delete/`

### Power Symbol Operations (4 tests)

- [ ] **Test 01**: Create power symbol - `power_symbol_crud/01_sync_power_create/`
- [ ] **Test 02**: Change power symbol type - `power_symbol_crud/02_sync_power_change_type/`
- [ ] **Test 03**: Rename power symbol - `power_symbol_crud/03_sync_power_rename/`
- [ ] **Test 04**: Delete power symbol - `power_symbol_crud/04_sync_power_delete/`

### Cross-Hierarchy Operations (4 tests)

- [ ] **Test 01**: Connect components across sheets - `cross_hierarchy/01_sync_cross_connect/`
- [ ] **Test 02**: Modify cross-hierarchy connections - `cross_hierarchy/02_sync_cross_modify/`
- [ ] **Test 03**: Move component between sheets - `cross_hierarchy/03_sync_cross_move/`
- [ ] **Test 04**: Propagate net across hierarchy - `cross_hierarchy/04_sync_cross_propagate/`

### Bulk Operations (4 tests)

- [ ] **Test 01**: Bulk add components - `bulk_operations/01_sync_bulk_add/`
- [ ] **Test 02**: Bulk update components - `bulk_operations/02_sync_bulk_update/`
- [ ] **Test 03**: Bulk delete components - `bulk_operations/03_sync_bulk_delete/`
- [ ] **Test 04**: Complete bulk workflow - `bulk_operations/04_sync_bulk_workflow/`

### Edge Cases (5 tests)

- [ ] **Test 01**: Empty circuit - `edge_cases/01_sync_empty_circuit/`
- [ ] **Test 02**: Duplicate component references - `edge_cases/02_sync_duplicate_refs/`
- [ ] **Test 03**: Invalid component values - `edge_cases/03_sync_invalid_values/`
- [ ] **Test 04**: Orphaned nets - `edge_cases/04_sync_orphaned_nets/`
- [ ] **Test 05**: Missing footprint - `edge_cases/05_sync_missing_footprint/`

### Rotation & Orientation (3 tests)

- [ ] **Test 01**: Component rotation - `rotation_orientation/01_sync_component_rotation/`
- [ ] **Test 02**: Component mirror - `rotation_orientation/02_sync_component_mirror/`
- [ ] **Test 03**: Mixed orientations - `rotation_orientation/03_sync_mixed_orientations/`

### Pin-Level Operations (3 tests)

- [ ] **Test 01**: Multi-pin component - `pin_level/01_sync_multi_pin_component/`
- [ ] **Test 02**: Swap pins - `pin_level/02_sync_swap_pins/`
- [ ] **Test 03**: Unconnected pins - `pin_level/03_sync_unconnected_pins/`

### Sheet Pin Operations (3 tests)

- [ ] **Test 01**: Sheet pin types - `sheet_pins/01_sync_sheet_pin_types/`
- [ ] **Test 02**: Sheet pin ordering - `sheet_pins/02_sync_sheet_pin_ordering/`
- [ ] **Test 03**: Mismatched pins - `sheet_pins/03_sync_mismatched_pins/`

### Special Net Types (4 tests)

- [ ] **Test 01**: Global labels - `special_nets/01_sync_global_labels/`
- [ ] **Test 02**: No-connect flags - `special_nets/02_sync_no_connect/`
- [ ] **Test 03**: Bus connections - `special_nets/03_sync_bus_connections/`
- [ ] **Test 04**: Net aliases - `special_nets/04_sync_net_aliases/`

### Annotation & References (3 tests)

- [ ] **Test 01**: Re-annotation - `annotation/01_sync_reannotation/`
- [ ] **Test 02**: Reference gaps - `annotation/02_sync_reference_gaps/`
- [ ] **Test 03**: Multi-unit components - `annotation/03_sync_multi_unit/`

### Schematic Properties (3 tests)

- [ ] **Test 01**: Text annotations - `schematic_props/01_sync_text_annotations/`
- [ ] **Test 02**: Graphic elements - `schematic_props/02_sync_graphic_elements/`
- [ ] **Test 03**: Wire styling - `schematic_props/03_sync_wire_styling/`

### Performance & Scale (3 tests)

- [ ] **Test 01**: Large circuit (100+ components) - `performance/01_sync_large_circuit/`
- [ ] **Test 02**: Deep hierarchy (5+ levels) - `performance/02_sync_deep_hierarchy/`
- [ ] **Test 03**: Wide hierarchy (10+ sheets) - `performance/03_sync_wide_hierarchy/`

### Regression Tests (3 tests)

- [ ] **Test 01**: DNP components - `regression/01_sync_dnp_components/`
- [ ] **Test 02**: Multiple value changes - `regression/02_sync_multiple_value_changes/`
- [ ] **Test 03**: Reference changes in hierarchy - `regression/03_sync_ref_changes_hier/`

### Real-World Workflows (5 tests)

- [ ] **Test 01**: Import subcircuit - `workflows/01_sync_import_subcircuit/`
- [ ] **Test 02**: Refactor to hierarchical - `workflows/02_sync_refactor_to_hier/`
- [ ] **Test 03**: Flatten hierarchy - `workflows/03_sync_flatten_hierarchy/`
- [ ] **Test 04**: Copy & paste - `workflows/04_sync_copy_paste/`
- [ ] **Test 05**: Design iteration - `workflows/05_sync_design_iteration/`

---

## 📊 Testing Progress Summary

**Total Tests:** 71
**Tests Verified:** 1 / 71

### Progress by Category:
- Component CRUD Root: 1 / 4
- Net CRUD Root: ___ / 4
- Component CRUD Hier: ___ / 4
- Net CRUD Hier: ___ / 4
- Sheet Operations: ___ / 4
- Label Operations: ___ / 4
- Power Symbols: ___ / 4
- Cross-Hierarchy: ___ / 4
- Bulk Operations: ___ / 4
- Edge Cases: ___ / 5
- Rotation/Orientation: ___ / 3
- Pin-Level: ___ / 3
- Sheet Pins: ___ / 3
- Special Nets: ___ / 4
- Annotation: ___ / 3
- Schematic Props: ___ / 3
- Performance: ___ / 3
- Regression: ___ / 3
- Workflows: ___ / 5

---

## 🎯 Test Execution Tips

### Running Individual Tests
```bash
# Navigate to test directory
cd tests/bidirectional/component_crud_root/01_sync_component_root_create/

# Run the circuit generation
uv run comprehensive_root.py

# Run pytest validation
pytest test_add_component.py -v --keep-output
```

### Running All Tests in a Category
```bash
pytest tests/bidirectional/component_crud_root/*/test_*.py -v
```

### Position Preservation Verification
The killer feature! For each test, verify:
1. **Initial generation** - Components appear at expected positions
2. **Regeneration** - Run circuit twice, unchanged components stay in exact same position
3. **Modification** - Change one component, verify others don't move

---

## 📝 Notes

- All test numbers are now **category-relative** (01-XX within each category)
- No more confusing global numbering (old Tests 10-80)
- Each category is independent and self-contained
- Test folder names clearly indicate category membership
