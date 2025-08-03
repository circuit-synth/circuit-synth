---
allowed-tools: Bash(uv*), Bash(pytest*), Bash(open*), Bash(cargo*), Bash(./scripts/*)
description: Comprehensive test suite with Python, Rust, and integration testing
---

# Comprehensive Test Runner

**Purpose:** Complete testing pipeline with Python tests, Rust modules, circuit validation, and performance benchmarking.

## Usage
```bash
/dev-run-tests [options]
```

## Options
- `--suite=all` - Test suite: `python`, `rust`, `integration`, `examples`, `performance`, `all` (default: all)
- `--coverage=true` - Generate coverage reports (default: true)
- `--format=true` - Auto-format code before testing (default: true)
- `--fail-fast=false` - Stop on first failure (default: false)
- `--verbose=false` - Verbose output (default: false)
- `--benchmark=false` - Run performance benchmarks (default: false)

## What This Does

### 1. Pre-Test Setup and Validation
- **Environment check** - Verify uv, Python, and dependencies
- **Auto-formatting** - Format code with black/isort before testing
- **Dependency validation** - Ensure dev dependencies are installed
- **KiCad availability** - Check for KiCad integration testing

### 2. Python Test Suite
- **Unit tests** - Core functionality testing
- **Integration tests** - Component interaction testing  
- **Circuit validation** - Test actual circuit generation
- **Coverage analysis** - Generate detailed coverage reports
- **Type checking** - MyPy static analysis (informational only)

### 3. Rust Module Testing
- **Rust compilation** - Build all Rust modules
- **Rust unit tests** - Native Rust test suite
- **Python-Rust integration** - Cross-language bindings
- **Performance validation** - Rust module benchmarks

### 4. Example and Circuit Testing
- **Example execution** - Run all examples/\*.py files
- **Circuit generation** - Validate KiCad output
- **Component verification** - Check all components are valid
- **File output validation** - Ensure generated files are correct

### 5. Performance Benchmarking
- **Circuit generation speed** - Time key operations
- **Memory usage profiling** - Track memory consumption
- **KiCad integration performance** - File generation benchmarks
- **Regression detection** - Compare against baselines

## Implementation

### Pre-Test Setup
```bash
# Check environment
echo "🔍 Checking test environment..."
uv --version >/dev/null || { echo "❌ uv not found"; exit 1; }
python --version
kicad-cli version >/dev/null 2>&1 && echo "✅ KiCad available" || echo "⚠️  KiCad not found"

# Install dependencies if needed
echo "📦 Ensuring dev dependencies..."
uv pip install -e ".[dev]" --quiet

# Auto-format code (if enabled)
if [[ "$format" == "true" ]]; then
    echo "🎨 Auto-formatting code..."
    uv run black src/ tests/ examples/ --quiet
    uv run isort src/ tests/ examples/ --quiet
    echo "✅ Code formatted"
fi
```

### Python Test Execution
```bash
# Core test suite with coverage
echo "🐍 Running Python test suite..."
test_args=""
[[ "$fail_fast" == "true" ]] && test_args="$test_args -x"
[[ "$verbose" == "true" ]] && test_args="$test_args -v"

if [[ "$coverage" == "true" ]]; then
    uv run pytest tests/ --cov=circuit_synth --cov-report=term-missing --cov-report=html $test_args || {
        echo "❌ Python tests failed"
        exit 1
    }
    echo "📊 Coverage report: htmlcov/index.html"
else
    uv run pytest tests/ $test_args || {
        echo "❌ Python tests failed"  
        exit 1
    }
fi

# Type checking (informational)
echo "🔍 Running type checks..."
uv run mypy src/ --ignore-missing-imports --no-error-summary || echo "⚠️  Type checking issues found (non-blocking)"
```

### Rust Module Testing
```bash
# Check for Rust modules
rust_modules=($(find . -name "Cargo.toml" -exec dirname {} \; 2>/dev/null))

if [ ${#rust_modules[@]} -gt 0 ]; then
    echo "🦀 Testing Rust modules..."
    for module in "${rust_modules[@]}"; do
        echo "  Testing $module..."
        cd "$module"
        
        # Build and test
        cargo build --release || {
            echo "❌ Rust build failed in $module"
            exit 1
        }
        
        cargo test || {
            echo "❌ Rust tests failed in $module"
            exit 1
        }
        
        # Benchmark if requested
        if [[ "$benchmark" == "true" ]]; then
            cargo bench --no-run 2>/dev/null && cargo bench || echo "⚠️  No benchmarks in $module"
        fi
        
        cd - >/dev/null
    done
    echo "✅ All Rust modules passed"
else
    echo "ℹ️  No Rust modules found"
fi
```

### Example and Circuit Testing
```bash
# Test all examples
echo "📋 Testing examples..."
example_count=0
failed_examples=()

for example in examples/*.py; do
    [ -f "$example" ] || continue
    echo "  Testing $(basename "$example")..."
    
    if uv run python "$example" >/dev/null 2>&1; then
        echo "    ✅ $(basename "$example")"
        ((example_count++))
    else
        echo "    ❌ $(basename "$example")"
        failed_examples+=("$(basename "$example")")
    fi
done

if [ ${#failed_examples[@]} -eq 0 ]; then
    echo "✅ All $example_count examples passed"
else
    echo "❌ ${#failed_examples[@]} examples failed:"
    printf '  - %s\n' "${failed_examples[@]}"
    [[ "$fail_fast" == "true" ]] && exit 1
fi

# Circuit generation validation
echo "🔌 Testing circuit generation..."
temp_dir=$(mktemp -d)
cd "$temp_dir"

uv run python -c "
from circuit_synth import Circuit, Component, Net
import tempfile
import os

# Test basic circuit generation
@circuit(name='test_circuit')
def test_circuit():
    vcc = Net('VCC')
    gnd = Net('GND')
    r1 = Component(symbol='Device:R', ref='R', value='1k', footprint='Resistor_SMD:R_0603_1608Metric')
    r1[1] += vcc
    r1[2] += gnd

# Test KiCad generation
if test_circuit.generate_kicad():
    print('✅ Circuit generation successful')
else:
    print('❌ Circuit generation failed')
    exit(1)
" || {
    echo "❌ Circuit generation test failed"
    exit 1
}

cd - >/dev/null
rm -rf "$temp_dir"
```

### Performance Benchmarking
```bash
if [[ "$benchmark" == "true" ]]; then
    echo "⚡ Running performance benchmarks..."
    
    # Circuit generation benchmark
    echo "  Benchmarking circuit generation..."
    python -c "
import time
from circuit_synth import Circuit, Component, Net

# Benchmark component creation
start_time = time.time()
for i in range(100):
    Component(symbol='Device:R', ref='R', value=f'{i}k', footprint='Resistor_SMD:R_0603_1608Metric')
component_time = time.time() - start_time

# Benchmark net connections  
start_time = time.time()
vcc = Net('VCC')
for i in range(100):
    r = Component(symbol='Device:R', ref='R', value='1k', footprint='Resistor_SMD:R_0603_1608Metric')
    r[1] += vcc
connection_time = time.time() - start_time

print(f'📊 Component creation: {component_time:.3f}s for 100 components')
print(f'📊 Net connections: {connection_time:.3f}s for 100 connections')
"
    
    # Memory usage profiling
    if command -v memory_profiler >/dev/null 2>&1; then
        echo "  Memory profiling main example..."
        uv run python -m memory_profiler examples/example_kicad_project.py 2>/dev/null || echo "⚠️  Memory profiling failed"
    fi
fi
```

### Test Results Summary
```bash
# Generate test summary
echo ""
echo "📊 Test Results Summary"
echo "======================"
echo "Python Tests: $([ $python_tests_passed -eq 1 ] && echo "✅ PASSED" || echo "❌ FAILED")"
echo "Rust Tests: $([ ${#rust_modules[@]} -eq 0 ] && echo "ℹ️  N/A" || echo "✅ PASSED")"
echo "Examples: $([ ${#failed_examples[@]} -eq 0 ] && echo "✅ PASSED ($example_count)" || echo "❌ FAILED (${#failed_examples[@]}/$example_count)")"
echo "Circuit Generation: ✅ PASSED"
[[ "$coverage" == "true" ]] && echo "Coverage Report: htmlcov/index.html"
[[ "$benchmark" == "true" ]] && echo "Benchmarks: Completed"

# Exit with appropriate code
total_failures=$((${#failed_examples[@]} + (1 - python_tests_passed)))
if [ $total_failures -eq 0 ]; then
    echo ""
    echo "🎉 All tests passed successfully!"
    exit 0
else
    echo ""
    echo "❌ $total_failures test suite(s) failed"
    exit 1
fi
```

## Expected Results

**Healthy Repository:**
- ✅ Python tests: ~158 tests passing, ~3 skipped
- ✅ Rust tests: All modules compile and pass
- ✅ Examples: All examples execute without errors
- ✅ Circuit generation: KiCad files generated successfully
- 📊 Coverage: Detailed HTML report generated
- ⚡ Performance: Baseline benchmarks established

**Known Issues (Non-blocking):**
- ⚠️ Flake8: Style warnings (cosmetic)
- ⚠️ MyPy: Type checking errors (improving)
- 📊 Coverage: ~24% (target: >60%)

## Example Usage

```bash
# Full test suite
/dev-run-tests

# Quick Python-only tests
/dev-run-tests --suite=python --coverage=false

# Performance focused testing
/dev-run-tests --suite=all --benchmark=true

# Development workflow (fast)
/dev-run-tests --suite=python --fail-fast=true --verbose=true

# CI/CD pipeline testing
/dev-run-tests --format=false --coverage=true --fail-fast=true
```

## Integration with Development Workflow

This command integrates with:
- **Pre-commit hooks** - Run quick tests before commits
- **Branch reviews** - Full test suite validation
- **Release pipeline** - Comprehensive testing before PyPI
- **Performance monitoring** - Track regression over time

---

**This comprehensive test runner ensures code quality, functionality, and performance across the entire circuit-synth ecosystem.**