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

## Test 1: Generate New KiCad Project from Python (Simple)

**Objective**: Verify basic Python → KiCad generation works without warnings

### Steps:
1. Create simple test circuit with basic components (resistor divider)
2. Generate KiCad project: `circuit.generate_kicad_project("test_simple", force_regenerate=False)`
3. Verify all files are created

### Expected Results:
- ✅ `.kicad_pro`, `.kicad_sch`, and subcircuit files created
- ✅ No warning messages about incomplete projects
- ✅ No netlist warnings
- ✅ All components have proper references
- ✅ Netlists (`.net` and `.json`) generated successfully

### Test Code:
```python
#!/usr/bin/env python3
from circuit_synth import *

# Simple resistor divider circuit
@circuit
def simple_resistor_divider():
    VCC = Net('VCC')
    GND = Net('GND') 
    OUT = Net('OUT')
    
    R1 = Component("Device:R", ref="R1", value="10K", footprint="Resistor_SMD:R_0603_1608Metric")
    R2 = Component("Device:R", ref="R2", value="10K", footprint="Resistor_SMD:R_0603_1608Metric")
    
    R1[1] += VCC
    R1[2] += OUT
    R2[1] += OUT  
    R2[2] += GND

if __name__ == '__main__':
    circuit = simple_resistor_divider()
    circuit.generate_kicad_netlist("test_simple.net")
    circuit.generate_json_netlist("test_simple.json")
    circuit.generate_kicad_project("test_simple", force_regenerate=False)
```

---

## Test 2: Import KiCad Project to Python and Generate Matching Code

**Objective**: Verify KiCad → Python import generates correct circuit representation

### Steps:
1. Use reference KiCad project (resistor divider)
2. Import KiCad project to Python circuit representation
3. Generate Python code that recreates the circuit
4. Compare generated Python code with reference Python file
5. Verify structural equivalence and correctness

### Expected Results:
- ✅ Imported circuit structure matches KiCad project
- ✅ Component references (R1, R2) correctly identified
- ✅ Net connections (VIN, MID, GND) properly reconstructed
- ✅ Generated Python code closely matches reference implementation
- ✅ Component values and footprints correctly imported

### Test Code:
```python
#!/usr/bin/env python3
from circuit_synth import import_kicad_project

# Import KiCad project and generate Python code
imported_circuit = import_kicad_project("reference_resistor_divider")
generated_code = imported_circuit.generate_python_code()

# Compare with reference implementation
with open("reference_resistor_divider.py", "r") as f:
    reference_code = f.read()

# Validate structural equivalence
assert_circuit_equivalence(imported_circuit, reference_circuit)
```

---

## Test 3: Round-Trip Verification (Python → KiCad → Python)

**Objective**: Verify round-trip stability and no data loss

### Steps:
1. Using project from Test 1
2. Import KiCad project back to Python circuit representation
3. Compare original vs. imported circuit
4. Re-generate KiCad project from imported circuit
5. Verify no files changed

### Expected Results:
- ✅ Imported circuit matches original circuit structure
- ✅ Component references preserved
- ✅ Net connections identical
- ✅ Re-generation produces identical files (diff check)
- ✅ No warnings during import/export cycle

### Validation Commands:
```bash
# Before import
cp -r test_simple test_simple_backup

# After round-trip
diff -r test_simple test_simple_backup
# Should show no differences in .kicad_sch files
```

---

## Test 4: Modify KiCad Project Manually and Test Round-Trip

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

---

## Test 5: Import KiCad Project to Python - Should There Be Changes?

**Objective**: Determine expected behavior when KiCad project contains manual additions

### Steps:
1. Using modified project from Test 4
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

---

## Test 6: Re-run Python File and Verify KiCad Project Unchanged

**Objective**: Verify incremental updates don't overwrite manual work

### Steps:
1. Using manually modified project from Test 4
2. Re-run original Python script (no changes to Python code)
3. Verify KiCad project unchanged

### Expected Results:
- ✅ Manual component positions preserved
- ✅ Manual wires preserved
- ✅ Manual annotations preserved
- ✅ No "incomplete project" warnings
- ✅ No forced regeneration
- ✅ Only Python-managed elements updated (if any)

---

## Test 7: Add Component to Resistor Divider in KiCad

**Objective**: Test importing manually added components from KiCad

### Steps:
1. Open KiCad project from previous test
2. **Manual Additions:**
   - Add capacitor C1 (100nF, 0603 footprint) 
   - Connect C1 between OUT and GND
   - Add reference designator and value
   - Save project
3. Import to Python
4. Verify new component appears in Python representation

### Expected Results:
- ✅ C1 appears in imported Python circuit
- ✅ C1 connections properly reconstructed
- ✅ C1 has correct reference, value, and footprint
- ✅ Original R1, R2 unchanged
- ✅ No import errors or warnings

### Import Verification:
```python
# Check that imported circuit contains C1
imported_circuit = import_from_kicad("test_simple")
components = get_components(imported_circuit)
assert "C1" in components
assert components["C1"].value == "100nF"
```

---

## Test 7: Add New Subcircuit to KiCad Project

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

---

## Test 8: Python Code Calls Circuit Twice - Duplicate Circuit Logic

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

---

## Test 9: Reference Change and Canonical Matching Test

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

## Test 10: Stress Test - Complex Circuit Round-Trip

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

# Test 1: Basic generation
echo "Test 1: Basic Generation..."
uv run python test_01_basic_generation.py
echo "✅ Test 1 completed"

# Test 1.5: Round-trip stability  
echo "Test 1.5: Round-trip Stability..."
# Add commands for round-trip verification
echo "✅ Test 1.5 completed"

# Continue for all tests...
```

### Success Criteria:
- [ ] All 10 tests pass without critical errors
- [ ] No data loss in any round-trip operation
- [ ] Manual KiCad work always preserved
- [ ] Canonical matching works in all scenarios
- [ ] Performance meets requirements
- [ ] Zero warnings in normal operation

### Test Documentation:
Each test should produce:
- Screenshots of before/after KiCad projects
- Diff outputs showing preserved/changed elements
- Performance timing data
- Memory usage reports
- Complete log files for debugging

---

## Test Results Template

```markdown
## Test Results Summary

| Test | Status | Issues Found | Notes |
|------|--------|--------------|-------|
| 1    | ✅/❌   |              |       |
| 1.5  | ✅/❌   |              |       |
| 2    | ✅/❌   |              |       |
| ...  | ✅/❌   |              |       |

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

This comprehensive test plan ensures robust validation of the bidirectional sync functionality and helps identify edge cases before they impact users.