# Legacy Bidirectional Tests Archive

**Archived Date**: 2025-11-01
**Branch**: test/bidirectional-phase1-component-crud
**Reason**: Complete test refactoring - replaced with systematic CRUD test matrix

## Contents

This archive contains 68 original bidirectional synchronization tests (numbered 01-68, test 27 removed).

These tests were the initial implementation of bidirectional sync testing. They are being replaced with a systematic, comprehensive CRUD test matrix organized by element type and operation.

## Legacy Test List

Tests by category:

### Component CRUD (9 tests)
- 06_add_component
- 07_delete_component
- 08_modify_value
- 13_rename_component
- 19_swap_component_type
- 50_component_footprint_change
- 09_position_preservation
- 20_component_orientation
- 63_component_rotation_preservation

### Hierarchical Component CRUD (3 tests)
- 39_modify_component_in_subcircuit
- 41_copy_component_cross_sheet
- 42_move_component_between_sheets

### Net CRUD (6 tests)
- 10_generate_with_net
- 11_add_net_to_components
- 12_change_pin_connection
- 14_merge_nets
- 15_split_net
- 40_net_operations_in_subcircuit

### Sheet CRUD (4 tests)
- 22_add_subcircuit_sheet
- 23_remove_subcircuit_sheet
- 37_replace_subcircuit_contents
- 38_empty_subcircuit

### Hierarchical Pin/Label CRUD (4 tests)
- 44_subcircuit_hierarchical_ports
- 59_modify_hierarchical_pin_name
- 60_remove_hierarchical_pin
- 58_hierarchical_pin_to_global_label

### Power Symbol CRUD (3 tests)
- 16_add_power_symbol
- 17_add_ground_symbol
- 26_power_symbol_replacement

### Labels (2 tests)
- 24_add_global_label
- 25_add_local_label

### Bulk Operations (3 tests)
- 34_bulk_component_add
- 35_bulk_component_remove
- 36_copy_paste_component

### Generation Tests (14 tests)
- 01_blank_circuit
- 02_kicad_to_python
- 03_python_to_kicad
- 04_roundtrip
- 05_add_resistor_kicad_to_python
- 18_multiple_power_domains
- 21_multi_unit_components
- 28_add_no_connect
- 29_component_custom_properties
- 30_component_missing_footprint
- 31_isolated_component
- 32_text_annotations
- 33_bus_connections
- 43_differential_pairs

### Integration Tests (4 tests)
- 54_drc_validation
- 55_erc_validation
- 56_bom_export
- 51_sync_after_external_edit

### Conversion/Fidelity Tests (5 tests)
- 45_import_power_symbols_from_kicad
- 46_export_power_symbols_to_kicad
- 47_power_symbol_in_subcircuit
- 48_multi_voltage_subcircuit
- 62_wire_routing_preservation

### Special Tests (5 tests)
- 49_annotate_schematic
- 52_unicode_component_names
- 53_reference_collision_detection
- 57_global_label_multi_sheet
- 66_duplicate_net_names_isolation
- 67_connected_multi_level_hierarchy
- 68_dynamic_sheet_sizing

### Performance/Workflow Tests (2 tests)
- 61_large_circuit_performance
- 64_complex_multi_step_workflow

### Conflict Resolution (2 tests)
- 65_conflict_resolution

## New Test Organization

The replacement test structure is organized by:

### Element Type
- Components (root and hierarchical)
- Nets (root and hierarchical)
- Sheets
- Labels
- Power symbols
- Cross-hierarchy connections

### Operation Type
- Create
- Read/Verify
- Update (value, reference, footprint, type, position, rotation)
- Delete

### Test Categories
- `component_crud_root/` - Root component CRUD
- `component_crud_hier/` - Hierarchical component CRUD
- `net_crud_root/` - Root net CRUD
- `net_crud_hier/` - Hierarchical net CRUD
- `sheet_crud/` - Sheet management
- `label_crud/` - Label operations
- `power_crud/` - Power symbol operations
- `cross_hierarchy/` - Cross-hierarchy connections
- `bulk_operations/` - Bulk operations

Plus separate categories for:
- `generation/` - One-way generation tests
- `integration/` - External tool integration
- `conversion/` - Round-trip fidelity
- `performance/` - Stress tests

## Migration Plan

Selected tests from this archive will be:
1. Reviewed for coverage gaps
2. Migrated to new structure if still relevant
3. Rewritten to use new comprehensive preservation pattern
4. Enhanced with kicad-sch-api verification

See `../REFACTORING_PROGRESS.md` for current migration status.

## Restoration

If needed, these tests can be restored with:

```bash
cd tests/bidirectional/_archive_legacy_tests
mv [0-9][0-9]_* ../
```

## Compressed Archive

A compressed tar.gz archive is also available:
- Location: `tests/bidirectional/_archive_legacy_tests.tar.gz`
- Created: 2025-11-01
- Size: 945K (compressed from ~68 test folders)
