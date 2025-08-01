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

### Root Cause: Flat vs Hierarchical Structure Mismatch

The issue stems from a fundamental mismatch between how components are initially generated and how they're organized in the final schematic:

1. **Initial PCB Generation**: Components created with flat structure
   - Nets: `VCC_3V3`, `GND`, `USB_DP`, etc.
   - Components reference flat sheet structure

2. **Schematic Structure**: Circuit-synth generates hierarchical schematics
   - Subcircuits in separate sheets: `USB_Port.kicad_sch`, `Power_Supply.kicad_sch`
   - Hierarchical net naming: `/ESP32_C6_Dev_Board_Main/VCC_3V3`
   - Components belong to specific hierarchical sheets

3. **Update Conflict**: When F8 updates PCB from schematic
   - KiCad sees completely different component organization
   - Forces complete replacement to match hierarchical structure
   - All nets get hierarchical prefixes
   - All components get new sheet associations

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

## Potential Solutions

### 1. Consistent Structure Generation
Ensure PCB and schematic use the same organizational structure from initial generation:
- Generate PCB with hierarchical component references from start
- Match net naming conventions between PCB and schematic generation

### 2. Improved Netlist Handling
- Detect hierarchical vs flat structure mismatches
- Provide warnings before major component replacements
- Offer migration options for existing flat PCBs

### 3. Documentation Improvements
- Clear warnings about F8 behavior with circuit-synth projects
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