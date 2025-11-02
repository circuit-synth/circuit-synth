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
├── bidirectional/          # Bidirectional sync tests (71 tests, Tests 10-80)
│   ├── component_crud_root/      # Root sheet component operations
│   ├── component_crud_hier/      # Hierarchical component operations
│   ├── net_crud_root/            # Root sheet net operations
│   ├── net_crud_hier/            # Hierarchical net operations
│   ├── sheet_crud/               # Sheet operations
│   ├── label_crud/               # Label operations
│   ├── power_symbol_crud/        # Power symbol operations
│   ├── cross_hierarchy/          # Cross-hierarchy operations
│   ├── bulk_operations/          # Bulk CRUD operations
│   ├── edge_cases/               # Edge case handling
│   ├── rotation_orientation/     # Rotation & orientation
│   ├── pin_level/                # Pin-level operations
│   ├── sheet_pins/               # Sheet pin operations
│   ├── special_nets/             # Special net types
│   ├── annotation/               # Annotation & references
│   ├── schematic_props/          # Schematic properties
│   ├── performance/              # Performance & scale tests
│   ├── regression/               # Regression tests
│   ├── workflows/                # Real-world workflows
│   └── MANUAL_TEST_CHECKLIST.md  # Manual verification checklist
│
├── conversion/             # Round-trip conversion tests (6 tests)
│   ├── 01_roundtrip_basic/            # Basic round-trip
│   ├── 02_roundtrip_hierarchical/     # Hierarchical circuits
│   ├── 03_roundtrip_complex_components/ # Complex components
│   ├── 04_roundtrip_power_nets/       # Power nets
│   ├── 05_roundtrip_net_attributes/   # Net attributes
│   └── 06_roundtrip_metadata/         # Metadata preservation
│
├── netlist/                # Netlist generation tests (4 tests)
│   ├── 01_basic_netlist/         # Basic netlist
│   ├── 02_hierarchical_netlist/  # Hierarchical netlist
│   ├── 03_power_nets_netlist/    # Power nets in netlist
│   └── 04_complex_components_netlist/ # Complex components
│
├── performance/            # Performance benchmark tests (7 tests)
│   ├── 01_small_circuit/         # 20 components
│   ├── 02_medium_circuit/        # 200 components
│   ├── 03_large_circuit/         # 1000 components
│   ├── 04_deep_hierarchy/        # 10 levels deep
│   ├── 05_wide_hierarchy/        # 30 subcircuits
│   ├── 06_complex_routing/       # High net density
│   └── 07_memory_usage/          # Memory profiling
│
├── regression/             # Regression tests for specific issues (5 tests)
│   ├── issue_238_text_parameters/     # Text class parameters
│   ├── issue_240_component_positions/ # Position preservation
│   ├── issue_250_net_names/           # Net name preservation
│   ├── issue_260_power_symbols/       # Power symbol generation
│   └── issue_270_footprint_selection/ # Footprint selection
│
├── manufacturing/          # Manufacturing output tests (4 tests)
│   ├── 01_bom_generation/        # BOM generation
│   ├── 02_pnp_generation/        # Pick-and-place data
│   ├── 03_gerber_validation/     # PCB file validation
│   └── 04_drill_files/           # Netlist for manufacturing
│
├── pcb/                    # PCB validation tests (4 tests)
│   ├── 01_pcb_generation/        # PCB file generation
│   ├── 02_footprint_placement/   # Footprint placement
│   ├── 03_pcb_nets/              # PCB net definitions
│   └── 04_pcb_layers/            # PCB layer structure
│
├── fixtures/               # Centralized test data
│   ├── circuits/           # Python circuit definitions
│   ├── kicad_projects/     # KiCad project files
│   ├── components/         # Component libraries
│   └── README.md           # Fixture documentation
│
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

### Bidirectional Sync Tests (`tests/bidirectional/`)

**Purpose:** Test Python ↔ KiCad bidirectional synchronization with position preservation.

**Characteristics:**
- 71 comprehensive tests (Tests 10-80)
- One-folder-per-test pattern
- Automated + manual verification
- Position preservation testing (THE KILLER FEATURE)
- Organized by operation category

**Categories:**
- Component & Net CRUD (root + hierarchical)
- Sheet, Label, Power Symbol operations
- Cross-hierarchy & bulk operations
- Edge cases, rotation, pin-level ops
- Performance, regression, real-world workflows

**Run:** `pytest tests/bidirectional/*/*/test_*.py -v`
**Manual Checklist:** `tests/bidirectional/MANUAL_TEST_CHECKLIST.md`

### Conversion Tests (`tests/conversion/`)

**Purpose:** Validate Python → KiCad → Python round-trip data integrity.

**Tests (6 total):**
- Basic, hierarchical, complex components
- Power nets, net attributes, metadata

**Run:** `pytest tests/conversion/*/test_*.py -v`

### Netlist Tests (`tests/netlist/`)

**Purpose:** Validate KiCad netlist generation correctness.

**Tests (4 total):**
- Basic, hierarchical, power nets, complex components

**Run:** `pytest tests/netlist/*/test_*.py -v`

### Performance Tests (`tests/performance/`)

**Purpose:** Benchmark circuit-synth scalability and performance.

**Tests (7 total):**
- Small (20), Medium (200), Large (1000) circuits
- Deep (10 levels), Wide (30 subcircuits) hierarchies
- Complex routing, memory profiling

**Run:** `pytest tests/performance/*/test_*.py -v`

### Regression Tests (`tests/regression/`)

**Purpose:** Prevent re-breaking of specific fixed issues.

**Tests (5 total):**
- Issues #238, #240, #250, #260, #270

**Run:** `pytest tests/regression/*/test_*.py -v`

### Manufacturing Tests (`tests/manufacturing/`)

**Purpose:** Validate production-ready manufacturing outputs.

**Tests (4 total):**
- BOM, Pick-and-Place, Gerber/PCB, Netlist

**Run:** `pytest tests/manufacturing/*/test_*.py -v`

### PCB Tests (`tests/pcb/`)

**Purpose:** Validate KiCad PCB file generation and structure.

**Tests (4 total):**
- File generation, footprints, nets, layers

**Run:** `pytest tests/pcb/*/test_*.py -v`

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
