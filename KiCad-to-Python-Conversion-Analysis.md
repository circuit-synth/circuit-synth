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

### ✅ **Partial Progress Made:**

1. **Basic File Generation Working**:
   - ✅ 4 out of 6 target files are generated successfully
   - ✅ Main circuit structure is detected and processed
   - ✅ Basic hierarchical parsing is functional

2. **Generated Structure** (Current Reality):
   ```
   ESP32_C6_Dev_Board/circuit-synth/
   ├── main.py              # ✅ Generated
   ├── esp32_c6_mcu.py      # ✅ Generated (naming mismatch)
   ├── power_supply.py      # ✅ Generated
   └── usb_port.py          # ✅ Generated (naming mismatch)
   ```

### 🚧 **Critical Issues Identified:**

1. **Missing Files**:
   - ❌ `debug_header.py` not generated (expected in target structure)
   - ❌ `led_blinker.py` not generated (expected in target structure)
   - ❌ Only 4 files generated instead of expected 6

2. **File Naming Mismatches**:
   - ❌ Generated: `esp32_c6_mcu.py` → Expected: `esp32c6.py`
   - ❌ Generated: `usb_port.py` → Expected: `usb.py`
   - ❌ Inconsistent naming convention between generated and target files

3. **Component Reference Issues**:
   - ❌ Components created as `c4 = Component(...)` but missing `ref="C4"`
   - ❌ We know the reference from parsing but not setting it properly
   - ❌ Need to map parsed component reference to ref parameter

4. **Net Naming Problems**:
   - ❌ Illegal net names like `_esp32_c6_dev_board_main_esp32_c6_mcu_n$3`
   - ❌ Creating unconnected nets that serve no purpose
   - ❌ Need to clean up net names and only create connected nets

5. **Implementation Quality**:
   - ❌ Still TODO placeholders instead of actual component connections
   - ❌ Missing actual netlist connections between components

## 🎯 **Next Action Plan (Priority Order):**

### **Phase 1: Fix Missing File Generation**
- **Issue**: Only 4/6 files generated - missing debug_header.py and led_blinker.py
- **Action**: Debug hierarchical sheet detection to ensure all subcircuits are found
- **Expected**: All 6 files generated (main.py, esp32c6.py, power_supply.py, usb.py, debug_header.py, led_blinker.py)

### **Phase 2: Fix File Naming Consistency**
- **Issue**: Generated file names don't match target structure
- **Action**: Update naming logic to match target: esp32_c6_mcu.py → esp32c6.py, usb_port.py → usb.py
- **Expected**: File names match exactly between generated and target directories

### **Phase 3: Fix Component References**
- **Issue**: Components like `c4 = Component(...)` missing `ref="C4"`
- **Action**: Extract component reference from parsed data and set ref parameter
- **Expected**: `c4 = Component(..., ref="C4")`

### **Phase 4: Clean Up Net Names**
- **Issue**: Illegal names like `_esp32_c6_dev_board_main_esp32_c6_mcu_n$3`
- **Action**: Sanitize net names, remove invalid characters, only create connected nets
- **Expected**: Clean names like `vcc_3v3`, `gnd`, `usb_dp`

### **Phase 5: Add Real Connections**
- **Issue**: TODO placeholders instead of actual connections
- **Action**: Parse netlist connections and generate actual pin assignments
- **Expected**: `component["pin"] += net` instead of TODO comments

## Target: Match Example Project Structure

### Expected Output Structure

The goal is to match `/Users/shanemattner/Desktop/circuit-synth/example_project/circuit-synth/`:

```
circuit-synth/
├── main.py              # Main hierarchical circuit
├── esp32c6.py          # ESP32-C6 microcontroller subcircuit
├── power_supply.py     # Power regulation subcircuit
├── usb.py              # USB-C port subcircuit
├── debug_header.py     # Debug interface subcircuit
└── led_blinker.py      # LED status subcircuit
```

### Actual Test Results vs Expected

**Current Generated Files (4/6):**
```
ESP32_C6_Dev_Board/circuit-synth/
├── main.py              # ✅ Generated
├── esp32_c6_mcu.py      # ❌ Wrong name (should be esp32c6.py)
├── power_supply.py      # ✅ Correct
└── usb_port.py          # ❌ Wrong name (should be usb.py)
```

**Missing Files (2/6):**
- ❌ `debug_header.py` - Not generated
- ❌ `led_blinker.py` - Not generated

**File Naming Issues:**
- Generated: `esp32_c6_mcu.py` → Expected: `esp32c6.py`
- Generated: `usb_port.py` → Expected: `usb.py`

**Success Rate:** 2/6 files match exactly (33% accuracy)

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

### Phase 1: Fix Missing File Generation

**Issue**: Only 4/6 target files are generated

**Investigation Needed**:
- Debug hierarchical sheet detection logic
- Ensure all subcircuits (debug_header, led_blinker) are properly identified
- Check if subcircuits are being filtered out incorrectly

### Phase 2: Fix File Naming Consistency

**Issue**: Generated file names don't match target structure

**Investigation Needed**:
- Update naming logic: esp32_c6_mcu.py → esp32c6.py
- Update naming logic: usb_port.py → usb.py
- Ensure consistent naming convention throughout

### Phase 3: Fix Component Reference Issues

**Issue**: `'Component' object has no attribute 'ref'`

**Investigation Needed**:
- Check what attributes are actually available on parsed Component objects
- Fix the attribute access in `generate_circuit_synth_code()`
- Ensure proper error handling

### Phase 4: Enhance Basic Conversion

**Goals**:
- Complete net connections (not just TODO comments)
- Proper component creation with correct symbols/footprints
- Clean up illegal net names

**Components**:
- Fix component reference extraction
- Add proper net connection generation
- Improve symbol/footprint mapping
- Sanitize net names

### Phase 5: Advanced Features

**Goals**:
- Match example project structure exactly (100% accuracy vs current 33%)
- Proper documentation generation
- Validation of generated code

## Critical Findings Summary

**Current Conversion Accuracy: 33% (2/6 files match exactly)**

### Immediate Blockers:
1. **Missing Files**: debug_header.py and led_blinker.py not generated
2. **Naming Mismatches**: esp32_c6_mcu.py vs esp32c6.py, usb_port.py vs usb.py
3. **Component Reference Errors**: Missing ref attributes causing runtime issues

### Root Cause Analysis Needed:
1. **Hierarchical Detection**: Why are only 4/6 subcircuits being detected?
2. **Naming Logic**: What controls the generated file names vs target names?
3. **Component Parsing**: What attributes are actually available on Component objects?

## Next Steps

**Immediate Action Items (Priority Order)**:

1. **Debug missing file generation** - investigate why debug_header and led_blinker subcircuits aren't detected
2. **Fix file naming consistency** - update naming logic to match target structure exactly
3. **Fix component reference errors** - investigate Component attribute access issues
4. **Test round-trip conversion** - ensure Python → KiCad → Python works perfectly

**Success Criteria**:
- All 6 files generated with correct names
- No runtime errors during conversion
- 100% structural match with example_project
- Clean, readable generated code

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

## 🔄 **Improved KiCad-to-Python Conversion Workflow**

### **New Streamlined Process:**

When someone runs `cs-init-existing-project`, the system should:

1. **Find KiCad Project File**
   - Locate the `.kicad_pro` file in the target directory
   - Extract project name and configuration

2. **Identify Top-Level Schematic**
   - Parse the `.kicad_pro` file's "sheets" section
   - Find the sheet with empty string ("") as name = TOP-LEVEL SHEET
   - Example from ESP32_C6_Dev_Board.kicad_pro:
     ```json
     "sheets": [
       [
         "ddf0d8a4-793f-4906-9d56-c254b619c467",
         ""  ← Empty string = TOP-LEVEL SHEET
       ],
       [
         "b5de37ab-1e1c-4462-8eeb-c648bdebd287",
         "ESP32_C6_Dev_Board_Main"  ← Hierarchical sheet
       ]
     ]
     ```

3. **Generate Complete Netlist**
   - Use `kicad-cli` to generate netlist from top-level schematic:
     ```bash
     kicad-cli sch export netlist /path/to/project/TopLevel.kicad_sch
     ```
   - This captures ALL components from ALL hierarchical sheets in one netlist

4. **Extract Hierarchical Structure from Netlist**
   - Parse netlist to identify all sheets and their components
   - Use `sheetpath` information to group components by hierarchical sheet:
     - `(sheetpath (names "/USB_Port/") (tstamps "/USB_Port/"))`
     - `(sheetpath (names "/ESP32_C6_MCU/Debug_Header/") (tstamps "/ESP32_C6_MCU/Debug_Header/"))`
   - Create hierarchical JSON structure with proper sheet relationships

5. **Generate Circuit-Synth Python Project**
   - Convert hierarchical JSON to individual Python files
   - Create proper imports between subcircuits
   - Generate clean, readable circuit-synth code

### **Key Advantages:**
- ✅ **Single Source of Truth**: One netlist contains everything
- ✅ **No Missing Components**: All hierarchical sheets included automatically
- ✅ **Proper Sheet Detection**: Uses netlist's built-in hierarchical information
- ✅ **Simplified Logic**: No need to parse individual schematic files
- ✅ **Robust**: Works with any KiCad hierarchical project structure

### **Implementation Status:**
- ✅ Netlist generation working (existing `generate_netlist()` method)
- 🚧 **IN PROGRESS**: Hierarchical structure extraction from netlist
- ⏳ Helper methods needed: `_extract_sheet_info_from_netlist()`, `_get_component_sheet_path()`, `_convert_sheet_path_to_name()`
- ⏳ Fallback method: `_analyze_hierarchical_structure_from_schematics()`