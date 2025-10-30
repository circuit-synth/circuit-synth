# Test 66: Duplicate Net Names Isolation (SAFETY TEST)

## What This Tests

**Core Question**: If two different circuits use the same net name `Net("SIGNAL")`, do they remain electrically isolated or do they accidentally connect?

This validates the **critical safety property of net namespace isolation** - preventing dangerous accidental connections between unrelated circuits.

## When This Situation Happens

- Developer creates `circuit_a` with `Net("SIGNAL")` connecting R1—R2
- Developer creates `circuit_b` with `Net("SIGNAL")` connecting R3—R4 (reuses name)
- Main circuit instantiates both: `circuit_a()` and `circuit_b()`
- **Critical question**: Are these two separate nets or one merged net?
- **Expected (SAFE)**: Two separate nets, no connection between R1 and R3
- **Dangerous (BUG)**: One merged net, R1—R2—R3—R4 all connected!

## What Should Work

```python
@circuit(name="circuit_a")
def circuit_a():
    r1 = Component(...)
    r2 = Component(...)
    signal = Net("SIGNAL")  # circuit_a's SIGNAL
    r1[1] += signal
    r2[1] += signal

@circuit(name="circuit_b")
def circuit_b():
    r3 = Component(...)
    r4 = Component(...)
    signal = Net("SIGNAL")  # circuit_b's SIGNAL (SAME NAME!)
    r3[1] += signal
    r4[1] += signal

@circuit(name="main")
def main():
    circuit_a()  # Has its own Net("SIGNAL")
    circuit_b()  # Has its own Net("SIGNAL")
```

**Expected netlist:**
```
Net 1 (circuit_a's SIGNAL):
  - R1 pin 1
  - R2 pin 1

Net 2 (circuit_b's SIGNAL):
  - R3 pin 1
  - R4 pin 1

R1 NOT connected to R3 ✓
```

**Dangerous bug (MUST NOT HAPPEN):**
```
Net 1 (merged SIGNAL):
  - R1 pin 1
  - R2 pin 1
  - R3 pin 1  ← WRONG!
  - R4 pin 1  ← WRONG!

R1 connected to R3 ✗ (SAFETY VIOLATION)
```

## Manual Test Instructions

```bash
cd tests/bidirectional/66_duplicate_net_names_isolation

# Step 1: Generate circuits with duplicate net names
uv run isolated_circuits.py
open isolated_circuits/isolated_circuits.kicad_pro
# Verify: R1, R2, R3, R4 all visible

# Step 2: Export netlist to check electrical connectivity
kicad-cli sch export netlist isolated_circuits/isolated_circuits.kicad_sch \
  --output isolated_circuits.net

# Step 3: Examine netlist (CRITICAL VALIDATION)
cat isolated_circuits.net
# Look for net blocks:
#   - One net should have R1 and R2
#   - Different net should have R3 and R4
#   - R1 should NOT be in same net as R3

# Example of CORRECT netlist:
# (net (code "1") (name "/circuit_a/SIGNAL")
#   (node (ref "R1") (pin "1"))
#   (node (ref "R2") (pin "1")))
#
# (net (code "2") (name "/circuit_b/SIGNAL")
#   (node (ref "R3") (pin "1"))
#   (node (ref "R4") (pin "1")))

# Step 4: Verify in KiCad GUI
# - R1 and R2 should have one net label
# - R3 and R4 should have different net label
# - No wire connecting R1 to R3
```

## Expected Result

- ✅ R1—R2 connected via circuit_a's Net("SIGNAL")
- ✅ R3—R4 connected via circuit_b's Net("SIGNAL")
- ✅ R1 NOT connected to R3 (nets are isolated)
- ✅ Netlist shows two separate nets with same base name
- ✅ Net names might be scoped: `/circuit_a/SIGNAL` and `/circuit_b/SIGNAL`
- ✅ No electrical connection between the two SIGNAL nets

## Why This Is CRITICAL

**This is a SAFETY test - if it fails, circuits can accidentally short together!**

### Scenario: Power distribution bug
```python
@circuit(name="analog_section")
def analog_section():
    # Analog 3.3V rail
    vcc = Net("VCC")
    op_amp = Component(...)
    op_amp["V+"] += vcc

@circuit(name="digital_section")
def digital_section():
    # Digital 5V rail (DIFFERENT voltage!)
    vcc = Net("VCC")  # SAME NAME as analog!
    mcu = Component(...)
    mcu["VDD"] += vcc
```

**If nets merge:**
- ❌ 3.3V analog rail connected to 5V digital rail
- ❌ Components destroyed by overvoltage
- ❌ Dangerous hardware bug from simple naming

**If nets isolated:**
- ✅ 3.3V analog rail separate from 5V digital rail
- ✅ Components safe
- ✅ Developer must explicitly connect rails if needed

### Why isolation is correct behavior:

1. **Explicit is better than implicit** - developer must explicitly pass nets to connect circuits
2. **Prevents accidental shorts** - same name doesn't mean same net
3. **Local reasoning** - each circuit's nets are scoped to that circuit
4. **Safety by default** - no surprise connections
5. **Hierarchical organization** - each circuit is isolated namespace

## Success Criteria

This test PASSES when:
- Four components generated (R1, R2, R3, R4)
- Netlist shows two separate nets
- R1 and R2 on one net (circuit_a's SIGNAL)
- R3 and R4 on different net (circuit_b's SIGNAL)
- R1 NOT connected to R3 (net isolation verified)
- Net names may be scoped with circuit hierarchy

This test FAILS when:
- ❌ R1 and R3 on same net (safety violation!)
- ❌ All four resistors on one merged net
- ❌ Duplicate net names cause automatic merging

## Validation Level

**Level 3 (Netlist Comparison)**: CRITICAL - netlist is only way to prove isolation

- kicad-sch-api for component verification
- kicad-cli netlist export
- Parse netlist to find which components are on which nets
- Prove R1 and R3 are on DIFFERENT nets
- This cannot be validated visually - MUST use netlist

## Related Tests

- **Test 24** - Cross-sheet connection (explicit net passing - CORRECT way to connect circuits)
- **Test 10** - Add net to components (same sheet)

## Design Philosophy

**Circuit-synth principle: No global nets, all connections explicit**

This test validates that circuit-synth follows this principle:
- Each `@circuit` function has isolated net namespace
- `Net("SIGNAL")` in circuit_a ≠ `Net("SIGNAL")` in circuit_b
- To connect circuits, developer must explicitly pass Net objects
- No implicit connections based on name matching
- Safety by default

## What Happens If This Test Fails

If this test fails (duplicate net names merge):

1. **Immediate action**: Create GitHub issue marked CRITICAL
2. **Impact**: Safety violation - accidental circuit connections
3. **Root cause**: Net namespace not properly isolated
4. **Fix needed**: Ensure each circuit has separate net namespace
5. **Priority**: BLOCKING - must fix before any hierarchical features ship

## Edge Cases

**Power nets (VCC, GND, etc.):**
- Power symbols are intentionally global across entire design
- This is KiCad convention (VCC connects everywhere)
- But user-defined nets like Net("VCC") should still be circuit-scoped
- Only power symbols (not Net() objects) should be global

**Hierarchical net names:**
- KiCad may prefix nets with hierarchy: `/circuit_a/SIGNAL` vs `/circuit_b/SIGNAL`
- This is acceptable - proves nets are isolated
- Net names don't have to match in .kicad_sch as long as they're separate

## Test Status

⚠️ **Status: Unknown - needs first execution**

This is a new safety test. First execution will reveal if net isolation works correctly.

If PASSES: ✅ Net namespace isolation working - safe to use
If FAILS: ❌ CRITICAL safety bug - must fix immediately
