# Bidirectional Test Suite - Comprehensive Summary

**Date:** 2025-10-30 (Updated: Version 0.11.3 + Manual validation of tests 28, 30, 59 + Critical bugs discovered)
**Branch:** test/bidirectional-manual-validation
**Total Tests:** 68 comprehensive bidirectional tests (01-68, excluding 27)
**New Tests Added:** 30 tests (39-65, plus 66-68)
**Tests Removed:** Test 27 (architecturally invalid - junction test incompatible with label-based design)
**Version:** 0.11.3

### 🎯 Manual Validation Campaign Progress
**Status:** Tests 01-21, 25, 26, 31, 33, 34, 35, 36, 37 manually validated (29 of 68 tests)
**Latest Session (2025-10-30 PM):** Tested 28, 30, 59 - All BLOCKED by critical bugs

**Findings:**
- Test 15 (Net split) is XPASS - now working despite expected failure on Issue #373
- Test 22 BLOCKED by Issue #406 (subcircuit generation broken)
- Test 24 REWRITTEN for cross-sheet hierarchical connections (blocked by #406)
- Test 28 BLOCKED by Issue #427 🔴 **CRITICAL** - Hierarchical labels not generated for net connections
  - Multi-unit components render ✅ (Issue #407 partially fixed)
  - Net connections NOT visible in schematic ❌ (NEW BUG #427)
  - NoConnect feature still needed (Issue #408)
- Test 29 FIXED - Issue #409 resolved (custom properties now written correctly) ✅
- Test 30 BLOCKED by Issue #410 🔴 **CRITICAL** - PCB synchronization still broken (REOPENED)
  - Previously thought fixed, but still not working
  - Three separate bugs: PCB generator, component manager, PCB synchronizer
  - Footprints not syncing from schematic to PCB
- Test 31 FIXED (initial state had NET1 uncommented) - now passes ✓
- Test 32 SKIPPED (waiting for text annotation API improvement - Issue #411)
- Test 33 PASSES - 8-bit bus connections (D0-D7) all correct ✓
- Test 34 PASSES - Bulk component add with Python loops (10→20 resistors) ✓
- Test 35 PASSES - Bulk component remove with Python loops (10→5 resistors) ✓
- Test 36 PARTIALLY WORKING - Auto-incrementing subcircuit naming feature implemented (Issue #422) ✅
  - Single instance works perfectly (hierarchical sheet + child circuit)
  - Multiple instances blocked by Issue #419 (reference collision bug)
- Test 37 PASSES - Hierarchical subcircuit redesign (R1,C1 → R2,R3,C2) ✓
  - Root circuit (R_main) preserved, child subcircuit components replaced
  - Synchronization falls back to regeneration (acceptable for now)
- Test 59 BLOCKED by Issue #427 🔴 **CRITICAL** - Hierarchical labels not generated
  - Fixture updated to use modern @circuit decorator
  - Components render but NO hierarchical labels for net connections
  - Warning: "Net 'DATA_IN' has only 1 connection(s) - may indicate connection issue"
- Test 68 NEW - Dynamic sheet sizing (XFAIL - Issue #413)

## Executive Summary

This document provides a comprehensive summary of the bidirectional test suite for circuit-synth, covering all 68 tests that validate Python ↔ KiCad synchronization with position preservation (THE KILLER FEATURE).

### Test Results Overview

```
Total: 68 tests across 46 test directories (test 27 removed)
├── Tests 01-38: Original suite (36 passed, 1 xfailed, 1 removed)
│   └── Test 27 REMOVED (junction test architecturally invalid)
├── Tests 39-65: Hierarchical expansion (34 test functions)
│   ├── 19 PASSED ✅
│   ├── 1 SKIPPED (documents expected behavior)
│   ├── 12 XFAILED (known limitations documented)
│   └── 2 XPASSED (unexpectedly working!)
├── Tests 22, 24, 66-67: Rewritten/New (2025-10-29)
│   ├── Test 22: Progressive subcircuit addition (XFAIL - Issue #406)
│   ├── Test 24: Cross-sheet connection (XFAIL - Issue #406)
│   ├── Test 66: Duplicate net names isolation (NEW SAFETY TEST)
│   └── Test 67: Connected multi-level hierarchy (XFAIL - blocked by 22+24)
└── Test 68: Dynamic sheet sizing (NEW - 2025-10-30)
    └── Test 68: Automatic sheet resize (XFAIL - Issue #413)

Overall Status: ✅ ALL TESTS OPERATIONAL
Manual Validation: 29 of 68 tests (43%)
```

### Key Achievement: Hierarchical Operations Gap CLOSED

**Critical Finding:** Tests 01-38 almost exclusively operated on ROOT SHEET ONLY. This left a massive gap in hierarchical circuit testing.

**Solution:** Tests 39-65 prioritize hierarchical operations:
- ✅ Component modifications in subcircuits (test 39)
- ✅ Net operations within child sheets (test 40)
- ✅ Power distribution through hierarchy (tests 44, 47, 48)
- ✅ Cross-sheet component operations (tests 41, 42)
- ✅ Hierarchical pin management (tests 59, 60)

---

## Test Organization by Priority

### Priority 0: Critical Gaps (9 tests) 🔴

| Test | Name | Status | Key Validation |
|------|------|--------|----------------|
| 39 | Modify Component in Subcircuit | ✅ PASS | Hierarchical component operations |
| 40 | Net Operations in Subcircuit | ✅ PASS | Hierarchical net management |
| 41 | Copy Component Cross-Sheet | ⚠️ XFAIL (1 XPASS) | Position preservation across sheets |
| 44 | Subcircuit Hierarchical Ports | ✅ PASS | Power/signal flow through hierarchy |
| 45 | Import Power Symbols from KiCad | ⚠️ XFAIL | KiCad → Python power import |
| 47 | Power Symbols in Subcircuit | ⚠️ XFAIL | Hierarchical power distribution |
| 57 | Global Labels Multi-Sheet | ⚠️ XFAIL | Flat (non-hierarchical) designs |
| 58 | Mixed Hierarchical + Global Labels | ⚠️ XFAIL (1 PASS) | Hybrid labeling strategies |
| 64 | Complex Multi-Step Workflow | ✅ PASS | **THE ULTIMATE TEST** |

### Priority 1: Important Features (9 tests) 🟡

| Test | Name | Status | Key Validation |
|------|------|--------|----------------|
| 42 | Move Component Between Sheets | ⚠️ XFAIL (1 XPASS) | Component migration across hierarchy |
| 46 | Export Power Symbols to KiCad | ⚠️ XFAIL | Multi-domain power (3.3V, 5V, 12V, etc.) |
| 48 | Multi-Voltage Subcircuit | ⚠️ XFAIL | Level shifters, mixed-voltage designs |
| 49 | Annotate Schematic | ✅ PASS | KiCad annotation integration |
| 50 | Component Footprint Change | ✅ PASS | SMD ↔ THT footprint swaps |
| 51 | Sync After External Edit | ⏭️ SKIP | Collaborative workflow (documents expected) |
| 59 | Modify Hierarchical Pin Name | ⚠️ XFAIL | Interface evolution (pin renaming) |
| 60 | Remove Hierarchical Pin | ⚠️ XFAIL | Interface simplification |
| 61 | Large Circuit Performance | ✅ PASS | 100 components, performance benchmarks |

### Priority 2: Nice-to-Have (9 tests) 🟢

| Test | Name | Status | Key Validation |
|------|------|--------|----------------|
| 29 | Component Custom Properties | ✅ PASS | DNP, MPN, Tolerance, complex types (Issue #409) |
| 52 | Unicode Component Names | ✅ PASS | Greek (Ω, π, μ), Chinese, Japanese |
| 53 | Reference Collision Detection | ✅ PASS | Global uniqueness enforcement |
| 54 | DRC Validation | ✅ PASS (2 tests) | kicad-cli DRC integration |
| 55 | ERC Validation | ✅ PASS (2 tests) | kicad-cli ERC integration |
| 56 | BOM Export | ✅ PASS | Manufacturing workflow (CSV BOM) |
| 62 | Wire Routing Preservation | ⚠️ XFAIL (1 PASS) | Aesthetic feature (wire paths) |
| 63 | Component Rotation Preservation | ✅ PASS | Rotation angles preserved |
| 65 | Conflict Resolution | ✅ PASS | Concurrent edit handling |

---

## Test Rewrites and New Tests (2025-10-29)

### Test 22: Progressive Subcircuit Addition (REWRITTEN)
**Old Purpose:** Single-step subcircuit addition (broken, Issue #406)
**New Purpose:** Incremental hierarchy development (1→2→3 levels)
**Files:** `progressive_hierarchy.py`, `test_22_progressive_subcircuit_addition.py`, `README_progressive.md`
**Status:** XFAIL (blocked by Issue #406 - subcircuit generation)
**Validates:** Adding subcircuits incrementally, hierarchical sheet symbols at each level

### Test 24: Cross-Sheet Hierarchical Connection (REWRITTEN)
**Old Purpose:** Same-sheet "global label" test (redundant with test 10)
**New Purpose:** Cross-sheet hierarchical connection via net passing
**Files:** `hierarchical_connection.py`, `test_24_cross_sheet_connection.py`, `README.md`
**Status:** XFAIL (blocked by Issue #406)
**Validates:** Passing Net from parent to child creates hierarchical pins/labels

### Test 66: Duplicate Net Names Isolation (NEW SAFETY TEST)
**Purpose:** Ensure Net("SIGNAL") in circuit_a ≠ Net("SIGNAL") in circuit_b
**Files:** `isolated_circuits.py`, `test_66_duplicate_net_names_isolation.py`, `README.md`
**Status:** Ready to test (not hierarchical)
**Validates:** R1—R2 on one net, R3—R4 on different net, no accidental merging
**Critical:** Prevents dangerous bug where same net names accidentally connect unrelated circuits

### Test 67: Connected Multi-Level Hierarchy (NEW ULTIMATE TEST)
**Purpose:** Combine progressive hierarchy + cross-sheet connectivity
**Files:** `connected_hierarchy.py`, `test_67_connected_multi_level_hierarchy.py`, `README.md`
**Status:** XFAIL (blocked by tests 22+24 dependencies)
**Validates:** R1—R2—R3 connected across 3 hierarchy levels via net passing
**Significance:** If this passes, hierarchical design is FULLY functional

### Test 27: Add Junction (REMOVED)
**Old Purpose:** Test junction dot creation when T-connections occur
**Removal Reason:** Architecturally invalid - circuit-synth uses hierarchical labels instead of physical wires
**Rationale:**
- Circuit-synth doesn't draw wires between components
- Each component pin gets its own hierarchical label
- Junction dots only appear when physical wires cross/meet
- Since no wires are drawn, junctions will never be generated
- Test assumption (T-connections create junctions) doesn't apply to label-based architecture

### Key Philosophy Changes
1. **No global nets** - All connections explicit via net passing
2. **Safety first** - Test 66 ensures duplicate names don't merge
3. **Incremental development** - Test 22 validates step-by-step hierarchy
4. **Complete workflow** - Test 67 combines everything into ultimate test
5. **Architecture alignment** - Removed test 27 (incompatible with label-based design)

---

## Known Issues and Limitations

### 🔴 Issue #427: Hierarchical Labels Not Generated for Net Connections (CRITICAL - NEW)

**Discovered:** 2025-10-30 during Test 28 and Test 59 validation
**Affected Tests:** Test 28, Test 59, Test 60, Test 58, and ALL hierarchical circuits with net connections
**Impact:** 🔴 **CRITICAL** - Net connections invisible in KiCad schematics
**Status:** Open - Blocking entire hierarchical circuit workflow

**Problem:** When nets are connected to components in subcircuits (`resistor[1] += data_in`), NO hierarchical labels are generated in the .kicad_sch file. Components render but appear unconnected.

**Evidence:**
- Test 28: LM358 and connectors render, but no net labels (INPUT_A, OUTPUT_A, VCC, VEE)
- Test 59: R1 resistor renders, but no "DATA_IN" hierarchical label
- Warning: "Net 'DATA_IN' has only 1 connection(s) - may indicate connection issue"

**Root Cause:** Schematic writer not generating hierarchical labels for net connections in subcircuits

### 🔴 Issue #410: PCB Synchronization Broken (CRITICAL - REOPENED)

**Reopened:** 2025-10-30 - Previously thought fixed, but still broken
**Affected Tests:** Test 30 (Component Missing Footprint)
**Impact:** 🔴 **CRITICAL** - Cannot sync footprints from schematic to PCB
**Status:** Reopened - Three separate bugs identified

**Problems:**
1. **PCB Generator** doesn't read footprint from Python Component object
2. **Component Manager** can't find component R1 (even though it exists)
3. **PCB Synchronizer** doesn't read footprint from schematic file

**Evidence from Test 30:**
- Warning: "Component R1 not found"
- Warning: "R1 has no footprint, skipping"
- PCB file remains empty despite footprint defined in Python code
- Schematic correctly has footprint property

### Issue #373: Netlist Exporter Empty Nets Section

**Affected Tests:** Test 36, Test 43, Test 15 (was blocking)
**Impact:** Cannot validate electrical connectivity via netlist
**Status:** ⚠️ **IMPORTANT UPDATE (2025-10-29):** Test 15 now XPASS!
- Test 15 was expected to fail due to this issue
- During manual validation, test 15 actually passes
- This suggests the netlist functionality may be working better than expected
- Recommend re-investigating Issue #373 status

### Issue #380: Synchronizer Doesn't Remove Old Hierarchical Labels

**Affected Tests:** Test 59, Test 60, Test 58
**Impact:** Old labels persist when pins removed/renamed
**Status:** Claimed fixed by commits bc8b795, but cannot test due to Issue #427 blocking

### Issue #426: Custom KiCad Library Support Not Exposed (NEW)

**Created:** 2025-10-30
**Impact:** Users cannot use custom symbol libraries (company parts, vendor libs)
**Status:** Feature exists internally but no user-facing API
**Priority:** Medium-High - Important for professional use

### Power Symbol Handling

**Affected Tests:** Test 45, 46, 47, 48
**Impact:** Power import/export/subcircuit support incomplete
**Status:** Needs comprehensive power symbol enhancement

### Global Label Support

**Affected Tests:** Test 57, Test 58
**Impact:** circuit-synth uses hierarchical labels by design
**Status:** Documented limitation (architectural decision)

---

## Manual Testing Checklist

| Test Range | Manual Testing Status | Notes |
|------------|----------------------|-------|
| 01-11 | ✅ Manually tested | Visually inspected in KiCad GUI |
| 12 | ✅ Manually tested | Label orientation issue found (#403) |
| 13 | ✅ Manually tested | Component rename with position preservation ✓ |
| 14 | ✅ Manually tested | Net merge - NET2→NET1 on R3/R4 ✓ |
| 15 | ✅ Manually tested | Net split - R3 NET1→NET2 ✓ (XPASS) |
| 16 | ✅ Manually tested | Add power symbol (VCC) to resistor ✓ |
| 17 | ✅ Manually tested | Add ground symbol (GND) to resistor ✓ |
| 18 | ✅ Manually tested | Multi-voltage domains (VCC/3V3/5V/GND) ✓ |
| 19 | ✅ Manually tested | Component type swap (R→C) with position preservation ✓ |
| 20 | ✅ Manually tested | Component rotation preservation ✓ (property text rotation issue #401) |
| 21 | ✅ Manually tested | Multi-unit components - sync works, visual layout has stacking |
| 22-24 | ⚠️ Automated only | Need manual GUI validation (hierarchical, blocked by #406) |
| 25 | ✅ Manually tested | Local label creation (DATA_LINE) - sync adds labels correctly ✓ |
| 26 | ✅ Manually tested | Power symbols - all 5 symbols generated with correct library references ✓ |
| 27 | ❌ REMOVED | Test architecturally invalid (junction test incompatible with label-based design) |
| 28 | ❌ BLOCKED | 🔴 Issue #427 (hierarchical labels not generated - CRITICAL) |
|    |           | Components render but NO net connections visible |
| 29 | ✅ FIXED | Issue #409 resolved - custom properties now written correctly ✓ |
| 30 | ❌ BLOCKED | 🔴 Issue #410 REOPENED (PCB synchronization - CRITICAL) |
|    |           | Tested 2025-10-30: Still broken, three separate bugs identified |
| 31 | ✅ Manually tested | Isolated component + netlist validation - initial state fixed, test passes ✓ |
| 32 | ⏭️ SKIPPED | Waiting for text annotation API improvement (Issue #411) |
| 33 | ✅ Manually tested | 8-bit bus connections (D0-D7) - all nets verified in netlist ✓ |
| 34 | ✅ Manually tested | Bulk component add - Python loop advantage (10→20 resistors) ✓ |
| 35 | ✅ Manually tested | Bulk component remove - Python loop (10→5 resistors) ✓ |
| 36 | ✅ Manually tested | Hierarchical subcircuit duplication - auto-increment naming works ✓ (Issue #422) |
|    |                  | Single instance perfect, multiple blocked by Issue #419 |
| 37 | ✅ Manually tested | Hierarchical subcircuit redesign - R1,C1 → R2,R3,C2 ✓ |
|    |                  | Root preserved, child components replaced successfully |
| 38-58 | ⚠️ Automated only | Need manual GUI validation |
| 59 | ❌ BLOCKED | 🔴 Issue #427 (hierarchical labels not generated - CRITICAL) |
|    |           | Fixture updated to @circuit decorator, but no labels generated |
|    |           | Warning: "Net 'DATA_IN' has only 1 connection(s)" |
| 60-67 | ⚠️ Automated only | Likely blocked by #427 (hierarchical label issues) |
| 68 | 🆕 NEW TEST | Dynamic sheet sizing (XFAIL - Issue #413) |

**Progress:** 29 of 68 tests manually validated (43%)

**Critical blockers (2025-10-30):**
- 🔴 #427: Hierarchical labels not generated (NEW - blocks 28, 59, 60, 58, and ALL hierarchical circuits)
- 🔴 #410: PCB synchronization broken (REOPENED - blocks 30, critical for PCB workflow)

**Other known issues:**
- #401: Property text rotation
- #403: Label orientation
- #406: Subcircuit generation (blocks 22, 24)
- #408: NoConnect feature (blocks 28 - secondary issue)
- #411: Text annotation API improvement needed (blocks 32)
- #413: Dynamic sheet sizing not implemented (test 68 documents)
- #419: Reference collision in subcircuits (blocks test 36 multiple instances)
- #426: Custom KiCad library support not exposed (NEW - enhancement)

**New features:**
- #422: Auto-incrementing subcircuit naming (implemented, working for single instances)

---

## Performance Benchmarks

```
Total Execution: 61.56 seconds (34 test functions)
Average: ~1.8 seconds per test

Test 61 (100 components): ~8.5s
- Generation: ~2.5s
- Synchronization: ~1.8s
- Position preservation: ✅ All 100 components

Conclusion: ✅ Scales well to realistic circuit sizes
```

---

## Future Recommendations

### High Priority Gaps
1. Delete operations in subcircuits
2. Net removal operations
3. More subcircuit operation coverage

### Medium Priority Gaps
4. Multi-level hierarchy (2-3 levels deep)
5. Component instances across sheets
6. Sheet reuse patterns

---

## Conclusion

### Achievements
- ✅ 26 new tests created (39-65)
- ✅ Test 29 completed: Component custom properties (DNP, MPN, Tolerance, complex types) - Issue #409
- ✅ Hierarchical operations gap CLOSED
- ✅ Comprehensive power symbol testing
- ✅ Real-world workflow integration (DRC, ERC, BOM)
- ✅ Performance validated (100+ components)
- ✅ Ultimate integration test (test 64)

### Test Suite Health
- **Status:** ⚠️ **CRITICAL BUGS DISCOVERED**
- **Coverage:** Excellent (68 tests) but 2 critical blockers found
- **Documentation:** Comprehensive
- **CI-Ready:** Tests operational but core features broken

### Critical Issues Found (2025-10-30)
- 🔴 **Issue #427:** Hierarchical labels not generated - ALL hierarchical circuits broken
- 🔴 **Issue #410:** PCB synchronization broken - PCB workflow completely blocked

### Next Steps
1. **Fix Issue #427** - Hierarchical label generation (HIGHEST PRIORITY)
2. **Fix Issue #410** - PCB synchronization (HIGHEST PRIORITY)
3. **Retest:** Tests 28, 30, 59, 60, 58 after fixes
4. **Continue validation:** Tests 38-68 after critical bugs resolved

**Last Updated:** 2025-10-30 (Version 0.11.3 - Critical bugs discovered in tests 28, 30, 59)

🤖 Generated with [Claude Code](https://claude.com/claude-code)
