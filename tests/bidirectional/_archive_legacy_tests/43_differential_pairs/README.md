# Test 43: Differential Pairs

## What This Tests

**Core Question**: Can you create USB differential pairs (D+ and D- signals) in Python code with proper naming and pairing, generate them in KiCad, and modify individual differential lines while preserving pair relationships?

This tests **differential pair recognition and handling** - creating paired nets with complementary naming conventions and validating that modifications preserve both signals in the pair.

## When This Situation Happens

- USB, LVDS, or high-speed serial circuits require differential pairs
- USB has D+ (D positive) and D- (D negative) signals that must be paired
- Need to connect differential pairs from a buffer/transceiver to a USB connector
- Modifying one differential line should preserve the pair relationship
- Layout and signal integrity depend on pairing being recognized

## What Should Work

1. Generate initial circuit with USB differential pair (D+ and D-)
   - USB Connector (USB_B_Micro or similar)
   - Buffer/transceiver component (e.g., TUSB2077 USB hub IC)
   - Net("USB_DP") for D+ signal
   - Net("USB_DM") for D- signal
   - Both nets connecting appropriate pins
2. Verify both USB_DP and USB_DM nets exist in schematic and netlist
3. Verify correct pins are connected (Level 3 netlist analysis)
4. Modify one differential signal in Python
5. Regenerate circuit
6. Validate change is reflected in schematic and netlist
7. Verify positions are preserved, both signals remain paired

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth2/tests/bidirectional/43_differential_pairs

# Step 1: Generate initial circuit with USB differential pair
uv run usb_differential_pair.py
open usb_differential_pair/usb_differential_pair.kicad_pro

# Verify in KiCad:
#   - USB connector component visible
#   - Buffer/transceiver component visible
#   - Hierarchical labels USB_DP and USB_DM on their pins
#   - Both labels visible on correct pins
#   - Components positioned without overlap

# Step 2: Check netlist for differential pair connections
kicad-cli sch export netlist usb_differential_pair/usb_differential_pair.kicad_sch \
  --output usb_differential_pair/usb_differential_pair.net

# Verify netlist contains:
#   - USB_DP net with correct connections
#   - USB_DM net with correct connections
#   - Both nets connecting USB connector and buffer pins

# Step 3: Edit usb_differential_pair.py to modify a differential signal
# Example: Change which pins the differential pair connects to
# Or: Add termination resistors to the differential pair

# Step 4: Regenerate circuit
uv run usb_differential_pair.py

# Step 5: Verify modification in KiCad
open usb_differential_pair/usb_differential_pair.kicad_pro

# Verify:
#   - USB_DP and USB_DM still both exist
#   - Connections reflect the modifications
#   - No component overlap
#   - Both signals remain electrically connected
```

## Expected Result

- ✅ Initial generation: USB_DP and USB_DM nets created
- ✅ Both nets visible in schematic with correct pins
- ✅ Netlist shows both USB_DP and USB_DM with proper connections
- ✅ Can modify individual differential signals via Python
- ✅ Regeneration updates modified connections
- ✅ Pair relationship preserved (both signals always exist together)
- ✅ Component positions preserved during regeneration
- ✅ No naming conflicts or duplicate nets

## Why This Is Important

**Real-world high-speed communication patterns:**
1. USB, LVDS, HDMI, and other protocols require differential pairs
2. Differential pairs must be:
   - Properly named (D+/D- or DP/DM convention)
   - Routed together on PCB for signal integrity
   - Length-matched to prevent timing skew
   - Impedance-matched for proper termination
3. Dynamic pair reconfiguration during iterative design:
   - Start with basic USB connectivity
   - Later add ESD protection devices
   - Add series termination resistors
   - Swap differential pair routing

**If this doesn't work:**
- Users cannot easily create differential pair circuits
- Pair relationships may be lost during modifications
- Signal integrity issues arise from improper handling
- Manual KiCad editing required instead of Python automation

**If this works:**
- Can define USB and other differential pairs simply in Python
- Pair relationships preserved through regeneration
- Real USB/LVDS/HDMI circuit development becomes practical
- KiCad schematic shows professional differential pair notation

## Success Criteria

This test PASSES when:
- USB_DP and USB_DM nets created and visible in schematic
- Both nets properly connected to USB connector and buffer pins
- Netlist exports with both nets and correct connections
- Can modify a single differential signal without losing the pair
- Regeneration updates modified connections while preserving pair
- Positions preserved across regeneration cycles
- No naming conflicts or duplicate nets

## Additional Notes

- Uses hierarchical labels for electrical connections (no physical wires)
- Differential pair naming convention: Signal_P / Signal_N or Signal_DP / Signal_DM
- Could extend test to LVDS, HDMI, or other differential protocol pairs
- Future enhancement: Validate length matching recommendations
- Future enhancement: ESD protection device integration

## Level 3 Validation (Electrical/Netlist)

This test validates:
- Schematic structure using kicad-sch-api (component placement, labels)
- KiCad netlist export showing actual connections
- Circuit-synth netlist showing intended connections
- Pin-to-pin electrical connectivity via netlist parsing
- Modification detection: before/after netlist comparison
