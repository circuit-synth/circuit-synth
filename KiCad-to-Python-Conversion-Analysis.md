# KiCad-to-Python Conversion Feature Analysis

## 🔧 Testing & Debugging Instructions

### **Essential Test Commands** 
**ONLY run these 2 commands when testing, from the top-level 'circuit-synth' directory:**

```bash
# 1. Generate example KiCad project (creates ESP32_C6_Dev_Board/)
uv run example_project/circuit-synth/main.py

# 2. Test conversion (converts KiCad → circuit-synth)
uv run cs-init-existing-project ESP32_C6_Dev_Board/
```

**IMPORTANT:** Remove ESP32_C6_Dev_Board directory between tests:
```bash
rm -rf ESP32_C6_Dev_Board
```

### **Expected Output Comparison**
After conversion, compare these directories:
- **Generated:** `/Users/shanemattner/Desktop/circuit-synth/ESP32_C6_Dev_Board/circuit-synth/` 
- **Target:** `/Users/shanemattner/Desktop/circuit-synth/example_project/circuit-synth/`

**Target structure (what we want to match):**
```
example_project/circuit-synth/
├── main.py                    # Main hierarchical circuit
├── usb_subcircuit.py         # USB-C port subcircuit  
├── power_supply_subcircuit.py # Power regulation subcircuit
├── debug_header_subcircuit.py # Debug header subcircuit
├── led_blinker_subcircuit.py  # LED blinker subcircuit
├── simple_led.py             # Simple examples
└── voltage_divider.py        # Simple examples
```

### **Debugging Tips**
1. **Add debug logs** during development - comment them out when done
2. **Use descriptive logging** for key decision points in the conversion logic
3. **Test hierarchical detection** - ensure main circuit with subcircuits is found correctly
4. **Verify file generation** - check all subcircuit files are created with proper imports

## Current State Assessment

### Existing Conversion Code

#### ✅ **We Have:**

1. **Main Conversion Pipeline** (`/src/circuit_synth/tools/init_existing_project.py`)
   - `convert_kicad_to_circuit_synth()` function
   - `generate_circuit_synth_code()` function 
   - Basic template fallback when conversion fails
   - Integration with `cs-init-existing-project` command

2. **KiCad Parsing Infrastructure**
   - `KiCadNetlistParser` in `/src/circuit_synth/kicad/netlist_importer.py`
   - `CircuitSynthParser` for converting netlist to Circuit-Synth JSON
   - `SExpressionParser` for parsing KiCad S-expressions
   - Multiple parser classes for different KiCad file types

3. **Synchronization Tools**
   - `KiCadToPythonSyncer` in `/src/circuit_synth/tools/kicad_to_python_sync.py`
   - `PythonCircuitParser` for parsing existing Python code
   - LLM-assisted code merging capabilities

4. **Supporting Infrastructure**
   - Component and Net models
   - Symbol and footprint caching
   - KiCad project validation

#### ❌ **Current Issues:**

1. **Conversion Error**: `'Component' object has no attribute 'ref'`
   - The current conversion logic has a bug accessing component references
   - Code tries to access `component.ref` but the attribute doesn't exist or is named differently

2. **Incomplete Hierarchical Support**
   - Current code doesn't properly handle hierarchical subcircuits
   - Missing logic to detect and recreate subcircuit imports

3. **Basic Template Only**
   - When conversion fails, falls back to a very basic template
   - Doesn't leverage the rich circuit structure from the netlist

## Target: Match Example Project Structure

### Expected Output Structure

The goal is to match `/Users/shanemattner/Desktop/circuit-synth/example_project/circuit-synth/`:

```
circuit-synth/
├── main.py                    # Main hierarchical circuit
├── usb_subcircuit.py         # USB-C port subcircuit  
├── power_supply_subcircuit.py # Power regulation subcircuit
├── debug_header_subcircuit.py # Debug interface subcircuit
├── led_blinker_subcircuit.py  # LED status subcircuit
├── simple_led.py             # Basic examples
└── voltage_divider.py        # Basic examples
```

### Key Features Needed

1. **Hierarchical Circuit Detection**
   - Parse KiCad hierarchical sheets
   - Identify subcircuits and their interfaces
   - Generate separate Python files for each subcircuit

2. **Component Mapping**
   - Map KiCad components to circuit-synth Component objects
   - Handle symbol/footprint translation
   - Preserve component values and properties

3. **Net Analysis**
   - Identify inter-subcircuit nets (like VCC_3V3, GND, USB_DP)
   - Map pin connections correctly
   - Handle hierarchical net names

4. **Code Generation**
   - Generate proper circuit-synth syntax
   - Include correct imports between subcircuits
   - Add meaningful docstrings and comments

## Technical Implementation Plan

### Phase 1: Fix Current Conversion Bug

**Issue**: `'Component' object has no attribute 'ref'`

**Investigation Needed**:
- Check what attributes are actually available on parsed Component objects
- Fix the attribute access in `generate_circuit_synth_code()`
- Ensure proper error handling

### Phase 2: Enhance Basic Conversion

**Goals**:
- Generate working single-file circuit-synth code
- Proper component creation with correct symbols/footprints
- Complete net connections (not just TODO comments)

**Components**:
- Fix component reference extraction
- Add proper net connection generation
- Improve symbol/footprint mapping

### Phase 3: Hierarchical Support

**Goals**:
- Detect KiCad hierarchical sheets
- Generate multiple Python files for subcircuits
- Create proper import structure

**Components**:
- Sheet hierarchy parser
- Subcircuit interface analysis
- Multi-file code generation

### Phase 4: Advanced Features

**Goals**:
- Match example project structure exactly
- Include basic examples alongside main circuit
- Proper documentation generation

## Questions for Clarification

1. **Hierarchical Priority**: Should we focus first on fixing the basic single-file conversion, or jump straight to hierarchical support?

2. **Testing Strategy**: Would you prefer to test incrementally (fix basic conversion first) or build the full hierarchical system?

3. **Error Handling**: When hierarchical sheets aren't detected, should we fall back to single-file generation or basic template?

4. **Component Library**: How should we handle cases where KiCad symbols don't have direct circuit-synth equivalents?

5. **Validation**: Should the converted code be validated by actually running it and comparing the generated KiCad output?

## Next Steps

**Immediate Action Items**:

1. **Debug the current conversion error** - investigate the Component attribute issue
2. **Examine the netlist parsing** - ensure we're getting proper component data  
3. **Test with the ESP32_C6_Dev_Board** - use it as a concrete test case
4. **Compare outputs** - analyze differences between expected and actual results

**Proposed Approach**:
1. Fix the immediate bug to get basic conversion working
2. Test with ESP32_C6_Dev_Board project  
3. Incrementally add hierarchical support
4. Validate against example_project output

## Test Cases

**Primary Test**: 
```bash
# Generate reference
uv run example_project/circuit-synth/main.py 

# Test conversion  
uv run cs-init-existing-project ESP32_C6_Dev_Board/

# Compare outputs
diff -r example_project/circuit-synth/ ESP32_C6_Dev_Board/circuit-synth/
```

**Success Criteria**:
- No conversion errors
- Generated code runs without errors
- Output structure matches example_project
- Generated KiCad files are equivalent