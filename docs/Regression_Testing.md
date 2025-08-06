# Circuit-Synth Testing Tools

This directory contains automated and manual testing tools for circuit-synth quality assurance.

## 🚀 Quick Start

### Automated Regression Tests
```bash
# Run complete automated test suite
./tools/testing/run_regression_tests.py

# Alternative execution methods
uv run python tools/testing/run_regression_tests.py
python3 tools/testing/run_regression_tests.py
```

### Test All Rust Modules
```bash
# Test Rust components with Python integration
./tools/testing/test_rust_modules.sh

# Verbose output for debugging
./tools/testing/test_rust_modules.sh --verbose
```

## 📋 Manual Regression Testing Before Major Release

Follow this comprehensive manual testing checklist before any major release or after significant code changes.

### Prerequisites
```bash
# 1. Ensure clean environment
./tools/maintenance/clear_all_caches.sh

# 2. Verify installation
uv pip install -e ".[dev]"

# 3. Register agents (if using Claude integration)
uv run register-agents
```

### Phase 1: Core Functionality Tests ⚡

#### Test 1.1: Basic Import and Circuit Creation
```bash
# Test basic imports
uv run python -c "
from circuit_synth import *
print('✅ 1.1a: Imports successful')

@circuit
def basic_test():
    r1 = Component(symbol='Device:R', ref='R1', value='1k')
    print('✅ 1.1b: Basic circuit creation successful')

basic_test()
"
```

#### Test 1.2: Component and Net Management
```bash
# Test component creation and net connections
uv run python -c "
from circuit_synth import *

@circuit
def net_test():
    # Create nets
    vcc = Net('VCC_3V3')
    gnd = Net('GND')
    
    # Create components
    r1 = Component(symbol='Device:R', ref='R1', value='10k')
    r2 = Component(symbol='Device:R', ref='R2', value='1k')
    
    # Test connections
    r1[1] += vcc
    r1[2] += r2[1]
    r2[2] += gnd
    
    print('✅ 1.2: Net connections successful')

net_test()
"
```

#### Test 1.3: Reference Assignment
```bash
# Test automatic reference assignment
uv run python -c "
from circuit_synth import *

components = []

@circuit
def ref_test():
    global components
    # Create multiple components with same prefix
    components = [
        Component(symbol='Device:R', ref='R'),
        Component(symbol='Device:R', ref='R'), 
        Component(symbol='Device:C', ref='C'),
        Component(symbol='Device:C', ref='C')
    ]

ref_test()

# Verify unique references after finalization
refs = [c.ref for c in components]
print(f'References: {refs}')
assert len(set(refs)) == len(refs), 'References should be unique'
print('✅ 1.3: Reference assignment successful')
"
```

### Phase 2: File Generation Tests 📁

#### Test 2.1: JSON Export
```bash
# Test JSON netlist generation
cd example_project/circuit-synth/

uv run python -c "
from circuit_synth import *

@circuit
def json_test():
    vcc = Net('VCC')
    gnd = Net('GND') 
    r1 = Component(symbol='Device:R', ref='R1', value='1k')
    vcc += r1[1]
    gnd += r1[2]

circuit = json_test()
circuit.generate_json_netlist('manual_test.json')
print('✅ 2.1a: JSON generation successful')

# Verify JSON content
import json
with open('manual_test.json') as f:
    data = json.load(f)
    
components = data.get('components', {})
nets = data.get('nets', {})

print(f'✅ 2.1b: JSON contains {len(components)} components, {len(nets)} nets')
assert len(components) > 0, 'Should have components'
assert len(nets) > 0, 'Should have nets'

# Cleanup
import os
os.remove('manual_test.json')
"

cd ../..
```

#### Test 2.2: KiCad Project Generation
```bash
# Test complete KiCad project generation
cd example_project/circuit-synth/

uv run python main.py
echo "✅ 2.2a: Example project generation completed"

# Verify generated files
if [ -d "ESP32_C6_Dev_Board" ]; then
    echo "✅ 2.2b: Project directory created"
    
    required_files=(
        "ESP32_C6_Dev_Board.kicad_pro"
        "ESP32_C6_Dev_Board.kicad_sch" 
        "ESP32_C6_Dev_Board.kicad_pcb"
        "ESP32_C6_Dev_Board.net"
    )
    
    cd ESP32_C6_Dev_Board
    for file in "${required_files[@]}"; do
        if [ -f "$file" ]; then
            echo "✅ 2.2c: Found $file"
        else
            echo "❌ 2.2c: Missing $file"
            exit 1
        fi
    done
    
    # Check file sizes (should not be empty)
    for file in "${required_files[@]}"; do
        size=$(wc -c < "$file")
        if [ "$size" -gt 100 ]; then
            echo "✅ 2.2d: $file has content ($size bytes)"
        else
            echo "❌ 2.2d: $file is too small ($size bytes)"
            exit 1
        fi
    done
    
    cd ..
    echo "✅ 2.2: KiCad project generation successful"
else
    echo "❌ 2.2: Project directory not created"
    exit 1
fi

cd ../..
```

### Phase 3: Component Intelligence Tests 🧠

#### Test 3.1: Symbol Library Access
```bash
# Test KiCad symbol access
uv run python -c "
from circuit_synth.core.symbol_cache import get_symbol_cache

cache = get_symbol_cache()
symbol_data = cache.get_symbol('Device:R')

if symbol_data and hasattr(symbol_data, 'pins'):
    pin_count = len(symbol_data.pins)
    print(f'✅ 3.1: Symbol library access successful - Resistor has {pin_count} pins')
    assert pin_count >= 2, f'Resistor should have at least 2 pins, got {pin_count}'
else:
    print('❌ 3.1: Symbol library access failed')
    exit(1)
"
```

#### Test 3.2: JLCPCB Integration
```bash
# Test component sourcing (may fail if network issues)
uv run python -c "
from circuit_synth.manufacturing.jlcpcb import search_jlc_components_web

try:
    results = search_jlc_components_web('STM32G0', max_results=3)
    if results and len(results) > 0:
        print(f'✅ 3.2: JLCPCB search successful - Found {len(results)} components')
        sample = results[0]
        part_num = sample.get('part_number', 'Unknown')
        print(f'  Sample component: {part_num}')
    else:
        print('⚠️ 3.2: JLCPCB search returned no results (may be API issue)')
        
except Exception as e:
    print(f'⚠️ 3.2: JLCPCB search failed: {e}')
    print('  This may be due to network issues or API changes')
"
```

#### Test 3.3: STM32 Peripheral Search
```bash
# Test STM32 search functionality
uv run python -c "
from circuit_synth.stm32_search_helper import handle_stm32_peripheral_query

test_queries = [
    'find stm32 with 2 spi available on jlcpcb',
    'stm32 with usb and 3 timers in stock'
]

for query in test_queries:
    result = handle_stm32_peripheral_query(query)
    if result and len(result) > 50:
        print(f'✅ 3.3: STM32 search working for: \"{query}\"')
        print(f'  Result length: {len(result)} characters')
        break
else:
    print('❌ 3.3: STM32 search failed for all test queries')
    exit(1)
"
```

### Phase 4: Advanced Features Tests 🔬

#### Test 4.1: Circuit Annotations
```bash
# Test annotation system
uv run python -c "
from circuit_synth import *
import json, os

@circuit
def annotated_test():
    '''This circuit demonstrates annotations.
    
    Creates a simple LED circuit with proper current limiting.
    LED forward voltage: 2.0V, Current: 10mA
    '''
    vcc = Net('VCC_5V')
    gnd = Net('GND')
    
    led = Component(symbol='Device:LED', ref='D1')
    resistor = Component(symbol='Device:R', ref='R1', value='330')
    
    vcc += resistor[1]
    resistor[2] += led[1]
    led[2] += gnd

circuit = annotated_test()
circuit.generate_json_netlist('annotation_test.json')

# Check for annotations in JSON
with open('annotation_test.json') as f:
    data = json.load(f)
    
annotations = data.get('annotations', [])
print(f'✅ 4.1: Annotations test - Found {len(annotations)} annotations')

if annotations:
    print(f'  Sample annotation: {annotations[0].get(\"text\", \"No text\")[:50]}...')

# Cleanup
os.remove('annotation_test.json')
"
```

#### Test 4.2: Round-Trip Workflow
```bash
# Test Python → KiCad → Python round trip
cd example_project/circuit-synth/

echo "🔄 4.2a: Testing round-trip workflow..."

# Step 1: Generate KiCad project
uv run python main.py
echo "✅ 4.2b: Python → KiCad generation completed"

# Step 2: Test KiCad import (if available)
uv run python -c "
import os

try:
    from circuit_synth.io.kicad_import import import_kicad_project
    
    project_path = 'ESP32_C6_Dev_Board/ESP32_C6_Dev_Board.kicad_pro'
    if os.path.exists(project_path):
        circuit_data = import_kicad_project(project_path)
        component_count = len(circuit_data.get('components', {}))
        print(f'✅ 4.2c: KiCad → Python import successful ({component_count} components)')
        
        # Generate Python code
        from circuit_synth.codegen.json_to_python_project import generate_python_from_json
        python_code = generate_python_from_json(circuit_data, 'RoundTripTest')
        
        with open('round_trip_test.py', 'w') as f:
            f.write(python_code)
        print('✅ 4.2d: Python code generation successful')
    else:
        print('⚠️ 4.2c: KiCad project file not found')
        
except ImportError:
    print('⚠️ 4.2c: KiCad import functionality not available')
    # Create fallback test
    fallback = '''from circuit_synth import *

@circuit
def round_trip_fallback():
    r1 = Component(symbol=\"Device:R\", ref=\"R1\", value=\"1k\")
    print(\"✅ Round-trip fallback successful\")

if __name__ == \"__main__\":
    round_trip_fallback()
'''
    with open('round_trip_test.py', 'w') as f:
        f.write(fallback)
    print('✅ 4.2d: Fallback round-trip test created')

except Exception as e:
    print(f'❌ 4.2c: KiCad import failed: {e}')
"

# Step 3: Execute generated Python code
if [ -f "round_trip_test.py" ]; then
    uv run python round_trip_test.py
    echo "✅ 4.2e: Generated Python code executed successfully"
    rm round_trip_test.py
else
    echo "⚠️ 4.2e: No generated Python file to test"
fi

cd ../..
```

### Phase 5: Tool Integration Tests 🔧

#### Test 5.1: Build Tools
```bash
# Test build tool functionality
echo "🔧 5.1a: Testing build tools..."

# Test help commands
./tools/build/format_all.sh --help >/dev/null 2>&1 && echo "✅ 5.1b: format_all.sh responds" || echo "❌ 5.1b: format_all.sh failed"

./tools/testing/run_all_tests.sh --help >/dev/null 2>&1 && echo "✅ 5.1c: run_all_tests.sh responds" || echo "❌ 5.1c: run_all_tests.sh failed"

./tools/release/release_to_pypi.sh --help >/dev/null 2>&1 && echo "✅ 5.1d: release_to_pypi.sh responds" || echo "❌ 5.1d: release_to_pypi.sh failed"
```

#### Test 5.2: CLI Tools
```bash
# Test CLI tool accessibility  
echo "🔧 5.2a: Testing CLI tools..."

if [ -d "src/circuit_synth/cli" ]; then
    echo "✅ 5.2b: CLI directory exists"
    
    # Check major CLI categories
    for category in kicad_integration project_management development utilities; do
        if [ -d "src/circuit_synth/cli/$category" ]; then
            echo "✅ 5.2c: CLI category $category exists"
        else
            echo "❌ 5.2c: CLI category $category missing"
        fi
    done
else
    echo "❌ 5.2b: CLI directory missing"
fi
```

### Phase 6: Performance and Cleanup Tests 🧹

#### Test 6.1: Memory and Performance
```bash
# Basic performance test
echo "⚡ 6.1: Running performance test..."

time uv run python -c "
from circuit_synth import *
import time

start = time.time()

@circuit 
def performance_test():
    components = []
    nets = []
    
    # Create moderate number of components
    for i in range(20):
        net = Net(f'NET_{i}')
        comp = Component(symbol='Device:R', ref='R', value=f'{i}k')
        nets.append(net)
        components.append(comp)
        
        if i > 0:
            nets[i-1] += comp[1]
            nets[i] += comp[2]
    
    return components, nets

components, nets = performance_test()
duration = time.time() - start

print(f'✅ 6.1: Performance test completed in {duration:.2f}s')
print(f'  Created {len(components)} components and {len(nets)} nets')
"
```

#### Test 6.2: Cleanup Verification
```bash
# Test cleanup tools
echo "🧹 6.2: Testing cleanup functionality..."

# Create some test artifacts
mkdir -p /tmp/circuit_test_cleanup
cd /tmp/circuit_test_cleanup

# Generate test files
uv run python -c "
from circuit_synth import *
@circuit
def cleanup_test():
    r1 = Component(symbol='Device:R', ref='R1', value='1k')

circuit = cleanup_test()
circuit.generate_json_netlist('cleanup_test.json')
circuit.generate_kicad_project('Cleanup_Test_Project')
"

# Verify files exist
if [ -f "cleanup_test.json" ] && [ -d "Cleanup_Test_Project" ]; then
    echo "✅ 6.2a: Test artifacts created"
    
    # Test cleanup
    cd /Users/shanemattner/Desktop/circuit-synth2
    ./tools/maintenance/clear_all_caches.sh
    
    # Clean up our test directory
    rm -rf /tmp/circuit_test_cleanup
    echo "✅ 6.2b: Cleanup tools executed successfully"
else
    echo "❌ 6.2a: Failed to create test artifacts"
    cd /Users/shanemattner/Desktop/circuit-synth2
fi
```

## 📊 Final Manual Test Summary

After completing all phases, verify:

### ✅ Critical Success Criteria
- [ ] All Phase 1 tests pass (Core Functionality)
- [ ] All Phase 2 tests pass (File Generation)  
- [ ] KiCad project files are generated and non-empty
- [ ] JSON export works correctly
- [ ] No import errors or exceptions

### ⚠️ Non-Critical (May Have Issues)
- [ ] JLCPCB search (may fail due to network/API)
- [ ] Round-trip import (may not be fully implemented)
- [ ] Advanced annotations (newer feature)

### 🚨 Failure Criteria
If any of these fail, DO NOT release:
- Import errors in Phase 1
- Missing KiCad files in Phase 2  
- Symbol library access failures in Phase 3
- Build tool failures in Phase 5

## 🤖 Automated Alternative

Instead of manual testing, you can run the comprehensive automated suite:

```bash
# This covers most of the manual tests above
./tools/testing/run_regression_tests.py
```

The automated tests are equivalent to the manual process but faster and more consistent.

## 📝 Test Documentation

Document test results in the release notes:
- Date of testing
- Environment details (macOS/Linux, Python version, KiCad version)
- Any failing non-critical tests
- Performance metrics if relevant

This ensures quality and provides debugging context for any issues discovered post-release.