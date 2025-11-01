# Test 40: Net Operations in Subcircuit

## Priority 0 - Hierarchical Operations Gap

**Status:** ✅ Implemented
**Category:** Hierarchical Net Operations
**Difficulty:** High
**Related Issues:** #380 (hierarchical label synchronization)

## Overview

Tests adding and modifying electrical connections (nets) INSIDE a subcircuit (child sheet), not on the root sheet. This is a critical hierarchical design capability that validates:

1. **Net creation within subcircuits** - Can we programmatically connect components on child sheets?
2. **Hierarchical label generation** - Do labels appear correctly for cross-sheet connectivity?
3. **Parent circuit awareness** - Does the parent circuit see new hierarchical pins?
4. **Netlist connectivity** - Does electrical connectivity work through hierarchy?

**Why Priority 0:** ALL current tests (01-43) only test operations on the root sheet. This is the first test to validate net operations within hierarchical sheets - a critical gap for real-world hierarchical design workflows.

## Test Scenario

### Initial State
Hierarchical circuit with:
- **Root sheet**: Empty (no components)
- **Subcircuit "SubCircuit"**: Two resistors (R1, R2) that are **disconnected**

### Operation
Add a net connecting R1 pin 1 to R2 pin 2 **inside the subcircuit**.

### Expected Results
1. **Subcircuit internal:** Net "NET1" exists connecting R1[1] to R2[2]
2. **Hierarchical labels:** Labels appear on subcircuit sheet for the connection
3. **Parent awareness:** Root circuit sees subcircuit with hierarchical pins (if exposed)
4. **Netlist validation:** KiCad-exported netlist shows R1[1] and R2[2] connected

## Validation Levels

### Level 1: File Structure (Basic)
- ✅ Subcircuit schematic file exists
- ✅ JSON netlist contains subcircuit with components

### Level 2: Semantic Structure (kicad-sch-api)
- ✅ Hierarchical labels exist on subcircuit sheet
- ✅ Labels have correct net name ("NET1")
- ✅ Component positions preserved in subcircuit

### Level 3: Electrical Connectivity (Netlist)
- ✅ KiCad-exported netlist shows R1 and R2 connected
- ✅ Net name matches expected ("NET1")
- ✅ Pin-level connectivity validated

## Workflow

```
Step 1: Generate hierarchical circuit with disconnected R1, R2 in subcircuit
   ├─ Root sheet: Empty (just contains subcircuit reference)
   └─ Subcircuit: R1 (10k), R2 (4.7k) - NO connection

Step 2: Synchronize to KiCad
   ├─ Verify subcircuit schematic file created
   └─ Verify R1 and R2 exist but are isolated

Step 3: Add net in Python: subcircuit.add_net("NET1", [R1[1], R2[2]])
   └─ This is the KEY operation - net inside subcircuit, not root

Step 4: Regenerate KiCad from modified Python
   └─ Force fresh generation to see changes

Step 5: Validate hierarchical labels appeared
   ├─ Subcircuit sheet should have hierarchical labels "NET1"
   ├─ Labels should be at R1 pin 1 and R2 pin 2 locations
   └─ Component positions preserved

Step 6: Validate electrical connectivity via netlist
   ├─ Export KiCad netlist using kicad-cli
   ├─ Parse netlist to extract net information
   └─ Verify NET1 contains (R1, 1) and (R2, 2)
```

## Implementation Details

### Python Code Structure
```python
from circuit_synth import circuit, Component, Circuit, Net

@circuit(name="subcircuit_disconnected")
def subcircuit_disconnected():
    """Hierarchical circuit with subcircuit containing disconnected resistors."""
    from circuit_synth.core.decorators import get_current_circuit
    root = get_current_circuit()

    # Create subcircuit with disconnected components
    sub = Circuit("SubCircuit")
    r1 = Component(symbol="Device:R", ref="R1", value="10k",
                   footprint="Resistor_SMD:R_0603_1608Metric")
    r2 = Component(symbol="Device:R", ref="R2", value="4.7k",
                   footprint="Resistor_SMD:R_0603_1608Metric")

    sub.add_component(r1)
    sub.add_component(r2)

    # START_MARKER: Test will add net connection here
    # END_MARKER

    root.add_subcircuit(sub)
```

### Test Modification
The test modifies the code to add between markers:
```python
net1 = Net("NET1")
r1[1] += net1
r2[2] += net1
```

## Key Technical Points

### Accessing Subcircuit Components
```python
# After loading circuit from KiCad/Python:
subcircuit = circuit.subcircuits[0]
r1 = next(c for c in subcircuit.components if c.reference == "R1")
r2 = next(c for c in subcircuit.components if c.reference == "R2")

# Add net to subcircuit (not root circuit)
net1 = Net("NET1")
r1[1] += net1
r2[2] += net1
```

### Hierarchical Labels
When you add a net inside a subcircuit:
- **Local to subcircuit:** Net connects components within the sheet
- **Hierarchical labels:** Created at component pins to enable parent connectivity
- **NOT global labels:** These are hierarchical (sheet-scoped) labels
- **Parent exposure:** If net is exposed via hierarchical pins, parent sees it

### Netlist Validation
```python
# KiCad netlist shows flattened hierarchy:
# (net (code "1") (name "/SubCircuit/NET1")
#   (node (ref "R1") (pin "1"))
#   (node (ref "R2") (pin "2"))
# )
```

## Known Limitations

### Issue #380: Hierarchical Label Synchronization
**Problem:** When modifying nets in subcircuits, old hierarchical labels may not be removed, leading to duplicate or stale labels.

**Workaround:** Test may use `@pytest.mark.xfail(reason="Issue #380: Old labels not removed")` if synchronizer doesn't clean up properly.

**Test Behavior:**
- Test validates NET CREATION works (new labels appear)
- May xfail if OLD labels aren't removed properly
- Netlist connectivity is the ultimate validation (Level 3)

## Comparison to Other Tests

| Test | Operation | Sheet | Coverage |
|------|-----------|-------|----------|
| 11 | Add net to components | Root | ✅ Root-level connectivity |
| 40 | Add net in subcircuit | Subcircuit | ✅ Hierarchical connectivity |
| 10 | Generate with net | Root | ✅ Initial net creation |
| 10H (future) | Generate with net | Subcircuit | ❌ Not yet implemented |

**Test 40 is the first to validate net operations within hierarchy!**

## Success Criteria

✅ **Test passes when:**
1. Net can be added to subcircuit programmatically
2. Hierarchical labels appear on subcircuit sheet
3. KiCad netlist shows correct connectivity
4. Component positions preserved within subcircuit
5. No crashes or validation errors

❌ **Test may xfail (acceptable) when:**
1. Old hierarchical labels not removed (Issue #380)
2. Duplicate labels exist but connectivity is correct

## Files Generated

```
tests/bidirectional/40_net_operations_in_subcircuit/
├── README.md                          # This file
├── subcircuit_disconnected.py         # Fixture with disconnected resistors
├── test_40_net_operations_in_subcircuit.py  # Automated test
└── subcircuit_disconnected/           # Generated (with --keep-output)
    ├── subcircuit_disconnected.kicad_pro
    ├── subcircuit_disconnected.kicad_sch  # Root sheet
    ├── SubCircuit.kicad_sch           # Subcircuit sheet
    └── subcircuit_disconnected.json   # JSON netlist
```

## Usage

```bash
# Run test
pytest tests/bidirectional/40_net_operations_in_subcircuit/test_40_net_operations_in_subcircuit.py -v

# Keep generated files for inspection
pytest tests/bidirectional/40_net_operations_in_subcircuit/test_40_net_operations_in_subcircuit.py -v --keep-output

# Run only this test with detailed output
pytest tests/bidirectional/40_net_operations_in_subcircuit/test_40_net_operations_in_subcircuit.py -v -s
```

## Related Tests

- **Test 11:** Add net to components (root sheet only)
- **Test 22:** Add subcircuit sheet (hierarchical structure)
- **Test 38:** Empty subcircuit (hierarchical edge case)
- **Future Test 10H:** Generate with net on child sheet

## References

- **Issue #380:** Hierarchical label synchronization gap
- **FUTURE_TESTS.md:** Section on hierarchical testing gap
- **kicad-sch-api:** For schematic semantic validation
