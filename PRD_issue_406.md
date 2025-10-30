# PRD: Fix Hierarchical Subcircuit Sheet Generation (Issue #406)

## Problem Statement

**Critical Bug:** Hierarchical circuits with subcircuits fail to generate separate KiCad sheet files (.kicad_sch), breaking a core feature of circuit-synth.

**Current Behavior:**
- Test 22 automated test PASSES (validates JSON structure only)
- Manual validation FAILS (no separate .kicad_sch files generated for subcircuits)
- Only root sheet file is created
- No hierarchical sheet symbol appears on root sheet linking to subcircuit
- Synchronizer crashes on second run with `'str' object has no attribute 'name'`

**Impact:**
- Severity: CRITICAL (Priority 0 test)
- Blocks manual validation of all hierarchical tests (22-65, ~44 tests)
- Breaks hierarchical design workflow - a killer feature
- False positive in test suite (passing test doesn't validate actual functionality)

---

## Expected Behavior

When a Python circuit defines a subcircuit using `root.add_subcircuit(child_sheet)`:

### File Structure
```
hierarchical_circuit/
├── hierarchical_circuit.kicad_pro
├── hierarchical_circuit.kicad_sch          # Root sheet with R1 + hierarchical sheet symbol
├── ChildSheet.kicad_sch                    # NEW: Child sheet file with R2
└── hierarchical_circuit.kicad_pcb
```

### KiCad Schematic Structure
1. **Root sheet** (`hierarchical_circuit.kicad_sch`):
   - Contains R1 component
   - Contains hierarchical sheet symbol linking to ChildSheet.kicad_sch
   - Sheet symbol shows sheet name and file path

2. **Child sheet** (`ChildSheet.kicad_sch`):
   - Separate .kicad_sch file
   - Contains R2 component
   - Has hierarchical labels for connections to parent sheet

### User Experience
- Open `hierarchical_circuit.kicad_pro` in KiCad
- See R1 on root sheet
- See hierarchical sheet symbol for ChildSheet
- Double-click sheet symbol → opens ChildSheet.kicad_sch with R2

---

## Current Implementation Analysis

### What Currently Works ✅
- Python `Circuit.add_subcircuit()` API exists and is used in 44 tests
- JSON netlist correctly captures hierarchical structure
- Test validates JSON structure (subcircuits array populated)
- Components are flattened onto single root sheet (intentional intermediate state?)

### What's Broken ❌
1. **No separate .kicad_sch file generation** for subcircuits
2. **No hierarchical sheet symbol** on root sheet
3. **Synchronizer error** when loading sheet on second run
4. **Test doesn't validate actual KiCad behavior** - only JSON structure

### Code Gaps Identified

From test expectations (lines 203-208):
```python
# Check that both schematic files exist
sch_files = list(output_dir.glob("*.kicad_sch"))
# Currently finds only 1 file (root)
# Expected: 2 files (root + child)
```

Test explicitly notes (line 270-271):
```python
# Note: KiCad schematic file currently uses flattened structure
# (hierarchy is preserved in JSON for future sheet separation)
```

**This suggests hierarchical sheet file generation was planned but not implemented.**

---

## ROOT CAUSE IDENTIFIED ✅

### The Real Problem

**Hierarchical sheet generation WORKS on first generation**, but **synchronizer CRASHES on second generation**.

**Timeline:**
1. First `generate_kicad_project()`: Creates root + child .kicad_sch files ✅
2. User modifies Python code
3. Second `generate_kicad_project()`:
   - Synchronizer loads existing schematic
   - **CRASHES** with `'str' object has no attribute 'name'`
   - Falls back to root-only generation
   - Child sheet disappears

**Error Location:** `/src/circuit_synth/kicad/schematic/hierarchical_synchronizer.py:134-138`

```python
if hasattr(sheet_elem, "properties"):
    for prop in sheet_elem.properties:  # prop is a STRING, not object!
        if prop.name == "Sheetfile":      # ← CRASH HERE
            sheet_file = prop.value
```

**The Bug:** Code assumes `prop` is an object with `.name` and `.value` attributes, but kicad-sch-api returns strings or different structure.

### Why Test Passes But Manual Fails

- **Automated test:** Deletes output directory before each run → always "first generation" → works
- **Manual workflow:** Keeps output directory → triggers synchronizer → crashes

### The Fix

Need to fix hierarchical_synchronizer.py to correctly parse sheet properties from kicad-sch-api.

## Root Cause Investigation Plan

### Questions to Answer

1. **Architecture Questions:**
   - Where in the codebase should subcircuit .kicad_sch files be generated?
   - Is there existing code that attempts this but fails silently?
   - What is the relationship between JSON hierarchy and KiCad file structure?

2. **Implementation Questions:**
   - Does `generate_kicad_project()` iterate over subcircuits?
   - Is there code to create hierarchical sheet symbols on root sheet?
   - Is there code to generate child .kicad_sch files?
   - How should sheet file names be determined? (circuit name? sheet name?)

3. **Synchronizer Questions:**
   - Why does synchronizer crash with `'str' object has no attribute 'name'`?
   - What does synchronizer expect when loading hierarchical sheets?
   - Is synchronizer trying to load subcircuit sheets that don't exist?

4. **Test Questions:**
   - Why does automated test pass when functionality is broken?
   - Should test validate actual .kicad_sch file existence?
   - What is the correct validation strategy for hierarchical circuits?

---

## Technical Investigation Areas

### 1. KiCad Project Generation
**Files:**
- `src/circuit_synth/core/circuit.py` (generate_kicad_project)
- `src/circuit_synth/kicad/atomic_integration.py`

**Investigation:**
- Does `generate_kicad_project()` recursively process subcircuits?
- Where is schematic file writing logic?
- Is there a TODO or placeholder for hierarchical sheet generation?

### 2. Schematic Writing
**Files:**
- `src/circuit_synth/kicad/sch_gen/schematic_writer.py`

**Investigation:**
- Does schematic writer support multiple output files?
- Is there code for hierarchical sheet symbols?
- How are components assigned to sheets?

### 3. Hierarchical Synchronizer
**Files:**
- `src/circuit_synth/kicad/schematic/hierarchical_synchronizer.py`

**Investigation:**
- What causes `'str' object has no attribute 'name'` error?
- How does synchronizer handle missing child sheet files?
- What is the expected sheet loading pattern?

### 4. Netlist Service
**Files:**
- `src/circuit_synth/kicad/netlist_service.py`

**Investigation:**
- How does JSON hierarchy map to KiCad sheet structure?
- Is there a conversion step that's missing?

---

## Success Criteria

### Functional Requirements
1. ✅ Generate separate .kicad_sch file for each subcircuit
2. ✅ Create hierarchical sheet symbol on parent sheet linking to child
3. ✅ Child sheet contains correct components
4. ✅ Sheet symbols show correct file paths
5. ✅ Synchronizer can load multi-sheet hierarchies without errors
6. ✅ Opening in KiCad shows full hierarchical structure

### Test Requirements
1. ✅ Test 22 validates actual .kicad_sch file existence (not just JSON)
2. ✅ Test validates hierarchical sheet symbol presence
3. ✅ Test validates child sheet component placement
4. ✅ No synchronizer errors on regeneration
5. ✅ Manual validation passes (open in KiCad, verify sheets exist)

### Documentation Requirements
1. ✅ Test comments accurately reflect validation performed
2. ✅ README updated if hierarchical sheet generation has limitations
3. ✅ Code comments explain sheet file naming strategy

---

## Implementation Strategy (TBD)

### Phase 1: Investigation (First Session - 30 min)
Using iterative log-driven cycles to understand current state:

1. **Cycle 1-3: Map data flow** (10 min)
   - Add logs to `generate_kicad_project()`
   - Trace how subcircuits are processed (or not)
   - Identify where schematic files are written

2. **Cycle 4-6: Find the gap** (10 min)
   - Locate schematic writer code
   - Check if it supports multi-file output
   - Verify hierarchical sheet symbol generation exists

3. **Cycle 7-8: Understand synchronizer error** (5 min)
   - Add logs to synchronizer loading
   - Reproduce error with logs
   - Identify what object has wrong type

4. **Cycle 9-10: Document findings** (5 min)
   - Create issue comment with findings
   - Update this PRD with root cause
   - Plan implementation approach

### Phase 2: Implementation (TBD - depends on findings)
Will be defined after Phase 1 investigation completes.

Likely tasks:
- Add multi-file schematic generation
- Implement hierarchical sheet symbol creation
- Fix synchronizer to handle missing sheets gracefully
- Update test to validate file existence

### Phase 3: Verification (15 min)
- Run test 22 with manual verification
- Open in KiCad, verify sheets exist
- Test synchronizer with multiple regenerations
- Verify tests 23-65 still pass

---

## Open Questions for User

### Critical Architectural Questions

**Q1: Sheet File Naming Strategy**
- Should child sheet filename be based on Circuit name or sheet name?
- Example options:
  - Option A: Use circuit name → `ChildSheet.kicad_sch`
  - Option B: Use parent name + suffix → `hierarchical_circuit_ChildSheet.kicad_sch`
  - Option C: Let user specify filename explicitly

**Your preference?**

**Q2: Hierarchical Sheet Symbol Placement**
- Where should hierarchical sheet symbols be placed on parent sheet?
- Options:
  - Option A: Auto-placement algorithm (what strategy?)
  - Option B: Manual placement via position parameter
  - Option C: Grid-based layout (e.g., each child gets column)

**Your preference?**

**Q3: Sheet UUID Handling**
- How should KiCad sheet UUIDs be generated?
- Options:
  - Option A: Deterministic (based on sheet name hash)
  - Option B: Random UUID each generation
  - Option C: Persistent UUIDs stored in JSON

**Your preference?**

### Implementation Scope Questions

**Q4: Error Handling for Missing Sheets**
- Should synchronizer gracefully handle missing child sheets?
- Scenario: User deletes child .kicad_sch file manually
- Options:
  - Option A: Error and stop (current behavior)
  - Option B: Warning and regenerate missing sheet
  - Option C: Ask user what to do

**Your preference?**

**Q5: Test Coverage Strategy**
- Should we add KiCad file validation to ALL hierarchical tests (22-65)?
- Options:
  - Option A: Yes, validate files in every test (thorough but slow)
  - Option B: No, only validate in test 22 (fast but less coverage)
  - Option C: Sample validation (e.g., every 5th test)

**Your preference?**

**Q6: Backward Compatibility**
- Should we support existing projects with flattened hierarchy?
- Options:
  - Option A: Auto-migrate to multi-file on next generation
  - Option B: Keep flattened, only new projects get multi-file
  - Option C: Let user choose via parameter

**Your preference?**

---

## Investigation First Approach

Per CLAUDE.md guidelines, we should:
1. **Start with log-driven investigation** (Phase 1)
2. **Run 8-10 tight cycles** to understand current behavior
3. **Document findings** in this PRD
4. **Then discuss implementation** with you

This PRD will be updated after investigation phase with:
- Root cause analysis
- Specific code changes needed
- Updated implementation plan
- Revised questions based on findings

---

## Next Steps

1. **Review this PRD** - Are the questions clear?
2. **Answer critical questions** (Q1-Q6) to guide implementation
3. **Approve investigation phase** - Should I start 30-min investigation?
4. **Issue creation** - Create subtask issues if this needs breakdown

**Estimated total time:**
- Investigation: 30 min (1 session)
- Implementation: 45-90 min (1-2 sessions, depends on complexity)
- Testing: 30 min (1 session)

---

**Last Updated:** 2025-10-29
**Status:** Draft - Awaiting user feedback on questions
**GitHub Issue:** #406
