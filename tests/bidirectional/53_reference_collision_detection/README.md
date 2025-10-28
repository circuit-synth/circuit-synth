# Test 53: Reference Collision Detection (Priority 2)

## What This Tests

**Core Question**: When you have duplicate component references in a circuit, does the system properly detect and handle collisions?

This validates that **reference uniqueness checking works correctly** for both single-sheet and hierarchical circuits.

**Important**: circuit-synth enforces **GLOBAL reference uniqueness** across the entire hierarchy. This is stricter than KiCad, which allows the same reference on different hierarchical sheets (disambiguated by hierarchical paths). In circuit-synth, all references must be globally unique.

## When This Situation Happens

- Developer creates R1 on root sheet
- Later creates another R1 on the same sheet (should fail or auto-rename)
- Developer creates hierarchical circuit with R1 on root sheet
- Tries to create R1 on child sheet (fails in circuit-synth due to global uniqueness)
- Must use different reference (R2) on child sheet
- Critical for maintaining design integrity

## What Should Work

### Case 1: Duplicate References on Same Sheet (Should Fail/Auto-Rename)
1. Create circuit with R1
2. Try to add another R1 on the same sheet
3. System should either:
   - Raise error indicating duplicate reference
   - Auto-rename second R1 to R2
4. Only one R1 exists on the sheet after operation

### Case 2: Global Reference Uniqueness
1. Create hierarchical circuit with R1 on root sheet
2. Create subcircuit with R2 on child sheet (different reference required)
3. Generate KiCad project
4. Verify:
   - R1 component exists on root sheet
   - R2 component exists on child sheet
   - All references are globally unique
   - No duplicate reference errors
   - KiCad electrical rules pass

## Manual Test Instructions

### Test Case 1: Same Sheet Collision
```bash
cd /Users/shanemattner/Desktop/circuit-synth2/tests/bidirectional/53_reference_collision_detection

# Step 1: Generate circuit with duplicate R1 on same sheet
uv run duplicate_refs.py
# Expected: Either error message or auto-rename to R1, R2

# Step 2: Verify circuit if generated
open duplicate_refs/duplicate_refs.kicad_pro
# Verify: Only unique references (no duplicate R1 on same sheet)
```

### Test Case 2: Global Reference Uniqueness
```bash
# Step 1: Generate hierarchical circuit with R1 on root and R2 on child
uv run duplicate_refs.py

# Step 2: Open in KiCad
open duplicate_refs/duplicate_refs.kicad_pro
# Verify:
#   - Root sheet has R1
#   - Child sheet has R2 (not R1 - global uniqueness enforced)
#   - Both are visible and electrically distinct

# Step 3: Export netlist
kicad-cli sch export netlist duplicate_refs/duplicate_refs.kicad_sch --output duplicate_refs.net
# Verify:
#   - Netlist shows R1 and R2 components
#   - All references globally unique
#   - No netlist errors or warnings

# Step 4: Run electrical rules check in KiCad
# Verify: No duplicate reference errors reported
```

## Expected Result

### Case 1: Same Sheet
- ❌ Circuit generation fails with clear error message, OR
- ✅ Second R1 auto-renamed to R2
- ✅ Schematic shows R1 and R2 (or error prevents creation)
- ✅ No duplicate references on single sheet

### Case 2: Global Uniqueness
- ✅ KiCad generated with hierarchical structure
- ✅ Root sheet contains R1
- ✅ Child sheet contains R2 (different reference, globally unique)
- ✅ Netlist shows both R1 and R2:
  - R1 (root)
  - R2 (child)
- ✅ Electrical rules check passes (no duplicate reference errors)
- ✅ All references are globally unique across entire hierarchy

## Why This Is Important

**Reference uniqueness is critical for circuit integrity:**
- Duplicate references on same sheet cause electrical errors
- Ambiguous references create confusion during design and debugging
- Netlist generation can produce incorrect results
- PCB layout becomes impossible (which component gets placed where?)

**circuit-synth's global uniqueness approach:**
- **Simpler mental model**: All references must be unique, period
- **No ambiguity**: R1 always refers to exactly one component
- **Stricter than KiCad**: KiCad allows same ref on different sheets with hierarchical paths
- **Prevents confusion**: No need to track which sheet a reference is on
- **Easier debugging**: Reference collision caught immediately at creation time

**If collision detection works:**
- User gets clear error when creating duplicate reference anywhere in hierarchy
- System enforces global uniqueness across all sheets
- All references are unambiguous
- Circuit integrity maintained

**If collision detection fails:**
- Duplicate references silently break circuit
- Netlist generation produces incorrect connections
- PCB layout fails or produces wrong board
- Design integrity compromised

**This is PRIORITY 2** because while not common, duplicate references can silently corrupt designs.

## Validation Levels

### Level 2: Reference Uniqueness Checking
- Component references are globally unique across entire hierarchy
- Error handling for duplicate references anywhere in circuit
- Auto-rename functionality (if implemented)

### Level 3: Netlist Reference Validation
- Netlist contains all components with unique references
- R1 on root sheet
- R2 on child sheet (not R1)
- Electrical rules check passes (no duplicate reference errors)

## Success Criteria

This test PASSES when:

### Case 1: Same Sheet Collision
- Attempting to create duplicate R1 on same sheet either:
  - Raises clear error message indicating duplicate reference
  - Auto-renames second R1 to R2 or next available reference
- Only unique references exist on single sheet
- No silent failures or corrupted designs

### Case 2: Global Reference Uniqueness
- R1 component present on root sheet
- R2 component present on child sheet
- Netlist contains both R1 and R2 with unique references
- Netlist exports without errors
- Electrical rules check in KiCad passes
- All references globally unique across hierarchy
- No duplicate reference errors

## Implementation Notes

### KiCad Reference Scoping Rules
- KiCad allows references to be unique **within each sheet**
- KiCad allows same reference on **different hierarchical sheets**
- KiCad netlist uses **full hierarchical path** for disambiguation
- Example KiCad netlist paths:
  ```
  /R1               # Root sheet R1
  /SubCircuit/R1    # Child sheet R1
  /SubCircuit1/R1   # Another child R1
  ```

### circuit-synth Behavior (STRICTER than KiCad)
- **Enforces GLOBAL reference uniqueness** across entire hierarchy
- References must be unique everywhere, not just within each sheet
- Same reference on different sheets is NOT allowed
- Simpler mental model: R1 always means exactly one component
- Provides clear error messages for violations
- Example:
  ```python
  # Root sheet
  r1 = Component(ref="R1", ...)  # OK

  # Child sheet
  r1_child = Component(ref="R1", ...)  # ERROR! R1 already exists
  r2_child = Component(ref="R2", ...)  # OK - globally unique
  ```

### Test Strategy
- Test same-sheet collision first (should fail or auto-rename)
- Test global uniqueness enforcement (R1 + R2, not R1 + R1)
- Validate netlist contains unique references
- Verify electrical rules check passes
- Document that circuit-synth is stricter than KiCad
