# Test 24: Cross-Sheet Hierarchical Label Connection

## What This Tests

**Core Question**: Can you pass a Net from a parent circuit to a child circuit to establish electrical connectivity across hierarchical sheets via hierarchical labels and pins?

This validates the **critical cross-sheet connection workflow** - the foundation for hierarchical circuit development.

## When This Situation Happens

- Developer creates parent circuit with R1
- Creates child circuit with R2
- Initially unconnected (separate sheets)
- Later decides R1 and R2 should be electrically connected
- Passes `Net("SIGNAL")` from parent to child
- Connects R1[1] and R2[1] to the shared net
- Regenerates KiCad
- **Expected**: Hierarchical infrastructure appears automatically:
  - Hierarchical sheet symbol on parent sheet
  - Hierarchical pin "SIGNAL" on the sheet symbol
  - Hierarchical label "SIGNAL" on child sheet
  - R1[1] and R2[1] electrically connected (verified in netlist)

## What Should Work

1. Generate parent + child circuits with unconnected components (R1, R2)
   - Parent sheet shows R1 and hierarchical sheet symbol
   - Child sheet shows R2
   - No connection between R1 and R2
2. Modify Python to pass Net("SIGNAL") from parent to child:
   ```python
   @circuit(name="child_circuit")
   def child_circuit(signal_net):  # Accept net parameter
       r2 = Component(...)
       r2[1] += signal_net  # Connect to passed net

   @circuit(name="parent_circuit")
   def parent_circuit():
       r1 = Component(...)
       signal = Net("SIGNAL")
       r1[1] += signal
       child_circuit(signal_net=signal)  # Pass net to child
   ```
3. Regenerate KiCad project
4. Verify hierarchical infrastructure created:
   - Hierarchical pin "SIGNAL" appears on sheet symbol (parent sheet)
   - Hierarchical label "SIGNAL" appears on child sheet
   - R1[1] and R2[1] electrically connected (netlist shows same net)
5. Component positions preserved during regeneration

## Manual Test Instructions

```bash
cd tests/bidirectional/24_add_global_label

# Step 1: Generate initial hierarchical circuit (unconnected)
uv run hierarchical_connection.py
open hierarchical_connection/hierarchical_connection.kicad_pro
# Verify:
#   - Parent sheet shows R1
#   - Hierarchical sheet symbol visible (links to child)
#   - Child sheet shows R2
#   - No connection between R1 and R2

# Step 2: Edit hierarchical_connection.py to pass Net("SIGNAL")
# Modify child_circuit:
#   @circuit(name="child_circuit")
#   def child_circuit(signal_net):
#       r2 = Component(...)
#       r2[1] += signal_net
#
# Modify parent_circuit:
#   signal = Net("SIGNAL")
#   r1[1] += signal
#   child_circuit(signal_net=signal)

# Step 3: Regenerate KiCad project
uv run hierarchical_connection.py

# Step 4: Verify hierarchical connection
open hierarchical_connection/hierarchical_connection.kicad_pro
# Verify:
#   - Hierarchical pin "SIGNAL" on sheet symbol (parent sheet)
#   - Hierarchical label "SIGNAL" on child sheet
#   - R1 and R2 positions preserved

# Step 5: Verify electrical connectivity via netlist
kicad-cli sch export netlist hierarchical_connection/hierarchical_connection.kicad_sch \
  --output hierarchical_connection.net
# Verify: R1 pin 1 and R2 pin 1 on same net "SIGNAL"
```

## Expected Result

- ✅ Initial: Parent + child sheets generated, hierarchical sheet symbol visible
- ✅ Parent sheet: R1 + hierarchical sheet symbol
- ✅ Child sheet: R2
- ✅ After passing Net: Hierarchical pin "SIGNAL" on sheet symbol
- ✅ After passing Net: Hierarchical label "SIGNAL" on child sheet
- ✅ Netlist: R1[1] and R2[1] on same net (cross-sheet connection)
- ✅ Component positions preserved
- ✅ No electrical rule errors

## Why This Is Critical

**Cross-sheet connectivity is fundamental to hierarchical design:**

1. **Modularity**: Child circuits are reusable modules
2. **Organization**: Complex circuits split across logical sheets
3. **Explicit data flow**: Nets passed between circuits make connections visible in code
4. **Safety**: No implicit global nets - all connections explicit

**If this doesn't work:**
- Hierarchical circuits are disconnected islands
- Cannot build complex designs
- Tool is limited to flat single-sheet circuits
- Major feature unusable

**If this works:**
- Hierarchical design becomes practical
- Can build complex multi-sheet circuits
- Code clearly shows inter-circuit connections
- Foundation for real-world circuit development

## Success Criteria

This test PASSES when:
- Parent and child sheets generate correctly
- Hierarchical sheet symbol appears on parent sheet
- Passing Net from parent to child creates hierarchical pin on sheet symbol
- Hierarchical label appears on child sheet with matching name
- Netlist proves R1 and R2 are electrically connected
- Component positions preserved across regeneration
- No electrical rule errors

## Current Status

⚠️ **XFAIL - Blocked by Issue #406**

This test is currently marked as XFAIL because:
1. Subcircuit sheet generation is broken (Issue #406)
2. Net passing syntax between @circuit functions needs confirmation
3. Test documents the expected workflow but cannot execute until dependencies resolved

## Validation Level

**Level 3 (Netlist Comparison)**: Cross-sheet electrical connectivity
- kicad-sch-api for schematic structure
- Text search for hierarchical_pin and hierarchical_label in .kicad_sch files
- Netlist comparison to prove R1 and R2 electrically connected
- Position preservation verification

## Related Tests

- **Test 22** - Add subcircuit progressively (1→2→3 levels) - MUST PASS FIRST
- **Test 10** - Add net to components (same sheet)
- **Test 11** - Add hierarchical labels (same sheet)

## Design Notes

**Hierarchical Infrastructure in KiCad:**

When you pass a Net from parent to child, circuit-synth must generate:

1. **Hierarchical Sheet Symbol** (parent sheet)
   - Rectangle representing child circuit
   - Contains hierarchical pins for each passed net

2. **Hierarchical Pin** (on sheet symbol)
   - Pin labeled "SIGNAL"
   - Connects to parent net (R1[1])

3. **Hierarchical Label** (child sheet)
   - Label "SIGNAL" on child sheet
   - Connects to child component (R2[1])

4. **Electrical Connection**
   - KiCad connects hierarchical pin to hierarchical label by matching names
   - Creates single net spanning both sheets
   - Netlist shows R1[1] and R2[1] on same net

**Example:**

Parent sheet:
```
R1 --o SIGNAL
      |
   +--+------------+
   | SIGNAL        |  <- Hierarchical sheet symbol
   | child_circuit |
   +---------------+
```

Child sheet (child_circuit.kicad_sch):
```
SIGNAL o-- R2
```

Netlist:
```
(net (code "1") (name "SIGNAL")
  (node (ref "R1") (pin "1"))
  (node (ref "R2") (pin "1")))
```
