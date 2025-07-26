# Test Case 15: Power Supply Architecture Changes

## Objective
Test the ability to change power supply topology (linear to switching regulator) in KiCad and sync back.

## Test Scenario
1. Create a circuit with linear voltage regulator in Python
2. Generate KiCad project
3. In KiCad:
   - Remove linear regulator components
   - Add switching regulator IC
   - Add required inductor and diodes
   - Update feedback network
   - Add input/output capacitors for switching design
4. Import changes back to Python
5. Verify new power architecture is correctly represented

## Expected Results
- Linear regulator components removed from Python code
- Switching regulator components added with correct values
- All new connections properly established
- Power net names preserved
- Circuit maintains proper power distribution

## Key Aspects Tested
- Major topology changes
- Component removal and addition
- Complex circuit modifications
- Power architecture flexibility