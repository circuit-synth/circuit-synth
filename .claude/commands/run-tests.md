---
description: Orchestrates existing test tools for comprehensive testing
---

# Comprehensive Test Runner


## Usage
```bash
/dev-run-tests [options]
```

## Options
- `--suite=standard` - Test suite: `quick`, `standard`, `full`, `regression` (default: standard)
- `--skip-install` - Skip dependency reinstallation (faster, for development)
- `--keep-outputs` - Don't delete generated test files
- `--verbose` - Show detailed output
- `--format=true` - Auto-format code before testing (default: true)
- `--fail-fast=false` - Stop on first failure (default: false)

## Test Suites

### 🚀 Quick Suite (~30 seconds)
Fast development testing:
```bash
./tools/testing/run_all_tests.sh --python-only --fail-fast
```

### 📋 Standard Suite - Default (~2 minutes)
Comprehensive testing without environment rebuild:
```bash
# Auto-format if requested
uv run black src/ tests/ examples/ --quiet
uv run isort src/ tests/ examples/ --quiet

# Run all tests
./tools/testing/run_all_tests.sh --verbose
```

### 🔬 Full Suite (~5 minutes)
```bash
# Run comprehensive tests
./tools/testing/run_all_tests.sh --verbose


# Test all examples
for example in examples/*.py; do
    uv run python "$example"
done
```

### 🏗️ Regression Suite (~10 minutes)
**CRITICAL for releases** - complete environment reconstruction:
```bash
./tools/testing/run_full_regression_tests.py --verbose
```

## What Each Tool Does

### 1. `run_all_tests.sh`
Main test orchestrator:
- 🐍 **Python Tests** - Unit tests via pytest
- ⚙️ **Core Tests** - End-to-end functionality

### 2. `run_full_regression_tests.py` 
**MANDATORY for releases**:
- 📦 **Reinstalls all dependencies** from scratch
- 🧪 **Runs comprehensive test suite**
- ✅ **Validates generated outputs**

- 🔨 **Compilation checks** - Ensures all modules build
- 📊 **Python modules** - Validates module imports and functionality

## Implementation

The command orchestrates existing test tools rather than duplicating functionality:

```bash
#!/bin/bash

# Parse arguments
SUITE="standard"
SKIP_INSTALL=false
KEEP_OUTPUTS=false
VERBOSE=false
FORMAT=true
FAIL_FAST=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --suite=*)
            SUITE="${1#*=}"
            shift
            ;;
        --skip-install)
            SKIP_INSTALL=true
            shift
            ;;
        --keep-outputs)
            KEEP_OUTPUTS=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --format=*)
            FORMAT="${1#*=}"
            shift
            ;;
        --fail-fast)
            FAIL_FAST=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Build test command arguments
TEST_ARGS=""
[[ "$VERBOSE" == "true" ]] && TEST_ARGS="$TEST_ARGS --verbose"
[[ "$FAIL_FAST" == "true" ]] && TEST_ARGS="$TEST_ARGS --fail-fast"
[[ "$SKIP_INSTALL" == "true" ]] && TEST_ARGS="$TEST_ARGS --skip-install"
[[ "$KEEP_OUTPUTS" == "true" ]] && TEST_ARGS="$TEST_ARGS --keep-outputs"

# Pre-test formatting
if [[ "$FORMAT" == "true" ]]; then
    echo "🎨 Auto-formatting code..."
    uv run black src/ tests/ examples/ --quiet
    uv run isort src/ tests/ examples/ --quiet
    echo "✅ Code formatted"
fi

# Execute test suite based on selection
case $SUITE in
    quick)
        echo "🚀 Running quick test suite..."
        ./tools/testing/run_all_tests.sh --python-only --fail-fast
        ;;
        
    standard)
        echo "📋 Running standard test suite..."
        ./tools/testing/run_all_tests.sh $TEST_ARGS
        ;;
        
    full)
        echo "🔬 Running full test suite..."
        
        # Main tests
        ./tools/testing/run_all_tests.sh $TEST_ARGS || exit 1
        
        
        # Example validation
        echo "📚 Testing all examples..."
        failed_examples=()
        for example in examples/*.py; do
            [ -f "$example" ] || continue
            echo "  Testing $(basename "$example")..."
            if uv run python "$example" >/dev/null 2>&1; then
                echo "    ✅ $(basename "$example")"
            else
                echo "    ❌ $(basename "$example")"
                failed_examples+=("$(basename "$example")")
            fi
        done
        
        if [ ${#failed_examples[@]} -gt 0 ]; then
            echo "❌ ${#failed_examples[@]} examples failed"
            exit 1
        fi
        ;;
        
    regression)
        echo "🏗️ Running full regression suite (this will take several minutes)..."
        echo "⚠️  WARNING: This will clear all caches and rebuild everything!"
        echo ""
        
        # Run the comprehensive regression test
        ./tools/testing/run_full_regression_tests.py $TEST_ARGS
        ;;
        
    *)
        echo "❌ Unknown suite: $SUITE"
        echo "Available suites: quick, standard, full, regression"
        exit 1
        ;;
esac
```

## Test Results Interpretation

### Expected Results by Suite

**Quick Suite** (~30 seconds):
- Python tests only
- ~300 tests, expect 13 failures (known issues)
- Good for rapid development iteration

**Standard Suite** (~2 minutes):
- Full test coverage without environment rebuild
- Recommended for pre-commit checks

**Full Suite** (~5 minutes):
- Everything in Standard plus:
- All examples validated
- Recommended for branch merges

**Regression Suite** (~10 minutes):
- Complete environment reconstruction
- **MANDATORY before PyPI releases**
- Ensures clean slate testing
- Validates all dependencies

## Known Issues

Currently failing tests (not blockers for most development):
1. **Net constructor API** (5 failures) - Breaking change needs fix
2. **JLCPCB integration** (3 failures) - API reliability issues
3. **Hierarchical synchronizer** (4 failures) - Incomplete implementation
4. **DigiKey config** (1 failure) - Test assumption issue

## Usage Examples

```bash
# Quick development check
/dev-run-tests --suite=quick

# Standard pre-commit validation
/dev-run-tests

# Full validation before merge
/dev-run-tests --suite=full --verbose

# Release preparation (MANDATORY)
/dev-run-tests --suite=regression --verbose

# Debug specific failures
/dev-run-tests --suite=standard --verbose --fail-fast

# Fast iteration during debugging
/dev-run-tests --suite=quick --skip-install --format=false
```

## CI/CD Integration

```yaml
# GitHub Actions example
- name: Quick Tests
  run: /dev-run-tests --suite=quick --fail-fast
  
- name: Full Tests (on PR)
  run: /dev-run-tests --suite=full
  
- name: Regression Tests (on release)
  run: /dev-run-tests --suite=regression
```

## Best Practices

1. **Development**: Use `--suite=quick` for rapid iteration
2. **Pre-commit**: Run `--suite=standard` before committing
3. **Pre-merge**: Run `--suite=full` before merging branches
4. **Pre-release**: **ALWAYS** run `--suite=regression` before PyPI release
5. **Debugging**: Use `--verbose --fail-fast` to isolate issues

## Troubleshooting

**If tests fail:**
1. Check known issues above
2. Run with `--verbose` for details
3. Use `--fail-fast` to stop at first failure
4. Check `test_outputs/` directory for artifacts

**If regression suite fails:**
1. Ensure clean git working directory
2. Check network connection (for dependency downloads)
3. Verify KiCad is installed (for integration tests)
4. Review environment requirements in `pyproject.toml`

---

**This command orchestrates all existing test infrastructure, providing a single entry point for comprehensive testing while preserving the power of specialized test tools.**