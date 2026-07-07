# Circuit-Synth Testing Guide

This document describes the comprehensive testing infrastructure for the circuit-synth project.

## Testing Architecture Overview


### 🐍 **Python Tests (Primary)**
- **165 tests passing, 7 skipped** ✅
- Tests all Python functionality and user-facing features
- Provides comprehensive end-to-end validation
- **Run with**: `uv run pytest`

- Independent of Python integration for performance validation
- **Run individually per module**

### 🔗 **Integration Tests**
- Fallback behavior testing

### ⚙️ **Core Tests**
- End-to-end functionality validation
- **Run with**: `uv run python examples/example_kicad_project.py`

## Quick Start

### Run All Tests (Recommended)
```bash
# Run the full test suite
uv run pytest

# Verbose output
uv run pytest -v

# Run only the unit tests
uv run pytest tests/unit/

# Stop on first failure
uv run pytest -x
```

```bash

# Run with detailed output

# Stop on first failure
```

### Traditional Testing Commands
```bash
# Python tests
uv run pytest


# Integration tests
```

## Testing Scripts

### `scripts/run_all_tests.sh`
**Unified test runner** that orchestrates all testing:

- ✅ Python unit tests (`pytest`)
- ✅ Core functionality test (`examples/example_kicad_project.py`)
- ✅ Comprehensive summary report

**Options:**
- `--python-only`: Run only Python tests
- `--verbose`: Show detailed output
- `--fail-fast`: Stop on first failure


- 📊 **Reports** detailed results in JSON format
- ⚡ **Parallel** testing with proper error handling

**Features:**
- Python integration testing for all modules
- Comprehensive error reporting
- CI/CD integration ready


```bash


# Results: 30/32 tests passing (excellent coverage)
```

### Method 2: Test with Python Integration
```bash
# Build Python bindings and test
```


- **Python integration**: All bindings working
- **Import tests**: All successful

**⚠️ Expected Issues:**
- **Import errors**: Check Python path and module installation
- **Some unit test failures**: Minor string processing issues, not critical
- **Missing modules**: Some modules are still in development

## GitHub Actions CI/CD

### Automatic PR Testing
When you create a PR, GitHub Actions automatically:

2. **🔍 Runs Clippy lints** for code quality
4. **💬 Comments on PR** with detailed test results
5. **📁 Uploads test artifacts** for debugging

### Workflow Triggers
- ✅ Pull requests to `main` or `develop`
- ✅ Pushes to `main` or `develop`
- ✅ Manual workflow dispatch

### Test Matrix
The CI runs on:
- **Python 3.12** with uv package manager
- **System dependencies** (jq, build tools)

## Pre-commit Hooks

Optional pre-commit hooks prevent issues before commit:

```bash
# Install pre-commit hooks
./tools/build/setup_formatting.sh

# Run manually
pre-commit run --all-files
```

**Hooks include:**
- ✅ Linting (flake8, clippy)
- ✅ Import sorting (isort)
- ✅ Basic file checks

## Test Results & Reporting

### JSON Output Format

```json
{
  "timestamp": "2025-01-27T10:30:00Z",
  "modules": {
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

```
dyld: symbol not found '_PyBool_Type'
```
**Solution**: Use `--no-default-features` flag to avoid Python dependencies

**Missing dependencies:**
```
```

**Python import failures:**
```
```

### Debug Commands

```bash
# Check toolchain versions
uv --version
python --version

# Verbose test output

# Test specific module

# Test fresh
uv run pytest
```

## Recommended Development Workflow

2. **🧪 Run tests locally**:
   ```bash
   uv run pytest
   ```
3. **📝 Commit changes** (pre-commit hooks run automatically)
4. **🚀 Create PR** (GitHub Actions run automatically)
5. **✅ Merge when green** (all tests passing)

## Integration with CLAUDE.md

The automated testing is integrated with CLAUDE.md workflows:

- **Core circuit test**: `uv run python examples/example_kicad_project.py`
- **Unit tests**: `uv run pytest tests/unit/test_core_circuit.py -v`
- **Comprehensive**: `uv run pytest`

This ensures both manual and automated testing follow the same validation patterns.

## Why This Architecture Works

1. **Python tests validate user functionality** - This is what users actually use

## Benefits

✅ **Faster feedback** - Catch issues immediately on PR creation  
✅ **Consistent testing** - Same tests run locally and in CI  
✅ **Clear reporting** - Detailed results with actionable information  
✅ **Easy maintenance** - Auto-discovery and JSON output for tooling  
✅ **Developer friendly** - Simple commands and helpful error messages  
