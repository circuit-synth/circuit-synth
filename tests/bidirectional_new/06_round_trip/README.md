# Test 06: Round-Trip Validation - Full Cycle Correctness

**Priority:** P0 (CRITICAL) ⚠️
**Category:** Foundation - Cycle Integrity
**Tests:** 5 total
**Status:** In Development

## Overview

CRITICAL tests validating complete Python → KiCad (schematic + PCB) → Python → KiCad cycles work correctly and produce stable results.

This test suite validates that:
- Full cycle completes without errors or data loss (both schematic and PCB)
- Generated code is syntactically valid after import
- Circuit properties identical before and after cycle
- PCB footprints preserved through cycles
- Idempotency: repeated cycles produce identical results
- No data accumulation or corruption through cycles
- Performance acceptable for large circuits

**Why P0 CRITICAL:** Full cycle correctness is the foundation of bidirectional sync. If cycles break, the entire feature is broken.

## Test Cases

### Test 6.1: Simple Circuit Full Cycle (3 iterations)
**What:** Python circuit → KiCad (sch + pcb) → Python → KiCad → Python
**Validates:** 3-cycle stability, idempotency proof (both schematic and PCB), footprint placement preserved

### Test 6.2: Full Cycle Data Integrity
**What:** All component properties and PCB placements identical after cycle
**Validates:** No silent data corruption in schematic or PCB, footprints maintain positions

### Test 6.3: Generated Code Quality
**What:** Imported Python code is properly formatted and importable
**Validates:** Code usability, no syntax/import errors, includes footprint/position data

### Test 6.4: Large Circuit Full Cycle
**What:** 10+ component circuit (schematic + PCB) cycles correctly
**Validates:** Scalability, PCB handles many footprints, no degradation with size

### Test 6.5: Cycle Performance
**What:** Single cycle completes in reasonable time (schematic + PCB generation/import)
**Validates:** No exponential slowdown, PCB generation doesn't impact performance

## Related Tests

- **Previous:** 05_nets_connectivity
- **Critical Set:** 03, 06, 07, 08 (all must pass)
