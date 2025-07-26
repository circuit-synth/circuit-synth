# Test 01: Single Resistor Circuit

## Purpose
This test validates the basic Circuit Synth to KiCad generation and synchronization for a simple single resistor circuit.

## Test Scenarios

### 1.1 Initial Generation
- Generate a single resistor circuit from Python
- Verify KiCad project is created correctly
- Verify resistor has proper reference (R1), value (1k), and connections

### 1.2 Re-run Stability
- Re-run the generation script
- Verify nothing changes in the KiCad files (idempotent operation)

### 1.3 Position Preservation
- Open in KiCad and manually move the resistor to a new position
- Re-run the generation script
- Verify the resistor position is NOT changed back to original
- Change net names of resistor in kicad
   - re-run circuit.py does not change net names and position of resistor
   - sync circuit.py with kicad project and see that net names in circuit.py change to match kicad project
- copy the single resistor in kicad, then rerun circuit.py to see there is only 1 resistor
- remove one label, connect the pin to the label it should be connected to

## Files
- `circuit.py` - Python circuit definition with single 1k resistor

## Reference example project
- the `example` project contains the reference project that should be generated on the first run of the script

## Expected Results
- All test scenarios should pass
- Manual position changes in KiCad should be preserved
- Re-running should not create duplicate components