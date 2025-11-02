# Bidirectional Sync Tests

Comprehensive test suite for validating bidirectional synchronization between Python circuit definitions and KiCad schematics.

## Quick Start

**Run all passing tests:**
```bash
pytest tests/bidirectional/component_crud_root/*/test_*.py tests/bidirectional/net_crud_root/*/test_*.py -v
```

**Manual verification checklist:**
See [MANUAL_TEST_CHECKLIST.md](./MANUAL_TEST_CHECKLIST.md) for detailed manual testing instructions.

## Current Status

**Completed & Passing**: 8/45 tests (18%)
- ✅ Tests 10-13: Component CRUD (Root Sheet)
- ✅ Tests 14-17: Net CRUD (Root Sheet)

**In Progress**: Tests 18-25 (Hierarchical CRUD operations)

## Philosophy

**Simple, Automated, Comprehensive**

- **One test = One scenario** - Each test demonstrates one specific CRUD operation
- **Automated verification** - Tests use kicad-sch-api for programmatic validation
- **Position preservation** - Tests verify component positions survive regeneration
- **Self-contained** - Each test directory has circuit + test + README

## Test Coverage Plan (45 Tests Total)

### Component CRUD - Root Sheet (Tests 10-13) ✅
- Test 10: Add component
- Test 11: Update component value
- Test 12: Rename component (update ref)
- Test 13: Delete component

### Net CRUD - Root Sheet (Tests 14-17) ✅
- Test 14: Add net
- Test 15: Update net connection
- Test 16: Rename net
- Test 17: Delete net

### Component CRUD - Hierarchical (Tests 18-21) 🏗️
- Test 18: Add component in subcircuit
- Test 19: Update component value in subcircuit
- Test 20: Rename component in subcircuit
- Test 21: Delete component in subcircuit

### Net CRUD - Hierarchical (Tests 22-25) 🏗️
- Test 22: Add net in subcircuit
- Test 23: Update net in subcircuit
- Test 24: Rename net in subcircuit
- Test 25: Delete net in subcircuit

### Sheet CRUD (Tests 26-29) 📋
- Test 26: Add hierarchical sheet
- Test 27: Update sheet properties
- Test 28: Rename sheet
- Test 29: Delete sheet

### Label CRUD (Tests 30-33) 📋
- Test 30: Add hierarchical label
- Test 31: Update label properties
- Test 32: Rename label
- Test 33: Delete label

### Power Symbol CRUD (Tests 34-37) 📋
- Test 34: Add power symbol
- Test 35: Change power symbol type
- Test 36: Rename power net
- Test 37: Delete power symbol

### Cross-Hierarchy Operations (Tests 38-41) 📋
- Test 38: Connect across sheets
- Test 39: Modify cross-sheet connection
- Test 40: Move component between sheets
- Test 41: Propagate changes up/down hierarchy

### Bulk Operations (Tests 42-45) 📋
- Test 42: Add multiple components
- Test 43: Update multiple components
- Test 44: Delete multiple components
- Test 45: Complex multi-operation workflow

## Test Structure

Each test follows the **one-folder-per-test** pattern:

```
tests/bidirectional/
├── component_crud_root/
│   ├── 10_sync_component_root_create/
│   │   ├── comprehensive_root.py      # Circuit definition
│   │   ├── test_add_component.py      # Automated test
│   │   └── README.md                  # Manual instructions
│   ├── 11_sync_component_root_update_value/
│   ├── 12_sync_component_root_update_ref/
│   └── 13_sync_component_root_delete/
├── net_crud_root/
│   ├── 14_sync_net_root_create/
│   ├── 15_sync_net_root_update/
│   ├── 16_sync_net_root_rename/
│   └── 17_sync_net_root_delete/
├── component_crud_hier/
│   └── 18-21...
├── net_crud_hier/
│   └── 22-25...
└── MANUAL_TEST_CHECKLIST.md           # Manual verification checklist
```

## Running Tests

### Automated Tests (Recommended)

Run all passing tests:
```bash
pytest tests/bidirectional/component_crud_root/*/test_*.py \
       tests/bidirectional/net_crud_root/*/test_*.py -v
```

Run specific test:
```bash
pytest tests/bidirectional/component_crud_root/10_sync_component_root_create/test_add_component.py -v
```

Keep test outputs for inspection:
```bash
pytest tests/bidirectional/component_crud_root/10_sync_component_root_create/test_add_component.py -v --keep-output
```

### Manual Testing

For manual verification in KiCad:

1. Navigate to test directory:
   ```bash
   cd tests/bidirectional/component_crud_root/10_sync_component_root_create
   ```

2. Generate circuit:
   ```bash
   uv run comprehensive_root.py
   ```

3. Open in KiCad:
   ```bash
   open comprehensive_root/comprehensive_root.kicad_pro
   ```

4. Follow README.md instructions to perform the test operation

## Test Verification

Each test verifies:
- ✅ Circuit generates without errors
- ✅ Component positions preserved across regeneration
- ✅ Component values preserved
- ✅ Net connections preserved
- ✅ Power symbols preserved
- ✅ Modified elements updated correctly

Tests use **kicad-sch-api 0.4.5+** for programmatic KiCad schematic verification.

## Key Testing Patterns

### Position Preservation Test

```python
# STEP 1: Generate initial circuit
result = subprocess.run(["uv", "run", "comprehensive_root.py"])
sch = Schematic.load("comprehensive_root/comprehensive_root.kicad_sch")

# Store positions
r1_pos_before = r1.position

# STEP 2: Modify circuit (e.g., change R1 value)
modify_circuit_code()

# STEP 3: Regenerate
result = subprocess.run(["uv", "run", "comprehensive_root.py"])
sch_after = Schematic.load("comprehensive_root/comprehensive_root.kicad_sch")

# STEP 4: Verify position preserved
assert r1_after.position.x == r1_pos_before.x
assert r1_after.position.y == r1_pos_before.y
```

## Legacy Tests

Old tests are archived in `_archive_legacy_tests/` for reference but are not actively maintained.

## Contributing

When adding new tests:
1. Follow the one-folder-per-test pattern
2. Include comprehensive_root.py (circuit), test_*.py (automated test), README.md (manual instructions)
3. Use kicad-sch-api for verification
4. Test both automated pytest execution and manual KiCad verification
5. Update MANUAL_TEST_CHECKLIST.md

## Documentation

- **MANUAL_TEST_CHECKLIST.md** - Checkbox list for manual verification of all 45 tests
- **README.md** (this file) - Overview and quick reference
- **_archive_docs/** - Historical status documents (archived)
