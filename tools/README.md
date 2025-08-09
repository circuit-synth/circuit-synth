# Circuit-Synth Development Tools

This directory contains all development tools and scripts for circuit-synth. These tools are used for building, testing, analysis, and maintenance but are not part of the installed package.

## 📁 Directory Structure

### `ci-setup/`
**Continuous Integration Setup Tools**
- `setup-ci-symbols.sh` - Cross-platform bash script for KiCad symbol setup
- `setup_ci_symbols.py` - Python alternative for environments without bash
- `CI_SETUP.md` - Complete CI setup documentation

### `build/`
**Build and Compilation Tools**
- `setup_formatting.sh` - Set up code formatting tools

### `testing/`
**Test Automation and Execution**
- `run_regression_tests.py` - Execute regression test suite

### `release/`
**Release and Distribution**
- `release_to_pypi.sh` - Automated PyPI release pipeline

### `analysis/`
**Code Analysis and Quality**
- `dead-code-analysis.py` - Identify and analyze unused code
- `dead-code-analysis.sh` - Shell wrapper for dead code analysis

### `maintenance/`
**Repository Maintenance Utilities**
- `clear_all_caches.sh` - Clear all build and runtime caches
- `update_examples_with_stock.py` - Update examples with current stock info

## 🚀 Quick Reference

### Build Operations
```bash
# Build everything

# Format all code
./tools/build/format_all.sh

# Clean rebuild
```

### Testing
```bash
# Run complete test suite
./tools/testing/run_all_tests.sh


# Run regression tests
python3 tools/testing/run_regression_tests.py
```

### Release
```bash
# Release to PyPI
./tools/release/release_to_pypi.sh 0.5.1
```

### Analysis & Maintenance
```bash
# Analyze dead code
./tools/analysis/dead-code-analysis.sh

# Clear all caches
./tools/maintenance/clear_all_caches.sh
```

### CI Setup
```bash
# Cross-platform KiCad symbol setup for CI
./tools/ci-setup/setup-ci-symbols.sh

# Python alternative
python3 tools/ci-setup/setup_ci_symbols.py
```

## 📋 Directory Purpose

| Directory | Purpose | Installed with Package |
|-----------|---------|----------------------|
| **`tools/`** | Development, build, test, analysis tools | ❌ No |
| **`src/circuit_synth/cli/`** | User-facing CLI utilities | ✅ Yes |
| **`src/circuit_synth/`** | Core library code | ✅ Yes |
| **`examples/`** | Usage examples and demos | ✅ Yes |
| **`docs/`** | API documentation and guides | ✅ Yes |

This organization provides clear separation between development tools (not installed) and user tools (part of the package).