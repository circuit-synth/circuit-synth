# Cache Testing Strategy

This directory contains testing utilities for validating cache systems in the Circuit Synth project, focusing on the remaining Rust cache implementations.

**Location:** `tests/cache/` (moved from `scripts/cache_testing/`)

## 🎯 Overview

The testing strategy provides:

1. **Cache Clearing Utilities** - Clean testing environments
2. **Performance Monitoring** - Real-time cache usage tracking
3. **Master Test Runner** - Orchestrate cache testing

## 📁 Files Structure

```
tests/cache/
├── README.md                           # This documentation
├── clear_caches.py                     # Cache clearing utility
├── cache_monitor.py                    # Performance monitoring system
└── run_cache_tests.py                  # Master test runner
```

## 🚀 Quick Start

### Prerequisites

1. **Python Environment**: Ensure Circuit Synth dependencies are installed
2. **Rust Caches**: The remaining Rust cache systems should be built:
   - `rust_symbol_cache`
   - `rust_symbol_search` 
   - `rust_reference_manager`
3. **Project Structure**: Run from Circuit Synth root directory

### Running Tests

```bash
# Quick validation
python tests/cache/run_cache_tests.py --quick

# Complete test suite
python tests/cache/run_cache_tests.py

# With verbose output
python tests/cache/run_cache_tests.py --verbose
```

## 🔧 Building Rust Caches

Before running tests, ensure the remaining Rust caches are properly built:

```bash
# Build rust_symbol_cache
cd rust_symbol_cache
cargo build --features python-bindings
pip install maturin
maturin develop

# Build rust_symbol_search
cd ../rust_symbol_search
cargo build --features python-bindings
maturin develop

# Build rust_reference_manager
cd ../rust_reference_manager
cargo build --features python-bindings
maturin develop
```

## 📋 Detailed Usage

### 1. Cache Clearing (`clear_caches.py`)

Clears all caches to ensure clean testing environments.

```bash
# Clear all caches
python tests/cache/clear_caches.py --all

# Clear only Rust caches
python tests/cache/clear_caches.py --rust

# Clear only Python caches
python tests/cache/clear_caches.py --python

# List cache locations without clearing
python tests/cache/clear_caches.py --list
```

**Features:**
- Discovers cache locations automatically
- Handles Python `__pycache__`, Rust `target/`, KiCad caches
- Safe operation with error handling
- Detailed logging of cleared items

### 2. Performance Monitoring (`cache_monitor.py`)

Real-time monitoring of cache operations with performance metrics.

```bash
# Monitor example project execution
python tests/cache/cache_monitor.py --run-example

# Monitor for specific duration
python tests/cache/cache_monitor.py --duration 120

# Save metrics to custom file
python tests/cache/cache_monitor.py --output my_metrics.json
```

**Features:**
- Real-time operation tracking
- Memory usage monitoring
- Performance comparison between cache systems
- Cache hit/miss rates
- Automatic instrumentation of cache methods

### 3. Master Test Runner (`run_cache_tests.py`)

Orchestrates the cache testing suite with comprehensive reporting.

```bash
# Complete test suite
python tests/cache/run_cache_tests.py

# Quick validation only
python tests/cache/run_cache_tests.py --quick

# Skip specific test types
python tests/cache/run_cache_tests.py --no-benchmarks --no-monitoring

# Custom output directory
python tests/cache/run_cache_tests.py --output-dir my_test_results
```

**Test Suite Components:**
1. **Cache Clearing** - Clean environment
2. **Monitored Example** - Real-world usage
3. **Performance Benchmarks** - Detailed metrics

## 📊 Understanding Results

### Success Indicators

**✅ Cache Systems Working:**
- Python cache systems functional
- Remaining Rust caches (symbol_cache, symbol_search, reference_manager) operational
- No import or initialization errors

**🚀 Performance Monitoring:**
- Cache hit/miss rates tracked
- Memory usage monitored
- Performance comparisons available

### Output Files

The test suite generates reports:

```
cache_test_results/
├── master_test_report.json              # Complete summary
├── example_monitoring_metrics.json      # Performance monitoring
├── performance_benchmarks.json          # Benchmark results
└── cache_locations.json                 # Cache discovery results
```

### Reading Reports

**Master Report Structure:**
```json
{
  "rust_cache_status": {
    "working": false,
    "note": "rust_unified_cache removed from project"
  },
  "success_rate": 100.0,
  "recommendations": [
    "ℹ️  Rust unified cache has been removed from the project.",
    "✅ Other Rust cache systems remain available."
  ]
}
```

## 🎯 Available Cache Systems

The following cache systems remain available in the project:

| System | Purpose | Status |
|--------|---------|--------|
| **Python Symbol Cache** | KiCad symbol caching | ✅ Active |
| **Python Footprint Cache** | KiCad footprint caching | ✅ Active |
| **rust_symbol_cache** | Rust-based symbol caching | ✅ Active |
| **rust_symbol_search** | Rust-based symbol search | ✅ Active |
| **rust_reference_manager** | Rust-based reference management | ✅ Active |

## 🐛 Troubleshooting

### Common Issues

**1. Rust Cache Import Error**
```
ImportError: No module named 'rust_symbol_cache'
```
**Solution:**
```bash
cd rust_symbol_cache
maturin develop
```

**2. Compilation Errors**
```
error: could not compile `rust_symbol_cache`
```
**Solution:**
- Check Rust installation: `rustc --version`
- Update dependencies: `cargo update`
- Clean build: `cargo clean && cargo build`

**3. Example Project Fails**
```
❌ Example project failed (exit code: 1)
```
**Solution:**
- Check dependencies: `pip install -r requirements.txt`
- Verify KiCad libraries are available
- Run with verbose output: `--verbose`

### Debug Mode

Enable detailed logging for troubleshooting:

```bash
# Set environment variable
export RUST_LOG=debug

# Run with verbose output
python scripts/cache_testing/run_cache_tests.py --verbose
```

### Manual Testing

Test individual components:

```python
# Test rust_symbol_cache
python -c "
import rust_symbol_cache
cache = rust_symbol_cache.SymbolCache()
print('rust_symbol_cache available')
"

# Test Python cache
python -c "
from circuit_synth.kicad_api.core.symbol_cache import get_symbol_cache
cache = get_symbol_cache()
print('Python cache available')
"
```

## 🔄 Development Workflow

### Before Making Changes

1. **Clear Caches:**
   ```bash
   python tests/cache/clear_caches.py --all
   ```

2. **Baseline Performance:**
   ```bash
   python tests/cache/run_cache_tests.py --quick
   ```

### After Making Changes

1. **Rebuild Rust Caches:**
   ```bash
   cd rust_symbol_cache && maturin develop
   cd ../rust_symbol_search && maturin develop
   cd ../rust_reference_manager && maturin develop
   ```

2. **Run Validation:**
   ```bash
   python tests/cache/run_cache_tests.py
   ```

## 📚 Additional Resources

- **Rust Symbol Cache:** [`rust_symbol_cache/README.md`](../../rust_symbol_cache/README.md)
- **Rust Symbol Search:** [`rust_symbol_search/README.md`](../../rust_symbol_search/README.md)
- **Rust Reference Manager:** [`rust_reference_manager/README.md`](../../rust_reference_manager/README.md)
- **Example Project:** [`examples/example_kicad_project.py`](../../examples/example_kicad_project.py)

## 🤝 Contributing

When adding new tests:

1. **Follow the pattern** of existing test modules
2. **Add comprehensive logging** with appropriate levels
3. **Include error handling** and graceful degradation
4. **Update this documentation** with new features
5. **Test with available cache systems**

## 📄 License

This testing suite is part of the Circuit Synth project and follows the same license terms.