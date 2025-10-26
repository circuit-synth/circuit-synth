# Test 05: Nets & Connectivity

## Purpose

Validates net handling: named nets, complex topologies, implicit vs explicit nets.

## Test Cases

### Test 5.1: Named Nets (VCC, GND, SIG)
- Create nets with specific names in Python
- Verify names preserved in KiCad
- Verify names preserved in round-trip

### Test 5.2: Rename Net (VCC → VDD)
- Start with VCC net
- Rename to VDD in Python
- Verify all connections updated

### Test 5.3: Multi-Point Net
- 5 components all connected to VCC
- Verify single net with 5 connection points
- No separate nets created

### Test 5.4: Implicit vs Explicit Nets
- Implicit: `r1[1] & r2[1]` (auto-named)
- Explicit: `VCC = Net("VCC")` then `r1[1] & VCC`
- Verify both work

### Test 5.5: Split Net (Disconnect Components)
- Start with R1-R2-R3 on same net
- Disconnect R3
- Verify R1-R2 still connected, R3 separate

### Test 5.6: Merge Nets (Connect Components)
- Start with two separate nets
- Connect them via new wire in KiCad
- Import to Python → verify single net

### Test 5.7: Power Nets (VCC, GND Symbols)
- Use KiCad power symbols
- Verify imported as nets in Python
- Verify connections to components

### Test 5.8: Complex Topology (Star Network)
- Central node connected to 6 components
- All on same net
- Verify topology preserved

## Manual Setup

**Fixtures needed:**
- `named_nets/` - VCC, GND, SIG examples
- `power_symbols/` - KiCad power symbol usage
- `complex_topology/` - Star or mesh network

## Success Criteria

- ✅ Named nets preserved both directions
- ✅ Multi-point nets work correctly
- ✅ Net modifications detected and applied
- ✅ No phantom nets or lost connections

---

**Status**: 🚧 Setup required
**Priority**: P1
**Time**: 30 min
