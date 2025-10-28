# Test 44: Subcircuit Hierarchical Ports - Creation Summary

## Test Created Successfully

This test validates **hierarchical port synchronization** - the core mechanism for connecting parent and subcircuit sheets in professional hierarchical design.

## Files Created

### 1. README.md (8.3 KB)
Comprehensive documentation including:
- What this tests (hierarchical port synchronization)
- Priority 0 designation (critical for hierarchical design)
- Real-world scenarios and professional workflows
- How KiCad hierarchical ports work (technical explanation)
- Manual test instructions
- Expected results
- Known Issue #380 documentation
- Success criteria
- Validation levels (Level 2 + Level 3)

### 2. led_subcircuit.py (2.7 KB)
Python fixture demonstrating:
- Parent circuit with VCC, GND power nets
- LED_Driver subcircuit with LED and current-limiting resistor
- Hierarchical port connections via `add_subcircuit(connections=...)`
- Modification markers for test to inject new signals
- Clear documentation of hierarchical port creation

### 3. test_44_subcircuit_hierarchical_ports.py (16 KB)
Comprehensive automated test with:
- **8 validation steps**:
  1. Generate with VCC, GND hierarchical ports
  2. Validate hierarchical labels in subcircuit (Level 2)
  3. Validate hierarchical pins on sheet symbol (Level 2)
  4. Validate label/pin name matching
  5. Validate netlist connectivity (Level 3)
  6. Add new SIGNAL port to Python
  7. Regenerate KiCad
  8. Validate new SIGNAL label/pin added dynamically

- **Level 2 Validation** (kicad-sch-api):
  - Regex parsing of hierarchical_label elements in subcircuit
  - Regex parsing of pin elements on sheet symbol in parent
  - Name matching verification

- **Level 3 Validation** (kicad-cli):
  - Netlist export via kicad-cli
  - Netlist parsing for electrical connectivity
  - Cross-hierarchy net verification

- **Test Quality**:
  - Comprehensive step-by-step output
  - Detailed error messages
  - Try/finally cleanup
  - --keep-output flag support
  - Issue #380 documentation

## Why This Test Is Critical (Priority 0)

Hierarchical ports are THE fundamental mechanism for professional circuit design:

1. **Power Distribution**: Every subcircuit needs power (VCC, GND) - hierarchical ports distribute it
2. **Signal Flow**: Control signals, data buses, clocks flow between subsystems via ports
3. **Modularity**: Reusable subcircuits (USB port, power supply, MCU) need well-defined interfaces
4. **Organization**: Large designs become unmanageable without hierarchical structure
5. **Team Collaboration**: Different engineers work on different subcircuits with defined interfaces

**Without working hierarchical ports, circuit-synth cannot support professional multi-sheet design.**

## Technical Validation

### Hierarchical Label Detection
```python
# Regex pattern for hierarchical_label in subcircuit
hierarchical_label_pattern = r'\(hierarchical_label\s+"([^"]+)"'
labels = re.findall(pattern, subcircuit_content)
```

### Hierarchical Pin Detection
```python
# Regex pattern for pin on sheet symbol in parent
sheet_pin_pattern = r'\(pin\s+"([^"]+)"\s+(input|output|bidirectional|passive)'
pins = re.findall(pattern, parent_content)
```

### Label/Pin Matching
- Verifies all hierarchical labels have corresponding sheet pins
- Ensures pin names match label names (VCC ↔ VCC, GND ↔ GND)

### Netlist Validation
- Exports netlist via `kicad-cli sch export netlist`
- Parses netlist to verify:
  - VCC and GND nets exist
  - LED (D1) and resistor (R1) appear in netlist
  - Connectivity across hierarchy preserved

## Test Workflow Pattern

Follows established bidirectional test pattern:
1. **Initial state**: Generate with minimal ports (VCC, GND)
2. **Validation**: Verify initial hierarchical structure
3. **Modification**: Add new port (SIGNAL) in Python
4. **Regeneration**: Regenerate KiCad project
5. **Validation**: Verify dynamic update (new SIGNAL port added)
6. **Preservation**: Verify original ports (VCC, GND) preserved

This pattern validates **iterative development workflow** - the killer feature of circuit-synth.

## Known Issues

### Issue #380: Synchronizer Label Cleanup
The synchronizer may not remove old hierarchical labels when connections change.

**Impact on Test 44:**
- If SIGNAL port is later removed, old SIGNAL hierarchical label may remain
- Old sheet pins may not be cleaned up
- Results in orphaned/extra labels and pins

**Mitigation:**
- Test documents expected behavior
- If test fails due to Issue #380, mark as XFAIL
- Test provides clear diagnostics to identify Issue #380 symptoms

## Success Metrics

Test PASSES when:
- ✅ Initial generation creates VCC, GND hierarchical labels and pins
- ✅ Labels in subcircuit match pins on sheet symbol (name matching)
- ✅ Netlist shows electrical connectivity across hierarchy
- ✅ Adding new SIGNAL port creates both label and pin
- ✅ Original VCC, GND ports preserved during regeneration
- ✅ No duplicate or orphaned labels/pins (unless Issue #380)

## Integration with Test Suite

- **Category**: Hierarchical Design (Tests 22-23, 44)
- **Priority**: 0 (Critical hierarchical feature)
- **Validation Level**: Level 2 (kicad-sch-api) + Level 3 (kicad-cli netlist)
- **Related Tests**:
  - Test 22: Add subcircuit sheet (basic hierarchy, no cross-sheet connections)
  - Test 23: Remove subcircuit sheet
  - FUTURE_TESTS.md Category B: Advanced hierarchical tests (50-66)

## Running the Test

```bash
# Run test individually
cd tests/bidirectional/44_subcircuit_hierarchical_ports
pytest test_44_subcircuit_hierarchical_ports.py -v

# Run with output preserved
pytest test_44_subcircuit_hierarchical_ports.py -v --keep-output

# Run test as part of full suite
cd tests/bidirectional
pytest -v

# Manual verification
uv run led_subcircuit.py
open led_subcircuit/led_subcircuit.kicad_pro
```

## Conclusion

Test 44 successfully created with:
- ✅ Comprehensive README.md documenting hierarchical ports
- ✅ Python fixture demonstrating hierarchical port creation
- ✅ Automated test with 8 validation steps
- ✅ Level 2 + Level 3 validation
- ✅ Issue #380 awareness and documentation
- ✅ Follows established test patterns
- ✅ Priority 0 designation justified

**This test validates the core mechanism for professional hierarchical circuit design in circuit-synth.**
