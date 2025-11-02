# Test 21: Multi-Unit Components (CRITICAL)

## What This Tests

**Core Question**: When you use a multi-unit component (quad op-amp with 4 units) and regenerate, are all units preserved with correct pin connections?

This validates that **multi-unit components (op-amps, logic gates, etc.) maintain all units and pin mappings** when regenerating from Python code.

## When This Situation Happens

- Developer needs quad op-amp (TL074, LM324, etc.) with 4 operational amplifier units
- Each unit has independent pins (U1A, U1B, U1C, U1D)
- Units connect to different signals in the circuit
- Later decides to change connections on one unit (e.g., unit B)
- Regenerates KiCad from Python
- **Critical**: Are all 4 units still there with correct pin mappings?

## What Should Work

1. Generate KiCad with quad op-amp using all 4 units
   - Netlist shows U1A, U1B, U1C, U1D with correct pin connections
2. Verify netlist shows all 4 units with correct electrical connections
3. Modify Python to change unit B connections
4. Regenerate KiCad project
5. **All 4 units still present** with correct mappings
6. **Unit B has updated connections** (verified in netlist)
7. **Other units (A, C, D) unchanged** (preserved from previous run)

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth2/tests/bidirectional/21_multi_unit_components

# Step 1: Generate initial KiCad project with quad op-amp using all 4 units
uv run quad_opamp.py
open quad_opamp/quad_opamp.kicad_pro
# Verify: All 4 op-amp units visible in schematic

# Step 2: Export netlist to see initial connections
kicad-cli sch export netlist quad_opamp/quad_opamp.kicad_sch --output quad_opamp_initial.net
# Verify:
#   - U1A has connections on pins 1,2,3 (non-inverting in, inverting in, out)
#   - U1B has different connections on same pins (but different nets)
#   - U1C and U1D have their own connections
#   - All units present and electrically distinct

# Step 3: Edit quad_opamp.py to modify unit B connections
# Change unit B output to different net (e.g., from OUT_B to OUT_B_MODIFIED)

# Step 4: Regenerate KiCad project
uv run quad_opamp.py

# Step 5: Open regenerated KiCad and verify all units present
open quad_opamp/quad_opamp.kicad_pro
# Verify:
#   - All 4 units still visible (U1A, U1B, U1C, U1D)
#   - Unit B has modified connections
#   - Units A, C, D unchanged from initial

# Step 6: Export netlist and compare
kicad-cli sch export netlist quad_opamp/quad_opamp.kicad_sch --output quad_opamp_modified.net
# Verify:
#   - U1B output net changed to OUT_B_MODIFIED
#   - U1A, U1C, U1D connections unchanged
#   - All 4 units present
```

## Expected Result

- ✅ Initial KiCad generated with quad op-amp (4 units visible)
- ✅ Netlist shows U1A, U1B, U1C, U1D with correct pin mappings
- ✅ Each unit has independent pins (1, 2, 3 for each op-amp)
- ✅ Unit B modified in Python code
- ✅ Regenerated KiCad preserves all 4 units
- ✅ Unit B has updated connections (verified in netlist)
- ✅ Units A, C, D preserved unchanged
- ✅ Multi-unit component integrity maintained

## Why This Is Critical

**Multi-unit components are fundamental to electronics:**
- Quad op-amps (TL074, LM324, OPA4134)
- Dual/quad gates (7408, CD4081)
- Dual diodes, dual transistors, etc.

**If multi-unit components don't work:**
- Users must manually recreate units after regeneration
- Complex circuits become unmaintainable
- Key feature (multi-unit ICs) becomes unusable
- Tool loses credibility for real-world designs

**If multi-unit components work correctly:**
- All 4 units preserved when regenerating
- Can modify individual units without affecting others
- Iterative development works for ICs
- Tool becomes production-ready for real circuits

**This is CRITICAL** for tool credibility with electronics engineers.

## Multi-Unit Component Details

### Typical Quad Op-Amp Structure
```
TL074 (4-unit quad op-amp)
├── Unit A: Pins 1(out), 2(inv), 3(non-inv), 4(V-), 11(V+)
├── Unit B: Pins 7(out), 6(inv), 5(non-inv), 4(V-), 11(V+)
├── Unit C: Pins 8(out), 9(inv), 10(non-inv), 4(V-), 11(V+)
└── Unit D: Pins 14(out), 13(inv), 12(non-inv), 4(V-), 11(V+)

KiCad References:
- U1A (unit A)
- U1B (unit B)
- U1C (unit C)
- U1D (unit D)
```

### Why Netlist Comparison (Level 3)

Multi-unit component validation requires **netlist comparison** (Level 3) because:
1. **Pin mapping complexity**: Each unit has independent pins within same IC
2. **Electrical connectivity**: Units connect to different signals in the circuit
3. **Preservation requirements**: When regenerating, all units and mappings must be maintained
4. **No visual inspection**: Even if schematic shows all 4 units, netlist proves electrical connections are correct

## Success Criteria

This test PASSES when:
- All 4 units present in generated KiCad schematic
- Netlist shows all 4 units (U1A, U1B, U1C, U1D) with correct pins
- Each unit's pins map to correct nets
- Modifying unit B connections updates only that unit's netlist entries
- Units A, C, D netlist entries remain unchanged after regeneration
- No electrical rule errors in KiCad
- Multi-unit component integrity maintained across regeneration
