# Test 10: Generate Circuit with Named Net (Foundation)

## What This Tests

**Core Question**: Does a simple named net connection in Python code correctly appear as hierarchical labels in the KiCad schematic, establishing electrical connection without physical wires?

This is the **foundational net test** - validates that basic net generation works before testing more complex net operations.

**Note**: Hierarchical labels with the same name establish electrical connection without drawing wires between them. This is the correct KiCad behavior for hierarchical labels.

## When This Situation Happens

- Developer creates circuit with two components
- Wants to connect them electrically via a named net
- Defines `Net("NET1")` and connects component pins
- Generates KiCad project expecting hierarchical labels establishing connection

## What Should Work

1. Python code defines R1 and R2 connected via NET1
2. Generate KiCad project from Python
3. KiCad schematic shows:
   - R1 and R2 components with hierarchical labels "NET1" on their pins
   - No physical wire between components (labels establish electrical connection)
   - Both components placed without overlap

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional/10_generate_with_net

# Step 1: Generate KiCad project with net connection
uv run two_resistors_connected.py

# Step 2: Open KiCad schematic
open two_resistors_connected/two_resistors_connected.kicad_pro

# Step 3: Verify in KiCad schematic editor:
# Expected:
#   - R1 and R2 visible
#   - Hierarchical label "NET1" on R1 pin 1 (small square flag)
#   - Hierarchical label "NET1" on R2 pin 1 (small square flag)
#   - NO physical wire between components
#   - Electrical connection established by matching label names
#   - Components placed without overlap
```

## Expected Result

- ✅ KiCad schematic generated successfully
- ✅ Hierarchical label "NET1" on R1 pin 1 (square flag shape)
- ✅ Hierarchical label "NET1" on R2 pin 1 (square flag shape)
- ✅ Labels are readable and properly positioned on component pins
- ✅ NO physical wire between R1 and R2
- ✅ Electrical connection established by matching hierarchical label names
- ✅ Components placed without overlap
- ✅ No electrical rule errors when checked in KiCad

**How it works:** Hierarchical labels with identical names create electrical connection without physical wires. KiCad's ERC recognizes this as a valid electrical connection.

## Why This Is Important

**Foundation for all net tests.** If basic net generation doesn't work:
- Can't test adding nets to existing circuits
- Can't test adding components to nets
- Can't test power rails
- Can't validate netlist export

This test validates the most basic net functionality before attempting more complex scenarios.

## Success Criteria

This test PASSES when:
- Circuit generates without errors
- Two hierarchical labels "NET1" visible (one on each component pin)
- NO physical wire between components
- Labels have matching names, establishing electrical connection
- Opening schematic in KiCad shows no electrical rule errors
