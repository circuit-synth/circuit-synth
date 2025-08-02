# Testing Guidelines

Circuit-synth follows a **Test-Driven Development (TDD)** approach with comprehensive testing infrastructure. This guide covers our testing philosophy, tools, and best practices.

## 🧪 Testing Philosophy

### Core Principles

1. **Test-Driven Development (TDD)**: Write tests first, then implement functionality
2. **Comprehensive Coverage**: Every feature has unit, integration, and functional tests
3. **Performance Validation**: All optimizations include benchmark tests
4. **Regression Prevention**: Tests prevent functionality breakdown
5. **AI-Friendly Testing**: Tests designed to be understood and extended by AI agents

### Testing Pyramid

```
        ┌─────────────────┐
        │  Manual Testing │  ← Final validation, edge cases
        ├─────────────────┤
        │  E2E/Functional │  ← Complete workflows (KiCad generation)
        │     Tests       │
        ├─────────────────┤
        │  Integration    │  ← Multi-component interactions
        │     Tests       │
        ├─────────────────┤
        │  Unit Tests     │  ← Individual functions and classes
        └─────────────────┘
```

## 🚀 Quick Testing Commands

### Automated Test Scripts

```bash
# Complete test suite (what CI uses)
./scripts/run_all_tests.sh

# Python-only tests (fastest for development)
./scripts/run_all_tests.sh --python-only

# Rust module tests  
./scripts/test_rust_modules.sh

# Specific test categories
./scripts/run_all_tests.sh --rust-only
./scripts/run_all_tests.sh --integration-only

# Development mode (stop on first failure)
./scripts/run_all_tests.sh --fail-fast --verbose
```

### Manual Test Commands

```bash
# Unit tests
uv run pytest tests/unit/ -v

# Integration tests
uv run pytest tests/integration/ -v

# Rust integration tests
uv run pytest tests/rust_integration/ -v

# Functional tests (end-to-end)
uv run pytest tests/functional_tests/ -v

# Performance tests
uv run pytest tests/performance/ -v --benchmark-only
```

## 📁 Test Organization

### Directory Structure

```
tests/
├── unit/                    # Individual component tests
│   ├── test_core_circuit.py       # Circuit class functionality
│   ├── test_component.py          # Component creation and validation
│   ├── test_net.py                # Net management and connections
│   └── io/
│       └── test_json_loader.py    # JSON import/export
├── integration/             # Multi-component interaction tests
│   ├── test_kicad_sync_integration.py  # KiCad bidirectional sync
│   └── test_manufacturing_integration.py  # JLCPCB, component search
├── rust_integration/        # Rust/Python integration tests
│   ├── test_rust_tdd_framework.py     # Rust module testing framework
│   └── test_simple_rust_tdd.py        # Basic Rust functionality
├── functional_tests/        # End-to-end workflow tests
│   ├── test_01_resistor_divider/      # Complete circuit generation
│   ├── test_02_import_resistor_divider/  # KiCad import workflow
│   └── test_03_round_trip_python_kicad_python/  # Bidirectional sync
├── performance/             # Performance and benchmark tests
│   ├── test_component_processing_benchmark.py
│   └── test_kicad_generation_performance.py
└── test_data/              # Test fixtures and data
    ├── expected_outputs.json      # Expected test results
    ├── kicad_symbols/             # Test KiCad libraries
    └── stm32-complex-pins.xml     # STM32 test data
```

## 🎯 Test-Driven Development Workflow

### TDD Cycle (Red-Green-Refactor)

```python
# 1. RED: Write failing test first
def test_component_processing_performance():
    """Component processing should be <10ms for typical circuits."""
    components = create_test_components(count=6)
    
    start_time = time.time()
    result = process_components(components)
    duration = time.time() - start_time
    
    # This will fail initially - that's the point!
    assert duration < 0.01, f"Too slow: {duration:.3f}s"
    assert result is not None
    assert len(result.components) == 6

# 2. GREEN: Write minimal code to make test pass
def process_components(components):
    # Minimal implementation that passes
    return ProcessingResult(components=components)

# 3. REFACTOR: Improve implementation while keeping tests green
def process_components(components):
    # Optimized implementation with Rust acceleration
    if RUST_AVAILABLE:
        return rust_component_acceleration.process(components)
    else:
        return python_fallback_process(components)
```

### TDD Example: Adding New Feature

**Example: Adding STM32 Peripheral Search**

```python
# Step 1: Write test for desired behavior
def test_stm32_peripheral_search():
    """Should find STM32s with specific peripherals and JLCPCB availability."""
    # Test the interface we want to exist
    results = search_stm32("3 spi 2 uart jlcpcb available")
    
    assert len(results) > 0
    assert all(r.spi_count >= 3 for r in results)
    assert all(r.uart_count >= 2 for r in results)
    assert all(r.jlcpcb_available for r in results)
    assert all(r.kicad_symbol_verified for r in results)

# Step 2: Run test (it will fail - no function exists yet)
uv run pytest tests/unit/test_stm32_search.py::test_stm32_peripheral_search -v
# FAILED: AttributeError: module has no attribute 'search_stm32'

# Step 3: Implement minimal functionality
def search_stm32(query):
    # Minimal implementation that passes basic test
    return [STM32Result(
        part_number="STM32F407VET6",
        spi_count=3,
        uart_count=4,
        jlcpcb_available=True,
        kicad_symbol_verified=True
    )]

# Step 4: Run test again (should pass)
uv run pytest tests/unit/test_stm32_search.py::test_stm32_peripheral_search -v
# PASSED

# Step 5: Add more comprehensive tests and refactor implementation
def test_stm32_search_edge_cases():
    """Test edge cases and error handling."""
    # Empty query
    assert search_stm32("") == []
    
    # Invalid query
    with pytest.raises(ValueError):
        search_stm32("invalid query format")
    
    # No matches
    results = search_stm32("100 spi 50 uart")  # Impossible requirements
    assert results == []

# Step 6: Implement robust solution
def search_stm32(query):
    # Parse query, validate input, search modm-devices, check JLCPCB, etc.
    # Full implementation with error handling and edge cases
```

## 🧪 Test Categories and Examples

### 1. Unit Tests

**Test individual components in isolation:**

```python
# tests/unit/test_core_circuit.py
import pytest
from circuit_synth import Circuit, Component, Net

class TestCircuit:
    def test_circuit_creation(self):
        """Test basic circuit creation and properties."""
        circuit = Circuit("test_circuit")
        
        assert circuit.name == "test_circuit"
        assert len(circuit.components) == 0
        assert len(circuit.nets) == 0
    
    def test_component_addition(self):
        """Test adding components to circuit."""
        circuit = Circuit("test")
        resistor = Component("Device:R", ref="R", value="1k")
        
        circuit.add_component(resistor)
        
        assert len(circuit.components) == 1
        assert circuit.components[0].ref == "R1"  # Auto-assigned
        assert circuit.components[0].value == "1k"
    
    def test_net_connections(self):
        """Test component connections via nets."""
        circuit = Circuit("test")
        vcc = Net("VCC")
        resistor = Component("Device:R", ref="R")
        
        resistor[1] += vcc  # Connect pin 1 to VCC net
        
        assert len(vcc.pins) == 1
        assert vcc.pins[0].component == resistor
        assert vcc.pins[0].pin_number == 1
```

### 2. Integration Tests

**Test component interactions:**

```python
# tests/integration/test_kicad_integration.py
import pytest
from circuit_synth import Circuit, Component, Net

class TestKiCadIntegration:
    def test_complete_kicad_generation(self):
        """Test complete circuit to KiCad workflow."""
        # Create circuit
        circuit = self.create_test_circuit()
        
        # Generate KiCad project
        project_path = circuit.generate_kicad_project("test_project")
        
        # Verify files exist
        assert (project_path / "test_project.kicad_pro").exists()
        assert (project_path / "test_project.kicad_sch").exists()
        assert (project_path / "test_project.kicad_pcb").exists()
        
        # Verify file contents
        sch_content = (project_path / "test_project.kicad_sch").read_text()
        assert "Device:R" in sch_content  # Component symbols
        assert "VCC" in sch_content       # Net names
        
    def test_bidirectional_sync(self):
        """Test Python → KiCad → Python round trip."""
        original_circuit = self.create_test_circuit()
        
        # Generate KiCad
        project_path = original_circuit.generate_kicad_project("roundtrip")
        
        # Import back from KiCad
        imported_circuit = Circuit.from_kicad_project(project_path / "roundtrip.kicad_pro")
        
        # Verify equivalence
        assert len(imported_circuit.components) == len(original_circuit.components)
        assert len(imported_circuit.nets) == len(original_circuit.nets)
        
        # Verify component properties preserved
        for orig, imported in zip(original_circuit.components, imported_circuit.components):
            assert orig.symbol == imported.symbol
            assert orig.value == imported.value
```

### 3. Functional Tests (End-to-End)

**Test complete user workflows:**

```python
# tests/functional_tests/test_esp32_development_board.py
import pytest
import tempfile
from pathlib import Path

class TestESP32DevelopmentBoard:
    def test_complete_esp32_board_generation(self):
        """Test generating complete ESP32 development board."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Run complete example
            result = run_command([
                "uv", "run", "python", 
                "example_project/circuit-synth/main.py"
            ], cwd=temp_dir)
            
            assert result.returncode == 0
            
            # Verify generated files
            project_dir = Path(temp_dir) / "ESP32_C6_Dev_Board"
            assert project_dir.exists()
            
            # Verify hierarchical structure
            assert (project_dir / "ESP32_C6_Dev_Board.kicad_sch").exists()
            assert (project_dir / "USB_Port.kicad_sch").exists()
            assert (project_dir / "Power_Supply.kicad_sch").exists()
            assert (project_dir / "ESP32_C6_MCU.kicad_sch").exists()
            
            # Verify netlist connectivity
            netlist_path = project_dir / "ESP32_C6_Dev_Board.net"
            assert netlist_path.exists()
            
            netlist_content = netlist_path.read_text()
            assert "VCC_3V3" in netlist_content
            assert "USB_DP" in netlist_content
            assert "USB_DM" in netlist_content
    
    def test_kicad_compatibility(self):
        """Test that generated files open in KiCad without errors."""
        # Generate project
        project_path = self.generate_test_project()
        
        # Test KiCad CLI validation (if available)
        try:
            result = run_command([
                "kicad-cli", "sch", "export", "netlist",
                str(project_path / "test.kicad_sch")
            ])
            assert result.returncode == 0, "KiCad validation failed"
        except FileNotFoundError:
            pytest.skip("KiCad CLI not available")
```

### 4. Performance Tests

**Test and benchmark performance:**

```python
# tests/performance/test_component_processing_benchmark.py
import pytest
import time
from circuit_synth import Component

class TestComponentProcessingPerformance:
    @pytest.mark.benchmark
    def test_component_processing_speed(self, benchmark):
        """Benchmark component processing performance."""
        components = [
            Component("Device:R", ref="R", value=f"{i}k")
            for i in range(100)  # 100 components
        ]
        
        def process_components():
            return [c.to_dict() for c in components]
        
        result = benchmark(process_components)
        
        # Verify performance targets
        assert benchmark.stats['mean'] < 0.01, "Component processing too slow"
        assert len(result) == 100
    
    def test_rust_acceleration_benchmark(self):
        """Compare Rust vs Python performance."""
        components = self.create_test_components(count=50)
        
        # Python implementation
        start = time.time()
        python_result = python_component_processor(components)
        python_time = time.time() - start
        
        # Rust implementation (if available)
        if RUST_AVAILABLE:
            start = time.time()
            rust_result = rust_component_processor(components)
            rust_time = time.time() - start
            
            # Verify results identical
            assert rust_result == python_result
            
            # Verify performance improvement
            speedup = python_time / rust_time
            assert speedup > 5.0, f"Expected >5x speedup, got {speedup:.1f}x"
            
            print(f"🚀 Rust speedup: {speedup:.1f}x ({python_time:.3f}s → {rust_time:.3f}s)")
```

### 5. Rust Integration Tests

**Test Rust/Python integration:**

```python
# tests/rust_integration/test_rust_kicad_integration.py
import pytest

class TestRustKiCadIntegration:
    def test_rust_module_import(self):
        """Test that Rust modules can be imported."""
        try:
            import rust_kicad_integration
            assert hasattr(rust_kicad_integration, 'format_s_expression')
        except ImportError:
            pytest.skip("Rust module not compiled")
    
    def test_s_expression_formatting(self):
        """Test Rust S-expression formatting vs Python."""
        test_data = '(symbol "Device:R" (pin_numbers hide) (pin_names (offset 0)))'
        
        # Python implementation
        python_result = python_format_s_expression(test_data)
        
        # Rust implementation (if available)
        if RUST_AVAILABLE:
            rust_result = rust_kicad_integration.format_s_expression(test_data)
            
            # Results should be identical
            assert rust_result == python_result
            
            # Performance should be better
            python_time = benchmark_function(python_format_s_expression, test_data)
            rust_time = benchmark_function(rust_kicad_integration.format_s_expression, test_data)
            
            speedup = python_time / rust_time
            assert speedup > 2.0, f"Expected >2x speedup, got {speedup:.1f}x"
```

## 🔧 Testing Tools and Utilities

### Test Fixtures and Helpers

```python
# tests/conftest.py - Shared test fixtures
import pytest
from circuit_synth import Circuit, Component, Net

@pytest.fixture
def simple_circuit():
    """Create a simple test circuit."""
    circuit = Circuit("test_circuit")
    
    # Add basic components
    resistor = Component("Device:R", ref="R", value="1k")
    capacitor = Component("Device:C", ref="C", value="100nF")
    
    # Add nets
    vcc = Net("VCC")
    gnd = Net("GND")
    
    # Make connections
    resistor[1] += vcc
    resistor[2] += capacitor[1]
    capacitor[2] += gnd
    
    circuit.add_component(resistor)
    circuit.add_component(capacitor)
    
    return circuit

@pytest.fixture
def performance_test_components():
    """Create components for performance testing."""
    return [
        Component("Device:R", ref="R", value=f"{i}k")
        for i in range(1, 101)  # 100 resistors
    ]

# Custom assertions
def assert_circuit_equivalent(circuit1, circuit2):
    """Assert that two circuits are functionally equivalent."""
    assert len(circuit1.components) == len(circuit2.components)
    assert len(circuit1.nets) == len(circuit2.nets)
    
    # More detailed comparison...

def assert_performance_target(duration, target_ms, operation_name):
    """Assert performance meets target."""
    target_seconds = target_ms / 1000.0
    assert duration < target_seconds, \
        f"{operation_name} too slow: {duration:.3f}s (target: {target_seconds:.3f}s)"
```

### Performance Testing Utilities

```python
# tests/utils/performance.py
import time
import statistics
from contextlib import contextmanager

@contextmanager
def performance_timer():
    """Context manager for timing operations."""
    start = time.perf_counter()
    yield lambda: time.perf_counter() - start
    end = time.perf_counter()

def benchmark_function(func, *args, runs=10, **kwargs):
    """Benchmark a function with multiple runs."""
    times = []
    
    for _ in range(runs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        times.append(end - start)
    
    return {
        'mean': statistics.mean(times),
        'median': statistics.median(times),
        'min': min(times),
        'max': max(times),
        'std': statistics.stdev(times) if len(times) > 1 else 0,
        'runs': runs,
        'result': result
    }

# Usage example
def test_component_creation_performance():
    """Test component creation performance over multiple runs."""
    def create_component():
        return Component("Device:R", ref="R", value="1k")
    
    benchmark = benchmark_function(create_component, runs=1000)
    
    assert benchmark['mean'] < 0.001, f"Component creation too slow: {benchmark['mean']:.6f}s"
    assert benchmark['std'] < 0.0005, f"Performance too variable: {benchmark['std']:.6f}s"
```

## 📊 Continuous Integration Testing

### CI Pipeline Structure

```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  python-tests:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11, 3.12]
    
    steps:
    - uses: actions/checkout@v4
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install uv
        uv sync
    
    - name: Run tests
      run: ./scripts/run_all_tests.sh --python-only
  
  rust-tests:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Set up Rust
      uses: actions-rs/toolchain@v1
      with:
        toolchain: stable
    
    - name: Test Rust modules
      run: ./scripts/test_rust_modules.sh
  
  performance-regression:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Setup environment
      run: |
        pip install uv
        uv sync
    
    - name: Run performance benchmarks
      run: |
        uv run pytest tests/performance/ --benchmark-json=benchmark.json
    
    - name: Check performance regression
      run: |
        # Compare with baseline performance metrics
        python scripts/check_performance_regression.py benchmark.json
```

## 🎯 Testing Best Practices

### 1. Test Naming Conventions

```python
# Good test names (descriptive and specific)
def test_component_reference_assignment_increments_correctly():
    """Test that component references increment: R1, R2, R3, etc."""

def test_kicad_generation_handles_unicode_component_values():
    """Test KiCad generation with unicode characters in component values."""

def test_rust_acceleration_falls_back_gracefully_when_unavailable():
    """Test that missing Rust modules fall back to Python gracefully."""

# Bad test names (vague and unclear)
def test_component():  # Too vague
def test_stuff():      # Meaningless
def test_case_1():     # Uninformative
```

### 2. Test Structure (Arrange-Act-Assert)

```python
def test_circuit_netlist_export():
    """Test circuit netlist export functionality."""
    # ARRANGE: Set up test data
    circuit = Circuit("test")
    resistor = Component("Device:R", ref="R", value="1k")
    capacitor = Component("Device:C", ref="C", value="100nF")
    vcc_net = Net("VCC")
    
    resistor[1] += vcc_net
    capacitor[1] += vcc_net
    
    circuit.add_component(resistor)
    circuit.add_component(capacitor)
    
    # ACT: Perform the operation being tested
    netlist = circuit.export_netlist(format="kicad")
    
    # ASSERT: Verify expected results
    assert "VCC" in netlist
    assert "R1" in netlist
    assert "C1" in netlist
    assert "(net (code 1) (name VCC)" in netlist
```

### 3. Test Data Management

```python
# Use factories for test data
class ComponentFactory:
    @staticmethod
    def resistor(value="1k", ref="R"):
        return Component("Device:R", ref=ref, value=value)
    
    @staticmethod
    def capacitor(value="100nF", ref="C"):
        return Component("Device:C", ref=ref, value=value)
    
    @staticmethod
    def esp32():
        return Component(
            "RF_Module:ESP32-S3-MINI-1",
            ref="U",
            footprint="RF_Module:ESP32-S3-MINI-1"
        )

# Use in tests
def test_esp32_circuit():
    esp32 = ComponentFactory.esp32()
    vcc = Net("VCC_3V3")
    esp32["VDD"] += vcc
    # Test continues...
```

### 4. Error Testing

```python
def test_component_invalid_symbol_raises_error():
    """Test that invalid symbol names raise appropriate errors."""
    with pytest.raises(SymbolNotFoundError) as exc_info:
        Component("NonExistent:Symbol", ref="U")
    
    assert "NonExistent:Symbol" in str(exc_info.value)
    assert "not found in KiCad libraries" in str(exc_info.value)

def test_net_connection_validation():
    """Test that invalid net connections are caught."""
    resistor = Component("Device:R", ref="R")
    
    # Invalid pin number should raise error
    with pytest.raises(InvalidPinError):
        resistor[999] += Net("VCC")  # Pin 999 doesn't exist
    
    # Invalid pin name should raise error  
    with pytest.raises(InvalidPinError):
        resistor["NonExistentPin"] += Net("VCC")
```

## 🚀 Running Tests Effectively

### Development Workflow

```bash
# 1. Run tests frequently during development
uv run pytest tests/unit/test_core_circuit.py -v

# 2. Run specific test methods
uv run pytest tests/unit/test_core_circuit.py::TestCircuit::test_component_addition -v

# 3. Run tests with coverage
uv run pytest --cov=circuit_synth tests/unit/ --cov-report=html

# 4. Run performance tests
uv run pytest tests/performance/ --benchmark-only

# 5. Run everything before PR
./scripts/run_all_tests.sh --verbose
```

### Debugging Failed Tests

```bash
# Run with detailed output
uv run pytest tests/unit/test_core_circuit.py -vv -s

# Drop into debugger on failure
uv run pytest tests/unit/test_core_circuit.py --pdb

# Run only failed tests from last run
uv run pytest --lf

# Show local variables in traceback
uv run pytest tests/unit/test_core_circuit.py -l
```

---

**Following these testing guidelines ensures circuit-synth maintains high quality while enabling rapid development. Every contribution should include comprehensive tests!** 🧪✅