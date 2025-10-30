# Test 36: Hierarchical Subcircuit Instance Duplication

## What This Tests
Validates that you can create **reusable hierarchical subcircuit blocks** by calling a `@circuit` decorated function multiple times. Each call automatically creates an independent subcircuit instance on its own KiCad sheet with auto-incremented naming.

**Key Concept:** Circuit-synth allows you to write a circuit pattern once (as a function) and instantiate it multiple times as hierarchical subcircuits - like creating classes/objects in programming.

## When This Situation Happens
- You have a useful circuit block (voltage divider, LED driver, sensor input, etc.)
- You need multiple instances of the same circuit
- Each instance should have unique component references
- All instances share common power/ground nets

**Real-world examples:**
- 8 sensor inputs, each with the same voltage divider circuit
- 4 LED drivers with identical current-limiting circuits
- Multiple power regulators with the same topology

## What Should Work
- Write `@circuit` decorated `voltage_divider_subcircuit()` function
- Call it once → one subcircuit appears on its own sheet (voltage_divider_subcircuit_1.kicad_sch)
- Call it twice → two subcircuits appear, each on its own sheet
- Auto-incremented naming: voltage_divider_subcircuit_1, voltage_divider_subcircuit_2, etc.
- Both subcircuits share VCC and GND nets via hierarchical pins
- Each subcircuit has its own VOUT hierarchical pin
- Synchronization preserves first subcircuit when adding/removing second

**Clean Syntax:**
```python
@circuit
def voltage_divider_subcircuit(vcc: Net, gnd: Net):
    # ... circuit implementation
    return output_net

@circuit(name="main")
def main():
    vcc = Net("VCC")
    gnd = Net("GND")

    vout_1 = voltage_divider_subcircuit(vcc, gnd)  # Auto-named: voltage_divider_subcircuit_1
    vout_2 = voltage_divider_subcircuit(vcc, gnd)  # Auto-named: voltage_divider_subcircuit_2
```

## Manual Test Instructions

```bash
cd tests/bidirectional/36_copy_paste_component

# Step 1: Generate initial KiCad project with ONE subcircuit instance
uv run resistor_divider_for_copy.py
open voltage_divider_instances/voltage_divider_instances.kicad_pro

# Verify in KiCad:
#   Parent sheet (voltage_divider_instances.kicad_sch):
#     - One hierarchical sheet symbol labeled "voltage_divider_subcircuit_1"
#     - Hierarchical pins: VCC, GND, VOUT
#
#   Child sheet (voltage_divider_subcircuit_1.kicad_sch):
#     - 2 resistors: R1 (10k), R2 (10k)
#     - Hierarchical labels: VCC, GND, VOUT
#     - VCC connects to R1 pin 1
#     - VOUT connects to R1 pin 2 and R2 pin 1
#     - GND connects to R2 pin 2

# Step 2: Edit resistor_divider_for_copy.py to ADD SECOND subcircuit instance
# Uncomment line 81:
#   vout_2 = voltage_divider_subcircuit(vcc, gnd)

# Step 3: Regenerate KiCad project (now with TWO subcircuit instances)
# NOTE: Currently blocked by Issue #419 - reference collision bug
# Each subcircuit should have independent namespace, but collision detection is global

# Expected behavior (when bug is fixed):
#   Parent sheet:
#     - Two hierarchical sheet symbols:
#       * voltage_divider_subcircuit_1 (first instance - positions preserved)
#       * voltage_divider_subcircuit_2 (second instance - newly placed)
#     - Both share VCC and GND nets via hierarchical pins
#
#   Child sheets:
#     - voltage_divider_subcircuit_1.kicad_sch: R1, R2 (first instance)
#     - voltage_divider_subcircuit_2.kicad_sch: R1, R2 (second instance)
#     - Each has independent namespace (no collision)

# Step 4: Comment out line 81 again and regenerate
# Verify second subcircuit disappears, first subcircuit remains
```

## Expected Result

**Initial state (1 subcircuit):**
- ✅ Parent sheet has one hierarchical sheet symbol: "voltage_divider_subcircuit_1"
- ✅ Child sheet (voltage_divider_subcircuit_1.kicad_sch) has R1 and R2
- ✅ Auto-incremented naming works correctly
- ✅ Hierarchical pins connect parent and child (VCC, GND, VOUT)
- ✅ Correct electrical connectivity

**After uncommenting (2 subcircuits):**
- ⏳ BLOCKED by Issue #419 (reference collision bug)
- ✅ (When fixed) Parent sheet has two hierarchical sheet symbols
- ✅ (When fixed) First subcircuit positions preserved
- ✅ (When fixed) Second subcircuit placed without overlap
- ✅ (When fixed) Two child sheets: voltage_divider_subcircuit_1.kicad_sch, voltage_divider_subcircuit_2.kicad_sch
- ✅ (When fixed) Each child sheet has its own R1 and R2 (independent namespaces)
- ✅ (When fixed) Both subcircuits share VCC and GND nets via hierarchical pins
- ✅ (When fixed) Synchronization logs show "Add: voltage_divider_subcircuit_2"

**After commenting back (1 subcircuit):**
- ✅ (When fixed) Second subcircuit removed
- ✅ (When fixed) First subcircuit preserved
- ✅ (When fixed) Synchronization logs show "Remove: voltage_divider_subcircuit_2"

**This demonstrates:**
- ✅ Auto-incrementing subcircuit naming feature (working!)
- ✅ Reusable hierarchical circuit blocks - write once, instantiate multiple times
- ⏳ Multiple instances blocked by Issue #419 (reference collision)
