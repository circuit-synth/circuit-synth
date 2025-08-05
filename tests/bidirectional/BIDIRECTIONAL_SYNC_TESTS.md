# Circuit-Synth Bidirectional Sync Test Plan

This document outlines comprehensive tests for validating the bidirectional synchronization between Python circuit definitions and KiCad projects, ensuring canonical matching and position preservation work correctly.

## Test Environment Setup

### Prerequisites
- Clean working directory
- KiCad 9.0+ installed
- circuit-synth development environment active
- `uv` package manager available

### Test Structure
Each test should:
1. Have clear success/failure criteria
2. Document expected vs. actual behavior
3. Validate both directions: Python → KiCad → Python
4. Check for unwanted side effects

---

## ~~Test 1: Generate New KiCad Project from Python (Simple)~~ ✅ COMPLETED

**Status**: ✅ **COMPLETED** - Basic Python → KiCad generation working  
**Objective**: Verify basic Python → KiCad generation works without warnings

### Steps:
1. ~~Create simple test circuit with basic components (resistor divider)~~
2. ~~Generate KiCad project: `circuit.generate_kicad_project("test_simple", force_regenerate=False)`~~
3. ~~Verify all files are created~~

### Expected Results:
- ✅ `.kicad_pro`, `.kicad_sch`, and subcircuit files created
- ✅ No warning messages about incomplete projects
- ✅ No netlist warnings
- ✅ All components have proper references
- ✅ Netlists (`.net` and `.json`) generated successfully

**Test Location**: `test_01_resistor_divider/`

---

## ~~Test 2: Import KiCad Project to Python and Generate Matching Code~~ ✅ COMPLETED

**Status**: ✅ **COMPLETED** - KiCad → Python import working correctly  
**Objective**: Verify KiCad → Python import generates correct circuit representation

### Steps:
1. ~~Use reference KiCad project (resistor divider)~~
2. ~~Import KiCad project to Python circuit representation~~
3. ~~Generate Python code that recreates the circuit~~
4. ~~Compare generated Python code with reference Python file~~
5. ~~Verify structural equivalence and correctness~~

### Expected Results:
- ✅ Imported circuit structure matches KiCad project
- ✅ Component references (R1, R2) correctly identified
- ✅ Net connections (VIN, MID, GND) properly reconstructed
- ✅ Generated Python code closely matches reference implementation
- ✅ Component values and footprints correctly imported

**Test Location**: `test_02_import_resistor_divider/test_kicad_import.py`

---

## ~~Test 3: Round-Trip Verification (Python → KiCad → Python)~~ ✅ COMPLETED

**Status**: ✅ **COMPLETED** - Round-trip conversion working with syntax fixes  
**Objective**: Verify round-trip stability and no data loss

### Steps:
1. ~~Using project from Test 1~~
2. ~~Import KiCad project back to Python circuit representation~~
3. ~~Compare original vs. imported circuit~~
4. ~~Re-generate KiCad project from imported circuit~~
5. ~~Verify no files changed~~

### Expected Results:
- ✅ Imported circuit matches original circuit structure
- ✅ Component references preserved
- ✅ Net connections identical
- ✅ Re-generation produces identical files (diff check)
- ✅ No warnings during import/export cycle

**Test Location**: `test_03_round_trip_python_kicad_python/test_round_trip.py`  
**Fix Applied**: Resolved syntax error in KiCad-to-Python converter function parameter generation

---

## Test 4: Complex Hierarchical File Structure with Nested Subcircuits

**Objective**: Verify KiCad-to-Python converter handles deep hierarchical structures with multiple subcircuit levels

### Steps:
1. **Create enhanced KiCad project with 3-level hierarchy:**
   - `main.kicad_sch` (top level)
   - `resistor_divider.kicad_sch` (contains resistors + capacitor bank subcircuit)
   - `capacitor_bank.kicad_sch` (contains filtering capacitors)
2. **Manual KiCad Setup:**
   - Add hierarchical sheet "CapacitorBank" inside resistor_divider
   - Create capacitor_bank subcircuit with 2-3 capacitors (C1: 100nF, C2: 10µF, C3: 1µF)
   - Connect capacitors between VCC/GND for filtering
   - Connect capacitor bank to resistor divider's power nets
3. Import using KiCadToPythonSyncer
4. Verify 3-level file structure generation and import chains

### Expected Results:
- ✅ Three Python files generated: `main.py`, `resistor_divider.py`, `capacitor_bank.py`
- ✅ **Import chain**: `main.py` → `resistor_divider.py` → `capacitor_bank.py`
- ✅ Each file contains only its level's circuit logic:
  - `main.py`: top-level nets and resistor_divider instantiation
  - `resistor_divider.py`: R1, R2 + capacitor_bank instantiation  
  - `capacitor_bank.py`: C1, C2, C3 filtering capacitors
- ✅ Proper hierarchical parameter passing through all levels
- ✅ All files syntactically valid and executable
- ✅ Deep import structure works: running main.py successfully imports all subcircuits

### File Structure Validation:
```python
# main.py should contain:
from resistor_divider import resistor_divider

@circuit 
def main_circuit():
    resistor_divider_instance = resistor_divider(vcc, gnd, out)

# resistor_divider.py should contain:
from capacitor_bank import capacitor_bank

@circuit
def resistor_divider(vcc, gnd, out):
    # R1, R2 definitions
    capacitor_bank_instance = capacitor_bank(vcc, gnd)

# capacitor_bank.py should contain:
@circuit
def capacitor_bank(vcc, gnd):
    # C1, C2, C3 filtering capacitors
```

### Circuit Description:
- **Main Circuit**: Power input, connects to resistor divider
- **Resistor Divider**: Voltage division (R1, R2) + power filtering (calls capacitor bank)
- **Capacitor Bank**: Multi-stage filtering (100nF, 10µF, 1µF bypass/decoupling)

**Test Location**: `test_04_complex_hierarchical_structure/`

---

## Test 5: Add Component in KiCad and Observe Python Code Update

**Objective**: Verify that manually adding components in KiCad properly updates Python code

### Steps:
1. Start with clean resistor divider KiCad project
2. **Manually add component in KiCad:**
   - Add capacitor C1 (100nF, 0603 footprint)
   - Connect C1 between OUT (MID) and GND nets
   - Save KiCad project
3. Re-import using KiCadToPythonSyncer
4. Compare new Python code with previous version
5. Verify new component appears correctly in Python representation

### Expected Results:
- ✅ New capacitor C1 appears in generated Python code
- ✅ C1 connections properly reconstructed (OUT and GND nets)
- ✅ C1 has correct properties: value="100nF", footprint="Capacitor_SMD:C_0603_1608Metric"
- ✅ Original R1, R2 components unchanged in Python code
- ✅ Net structure properly updated to include C1 connections
- ✅ Generated Python code remains syntactically valid and executable

### Validation:
```python
# Generated Python should now include:
C1 = Component("Device:C", ref="C1", value="100nF", footprint="Capacitor_SMD:C_0603_1608Metric")
# With connections:
C1[1] += OUT  # or MID net
C1[2] += GND
```

**Test Location**: `test_05_add_component_kicad/`

---

## Test 6: Add Component in Python and Observe KiCad Preservation

**Objective**: Verify that adding components in Python preserves existing KiCad work while adding new elements

### Steps:
1. Start with KiCad project that has manual positioning and annotations
2. **Modify Python code to add new component:**
   - Add inductor L1 (10µH, 0603 footprint) 
   - Connect L1 in series with R1 (between VCC and R1)
   - Regenerate KiCad project with `force_regenerate=False`
3. **Verify preservation:**
   - Check that manual component positions preserved
   - Check that manual annotations/text preserved
   - Verify new L1 component appears in KiCad
4. Open in KiCad and validate circuit integrity

### Expected Results:
- ✅ Existing R1, R2 positions and manual work preserved
- ✅ New inductor L1 appears in KiCad schematic
- ✅ L1 properly connected: VCC → L1 → R1 → (rest of circuit)
- ✅ No manual annotations lost
- ✅ No "incomplete project" warnings
- ✅ KiCad project opens without errors
- ✅ Net connections updated correctly to include L1

### Manual Work to Preserve:
- Component positions
- Wire routing preferences  
- Text annotations
- Power symbols placement

**Test Location**: `test_06_add_component_python/`

---

## Test 7: Swap Nested Schematic Hierarchy and Observe Python Import

**Objective**: Test Python import behavior when KiCad hierarchy structure is modified

### Steps:
1. Start with hierarchical KiCad project:
   - Main sheet contains resistor_divider subcircuit
   - Current: `main.kicad_sch` → `resistor_divider.kicad_sch`
2. **Manually restructure in KiCad:**
   - Make resistor_divider the top-level sheet
   - Make previous main circuit a subcircuit of resistor_divider
   - New: `resistor_divider.kicad_sch` → `main_circuit.kicad_sch`
   - Preserve all component connections
3. Import restructured project using KiCadToPythonSyncer
4. Analyze generated Python hierarchy

### Expected Results:
- ✅ Python import correctly identifies new top-level circuit (resistor_divider)
- ✅ Previous main circuit becomes a subcircuit in Python
- ✅ All component connections preserved during hierarchy swap
- ✅ Generated Python reflects new hierarchy: `resistor_divider()` calls `main_circuit()`
- ✅ No net or component data lost during restructuring
- ✅ Proper hierarchical labels and connections maintained

### Hierarchy Verification:
```python
# Should generate hierarchy like:
@circuit
def resistor_divider():  # Now top-level
    main_circuit_instance = main_circuit()  # Now subcircuit
    # resistor divider logic here
```

**Test Location**: `test_07_swap_kicad_hierarchy/`

---

## Test 8: Swap Python Circuit Hierarchy and Export to KiCad

**Objective**: Test KiCad export behavior when Python hierarchy is modified (challenging test for user input preservation)

### Steps:
1. Start with Python project where `main_circuit()` calls `resistor_divider()`
2. **Restructure Python hierarchy:**
   - Make `resistor_divider()` the top-level circuit
   - Make `main_circuit()` a subcircuit called by `resistor_divider()`
   - Preserve all component definitions and connections
3. Export to KiCad project
4. **Challenge**: Check if existing KiCad manual work is preserved
5. Compare with previous KiCad project structure

### Expected Results:
- ✅ KiCad project reflects new Python hierarchy structure
- ✅ resistor_divider becomes top-level .kicad_sch file
- ✅ main_circuit becomes hierarchical subcircuit sheet
- 🟡 **Challenging**: Manual KiCad positioning may be difficult to preserve during major restructuring
- ✅ All components and connections preserved in new structure
- ✅ Generated KiCad project is valid and opens without errors

### Preservation Assessment:
```
# This test may reveal limitations in user input preservation
# when major structural changes occur
Manual work preservation: ✅ Preserved / 🟡 Partially preserved / ❌ Lost
Component positions: ___
Manual annotations: ___
Wiring preferences: ___
```

**Note**: This test may identify areas where preservation vs. regeneration trade-offs need to be made explicit to users.

**Test Location**: `test_08_swap_python_hierarchy/`

---

## Test 9: Modify KiCad Project Manually and Test Round-Trip

**Objective**: Verify manual KiCad changes are preserved during Python updates

### Steps:
1. Open `test_simple.kicad_sch` in KiCad
2. **Manual Changes to Make:**
   - Move R1 to different position (record coordinates)
   - Add wire between VCC and R1 pin 1
   - Add power labels for VCC and GND
   - Add text annotation "Manual Addition"
   - Save project
3. Import to Python and verify manual changes detected
4. Re-run original Python script
5. Verify manual changes preserved

### Expected Results:
- ✅ Component positions preserved after Python re-generation
- ✅ Manual wires preserved
- ✅ Power labels preserved
- ✅ Text annotations preserved
- ✅ Only Python-defined components updated
- ✅ No force regeneration warnings

### Position Verification:
Record R1 position before/after:
```
Before: (x=___, y=___)
After:  (x=___, y=___)
Match: ✅/❌
```

**Test Location**: `test_09_manual_kicad_preservation/`

---

## Test 10: Import KiCad Project to Python - Manual Addition Detection

**Objective**: Determine expected behavior when KiCad project contains manual additions

### Steps:
1. Using modified project from Test 9
2. Import to Python circuit representation
3. Analyze what gets imported vs. ignored

### Expected Results:
- ✅ Core components (R1, R2) imported with correct values
- ✅ Net connections properly reconstructed  
- ❓ Manual wires: Should these create new net segments?
- ❓ Power labels: Should these become explicit net references?
- ❓ Text annotations: Should these be preserved in Python representation?

### Questions to Answer:
- What constitutes a "change" that should be imported?
- What constitutes "manual decoration" that should be preserved but not imported?
- How do we distinguish between the two?

**Test Location**: `test_10_manual_addition_detection/`

---

## Test 11: Re-run Python File and Verify KiCad Project Unchanged

**Objective**: Verify incremental updates don't overwrite manual work

### Steps:
1. Using manually modified project from Test 9
2. Re-run original Python script (no changes to Python code)
3. Verify KiCad project unchanged

### Expected Results:
- ✅ Manual component positions preserved
- ✅ Manual wires preserved
- ✅ Manual annotations preserved
- ✅ No "incomplete project" warnings
- ✅ No forced regeneration
- ✅ Only Python-managed elements updated (if any)

**Test Location**: `test_11_python_rerun_preservation/`

---

## Test 12: Add New Subcircuit to KiCad Project

**Objective**: Test hierarchical sheet handling and subcircuit import

### Steps:
1. Open KiCad project
2. **Manual Additions:**
   - Add new hierarchical sheet "PowerSupply"
   - Create power supply subcircuit with regulator
   - Connect to main circuit
   - Save project
3. Import to Python
4. Verify subcircuit structure

### Expected Results:
- ✅ New subcircuit imported as Python circuit function
- ✅ Subcircuit connections properly reconstructed
- ✅ Hierarchical labels become function parameters
- ✅ Original circuit structure preserved
- ✅ No import errors

**Test Location**: `test_12_add_subcircuit_kicad/`

---

## Test 13: Python Code Calls Circuit Twice - Duplicate Circuit Logic

**Objective**: Test proper handling of circuit instantiation patterns

### Steps:
1. **Modify Python code to call circuit multiple times:**
   ```python
   @circuit
   def power_stage():
       # Define power regulation circuit
       pass

   @circuit  
   def main_circuit():
       # Call power_stage twice for dual rails
       power_stage()  # First instance
       power_stage()  # Second instance
   ```
2. Generate KiCad project
3. Verify proper handling

### Expected Results:
- ✅ Two separate subcircuit sheets created OR proper instance handling
- ✅ No reference conflicts between instances
- ✅ Proper hierarchical organization
- ✅ Each instance independently manageable
- ✅ No warnings about duplicate circuits

**Test Location**: `test_13_duplicate_circuit_instantiation/`

---

## Test 14: Reference Change and Canonical Matching Test

**Objective**: Verify canonical matching works when users change component references

### Steps:
1. Generate initial project with specific references (R1, R2, C1)
2. **In KiCad, manually change references:**
   - R1 → R100
   - R2 → R200  
   - C1 → C100
3. Re-run Python script (with original references)
4. Verify canonical matching preserves positions

### Expected Results:
- ✅ Components matched by canonical properties (symbol + value + footprint)
- ✅ Position preservation despite reference changes
- ✅ No forced regeneration
- ✅ Reference changes preserved in KiCad
- ✅ Python can continue using original references

---

## Test 15: Stress Test - Complex Circuit Round-Trip

**Objective**: Test on realistic complex circuit with multiple subcircuits

### Steps:
1. Use existing `example_kicad_project.py` as base
2. Perform full round-trip test:
   - Generate → Manual KiCad edits → Import → Re-generate
3. Document any issues or edge cases

### Expected Results:
- ✅ All subcircuits handled correctly
- ✅ Complex hierarchical relationships preserved
- ✅ No data loss during round-trips
- ✅ Performance acceptable (< 10 seconds per operation)
- ✅ No memory leaks or resource issues

---

## Automated Test Validation

### Create Test Runner Script:
```bash
#!/bin/bash
# run_bidirectional_tests.sh

echo "🧪 Running Circuit-Synth Bidirectional Sync Tests"
echo "=================================================="

# Completed Tests
echo "Test 1: Basic Python→KiCad Generation..."
PRESERVE_FILES=1 uv run pytest tests/functional_tests/test_01_resistor_divider/ -v
echo "✅ Test 1 completed"

echo "Test 2: KiCad→Python Import..."
PRESERVE_FILES=1 uv run pytest tests/functional_tests/test_02_import_resistor_divider/ -v
echo "✅ Test 2 completed"

echo "Test 3: Round-Trip Verification..."
PRESERVE_FILES=1 uv run pytest tests/functional_tests/test_03_round_trip_python_kicad_python/ -v
echo "✅ Test 3 completed"

# New Tests (To Be Implemented)
echo "Test 4: Single File Generation..."
# PRESERVE_FILES=1 uv run pytest tests/functional_tests/test_04_single_file_generation/ -v
echo "⏳ Test 4 pending implementation"

echo "Test 5: Add Component in KiCad..."
# PRESERVE_FILES=1 uv run pytest tests/functional_tests/test_05_add_component_kicad/ -v
echo "⏳ Test 5 pending implementation"

echo "Test 6: Add Component in Python..."
# PRESERVE_FILES=1 uv run pytest tests/functional_tests/test_06_add_component_python/ -v
echo "⏳ Test 6 pending implementation"

echo "Test 7: Swap KiCad Hierarchy..."
# PRESERVE_FILES=1 uv run pytest tests/functional_tests/test_07_swap_kicad_hierarchy/ -v
echo "⏳ Test 7 pending implementation"

echo "Test 8: Swap Python Hierarchy..."
# PRESERVE_FILES=1 uv run pytest tests/functional_tests/test_08_swap_python_hierarchy/ -v
echo "⏳ Test 8 pending implementation"

echo "🏁 Functional Tests Summary: 3/8 core tests completed"
```

### Success Criteria:
- [ ] All 15 tests pass without critical errors
- [ ] No data loss in any round-trip operation
- [ ] Manual KiCad work always preserved
- [ ] Canonical matching works in all scenarios
- [ ] Performance meets requirements
- [ ] Zero warnings in normal operation
- [x] Tests 1-3: Basic functionality working (completed)
- [ ] Tests 4-8: Advanced bidirectional sync scenarios
- [ ] Tests 9-15: Edge cases and preservation scenarios

### Test Documentation:
Each test should produce:
- Screenshots of before/after KiCad projects
- Diff outputs showing preserved/changed elements
- Performance timing data
- Memory usage reports
- Complete log files for debugging

---

## Test Results Summary

| Test | Description | Status | Issues Found | Notes |
|------|-------------|--------|--------------|-------|
| 1    | Basic Python→KiCad Generation | ✅ | None | Working | 
| 2    | KiCad→Python Import | ✅ | None | Working |
| 3    | Round-Trip Verification | ✅ | Syntax fix applied | Working |
| 4    | Single File Generation | ⏳ | TBD | Pending |
| 5    | Add Component in KiCad | ⏳ | TBD | Pending |
| 6    | Add Component in Python | ⏳ | TBD | Pending |
| 7    | Swap KiCad Hierarchy | ⏳ | TBD | Pending |
| 8    | Swap Python Hierarchy | ⏳ | TBD | Pending |
| 9    | Manual KiCad Preservation | ⏳ | TBD | Pending |
| 10   | Manual Addition Detection | ⏳ | TBD | Pending |
| 11   | Python Rerun Preservation | ⏳ | TBD | Pending |
| 12   | Add Subcircuit in KiCad | ⏳ | TBD | Pending |
| 13   | Duplicate Circuit Logic | ⏳ | TBD | Pending |
| 14   | Reference Change Matching | ⏳ | TBD | Pending |
| 15   | Complex Circuit Stress Test | ⏳ | TBD | Pending |

### Critical Issues:
- Issue 1: Description and impact
- Issue 2: Description and impact

### Performance Metrics:
- Generation time: ___ms
- Import time: ___ms  
- Memory usage: ___MB

### Recommendations:
- Fix X before production release
- Consider optimization in Y area
```

---

## Implementation Priority

### Phase 1: Core Bidirectional Sync (COMPLETED ✅)
- [x] Test 1: Basic Python→KiCad generation
- [x] Test 2: KiCad→Python import  
- [x] Test 3: Round-trip verification

### Phase 2: Advanced Sync Scenarios (NEXT)
- [ ] Test 4: Single file generation validation
- [ ] Test 5: KiCad component addition workflow
- [ ] Test 6: Python component addition workflow
- [ ] Test 7: KiCad hierarchy restructuring
- [ ] Test 8: Python hierarchy restructuring

### Phase 3: Edge Cases & Preservation (FUTURE)
- [ ] Test 9-11: Manual work preservation scenarios
- [ ] Test 12-13: Complex hierarchical patterns
- [ ] Test 14-15: Canonical matching and stress testing

### Development Notes:
- Use `PRESERVE_FILES=1` environment variable for manual inspection
- Each test should be isolated in its own directory
- Generate comparison reports for before/after states
- Document any limitations discovered during implementation

---

This comprehensive test plan ensures robust validation of the bidirectional sync functionality and helps identify edge cases before they impact users. The completed tests (1-3) provide a solid foundation, and the remaining tests (4-8) will validate advanced workflow scenarios that users will encounter in real-world usage.