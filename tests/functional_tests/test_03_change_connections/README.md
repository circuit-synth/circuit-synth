# Test 03: Change Connections and Verify Sync

## Purpose
This test validates the ability to change component connections in both KiCad and Python, ensuring proper synchronization of wiring changes.

## Test Scenarios

### 3.1 Initial Two-Resistor Circuit
- Start with two resistors in series (R1 and R2)
- R1: VCC to OUT
- R2: OUT to GND
- Generate KiCad project

### 3.2 Change to Parallel Configuration in KiCad
- Open in KiCad and rewire resistors to parallel
- Both R1 and R2: VCC to GND
- Remove OUT net
- Re-import to Python
- Verify connections are updated correctly

### 3.3 Change Back to Series in Python
- Modify Python circuit back to series configuration
- Re-export to KiCad
- Verify KiCad schematic shows series connection

### 3.4 Complex Connection Changes
- Add third resistor (R3)
- Create voltage divider network
- Verify all connection changes sync properly

## Files
- `circuit.py` - Initial two-resistor series circuit
- `test_script.py` - Automated test script
- `workspace/` - Working directory for test execution (gitignored)

## Running the Test
```bash
python test_script.py
```

## Expected Results
- Connection changes in KiCad should reflect in Python
- Connection changes in Python should reflect in KiCad
- Net additions/removals should sync properly
- No loss of component properties during sync