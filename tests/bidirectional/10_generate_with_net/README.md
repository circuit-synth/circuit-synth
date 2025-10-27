# Test 10: Generate Circuit with Named Net (Foundation)

## What This Tests

**Core Question**: Does a simple named net connection in Python code correctly appear as a labeled wire in the KiCad schematic?

This is the **foundational net test** - validates that basic net generation works before testing more complex net operations.

## When This Situation Happens

- Developer creates circuit with two components
- Wants to connect them electrically via a named net
- Defines `Net("NET1")` and connects component pins
- Generates KiCad project expecting wire with net label

## What Should Work

1. Python code defines R1 and R2 connected via NET1
2. Generate KiCad project from Python
3. KiCad schematic shows:
   - Wire connecting R1 pin 1 to R2 pin 1
   - Net label "NET1" visible on the connection
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
#   - Wire connecting R1 pin 1 to R2 pin 1
#   - Net label "NET1" visible on wire
#   - Components placed without overlap
```

## Expected Result

- ✅ KiCad schematic generated successfully
- ✅ Wire visible connecting R1[1] to R2[1]
- ✅ Net label "NET1" appears in schematic
- ✅ Net label is readable and properly positioned
- ✅ Components placed without overlap
- ✅ No orphaned wires or net errors

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
- KiCad schematic shows clear wire connection
- Net label "NET1" is visible and properly placed
- Opening schematic in KiCad shows no electrical rule errors
