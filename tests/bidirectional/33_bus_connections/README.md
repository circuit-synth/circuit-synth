# Test 33: Bus Connections (8-bit Data Bus)

## What This Tests

**Core Question**: When you have multiple components connected to the same multi-line bus (e.g., an 8-bit data bus D[0..7]), can you create and modify bus connections using array notation in Python code, and are the connections reflected correctly in the KiCad schematic and netlist?

This tests **bus connection validation** - creating electrical connections using multiple individual nets that together form a logical bus.

## When This Situation Happens

- Microcontroller, CPU, or digital logic circuits need bidirectional data buses
- Multiple devices (memory, peripherals, MCU) share data lines
- Bus notation (D[0..7], ADDR[0..15]) is common in real schematics
- Modifying which pins connect to which bus lines is part of iterative design

## What Should Work

1. Generate initial circuit with 8-bit data bus (D0-D7 nets)
   - Microcontroller (MCU) with pins D0-D7
   - Memory device (MEM) with pins D0-D7
   - All 8 data lines connecting both devices
2. Verify all 8 nets exist in netlist (D0, D1, D2, D3, D4, D5, D6, D7)
3. Modify one bus line (e.g., disconnect D0 from MEM, add to buffer instead)
4. Regenerate circuit
5. Validate netlist shows modified connection for D0
6. Other bus lines (D1-D7) unchanged

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth2/tests/bidirectional/33_bus_connections

# Step 1: Generate initial circuit with 8-bit data bus
uv run eight_bit_bus.py
open eight_bit_bus/eight_bit_bus.kicad_pro
# Verify:
#   - MCU component with D[0..7] pins visible
#   - MEM component with D[0..7] pins visible
#   - All 8 data lines connected (hierarchical labels on pins)
#   - Can see all labels: D0, D1, D2, D3, D4, D5, D6, D7

# Step 2: Check netlist for all bus connections
kicad-cli sch export netlist eight_bit_bus/eight_bit_bus.kicad_sch \
  --output eight_bit_bus/eight_bit_bus.net
# Verify netlist contains:
#   - 8 separate nets: D0, D1, D2, D3, D4, D5, D6, D7
#   - Each net connects MCU and MEM (2 nodes per net)

# Step 3: Edit eight_bit_bus.py to modify a bus connection
# Option A: Disconnect D0 from MEM:
#   - Remove: mcu_d0_net += mem[8]  (assuming pin 8 is MEM D0)
# Option B: Add a buffer device and connect D0 to it instead

# Step 4: Regenerate circuit
uv run eight_bit_bus.py

# Step 5: Verify modification in KiCad
open eight_bit_bus/eight_bit_bus.kicad_pro
# Verify:
#   - D0 now has different connections (or missing if disconnected)
#   - D1-D7 unchanged (still connect MCU and MEM)
#   - No overlap, all components visible
```

## Expected Result

- ✅ Initial generation: 8 separate data nets (D0-D7)
- ✅ Each net visible in schematic with hierarchical labels
- ✅ Netlist shows 8 nets with correct pin connections
- ✅ Can modify bus lines independently via Python
- ✅ Regeneration updates only modified nets
- ✅ All 8 bus lines clearly visible and named
- ✅ No bus notation errors in KiCad
- ✅ Multi-pin connections on buses work correctly

## Why This Is Important

**Real-world digital design patterns:**
1. Data buses (8-bit, 16-bit, 32-bit) are fundamental in microcontroller circuits
2. Address buses, control buses, bidirectional buses all use same pattern
3. Dynamic bus reconfiguration during iterative design:
   - Start with all pins connected
   - Later discover pin conflicts or routing issues
   - Need to reassign which pins connect to which bus lines
   - Regenerate without losing overall structure

**If this doesn't work:**
- Users cannot easily create bus-based circuits
- Cannot iteratively modify bus connections
- Must manually edit KiCad or create 8 separate nets manually
- Bus-based circuit development becomes tedious

**If this works:**
- Can define 8-bit buses with simple Python code
- Iterative bus modifications work seamlessly
- Real microcontroller circuit patterns become practical
- KiCad schematic shows professional bus notation

## Success Criteria

This test PASSES when:
- 8 separate nets created (D0-D7) and visible in schematic
- All nets properly connected to both MCU and MEM devices
- Netlist exports with all 8 nets and correct connections
- Can modify a single bus line without affecting others
- Regeneration updates only modified nets
- No errors or warnings when validating bus connections

## Additional Notes

- Uses hierarchical labels for electrical connections (no physical wires)
- Could extend test to 16-bit or 32-bit buses for more complex patterns
- Could test differential buses (with pairs like D_P/D_N)
- Bus notation example: D[0..7] means D0, D1, D2, D3, D4, D5, D6, D7
