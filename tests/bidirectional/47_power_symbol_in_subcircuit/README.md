# Test 47: Power Symbols in Subcircuit

**Priority:** 0 (Critical hierarchical + power test)

**Category:** Hierarchical Operations + Power Distribution

## Overview

This test validates power distribution through hierarchical circuits by placing power symbols (VCC, GND) INSIDE subcircuits rather than on the root sheet.

This is a CRITICAL real-world pattern: power nets typically originate on the root sheet but are distributed to child sheets where components actually connect to them via local power symbols.

## Test Scenario

### Step 1: Initial Generation
Create hierarchical circuit with:
- **Root sheet:** VCC power net (global power rail)
- **Child sheet (LED_Circuit):**
  - LED component (D1) requiring VCC and GND
  - Power symbols (VCC, GND) placed IN child sheet
  - Hierarchical labels connecting to parent

### Step 2: Modification
Add second LED (D2) to subcircuit:
- Uses same VCC/GND power symbols
- No duplicate symbols created
- Power connectivity preserved

### Step 3: Validation
Verify:
- Power symbols exist in subcircuit sheet file
- Hierarchical labels/pins created for VCC, GND
- Netlist shows LEDs connected to power
- Position preservation of existing power symbols
- No duplicate power symbols after adding component

## Why This Test is Critical

### Real-World Design Pattern
Professional circuits organize power distribution hierarchically:
1. **Root sheet:** Power supply section (regulators, input connectors)
2. **Child sheets:** Functional blocks that CONSUME power
3. **Power symbols in children:** Connect local components to global power

**Example:**
```
Root Sheet:
  - VCC regulator output → VCC net
  - GND connection

Child Sheet "Microcontroller":
  - VCC power symbol → connects to MCU VCC pin
  - GND power symbol → connects to MCU GND pin
  - Both reference parent VCC/GND via hierarchical labels

Child Sheet "Sensors":
  - VCC power symbol → connects to sensor VCC pins
  - GND power symbol → connects to sensor GND pins
  - Same parent VCC/GND through hierarchy
```

### What This Tests
1. **Power symbol placement in subcircuits** - Not just on root
2. **Hierarchical power propagation** - From parent → child
3. **Hierarchical label generation** - For power nets crossing boundaries
4. **Power symbol reuse** - Multiple components share same symbols
5. **Position preservation** - Power symbols don't move when adding components

### Known Challenges
- Power symbols have special handling in KiCad (global net semantics)
- Hierarchical labels must match between parent and child
- Synchronizer may not handle subcircuit power symbols correctly yet
- May require XFAIL if not implemented

## Validation Levels

### Level 1: File Structure
- Root schematic file exists
- Child schematic file exists
- Both files are valid KiCad format

### Level 2: Component/Symbol Validation (kicad-sch-api)
- Power symbols (VCC, GND) exist in CHILD schematic
- LED components exist in child schematic
- Hierarchical labels exist for VCC, GND
- Position of power symbols preserved after modification

### Level 3: Electrical Connectivity (Netlist)
- Netlist shows D1 cathode connected to VCC
- Netlist shows D1 anode connected to GND (via resistor)
- After modification: D2 also connected to same power nets
- Global power net continuity through hierarchy

## Expected Files Generated

```
led_with_power/
├── led_with_power.kicad_pro
├── led_with_power.kicad_sch          # Root sheet
├── LED_Circuit.kicad_sch             # Child sheet with power symbols
├── led_with_power.kicad_pcb
├── led_with_power.json               # Hierarchical circuit netlist
└── led_with_power.net                # KiCad netlist
```

## Test Success Criteria

1. **Initial generation:**
   - Child sheet file created
   - Power symbols (VCC, GND) in child sheet
   - Hierarchical labels present
   - LED connected to power symbols
   - Netlist validates power connectivity

2. **After adding D2:**
   - Same power symbols used (no duplicates)
   - Both LEDs connected to power
   - Power symbol positions unchanged
   - Netlist shows both LEDs on VCC/GND

3. **Hierarchical structure:**
   - JSON netlist shows subcircuit structure
   - VCC net spans root → child
   - Power symbols in correct sheet (child, not root)

## Implementation Notes

### Python Circuit Structure
```python
@circuit(name="led_with_power")
def led_with_power():
    root = get_current_circuit()

    # Root sheet: Just establishes VCC power rail
    vcc = Net(name="VCC")

    # Child sheet: Contains LEDs and power symbols
    led_circuit = Circuit("LED_Circuit")

    # Power symbols IN child sheet
    vcc_symbol = PowerSymbol("VCC")
    gnd_symbol = PowerSymbol("GND")

    # LED on child sheet
    d1 = Component(symbol="Device:LED", ref="D1", ...)
    led_circuit.add_component(d1)

    # Connect LED to power symbols (child-local)
    vcc_in_child = Net(name="VCC")
    vcc_in_child += vcc_symbol
    vcc_in_child += d1["cathode"]

    root.add_subcircuit(led_circuit)
```

### KiCad Structure Expected
- **Root sheet:** May have hierarchical sheet symbol linking to child
- **Child sheet:** Contains actual power symbols and components
- **Hierarchical labels:** VCC and GND on child sheet boundary
- **Global nets:** VCC and GND recognized as power nets across hierarchy

## Related Tests
- **Test 16:** Add power symbol (root sheet only)
- **Test 17:** Add ground symbol (root sheet only)
- **Test 22:** Add subcircuit sheet (no power)
- **Test 18:** Multiple power domains (root sheet)

## Potential Issues / XFAIL

This test may need XFAIL if:
- Synchronizer doesn't support subcircuit power symbols yet
- Power symbols always placed on root sheet regardless of Python
- Hierarchical label creation for power nets not implemented
- Netlist doesn't show power connectivity through hierarchy

If XFAIL is needed, mark with:
```python
@pytest.mark.xfail(reason="Issue #XXX: Power symbols in subcircuits not yet supported")
```

## Success Impact

When this test passes, it validates:
- Real-world hierarchical power distribution works
- Professional circuit organization possible
- Power symbols can be placed where they're needed (in subcircuits)
- Iterative development safe for hierarchical + power designs
