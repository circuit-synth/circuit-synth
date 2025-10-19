# PRD: Phase 0 Integration Tests - JSON as Canonical Format

**Issue:** #212
**Epic:** #208 (Phase 0: Make JSON the Canonical Format)
**Branch:** `feature/issue-212-phase0-integration-tests`
**Created:** 2025-10-19
**Status:** In Development
**Dependencies:**
- ✅ #209 - Automatic JSON generation (COMPLETE)
- ✅ #210 - KiCad → JSON export (COMPLETE)
- ✅ #211 - KiCadToPythonSyncer refactor (COMPLETE)

---

## Executive Summary

This PRD defines comprehensive integration tests that verify JSON is the canonical data format for ALL circuit-synth conversions, completing Phase 0. These tests prove that the JSON-first architecture is working correctly and that no conversion bypasses the canonical JSON format.

**Goal:** Create a master integration test suite with 15+ tests that verifies all Phase 0 success criteria and completes Epic #208.

**Success Metric:** All tests pass, proving JSON is the single source of truth for circuit-synth data flows.

---

## Problem Statement

### Current State

Phase 0 has been implemented in three stages:
1. **#209 (COMPLETE):** `generate_kicad_project()` automatically creates JSON in project directory
2. **#210 (COMPLETE):** KiCad schematics can be exported to JSON format
3. **#211 (COMPLETE):** `KiCadToPythonSyncer` uses JSON as primary input (with backward compatibility)

### The Gap

While each piece has been implemented and unit tested individually, we lack **comprehensive integration tests** that verify:

- The complete data flow from Python → JSON → KiCad → JSON → Python
- JSON is truly canonical (never bypassed)
- Round-trip consistency is maintained
- Performance is acceptable for real-world circuits
- All Phase 0 success criteria are met

**Without these tests, we cannot confidently declare Phase 0 complete.**

---

## Phase 0 Success Criteria

From Epic #208, these are the criteria we must verify:

- ✅ `generate_kicad_project()` automatically creates JSON in project directory
- ✅ JSON path returned in generation result
- ✅ `KiCadToPythonSyncer` accepts JSON as input
- ✅ KiCad projects can be exported to JSON format
- ✅ All conversions flow through JSON (no .net bypassing)
- ✅ Round-trip tests pass: Python → JSON → Python

**Our integration tests must verify ALL of these criteria.**

---

## Test Strategy

### Testing Pyramid for Phase 0

```
        /\
       /  \  Integration Tests (this PRD)
      /    \  ← Comprehensive workflow testing
     /------\
    /        \ Unit Tests (already complete)
   /          \ ← Individual component testing
  /____________\
```

### Coverage Goals

1. **Workflow Coverage:** Test all major data flows
2. **Format Coverage:** Test both flat and hierarchical circuits
3. **Scale Coverage:** Test small to large circuits (100+ components)
4. **Error Coverage:** Test failure modes and edge cases
5. **Compatibility Coverage:** Test backward compatibility

---

## Comprehensive Test Plan

### Test Suite Organization

**File:** `tests/integration/test_phase0_json_canonical.py`

This will be the **master integration test suite** for Phase 0 with 15+ comprehensive tests.

### Test Categories

#### Category 1: Core Workflow Tests (Tests 1-4)
- Verify each major conversion path works end-to-end
- Test Python → JSON, KiCad → JSON, JSON → Python

#### Category 2: Canonical Format Tests (Tests 5-7)
- Verify JSON is never bypassed
- Test JSON schema consistency
- Validate JSON structure

#### Category 3: Round-Trip Tests (Tests 8-10)
- Complete round-trip: Python → JSON → Python
- Data preservation verification
- Semantic equivalence testing

#### Category 4: Scale & Performance Tests (Tests 11-12)
- Large circuit handling (100+ components)
- Hierarchical circuit testing
- Performance benchmarks

#### Category 5: Error & Edge Cases (Tests 13-15)
- Missing file handling
- Invalid JSON handling
- Backward compatibility

---

## Detailed Test Specifications

### Test 1: Automatic JSON Generation

**Objective:** Verify #209 implementation - automatic JSON creation in project directory

**Test Steps:**
1. Create simple Python circuit with @circuit decorator
2. Call `generate_kicad_project("test_board")`
3. Verify return value structure (dict with success, json_path, project_path)
4. Verify JSON file created in project directory
5. Verify JSON path naming convention: `{project_name}.json`
6. Verify JSON is valid circuit-synth schema

**Expected Result:**
- `result["success"]` is `True`
- `result["json_path"]` exists and points to `test_board/test_board.json`
- JSON file exists and validates against schema
- JSON contains all circuit components and nets

**Acceptance Criteria:**
- JSON auto-generated ✅
- JSON path in result ✅
- JSON in project directory (not temp file) ✅

---

### Test 2: JSON Path Returned in Result

**Objective:** Verify JSON path is accessible for downstream tools

**Test Steps:**
1. Generate KiCad project with Python circuit
2. Extract `json_path` from result
3. Verify path is absolute
4. Verify path points to existing file
5. Load and validate JSON content

**Expected Result:**
- JSON path is Path object (or str)
- Path is absolute, not relative
- File exists at path
- JSON is valid

**Acceptance Criteria:**
- JSON path available in result ✅
- Path is correct and accessible ✅

---

### Test 3: KiCadToPythonSyncer Accepts JSON Input

**Objective:** Verify #211 implementation - syncer accepts JSON as primary input

**Test Steps:**
1. Create JSON netlist file manually
2. Initialize `KiCadToPythonSyncer` with JSON path
3. Run `syncer.sync()`
4. Verify Python code generated
5. Verify no .net file was used
6. Verify no deprecation warning raised

**Expected Result:**
- Syncer accepts JSON path without error
- Python code generated successfully
- Generated code contains components from JSON
- No warnings about deprecated input

**Acceptance Criteria:**
- JSON input works ✅
- No .net file needed ✅
- Modern API preferred ✅

---

### Test 4: KiCad to JSON Export

**Objective:** Verify #210 implementation - KiCad projects export to JSON

**Test Steps:**
1. Create KiCad project using `generate_kicad_project()`
2. Get JSON path from result
3. Load JSON and verify it matches circuit-synth schema
4. Verify components dict (not list)
5. Verify nets dict (not list)
6. Verify required fields present

**Expected Result:**
- JSON exports successfully
- Schema matches circuit-synth format
- Components keyed by reference
- Nets keyed by name
- All required fields present

**Acceptance Criteria:**
- KiCad → JSON works ✅
- Schema is correct ✅
- Dict structure (not lists) ✅

---

### Test 5: No .net File Bypassing

**Objective:** Verify JSON is the only path for KiCad → Python conversion

**Test Steps:**
1. Mock/patch KiCad netlist parser
2. Run complete KiCad → Python workflow using JSON path
3. Verify netlist parser was NOT called
4. Verify only JSON loading was used

**Expected Result:**
- Netlist parser never invoked
- JSON loader called instead
- Workflow completes successfully using only JSON

**Acceptance Criteria:**
- No .net file parsing in JSON workflow ✅
- JSON is canonical path ✅

---

### Test 6: JSON Schema Consistency

**Objective:** Verify all JSON outputs match circuit-synth schema

**Test Steps:**
1. Generate JSON from Python circuit (via `generate_json_netlist()`)
2. Generate JSON from KiCad project
3. Compare schema structure
4. Verify both have same fields
5. Verify both use dict format for components/nets

**Expected Result:**
- Both JSONs have identical schema
- Both use dict format (not lists)
- Field names match (symbol, ref, value, footprint)
- Net connections have same structure

**Acceptance Criteria:**
- Schema consistent across sources ✅
- JSON is truly canonical format ✅

---

### Test 7: JSON Validates Against Schema

**Objective:** Verify all generated JSON is valid

**Test Steps:**
1. Generate JSON from various sources
2. Validate required fields: name, components, nets
3. Validate types: components is dict, nets is dict
4. Validate component fields: symbol, ref, value
5. Validate net connections: component, pin

**Expected Result:**
- All required fields present
- Types are correct
- No missing data
- Schema validation passes

**Acceptance Criteria:**
- JSON validation works ✅
- All JSONs are valid ✅

---

### Test 8: Round-Trip: Python → JSON → Python

**Objective:** Verify complete round-trip preserves circuit data

**Test Steps:**
1. Create Python circuit with @circuit decorator
2. Generate JSON via `generate_kicad_project()`
3. Load JSON and sync back to Python using `KiCadToPythonSyncer`
4. Compare original and generated Python (semantic equivalence)
5. Verify all components preserved
6. Verify all nets preserved
7. Verify component properties preserved

**Expected Result:**
- Round-trip completes without errors
- Component count matches
- Net count matches
- Component values preserved
- Net connections preserved
- Semantic equivalence achieved

**Acceptance Criteria:**
- Round-trip works ✅
- Data preservation verified ✅
- No data loss ✅

---

### Test 9: Round-Trip Data Preservation

**Objective:** Verify specific data fields are preserved

**Test Steps:**
1. Create circuit with specific component properties:
   - Reference designators (R1, C1, U1)
   - Values (10k, 100nF, ESP32-C6)
   - Footprints (R_0603, C_0603)
2. Round-trip through JSON
3. Verify each property preserved exactly

**Expected Result:**
- References preserved: R1 → R1
- Values preserved: 10k → 10k
- Footprints preserved: R_0603 → R_0603
- Net names preserved: VCC → VCC

**Acceptance Criteria:**
- All properties preserved ✅
- No data corruption ✅

---

### Test 10: Semantic Equivalence Verification

**Objective:** Verify circuits are functionally identical after round-trip

**Test Steps:**
1. Create circuit with specific connectivity
2. Round-trip through JSON
3. Extract connectivity graph from both
4. Compare graphs for semantic equivalence
5. Verify same components connected to same nets

**Expected Result:**
- Connectivity graph identical
- R1 pin 1 → VCC (before and after)
- R1 pin 2 → MID (before and after)
- All connections preserved

**Acceptance Criteria:**
- Semantic equivalence achieved ✅
- Connectivity preserved ✅

---

### Test 11: Hierarchical Circuit JSON

**Objective:** Verify JSON handles hierarchical designs

**Test Steps:**
1. Create hierarchical circuit with subcircuits
2. Generate JSON
3. Verify subcircuits array present
4. Verify nested circuit structure preserved
5. Round-trip and verify hierarchy preserved

**Expected Result:**
- JSON has subcircuits array
- Nested structure preserved
- Hierarchy maintained through round-trip

**Acceptance Criteria:**
- Hierarchical circuits supported ✅
- Subcircuits in JSON ✅

---

### Test 12: Large Circuit Performance

**Objective:** Verify JSON workflow scales to real-world circuits

**Test Steps:**
1. Create circuit with 100+ components
2. Measure time for Python → JSON
3. Measure time for JSON → Python
4. Verify total time < 10 seconds
5. Verify memory usage reasonable

**Expected Result:**
- 100 component circuit processes in < 10s
- No memory issues
- No performance degradation

**Acceptance Criteria:**
- Performance acceptable ✅
- Scales to real circuits ✅

---

### Test 13: Error Handling - Missing Files

**Objective:** Verify graceful error handling

**Test Steps:**
1. Try to load non-existent JSON file
2. Verify structured error returned
3. Verify error message is helpful
4. Try to sync with missing JSON
5. Verify appropriate exception raised

**Expected Result:**
- FileNotFoundError raised with clear message
- No crashes or stack traces
- Error message points to missing file

**Acceptance Criteria:**
- Error handling works ✅
- Messages are helpful ✅

---

### Test 14: Error Handling - Invalid JSON

**Objective:** Verify JSON validation catches errors

**Test Steps:**
1. Create malformed JSON file
2. Try to load with syncer
3. Verify JSONDecodeError or ValueError raised
4. Create valid JSON with missing required fields
5. Verify validation error raised

**Expected Result:**
- Malformed JSON caught
- Missing fields detected
- Clear error messages
- No silent failures

**Acceptance Criteria:**
- JSON validation works ✅
- Errors caught early ✅

---

### Test 15: Backward Compatibility

**Objective:** Verify legacy KiCad project input still works

**Test Steps:**
1. Create KiCad project
2. Pass .kicad_pro path to KiCadToPythonSyncer (legacy API)
3. Verify DeprecationWarning raised
4. Verify sync still works
5. Verify JSON auto-generated internally
6. Verify output identical to JSON input path

**Expected Result:**
- Legacy API works
- Deprecation warning shown
- JSON auto-generated
- Same result as JSON input

**Acceptance Criteria:**
- Backward compatibility maintained ✅
- Deprecation warning shown ✅
- Users can migrate gradually ✅

---

## Test Data Requirements

### Small Test Circuits (Tests 1-7)

Simple resistor divider:
```python
@circuit(name="voltage_divider")
def voltage_divider():
    r1 = Component("Device:R", ref="R1", value="10k", footprint="R_0603")
    r2 = Component("Device:R", ref="R2", value="10k", footprint="R_0603")
    vin = Net("VIN")
    vout = Net("VOUT")
    gnd = Net("GND")
    r1[1] += vin
    r1[2] += vout
    r2[1] += vout
    r2[2] += gnd
    return r1, r2
```

### Medium Test Circuits (Tests 8-10)

Decoupling network:
```python
@circuit(name="decoupling")
def decoupling():
    u1 = Component("RF_Module:ESP32-C6-MINI-1", ref="U1")
    c1 = Component("Device:C", ref="C1", value="100nF", footprint="C_0603")
    c2 = Component("Device:C", ref="C2", value="10uF", footprint="C_0805")
    vcc = Net("VCC_3V3")
    gnd = Net("GND")
    # Connections...
```

### Hierarchical Test Circuits (Test 11)

Main circuit with power supply subcircuit:
```python
@circuit(name="main")
def main():
    # Use subcircuit
    ps = power_supply()
    # Main circuit components
```

### Large Test Circuits (Test 12)

ESP32 dev board with 100+ components (USB, power, sensors, LEDs, etc.)

---

## Implementation Plan

### Phase 1: Test Infrastructure (Day 1)

**Create:** `tests/integration/helpers/phase0_helpers.py`

Helper functions:
- `create_simple_circuit()` - Basic resistor divider
- `create_medium_circuit()` - Decoupling network
- `create_hierarchical_circuit()` - Multi-level design
- `create_large_circuit(n_components)` - Scalable test circuit
- `validate_json_schema(json_path)` - Schema validation
- `compare_circuits_semantic(c1, c2)` - Semantic comparison
- `measure_performance(func)` - Performance timing

### Phase 2: Core Tests (Day 2)

Implement Tests 1-7 (core workflow and canonical format tests)

**Create:** `tests/integration/test_phase0_json_canonical.py`

### Phase 3: Round-Trip Tests (Day 3)

Implement Tests 8-10 (round-trip and data preservation tests)

### Phase 4: Scale & Error Tests (Day 4)

Implement Tests 11-15 (hierarchical, performance, error handling)

### Phase 5: Validation & PR (Day 5)

- Run all tests
- Fix any failures
- Verify Phase 0 completion criteria
- Create PR

---

## Test Implementation Template

```python
"""
Phase 0 Integration Tests: JSON as Canonical Format

These tests verify that JSON is the canonical format for ALL circuit-synth
conversions, completing Epic #208 (Phase 0).

Success criteria:
- Python → JSON automatic generation works
- KiCad → JSON export works
- JSON → Python sync works
- Round-trip preserves data
- No .net file bypassing
- JSON schema is consistent
"""

import pytest
import tempfile
import json
from pathlib import Path
from circuit_synth import Circuit, Component, Net, circuit
from circuit_synth.tools.kicad_integration.kicad_to_python_sync import (
    KiCadToPythonSyncer
)

# Import helpers
from .helpers.phase0_helpers import (
    create_simple_circuit,
    create_medium_circuit,
    create_hierarchical_circuit,
    create_large_circuit,
    validate_json_schema,
    compare_circuits_semantic,
    measure_performance,
)


class TestPhase0JSONCanonical:
    """Master test suite for Phase 0 completion."""

    def test_01_automatic_json_generation(self, tmp_path):
        """Test that generate_kicad_project() automatically creates JSON."""
        # Create circuit
        circuit = create_simple_circuit()

        # Generate project
        result = circuit.generate_kicad_project(
            str(tmp_path / "test_board"),
            generate_pcb=False
        )

        # Verify result structure
        assert result["success"] is True
        assert "json_path" in result

        # Verify JSON created
        json_path = Path(result["json_path"])
        assert json_path.exists()
        assert json_path.name == "test_board.json"

        # Verify JSON is valid
        assert validate_json_schema(json_path)

    # ... more tests ...
```

---

## Acceptance Criteria

### Functional Requirements

- ✅ **FR1:** All 15 integration tests implemented
- ✅ **FR2:** All tests pass consistently
- ✅ **FR3:** Test coverage includes all Phase 0 features
- ✅ **FR4:** Round-trip test verifies data preservation
- ✅ **FR5:** Performance test verifies scalability
- ✅ **FR6:** Error tests verify graceful failure
- ✅ **FR7:** Backward compatibility verified

### Non-Functional Requirements

- ✅ **NFR1:** Tests run in < 60 seconds total
- ✅ **NFR2:** Tests are deterministic (no flaky tests)
- ✅ **NFR3:** Test code is well-documented
- ✅ **NFR4:** Helper functions are reusable
- ✅ **NFR5:** Test data is realistic
- ✅ **NFR6:** No external dependencies required

### Quality Gates

1. **All 15 tests pass:** No failures or skips
2. **Coverage:** All Phase 0 criteria tested
3. **Performance:** Tests complete in < 60s
4. **Documentation:** Clear test descriptions
5. **Review:** PR approved by maintainer

---

## Success Metrics

### Phase 0 Completion Verification

When all tests pass, we can verify:

| Criterion | Test(s) | Status |
|-----------|---------|--------|
| JSON auto-generated | Test 1, 2 | ✅ |
| JSON path in result | Test 2 | ✅ |
| Syncer accepts JSON | Test 3 | ✅ |
| KiCad → JSON export | Test 4 | ✅ |
| No .net bypassing | Test 5 | ✅ |
| Round-trip works | Test 8, 9, 10 | ✅ |
| Schema consistent | Test 6, 7 | ✅ |
| Hierarchical support | Test 11 | ✅ |
| Performance OK | Test 12 | ✅ |
| Error handling | Test 13, 14 | ✅ |
| Backward compatible | Test 15 | ✅ |

**When all tests pass, Phase 0 is COMPLETE! 🎉**

---

## Dependencies and Risks

### Dependencies

1. **#209 (COMPLETE)** - Automatic JSON generation
2. **#210 (COMPLETE)** - KiCad → JSON export
3. **#211 (COMPLETE)** - KiCadToPythonSyncer refactor

All dependencies are met. ✅

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Tests reveal bugs in implementations | Medium | High | Fix bugs, update tests |
| Round-trip test fails | Medium | High | Debug data flow, fix converters |
| Performance test fails | Low | Medium | Optimize JSON generation |
| Flaky tests | Low | Medium | Use deterministic test data |

---

## Timeline

**Total: 5 days**

- **Day 1:** Test infrastructure and helpers
- **Day 2:** Core workflow tests (Tests 1-7)
- **Day 3:** Round-trip tests (Tests 8-10)
- **Day 4:** Scale and error tests (Tests 11-15)
- **Day 5:** Validation and PR

---

## References

### Documentation
- `docs/JSON_SCHEMA.md` - Circuit-synth JSON schema
- `docs/PRD_KICAD_SYNCER_REFACTOR.md` - #211 PRD
- Epic #208 - Phase 0 goals and criteria

### Code Files
- `src/circuit_synth/core/circuit.py` - Circuit class with JSON generation
- `src/circuit_synth/tools/kicad_integration/kicad_to_python_sync.py` - Refactored syncer
- `src/circuit_synth/core/netlist_exporter.py` - JSON netlist exporter

### Existing Tests
- `tests/integration/test_roundtrip_preservation.py` - Round-trip patterns
- `tests/integration/test_kicad_sync_integration.py` - Sync patterns

### GitHub Issues
- Issue #212 - This task
- Issue #209 - Automatic JSON generation (COMPLETE)
- Issue #210 - KiCad → JSON export (COMPLETE)
- Issue #211 - Syncer refactor (COMPLETE)
- Epic #208 - Phase 0: Make JSON the Canonical Format

---

**Document Version:** 1.0
**Last Updated:** 2025-10-19
**Author:** Claude Code
**Status:** Ready for Implementation
