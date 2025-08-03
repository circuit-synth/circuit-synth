# Bidirectional KiCad ↔ Python Testing Workflow

## Executive Summary

**Status**: 🚨 **Critical Gap Identified** - Selective update logic does not exist

**Key Finding**: The system claims to "synchronize" and "update" files but actually performs complete regeneration, losing all user modifications. Step 4 testing revealed this fundamental issue.

**Next Priority**: Implement true selective updating with canonical circuit comparison

## Overview

Progressive testing framework for validating bidirectional synchronization between KiCad projects and circuit-synth Python code. Each step builds complexity while testing preservation of user modifications.

**Testing Philosophy**: 
- 🔬 **Incremental complexity** - Start simple, add complexity gradually
- 🔄 **Bidirectional validation** - Test both KiCad→Python and Python→KiCad directions  
- 🛡️ **Preservation focus** - User modifications must survive all operations
- 📊 **Evidence-based** - Document actual vs expected behavior with examples

## Foundation Tests (Steps 0-4)

### Step 0: Initial KiCad Project
**Goal**: Create baseline KiCad project
**Content**: ESP32-C6 + bulk capacitor (no connections)
**Status**: ✅ Complete

### Step 1: KiCad → Python Import
**Goal**: Convert KiCad project to Python circuit-synth format
**Expected**: Clean Python code with proper @circuit decorator
**Status**: ✅ Complete

### Step 2: Python → KiCad Generation
**Goal**: Generate KiCad project from imported Python
**Expected**: KiCad files that match original project structure
**Validation**: Files open correctly in KiCad, components present
**Status**: 🔄 Next

### Step 3: Manual KiCad Edits
**Goal**: Simulate user making manual changes in KiCad
**Changes**: Connect ESP32 and capacitor to +3V3 and GND power symbols
**Expected**: Functional circuit with proper power connections
**Status**: 🔄 Pending

### Step 4: Re-import After Manual Edits ⚠️ **CRITICAL FINDING**
**Goal**: Test selective update - Python should preserve user code
**Expected**: Only net connections updated, all else unchanged
**Actual**: Complete file regeneration with data loss
**Critical Evidence**: 
- ❌ Reference designators: `C1`→`C?`, `U1`→`U?` (broken)
- ❌ User modifications: Completely overwritten
- ❌ Comments: All lost
- ✅ Backup created: `.backup` file preserves original
**Root Cause**: No selective update logic exists - claims to "update" but does full regeneration
**Status**: ❌ **FAILS** - Blocks all subsequent testing until fixed

## Selective Update Tests (Steps 5-8)

### Step 5: Component Addition (KiCad → Python)
**Goal**: Add resistor in KiCad, test selective Python update
**Changes**: Add single resistor component to KiCad schematic
**Expected**: Only resistor added to Python, comments preserved
**Critical Test**: Existing Python comments must survive the update
**Status**: 🔄 Pending

### Step 6: Component Addition (Python → KiCad)
**Goal**: Add capacitor in Python, test selective KiCad update
**Changes**: Add capacitor component to Python circuit
**Expected**: Only capacitor added to KiCad, user positioning preserved
**Critical Test**: Manual component positions must be unchanged
**Status**: 🔄 Pending

### Step 7: Circuit Addition (KiCad → Python)
**Goal**: Add voltage regulator circuit in KiCad
**Changes**: Complete 3.3V LDO circuit (IC + input/output caps)
**Expected**: All new components and nets added to Python selectively
**Validation**: Existing code structure preserved
**Status**: 🔄 Pending

### Step 8: Subcircuit Addition (Python → KiCad)
**Goal**: Add USB-C subcircuit in Python code
**Changes**: Complete USB-C connector with ESD protection
**Expected**: New components added to KiCad without affecting existing layout
**Validation**: User component positions and routing preserved
**Status**: 🔄 Pending

## Conflict Resolution Tests (Steps 9-12)

*Note: These tests require Step 4 to be fixed first*

### Step 9: Reference Designator Fixes
**Goal**: Fix the broken reference designator parsing
**Problem**: KiCad netlist contains proper refs (`C1`, `U1`) but parser outputs (`C?`, `U?`)
**Changes**: Test parser with various reference designator patterns
**Expected**: Proper reference extraction: `C1`, `U1`, `R1`, `J1`, etc.
**Critical Test**: All reference types parsed correctly (resistors, caps, ICs, connectors)
**Implementation**: Fix `circuit_synth.tools.kicad_netlist_parser`
**Status**: 🚨 **BLOCKING** - Must fix before other tests

### Step 10: Component Property Changes
**Goal**: Test value and property modification handling
**Changes**: Change resistor values, capacitor ratings, component properties
**Expected**: Only changed properties updated, structure preserved
**Status**: 🔄 Planned

### Step 11: Net Renaming and Reorganization
**Goal**: Test net name changes and signal reorganization
**Changes**: Rename nets, reorganize signal groups
**Expected**: Net connections updated while preserving circuit logic
**Status**: 🔄 Planned

### Step 12: Large Circuit Stress Test
**Goal**: Test performance and reliability with complex circuits
**Changes**: Circuit with 50+ components, multiple power rails, complex routing
**Expected**: Reasonable performance, no data loss
**Status**: 🔄 Planned

## Hierarchical Tests (Steps 13-15)

### Step 13: Hierarchical Sheet Creation
**Goal**: Test multi-sheet KiCad project handling
**Changes**: Move components to separate sheets, create hierarchical blocks
**Expected**: Python generates multiple files or proper hierarchical structure
**Status**: 🔄 Planned

### Step 14: Cross-Sheet Signal Management
**Goal**: Test hierarchical pin and signal management
**Changes**: Signals crossing sheet boundaries
**Expected**: Proper hierarchical pin handling in Python
**Status**: 🔄 Planned

### Step 15: Sheet Reorganization
**Goal**: Test moving components between sheets
**Changes**: Move subcircuits from one sheet to another
**Expected**: Python structure updated to match new organization
**Note**: User edits on original sheet may not be preservable
**Status**: 🔄 Planned

## Edge Cases and File Organization

### File Structure Challenges
**Question**: What if user doesn't follow expected 1-file-1-circuit pattern?

**Scenarios to Handle**:
1. **Multiple circuits in one file**: User puts several subcircuits in single Python file
2. **Distributed circuits**: User splits single circuit across multiple files
3. **Mixed organization**: Some circuits hierarchical, others flat
4. **Custom imports**: User imports circuits from other modules

**Strategy**: 
- Detect and document current patterns
- Provide migration tools for incompatible structures
- Support multiple organization schemes where possible
- Clear error messages when structure is unsupported

### Error Handling Tests
- Malformed KiCad files
- Invalid Python circuit code
- Missing component libraries
- Version compatibility issues
- File permission problems

## Architecture and File Organization Challenges

### Current System Assumptions
- 🏗️ **1-file-1-circuit pattern**: Each Python file contains one `@circuit` function
- 📁 **Flat file structure**: No complex imports or dependencies
- 🎯 **Single target**: All changes go to one main circuit file

### Real-World Usage Patterns

**Scenario 1: Multi-Circuit Files**
```python
# User wants this organization:
@circuit
def power_supply():
    # Power management circuit
    pass

@circuit  
def signal_processing():
    # Signal processing circuit
    pass
```
**Challenge**: Which circuit gets updated from KiCad changes?

**Scenario 2: Distributed Circuit Architecture**
```python
# main.py
from power.regulator import voltage_rail
from interface.usb import usb_connector

@circuit
def main_board():
    power = voltage_rail()
    usb = usb_connector()
    # Integration logic
```
**Challenge**: How to update components across multiple files?

**Scenario 3: Component Libraries and Reuse**
```python
# User has custom component library
from my_components import custom_mcu, power_module

@circuit
def my_design():
    mcu = custom_mcu(variant="high_speed")
    power = power_module(rails=[3.3, 5.0])
```
**Challenge**: Handle custom components not in standard libraries?

### Proposed Solutions

**Detection Strategy**:
1. **Analyze existing Python structure** before making changes
2. **Detect organization pattern** (flat, hierarchical, distributed)
3. **Validate compatibility** with current update capabilities
4. **Provide migration tools** for unsupported structures

**Support Matrix**:
| Pattern | KiCad→Python | Python→KiCad | Implementation Priority |
|---------|:------------:|:------------:|:-----------------------:|
| Single @circuit file | ✅ Target | ✅ Target | **Phase 1** |
| Multi-circuit file | ⚠️ Requires circuit selection | ⚠️ Complex | **Phase 2** |
| Distributed imports | ❌ Unsupported | ❌ Unsupported | **Phase 3** |
| Custom components | ⚠️ Limited | ⚠️ Limited | **Phase 3** |

**Error Handling Strategy**:
- 🚨 **Clear error messages** for unsupported patterns
- 🔄 **Migration assistance** to convert to supported formats
- 📖 **Documentation** of supported vs unsupported patterns
- 🛠️ **Future roadmap** for additional pattern support

## Implementation Roadmap

### Phase 1: Foundation (Steps 1-8)
- ✅ Basic import/export working
- 🚨 **FIX: Reference designator parsing**
- 🚨 **IMPLEMENT: Selective update logic**
- 🚨 **IMPLEMENT: Canonical circuit comparison**

### Phase 2: Robustness (Steps 9-15)  
- Conflict resolution and error handling
- Performance optimization
- Version compatibility

### Phase 3: Advanced Features (Steps 16-18)
- Hierarchical sheet support
- Complex file organization patterns
- Custom component libraries

### Success Metrics
- ✅ **Zero data loss** in all bidirectional operations
- ✅ **User modifications preserved** across all update operations
- ✅ **Performance acceptable** for circuits up to 100 components
- ✅ **Clear error messages** for all failure modes
- ✅ **Documentation coverage** for all supported patterns

## Quick Reference Commands

```bash
# Foundation tests
cd /Users/shanemattner/Desktop/circuit-synth3/bidirectional_update_test

# Step 1: KiCad → Python import
uv run kicad-to-python initial_kicad/ step1_imported_python/

# Step 2: Python → KiCad generation  
cd step1_imported_python && uv run python main.py

# Step 4: Test selective update (currently fails)
uv run kicad-to-python step3_manual_kicad_edits/initial_kicad_generated/ step4_reimported_python/main_reference.py --backup --verbose

# Restore from backup after failed update
mv step4_reimported_python/main_reference.py.backup step4_reimported_python/main_reference.py
```

## Current Blockers

1. **Reference Designator Parser Bug** - `kicad_netlist_parser.py` outputs `C?`/`U?` instead of `C1`/`U1`
2. **Missing Selective Update Logic** - No canonical circuit comparison exists
3. **Missing Canonical Analysis Module** - `circuit_synth.kicad.canonical` referenced in plans but doesn't exist

**Priority**: Fix blocker #1 first (reference designators) as it affects all subsequent testing.