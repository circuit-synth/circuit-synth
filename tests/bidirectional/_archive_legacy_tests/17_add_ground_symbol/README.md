# Test 17: Add Ground Symbol Connection

## What This Tests

Adding a GND ground symbol connection to a component pin in Python, then regenerating KiCad to validate the connection is reflected in the netlist.

**Core Question**: When a user adds `Net("GND")` connection in Python and regenerates, does the schematic correctly add the ground net connection with proper hierarchical labels?

## When This Situation Happens

- User has a component (resistor, capacitor, etc.) in the circuit
- Wants to connect one pin to ground/power plane
- Adds `Net("GND")` connection in Python
- Regenerates KiCad to see the ground connection
- Expects netlist to show component pin connected to GND net

## What Should Work

1. Generate initial circuit with R1 (no ground connection)
2. Verify netlist shows R1 with unconnected pins
3. Add GND connection in Python: `r1[2] += Net("GND")`
4. Regenerate KiCad
5. Verify netlist shows R1 pin 2 connected to GND
6. Component position should be preserved
7. KiCad schematic shows hierarchical label "GND" at R1 pin 2

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth2/tests/bidirectional/17_add_ground_symbol

# Step 1: Check initial Python code
cat resistor_with_ground.py
# Should show R1 component initially without ground connection

# Step 2: Generate initial circuit
uv run resistor_with_ground.py
# Creates resistor_with_ground/resistor_with_ground.kicad_pro

# Step 3: Open KiCad (optional - for visual verification)
open resistor_with_ground/resistor_with_ground.kicad_pro
# Should show:
#   - R1 component
#   - Pin 1 and Pin 2 unconnected (no labels)

# Step 4: Check the Python script
cat resistor_with_ground.py
# Currently has no ground connection

# Step 5: Edit to add ground (manually or via test)
# Add this to the circuit function:
#   gnd = Net("GND")
#   r1[2] += gnd

# Step 6: Regenerate
uv run resistor_with_ground.py

# Step 7: Open KiCad again
open resistor_with_ground/resistor_with_ground.kicad_pro
# Should now show:
#   - R1 component
#   - Pin 1 unconnected
#   - Pin 2 connected to "GND" hierarchical label
#   - Position preserved

# Step 8: Run automated test
pytest test_17_add_ground_symbol.py -v
```

## Expected Result

- ✅ Initial circuit generated with R1 (unconnected pins)
- ✅ Initial netlist shows R1 with no NET connections
- ✅ Python modified to add `r1[2] += Net("GND")`
- ✅ Regeneration succeeds
- ✅ Final netlist shows R1 pin 2 connected to GND net
- ✅ R1 position preserved between generations
- ✅ KiCad schematic shows "GND" label at R1 pin 2

## Why This Is Important

**Ground connections are fundamental to circuit design:**
1. Every circuit needs ground/return path
2. Connecting pins to ground is extremely common
3. Must validate netlist correctly shows these connections
4. Position preservation ensures no unexpected design changes
5. Ground handling is essential for PCB generation

## Validation Strategy

**Level 3 (Electrical Validation)**:
- Use `kicad-cli` netlist export to verify connectivity
- Parse netlist to extract component-pin-net relationships
- Validate GND net contains both R1 pin 2 reference and any power symbol references
- Use `kicad-sch-api` to verify positions preserved

## Critical Validation Points

1. **Initial state**: R1 pin 2 NOT in GND net
2. **Modified state**: R1 pin 2 IS in GND net
3. **Position check**: R1 x,y coordinates unchanged
4. **Netlist accuracy**: GND net properly formatted in KiCad netlist
5. **Hierarchical label**: "GND" label visible at R1 pin 2 in schematic

## Related Tests

- Test 11: Disconnect and reconnect nets (pin connection changes)
- Test 12: Change pin on net (similar pin-level validation)
- Test 26: Power symbol replacement (GND symbol handling)
