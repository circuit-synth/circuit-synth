# Test 46: Export Power Symbols to KiCad

**Priority:** Priority 1 (Important)

**Status:** Automated

## Test Scenario

Validates the EXPORT direction of power symbol bidirectional workflow:
- Test 45: KiCad → Python (import power symbols) ✓
- Test 46: Python → KiCad (export power symbols) ← THIS TEST

## Real-World Workflow

1. Create Python circuit with multiple power domains (VCC_3V3, VCC_5V, VCC_12V, GND, AGND)
2. Generate to KiCad with power symbols
3. Validate all 5 power symbols created correctly
4. Synchronize back, add component using VCC_3V3
5. Regenerate and validate:
   - Existing power symbols preserved
   - New component connected to existing VCC_3V3 symbol
   - No duplicate power symbols created

## Why This Test Matters

**Complete Power Bidirectional Coverage:**
- Test 45 validates IMPORT (KiCad → Python)
- Test 46 validates EXPORT (Python → KiCad)
- Together: complete round-trip power symbol support

**Multiple Power Domains:**
- Real embedded systems use multiple voltage rails
- Different power domains must not interfere
- Analog vs digital ground separation (AGND vs GND)

**Power Symbol Reuse:**
- Adding components should reuse existing power symbols
- No duplicate symbols per domain
- Efficient, clean KiCad schematics

## Test Steps

### Step 1: Generate circuit with 5 power domains
- Create R1→VCC_3V3, R2→VCC_5V, R3→VCC_12V, R4→GND, R5→AGND
- Generate to KiCad
- **Validate:** 5 distinct power symbols created

### Step 2: Validate initial power symbol structure
- Check power symbol count (5 symbols)
- Verify symbol types (power:VCC, power:GND variations)
- Confirm symbol positioning
- **Level 2 validation:** Symbol count and types correct

### Step 3: Validate initial electrical connectivity
- Export netlist using kicad-cli
- Parse power net assignments
- Verify each component on correct power domain
- **Level 3 validation:** Netlist shows correct power connectivity

### Step 4: Add new component using existing power domain
- Modify Python: add R6 connected to VCC_3V3 (same as R1)
- Regenerate circuit
- **Validate:** R6 shares VCC_3V3 symbol with R1

### Step 5: Validate no duplicate power symbols
- Check power symbol count still 5 (not 6)
- Verify VCC_3V3 symbol reused for R1 and R6
- Confirm other power symbols unchanged
- **Level 2 validation:** Symbol reuse working

### Step 6: Validate final electrical connectivity
- Export netlist
- Verify VCC_3V3 net contains both R1 and R6
- Confirm other power domains unchanged
- **Level 3 validation:** Power symbol reuse electrically correct

## Validation Levels

- **Level 2:** Power symbol count, types, positioning
- **Level 3:** Netlist electrical connectivity validation

## Files

- `multi_power_domain.py` - Circuit with 5 power domains
- `test_46_export_power.py` - Automated test script
- `README.md` - This file

## Success Criteria

1. All 5 power domains export as power symbols
2. Correct power symbol types for each domain
3. No duplicate symbols when reusing power domain
4. Netlist validates electrical connectivity
5. Analog vs digital ground properly separated

## Related Tests

- Test 16: Add power symbol (single domain)
- Test 17: Add ground symbol
- Test 18: Multiple power domains
- Test 45: Import power symbols from KiCad (reverse direction)
- Test 47: Power symbols in subcircuits

## Notes

- Complements test 45 for complete power bidirectional coverage
- Tests 5 distinct power domains (not just VCC/GND)
- Validates analog vs digital ground separation (AGND vs GND)
- Ensures power symbol reuse prevents schematic clutter
