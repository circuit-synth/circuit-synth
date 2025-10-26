# Test 04: Multiple Components - Multi-Element Circuit Handling

**Priority:** P1 (Core Functionality)
**Category:** Foundation
**Tests:** 7 total
**Status:** In Development

## Overview

Tests circuit generation and import with multiple components (resistors, capacitors, etc.) to validate proper handling of component collections and their relationships.

This test suite validates that:
- Multiple components can be created and generated to KiCad
- All components extracted correctly when importing from KiCad
- Component relationships preserved (no loss or duplication)
- Different component types handled correctly
- Component collection maintains integrity through round-trip
- No interference between components

## Test Cases

### Test 4.1: Generate Two Resistors to KiCad
**What:** Python circuit with 2 resistors generates KiCad schematic
**Validates:** Multiple components created and placed correctly

### Test 4.2: Generate Mixed Component Types
**What:** Resistor + Capacitor circuit generates correctly
**Validates:** Different component types coexist properly

### Test 4.3: Import Multiple Components from KiCad
**What:** KiCad project with 3+ components imports to valid Python
**Validates:** All components extracted, correct references

### Test 4.4: Multiple Component Round-Trip
**What:** Python → KiCad → Python preserves all components
**Validates:** No loss, duplication, or corruption

### Test 4.5: Component Count Stability
**What:** Repeated round-trips maintain exact component count
**Validates:** No spurious components added or lost

### Test 4.6: Component Property Preservation (Multiple)
**What:** All component properties preserved with multiple components
**Validates:** Values, references, footprints all correct

### Test 4.7: Large Component Count
**What:** 20+ component circuit handles correctly
**Validates:** Scalability and performance

## Manual Setup Required

Create KiCad fixture with multiple components:
- R1: 10k resistor
- R2: 47k resistor  
- C1: 100nF capacitor

Reference in: `04_kicad_ref/` directory

## Related Tests

- **Previous:** 03_position_preservation
- **Next:** 05_nets_connectivity
