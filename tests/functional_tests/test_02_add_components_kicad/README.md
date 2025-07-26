# Test 02: Add Components in KiCad and Sync Back

## Purpose
This test validates the ability to add components in KiCad and synchronize those changes back to the Python circuit definition.

## Test Scenarios

### 2.1 Change Net Names in KiCad
- Start with single resistor circuit
- Open in KiCad and rename nets (e.g., VCC -> +3V3, GND -> GND1)
- Re-import to Python
- Verify net names are updated in Python circuit

### 2.2 Add Second Resistor in KiCad
- Add a copy of R1 (creating R2) in KiCad
- Connect R2 in parallel or series with R1
- Re-import to Python
- Verify Python circuit now has two resistors with correct connections

### 2.3 Verify Round-Trip Consistency
- After importing KiCad changes to Python
- Re-export from Python to KiCad
- Verify no changes occur (stable round-trip)

## Files
- `circuit.py` - Initial Python circuit (single resistor)
- `test_script.py` - Automated test script
- `modified_schematics/` - Pre-modified KiCad files for testing
- `workspace/` - Working directory for test execution (gitignored)

## Running the Test
```bash
python test_script.py
```

## Expected Results
- Net name changes in KiCad should reflect in Python
- New components added in KiCad should appear in Python
- Round-trip sync should be stable (no data loss)