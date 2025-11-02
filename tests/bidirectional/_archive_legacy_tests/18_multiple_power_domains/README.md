# Test 18: Multiple Power Domains (Multi-Voltage Circuit)

## Status

✅ **PASSING** (as of 2025-10-28)

**Fixed in PR #396:** Power symbol replacement now works correctly when component power nets change. Old power symbols are properly removed and replaced with new ones, preventing text overlap.

**Test Coverage:**
- ✅ Multiple independent power rails (VCC, 3V3, 5V, GND)
- ✅ Power symbol generation for each domain
- ✅ Power domain modification (R2 from 3V3 → 5V)
- ✅ Power symbol replacement (no text overlap)
- ✅ Position preservation during power net changes
- ✅ Netlist validation for electrical connectivity

## What This Tests

**Core Question**: Can circuit-synth correctly handle circuits with multiple independent power rails (VCC, 3V3, 5V, GND) and validate that each component connects to the correct power domain?

This validates **multi-voltage circuit design** - a critical feature for real-world embedded systems that often use multiple supply voltages.

## When This Situation Happens

- Embedded system designs commonly use multiple voltages:
  - Primary power (VCC 12V or 24V)
  - Logic supply (5V or 3.3V)
  - Analog supply (separate from digital)
  - Ground (reference net)
- Each component must connect to the correct power domain
- Adding or modifying components may require changing their power connection
- Netlist must clearly show which components are on which power rail

## What Should Work

1. Generate circuit with 4 resistors on different power domains:
   - R1 → VCC (12V)
   - R2 → 3V3 (3.3V)
   - R3 → 5V (5V)
   - R4 → GND (0V reference)
2. Validate netlist shows 4 separate power nets (VCC, 3V3, 5V, GND)
3. Validate each resistor connected to correct power domain
4. Modify Python to change R2 from 3V3 to 5V
5. Regenerate KiCad project
6. Validate netlist shows R2 now on 5V net
7. Validate all positions preserved (iterative development)

## Manual Test Instructions

### Phase 1: Initial Multi-Voltage Circuit

```bash
cd /Users/shanemattner/Desktop/circuit-synth2/tests/bidirectional/18_multiple_power_domains

# Step 1: Generate initial circuit with multiple power domains
uv run multi_voltage_circuit.py
open multi_voltage_circuit/multi_voltage_circuit.kicad_pro

# Verify in KiCad:
#   - R1 has VCC label
#   - R2 has 3V3 label
#   - R3 has 5V label
#   - R4 has GND label
#   - Four distinct net labels visible
#   - No connections between resistors (each on separate power domain)
```

### Phase 2: Validate Initial Netlist

```bash
# Step 2: Export netlist and verify power domain assignments
kicad-cli sch export netlist \
  multi_voltage_circuit/multi_voltage_circuit.kicad_sch \
  --output multi_voltage_circuit/multi_voltage_circuit.net

# Verify in netlist:
#   - VCC net contains: R1 pin 1
#   - 3V3 net contains: R2 pin 1
#   - 5V net contains: R3 pin 1
#   - GND net contains: R4 pin 1
#   - Four separate nets (not all connected together)
```

### Phase 3: Modify R2 Power Domain

```bash
# Step 3: Edit multi_voltage_circuit.py
# Change line with R2 definition:
#   FROM: net_5v = Net(name="5V")
#         net_5v += r2[1]
#   TO:   net_5v += r2[1]  # Now R2 is on 5V instead of 3V3

# Remove R2 from 3V3:
#   FROM: net_3v3 = Net(name="3V3")
#         net_3v3 += r2[1]
#   TO:   (remove this line)

# Save the modified Python file

# Step 4: Regenerate with modified power domain
uv run multi_voltage_circuit.py

# Step 5: Open regenerated schematic
open multi_voltage_circuit/multi_voltage_circuit.kicad_pro

# Verify changes:
#   - R2 now has 5V label (not 3V3)
#   - R2 position preserved (didn't move)
#   - Other components (R1, R3, R4) unchanged
#   - Schematic is still readable
```

### Phase 4: Validate Modified Netlist

```bash
# Step 6: Re-export netlist and verify updated power domain
kicad-cli sch export netlist \
  multi_voltage_circuit/multi_voltage_circuit.kicad_sch \
  --output multi_voltage_circuit/multi_voltage_circuit.net

# Verify netlist now shows:
#   - VCC net: R1 pin 1 (unchanged)
#   - 3V3 net: (empty or removed - R2 no longer here)
#   - 5V net: R2 pin 1, R3 pin 1 (R2 moved here)
#   - GND net: R4 pin 1 (unchanged)
#   - Two of the original four nets now have 2 components each
```

## Expected Result

### Phase 1 (Initial Generation):
- ✅ All 4 resistors present: R1, R2, R3, R4
- ✅ Each has correct hierarchical label: VCC, 3V3, 5V, GND
- ✅ Components positioned with no overlaps
- ✅ 4 distinct power nets visible in schematic

### Phase 2 (Initial Netlist Validation):
- ✅ VCC net contains: R1 pin 1
- ✅ 3V3 net contains: R2 pin 1
- ✅ 5V net contains: R3 pin 1
- ✅ GND net contains: R4 pin 1
- ✅ Four separate nets (not cross-connected)

### Phase 3 (R2 Modification):
- ✅ R2 successfully moved from 3V3 to 5V net
- ✅ 5V net now has two components: R2 and R3
- ✅ R2 position preserved (not reset to default)
- ✅ All other components unchanged

### Phase 4 (Modified Netlist):
- ✅ 5V net now contains: R2 pin 1, R3 pin 1
- ✅ 3V3 net is empty or removed
- ✅ VCC and GND nets unchanged
- ✅ Netlist correctly reflects Python changes

## Why This Is Critical

**Multi-voltage designs are universal in real circuits:**
- Microcontroller (3.3V) + peripherals (5V) + power management (12V)
- Analog circuits requiring separate analog supply
- High-current digital + low-noise analog sections
- Battery-powered systems with multiple voltage rails

**Without proper multi-voltage support:**
- Users can't accurately represent their circuits
- Component-to-power connections are ambiguous
- Electrical errors possible (wrong voltage applied)
- Circuit documentation becomes unclear

**This test validates:**
1. Multiple power nets can coexist
2. Components reliably connect to correct power domain
3. Modifying power connections works correctly
4. Netlist accurately reflects power domain assignments
5. Iterative development works (positions preserved)

## Success Criteria

This test PASSES when:
- Initial circuit generates with 4 distinct power nets
- Netlist shows correct component-to-power mappings
- R2 can be moved from 3V3 to 5V without issues
- Modified netlist shows updated power domain
- Component positions preserved across regenerations
- No duplicate or missing nets in generated schematic

## Related Tests

- **Test 10-12** - Basic net operations (single net)
- **Test 26** - Power symbol replacement (power semantics)
- **Test 28** - Ground plane handling (future)
- **Test 29** - Power distribution network (future)

## Edge Cases to Explore Later

- More than 4 power domains (6+ rails)
- Power domain naming conventions (VCC vs +12V vs PWR_IN)
- Mixing power symbols and hierarchical labels across domains
- Power net isolation and short-circuit detection
- Multi-sheet designs with shared power domains
- Dynamic power domain switching (enable pins)

## Notes

**Level 3 Validation:**
- Netlist comparison for electrical connectivity
- Power net segregation verification
- Component-to-domain mapping confirmation

This test is CRITICAL for real-world circuit design support.
