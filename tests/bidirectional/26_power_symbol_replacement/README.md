# Test 26: Power Symbol Replacement

## What This Tests

Validates that power symbols (GND, VCC, +3V3, +5V, -5V) are generated with correct library references, positions, and rotations.

This test ensures:
1. Each power symbol type generates with correct KiCad library reference
2. Power symbols are positioned correctly relative to component pins
3. All power symbols generate correctly in a single schematic
4. Power domain changes work (replacing one power symbol with another)

## When This Situation Happens

- Multi-voltage designs with multiple power rails (3.3V, 5V, 12V, GND)
- Circuits using standard KiCad power symbols
- Power distribution networks requiring proper symbol representation
- Iterative development where power domains change (e.g., 3.3V → 5V)

## What Should Work

1. Generate circuit with 5 resistors connected to different power nets:
   - R1 → VCC (positive supply)
   - R2 → +3V3 (3.3V supply)
   - R3 → +5V (5V supply)
   - R4 → GND (ground)
   - R5 → -5V (negative supply)

2. Verify all power symbols generated with correct library references:
   - `power:VCC`
   - `power:+3V3`
   - `power:+5V`
   - `power:GND`
   - `power:-5V`

3. Verify electrical connections via netlist:
   - Each resistor connected to its power net
   - Power symbol nodes present in netlist

## Manual Test Instructions

```bash
cd tests/bidirectional/26_power_symbol_replacement

# Step 1: Generate circuit with all power symbols
uv run power_symbols.py
open power_symbols/power_symbols.kicad_pro

# Verify:
#   - 5 resistors visible (R1-R5)
#   - 5 power symbols visible (VCC, +3V3, +5V, GND, -5V)
#   - Each resistor connected to its power symbol

# Step 2: Export netlist to verify connections
kicad-cli sch export netlist power_symbols/power_symbols.kicad_sch \
  --output power_symbols.net

# Verify netlist shows:
#   - R1 connected to VCC
#   - R2 connected to +3V3
#   - R3 connected to +5V
#   - R4 connected to GND
#   - R5 connected to -5V

# Step 3 (Optional): Test power domain replacement
# Edit power_symbols.py to change R2 from +3V3 to +5V:
#   v5 = Net(name="+5V")
#   v5 += r2[1]  # Change from v3_3 to v5
#   v5 += r3[1]

# Regenerate and verify:
#   - +3V3 symbol removed (or only R2 disconnected)
#   - +5V symbol now connects both R2 and R3
#   - No text overlap issues
```

## Expected Result

- ✅ All 5 power symbols generated
- ✅ Correct library references (power:VCC, power:+3V3, etc.)
- ✅ Each resistor connected to correct power net
- ✅ Netlist shows correct electrical connections
- ✅ No visual overlaps or positioning issues

## Why This Is Important

**Power symbols are fundamental to KiCad schematics:**
- Standard way to represent power distribution
- Global net semantics (VCC connects everywhere)
- Cleaner than drawing wires everywhere
- Industry standard practice

**This test validates:**
- Power symbol generation works for all common types
- Library references are correct (KiCad compatibility)
- Electrical connectivity is correct
- Foundation for tests 16, 17, 18 (power symbol basics)

## Success Criteria

This test PASSES when:
- All 5 power symbols generate with correct library IDs
- Each resistor electrically connected to its power net (netlist)
- No errors or warnings during generation
- Schematic opens cleanly in KiCad
- Power symbols visually positioned correctly

## Validation Level

**Level 2 (Semantic Validation)**: Library references + netlist
- Text search for `power:VCC`, `power:+3V3` etc. in .kicad_sch
- kicad-sch-api for component verification
- Netlist comparison for electrical connectivity

## Related Tests

- **Test 16** - Add power symbol (VCC connection workflow)
- **Test 17** - Add ground symbol (GND connection workflow)
- **Test 18** - Multiple power domains (multi-voltage circuit, includes power domain replacement)

## Design Notes

**Power symbol library references:**
```
VCC   → power:VCC
+3V3  → power:+3V3
+5V   → power:+5V
GND   → power:GND
-5V   → power:-5V
```

**Pin connections:**
- Positive supplies (+) connect to component top pin (typically pin 1)
- Ground and negative supplies connect to component bottom pin (typically pin 2)

**Why separate from test 18:**
Test 18 focuses on multi-voltage circuit workflow and power domain **replacement**.
Test 26 focuses on detailed power symbol **generation** validation (library IDs, all symbol types).
Both tests complement each other - test 18 is workflow, test 26 is detailed validation.
