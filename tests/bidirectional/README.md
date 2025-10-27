# Bidirectional Sync Tests

Comprehensive test suite for validating bidirectional synchronization between Python circuit definitions and KiCad schematics.

## Philosophy

**Granular, Simple, Comprehensive**

- **One test = One thing** - Each test file tests exactly one behavior
- **Easy to understand** - Test name tells you what it tests
- **Shared utilities** - Common code extracted to `test_utils.py`
- **Reusable fixtures** - Standard circuits in `fixtures/`
- **Comprehensive coverage** - Many small tests cover all cases

## Overview

This test suite validates the complete workflow:
- **Python → KiCad**: Generate KiCad schematics from Python code
- **KiCad → Python**: Import KiCad schematics to Python code
- **Round-Trip**: Maintain consistency through multiple sync cycles
- **Preservation**: User edits survive sync operations (CRITICAL)
- **Idempotency**: Deterministic, stable behavior (CRITICAL)

## Structure

```
tests/bidirectional_new/
├── test_utils.py              # Shared utilities for all tests
├── fixtures/                  # Reusable circuit definitions
│   ├── single_resistor.py     # Simple 1-component circuit
│   └── positioned_resistor.py # Circuit with explicit positions
│
├── 01_blank_projects/         # Empty project tests
├── 02_single_component/       # Single component tests (GRANULAR ✨)
│   ├── test_01_generate_single_component.py
│   ├── test_02_import_single_component.py
│   ├── test_03_properties_preserved.py
│   └── test_04_simple_roundtrip.py
├── 03_position_preservation/  # Position handling tests
├── 04_multiple_components/    # Multi-component tests
├── 05_nets_connectivity/      # Connection/net tests
├── 06_round_trip/            # Full cycle tests
├── 07_user_content_preservation/  # Comment/doc preservation
└── 08_idempotency/           # Stability tests
```

## Test Organization

Tests are organized by complexity and functionality:

| # | Directory | Focus | Structure | Status |
|---|-----------|-------|-----------|--------|
| 01 | `01_blank_projects/` | Empty circuits (foundation) | Monolithic | ✅ Passing |
| 02 | `02_single_component/` | Single component operations | **GRANULAR ✨** | 🔄 Refactored |
| 03 | `03_position_preservation/` | Component positions survive sync | Monolithic | ✅ Passing |
| 04 | `04_multiple_components/` | Multiple components + connections | Monolithic | ✅ Passing |
| 05 | `05_nets_connectivity/` | Named nets, complex topologies | Monolithic | 🚧 Needs validation |
| 06 | `06_round_trip/` | Full cycle validation | Monolithic | 🚧 Needs validation |
| 07 | `07_user_content_preservation/` | Comments, annotations | Monolithic | 🚧 Needs validation |
| 08 | `08_idempotency/` | Deterministic behavior | Monolithic | 🚧 Needs validation |

## Running Tests

### Run all tests in a directory:
```bash
pytest tests/bidirectional_new/02_single_component/ -v
```

### Run a specific test:
```bash
pytest tests/bidirectional_new/02_single_component/test_01_generate_single_component.py -v
```

### Run with output (see print statements):
```bash
pytest tests/bidirectional_new/02_single_component/test_01_generate_single_component.py -v -s
```

### Run as standalone Python script:
```bash
python tests/bidirectional_new/02_single_component/test_01_generate_single_component.py
```

### Run validated tests (01-04):
```bash
uv run pytest 01_blank_projects/ 02_single_component/ 03_position_preservation/ 04_multiple_components/ -v
```

## Robust Validation Infrastructure

### Round-Trip Validator (`round_trip_validator.py`)

Production-ready validation module with three-phase validation:

1. **CircuitJSONComparator** - Validates electrical correctness
   - Order-independent component/net comparison
   - Floating-point tolerance for positions (0.01mm)
   - Metadata filtering (UUIDs, timestamps)

2. **CommentPreservationValidator** - Validates documentation preservation (CRITICAL)
   - Tokenize-based comment extraction
   - Order-independent comparison
   - Detects context loss

3. **PythonASTComparator** - Code quality validation (optional)
   - Function and import verification
   - Structure validation

### Documentation

- **`ROUND_TRIP_VALIDATION_STRATEGY.md`** - Complete validation strategy with production-ready functions
- **`COMMENT_PRESERVATION_ANALYSIS.md`** - Deep technical analysis of comment preservation with solution roadmap

## Known Issues

**Comment Preservation**: Currently comments are not preserved through KiCad→Python import. This is a known issue documented in `COMMENT_PRESERVATION_ANALYSIS.md` with:
- Root cause analysis
- 8 critical weaknesses identified
- Recommended solution (JSON metadata + structured annotations)
- 3-4 week implementation timeline

The robust validator correctly detects this issue, as demonstrated in test 01.

## Test Utilities (`test_utils.py`)

Common functions used across all tests:

### Running Circuits
- `run_python_circuit(py_file)` - Execute Python circuit with uv
- `import_kicad_to_python(kicad_pro, output_py)` - Run kicad-to-python

### File Management
- `clean_output_dir(dir)` - Clean and recreate directory
- `copy_to_output(source, dest)` - Copy files to test output

### Assertions
- `assert_kicad_project_exists(dir, name)` - Verify KiCad project
- `assert_component_in_schematic(sch, ref)` - Find component in .kicad_sch
- `assert_component_in_python(py, ref)` - Find component in Python
- `assert_component_properties(py, ref, value, footprint)` - Verify properties

### Helpers
- `get_test_output_dir(test_file, subdir)` - Standardized output paths
- `print_test_header(name)` - Formatted test headers
- `print_test_footer(success)` - Formatted test footers

## Fixtures (`fixtures/`)

Reusable circuit definitions:

- **`single_resistor.py`** - One 10kΩ resistor (R1)
  - Used for: Basic generation, import, property tests

- **`positioned_resistor.py`** - Two positioned resistors (R1, R2)
  - Used for: Position preservation tests

## 02_single_component/ - Granular Test Example

The `02_single_component/` directory demonstrates the **granular test pattern**:

### `test_01_generate_single_component.py`
**Tests ONLY:** Python → KiCad generation

```python
# Steps:
1. Copy fixture to output
2. Run Python circuit
3. Assert KiCad files exist
4. Assert R1 in schematic

# Does NOT test: Import, properties, round-trip
```

### `test_02_import_single_component.py`
**Tests ONLY:** KiCad → Python import

```python
# Steps:
1. Use reference KiCad project
2. Import to Python
3. Assert Python file exists
4. Assert R1 in Python

# Does NOT test: Generation, properties, round-trip
```

### `test_03_properties_preserved.py`
**Tests ONLY:** Property preservation

```python
# Steps:
1. Generate KiCad from fixture
2. Import back to Python
3. Assert ref="R1", value="10k", footprint="0603"

# Does NOT test: Position, modifications, connections
```

### `test_04_simple_roundtrip.py`
**Tests ONLY:** Full cycle works

```python
# Steps:
1. Generate KiCad from Python
2. Import back to Python
3. Generate KiCad again
4. Assert R1 in both KiCad projects

# Does NOT test: Detailed comparison, modifications
```

## Writing New Tests

### 1. Use test_utils for common operations

```python
from test_utils import (
    clean_output_dir,
    run_python_circuit,
    assert_component_in_schematic,
    print_test_header,
)

def test_my_feature():
    print_test_header("My Feature Test")

    # Use utilities...
    output_dir = get_test_output_dir(__file__, "my_feature")
    clean_output_dir(output_dir)

    # ... test logic ...
```

### 2. Use fixtures for standard circuits

```python
# Instead of defining circuit inline:
fixture = Path(__file__).parent.parent / "fixtures" / "single_resistor.py"
circuit_file = copy_to_output(fixture, output_dir)
```

### 3. Test ONE thing per file

**Good:**
- `test_add_component_python.py` - Add component in Python → appears in KiCad
- `test_remove_component_python.py` - Remove component in Python → gone from KiCad

**Bad:**
- `test_component_operations.py` - Tests add, remove, modify all in one test

### 4. Name tests clearly

Pattern: `test_<action>_<what>_<where>.py`

Examples:
- `test_generate_single_component.py`
- `test_import_positioned_resistor.py`
- `test_preserve_position_roundtrip.py`

## Test Organization Principles

1. **Granularity** - Each test is small and focused
2. **Independence** - Tests don't depend on each other
3. **Clarity** - Test name explains what it tests
4. **Reusability** - Shared code in utilities and fixtures
5. **Comprehensiveness** - Many small tests = full coverage

## Migration from Old Tests

Old monolithic tests (like `02_test.py`) are being replaced with granular tests.

**Old approach:**
```python
def test_03_round_trip():
    # 100+ lines doing generation, import, validation, modification...
```

**New approach:**
```python
# test_01_generate.py (30 lines)
# test_02_import.py (30 lines)
# test_03_properties.py (40 lines)
# test_04_roundtrip.py (50 lines)
```

Benefits:
- ✅ Easier to understand each test
- ✅ Faster to identify failures
- ✅ Simpler to add new tests
- ✅ Shared code eliminates duplication
- ✅ Tests run independently

## Test Details

Each test directory contains:
- `README.md` - Detailed test documentation
- `XX_test.py` - Test implementation (OLD monolithic style)
- `test_*.py` - Individual test files (NEW granular style)
- `XX_python_ref.py` - Reference Python circuit
- `XX_kicad_ref/` - Reference KiCad project (where applicable)

See individual test READMEs for detailed information about what each test validates.
