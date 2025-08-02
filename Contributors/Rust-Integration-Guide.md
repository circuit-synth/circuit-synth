# Rust Integration Guide

Complete guide for working with circuit-synth's Python+Rust hybrid architecture. This covers the current integration points, how to contribute to Rust modules, and performance optimization strategies.

## 🦀 Python + Rust Architecture

Circuit-synth uses a **hybrid approach**: Python for API design and flexibility, Rust for performance-critical operations.

```
┌─────────────────────────────────────────────────────────┐
│                 Circuit-Synth Hybrid Architecture       │
├─────────────────────────────────────────────────────────┤
│  Python Layer (User Interface & API)                   │
│  ├─ Simple circuit definition syntax                   │
│  ├─ Component and net management                       │
│  ├─ Agent integration and orchestration               │
│  └─ Development tooling and testing                   │
├─────────────────────────────────────────────────────────┤
│  Rust Layer (Performance-Critical Operations)          │
│  ├─ KiCad file generation (S-expression processing)   │
│  ├─ Component placement algorithms                     │
│  ├─ Large-scale netlist processing                    │
│  ├─ Symbol search and caching                         │
│  └─ Mathematical optimization routines                │
├─────────────────────────────────────────────────────────┤
│  PyO3 Bindings (Seamless Integration)                  │
│  ├─ Automatic Python type conversion                  │
│  ├─ Error handling and exception mapping              │
│  ├─ Memory management between languages               │
│  └─ Performance monitoring and fallback               │
└─────────────────────────────────────────────────────────┘
```

## 🎯 Current Integration Points

### High-Priority Rust Modules (Perfect for Contributors!)

Based on our recent analysis, these are the **highest-impact opportunities**:

#### 1. **rust_netlist_processor** (Issue #36 - HIGH PRIORITY)
- **Current State**: Module missing, Python fallback in use
- **Performance Impact**: High - netlist processing is computationally intensive
- **Scope**: Core netlist validation, optimization, and export logic

#### 2. **rust_kicad_integration** (Issue #37 - HIGH PRIORITY)  
- **Current State**: Source exists but not compiled
- **Performance Impact**: Critical - affects all KiCad file generation
- **Scope**: S-expression parsing, formatting, and generation

#### 3. **rust_component_acceleration** (Issue #40 - CRITICAL PERFORMANCE)
- **Current State**: 97% of generation time spent in Python component processing
- **Performance Impact**: **Massive** - 1796ms for 6 components (300ms per component!)
- **Scope**: Component validation, symbol lookup, property processing

#### 4. **rust_force_directed_placement** (Issue #39)
- **Current State**: Using basic sequential placement
- **Performance Impact**: Medium - affects schematic quality
- **Scope**: Advanced placement algorithms, physics simulations

#### 5. **rust_core_circuit_engine** (Issue #38)
- **Current State**: Core operations using Python implementations
- **Performance Impact**: Medium-High - affects core circuit operations
- **Scope**: Circuit graph operations, analysis, validation

#### 6. **rust_s_expression_formatting** (Issue #41)
- **Current State**: Python S-expression processing
- **Performance Impact**: Medium - affects all file generation
- **Scope**: High-performance S-expression parsing and formatting

## 🚀 Getting Started with Rust Development

### 1. Environment Setup

```bash
# Install Rust toolchain
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source ~/.cargo/env

# Install Python-Rust integration tools
pip install maturin

# Verify installation
rustc --version
cargo --version
maturin --version
```

### 2. Understanding Our Rust Module Structure

```bash
rust_modules/
├── rust_kicad_integration/       # KiCad file generation (EXISTS - needs compilation)
│   ├── src/lib.rs               # Main Rust module
│   ├── src/python_bindings.rs   # PyO3 Python interface
│   ├── Cargo.toml               # Rust dependencies
│   └── pyproject.toml           # Python integration config
├── rust_netlist_processor/      # Netlist processing (MISSING - high impact)
├── rust_component_acceleration/  # Component processing (MISSING - critical)
└── [other modules]/             # Additional acceleration points
```

### 3. Working with Existing Modules

**Example: Compiling rust_kicad_integration**

```bash
# Navigate to module
cd rust_modules/rust_kicad_integration

# Check current status
cargo check

# Run tests
cargo test --lib --no-default-features

# Compile for Python integration
maturin develop --release

# Verify Python can import
python -c "import rust_kicad_integration; print('✅ Module compiled successfully')"
```

## 📊 Performance Analysis & Optimization

### Current Performance Bottlenecks (From Real Data)

**Component Processing (Critical Bottleneck):**
```
Component Addition: 1796.33ms (97.1% of total generation time)
Total Generation Time: 1849.59ms  
Throughput: Only 21.5 chars/ms
```

**This means**: Adding 6 components takes 1.8 seconds - completely unacceptable for production use!

**S-Expression Processing:**
```
S-expression formatting: 0.64ms (63.1% of file write time)
Per-file processing: ~1ms of S-expression overhead
Multiple files: Impact multiplies across entire project
```

### Performance Targets

Based on industry standards and user expectations:

- **Component Processing**: <10ms for typical circuits (6-20 components) - **100x improvement needed**
- **S-Expression Processing**: >5x improvement in formatting speed
- **Netlist Processing**: Handle 1000+ component circuits efficiently  
- **Overall Throughput**: >1000 chars/ms (vs current 21.5 chars/ms)

## 🛠️ Rust Development Patterns

### 1. PyO3 Integration Pattern

```rust
// src/lib.rs - Main Rust implementation
use pyo3::prelude::*;

#[pyclass]
pub struct ComponentProcessor {
    // Rust implementation
}

#[pymethods]
impl ComponentProcessor {
    #[new]
    pub fn new() -> Self {
        ComponentProcessor {}
    }
    
    pub fn process_components(&self, components: Vec<PyDict>) -> PyResult<String> {
        // High-performance Rust logic here
        Ok("processed_result".to_string())
    }
}

#[pymodule]
fn rust_component_acceleration(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<ComponentProcessor>()?;
    Ok(())
}
```

### 2. Error Handling Pattern

```rust
use pyo3::exceptions::PyValueError;

pub fn process_circuit(data: &str) -> PyResult<String> {
    match parse_circuit_data(data) {
        Ok(result) => Ok(result),
        Err(e) => Err(PyValueError::new_err(format!("Circuit processing failed: {}", e)))
    }
}
```

### 3. Performance Monitoring Pattern

```rust
use std::time::Instant;

pub fn accelerated_function(&self, input: &str) -> PyResult<String> {
    let start = Instant::now();
    
    // Rust implementation
    let result = perform_operation(input);
    
    let duration = start.elapsed();
    println!("🦀 Rust acceleration: completed in {:?}", duration);
    
    Ok(result)
}
```

## 🧪 Testing Rust Modules

### Unit Testing

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_component_processing() {
        let processor = ComponentProcessor::new();
        let result = processor.process_components(vec![]);
        assert!(result.is_ok());
    }
    
    #[test]
    fn test_performance_benchmark() {
        use std::time::Instant;
        
        let start = Instant::now();
        // Test operation
        let duration = start.elapsed();
        
        // Assert performance target
        assert!(duration.as_millis() < 10, "Processing too slow: {:?}", duration);
    }
}
```

### Integration Testing

```bash
# Test Rust module compilation
cargo test --lib --no-default-features

# Test Python integration
maturin develop --release
python -c "
import rust_component_acceleration
processor = rust_component_acceleration.ComponentProcessor()
print('✅ Python-Rust integration working')
"

# Test performance improvement
uv run python example_project/circuit-synth/main.py
# Look for: "🦀 Rust acceleration: ..." log messages
```

## 📈 Performance Benchmarking

### 1. Before/After Comparisons

```python
# benchmark_script.py
import time
import rust_component_acceleration  # Your new module
from circuit_synth.core.component import ComponentProcessor  # Python fallback

def benchmark_component_processing():
    components = [...]  # Test data
    
    # Python implementation
    start = time.time()
    python_result = ComponentProcessor().process(components)
    python_time = time.time() - start
    
    # Rust implementation  
    start = time.time()
    rust_result = rust_component_acceleration.ComponentProcessor().process(components)
    rust_time = time.time() - start
    
    speedup = python_time / rust_time
    print(f"🚀 Rust speedup: {speedup:.1f}x faster ({python_time:.3f}s → {rust_time:.3f}s)")
    
    assert python_result == rust_result, "Results must be identical"
    assert speedup > 5.0, f"Expected >5x speedup, got {speedup:.1f}x"
```

### 2. Memory Usage Analysis

```rust
// Use in your Rust code for memory monitoring
#[cfg(feature = "profiling")]
fn monitor_memory_usage() {
    use std::alloc::{GlobalAlloc, Layout, System};
    // Memory monitoring implementation
}
```

## 🔄 Fallback System Implementation

### Python Fallback Pattern

```python
# src/circuit_synth/core/rust_integration.py
try:
    import rust_component_acceleration
    RUST_COMPONENT_AVAILABLE = True
    logging.info("🦀 Rust component acceleration available")
except ImportError:
    RUST_COMPONENT_AVAILABLE = False
    logging.info("🐍 Using Python component processing (Rust not available)")

def process_components(components):
    if RUST_COMPONENT_AVAILABLE:
        return rust_component_acceleration.ComponentProcessor().process(components)
    else:
        # Python fallback implementation
        return python_component_processor(components)
```

## 🎯 Contribution Workflow

### 1. Choose Your Module

Pick based on impact and complexity:
- **Highest Impact**: rust_component_acceleration (Issue #40)
- **Good Starting Point**: rust_s_expression_formatting (Issue #41)
- **Advanced Challenge**: rust_force_directed_placement (Issue #39)

### 2. Development Process

```bash
# 1. Create module directory
mkdir rust_modules/rust_your_module
cd rust_modules/rust_your_module

# 2. Initialize Rust project
cargo init --lib
maturin init --bindings pyo3

# 3. Implement core logic
# Edit src/lib.rs, src/python_bindings.rs

# 4. Test incrementally
cargo test --lib
maturin develop --release
python -c "import rust_your_module; print('Works!')"

# 5. Benchmark performance
# Compare with Python implementation

# 6. Integration testing
./scripts/test_rust_modules.sh --module your_module
```

### 3. Code Review Preparation

```bash
# Before submitting PR:
cargo fmt                    # Format Rust code
cargo clippy                # Lint Rust code  
cargo test --lib           # Run Rust tests
maturin develop --release   # Test Python integration
./scripts/run_all_tests.sh  # Ensure no regressions
```

## 🔍 Debugging Rust Integration

### Common Issues and Solutions

**Module Import Errors:**
```bash
# Check if module compiled
ls target/wheels/

# Reinstall in development mode
maturin develop --release --force

# Verify Python path
python -c "import sys; print(sys.path)"
```

**Performance Not Improving:**
```bash
# Ensure release build
maturin develop --release

# Check if Rust path is taken
# Look for "🦀 Rust acceleration: ..." in logs

# Profile Rust code
cargo build --release
perf record target/release/your_binary
```

**PyO3 Type Conversion Issues:**
```rust
// Use proper PyO3 types
use pyo3::types::{PyDict, PyList, PyString};

#[pyfunction]
fn process_data(py_dict: &PyDict) -> PyResult<String> {
    // Convert PyDict to Rust types
    let rust_data: HashMap<String, String> = py_dict.extract()?;
    // Process in Rust
    Ok(result)
}
```

## 📚 Additional Resources

### Learning Materials
- **PyO3 Documentation**: https://pyo3.rs/
- **Maturin Guide**: https://github.com/PyO3/maturin
- **Rust Performance Book**: https://nnethercote.github.io/perf-book/

### Circuit-Synth Specific
- **Performance Analysis**: Review our GitHub issues #36-41 for detailed performance data
- **Architecture Decisions**: See `memory-bank/decisions/` for technical reasoning
- **Existing Patterns**: Study `rust_modules/rust_kicad_integration/` for working example

---

**Ready to make a high-impact contribution?** Pick a Rust module and start optimizing! The performance improvements will directly benefit every circuit-synth user. 🚀