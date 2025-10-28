# Circuit-Synth Test Suite

The circuit-synth test suite is organized for clarity, maintainability, and efficient testing.

## Test Organization

```
tests/
├── unit/                    # Unit tests (fast, pure Python)
│   ├── test_*.py           # Individual test modules
│   ├── io/                 # I/O related unit tests
│   ├── jlc_integration/    # JLC lookup unit tests
│   ├── kicad/              # KiCad API unit tests
│   └── tools/              # Tool functionality unit tests
│
├── integration/            # Integration tests (file I/O, no external tools)
│   ├── test_*.py           # Workflow and roundtrip tests
│   └── helpers/            # Shared integration test helpers
│
├── e2e/                    # End-to-end tests (external tools allowed)
│   └── test_*.py           # Tests requiring kicad-cli, KiCad plugins, etc.
│
├── fixtures/               # Centralized test data
│   ├── circuits/           # Python circuit definitions
│   ├── kicad_projects/     # KiCad project files
│   ├── components/         # Component libraries
│   └── README.md           # Fixture documentation
│
├── bidirectional/          # Bidirectional sync test scenarios (26 workflows)
├── test_data/              # Legacy test data (being consolidated to fixtures/)
├── kicad/                  # KiCad-related utilities
├── kicad_to_python/        # KiCad→Python conversion workflows
└── conftest.py             # Shared pytest configuration and fixtures
```

## Test Categories

### Unit Tests (`tests/unit/`)

**Purpose:** Test individual components, functions, and classes in isolation.

**Characteristics:**
- Very fast execution (<100ms per test)
- Pure Python, no file I/O
- No external tools (no kicad-cli)
- Highly focused scope
- Run on every code change

**Examples:**
- Component class initialization
- Net property calculation
- Power net registry logic
- KiCad string escaping
- BOM generation algorithms

**Run:** `pytest tests/unit/ -v`

### Integration Tests (`tests/integration/`)

**Purpose:** Test component interactions, workflows, and end-to-end processes.

**Characteristics:**
- Moderate execution time
- File I/O allowed (create, read, modify KiCad files)
- No external tools (no kicad-cli)
- Test complete workflows
- Test roundtrip preservation

**Examples:**
- Roundtrip preservation (Python→KiCad→Python)
- KiCad synchronization workflows
- JSON export and import
- Hierarchical schematic handling
- Bidirectional component operations

**Run:** `pytest tests/integration/ -v`

### End-to-End Tests (`tests/e2e/`)

**Purpose:** Test complete system integration with external tools.

**Characteristics:**
- Can be very slow
- File I/O allowed
- External tools allowed (kicad-cli, KiCad plugins)
- Full system integration tests
- Environment-dependent (skip if tools missing)

**Examples:**
- Gerber export with kicad-cli
- PDF export with kicad-cli
- KiCad project generation and validation
- Manufacturing workflow integration

**Run:** `pytest tests/e2e/ -v`

## Running Tests

### Quick Feedback (Unit Tests Only)
```bash
pytest tests/unit/ -v
```

### All Tests
```bash
pytest tests/ -v
```

### By Category
```bash
pytest -m unit      # Unit tests
pytest -m integration  # Integration tests
pytest -m e2e       # End-to-end tests
```

### With Coverage
```bash
pytest tests/unit/ --cov=circuit_synth --cov-report=html
```

### Watch Mode (Requires pytest-watch)
```bash
ptw tests/unit/
```

## Key Fixtures

The `tests/conftest.py` provides shared fixtures:

### `mock_active_circuit`
Automatically creates a temporary circuit for each test, preventing "No active circuit found" errors.

```python
def test_my_component(mock_active_circuit):
    # Circuit is automatically available
    comp = Resistor("R1", value="10k")
    assert comp.reference == "R1"
```

### `configure_kicad_paths`
Session-scoped fixture that:
- Clears the KiCad symbol cache
- Prepares the environment for testing
- Cleans up after tests complete

## Test Markers

```python
import pytest

@pytest.mark.unit
def test_fast_operation():
    """Fast, pure Python test"""
    pass

@pytest.mark.integration
def test_workflow():
    """Tests file I/O and component interaction"""
    pass

@pytest.mark.e2e
def test_with_external_tools():
    """Tests requiring external tools like kicad-cli"""
    pass

@pytest.mark.slow
def test_long_running():
    """Marks any test as slow (can be used with any category)"""
    pass

@pytest.mark.asyncio
def test_async_operation():
    """Tests async/await code"""
    pass
```

## Contributing Tests

### Where Should My Test Go?

1. **Is it pure Python?** → `tests/unit/`
2. **Does it create/modify files?** → `tests/integration/`
3. **Does it need external tools?** → `tests/e2e/`

### Test File Naming

- Unit tests: `test_<module>.py` in `tests/unit/`
- Integration tests: `test_<workflow>.py` in `tests/integration/`
- E2E tests: `test_<feature>_e2e.py` in `tests/e2e/`

### Example Test

```python
import pytest
from circuit_synth.core.component import Resistor

@pytest.mark.unit
def test_resistor_creation(mock_active_circuit):
    """Test creating a resistor with proper values."""
    resistor = Resistor("R1", value="10k")

    assert resistor.reference == "R1"
    assert resistor.value == "10k"
```

## Current Test Status

**Overall:** ~640 passing, ~90 failing, ~55 skipped

**Unit Tests:** Most passing, focusing on core functionality
**Integration Tests:** Testing workflows and roundtrip preservation
**E2E Tests:** Tests for external tool integration

See `TEST_REORGANIZATION_PLAN.md` for complete reorganization strategy and phase breakdown.

## Test Reorganization Phases

The test suite is being reorganized in phases:

1. ✅ **Phase 1:** Create new structure, update pytest config
2. **Phase 2:** Audit and categorize all test files
3. **Phase 3:** Consolidate fixtures from scattered locations
4. **Phase 4:** Move tests to correct directories
5. **Phase 5:** Update configuration and documentation
6. **Phase 6:** Fix remaining test failures
7. **Phase 7:** Verification and validation

## Troubleshooting

### ImportError: No module named 'circuit_synth'
Ensure circuit-synth is installed in development mode:
```bash
pip install -e .
```

### Async test not running
Async tests require `pytest-asyncio`. Install with:
```bash
pip install pytest-asyncio
```

### KiCad symbol cache errors
The `configure_kicad_paths` fixture clears the cache. If you get cache errors, try clearing it manually:
```bash
rm -rf ~/.cache/circuit-synth/kicad-symbols/
```

### Some tests skipped with "No kicad-cli found"
E2E tests skip if kicad-cli is not available. Install KiCad to run them.

## Resources

- [TEST_REORGANIZATION_PLAN.md](../TEST_REORGANIZATION_PLAN.md) - Complete reorganization strategy
- [fixtures/README.md](fixtures/README.md) - Test fixture documentation
- [pytest documentation](https://docs.pytest.org/) - General pytest reference
