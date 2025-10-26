# Test 04: Multiple Components - Multi-Element Circuit Handling

**Priority:** P1 (Core Functionality)
**Category:** Foundation
**Tests:** 7 total
**Status:** In Development

## Overview

Tests circuit generation and import with multiple components (resistors, capacitors, etc.) to validate proper handling of component collections and their relationships in both schematic and PCB.

This test suite validates that:
- Multiple components can be created and generated to KiCad (schematic + PCB)
- All components extracted correctly when importing from KiCad
- Component footprints placed correctly on PCB
- Component relationships preserved (no loss or duplication)
- Different component types handled correctly
- Component collection maintains integrity through round-trip
- No interference between components
- PCB footprints track with schematic components

## Test Cases

### Test 4.1: Generate Two Resistors to KiCad
**What:** Python circuit with 2 resistors generates KiCad schematic and PCB
**Validates:** Multiple components created in schematic and footprints placed on PCB

### Test 4.2: Generate Mixed Component Types
**What:** Resistor + Capacitor circuit generates to schematic and PCB correctly
**Validates:** Different component types coexist properly in both files, different footprints placed

### Test 4.3: Import Multiple Components from KiCad
**What:** KiCad project with 3+ components (schematic + PCB) imports to valid Python
**Validates:** All components extracted from schematic, all footprints extracted from PCB, correct references and placements

### Test 4.4: Multiple Component Round-Trip
**What:** Python → KiCad (schematic + PCB) → Python preserves all components and placements
**Validates:** No loss, duplication, or corruption in schematic or PCB, footprints remain placed

### Test 4.5: Component Count Stability
**What:** Repeated round-trips maintain exact component count in schematic and PCB
**Validates:** No spurious components added or lost in either file, footprint count matches component count

### Test 4.6: Component Property Preservation (Multiple)
**What:** All component properties preserved with multiple components across schematic and PCB
**Validates:** Values, references, footprints all correct in both files, PCB footprints match schematic

### Test 4.7: Large Component Count
**What:** 20+ component circuit generates and imports correctly for schematic and PCB
**Validates:** Scalability and performance, PCB generation stays efficient with many footprints

## Manual Setup Required

Create KiCad fixture with multiple components (in both schematic and PCB):
1. In schematic editor:
   - R1: 10k resistor
   - R2: 47k resistor
   - C1: 100nF capacitor
2. In PCB editor:
   - Update PCB from schematic
   - Place all 3 footprints on board
   - Ensure each component has a placed footprint

Reference in: `04_kicad_ref/` directory
Include all files: .kicad_pro, .kicad_sch, .kicad_pcb, .kicad_prl

## Related Tests

- **Previous:** 03_position_preservation
- **Next:** 05_nets_connectivity
