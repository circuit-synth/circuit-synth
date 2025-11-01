# Test 60: Remove Hierarchical Pin

## Priority
Priority 1 (Important)

## Objective
Test bidirectional synchronization when removing a hierarchical pin connection from a subcircuit interface.

## Test Scenario

### Initial State
1. Create hierarchical circuit with subcircuit
2. Subcircuit has 3 hierarchical pins: VCC, GND, SIGNAL
3. Component inside subcircuit connected to all three
4. Generate to KiCad and synchronize back

### Modification
1. Remove SIGNAL connection from component in Python
2. Component only needs VCC and GND now
3. Regenerate and synchronize

### Expected Results
1. **Sheet Symbol (Root):**
   - SIGNAL pin removed from sheet symbol
   - VCC and GND pins preserved
   - Sheet still properly sized

2. **Subcircuit Sheet:**
   - SIGNAL hierarchical label removed
   - VCC and GND labels preserved
   - Component disconnected from SIGNAL net

3. **Netlist:**
   - SIGNAL net no longer appears
   - VCC and GND nets preserved
   - Component only connected to VCC, GND

4. **Validation:**
   - No orphaned labels
   - No orphaned wires
   - Clean netlist with reduced connectivity

## Real-World Use Case
Simplifying interfaces when:
- Removing unused signals from components
- Reducing pin count on modules
- Eliminating debug signals from production designs
- Simplifying power distribution (removing intermediate voltages)

## Known Issue: #380
**This test directly validates Issue #380:**
- Synchronizer may not remove old SIGNAL hierarchical label
- Old SIGNAL pin may remain on sheet symbol
- Expected to XFAIL until Issue #380 is resolved

## Validation Levels
- **Level 1:** Basic file structure and syntax
- **Level 2:** Pin/label removed from both sheets, remaining pins preserved
- **Level 3:** Netlist shows only VCC/GND connectivity, no SIGNAL net

## Test Structure
```
60_remove_hierarchical_pin/
├── README.md
├── three_pin_subcircuit.py          # Initial circuit with 3 pins
└── test_60_remove_pin.py            # Test script with modification
```

## Implementation Notes
1. Use simple resistor component (easy to verify connections)
2. Start with 3 clear hierarchical pins
3. Remove middle signal (SIGNAL) to test selective removal
4. Keep power pins (VCC, GND) to verify unaffected elements
5. Validate at multiple levels:
   - File structure (sheet exists)
   - Pin presence (SIGNAL removed, VCC/GND present)
   - Netlist connectivity (SIGNAL net gone)

## Expected Failure Mode
Until Issue #380 is resolved:
- Old SIGNAL label may remain in subcircuit
- Old SIGNAL pin may remain on sheet symbol
- Test marked as XFAIL with reference to #380
- Test will pass once synchronizer properly removes old elements
