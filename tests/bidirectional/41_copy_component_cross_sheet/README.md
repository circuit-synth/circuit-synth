# Test 41: Copy Component Cross Sheet

**Priority:** 0 (Critical - Real-world workflow)

## Overview

Tests the KILLER FEATURE: position preservation when a circuit is duplicated from one sheet to another. This is a fundamental workflow where users:

1. Create circuit in Python
2. Generate to KiCad and make it visually pretty (arrange components, route wires)
3. Copy and paste the circuit to a different sheet/subcircuit
4. Expect positions to be preserved

## Real-World Scenario

A user designs a voltage divider on the root sheet, spends time arranging components in KiCad for optimal clarity, then wants to reuse that same circuit block in multiple subcircuits. The circuit should appear with the SAME layout in each location, not regenerated with random positions.

## Why This Is Critical

**Position preservation is the foundation of practical KiCad workflow:**
- Users invest time in component placement
- Visual clarity matters for board layout
- Copy-paste is faster than redesigning
- Consistency across sheets improves readability
- Supports modular circuit design patterns

## Test Cases

### Test 1: Copy to Empty Subcircuit
1. Create R1-R2 voltage divider on root sheet
2. Generate to KiCad, synchronize back (captures positions)
3. Create subcircuit sheet
4. Duplicate divider as R3-R4 in subcircuit
5. Regenerate and validate:
   - R1-R2 positions preserved on root
   - R3-R4 created in subcircuit with same relative positions
   - Both circuits electrically independent
   - Netlist shows both voltage dividers

### Test 2: Copy to Non-Empty Subcircuit
1. Subcircuit already has R5 component with position
2. Copy divider as R6-R7 alongside existing R5
3. Validate:
   - R1-R2 original positions preserved
   - R5 existing position preserved
   - R6-R7 created with copied positions
   - All components coexist without conflicts

## Technical Challenges

### UUID-Based Component Matching
- Components identified by UUID across sheets
- Same component can't exist on multiple sheets
- Copied components need new UUIDs
- Position data must transfer with copies

### Reference Numbering
- R3-R4 must not conflict with root R1-R2
- Reference designators must be unique across project
- Automatic renumbering when copying

### Sheet Hierarchy
- Root sheet vs subcircuit sheet semantics
- Hierarchical labels and connections
- Cross-sheet netlist generation

### Position Data Structure
- Positions are sheet-specific
- Must preserve relative positions when copying
- May need position offset when pasting

## Expected Validation Levels

**Level 2: Symbol file validation**
- Components exist in correct sheets
- Positions match expected coordinates
- UUIDs are unique across sheets
- References are unique

**Level 3: Netlist validation**
- Independent nets for each divider
- No electrical connection between copies
- Both dividers show correct connectivity

## Possible XFAIL Scenarios

May need XFAIL if:
- Synchronizer doesn't support cross-sheet operations
- Position data doesn't transfer across sheets
- UUID generation conflicts with existing components
- Netlist generator doesn't handle hierarchical sheets

## Success Criteria

Test passes when:
1. Components can be copied from root to subcircuit
2. Original positions are preserved after regeneration
3. Copied positions match original relative layout
4. Both circuits are electrically independent
5. All references and UUIDs are unique
6. Netlist correctly represents both circuits

## Related Tests

- Test 22: Add subcircuit sheet (hierarchical structure)
- Test 23: Remove subcircuit sheet (cleanup)
- Test 27: Modify component positions (position preservation)
- Test 31: Update component reference (reference management)
