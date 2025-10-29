# Test 64: Complex Multi-Step Workflow

## Priority: 0 - THE ULTIMATE TEST

This test simulates a real-world professional EE workflow with multiple iterations between Python code and KiCad GUI.

## Why This Test Matters

In professional electronics design, engineers don't create a circuit once and call it done. Instead:

1. **Initial Design** - Create basic circuit structure in code
2. **Layout in KiCad** - Position components optimally, route traces
3. **Add Features** - Modify Python code to add protection, indicators, etc.
4. **Re-layout** - Fine-tune the new components in KiCad
5. **Iterate** - Repeat steps 3-4 multiple times
6. **Modularize** - Copy successful circuits to subcircuits for reuse

**THE CRITICAL QUESTION:** Does position preservation survive this multi-step iterative process?

If positions are lost at ANY step, the workflow breaks. Engineers would have to:
- Manually re-position everything after each code change
- Avoid using Python for modifications (defeats the purpose)
- Maintain two separate sources of truth (Python code vs KiCad layout)

This test validates that circuit-synth enables TRUE bidirectional workflow.

## Test Scenario: Voltage Regulator Development

### Step 1: Initial Design (Python)
```python
# Simple voltage regulator
circuit = Circuit("VoltageRegulator")
circuit.add(Capacitor("C1", "100uF", between=("VIN", "GND")))
circuit.add(LM7805("U1", input="VIN", output="VOUT", ground="GND"))
circuit.add(Capacitor("C2", "10uF", between=("VOUT", "GND")))
```
**Generate → KiCad**

### Step 2: Layout in KiCad (Manual)
- Position components for optimal trace routing
- Arrange for thermal management
- **Synchronize back to Python (preserves positions)**

### Step 3: Add Protection (Python)
```python
# Add reverse polarity protection
circuit.add(Diode("D1", "1N4007", anode="VIN_RAW", cathode="VIN"))
```
**Regenerate → KiCad**
- D1 appears as new component
- C1, U1, C2 positions PRESERVED from Step 2

### Step 4: Refine Layout (KiCad)
- Position D1 near input
- **Synchronize back (preserves all positions)**

### Step 5: Add Power Indicator (Python)
```python
# Add LED indicator
circuit.add(LED("D2", anode="VOUT", cathode="LED_CATHODE"))
circuit.add(Resistor("R1", "1k", between=("LED_CATHODE", "GND")))
```
**Regenerate → KiCad**
- D2, R1 appear as new components
- D1, C1, U1, C2 positions PRESERVED from Steps 2 & 4

### Step 6: Create Subcircuit (Copy to Second Rail)
```python
# Duplicate regulator for 3.3V rail
subcircuit = circuit.create_subcircuit("Regulator3V3")
# Modify subcircuit to use LM1117-3.3
```
**Regenerate → KiCad**
- Subcircuit sheet created
- Both circuits maintain independent positions
- Root circuit positions UNCHANGED

### Step 7: Final Modifications (Python)
```python
# Update root circuit
circuit.get("C2").value = "22uF"  # Increase output cap

# Update subcircuit
subcircuit.get("C2").value = "47uF"  # Different value for 3.3V rail
```
**Regenerate → KiCad**
- Component values updated in both circuits
- ALL positions preserved throughout entire workflow

## Validation Levels

### Level 2: Position Preservation (PRIMARY)
- After each regenerate, validate positions match previous KiCad layout
- Track positions through all 7 steps
- Verify both root and subcircuit positions preserved independently

### Level 3: Electrical Correctness
- Netlist validation after each step
- Component count matches expected
- Net count matches expected
- Values reflect current design

### Level 4: Structural Integrity
- Subcircuit hierarchy maintained
- Root circuit independent from subcircuit
- Sheet references correct

## Expected Outcome

If circuit-synth works correctly:
- ✅ All positions preserved through 7 design iterations
- ✅ Engineers can freely modify Python code
- ✅ KiCad layouts remain intact
- ✅ True bidirectional workflow achieved

If this test fails:
- ❌ Positions lost at some iteration
- ❌ Workflow broken
- ❌ Engineers forced to choose: code OR layout, not both

## Implementation Notes

This test is complex and may expose edge cases:
- Position tracking through multiple synchronizations
- UUID stability through iterations
- Subcircuit position independence
- Attribute updates without position changes

If test fails, mark as `@pytest.mark.xfail` with clear explanation of what breaks.
This test defines the aspirational goal for circuit-synth bidirectional workflow.
