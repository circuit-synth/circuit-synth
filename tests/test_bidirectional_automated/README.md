## Automated Bidirectional Sync Tests

Automated pytest suite for validating Python ↔ KiCad bidirectional synchronization.

### Overview

These tests use **programmatic manipulation** via `kicad-sch-api` to simulate manual KiCad edits, enabling fully automated testing of bidirectional sync workflows.

**Key principle**: We trust `kicad-sch-api` (validated by its own 302-test suite) to reliably read/write KiCad files, allowing us to automate tests that would otherwise require manual KiCad interaction.

### Test Coverage

| Test File | Tests | Coverage |
|-----------|-------|----------|
| `test_python_to_kicad.py` | 10 | Python → KiCad generation |
| `test_kicad_to_python.py` | 4 | KiCad → Python import |
| `test_roundtrip.py` | 5 | Python → KiCad → Python consistency |
| `test_position_preservation.py` | 4 | Manual position preservation (CRITICAL) |
| `test_component_operations.py` | 7 | Add/delete/modify/rename components |
| `test_net_operations.py` | 9 | Net creation/modification/deletion |

**Total**: 39 automated tests covering 26 manual test scenarios

### Running Tests

```bash
# Run all automated bidirectional tests
pytest tests/test_bidirectional_automated/ -v

# Run specific test file
pytest tests/test_bidirectional_automated/test_python_to_kicad.py -v

# Run specific test
pytest tests/test_bidirectional_automated/test_python_to_kicad.py::TestPythonToKiCadGeneration::test_01_blank_circuit -v

# Run with coverage
pytest tests/test_bidirectional_automated/ -v --cov=circuit_synth.kicad
```

### Test Architecture

```
tests/test_bidirectional_automated/
├── conftest.py                      # Pytest fixtures
├── fixtures/
│   ├── circuits.py                  # Circuit fixture generators
│   └── assertions.py                # Semantic assertion helpers
├── test_python_to_kicad.py          # Generation tests
├── test_kicad_to_python.py          # Import tests
├── test_roundtrip.py                # Consistency tests
├── test_position_preservation.py    # Position tests (CRITICAL)
├── test_component_operations.py     # Component manipulation
└── test_net_operations.py           # Net operations
```

### Manual Tests Still Available

The original manual tests in `tests/bidirectional/` are **preserved and runnable**:

```bash
# Run manual tests as before
cd tests/bidirectional/01_blank_circuit
uv run blank.py
open blank/blank.kicad_pro
```

### Mapping: Manual → Automated Tests

| Manual Test | Automated Test | Description |
|-------------|---------------|-------------|
| 01_blank_circuit | `test_01_blank_circuit` | Blank circuit generation |
| 02_kicad_to_python | `test_02_import_generated_schematic` | Import generated schematic |
| 03_python_to_kicad | `test_03_single_resistor` | Single component generation |
| 04_roundtrip | `test_04_simple_roundtrip` | Round-trip consistency |
| 05_add_resistor_kicad_to_python | `test_05_add_component_in_kicad_then_import` | Add in KiCad, import to Python |
| 06_add_component | `test_06_add_component` | Add component operation |
| 07_delete_component | `test_07_delete_component` | Delete component operation |
| 08_modify_value | `test_08_modify_component_value` | Modify component value |
| 09_position_preservation | `test_09_position_preserved_when_adding_component` | **KILLER FEATURE** - position preservation |
| 10_generate_with_net | `test_10_generate_circuit_with_net` | Net generation |
| 11_add_net_to_components | `test_11_add_net_to_existing_components` | Add net to existing components |
| 12_add_to_net | (covered by test_11) | Add component to net |
| 13_rename_component | `test_13_rename_component` | Rename component reference |
| 14_incremental_growth | `test_14_incremental_growth_roundtrip` | Multiple iteration cycles |
| 15_complex_no_overlap | `test_15_complex_circuit` | Complex circuit generation |
| 16_rename_python_canonical | `test_16_position_preserved_on_regeneration` | Position on regeneration |
| 17_remove_from_net | (part of net operations) | Remove component from net |
| 18_rename_net | `test_18_rename_net` | Rename net |
| 19_delete_net | `test_19_delete_net` | Delete net |
| 20_change_pin_on_net | (future) | Change pin connection |
| 21_split_net | `test_21_split_net` | Split net into two |
| 22_merge_nets | `test_22_merge_nets` | Merge two nets |
| 23_multiple_nets_per_component | `test_23_multiple_nets_per_component` | Component on multiple nets |
| 24_auto_net_name | `test_24_auto_net_naming` | Auto-generated net names |
| 25_add_component_and_net | `test_25_add_component_and_net_together` | Add component + connect to net |
| 26_power_symbol_replacement | (future - needs power symbol support) | Power symbols |

### Key Testing Principles

1. **Semantic Assertions**: Test *what matters* (component properties, connections) not exact bytes
2. **Tolerance-Based Comparison**: Account for grid snapping and floating-point rounding
3. **Programmatic Manipulation**: Use `kicad-sch-api` to simulate KiCad edits
4. **Round-Trip Validation**: Verify Python → KiCad → Python preserves data
5. **Position Preservation**: The killer feature - manual layout work survives regeneration

### Fixtures and Helpers

#### `conftest.py` Fixtures

- `temp_project_dir`: Temporary directory for test projects (auto-cleanup)
- `parse_schematic`: Parse KiCad schematic using kicad-sch-api
- `assert_component_equal`: Semantic component comparison
- `create_schematic`: Factory for creating schematics

#### `fixtures/circuits.py` Generators

- `blank()`: Empty circuit
- `single_resistor()`: Single 10kΩ resistor
- `two_resistors()`: Two resistors (10k, 4.7k)
- `two_resistors_connected()`: Two resistors on NET1
- `three_resistors_on_net()`: Three resistors on NET1
- `four_resistors_two_nets()`: Four resistors on NET1, NET2
- `voltage_regulator_led()`: Complex circuit (regulator + LED)

#### `fixtures/assertions.py` Helpers

- `assert_schematic_has_component()`: Component with properties exists
- `assert_schematic_component_count()`: Exact component count
- `assert_position_near()`: Positions close (within tolerance)
- `assert_position_preserved()`: Position unchanged
- `assert_roundtrip_preserves_components()`: Round-trip consistency
- `assert_net_exists()`: Net name found in schematic
- `assert_component_on_net()`: Component pin on net (future)

### CI/CD Integration

These tests are designed to run in CI/CD:

```yaml
# .github/workflows/test.yml
- name: Run Bidirectional Tests
  run: pytest tests/test_bidirectional_automated/ -v --cov
```

### Development Workflow

1. **Add new feature** to circuit-synth
2. **Run automated tests** to verify no regressions
3. **Add new test** if feature needs coverage
4. **Commit with passing tests**

### Future Enhancements

- [ ] Power symbol tests (test_26)
- [ ] Hierarchical sheet tests
- [ ] Multi-unit component tests
- [ ] Property preservation tests (custom properties)
- [ ] Symbol library tests
- [ ] PCB synchronization tests

### Notes

- **kicad-sch-api reliability**: These tests assume kicad-sch-api correctly reads/writes KiCad files (validated by its 302-test suite)
- **Import function**: Tests use `circuit_synth.kicad.importer.import_kicad_project()` - verify this function exists and works
- **Temp directories**: Each test gets isolated temp directory (pytest `tmp_path` fixture)
- **Manual tests preserved**: Original manual tests remain for visual verification in KiCad

### Questions?

- How do I add a new test? Copy pattern from existing test file
- How do I test a new feature? Add test to appropriate test file
- Tests failing? Check kicad-sch-api version, verify import function exists
- Need to debug? Run single test with `-v -s` flags for verbose output
