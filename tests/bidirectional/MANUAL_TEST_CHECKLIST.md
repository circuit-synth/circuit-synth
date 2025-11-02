# Bidirectional Test Suite - Manual Test Checklist

**Last Updated:** 2025-11-01
**Total Tests:** 71 comprehensive bidirectional tests (Tests 10-80)
**Test Pattern:** One-folder-per-test with automated + manual verification
**Related PR:** #461 (test/bidirectional-phase1-component-crud)

---

## 📋 How to Use This Checklist

1. **Run automated test** to generate KiCad files
2. **Open in KiCad GUI** and visually verify correctness
3. **Perform manual operations** as described in test README
4. **Verify position preservation** - the killer feature!
5. **Check the box** ✅ when verified

---

## ✅ Manual Testing Progress

### Core CRUD Operations - Root Sheet (8 tests)

#### Component CRUD - Root
- [ ] **Test 10**: Create component on root sheet - `component_crud_root/10_sync_component_root_create/`
- [ ] **Test 11**: Update component value on root sheet - `component_crud_root/11_sync_component_root_update_value/`
- [ ] **Test 12**: Update component reference on root sheet - `component_crud_root/12_sync_component_root_update_ref/`
- [ ] **Test 13**: Delete component from root sheet - `component_crud_root/13_sync_component_root_delete/`

#### Net CRUD - Root
- [ ] **Test 14**: Create net on root sheet - `net_crud_root/14_sync_net_root_create/`
- [ ] **Test 15**: Update net connection on root sheet - `net_crud_root/15_sync_net_root_update/`
- [ ] **Test 16**: Rename net on root sheet - `net_crud_root/16_sync_net_root_rename/`
- [ ] **Test 17**: Delete net from root sheet - `net_crud_root/17_sync_net_root_delete/`

### Core CRUD Operations - Hierarchical (8 tests)

#### Component CRUD - Hierarchical
- [ ] **Test 18**: Create component in subcircuit - `component_crud_hier/18_sync_component_hier_create/`
- [ ] **Test 19**: Update component value in subcircuit - `component_crud_hier/19_sync_component_hier_update_value/`
- [ ] **Test 20**: Update component reference in subcircuit - `component_crud_hier/20_sync_component_hier_update_ref/`
- [ ] **Test 21**: Delete component from subcircuit - `component_crud_hier/21_sync_component_hier_delete/`

#### Net CRUD - Hierarchical
- [ ] **Test 22**: Create net in subcircuit - `net_crud_hier/22_sync_net_hier_create/`
- [ ] **Test 23**: Update net connection in subcircuit - `net_crud_hier/23_sync_net_hier_update/`
- [ ] **Test 24**: Rename net in subcircuit - `net_crud_hier/24_sync_net_hier_rename/`
- [ ] **Test 25**: Delete net from subcircuit - `net_crud_hier/25_sync_net_hier_delete/`

### Sheet Operations (4 tests)

- [ ] **Test 26**: Create hierarchical sheet - `sheet_crud/26_sync_sheet_create/`
- [ ] **Test 27**: Update sheet properties - `sheet_crud/27_sync_sheet_update/`
- [ ] **Test 28**: Rename sheet - `sheet_crud/28_sync_sheet_rename/`
- [ ] **Test 29**: Delete sheet - `sheet_crud/29_sync_sheet_delete/`

### Label Operations (4 tests)

- [ ] **Test 30**: Create local label - `label_crud/30_sync_label_create/`
- [ ] **Test 31**: Update label text - `label_crud/31_sync_label_update/`
- [ ] **Test 32**: Move label - `label_crud/32_sync_label_move/`
- [ ] **Test 33**: Delete label - `label_crud/33_sync_label_delete/`

### Power Symbol Operations (4 tests)

- [ ] **Test 34**: Create power symbol - `power_symbol_crud/34_sync_power_create/`
- [ ] **Test 35**: Update power net - `power_symbol_crud/35_sync_power_update/`
- [ ] **Test 36**: Replace power symbol type - `power_symbol_crud/36_sync_power_replace/`
- [ ] **Test 37**: Delete power symbol - `power_symbol_crud/37_sync_power_delete/`

### Cross-Hierarchy Operations (4 tests)

- [ ] **Test 38**: Connect components across sheets - `cross_hierarchy/38_sync_cross_connect/`
- [ ] **Test 39**: Move component between sheets - `cross_hierarchy/39_sync_cross_move/`
- [ ] **Test 40**: Copy component to another sheet - `cross_hierarchy/40_sync_cross_copy/`
- [ ] **Test 41**: Propagate net across hierarchy - `cross_hierarchy/41_sync_cross_propagate/`

### Bulk Operations (4 tests)

- [ ] **Test 42**: Bulk add components - `bulk_operations/42_sync_bulk_add/`
- [ ] **Test 43**: Bulk update components - `bulk_operations/43_sync_bulk_update/`
- [ ] **Test 44**: Bulk delete components - `bulk_operations/44_sync_bulk_delete/`
- [ ] **Test 45**: Complete bulk workflow - `bulk_operations/45_sync_bulk_workflow/`

### Edge Cases (5 tests)

- [ ] **Test 46**: Empty circuit - `edge_cases/46_sync_empty_circuit/`
- [ ] **Test 47**: Duplicate component references - `edge_cases/47_sync_duplicate_refs/`
- [ ] **Test 48**: Invalid component values - `edge_cases/48_sync_invalid_values/`
- [ ] **Test 49**: Missing footprint - `edge_cases/49_sync_missing_footprint/`
- [ ] **Test 50**: Unconnected component - `edge_cases/50_sync_unconnected/`

### Rotation & Orientation (3 tests)

- [ ] **Test 51**: Component rotation 90° - `rotation_orientation/51_sync_rotation_90/`
- [ ] **Test 52**: Component rotation 180° - `rotation_orientation/52_sync_rotation_180/`
- [ ] **Test 53**: Component mirroring - `rotation_orientation/53_sync_mirror/`

### Pin-Level Operations (3 tests)

- [ ] **Test 54**: Pin swap - `pin_level/54_sync_pin_swap/`
- [ ] **Test 55**: Pin rename - `pin_level/55_sync_pin_rename/`
- [ ] **Test 56**: No-connect flags - `pin_level/56_sync_no_connect/`

### Sheet Pin Operations (3 tests)

- [ ] **Test 57**: Create sheet pin - `sheet_pins/57_sync_sheet_pin_create/`
- [ ] **Test 58**: Rename sheet pin - `sheet_pins/58_sync_sheet_pin_rename/`
- [ ] **Test 59**: Delete sheet pin - `sheet_pins/59_sync_sheet_pin_delete/`

### Special Nets (4 tests)

- [ ] **Test 60**: Global labels - `special_nets/60_sync_global_label/`
- [ ] **Test 61**: Bus connections - `special_nets/61_sync_bus/`
- [ ] **Test 62**: Bus aliases - `special_nets/62_sync_bus_alias/`
- [ ] **Test 63**: Differential pairs - `special_nets/63_sync_diff_pair/`

### Annotation & References (3 tests)

- [ ] **Test 64**: Re-annotation - `annotation/64_sync_reannotation/`
- [ ] **Test 65**: Reference gap filling - `annotation/65_sync_reference_gaps/`
- [ ] **Test 66**: Multi-unit component annotation - `annotation/66_sync_multi_unit/`

### Schematic Properties (3 tests)

- [ ] **Test 67**: Text annotations - `schematic_props/67_sync_text_annotation/`
- [ ] **Test 68**: Graphic lines - `schematic_props/68_sync_graphics/`
- [ ] **Test 69**: Sheet properties - `schematic_props/69_sync_sheet_properties/`

### Performance & Scale (3 tests)

- [ ] **Test 70**: Large circuit (1000+ components) - `performance/70_sync_large_circuit/`
- [ ] **Test 71**: Deep hierarchy (10+ levels) - `performance/71_sync_deep_hierarchy/`
- [ ] **Test 72**: Wide hierarchy (50+ subcircuits) - `performance/72_sync_wide_hierarchy/`

### Regression Tests (3 tests)

- [ ] **Test 73**: Label placement regression - `regression/73_sync_label_placement/`
- [ ] **Test 74**: Symbol placement regression - `regression/74_sync_symbol_placement/`
- [ ] **Test 75**: Net naming regression - `regression/75_sync_net_naming/`

### Real-World Workflows (5 tests)

- [ ] **Test 76**: Voltage divider design - `workflows/76_sync_voltage_divider/`
- [ ] **Test 77**: LED driver circuit - `workflows/77_sync_led_driver/`
- [ ] **Test 78**: Power supply design - `workflows/78_sync_power_supply/`
- [ ] **Test 79**: Microcontroller circuit - `workflows/79_sync_microcontroller/`
- [ ] **Test 80**: Complete PCB project - `workflows/80_sync_complete_project/`

---

## 📊 Testing Progress Summary

**Total Tests:** 71
**Tests Verified:** ___ / 71
**Automated Passing:** 68 / 71 (from PR #461)
**Expected Failures:** 3 / 71

---

## 🎯 The Killer Feature

**Position Preservation** - When you regenerate from Python after manually arranging in KiCad, positions are preserved!

---

## 🚀 Running Tests

```bash
# Run all tests
pytest tests/bidirectional/*/*/test_*.py -v

# Run by category
pytest tests/bidirectional/component_crud_root/*/test_*.py -v

# Keep output for manual inspection
pytest tests/bidirectional/*/10_*/test_*.py -v --keep-output
```

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
