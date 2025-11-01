# Test 42: Move Component Between Sheets

**Priority:** Priority 1 (Important)

## Overview

This test validates the ability to move a component from the root sheet to a subcircuit sheet in a hierarchical KiCad project. Unlike copying (test 41), this test moves the component - it should disappear from the source sheet and appear on the destination sheet.

## Test Scenario

1. Create root circuit with R1, R2
2. Create subcircuit with R3
3. Generate to KiCad, synchronize back
4. Move R2 from root to subcircuit (becomes R4 or renumbered)
5. Regenerate and validate:
   - R1 remains on root with position preserved
   - R2 removed from root
   - R2 (or R4) appears in subcircuit
   - R3 unaffected in subcircuit
   - Netlist reflects new hierarchy

## Validation Levels

### Level 2: Semantic Structure Validation
- Components appear on correct sheets (kicad-sch-api)
- R1 exists on root sheet only
- R2 removed from root sheet
- R4 (or R2) exists on subcircuit sheet
- R3 unaffected on subcircuit sheet
- Component positions preserved for unmoved components

### Level 3: Electrical Validation
- JSON netlist shows correct sheet assignment
- Moved component's nets properly reflect new sheet location
- No orphaned nets on source sheet
- Netlist hierarchy matches physical sheet structure

## Key Requirements

- **Reference Management:** Test reference renumbering if needed (R2 → R4)
- **Position Preservation:** Unmoved components (R1, R3) keep original positions
- **Net Reassignment:** Component's nets move with it to new sheet
- **Netlist Validation:** Hierarchical structure reflects move
- **Clean Migration:** No artifacts left on source sheet

## Expected Behavior

### Before Move (Initial State)
```
Root Sheet:
  - R1 (10k) at position (X1, Y1)
  - R2 (10k) at position (X2, Y2)

Subcircuit Sheet:
  - R3 (1k) at position (X3, Y3)
```

### After Move
```
Root Sheet:
  - R1 (10k) at position (X1, Y1) [PRESERVED]

Subcircuit Sheet:
  - R3 (1k) at position (X3, Y3) [PRESERVED]
  - R4 (10k) at position (X2, Y2) [MOVED from root, reference renumbered]
```

## Files

1. **README.md** - This file
2. **multi_sheet.py** - Circuit fixture with root and subcircuit
3. **test_42_move_between_sheets.py** - Automated test

## Current Status

**XFAIL Expected** - The synchronizer may not yet support moving components between sheets. This requires:
- Detecting component removal from source sheet
- Adding component to destination sheet
- Reference renumbering to avoid conflicts
- Net reassignment to new sheet context
- Position preservation during move

## Related Tests

- Test 41: Copy component cross-sheet (duplicates, doesn't move)
- Test 39: Modify component in subcircuit (changes properties)
- Test 37: Replace subcircuit contents (bulk changes)
- Test 22: Add subcircuit sheet (creates hierarchy)
- Test 23: Remove subcircuit sheet (removes hierarchy)

## Why This Matters

Moving components between sheets is a common refactoring operation in hierarchical designs:
- Reorganizing circuit modules
- Splitting complex root sheets
- Creating reusable subcircuits from existing circuits
- Improving circuit hierarchy organization

Position preservation during moves ensures the visual layout remains consistent, which is crucial for:
- Maintaining readability
- Preserving user's organizational work
- Enabling confident refactoring
- Supporting iterative design improvements
