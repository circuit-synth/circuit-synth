# Test 48: Multi-Voltage Subcircuit (Dual Power Domains in Hierarchy)

**Priority:** 1 (Important hierarchical + multi-voltage integration)

**Category:** Hierarchical Operations + Power Distribution

## Overview

This test validates multi-voltage power distribution through hierarchical circuits by placing power symbols for MULTIPLE voltage domains (VCC_5V, VCC_3V3) INSIDE subcircuits.

This combines the critical patterns from:
- **Test 18:** Multiple power domains (VCC, 3V3, 5V, GND)
- **Test 47:** Power symbols in subcircuits

Real-world scenario: Level shifter circuit in a subcircuit that needs both 5V and 3.3V power rails from parent.

## Test Scenario

### Phase 1: Initial Generation (Single Level Shifter)

Create hierarchical circuit with:
- **Root sheet:** VCC_5V and VCC_3V3 power rails (two voltage domains)
- **Child sheet (Level_Shifter):**
  - Level shifter component (BSS138 N-channel MOSFET)
  - Two resistors (pull-ups for 5V and 3.3V sides)
  - Power symbols for BOTH voltages in subcircuit
  - Hierarchical pins/labels for VCC_5V, VCC_3V3, GND

**Circuit topology:**
```
VCC_5V (parent) → Hierarchical Label → VCC_5V (child power symbol)
    ├─ R1 (10k pull-up to 5V input side)
    └─ Q1 gate

VCC_3V3 (parent) → Hierarchical Label → VCC_3V3 (child power symbol)
    └─ R2 (10k pull-up to 3.3V output side)

Q1 (BSS138):
    - Gate: 5V side input
    - Source: GND
    - Drain: 3.3V side output
```

### Phase 2: Add Second Level Shifter

Modify Python to add second level shifter (Q2, R3, R4) in same subcircuit:
- Uses SAME power symbols (VCC_5V, VCC_3V3, GND)
- No duplicate power symbols created
- Both shifters share power rails

### Phase 3: Validation

Verify after each step:

**Level 1 - File Structure:**
- Root schematic exists
- Child schematic exists (Level_Shifter.kicad_sch)

**Level 2 - Schematic Structure (kicad-sch-api):**
- Power symbols exist in CHILD schematic for both voltages
- Hierarchical labels for VCC_5V, VCC_3V3, GND
- All components (Q1, R1, R2) present
- No duplicate power symbols after adding Q2

**Level 3 - Electrical Connectivity (Netlist):**
- R1 connected to VCC_5V net
- R2 connected to VCC_3V3 net
- Q1 source connected to GND
- After adding Q2: R3 and R4 also on correct voltage nets
- Netlist shows dual power connectivity through hierarchy

## Why This Test is Critical

### Real-World Design Pattern

Multi-voltage subcircuits are UBIQUITOUS in modern electronics:

**Example 1: Level Shifter Circuit**
- Microcontroller at 3.3V needs to communicate with 5V peripherals
- Level shifter subcircuit requires BOTH voltages
- Parent supplies both rails, child distributes to shifter components

**Example 2: Mixed-Voltage Sensor Interface**
- Sensor operates at 5V
- MCU operates at 3.3V
- Interface circuit needs both power domains

**Example 3: Power Management**
- Root sheet: Multiple voltage regulators (5V, 3.3V, 1.8V outputs)
- Child sheets: Each functional block uses appropriate voltages
- Some blocks (like level shifters) need MULTIPLE voltages

### What This Tests

1. **Multiple power domains in subcircuits** - Not just single voltage
2. **Hierarchical multi-voltage propagation** - Parent → child for multiple rails
3. **Power symbol creation for each domain** - VCC_5V and VCC_3V3 symbols in child
4. **Hierarchical label generation** - For each voltage crossing hierarchy
5. **Power symbol reuse across domains** - Multiple components, multiple voltages
6. **Position preservation** - Power symbols don't move when adding components
7. **Real-world level shifter topology** - Actual working circuit pattern

### Known Challenges

- Hierarchical labels must be created for EACH voltage domain
- Power symbols with different net names (VCC_5V vs VCC_3V3)
- Synchronizer must handle multiple power nets in subcircuit
- Netlist must show segregation of voltage domains through hierarchy
- May require XFAIL if multi-voltage subcircuit support incomplete

## Validation Levels

### Level 1: File Structure
- Root schematic file exists
- Child schematic file exists (Level_Shifter.kicad_sch)
- Both files are valid KiCad format

### Level 2: Component/Symbol Validation (kicad-sch-api)
- Power symbols for VCC_5V, VCC_3V3, GND exist in CHILD schematic
- Level shifter components (Q1, R1, R2) exist in child
- Hierarchical labels exist for all three power nets
- Position of power symbols preserved after adding Q2

### Level 3: Electrical Connectivity (Netlist)
- VCC_5V net connects R1 in child
- VCC_3V3 net connects R2 in child
- GND net connects Q1 source
- After adding Q2: R3 on VCC_5V, R4 on VCC_3V3
- Power net segregation maintained (5V and 3.3V separate)
- Global power nets continuous through hierarchy

## Test Workflow

### Step 1: Initial Generation
```bash
cd /Users/shanemattner/Desktop/circuit-synth2/tests/bidirectional/48_multi_voltage_subcircuit
uv run level_shifter.py
```

**Expected:**
- level_shifter/level_shifter.kicad_sch (root)
- level_shifter/Level_Shifter.kicad_sch (child)
- Child sheet contains: Q1, R1, R2
- Child sheet contains: VCC_5V, VCC_3V3, GND power symbols
- Hierarchical labels: VCC_5V, VCC_3V3, GND

### Step 2: Validate Initial Netlist
```bash
kicad-cli sch export netlist \
  level_shifter/level_shifter.kicad_sch \
  --output level_shifter/level_shifter_initial.net
```

**Verify netlist shows:**
- VCC_5V net: contains R1
- VCC_3V3 net: contains R2
- GND net: contains Q1 source
- Three separate power domains (not cross-connected)

### Step 3: Add Second Level Shifter
Modify Python to add Q2, R3, R4 to same subcircuit.

**Expected:**
- Same power symbols reused
- No duplicate VCC_5V, VCC_3V3, GND symbols
- Q1, R1, R2 positions preserved
- Q2, R3, R4 added

### Step 4: Validate Modified Netlist
```bash
kicad-cli sch export netlist \
  level_shifter/level_shifter.kicad_sch \
  --output level_shifter/level_shifter_modified.net
```

**Verify netlist shows:**
- VCC_5V net: contains R1, R3 (both 5V pull-ups)
- VCC_3V3 net: contains R2, R4 (both 3.3V pull-ups)
- GND net: contains Q1 source, Q2 source
- Power domain segregation maintained

## Expected Files Generated

```
level_shifter/
├── level_shifter.kicad_pro
├── level_shifter.kicad_sch          # Root sheet
├── Level_Shifter.kicad_sch          # Child sheet with multi-voltage power
├── level_shifter.kicad_pcb
├── level_shifter.json               # Hierarchical circuit netlist
└── level_shifter.net                # KiCad netlist (for validation)
```

## Test Success Criteria

### Phase 1 (Initial generation):
- Child sheet file created
- Power symbols for VCC_5V, VCC_3V3, GND in child sheet
- Hierarchical labels present for all three nets
- Level shifter components connected to correct voltages
- Netlist validates multi-voltage connectivity

### Phase 2 (After adding Q2):
- Same power symbols used (no duplicates)
- Both shifters connected to correct power domains
- Power symbol positions unchanged
- Netlist shows both shifters on VCC_5V/VCC_3V3/GND
- Voltage domain segregation maintained (5V separate from 3.3V)

### Phase 3 (Hierarchical structure):
- JSON netlist shows subcircuit structure
- VCC_5V net spans root → child
- VCC_3V3 net spans root → child
- Power symbols in correct sheet (child, not root)
- No cross-contamination between voltage domains

## Python Circuit Structure

```python
@circuit(name="level_shifter")
def level_shifter():
    root = get_current_circuit()

    # Root sheet: Establish two voltage domains
    vcc_5v = Net(name="VCC_5V")    # 5V supply
    vcc_3v3 = Net(name="VCC_3V3")  # 3.3V supply
    gnd = Net(name="GND")

    # Child sheet: Level shifter with dual power domains
    shifter_circuit = Circuit("Level_Shifter")

    # Components in child
    q1 = Component(symbol="Device:Q_NMOS_GSD", ref="Q1", ...)  # BSS138
    r1 = Component(symbol="Device:R", ref="R1", value="10k")    # 5V pull-up
    r2 = Component(symbol="Device:R", ref="R2", value="10k")    # 3.3V pull-up

    # Power symbols IN child sheet (BOTH voltages)
    vcc_5v_child = Net(name="VCC_5V")
    vcc_3v3_child = Net(name="VCC_3V3")
    gnd_child = Net(name="GND")

    # Connect level shifter circuit
    vcc_5v_child += r1[1]        # 5V pull-up
    vcc_3v3_child += r2[1]       # 3.3V pull-up
    r1[2] += q1["G"]             # Gate to 5V side input
    r2[2] += q1["D"]             # Drain to 3.3V side output
    q1["S"] += gnd_child         # Source to GND

    root.add_subcircuit(shifter_circuit)
```

## Related Tests

- **Test 16:** Add power symbol (root sheet, single voltage)
- **Test 18:** Multiple power domains (root sheet only)
- **Test 22:** Add subcircuit sheet (no power)
- **Test 47:** Power symbols in subcircuit (single voltage)
- **Test 64:** Complex multi-step workflow (includes voltage regulators)

## Edge Cases for Future Exploration

- More than 2 voltage domains in subcircuit (3+ rails)
- Nested subcircuits with different voltage domains
- Power domain naming variations (VCC_5V vs 5V vs VCC_5)
- Bidirectional level shifters (more complex topology)
- Multiple subcircuits sharing same multi-voltage power
- Dynamic power switching (enable pins, power sequencing)

## Potential Issues / XFAIL

This test may need XFAIL if:
- Synchronizer doesn't support multiple power domains in subcircuits
- Hierarchical labels not created for all voltage nets
- Power symbols with custom names (VCC_5V) not handled
- Netlist doesn't show multi-voltage connectivity through hierarchy
- Power symbol reuse fails across multiple domains

If XFAIL is needed, mark with:
```python
@pytest.mark.xfail(
    reason="Issue #XXX: Multi-voltage power in subcircuits not yet supported"
)
```

## Success Impact

When this test passes, it validates:
- Real-world multi-voltage hierarchical designs work
- Professional mixed-voltage circuit organization possible
- Level shifters and voltage interface circuits supported
- Power symbols can handle multiple domains in subcircuits
- Iterative development safe for hierarchical + multi-voltage designs
- Critical foundation for complex embedded systems

This is a **high-value integration test** combining hierarchical structure with multi-voltage power distribution - two of the most important real-world circuit patterns.
