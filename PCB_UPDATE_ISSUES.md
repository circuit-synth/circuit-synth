# PCB Update Issues with Circuit-Synth Generated Projects

## Issue Summary

When updating a PCB from a circuit-synth generated schematic in KiCad, all components are being replaced rather than performing a minimal update. This occurs even when the netlist hasn't changed, resulting in complete component replacement and potential loss of manual PCB layout work.

## Test Case Details

### Setup
- **Project Generation**: Used stock `cs-new-project` command to create default ESP32-C6 project
- **Circuit-Synth Version**: Latest from repository (as of 2025-08-01)
- **KiCad Version**: 8.0+ (macOS installation)
- **Test Project**: `my_circuit_project/ESP32_C6_Dev_Board/`

### Testing Method
1. Generated fresh project with `uv run cs-new-project`
2. Ran `uv run python circuit-synth/main.py` to create KiCad project
3. Opened generated PCB in KiCad (`ESP32_C6_Dev_Board.kicad_pcb`)
4. Verified schematic and PCB looked correct initially
5. Attempted to update PCB from schematic using **F8** (Update PCB from Schematic)
6. Observed complete component replacement instead of minimal update

### Expected vs Actual Behavior

**Expected:**
- Minimal changes when updating PCB from unchanged schematic
- Components retain their existing positions and properties
- Only actual schematic changes reflected in PCB

**Actual:**
- **All components completely replaced** with new UUIDs
- **All nets renamed** with hierarchical prefixes
- Complete reorganization of component associations
- Loss of any manual PCB placement work

## Technical Analysis

### Root Cause: Architectural Inconsistency Between Generation Components

**DETAILED ROOT CAUSE ANALYSIS (2025-08-01 Investigation):**

The issue is a **fundamental architectural inconsistency** within circuit-synth's generation pipeline. The problem occurs because different components of the generation system create incompatible organizational structures:

#### **The Problem Flow:**

1. **Circuit-Synth Python Code**: Defines hierarchical subcircuits (`usb_port_subcircuit()`, `power_supply_subcircuit()`, etc.)

2. **JSON Generation**: Creates hierarchical circuit structure in temporary JSON file

3. **Schematic Generation**: `SchematicGenerator.generate_project()` creates hierarchical KiCad schematics with:
   - `/ESP32_C6_Dev_Board_Main/` (main sheet)
   - `/ESP32_C6_Dev_Board_Main/USB_Port/` (USB subcircuit sheet) 
   - `/ESP32_C6_Dev_Board_Main/Power_Supply/` (power subcircuit sheet)
   - Components properly assigned to hierarchical sheets

4. **Netlist Generation**: `circuit.generate_kicad_netlist()` creates **FLAT** netlist with:
   - Net names: `VCC_3V3`, `GND`, `USB_DP` (no hierarchy prefixes)
   - Component sheet paths: `(sheetpath (names "/") (tstamps "/"))` (flat structure)

5. **PCB Generation**: `PCBGenerator._apply_netlist_to_pcb()` reads the flat netlist and creates PCB with flat structure

6. **F8 Update Conflict**: When user presses F8 in KiCad:
   - KiCad reads the hierarchical schematic structure
   - Expects hierarchical nets: `/ESP32_C6_Dev_Board_Main/VCC_3V3`
   - PCB has flat nets: `VCC_3V3`
   - **Complete mismatch → Replace all components**

#### **Critical Code Locations:**

**The fundamental flaw is in `src/circuit_synth/core/netlist_exporter.py`:**
- Line 34: `(sheetpath (names "/") (tstamps "/"))` - **Forces flat structure**
- Netlist always generates flat sheet paths regardless of hierarchical circuit definition

**Secondary issue in `src/circuit_synth/kicad/pcb_gen/pcb_generator.py`:**
- Lines 766-813: Attempts to "flatten" hierarchical nets from schematic
- Lines 772-813: Dynamic net merging logic that tries to reconcile hierarchical/flat mismatch
- This flattening logic creates the inconsistency that causes F8 conflicts

#### **Evidence Comparison:**

**Circuit-Synth Generated Netlist (Flat):**
```
(net (code "4") (name "VCC_3V3")
(sheetpath (names "/") (tstamps "/"))
```

**KiCad Hierarchical Reference Netlist (After F8):**
```
(net (code "5") (name "/ESP32_C6_Dev_Board_Main/VCC_3V3")
(sheetpath (names "/ESP32_C6_Dev_Board_Main/") (tstamps "/57232bfa-1bd4-40ca-b3b3-06d16c6c299c/"))
```

The netlist exporter generates flat structures while the schematic generator creates hierarchical structures, causing the F8 update to see completely different organizational structures.

### Evidence from KiCad Report

```
Updated C3 sheetname to '/ESP32_C6_Dev_Board_Main/Power_Supply/'.
Updated C3 sheetfile to 'Power_Supply.kicad_sch'.
Reconnected C3 pin 1 from VCC_3V3_OUT to /ESP32_C6_Dev_Board_Main/VCC_3V3_OUT.

Updated J1 sheetname to '/ESP32_C6_Dev_Board_Main/USB_Port/'.
Updated J1 sheetfile to 'USB_Port.kicad_sch'.

Removed unused net VCC_3V3.
Removed unused net GND.
Add net /ESP32_C6_Dev_Board_Main/VCC_3V3.
Add net /ESP32_C6_Dev_Board_Main/GND.
```

## Impact on Workflow

### User Experience Issues
- **Lost Manual Work**: Any manual component placement, routing, or PCB optimizations are lost
- **Unexpected Behavior**: Users expect F8 to perform minimal updates
- **Design Iteration Problems**: Makes iterative PCB design difficult
- **Professional Workflow Disruption**: Incompatible with standard KiCad practices

### Manufacturing Impact
- **Component Position Changes**: May affect automated assembly programs
- **Trace Routing Reset**: Manual routing work needs to be redone
- **Design Review Overhead**: Need to re-verify entire PCB layout

## Solution Architecture

### **Primary Solution: Hierarchical Consistency**

**PROGRESS UPDATE (2025-08-01): Partially Fixed - Multi-Stage Pipeline Issue Identified**

The fix requires ensuring both netlist and PCB generation preserve the same hierarchical structure that schematic generation creates.

#### **Required Code Changes:**

**✅ COMPLETED:**
1. **`src/circuit_synth/kicad/netlist_service.py`**:
   - **FIXED**: `CircuitReconstructor.reconstruct_circuit()` now preserves hierarchical structure
   - **Previously**: Created single `temp_netlist_` circuit flattening all components
   - **Now**: Maintains hierarchical subcircuits and proper circuit structure
   - **Verification**: First stage now shows components getting correct sheet paths (`/USB_Port/`, `/Power_Supply/`, etc.)

**🚧 IN PROGRESS:**
2. **Multi-Stage Pipeline Issue Discovered**:
   - **Problem**: Additional flattening step occurs during KiCad project generation
   - **Evidence**: Second circuit `ESP32_C6_Dev_Board` created with 0 subcircuits and 14 flattened components
   - **Root Cause Identified**: `PCBGenerator._extract_components_from_schematics()` in `src/circuit_synth/kicad/pcb_gen/pcb_generator.py:455`
   - **Issue**: PCB generator bypasses hierarchical Circuit structure and reads components directly from `.kicad_sch` files
   - **Impact**: Our CircuitReconstructor fix works for netlist generation, but PCB generation uses a completely different code path
   - **Current Behavior**: Creates flat hierarchical paths like `/USB_Port` instead of proper `/ESP32_C6_Dev_Board_Main/USB_Port/`

**🔄 REMAINING FIXES:**
3. **`src/circuit_synth/core/netlist_exporter.py`**:
   - **CRITICAL**: Replace flat sheet path generation with hierarchical sheet path extraction
   - Extract actual sheet hierarchy from circuit JSON structure
   - Generate proper `(sheetpath (names "/ESP32_C6_Dev_Board_Main/Power_Supply/") (tstamps "..."))` entries

4. **`src/circuit_synth/kicad/pcb_gen/pcb_generator.py`**:
   - **Remove flattening logic** (lines 766-813) that tries to merge hierarchical nets
   - Preserve hierarchical net names from netlist as-is
   - Update net assignment to match hierarchical component references

5. **`src/circuit_synth/kicad/sch_gen/main_generator.py`**:
   - Identify and fix the secondary flattening step that occurs during KiCad project generation
   - Ensure UUID consistency between schematic and netlist generation
   - Pass hierarchical structure information to netlist generation

#### **Implementation Strategy:**

**Phase 1: Fix Netlist Generation**
- Modify netlist exporter to extract hierarchical sheet information from circuit JSON
- Generate netlist with proper hierarchical sheet paths and net names
- Ensure component UUIDs and sheet references match schematic structure

**Phase 2: Update PCB Generation**  
- Remove net flattening logic from PCB generator
- Update PCB to use hierarchical net names directly from netlist
- Test F8 updates show minimal changes

**Phase 3: Validation**
- Test with stock cs-new-project workflow
- Verify F8 updates are minimal with hierarchical consistency
- Validate manual PCB layout preservation

### **Alternative Solutions (Lower Priority)**

#### **1. Migration Utilities**
- Detect hierarchical vs flat structure mismatches
- Provide warnings before major component replacements  
- Offer migration options for existing flat PCBs

#### **2. Documentation Improvements**
- Clear warnings about F8 behavior with current circuit-synth projects
- Recommended workflows for PCB updates
- Migration guides for existing projects

## Reproduction Steps

```bash
# 1. Create fresh project
uv init test_project
cd test_project
uv add circuit-synth

# 2. Generate template
uv run cs-new-project

# 3. Generate KiCad project
uv run python circuit-synth/main.py

# 4. Open in KiCad
open ESP32_C6_Dev_Board/ESP32_C6_Dev_Board.kicad_pro

# 5. Open PCB editor, press F8
# 6. Observe complete component replacement
```

## Test Environment

- **OS**: macOS (Darwin 24.5.0)
- **Circuit-Synth**: Repository version (develop branch, commit c00e015)
- **KiCad**: 8.0+ (Homebrew installation)
- **Python**: Via uv package manager
- **Test Date**: 2025-08-01

## Related Files

- Test project: `my_circuit_project/ESP32_C6_Dev_Board/`
- KiCad update report: `my_circuit_project/ESP32_C6_Dev_Board/report.txt`
- Generation logs: Console output from `main.py` execution
- Circuit definition: `my_circuit_project/circuit-synth/main.py`

## Priority

**High** - This affects the core workflow integration between circuit-synth and KiCad, potentially blocking adoption for professional PCB design workflows where manual layout optimization is required.