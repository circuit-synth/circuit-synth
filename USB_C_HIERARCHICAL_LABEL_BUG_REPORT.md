# USB-C Hierarchical Net Label Bug Report

## Problem Summary

USB-C connectors in circuit-synth are only generating **5 hierarchical net labels instead of the expected 7**. Specifically, the D+ and D- differential pair pins are each receiving only 1 label instead of 2, despite USB-C connectors having duplicate pins (A6/B6 for D+ and A7/B7 for D-) to support cable flipping functionality.

**Current Output:** 2 GND + 1 VBUS_OUT + 1 USB_DM + 1 USB_DP = **5 labels**  
**Expected Output:** 2 GND + 1 VBUS_OUT + 2 USB_DM + 2 USB_DP = **7 labels**

This issue prevents proper hierarchical net connectivity for USB-C differential pairs, potentially causing signal integrity problems and incomplete PCB routing.

## Technical Background

### USB-C Pin Structure

USB-C connectors implement cable flipping support through duplicate pins:

- **D+ (USB Data Plus)**: Pins A6 and B6
- **D- (USB Data Minus)**: Pins A7 and B7  
- **VBUS (Power)**: Pins A4, A9, B4, B9 (typically connected together)
- **GND (Ground)**: Pins A1, A12, B1, B12 (typically connected together)

### Expected vs Actual Behavior

**Expected Hierarchical Labels:**
- `/USB_Port/GND` (2 labels - one for each GND pin group)
- `/USB_Port/VBUS_OUT` (1 label - VBUS pins connected together)
- `/USB_Port/USB_DP` (2 labels - one for A6, one for B6)
- `/USB_Port/USB_DM` (2 labels - one for A7, one for B7)

**Actual Hierarchical Labels:**
- `/USB_Port/GND` (2 labels - ✅ Working correctly)
- `/USB_Port/VBUS_OUT` (1 label - ✅ Working correctly)  
- `/USB_Port/USB_DP` (1 label - ❌ Missing second label)
- `/USB_Port/USB_DM` (1 label - ❌ Missing second label)

## Root Cause Analysis

### Confirmed Root Cause: Pin Name-Based Deduplication Logic

After running the USB subcircuit test case, the issue has been **confirmed and identified**. The problem is **NOT** position-based deduplication, but rather **pin name-based deduplication logic** that prevents multiple hierarchical labels for pins with the same name.

**Evidence from Generated Schematic:**
- **GND**: 2 hierarchical labels generated ✅ (pins A1, A12, B1, B12 all have name "GND")
- **VBUS_OUT**: 1 hierarchical label generated ✅ (pins A4, A9, B4, B9 all have name "VBUS")
- **USB_DM**: 1 hierarchical label generated ❌ (pins A7, B7 both have name "D-" - **only 1 label created**)
- **USB_DP**: 1 hierarchical label generated ❌ (pins A6, B6 both have name "D+" - **only 1 label created**)

**USB-C Pin Analysis from Symbol Definition:**
- **A6 pin**: name="D+", number="A6" (lines 684-705 in generated schematic)
- **B6 pin**: name="D+", number="B6" (lines 706-727 in generated schematic)
- **A7 pin**: name="D-", number="A7" (lines 640-661 in generated schematic)
- **B7 pin**: name="D-", number="B7" (lines 662-683 in generated schematic)

### Root Cause Location

The deduplication logic exists somewhere in the label generation pipeline that prevents multiple hierarchical labels from being created for pins that share the same **pin name** (not position). This logic incorrectly assumes that pins with the same name should only get one label, but USB-C differential pairs legitimately need separate labels for each physical pin to support proper hierarchical connectivity.

**Key Finding**: GND and VBUS work correctly (multiple labels generated), but D+ and D- fail (single label generated), indicating the issue is specifically with how the system handles multiple pins with identical names in differential pair scenarios.

### Evidence from Log Analysis

Based on the task description, the logging shows:
- Only **5 labels generated** instead of expected **7**
- Missing labels specifically for USB differential pairs (D+/D-)
- Other nets (GND, VBUS_OUT) working correctly

## Investigation Status: STILL UNRESOLVED

**Status**: ❌ **UNRESOLVED** - Despite multiple fix attempts, the issue persists
**Last Updated**: 2025-08-02
**Issue Duration**: Multiple investigation cycles

### Work Completed

The following fixes have been attempted and **FAILED** to resolve the issue:

1. **✅ Position-Based Deduplication Fix**: Modified [`schematic_writer.py`](src/circuit_synth/kicad/sch_gen/schematic_writer.py) to use position-based deduplication instead of pin name-based
   - **Result**: ❌ Failed - Issue persisted
   - **Evidence**: ESP32_C6_Dev_Board still shows only 2 hierarchical labels instead of 4

2. **✅ Pin-Number-Based Deduplication**: Enhanced deduplication logic to use pin numbers for unique identification
   - **Result**: ❌ Failed - Issue persisted
   - **Evidence**: USB differential pairs still missing second labels

3. **✅ USB Circuit Template Updates**: Modified USB circuit templates in [`new_project.py`](src/circuit_synth/tools/new_project.py)
   - **Result**: ❌ Failed - Issue persisted
   - **Evidence**: Template changes did not affect hierarchical label generation

4. **✅ Special Handling for USB Differential Pairs**: Added specific logic for USB_DP and USB_DM nets
   - **Result**: ❌ Failed - Issue persisted
   - **Evidence**: Differential pair detection did not resolve missing labels

5. **✅ Enhanced Debug Logging**: Added comprehensive logging to track label generation process
   - **Result**: ✅ Successful for debugging - Confirmed issue location but did not fix
   - **Evidence**: Logs show correct pin assignments but missing schematic labels

6. **✅ Multiple Verification Attempts**: Tested across different USB-C circuits and configurations
   - **Result**: ❌ Failed - Issue consistent across all USB-C implementations
   - **Evidence**: All USB-C circuits show same missing label pattern

### Current Evidence of Unresolved Issue

**Latest Test Results (ESP32_C6_Dev_Board)**:
- **Expected**: 4 hierarchical labels for USB differential pairs (2 for USB_DM, 2 for USB_DP)
- **Actual**: 2 hierarchical labels total (1 for USB_DM, 1 for USB_DP)
- **Missing**: 2 hierarchical labels for second set of differential pair pins

**PCB Log Evidence**:
```
PCB logs show correct pin assignments:
- USB_DM connected to pins A7, B7
- USB_DP connected to pins A6, B6
```

**Schematic Evidence**:
- Visual inspection confirms only 1 label per differential pair net
- Missing labels for B6 (USB_DP) and B7 (USB_DM) pins
- Issue persists across all generated USB-C schematics

### Failed Approaches Summary

| Approach | Files Modified | Result | Reason for Failure |
|----------|---------------|--------|-------------------|
| Position-based deduplication | `schematic_writer.py` | ❌ Failed | Root cause not position-related |
| Pin-number-based deduplication | `schematic_writer.py` | ❌ Failed | Deduplication logic not the core issue |
| USB template updates | `new_project.py` | ❌ Failed | Templates don't control label generation |
| Differential pair special handling | `schematic_writer.py` | ❌ Failed | Issue occurs before differential pair detection |
| Enhanced logging | Multiple files | ✅ Debug only | Identified issue location but no fix |

### Root Cause Status

**Current Understanding**: The root cause has **NOT** been properly identified despite multiple investigation attempts. The issue appears to be deeper in the label generation pipeline than initially suspected.

**Key Findings**:
- Issue is NOT related to position-based deduplication
- Issue is NOT related to pin-number-based deduplication
- Issue is NOT related to USB circuit templates
- Issue persists despite multiple targeted fixes
- **The actual root cause remains unknown**

### Current Investigation Focus

- **🔍 CRITICAL**: Identify the actual root cause of missing hierarchical labels
- **🔍 Deep Pipeline Analysis**: Investigate earlier stages of label generation process
- **🔍 Symbol Processing**: Examine how USB-C symbol pins are processed before label creation
- **🔍 Net Processing**: Analyze net-to-pin mapping logic for differential pairs

## Debugging Steps

### 1. Locate Pin Name Deduplication Logic
```bash
# Search for deduplication logic that might be based on pin names
grep -r "pin.*name.*duplicate\|duplicate.*pin.*name" src/
grep -r "same.*name\|identical.*name" src/circuit_synth/kicad/sch_gen/
```

### 2. Add Debug Logging to Label Generation
```python
# Add to _add_pin_level_net_labels() method in schematic_writer.py
logger.debug(f"Processing pin {pin_identifier} (name: {pin_dict.get('name')}, number: {pin_dict.get('number')}) for net {net_name}")
logger.debug(f"Position key: {position_key}, already processed: {position_key in net_positions}")
```

### 3. Trace Label Creation for D+ and D- Pins
```bash
# Run with verbose logging to see label creation process
cd usb_port && PYTHONPATH=/Users/shanemattner/Desktop/circuit-synth3/src uv run python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
exec(open('../usb_subcircuit.py').read())
" 2>&1 | grep -E "(USB_DP|USB_DM|D\+|D-)"
```

### 4. Examine Generated vs Expected Labels
```python
# Count hierarchical labels in generated schematic
with open('usb_port/usb_port/USB_Port.kicad_sch', 'r') as f:
    content = f.read()
    labels = content.count('hierarchical_label')
    usb_dp_labels = content.count('hierarchical_label\n\t\tUSB_DP')
    usb_dm_labels = content.count('hierarchical_label\n\t\tUSB_DM')
    print(f"Total labels: {labels}, USB_DP: {usb_dp_labels}, USB_DM: {usb_dm_labels}")
```

## Potential Solutions

### Solution 1: Pin-Number Based Deduplication (Recommended)
**Approach**: Modify the deduplication logic to use pin number instead of pin name.

```python
# Current (problematic): Deduplication based on pin name
# Proposed: Deduplication based on component reference + pin number
position_key = (comp_ref, pin_number)  # Unique per physical pin
```

**Pros**:
- Ensures each physical pin gets its own hierarchical label
- Preserves differential pair connectivity (A6/B6 for D+, A7/B7 for D-)
- More semantically correct for electrical connectivity
- Maintains existing position-based logic while fixing the core issue

**Cons**:
- May generate more labels than current implementation
- Requires identifying where pin name-based deduplication occurs

### Solution 2: Disable Deduplication for Differential Pairs
**Approach**: Add special handling for differential pair nets to bypass deduplication.

```python
# Add differential pair detection
DIFFERENTIAL_PAIR_NETS = ["USB_DP", "USB_DM", "CAN_H", "CAN_L", "LVDS_P", "LVDS_N"]
if net_name in DIFFERENTIAL_PAIR_NETS:
    # Force creation of labels for all pins, regardless of name duplication
    create_label_for_each_pin = True
```

**Pros**:
- Targeted fix for known problematic net types
- Preserves existing behavior for other nets
- Easy to extend for other differential pair types

**Cons**:
- Requires maintaining list of differential pair net names
- May miss custom differential pair naming conventions
- Doesn't address root cause of the deduplication logic

### Solution 3: Enhanced Pin Identity Logic
**Approach**: Improve pin identification to distinguish between pins with same name but different numbers.

```python
# Create unique pin identity combining name, number, and position
pin_identity = {
    'component_ref': comp_ref,
    'pin_name': pin_name,
    'pin_number': pin_number,
    'position': (global_x, global_y)
}
# Use this comprehensive identity for deduplication instead of just pin name
```

**Pros**:
- Most comprehensive solution addressing multiple identification methods
- Handles edge cases with complex pin naming
- Future-proof for other connector types

**Cons**:
- More complex implementation
- May require significant refactoring of existing deduplication logic
- Higher computational overhead

## Files to Investigate

### Primary Files
- [`src/circuit_synth/kicad/sch_gen/schematic_writer.py`](src/circuit_synth/kicad/sch_gen/schematic_writer.py) - Contains `_add_pin_level_net_labels()` method
- [`example_project/circuit-synth/usb_subcircuit.py`](example_project/circuit-synth/usb_subcircuit.py) - Test case for USB-C connector

### Supporting Files
- [`src/circuit_synth/core/component.py`](src/circuit_synth/core/component.py) - SymbolLibCache for pin data
- [`src/circuit_synth/kicad/kicad_symbol_cache.py`](src/circuit_synth/kicad/kicad_symbol_cache.py) - Python symbol cache fallback
- USB-C symbol library file - Contains actual pin coordinate definitions

### Related Architecture Files
- [`src/circuit_synth/kicad_api/core/types.py`](src/circuit_synth/kicad_api/core/types.py) - Label and Point type definitions
- [`src/circuit_synth/kicad_api/schematic/component_manager.py`](src/circuit_synth/kicad_api/schematic/component_manager.py) - Component lookup functionality

## Testing Plan

### 1. Unit Test for Position Calculation
```python
def test_usb_c_pin_positions():
    """Test that USB-C D+/D- pins get unique positions"""
    # Create USB-C component
    # Calculate positions for A6, B6, A7, B7 pins
    # Assert positions are unique
    pass
```

### 2. Integration Test for Label Generation
```python
def test_usb_c_hierarchical_labels():
    """Test that USB-C generates 7 hierarchical labels"""
    circuit = usb_port_subcircuit()
    writer = SchematicWriter(circuit)
    writer._add_pin_level_net_labels()
    
    # Count labels by net
    label_counts = {}
    for label in writer.schematic.labels:
        label_counts[label.text] = label_counts.get(label.text, 0) + 1
    
    assert label_counts["USB_DP"] == 2, f"Expected 2 USB_DP labels, got {label_counts.get('USB_DP', 0)}"
    assert label_counts["USB_DM"] == 2, f"Expected 2 USB_DM labels, got {label_counts.get('USB_DM', 0)}"
```

### 3. End-to-End Test
```bash
# Generate USB subcircuit and verify KiCad output
cd example_project/circuit-synth
python usb_subcircuit.py
# Open generated .kicad_sch file
# Count hierarchical labels manually
# Verify PCB netlist has correct connectivity
```

## Success Criteria

### Exact Expected Output
When generating hierarchical labels for USB-C subcircuit, the system should create:

1. **GND net**: 2 hierarchical labels (one for each GND pin group)
2. **VBUS_OUT net**: 1 hierarchical label (VBUS pins connected together)
3. **USB_DP net**: 2 hierarchical labels (one for A6 pin, one for B6 pin)
4. **USB_DM net**: 2 hierarchical labels (one for A7 pin, one for B7 pin)

**Total**: 7 hierarchical labels

### Verification Methods
1. **Log Output**: Debug logs show 7 labels created with correct net names
2. **KiCad Schematic**: Visual inspection shows 2 labels each for USB_DP and USB_DM nets
3. **Netlist Export**: Generated netlist contains proper connectivity for all USB-C pins
4. **PCB Import**: PCB correctly imports all USB-C net connections without warnings

### Performance Requirements
- Label generation time should not increase significantly (< 10% overhead)
- Memory usage should remain within acceptable bounds
- No regression in other connector types (verify with test suite)

## Priority and Impact

**Priority**: High  
**Impact**: Signal Integrity and PCB Routing

This bug affects the fundamental electrical connectivity of USB-C interfaces, potentially causing:
- Incomplete PCB routing for differential pairs
- Signal integrity issues due to missing return paths
- Manufacturing defects from incorrect net connectivity
- Compliance failures for USB-C certification

The issue is particularly critical for professional PCB design workflows where accurate hierarchical net labeling is essential for complex multi-sheet designs.

---

**Report Generated**: 2025-08-02
**Circuit-Synth Version**: Latest (develop branch)
**Affected Component**: USB-C Hierarchical Label Generation
**Status**: ❌ **STILL UNRESOLVED** - Multiple fix attempts failed

## Next Steps Required

### Immediate Actions Needed

1. **Deep Root Cause Analysis**: Conduct systematic investigation of the entire label generation pipeline
   - Trace label creation from symbol loading through final schematic output
   - Identify where USB differential pair pins are being filtered or deduplicated
   - Use step-by-step debugging to isolate the exact failure point

2. **Symbol Processing Investigation**: Examine how USB-C connector symbols are loaded and processed
   - Verify pin data extraction from symbol libraries
   - Check if pin filtering occurs during symbol processing
   - Analyze net-to-pin mapping for differential pairs

3. **Alternative Debugging Approach**: Since current fixes failed, try different investigation methods
   - Compare working nets (GND, VBUS) vs failing nets (USB_DP, USB_DM) processing
   - Create minimal test case with only USB differential pairs
   - Use external KiCad tools to verify expected vs actual symbol behavior

4. **Expert Review**: Consider architectural review of label generation system
   - The multiple failed attempts suggest a fundamental misunderstanding of the root cause
   - May require deeper understanding of KiCad schematic generation pipeline
   - Consider if issue is in circuit-synth code vs KiCad symbol definitions

### Success Criteria for Resolution

- **ESP32_C6_Dev_Board generates 4 hierarchical labels** (2 USB_DM + 2 USB_DP)
- **All USB-C circuits show complete differential pair labeling**
- **Fix is verified across multiple USB-C implementations**
- **No regression in other connector types**

### Priority

**CRITICAL** - This issue affects fundamental USB-C connectivity and has resisted multiple fix attempts. The unknown root cause indicates a potentially serious architectural issue that requires immediate expert attention.