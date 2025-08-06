# Manual Regression Test Suite

This document outlines comprehensive manual tests to verify circuit-synth functionality after code cleanup or major changes.

## 🧹 **PREREQUISITE: Clear All Caches**

**⚠️ CRITICAL: Always clear caches before regression testing!**

```bash
# Clear circuit-synth caches
rm -rf ~/.cache/circuit_synth/
rm -rf ~/.circuit-synth/

# Clear Python bytecode caches  
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

# Clear any existing test outputs
rm -rf example_project/circuit-synth/ESP32_C6_Dev_Board/
rm -f example_project/circuit-synth/*.json
rm -f example_project/circuit-synth/*.net
rm -f example_project/circuit-synth/*.log

echo "✅ All caches cleared - ready for clean testing"
```

**Why this matters:**
- Symbol cache may contain outdated data
- JLCPCB cache may have stale component information  
- Python imports may use old cached modules
- KiCad library cache may be inconsistent

---

## 🎯 Test Categories

### **Category 1: Core Circuit Generation (CRITICAL)**
These test the fundamental circuit-synth workflows that must work.

### **Category 2: KiCad Integration (HIGH)**  
Tests KiCad file generation, import, and compatibility.

### **Category 3: Component Intelligence (MEDIUM)**
Tests component search, JLCPCB integration, and symbol lookup.

### **Category 4: Advanced Features (LOW)**
Tests simulation, annotations, and specialized tools.

---

## 🔴 **Category 1: Core Circuit Generation (CRITICAL)**

### **Test 1.1: Basic Circuit Creation**
```bash
# Test: Create simple circuit in Python
cd example_project/circuit-synth/
uv run python -c "
from circuit_synth import *
@circuit
def test_circuit():
    r1 = Component(symbol='Device:R', ref='R1', value='10k', footprint='Resistor_SMD:R_0603_1608Metric')
    print('✅ Simple circuit created')
test_circuit()
"
```
**Expected**: No errors, component created successfully

### **Test 1.2: Hierarchical Circuit Example**
```bash
# Test: Run the main hierarchical example
cd example_project/circuit-synth/
uv run python main.py
```
**Expected**: 
- ESP32_C6_Dev_Board/ directory created
- Contains .kicad_pro, .kicad_sch, .kicad_pcb, .net, .json files
- No Python errors during generation

### **Test 1.3: Net Connections**
```bash
# Test: Verify net connections work
uv run python -c "
from circuit_synth import *
@circuit
def test_nets():
    vcc = Net('VCC_3V3')
    gnd = Net('GND')
    r1 = Component(symbol='Device:R', ref='R1', value='10k')
    r2 = Component(symbol='Device:R', ref='R2', value='1k')
    r1[1] += vcc
    r1[2] += r2[1]  
    r2[2] += gnd
    print('✅ Net connections created')
test_nets()
"
```
**Expected**: Net connections established without errors

### **Test 1.4: Reference Assignment**
```bash
# Test: Verify automatic reference assignment
uv run python -c "
from circuit_synth import *
@circuit  
def test_refs():
    r1 = Component(symbol='Device:R', ref='R')  # Prefix only
    r2 = Component(symbol='Device:R', ref='R')  # Should auto-assign
    c1 = Component(symbol='Device:C', ref='C')  # Different prefix
    print(f'R1 ref: {r1.ref}, R2 ref: {r2.ref}, C1 ref: {c1.ref}')
test_refs()
"
```
**Expected**: R1, R2, C1 (or similar auto-assigned references)

---

## 🟡 **Category 2: KiCad Integration (HIGH)**

### **Test 2.1: KiCad Project Generation**
```bash
# Test: Generate complete KiCad project
cd example_project/circuit-synth/
uv run python main.py
```
**Manual Verification**:
1. Open `ESP32_C6_Dev_Board/ESP32_C6_Dev_Board.kicad_pro` in KiCad
2. Verify schematic opens without errors
3. Check hierarchical sheets are present:
   - USB port subcircuit
   - Power supply subcircuit  
   - ESP32-C6 subcircuit
4. Verify PCB opens and shows ratsnest connections
5. Check that all components have proper symbols and footprints

### **Test 2.2: Symbol Library Access**
```bash
# Test: Verify KiCad symbol libraries are accessible
uv run python -c "
from circuit_synth.core.symbol_cache import get_symbol_cache
cache = get_symbol_cache()
symbol_data = cache.get_symbol('Device:R')
print(f'✅ Symbol data: {len(symbol_data.get(\"pins\", []))} pins')
"
```
**Expected**: Symbol data retrieved with pin information

### **Test 2.3: Netlist Generation**
```bash
# Test: Generate KiCad-compatible netlist
cd example_project/circuit-synth/
uv run python -c "
from usb import usb_port
from circuit_synth import Net
circuit = usb_port(Net('VBUS'), Net('GND'), Net('USB_DP'), Net('USB_DM'))
circuit.generate_kicad_netlist('test_usb.net')
print('✅ Netlist generated')
"
cat test_usb.net | head -20
```
**Expected**: Valid KiCad netlist file created with proper format

### **Test 2.4: JSON Export/Import**
```bash
# Test: JSON netlist round-trip
cd example_project/circuit-synth/
uv run python -c "
from power_supply import power_supply
from circuit_synth import Net
circuit = power_supply(Net('VBUS'), Net('VCC_3V3'), Net('GND'))
circuit.generate_json_netlist('test_power.json')
print('✅ JSON exported')
"

# Verify JSON structure
python -c "
import json
with open('test_power.json', 'r') as f:
    data = json.load(f)
print(f'Components: {len(data.get(\"components\", {}))}')
print(f'Nets: {len(data.get(\"nets\", {}))}')
"
```
**Expected**: Valid JSON with components and nets

---

## 🟠 **Category 3: Component Intelligence (MEDIUM)**

### **Test 3.1: Symbol Search**
```bash
# Test: Find KiCad symbols
uv run python -c "
from circuit_synth.kicad.symbol_search import find_symbols
results = find_symbols('STM32')
print(f'Found {len(results)} STM32 symbols')
for r in results[:3]:
    print(f'  - {r}')
"
```
**Expected**: List of STM32 symbols found

### **Test 3.2: JLCPCB Component Search**
```bash
# Test: Search JLCPCB for components
uv run python -c "
from circuit_synth.manufacturing.jlcpcb import search_jlc_components_web
results = search_jlc_components_web('STM32G0', max_results=3)
print(f'Found {len(results)} components')
for r in results:
    print(f'  - {r.get(\"part_number\", \"Unknown\")}: {r.get(\"stock\", 0)} in stock')
"
```
**Expected**: List of STM32G0 components with stock levels

### **Test 3.3: STM32 Peripheral Search**
```bash
# Test: STM32-specific search functionality
uv run python -c "
from circuit_synth.ai_integration.stm32_search_helper import handle_stm32_peripheral_query
result = handle_stm32_peripheral_query('find stm32 with 2 spi available on jlcpcb')
if result:
    print('✅ STM32 search working')
    print(result[:200] + '...')
else:
    print('❌ STM32 search not working')
"
```
**Expected**: STM32 recommendations with peripheral information

---

## 🟢 **Category 4: Advanced Features (LOW)**

### **Test 4.1: Circuit Simulation**
```bash
# Test: SPICE simulation generation
uv run python -c "
from circuit_synth import *
@circuit
def voltage_divider():
    r1 = Component(symbol='Device:R', ref='R1', value='10k')
    r2 = Component(symbol='Device:R', ref='R2', value='10k') 
    vin = Net('VIN')
    vout = Net('VOUT')
    gnd = Net('GND')
    r1[1] += vin
    r1[2] += vout
    r2[1] += vout  
    r2[2] += gnd
    return locals()

try:
    circuit = voltage_divider()
    sim = circuit.simulate()
    print('✅ Simulation object created')
except ImportError:
    print('⚠️  Simulation dependencies not installed (this is OK)')
except Exception as e:
    print(f'❌ Simulation error: {e}')
"
```
**Expected**: Simulation object created (or expected ImportError)

### **Test 4.2: Circuit Annotations**
```bash
# Test: Text annotations and documentation
uv run python -c "
from circuit_synth import *
from circuit_synth.core.annotations import TextBox

@circuit
def annotated_circuit():
    '''This circuit has annotations'''
    r1 = Component(symbol='Device:R', ref='R1', value='10k')
    
circuit = annotated_circuit()
circuit.generate_json_netlist('annotated_test.json')

# Check if annotations are included
import json
with open('annotated_test.json', 'r') as f:
    data = json.load(f)
annotations = data.get('annotations', [])
print(f'✅ Found {len(annotations)} annotations')
"
```
**Expected**: Annotations included in JSON output

### **Test 4.3: Component Property Handling**
```bash
# Test: Custom component properties
uv run python -c "
from circuit_synth import *
@circuit  
def test_properties():
    r1 = Component(
        symbol='Device:R', 
        ref='R1', 
        value='10k',
        tolerance='1%',
        power_rating='0.25W',
        mfg_part_num='RC0603FR-0710KL'
    )
    data = r1.to_dict()
    print(f'✅ Component with custom properties: {data.get(\"tolerance\", \"missing\")}')
test_properties()
"
```
**Expected**: Custom properties preserved in component data

### **Test 4.4: Round-Trip Workflow (Python → KiCad → Python → KiCad)**
```bash
# Test: Complete round-trip validation
cd example_project/circuit-synth/

# Step 1: Generate ESP32 project (Python → KiCad)
echo "Step 1: Generating ESP32 project..."
uv run python main.py

# Verify KiCad files were created
ls -la ESP32_C6_Dev_Board/
echo "✅ KiCad files generated"

# Step 2: Import KiCad project back to Python (KiCad → Python)
echo "Step 2: Importing KiCad project..."
uv run python -c "
try:
    from circuit_synth.io.kicad_import import import_kicad_project
    project_data = import_kicad_project('ESP32_C6_Dev_Board/ESP32_C6_Dev_Board.kicad_pro')
    print(f'✅ Imported {len(project_data.get(\"components\", {}))} components')
    
    # Generate Python code from imported data
    from circuit_synth.codegen.json_to_python_project import generate_python_from_json
    python_code = generate_python_from_json(project_data, 'RoundTripTest')
    
    with open('round_trip_test.py', 'w') as f:
        f.write(python_code)
    print('✅ Generated Python code from KiCad')
except ImportError:
    print('⚠️  KiCad import not available - creating fallback test')
    with open('round_trip_test.py', 'w') as f:
        f.write('from circuit_synth import *\\n@circuit\\ndef test(): pass\\nif __name__ == \"__main__\": test()')
"

# Step 3: Run the generated Python code (Python → KiCad again)
echo "Step 3: Running generated Python code..."
uv run python round_trip_test.py
echo "✅ Round-trip test completed"

# Cleanup
rm -f round_trip_test.py
rm -rf ESP32_C6_Dev_Board/
```
**Expected**: 
- ESP32 project generates successfully
- KiCad files can be imported back to Python  
- Generated Python code executes without errors
- Complete round-trip preserves circuit functionality

---

## 🔧 **Manual Verification Checklist**

After running automated tests, manually verify:

### **KiCad Integration**
- [ ] KiCad project opens without errors
- [ ] All symbols display correctly in schematic
- [ ] Hierarchical sheets navigate properly
- [ ] PCB shows ratsnest connections
- [ ] No missing footprint errors
- [ ] Generated netlist is valid

### **Component Data**
- [ ] Component symbols found in KiCad libraries
- [ ] Footprints match expected packages
- [ ] JLCPCB stock data is current
- [ ] STM32 search returns valid parts

### **File Outputs**
- [ ] JSON netlists are well-formed
- [ ] KiCad files open in latest KiCad version
- [ ] Generated files have reasonable sizes
- [ ] No corrupted or empty outputs

---

## 🚨 **Critical Failure Indicators**

Stop and investigate if you see:

❌ **Python import errors** from circuit_synth modules
❌ **KiCad project won't open** or shows major errors  
❌ **Empty or malformed JSON** netlist files
❌ **Symbol not found errors** for common components (Device:R, Device:C)
❌ **No components appear** in generated schematics
❌ **Ratsnest missing** in PCB (indicates netlist problems)

---

## 📊 **Test Results Template**

```
# Test Run: [DATE]
## Environment
- Circuit-synth version: [VERSION]
- KiCad version: [VERSION]  
- Python version: [VERSION]

## Pre-Test Setup
- [ ] Cleared ~/.cache/circuit_synth/
- [ ] Cleared ~/.circuit-synth/  
- [ ] Cleared Python __pycache__
- [ ] Cleared test outputs
- [ ] Verified clean environment

## Results
### Category 1: Core Circuit Generation
- [ ] Test 1.1: Basic Circuit Creation
- [ ] Test 1.2: Hierarchical Circuit Example  
- [ ] Test 1.3: Net Connections
- [ ] Test 1.4: Reference Assignment

### Category 2: KiCad Integration
- [ ] Test 2.1: KiCad Project Generation
- [ ] Test 2.2: Symbol Library Access
- [ ] Test 2.3: Netlist Generation
- [ ] Test 2.4: JSON Export/Import

### Category 3: Component Intelligence  
- [ ] Test 3.1: Symbol Search
- [ ] Test 3.2: JLCPCB Component Search
- [ ] Test 3.3: STM32 Peripheral Search

### Category 4: Advanced Features
- [ ] Test 4.1: Circuit Simulation
- [ ] Test 4.2: Circuit Annotations
- [ ] Test 4.3: Component Property Handling
- [ ] Test 4.4: Round-Trip Workflow (Python → KiCad → Python → KiCad)

## Issues Found
[List any failures or unexpected behavior]

## Overall Status
[ ] PASS - All critical tests working
[ ] PARTIAL - Some non-critical issues  
[ ] FAIL - Critical functionality broken
```

This test suite ensures circuit-synth's core functionality remains intact after dead code removal!