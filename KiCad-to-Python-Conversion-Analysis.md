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

The 2 directories should match exactly. We need to keep debugging the code until we can do this round trip exercise of Python -> Kicad -> Python perfectly.

### **Debugging Tips**
1. **Add debug logs** during development - comment them out when done
2. **Use descriptive logging** for key decision points in the conversion logic
3. **Test hierarchical detection** - ensure main circuit with subcircuits is found correctly
4. **Verify file generation** - check all subcircuit files are created with proper imports

## Current State Assessment - UPDATED 🚧

### ✅ **Major Progress Made:**

1. **Recursive Subcircuit Detection (FIXED)**:
   - ✅ All 6 subcircuits now generated (usb_port, power_supply, esp32_c6_mcu, debug_header, led_blinker)
   - ✅ Hierarchical parsing works for nested subcircuits
   - ✅ No hardcoded logic - handles arbitrary circuit structures

2. **Generated Structure** (Current):
   ```
   ESP32_C6_Dev_Board/circuit-synth/
   ├── main.py              # ✅ All imports and calls
   ├── usb_port.py          # ✅ Generated
   ├── power_supply.py      # ✅ Generated  
   ├── esp32_c6_mcu.py      # ✅ Generated
   ├── debug_header.py      # ✅ Now working!
   └── led_blinker.py       # ✅ Now working!
   ```

### 🚧 **Current Issues Identified:**

1. **Incorrect Hierarchical Structure**:
   - ❌ `debug_header` and `led_blinker` should be **subcircuits of esp32**, not top-level
   - ❌ Currently treating all as top-level subcircuits in main.py
   - ❌ Need to nest them inside esp32_c6_mcu.py instead

2. **Component Reference Issues**:
   - ❌ Components created as `c4 = Component(...)` but missing `ref="C4"`
   - ❌ We know the reference from parsing but not setting it properly
   - ❌ Need to map parsed component reference to ref parameter

3. **Net Naming Problems**:
   - ❌ Illegal net names like `_esp32_c6_dev_board_main_esp32_c6_mcu_n$3`
   - ❌ Creating unconnected nets that serve no purpose
   - ❌ Need to clean up net names and only create connected nets

4. **Implementation Quality**:
   - ❌ Still TODO placeholders instead of actual component connections
   - ❌ Missing actual netlist connections between components

## 🎯 **Next Action Plan (Priority Order):**

### **Phase 1: Fix Hierarchical Structure** 
- **Issue**: debug_header and led_blinker should be subcircuits **within** esp32_c6_mcu, not top-level
- **Action**: Modify hierarchy detection to only generate top-level sheets as separate files
- **Expected**: Only 3 files (main.py, usb_port.py, power_supply.py, esp32_c6_mcu.py)
- **Expected**: esp32_c6_mcu.py internally calls debug_header and led_blinker functions

### **Phase 2: Fix Component References**
- **Issue**: Components like `c4 = Component(...)` missing `ref="C4"`
- **Action**: Extract component reference from parsed data and set ref parameter
- **Expected**: `c4 = Component(..., ref="C4")`

### **Phase 3: Clean Up Net Names**
- **Issue**: Illegal names like `_esp32_c6_dev_board_main_esp32_c6_mcu_n$3`
- **Action**: Sanitize net names, remove invalid characters, only create connected nets
- **Expected**: Clean names like `vcc_3v3`, `gnd`, `usb_dp`

### **Phase 4: Add Real Connections**
- **Issue**: TODO placeholders instead of actual connections
- **Action**: Parse netlist connections and generate actual pin assignments
- **Expected**: `component["pin"] += net` instead of TODO comments

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