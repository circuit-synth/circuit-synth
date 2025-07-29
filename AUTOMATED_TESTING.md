# Automated Testing Guide

This document describes the automated testing infrastructure for the circuit-synth project.

## Overview

The project uses a comprehensive testing strategy with automated Rust and Python testing:

- **🐍 Python Tests**: 165 passing tests for core functionality
- **🦀 Rust Tests**: Unit tests for performance-critical modules  
- **🔗 Integration Tests**: Python-Rust binding validation
- **⚙️ Core Tests**: End-to-end functionality validation
- **🤖 CI/CD**: Automated testing on PR creation

## Quick Start

### Run All Tests
```bash
# Run comprehensive test suite
./scripts/run_all_tests.sh

# Run with verbose output
./scripts/run_all_tests.sh --verbose

# Run only Python tests
./scripts/run_all_tests.sh --python-only

# Run only Rust tests  
./scripts/run_all_tests.sh --rust-only
```

### Run Rust Tests Only
```bash
# Run all Rust module tests
./scripts/test_rust_modules.sh

# Run with detailed output
./scripts/test_rust_modules.sh --verbose

# Stop on first failure
./scripts/test_rust_modules.sh --fail-fast
```

### Traditional Testing
```bash
# Python tests
uv run pytest

# Rust tests (per module)
cd rust_modules/rust_netlist_processor
cargo test --lib --no-default-features
```

## Scripts

### `scripts/run_all_tests.sh`
**Unified test runner** that orchestrates all testing:

- ✅ Python unit tests (`pytest`)
- ✅ Rust unit tests (via `test_rust_modules.sh`)
- ✅ Integration tests (`pytest tests/rust_integration/`)
- ✅ Core functionality test (`examples/example_kicad_project.py`)
- ✅ Comprehensive summary report

**Options:**
- `--python-only`: Run only Python tests
- `--rust-only`: Run only Rust tests
- `--verbose`: Show detailed output
- `--fail-fast`: Stop on first failure

### `scripts/test_rust_modules.sh`
**Automated Rust testing** for all modules:

- 🔍 **Discovers** all Rust modules automatically
- 🧪 **Tests** each module with `cargo test --lib --no-default-features`
- 🐍 **Validates** Python bindings with `maturin develop`
- 📊 **Reports** detailed results in JSON format
- ⚡ **Parallel** testing with proper error handling

**Features:**
- Auto-discovery of Rust modules in `rust_modules/`
- JSON results output (`rust_test_results.json`)
- Python integration testing for PyO3 modules
- Comprehensive error reporting
- CI/CD integration ready

## GitHub Actions

### Automatic PR Testing
When you create a PR, GitHub Actions automatically:

1. **🦀 Runs Rust unit tests** for all modules
2. **🔍 Runs Clippy lints** for code quality
3. **📝 Checks code formatting** (rustfmt)
4. **💬 Comments on PR** with detailed test results
5. **📁 Uploads test artifacts** for debugging

### Workflow Triggers
- ✅ Pull requests to `main` or `develop`
- ✅ Pushes to `main` or `develop`
- ✅ Manual workflow dispatch
- ✅ Changes to Rust code or test scripts

### Test Matrix
The CI runs on:
- **Ubuntu Latest** with Rust stable toolchain
- **Python 3.12** with uv package manager
- **Maturin** for Python-Rust integration
- **System dependencies** (jq, build tools)

## Pre-commit Hooks

Optional pre-commit hooks prevent issues before commit:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

**Hooks include:**
- ✅ Code formatting (black, rustfmt)
- ✅ Linting (flake8, clippy)
- ✅ Import sorting (isort)
- ✅ Basic file checks
- ✅ Python and Rust tests on changed files

## Test Results

### JSON Output Format
Rust tests generate structured results in `rust_test_results.json`:

```json
{
  "timestamp": "2025-01-27T10:30:00Z",
  "modules": {
    "rust_netlist_processor": {
      "status": "passed",
      "tests_passed": 30,
      "tests_failed": 2,
      "error_message": ""
    }
  },
  "summary": {
    "total_modules": 9,
    "tested_modules": 5,
    "passing_modules": 4,
    "failing_modules": 1,
    "skipped_modules": 4
  }
}
```

### PR Comments
GitHub Actions automatically comment on PRs with:
- 📊 **Summary table** of test results
- ❌ **Failed module details** if any
- 📁 **Detailed JSON results** in collapsible section
- ✅ **Success confirmation** when all tests pass

## Troubleshooting

### Common Issues

**Rust linking errors:**
```
dyld: symbol not found '_PyBool_Type'
```
**Solution**: Use `--no-default-features` flag to avoid Python dependencies

**Missing dependencies:**
```
cargo: command not found
```
**Solution**: Install Rust toolchain or use Docker

**Python import failures:**
```
ImportError: No module named 'rust_module'
```
**Solution**: Run `maturin develop` in the module directory

### Debug Commands

```bash
# Check Rust toolchain
cargo --version
rustc --version

# Check Python environment
uv --version
python --version

# Verbose test output
./scripts/test_rust_modules.sh --verbose

# Test specific module
cd rust_modules/rust_netlist_processor
cargo test --lib --no-default-features --verbose
```

## Integration with Development Workflow

### Recommended Workflow

1. **🔧 Make changes** to Rust or Python code
2. **🧪 Run tests locally**:
   ```bash
   ./scripts/run_all_tests.sh
   ```
3. **📝 Commit changes** (pre-commit hooks run automatically)
4. **🚀 Create PR** (GitHub Actions run automatically)
5. **✅ Merge when green** (all tests passing)

### CLAUDE.md Integration

The automated testing is integrated with CLAUDE.md workflows:

- **Core circuit test**: `uv run python examples/example_kicad_project.py`
- **Unit tests**: `uv run pytest tests/unit/test_core_circuit.py -v`
- **Rust tests**: `./scripts/test_rust_modules.sh`
- **Comprehensive**: `./scripts/run_all_tests.sh`

This ensures both manual and automated testing follow the same validation patterns.

## Benefits

✅ **Faster feedback** - Catch issues immediately on PR creation  
✅ **Consistent testing** - Same tests run locally and in CI  
✅ **Comprehensive coverage** - Python, Rust, and integration tests  
✅ **Clear reporting** - Detailed results with actionable information  
✅ **Easy maintenance** - Auto-discovery and JSON output for tooling  
✅ **Developer friendly** - Simple commands and helpful error messages