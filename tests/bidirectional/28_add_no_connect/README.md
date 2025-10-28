# Test 28: Add No-Connect Flags to Unused Pins (CRITICAL)

## What This Tests

**Core Question**: When you have a component with unused pins (marked as no-connect) and regenerate, do the no-connect symbols appear on the schematic to prevent ERC (electrical rule check) errors?

This validates that **no-connect flags are properly generated** when marking pins as intentionally unused, preventing false ERC violations.

## When This Situation Happens

- Developer generates circuit with op-amp or other IC with many pins
- Some pins are not used in the application (e.g., NC pins on op-amp)
- Needs to mark these pins as "no-connect" to prevent ERC errors
- Regenerates KiCad project expecting no-connect symbols to appear

## What Should Work

1. Generate KiCad with op-amp having unused pins (no NC flags initially)
2. Verify schematic has NO no-connect symbols (0 initially)
3. Edit Python to explicitly mark unused pins as PinType.NO_CONNECT
4. Regenerate KiCad project
5. Verify no-connect symbols appear on unused pins
6. Validate ERC accepts NC flags without errors

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth2/tests/bidirectional/28_add_no_connect

# Step 1: Generate initial KiCad project (no NC pins)
uv run opamp_with_unused_pins.py
open opamp_with_unused_pins/opamp_with_unused_pins.kicad_pro
# Verify: Op-amp displayed but NO (no_connect) symbols visible

# Step 2: Edit opamp_with_unused_pins.py to mark NC pins
# Find the op-amp definition and add:
#   u1_pin_nc = Component(
#       symbol="Device:NC",  # or use PinType.NO_CONNECT on pins
#       ref="NC1",
#   )
# Modify the circuit to mark pins 6 and 7 as unused

# Step 3: Regenerate KiCad project with NC pins
uv run opamp_with_unused_pins.py

# Step 4: Open regenerated KiCad project
open opamp_with_unused_pins/opamp_with_unused_pins.kicad_pro
# Verify:
#   - (no_connect) symbols appear at pins 6, 7
#   - Symbols appear as small X marks on the pins
#   - ERC checks pass (no unconnected pin errors)
#   - Component positions preserved
```

## Expected Result

**Current Implementation Status:**

- ✅ Initial generation: Op-amp with unused pins generated successfully
- ✅ Modified Python code accepts PinType.NO_CONNECT assignments
- ✅ Circuit regeneration succeeds with NO_CONNECT pins defined
- ✅ Component data structures preserve NO_CONNECT pin types
- ✅ Netlist exporter recognizes and handles NO_CONNECT pins
- ⚠️ **LIMITATION**: Schematic generator (sch_gen) doesn't currently export NO_CONNECT pin types to (no_connect) symbols in .kicad_sch files
- ✅ Component positions preserved during regeneration
- ✅ No errors or crashes when marking pins as NO_CONNECT

**When Schematic Generator is Enhanced:**

- ✅ Count of (no_connect) elements in .kicad_sch will be > 0
- ✅ Each unused pin will have corresponding no-connect symbol
- ✅ Symbols placed at correct pin coordinates
- ✅ ERC checks will accept the no-connect flags without errors

## Why This Is Critical

**Real circuit development workflow:**
1. Design circuit with microcontroller or op-amp IC
2. Not all pins used (e.g., spare op-amp stages, NC pins)
3. Without no-connect flags, ERC reports false "unconnected pin" errors
4. No-connect symbols explicitly mark intentional unused pins
5. ERC then passes without false positives

If this doesn't work:
- Users must manually add no-connect symbols in KiCad (defeating code-based design)
- ERC reports false errors on intentional unused pins
- Schematic validation workflow breaks
- Tool reliability decreases

If this works:
- Unused pins automatically marked as no-connect
- ERC validation passes cleanly
- Schematic design follows best practices
- Code-based circuit design is fully functional

## Success Criteria

This test PASSES when:
- Initial circuit generates correctly with no no-connect symbols
- After marking pins NO_CONNECT, symbols appear in schematic
- Count of (no_connect) elements increases (0 → N)
- Each symbol is at correct pin coordinates
- ERC validation accepts the no-connect flags
- No errors during regeneration
- Component positions preserved across regeneration
