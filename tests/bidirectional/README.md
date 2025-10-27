# Bidirectional Sync Tests

Manual test suite for validating bidirectional synchronization between Python circuit definitions and KiCad schematics.

## Philosophy

**Simple, Manual, Comprehensive**

- **One test = One scenario** - Each test demonstrates one specific behavior
- **Manual verification** - Run the circuit, inspect output, verify functionality
- **Self-contained** - Each test directory has everything needed to run
- **Comprehensive coverage** - Tests cover all critical workflows

## Test Coverage

This test suite validates:
- **Python → KiCad**: Generate KiCad schematics from Python code
- **KiCad → Python**: Import KiCad schematics to Python code
- **Round-Trip**: Maintain consistency through multiple sync cycles
- **Position Preservation**: Manual component positions survive sync
- **Property Preservation**: Component values, footprints, references preserved

## Test Structure

Each test directory contains:
- **Starting file(s)**: Python circuit or KiCad project to run
- **README.md**: Instructions on how to test and what to verify

```
tests/bidirectional/
├── 01_test_blank/              # Empty circuit generation
│   ├── blank.py
│   └── README.md
├── 02_test_generate/           # Python → KiCad generation
│   ├── single_resistor.py
│   └── README.md
├── 03_test_import/             # KiCad → Python import
│   ├── kicad_ref/
│   └── README.md
├── 04_test_properties/         # Property preservation
├── 05_test_roundtrip/          # Full cycle test
├── 06_test_add_component/      # Adding components
├── 07_test_delete_component/   # Removing components
├── 08_test_modify_value/       # Changing values
├── 09_test_manual_position_preservation/  # Position handling
├── 10_test_add_to_existing_net/  # Net operations
├── 11_test_power_rails/        # Power/ground nets
├── 12_test_set_position/       # Explicit positioning
├── 13_test_component_rename/   # Reference changes
├── 14_test_incremental_growth/ # Multiple iterations
├── 15_test_move_component/     # Position changes
├── 17_test_create_net/         # Creating connections
└── 22_test_delete_net/         # Removing connections
```

## Running Tests

### General Pattern

1. Navigate to test directory:
   ```bash
   cd tests/bidirectional/01_test_blank
   ```

2. Read the README.md for specific instructions

3. Run the starting file:
   ```bash
   uv run blank.py
   # or
   uv run kicad-to-python kicad_ref/project.kicad_pro -o output.py
   ```

4. Verify output manually (open in KiCad, inspect files, etc.)

### Example: Test 01 (Blank Circuit)

```bash
cd tests/bidirectional/01_test_blank
uv run blank.py
open blank/blank.kicad_pro  # Verify blank schematic opens
```

### Example: Test 02 (Generate from Python)

```bash
cd tests/bidirectional/02_test_generate
uv run single_resistor.py
open single_resistor/single_resistor.kicad_pro  # Verify R1 resistor appears
```

### Example: Test 03 (Import from KiCad)

```bash
cd tests/bidirectional/03_test_import
uv run kicad-to-python kicad_ref/02_kicad_ref.kicad_pro -o imported.py
cat imported.py  # Verify Python code generated with R1 component
```

## Manual Verification Checklist

When testing, verify:
- ✅ Files generate without errors
- ✅ KiCad projects open in KiCad
- ✅ Components appear with correct references (R1, C1, etc.)
- ✅ Component values are correct (10k, 100nF, etc.)
- ✅ Connections/nets are present (if applicable)
- ✅ Positions are preserved (if applicable)
- ✅ Round-trip maintains all properties

## Test Status

All tests are functional and ready for manual verification. See individual test README.md files for specific verification steps.
