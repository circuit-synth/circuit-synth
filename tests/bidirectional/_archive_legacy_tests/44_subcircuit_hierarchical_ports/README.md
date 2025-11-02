# Test 44: Subcircuit Hierarchical Ports

## What This Tests

**Core Question**: When you create a hierarchical circuit with subcircuits that have port connections (hierarchical labels in subcircuit and hierarchical pins on sheet symbol), do those ports synchronize correctly between parent and child sheets during bidirectional development?

This tests **hierarchical port management** - the mechanism by which nets flow between parent and subcircuit sheets via hierarchical labels and pins.

## Priority 0 Test - Critical for Hierarchical Design

This is a **Priority 0** test because hierarchical pin connections are fundamental to professional circuit design. Without working hierarchical ports, subcircuits are isolated and cannot communicate with parent circuits - defeating the entire purpose of hierarchical organization.

## When This Situation Happens

Real-world scenario (professional workflow):
1. Designer creates LED driver subcircuit that requires power (VCC, GND)
2. Parent circuit has power rails that need to connect to subcircuit
3. Designer defines ports on subcircuit (hierarchical labels inside subcircuit)
4. Designer connects parent nets to subcircuit ports (hierarchical pins on sheet symbol)
5. Later, designer adds new signal (e.g., ENABLE) that must flow from parent to subcircuit
6. Circuit-synth must update both hierarchical labels and pins accordingly

## What Should Work

### Initial State
1. Generate parent circuit with VCC and GND nets
2. Create LED subcircuit that needs VCC and GND
3. Connect parent VCC/GND to subcircuit via hierarchical ports
4. Validate:
   - Subcircuit .kicad_sch has hierarchical_label elements for VCC, GND
   - Parent .kicad_sch has sheet symbol with pin elements for VCC, GND
   - Netlist shows LED connected to parent's VCC/GND nets

### Dynamic Update
5. Add new net (SIGNAL) in parent
6. Connect SIGNAL to subcircuit (add new port)
7. Regenerate KiCad
8. Validate:
   - Subcircuit has new hierarchical_label for SIGNAL
   - Parent sheet symbol has new pin for SIGNAL
   - Netlist shows connectivity for new signal

## How Hierarchical Ports Work in KiCad

### KiCad's Hierarchical Mechanism

Hierarchical ports connect parent and child sheets using two paired elements:

**In Subcircuit (.kicad_sch):**
```lisp
(hierarchical_label "VCC"
  (shape input)
  (at 100.0 50.0 0)
  (effects (font (size 1.27 1.27)))
  (uuid "...")
)
```

**In Parent Sheet (.kicad_sch):**
```lisp
(sheet
  (at 35.56 34.29)
  (size 43.02 25.4)
  ...
  (property "Sheetname" "LED_Driver" ...)
  (property "Sheetfile" "led_driver.kicad_sch" ...)
  (pin "VCC" passive
    (at 77.31 36.83 0)
    (effects (font (size 1.27 1.27)))
    (uuid "...")
  )
  (pin "GND" passive
    (at 77.31 39.37 0)
    (effects (font (size 1.27 1.27)))
    (uuid "...")
  )
)
```

### Key Concepts

**Hierarchical Labels (in subcircuit):**
- Appear INSIDE the subcircuit schematic file
- Mark connection points where nets enter/exit the subcircuit
- Have position, shape (input/output/bidirectional), and name

**Hierarchical Pins (on sheet symbol in parent):**
- Appear on the SHEET SYMBOL in the parent schematic
- Connect parent nets to subcircuit hierarchical labels
- Must have matching names to corresponding hierarchical labels
- Have position on sheet symbol boundary, type (input/output/passive)

**Net Flow:**
1. Parent net connects to sheet symbol pin (e.g., parent VCC → sheet pin "VCC")
2. Sheet pin "VCC" connects to hierarchical label "VCC" inside subcircuit
3. Subcircuit hierarchical label "VCC" connects to component pins inside subcircuit
4. Result: parent VCC net electrically connects to subcircuit components

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth2/tests/bidirectional/44_subcircuit_hierarchical_ports

# Step 1: Generate initial hierarchical circuit with power connections
uv run led_subcircuit.py
open led_subcircuit/led_subcircuit.kicad_pro

# Step 2: Verify hierarchical ports exist
# In KiCad:
#   - Open parent sheet (led_subcircuit.kicad_sch)
#   - See sheet symbol for LED_Driver with VCC and GND pins on border
#   - Open LED_Driver sheet (double-click or via hierarchy navigator)
#   - See hierarchical labels for VCC and GND inside subcircuit
#   - See LED component with connections to VCC, GND labels

# Step 3: Verify netlist connectivity
# Tools → Generate Netlist → Export
# Check that LED pins connect to parent VCC/GND nets

# Step 4: Modify Python to add new signal (SIGNAL net to subcircuit)
# Edit led_subcircuit.py to add SIGNAL net connection

# Step 5: Regenerate and verify new port added
uv run led_subcircuit.py
open led_subcircuit/led_subcircuit.kicad_pro
# Verify:
#   - Sheet symbol now has SIGNAL pin
#   - Subcircuit has SIGNAL hierarchical label
#   - Netlist shows SIGNAL connectivity
```

## Expected Result

**Initial Generation:**
- ✅ Parent circuit has VCC, GND nets
- ✅ LED_Driver sheet symbol appears on parent with VCC, GND pins
- ✅ LED_Driver.kicad_sch exists with hierarchical labels for VCC, GND
- ✅ LED component connected to hierarchical labels
- ✅ Netlist shows LED connected to parent VCC/GND

**After Adding New Signal:**
- ✅ Sheet symbol has new SIGNAL pin
- ✅ Subcircuit has new SIGNAL hierarchical label
- ✅ Netlist reflects new connectivity
- ✅ All existing hierarchical labels preserved (VCC, GND still present)

## Known Issue (Issue #380)

**Potential Failure Mode:**
The synchronizer may NOT remove old hierarchical labels when connections change. This could cause:
- Old hierarchical labels to remain even if port removed
- Extra pins on sheet symbol
- Netlist confusion with disconnected ports

**If this test fails due to Issue #380:** Mark test as XFAIL and document the specific behavior observed.

## Why This Is Important

**Hierarchical design is THE professional workflow for complex circuits:**

1. **Power Distribution**: Every subcircuit needs power - hierarchical ports distribute VCC/GND
2. **Signal Flow**: Control signals, data buses, clocks flow between subsystems via ports
3. **Modularity**: Reusable subcircuits (USB port, power supply, MCU) need well-defined interfaces
4. **Organization**: Large designs become unmanageable without hierarchical structure
5. **Team Collaboration**: Different engineers work on different subcircuits with defined interfaces

**Real-world impact:**
- Multi-board systems (e.g., ESP32 dev board with USB, power, debug, LED subsystems)
- Signal integrity (differential pairs crossing hierarchy)
- Power integrity (ensuring all subcircuits properly powered)
- Design reuse (standard subcircuits like USB ports, power regulators)

If hierarchical ports don't work, circuit-synth cannot support professional multi-sheet design.

## Success Criteria

This test PASSES when:
- Parent sheet has sheet symbol with hierarchical pins matching subcircuit ports
- Subcircuit has hierarchical labels for all ports
- Pin names on sheet symbol match hierarchical label names
- Netlist shows electrical connectivity across hierarchy (parent net → sheet pin → hierarchical label → component)
- Adding new port dynamically updates both sheet pins and hierarchical labels
- No duplicate or orphaned hierarchical labels/pins

## Validation Level

**Level 2 (kicad-sch-api Semantic Validation):**
- Parse parent .kicad_sch to verify sheet symbol and hierarchical pins
- Parse subcircuit .kicad_sch to verify hierarchical labels
- Check pin/label name matching

**Level 3 (Netlist Validation):**
- Export netlist via kicad-cli
- Parse netlist to verify connectivity across hierarchy
- Confirm LED pins connect to parent VCC/GND nets

## Related Tests

- **Test 22**: Add subcircuit sheet (basic hierarchy, no cross-sheet connections)
- **Test 23**: Remove subcircuit sheet (hierarchy removal)
- **FUTURE_TESTS.md Category B**: Advanced hierarchical tests (multi-instance sheets, deep nesting)

## Notes

- This test validates the CORE hierarchical port mechanism
- Focus on label-based connectivity (circuit-synth uses labels, not physical wires)
- Tests both initial generation AND dynamic updates (bidirectional workflow)
- May expose Issue #380 if old hierarchical labels aren't cleaned up
- Essential foundation for all advanced hierarchical tests
