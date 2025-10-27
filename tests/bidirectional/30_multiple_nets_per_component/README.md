# Test 30: Multiple Nets Per Component

## What This Tests

**Core Question**: When a single component participates in multiple nets (R1[1] on NET1, R1[2] on NET2), do both hierarchical labels appear correctly on their respective pins?

This tests **bidirectional sync for multi-net component topology** - ensuring components can participate in multiple electrical connections simultaneously without conflicts.

## When This Situation Happens

- Developer creates component connected to multiple nets
- Common pattern: resistor between two signals, IC with multiple power/signal pins
- Each pin connected to different net
- Regenerates KiCad expecting multiple labels per component

## What Should Work

1. Generate initial KiCad with R1[1] on NET1, R1[2] on NET2
2. Verify both labels appear on correct pins
3. Edit Python to change one net
4. Regenerate - both labels update correctly
5. No interference between labels on different pins

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional/30_multiple_nets_per_component

# Step 1: Generate initial KiCad project
uv run resistor_two_nets.py
open resistor_two_nets/resistor_two_nets.kicad_pro
# Verify:
#   - R1 pin 1 has "NET1" label
#   - R1 pin 2 has "NET2" label
#   - Both labels present simultaneously

# Step 2: Edit resistor_two_nets.py to change NET2 name
# Change line:
#   net2 = Net(name="NET2")
# To:
#   net2 = Net(name="SIGNAL_OUT")

# Step 3: Regenerate KiCad project
uv run resistor_two_nets.py

# Step 4: Open regenerated KiCad project
open resistor_two_nets/resistor_two_nets.kicad_pro
# Verify:
#   - R1 pin 1 still has "NET1" label (unchanged)
#   - R1 pin 2 has "SIGNAL_OUT" label (changed from NET2)
#   - Both labels still present
#   - No interference between the two nets
```

## Expected Result

- ✅ Initial generation: R1 pin 1 has "NET1", pin 2 has "NET2"
- ✅ Both labels appear simultaneously
- ✅ After rename: pin 1 unchanged, pin 2 updates
- ✅ No label conflicts or missing labels
- ✅ Each pin correctly labeled with its net

**Expected sync summary:**
```
Actions:
   ✅ Keep: R1 (matches Python)
   ✅ Keep net: NET1 (unchanged)
   🔄 Rename net: NET2 → SIGNAL_OUT
   🏷️  Update label: NET2 → SIGNAL_OUT on R1 pin 2
   ✅ NET1 label on pin 1 unchanged
```

## Likely Actual Result (Based on #344, #345)

**Prediction:** May see label conflicts or missing labels

- ❌ Only one label appears (first net wins)
- ❌ Labels conflict or overwrite each other
- ❌ Rename doesn't update label on pin 2
- ❌ Labels appear on wrong pins
- ❌ Sync confused by multiple nets per component

## Why This Is Important

**Extremely common pattern in real circuits:**
- Pull-up/pull-down resistors (pin 1 to signal, pin 2 to power)
- Voltage dividers (pin 1 to input, pin 2 to output)
- ICs with multiple power domains (VDD, VDDIO, etc.)
- Multi-function components (each pin different signal)

If multiple nets don't work:
- Can't model basic circuit patterns
- Schematic shows incorrect connections
- PCB netlist incomplete
- Library fundamentally limited

## Success Criteria

This test PASSES when:
- Both labels present on correct pins
- No label conflicts or overwrites
- Can rename one net without affecting other
- Sync summary shows independent net handling
- Electrical connections correct in KiCad

## Related Tests

- **Test 27** - Change pin on net (moves label between pins)
- **Test 28** - Split net (one net becomes multiple)
- **Test 11** - Add component to net (single net case)

## Related Issues

- **#344** - Net sync doesn't add labels (both labels may fail)
- **#345** - New component on net doesn't get labels
- **#336** - Component operations may fail
- **#338** - Rename operations may fail

## Edge Cases to Consider

**After this basic test works:**
- Three or more nets per component (multi-pin ICs)
- Swap nets between pins (NET1/NET2 → NET2/NET1)
- Remove one net, keep other
- Add third net to existing two-net component
- Auto-generated net names with multiple nets
- Power nets vs signal nets on same component

## Real-World Examples

**Pull-up resistor:**
```python
# R1[1] to GPIO signal
# R1[2] to VCC power rail
net_gpio = Net(name="GPIO_PIN")
net_gpio += r1[1]

net_vcc = Net(name="VCC")
net_vcc += r1[2]
```

**Voltage divider:**
```python
# R1[1] to input signal
# R1[2] to divider midpoint
# R2[1] to divider midpoint
# R2[2] to ground
```

**This test verifies the foundation for these patterns.**
