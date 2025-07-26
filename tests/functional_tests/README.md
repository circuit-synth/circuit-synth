# Functional Tests for Circuit Synth to KiCad Synchronization

This directory contains functional test cases for verifying bidirectional synchronization between Circuit Synth (Python) and KiCad projects.

## Test Structure

Each test case is organized in its own directory with:
- `circuit.py` - Initial Python circuit definition
- `expected/` - Expected KiCad output files (when applicable)
- `test_script.py` - Automated test script (when applicable)
- `MANUAL_STEPS.md` - Manual instructions for KiCad operations
- `README.md` - Documentation of what the test validates

## Test Cases

### 1. `test_01_single_resistor/`
Basic single resistor circuit generation and synchronization.
- Initial generation
- Re-run stability
- Position preservation

### 2. `test_02_add_components_kicad/`
Tests adding components in KiCad and syncing back to Python.
- Net name changes
- Component additions
- Round-trip consistency

### 3. `test_03_change_connections/`
Tests changing connections in KiCad and verifying sync.
- Series to parallel conversion
- Connection modifications
- Net additions/removals

### 4. `test_04_hierarchical_sheets/`
Tests hierarchical sheet handling from both Python and KiCad sides.
- Python to KiCad hierarchy
- KiCad to Python hierarchy
- Inter-sheet connections

### 5. `test_05_component_properties/`
Tests synchronization of component properties and fields.
- Value changes
- Footprint updates
- Custom fields

### 6. `test_06_power_symbols/`
Tests handling of power symbols and global labels.
- Power symbol placement
- Global label connections
- Power net management

### 7. `test_07_multi_unit_components/`
Tests multi-unit component handling.
- Op-amps with multiple units
- Digital ICs with multiple gates
- Unit placement and connections

### 8. `test_08_net_classes/`
Tests net class definitions and constraints.
- Differential pairs
- High-speed signals
- Power net specifications

### 9. `test_09_annotations/`
Tests annotation and reference designator handling.
- Automatic annotation
- Reference preservation
- Annotation conflicts

### 10. `test_10_library_symbols/`
Tests custom library symbol usage.
- Custom symbol definitions
- Library path handling
- Symbol updates

## Running Tests

### Automated Tests
To run all automated tests:
```bash
python run_all_tests.py
```

To run a specific automated test:
```bash
python tests/functional_tests/test_01_single_resistor/test_script.py
```

### Manual Tests
For tests involving KiCad operations:
1. Navigate to the test directory
2. Run the initial Python script
3. Follow the instructions in `MANUAL_STEPS.md`

## Test Development Guidelines

When creating new tests:
1. Create a descriptive directory name
2. Include clear documentation in README.md
3. Provide initial circuit.py for setup
4. Create MANUAL_STEPS.md for KiCad operations
5. Include expected results and verification steps

## Known Limitations

Some tests use simulated results until full bidirectional synchronization is implemented:
- KiCad to Python import (sync_from_kicad)
- Complex hierarchy handling
- Custom field synchronization

## Contributing

To add a new test case:
1. Create a new directory following the naming convention
2. Implement the test following the structure above
3. Update this README with the new test description
4. Ensure all files are properly documented