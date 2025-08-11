# /dev-run-tests

Run comprehensive test suite for circuit-synth development and validation.

## Usage
```
/dev-run-tests [options]
```

## Description
Executes the complete circuit-synth testing pipeline including unit tests, integration tests, and regression validation. This command is essential for ensuring code quality and preventing regressions during development.

## Test Categories

### Unit Tests
- Core circuit functionality (`tests/unit/test_core_circuit.py`)
- Component and net management 
- JSON processing and validation
- KiCad symbol parsing and caching
- Manufacturing integration components

### Integration Tests
- KiCad CLI integration and project generation
- JLCPCB and DigiKey API integration 
- Complete workflow validation (Python → JSON → KiCad)
- External dependency testing

### Regression Tests
- Reference circuit validation
- Netlist export/import round-trip testing
- Hierarchical circuit structure validation
- Cross-platform compatibility testing

## Command Options

### Basic Execution
```bash
# Run all tests with coverage
uv run pytest --cov=circuit_synth

# Run specific test categories
uv run pytest tests/unit/
uv run pytest tests/integration/

# Run with verbose output
uv run pytest -v
```

### Advanced Testing
```bash
# Comprehensive regression testing
./tools/testing/run_full_regression_tests.py

# Automated test suite with multiple configurations
./tools/testing/run_all_tests.sh --verbose

# Performance testing and profiling
uv run pytest --benchmark-only
```

### CI/CD Integration
```bash
# Pre-commit testing (fast)
uv run pytest tests/unit/ --maxfail=1

# Full validation before release
./tools/testing/run_full_regression_tests.py --skip-install --quick
```

## Prerequisites
- uv package manager installed
- KiCad CLI available (for integration tests)
- Internet connection (for manufacturing API tests)
- Git repository in clean state (for some regression tests)

## Expected Output
The command provides detailed test results including:
- Test coverage percentage and missing coverage areas
- Performance benchmarks for critical algorithms
- Integration test status for external dependencies
- Regression test validation results

## Usage in Development Workflow
1. **Before implementing**: Run tests to establish baseline
2. **During development**: Run relevant test subsets frequently
3. **Before committing**: Run full test suite to prevent regressions
4. **Before releasing**: Execute comprehensive regression validation

This command is essential for maintaining code quality and ensuring reliable releases.