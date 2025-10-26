# Test 01: Blank Projects

## Purpose

Validates the absolute foundation of bidirectional sync: empty circuits with no components or nets.

## What This Tests

### Foundation Validation
- Python → KiCad generation works with empty circuit
- KiCad → Python import works with empty schematic
- Round-trip produces stable, valid output
- No crashes or errors on minimal input

### File Generation
- Valid `.kicad_pro` project file created
- Valid `.kicad_sch` schematic file created (empty, no components)
- Valid `.kicad_pcb` PCB file created (empty, no footprints)
- Valid `.kicad_prl` project-local settings file created
- Python file has valid syntax (can be imported)

## Test Cases

### Test 1.1: Generate Blank KiCad from Blank Python
```python
# Input: blank_circuit.py
@circuit
def blank():
    pass

# Expected Output:
# - blank.kicad_pro (valid project file)
# - blank.kicad_sch (valid schematic, no components)
# - blank.kicad_pcb (valid PCB file, no footprints)
# - blank.kicad_prl (project-local settings file)
```

**Validates**:
- Project file generation
- Schematic structure generation (empty but valid)
- PCB file generation (empty but valid)
- No components = no errors
- No footprints = no errors
- Valid KiCad 8 format for all files

### Test 1.2: Generate Blank Python from Blank KiCad
```python
# Input: blank.kicad_pro with:
#   - blank.kicad_sch (no components)
#   - blank.kicad_pcb (no footprints)

# Expected Output: blank_generated.py
@circuit
def blank():
    pass
```

**Validates**:
- Empty schematic parsing
- Empty PCB file handling
- Python code generation with no components
- Valid Python syntax
- Proper imports generated
- No spurious footprint data added

### Test 1.3: Round-Trip Blank Circuit
```python
# Cycle: Python → KiCad (schematic + PCB) → Python → KiCad
# Expected: All outputs identical (or semantically equivalent)
```

**Validates**:
- No data accumulation in schematic or PCB
- Stable round-trip behavior for both files
- Idempotency on blank projects
- PCB remains empty through cycles
- No spurious components or footprints added
- File structure preserved (except UUIDs)

## Files

### Manual Setup Required
You need to create:

1. **`fixtures/blank/blank.py`** - Blank Python circuit
   ```python
   from circuit_synth import circuit

   @circuit
   def blank():
       """Blank circuit for testing."""
       pass
   ```

2. **`fixtures/blank/blank.kicad_pro`** - Blank KiCad project (create in KiCad GUI)
   - Open KiCad
   - Create New Project → "blank"
   - Don't add any components
   - Save and close

### Test Files
- `test_blank_python_to_kicad.py` - Test 1.1
- `test_blank_kicad_to_python.py` - Test 1.2
- `test_blank_round_trip.py` - Test 1.3

## Expected Output

### Test 1.1 Output:
```
test_blank_python_to_kicad PASSED

✓ KiCad project generated
✓ Schematic is valid
✓ No components present
✓ File structure correct
```

### Test 1.2 Output:
```
test_blank_kicad_to_python PASSED

✓ Python code generated
✓ Code is syntactically valid
✓ Circuit function present
✓ No components defined
```

### Test 1.3 Output:
```
test_blank_round_trip PASSED

✓ Python → KiCad successful
✓ KiCad → Python successful
✓ Output matches original
✓ No data drift
```

## Debugging

### If Test 1.1 Fails:
- Check circuit_synth can generate projects
- Verify output directory permissions
- Look for exceptions in generation code

### If Test 1.2 Fails:
- Check KiCad project file is valid format
- Verify KiCadToPythonSyncer is working
- Look for AST parsing errors

### If Test 1.3 Fails:
- Compare original vs final Python (should be identical or equivalent)
- Check for added UUIDs or timestamps
- Look for whitespace changes

## Success Criteria

- ✅ All 3 tests passing
- ✅ No errors or warnings
- ✅ Generated files are valid
- ✅ Round-trip is stable (idempotent)

## Dependencies

- `circuit_synth` library
- KiCad 8+ (for manual fixture creation)
- Python 3.12+

---

**Status**: 🚧 Manual setup required
**Priority**: P0 (Critical)
**Estimated Setup Time**: 5 minutes
