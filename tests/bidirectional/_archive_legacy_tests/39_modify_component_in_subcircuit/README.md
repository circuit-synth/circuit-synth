# Test 39: Modify Component in Subcircuit

## Priority: 0 (CRITICAL GAP)

## Overview
Tests modifying a component VALUE inside a subcircuit (not the root circuit) and validating that changes are correctly applied to the subcircuit sheet while preserving positions and leaving the parent circuit unchanged.

## Why This is Critical
**MAJOR GAP IDENTIFIED:** Almost all existing bidirectional tests (01-43) operate exclusively on the ROOT SHEET. This test addresses hierarchical operation support by validating component modifications WITHIN subcircuits.

This is a fundamental capability for hierarchical circuit design - users must be able to modify components inside subcircuits during iterative development.

## Test Scenario

### Initial State
- Hierarchical circuit with:
  - Root circuit: Contains main resistor R_main
  - Subcircuit "PowerSupply": Contains R1=1k, R2=2k

### Modification
1. Generate initial KiCad project with hierarchical structure
2. Synchronize back to capture positions
3. Modify R1 value in PowerSupply subcircuit: 1k → 10k
4. Regenerate KiCad

### Expected Results
- R1 in PowerSupply subcircuit has new value (10k)
- R1 position in subcircuit preserved
- R2 in subcircuit unchanged (still 2k)
- Root circuit completely unaffected
- Netlist reflects new R1 value in hierarchical context

## Validation Levels

### Level 1: File Existence
- PowerSupply subcircuit schematic file exists
- Root schematic file exists
- JSON netlist generated

### Level 2: Semantic Validation (kicad-sch-api)
- PowerSupply schematic contains R1 with value=10k
- PowerSupply schematic contains R2 with value=2k (unchanged)
- R1 position preserved across regeneration
- Root circuit unchanged

### Level 3: Netlist Validation
- JSON netlist hierarchical structure preserved
- PowerSupply subcircuit in JSON contains R1=10k
- Electrical connectivity correct

## Potential Failure Modes

This test may XFAIL if:
1. Synchronizer doesn't support hierarchical component access
2. Component modifications in subcircuits not supported
3. Position preservation fails for subcircuit components
4. Hierarchical structure lost during regeneration

## Success Criteria
- All validation levels pass
- R1 value correctly updated to 10k
- R1 position preserved in subcircuit
- R2 and root circuit unaffected
- Hierarchical structure maintained

## Related Tests
- Test 22: Add subcircuit sheet (hierarchical creation)
- Test 37: Replace subcircuit contents (complete redesign)
- Test 08: Modify component value (root sheet only)

## Files
- `subcircuit_with_resistors.py` - Fixture with PowerSupply subcircuit
- `test_39_modify_component_in_subcircuit.py` - Comprehensive pytest
- `README.md` - This file
