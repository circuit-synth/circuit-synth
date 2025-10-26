# PCB Testing Clarification

## Overview

All tests in the bidirectional_new test suite validate **complete KiCad projects**, including both:
1. **Schematic files** (.kicad_sch) - Electrical connections and component symbols
2. **PCB files** (.kicad_pcb) - Footprint placement and physical layout

This document clarifies which tests cover PCB functionality and what they validate.

---

## PCB Coverage by Test

### ✅ All Tests Generate Both Schematic + PCB

When circuit-synth generates a KiCad project, it creates:
- `.kicad_pro` - Project file
- `.kicad_sch` - Schematic with component symbols
- `.kicad_pcb` - PCB with footprints placed
- `.kicad_prl` - Project-local settings

### Test 01: Blank Projects
**PCB Testing:**
- ✅ Empty PCB file generated
- ✅ PCB file is valid (no components, no footprints)
- ✅ Empty PCB survives round-trip cycles
- **What it tests:** PCB generation works for minimal case (no footprints to place)

### Test 02: Single Component
**PCB Testing:**
- ✅ Single resistor footprint generated on PCB
- ✅ Footprint placed automatically (auto-layout)
- ✅ Footprint designation matches schematic reference (R1)
- ✅ Footprint type matches component value (10k resistor)
- **Tests changing:** When component value changes (Test 2.4, 2.5), PCB footprint updates
- **Tests removing:** When component is removed, PCB footprint removed
- **Tests position:** Component position/rotation on PCB preserved (Test 2.7)
- **What it tests:** Single footprint generation, placement, updates, and position preservation

### Test 03: Position Preservation [P0 CRITICAL]
**PCB Testing:**
- ✅ Component position on PCB extracted and preserved
- ✅ Component rotation on PCB extracted and preserved
- ✅ Footprint placement synchronized with schematic position
- ✅ Position tolerance: < 0.1mm deviation
- ✅ Position stable across multiple cycles
- **What it tests:** PCB footprint placement is reliable and recoverable

### Test 04: Multiple Components
**PCB Testing:**
- ✅ Multiple footprints generated and placed on PCB
- ✅ All footprints have correct designators (R1, R2, C1)
- ✅ Different component types have different footprint shapes
- ✅ Footprint count matches component count
- ✅ No footprint duplication or loss
- **What it tests:** PCB handles multiple diverse components correctly

### Test 05: Nets & Connectivity
**PCB Testing:**
- ✅ Footprints connected by nets on PCB
- ✅ Net names visible on PCB (VCC, GND, etc.)
- ✅ Connectivity preserved through round-trips
- ✅ **NEW:** Net rewiring test (Test 5.9) - changing which footpads connect to which nets
- **What it tests:** PCB connectivity matches schematic electrical connections

### Test 06: Round-Trip Validation [P0 CRITICAL]
**PCB Testing:**
- ✅ Complete cycles preserve PCB file integrity
- ✅ Footprints don't accumulate or disappear
- ✅ Footprint placements remain stable
- ✅ Large circuits (10+) handle efficient PCB generation
- **What it tests:** PCB generation is repeatable and stable through full cycles

### Test 07: User Content Preservation [P0 CRITICAL]
**PCB Testing:**
- ✅ User annotations on PCB (if any) preserved
- ✅ Footprint silkscreen text preserved
- **What it tests:** User customizations on PCB survive round-trips

### Test 08: Idempotency [P0 CRITICAL]
**PCB Testing:**
- ✅ Same Python circuit generates identical PCB structure
- ✅ Footprint placement is deterministic (except UUIDs)
- ✅ PCB generation doesn't introduce timestamps
- **What it tests:** PCB generation is reproducible (except for expected UUID changes)

---

## What "PCB Testing" Means in This Suite

### What We DO Test
1. **Footprint Generation:** Components have footprints placed
2. **Footprint Placement:** X, Y, rotation values preserved
3. **Footprint Naming:** Designators match schematic (R1, C1, etc.)
4. **Footprint Integrity:** Count and types correct
5. **Footprint Connectivity:** Connected to correct nets
6. **Footprint Stability:** Positions maintained through cycles

### What We DON'T Test (Not in Scope)
- ❌ Detailed PCB routing (trace routing)
- ❌ PCB design rules (clearances, widths)
- ❌ Layer assignments
- ❌ DFM-specific validations
- ❌ Thermal management features
- ❌ 3D model associations
- ❌ Manual PCB layout modifications (we preserve them, but don't test user routing)

**Rationale:** circuit-synth focuses on **schematic-to-PCB synchronization**, not PCB design.
The tool ensures footprints are placed and track with the schematic, but doesn't design the PCB layout.

---

## Important Note: "Did the part get generated"

Many PCB tests validate at the basic level of:
1. ✅ **Did the part get generated?** (Footprint exists)
2. ✅ **Didn't the part get moved** unexpectedly (Position preserved)
3. ✅ **Can I add a new part?** (Multiple footprints work)
4. ✅ **Can I remove a part?** (Footprint deleted with component)

These are the essential validations. PCB design details (routing, traces, etc.) are outside scope.

---

## Fixture Requirements for PCB Tests

When creating KiCad fixtures, you must:

1. **Create the schematic** with components
2. **Update PCB from schematic** (Tools → Update PCB from Schematic)
3. **Place footprints** on the PCB board
   - Specific positions if testing position preservation
   - Auto-layout is fine for basic tests
4. **Verify footprint placement** in KiCad before saving
5. **Save the PCB file** (.kicad_pcb)

**Example for Test 03:**
```
1. Create schematic with R1 (10k resistor)
2. In PCB editor: Tools → Update PCB from Schematic
3. Move R1 footprint to X=30mm, Y=40mm
4. Verify position in Properties panel
5. Save PCB
6. Copy all files to 03_kicad_ref/
```

---

## Test Commands

### Run all tests (including PCB tests)
```bash
env PRESERVE_TEST_ARTIFACTS=1 uv run pytest tests/bidirectional_new/ -v
```

### Run specific PCB-focused tests
```bash
# Test 02: Single component + PCB footprint
env PRESERVE_TEST_ARTIFACTS=1 uv run pytest tests/bidirectional_new/02_single_component/ -v

# Test 03: Position preservation (schematic + PCB)
env PRESERVE_TEST_ARTIFACTS=1 uv run pytest tests/bidirectional_new/03_position_preservation/ -v

# Test 04: Multiple components + multiple footprints
env PRESERVE_TEST_ARTIFACTS=1 uv run pytest tests/bidirectional_new/04_multiple_components/ -v
```

### View generated PCB files
```bash
ls -la tests/bidirectional_new/*/test_artifacts/*/
# Look for .kicad_pcb files in each test's artifacts
```

---

## PCB File Generation

When circuit-synth generates a KiCad project:

1. **Component Properties** (from Python) → **Schematic** (.kicad_sch)
   - Reference (R1, C1)
   - Value (10k, 100nF)
   - Position/rotation
   - Electrical connections

2. **Netlist** (from Python nets) → **Schematic connections** (.kicad_sch)
   - Which pins connect to which nets
   - Net names (VCC, GND, etc.)

3. **Footprint Selection** (from component) → **PCB** (.kicad_pcb)
   - Footprint library selection
   - Footprint dimensions
   - Pad layout

4. **Auto-Placement** → **PCB** (.kicad_pcb)
   - Footprints placed in grid pattern
   - Can be manually moved for testing position preservation

---

## Summary

**PCB testing is integrated throughout the test suite:**
- Every test validates complete KiCad projects (schematic + PCB)
- Position preservation tests explicitly cover PCB footprint placement
- Multiple component tests ensure all footprints are generated
- Round-trip tests confirm PCB data survives full cycles
- Idempotency tests validate PCB structure is repeatable

**The goal:** Ensure that circuit-synth generates valid, complete KiCad projects where the PCB footprints correctly reflect the schematic circuit and preserve all user-intentional placements.

---

Generated: 2025-10-25 | Session: PCB Testing Clarification
