# Test 02: Single Component - Basic CRUD Operations

**Priority:** P1 (Core Functionality)
**Category:** Foundation
**Tests:** 8 total
**Status:** In Development

## Overview

Tests basic Create, Read, Update, Delete (CRUD) operations on a single resistor component through bidirectional sync.

This test suite validates that:
- Single components can be created in Python and generated to KiCad
- Single components can be imported from KiCad to Python
- Component properties (reference, value, footprint) are preserved through round-trip
- Component modifications survive round-trip cycles
- Component removal/replacement works correctly

## Test Cases

### Test 2.1: Generate Single Resistor to KiCad
**What:** Python circuit with single 10kΩ resistor generates valid KiCad project
**Validates:**
- Component creation in Python works
- Footprint selection works
- KiCad generation with single component succeeds
- Schematic has exactly 1 component

### Test 2.2: Import Single Resistor from KiCad
**What:** KiCad project with single resistor imports to valid Python
**Validates:**
- KiCad → Python import works
- Component reference extracted correctly (R1)
- Component value extracted correctly (10k)
- Component footprint extracted correctly
- Generated Python has valid syntax

### Test 2.3: Single Component Round-Trip
**What:** Python → KiCad → Python preserves single component
**Validates:**
- No data loss through cycle
- Component properties identical before/after
- No spurious components added/removed
- File size remains stable

### Test 2.4: Resistor Value Modification
**What:** Change resistor value in Python, generate, import back
**Validates:**
- Value changes propagate correctly
- Modified value preserved through round-trip
- No other properties affected

### Test 2.5: Resistor Footprint Change
**What:** Change resistor footprint in Python, verify in KiCad
**Validates:**
- Footprint selection works for resistor
- Footprint change persists through round-trip
- Correct footprint library references

### Test 2.6: Component Reference Preservation
**What:** Custom component reference (R_LOAD instead of R1) preserved
**Validates:**
- Custom references work in Python
- References correctly exported to KiCad
- References reimported without modification

### Test 2.7: Component Position Stability
**What:** Component placement in KiCad preserved through round-trip
**Validates:**
- Component X,Y position extracted from KiCad
- Position preserved when re-exporting
- No spurious position changes

### Test 2.8: Switching Components
**What:** Replace one resistor with different value
**Validates:**
- Component replacement works
- Old component completely removed
- New component correctly added
- No ghost components remain

## Test Fixtures

Required files in `02_kicad_ref/`:
- `02_kicad_ref.kicad_pro` - KiCad project file (blank with 1 resistor R1=10k)
- `02_kicad_ref.kicad_sch` - KiCad schematic (single resistor)
- `02_kicad_ref.kicad_pcb` - KiCad PCB (footprint placed)
- `02_kicad_ref.kicad_prl` - KiCad project-local settings

## Manual Setup Required

You must create a KiCad project with a single 10kΩ resistor:

1. Open KiCad
2. Create new project: `02_kicad_ref`
3. In schematic editor:
   - Add symbol: Device → R (Resistor)
   - Set reference: R1
   - Set value: 10k
   - Save schematic
4. In PCB editor:
   - Select Tools → Update PCB from Schematic
   - Place resistor footprint somewhere on board
   - Save PCB
5. Copy project files to `02_kicad_ref/` directory

## Implementation Notes

- Uses same cleanup/preservation pattern as 01_blank_projects
- Generates to `single_resistor/` directory (test cleans before/after)
- All artifacts preserved if `PRESERVE_TEST_ARTIFACTS=1`
- Tests validate component properties against expected values

## Related Tests

- **Previous:** 01_blank_projects (foundation)
- **Next:** 03_position_preservation (advanced positioning)
- **Parallel:** 05_nets_connectivity (multi-component)
