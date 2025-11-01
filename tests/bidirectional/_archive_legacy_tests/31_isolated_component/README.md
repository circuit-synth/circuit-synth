# Test 31: Isolated Component (No Net Connections)

## What This Tests

**Core Question**: When you have a component with NO net connections at all (completely isolated), does the KiCad schematic correctly show it with no hierarchical labels, and does the netlist show all pins as unconnected?

This tests **handling of isolated components** - a common scenario during early circuit design stages when components haven't been electrically connected yet.

## When This Situation Happens

- Developer generates initial circuit with components placed but not connected
- Reviews component layout in KiCad without any nets defined
- Later adds net connections to some components
- Needs to validate that isolated components show correctly (no labels, no net entries)

## What Should Work

1. Generate KiCad with R1 component, completely isolated (no nets connected to any pins)
2. Verify R1 shows 0 hierarchical labels in schematic
3. Export netlist, verify all R1 pins show as unconnected (unconnected-*)
4. Add net connection to R1 pin 1 in Python code
5. Regenerate KiCad
6. Verify R1 pin 1 now has hierarchical label
7. Verify netlist shows pin 1 connected, other pins still unconnected

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth2/tests/bidirectional/31_isolated_component

# Step 1: Generate initial KiCad project with isolated R1
uv run isolated_resistor.py
open isolated_resistor/isolated_resistor.kicad_pro
# Verify: R1 visible but NO hierarchical labels (completely unconnected)

# Step 2: Export netlist
kicad-cli sch export netlist isolated_resistor/isolated_resistor.kicad_sch --output isolated_resistor/isolated_resistor.net
# Verify: All R1 pins show unconnected (unconnected-*)

# Step 3: Edit isolated_resistor.py to add net connection
# Change the Python code to add:
#   net1 = Net("NET1")
#   r1[1] += net1

# Step 4: Regenerate KiCad project with connection
uv run isolated_resistor.py

# Step 5: Open regenerated KiCad project
open isolated_resistor/isolated_resistor.kicad_pro
# Verify:
#   - Hierarchical label "NET1" now appears on R1[1]
#   - R1[2] still has no label
#   - Component position preserved
#   - Only pin 1 is now connected

# Step 6: Export netlist again
kicad-cli sch export netlist isolated_resistor/isolated_resistor.kicad_sch --output isolated_resistor/isolated_resistor.net
# Verify: R1[1] in NET1, R1[2] still unconnected
```

## Expected Result

- ✅ Initial generation: R1 isolated (0 hierarchical labels)
- ✅ Initial netlist: All R1 pins unconnected (unconnected-*)
- ✅ After adding Net in Python: R1[1] has hierarchical label "NET1"
- ✅ After regeneration: R1[2] still has no label (isolated)
- ✅ Final netlist: R1[1] in NET1, R1[2] unconnected
- ✅ Component position preserved during regeneration
- ✅ No duplicate components
- ✅ Isolated pins don't create spurious net entries

## Why This Is Important

**Early design workflow:**
1. Place components first, don't worry about connections
2. Review layout in KiCad
3. Add connections incrementally
4. Regenerate - isolated components stay isolated, connected pins show labels

**Common in real development:**
- Placing decoupling caps that will be connected later
- Prototyping with multiple unconnected test points
- Adding components as placeholders before deciding connections

If this doesn't work, isolated components create false net entries or spurious label generation, making netlists incorrect and making it hard to distinguish what's actually connected.

## Success Criteria

This test PASSES when:
- Isolated component generates with 0 hierarchical labels
- Netlist shows all pins as unconnected (unconnected-*)
- Adding net to one pin creates label only on that pin
- Other pins remain unconnected in netlist
- No spurious unconnected-* entries for pins with labels
- Component positions preserved across regeneration

