# Cache Testing Strategy


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



```bash


```

## 📋 Detailed Usage

### 1. Cache Clearing (`clear_caches.py`)

Clears all caches to ensure clean testing environments.

```bash
# Clear all caches
python tests/cache/clear_caches.py --all


# Clear only Python caches
python tests/cache/clear_caches.py --python

# List cache locations without clearing
python tests/cache/clear_caches.py --list
```

**Features:**
- Discovers cache locations automatically
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
    "working": false,
  },
  "success_rate": 100.0,
  "recommendations": [
  ]
}
```

## 🎯 Available Cache Systems

The following cache systems remain available in the project:

| System | Purpose | Status |
|--------|---------|--------|
| **Python Symbol Cache** | KiCad symbol caching | ✅ Active |
| **Python Footprint Cache** | KiCad footprint caching | ✅ Active |

## 🐛 Troubleshooting

### Common Issues

```
```
**Solution:**
```bash
```

**2. Compilation Errors**
```
```
**Solution:**

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

# Run with verbose output
python scripts/cache_testing/run_cache_tests.py --verbose
```

### Manual Testing

Test individual components:

```python
python -c "
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

   ```bash
   ```

2. **Run Validation:**
   ```bash
   python tests/cache/run_cache_tests.py
   ```

## 📚 Additional Resources

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