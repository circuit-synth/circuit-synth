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
**What:** Python circuit with single 10kΩ resistor generates valid KiCad project (schematic + PCB)
**Validates:**
- Component creation in Python works
- Footprint selection works
- KiCad schematic generation with single component succeeds
- KiCad PCB generation with footprint succeeds
- Schematic has exactly 1 component
- PCB has exactly 1 footprint placed

### Test 2.2: Import Single Resistor from KiCad
**What:** KiCad project with single resistor (schematic + PCB) imports to valid Python
**Validates:**
- KiCad schematic → Python import works
- KiCad PCB footprint information recognized
- Component reference extracted correctly (R1)
- Component value extracted correctly (10k)
- Component footprint extracted correctly from PCB
- Component position preserved from PCB placement
- Generated Python has valid syntax

### Test 2.3: Single Component Round-Trip
**What:** Python → KiCad (schematic + PCB) → Python preserves single component and position
**Validates:**
- No data loss through cycle (schematic and PCB)
- Component properties identical before/after
- Component position preserved (from PCB placement)
- No spurious components added/removed
- Both schematic and PCB files valid after cycle
- Footprint placement remains stable

### Test 2.4: Resistor Value Modification
**What:** Change resistor value in Python, generate (schematic + PCB), import back
**Validates:**
- Value changes propagate correctly to schematic
- PCB footprint remains and moves correctly
- Modified value preserved through round-trip
- Component reference unchanged
- No other properties affected
- Position stable despite value change

### Test 2.5: Resistor Footprint Change
**What:** Change resistor footprint in Python, verify in KiCad schematic and PCB
**Validates:**
- Footprint selection works for resistor
- New footprint appears in PCB editor
- Footprint change persists through round-trip
- Correct footprint library references
- PCB footprint dimensions updated for new footprint
- Old footprint completely removed, not duplicated

### Test 2.6: Component Reference Preservation
**What:** Custom component reference (R_LOAD instead of R1) preserved in schematic and PCB
**Validates:**
- Custom references work in Python
- References correctly exported to KiCad schematic
- References updated in PCB footprint designator
- References reimported without modification
- PCB footprint shows correct designator after import

### Test 2.7: Component Position Stability
**What:** Footprint placement (X, Y, rotation) in KiCad PCB preserved through round-trip
**Validates:**
- Component X, Y position extracted from KiCad PCB
- Component rotation extracted from KiCad PCB
- Position and rotation preserved when re-exporting
- No spurious position changes
- PCB footprint placed exactly at same coordinates
- Rotation angle unchanged after round-trip

### Test 2.8: Switching Components
**What:** Replace one resistor with different value in Python, verify in schematic and PCB
**Validates:**
- Component replacement works in schematic
- Old component completely removed from schematic
- New component correctly added to schematic
- Old footprint completely removed from PCB
- New footprint correctly placed on PCB
- No ghost components remain in schematic or PCB
- Reference maintained (still R1)
- Position maintained (footprint placed at same location)

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
