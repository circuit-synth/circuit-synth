# Test 06: Round-Trip Validation

## Purpose

🔴 **CRITICAL TEST** - Validates that circuits survive complete round-trip cycles without data loss.

## Test Cases

### Test 6.1: Python → KiCad → Python (Resistor Divider)
```
Input: resistor_divider.py
  ↓ Generate
KiCad project
  ↓ Import
Output: resistor_divider_generated.py

Expected: Output matches input (semantically)
```

### Test 6.2: KiCad → Python → KiCad (Resistor Divider)
```
Input: resistor_divider.kicad_pro
  ↓ Import
Python code
  ↓ Generate
Output: resistor_divider_generated.kicad_pro

Expected: Netlist equivalence (electrical identity)
```

### Test 6.3: Multiple Cycles (P→K→P→K→P→K)
- Run 3 complete round-trips
- Expected: Cycle 3 output = Cycle 1 output
- No data drift or accumulation

### Test 6.4: Netlist Equivalence
- Compare netlists using `kicad-cli`
- Verify electrical equivalence (not byte-for-byte)
- Allow for:
  - Different UUIDs
  - Different component ordering (if electrically same)
  - Minor formatting differences

### Test 6.5: Hierarchical Circuit Round-Trip
- 2-level hierarchy: main + subcircuit
- Full round-trip preserves structure
- Subcircuit still separate file

## Success Criteria

- ✅ Single round-trip preserves circuit function
- ✅ Multiple cycles are stable (no drift)
- ✅ Netlists are electrically equivalent
- ✅ Hierarchical structure preserved

## Known Acceptable Differences

**Python Code**:
- Variable names may change (if auto-generated)
- Comment formatting may differ
- Whitespace differences OK
- Import order may differ

**KiCad Files**:
- UUIDs will differ (expected)
- Component ordering may differ
- Formatting/indentation may differ
- Timestamps will differ

## Not Acceptable

**Data Loss**:
- Missing components
- Missing connections
- Wrong component values
- Lost net names

**Data Accumulation**:
- File size growing each cycle
- Duplicate comments/data
- Phantom components appearing

---

**Status**: 🚧 Setup required
**Priority**: P0 🔴 CRITICAL
**Time**: 20 min
