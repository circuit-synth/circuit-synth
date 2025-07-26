# Test 04: Hierarchical Sheet Tests

## Purpose
This test validates the handling of hierarchical sheets in both directions - adding sheets from Python and from KiCad.

## Test Scenarios

### 4.1 Add Hierarchical Sheet from Python
- Create main circuit with power supply
- Add sub-sheet with voltage divider circuit
- Generate KiCad project with hierarchy
- Verify proper sheet structure in KiCad

### 4.2 Add Hierarchical Sheet from KiCad
- Start with flat circuit
- Add new hierarchical sheet in KiCad
- Add components to the sub-sheet
- Import back to Python
- Verify hierarchical structure is preserved

### 4.3 Modify Hierarchical Connections
- Change inter-sheet connections
- Add/remove hierarchical pins
- Verify changes sync properly

### 4.4 Multiple Hierarchy Levels
- Create nested hierarchical sheets (3 levels deep)
- Verify all levels sync correctly

## Files
- `circuit.py` - Initial circuit with hierarchical sheet
- `flat_circuit.py` - Flat circuit for KiCad hierarchy test
- `MANUAL_STEPS.md` - Manual instructions for KiCad operations
- `workspace/` - Working directory for test execution (gitignored)

## Running the Test
```bash
# For Python to KiCad hierarchy
python circuit.py

# For KiCad to Python hierarchy
python flat_circuit.py
# Then follow MANUAL_STEPS.md
```

## Expected Results
- Hierarchical sheets created in Python appear correctly in KiCad
- Hierarchical sheets created in KiCad import correctly to Python
- Inter-sheet connections are preserved
- Sheet instances and references work correctly