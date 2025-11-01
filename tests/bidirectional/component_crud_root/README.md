# Phase 1: Root Sheet Component CRUD Tests

This folder contains comprehensive tests for Component CRUD operations on root-level schematics.

## Test Coverage

All tests use the `comprehensive_root` fixture containing:
- **Components**: R1 (10k), R2 (4.7k), C1 (100nF)
- **Power**: VCC, GND
- **Labels**: DATA, CLK

Each test verifies **complete preservation** of all non-modified elements.

### Implemented Tests

| Test | Name | Operation | Status |
|------|------|-----------|--------|
| 10 | `sync_component_root_create` | Add component (R2) | ✅ PASS |
| 11 | `sync_component_root_update_value` | Update value (R1: 10k→47k) | ✅ PASS |
| 12 | `sync_component_root_update_ref` | Rename reference (R1→R10) | ✅ PASS |
| 13 | `sync_component_root_delete` | Delete component (R2) | ✅ PASS |
| 14 | `sync_component_root_update_footprint` | Change footprint | 🔲 TODO |
| 15 | `sync_component_root_update_type` | Change type (R→C) | 🔲 TODO |
| 16 | `sync_component_root_position_preserve` | Position preservation | 🔲 TODO |
| 17 | `sync_component_root_rotation_preserve` | Rotation preservation | 🔲 TODO |

## Test Pattern

Each test follows this structure:

```python
def test_XX_sync_component_root_<operation>(request):
    """Test <operation> while preserving all other elements."""

    # STEP 1: Generate initial state
    # - Verify: all expected components, power, labels
    # - Capture: initial state for comparison

    # STEP 2: Perform CRUD operation
    # - Modify Python code
    # - Regenerate schematic
    # - Verify: operation succeeded
    # - Verify: ALL other elements unchanged
```

## Preservation Checks

Every test verifies:
1. ✅ **Component preservation**: value, footprint, lib_id, position, rotation
2. ✅ **Power symbol preservation**: VCC, GND unchanged
3. ✅ **Label preservation**: DATA, CLK unchanged (where applicable)
4. ✅ **Count verification**: Exact component counts match expectations

## Running Tests

```bash
# Run all component CRUD root tests
pytest tests/bidirectional/component_crud_root/ -v

# Run specific test
pytest tests/bidirectional/component_crud_root/test_10_sync_component_root_create.py -v

# Keep output for inspection
pytest tests/bidirectional/component_crud_root/ -v --keep-output
```

## Dependencies

- **kicad-sch-api >= 0.4.5**: For hierarchical_labels property
- **Fixture**: `comprehensive_root.py` in `../fixtures/`
- **Helpers**: Verification functions in `../fixtures/helpers.py`

## Notes

- **Label behavior**: CLK label may persist even when no components connect to it (Net() definition creates label)
- **Power preservation**: Power symbols preserved by default (preserve_user_components=True)
- **Sync logs**: May not be visible when running fixtures as standalone scripts
