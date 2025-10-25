# Fix Issue #253: KiCad → Python Sync Broken

**Branch:** `fix/issue-253-kicad-sync`
**Status:** Planning Phase
**Date:** 2025-10-24

---

## Problem Statement

When users manually edit a KiCad schematic and save changes, the circuit-synth JSON netlist is NOT automatically updated. This breaks the KiCad → Python synchronization workflow:

```
User edits in KiCad:
  .kicad_sch file → UPDATED ✅
  .json netlist → STALE ❌

Result: kicad_to_python_sync.py reads stale .json, imports empty circuit
```

**Impact:** Bidirectional sync only works one direction (Python → KiCad). Test 2.2 fails.

---

## Root Cause Analysis

### Current Architecture

The sync flow has three distinct operations:

1. **Python → KiCad (Works)**
   - `circuit.generate_json_netlist()` → Creates JSON
   - `circuit.generate_kicad_project()` → Creates .kicad_sch
   - Result: Both JSON and schematic in sync ✅

2. **KiCad → Python (BROKEN)**
   - User edits .kicad_sch manually
   - `kicad_to_python_sync.py` reads JSON (not .kicad_sch)
   - Result: Reads stale JSON, gets empty circuit ❌

3. **Why It Breaks**
   - `KiCadToPythonSyncer` constructor defaults to reading JSON netlist
   - JSON is only updated via `circuit.generate_json_netlist()`
   - When user edits KiCad, JSON is never regenerated
   - .kicad_sch file has new components, but JSON doesn't

### Existing Capabilities

The codebase already has the tools needed to fix this:

| Class | Purpose | Location |
|-------|---------|----------|
| `KiCadParser` | Parses .kicad_sch → Circuit object | `tools/utilities/kicad_parser.py` |
| `KiCadSchematicParser` | Wrapper for .kicad_sch parsing | `tools/utilities/kicad_schematic_parser.py` |
| `KiCadNetlistParser` | Parses .net files | `tools/utilities/kicad_netlist_parser.py` |
| `NetlistExporter.generate_json_netlist()` | Creates JSON from Circuit | `core/netlist_exporter.py` |
| `kicad-cli sch export netlist` | Generates .net from .kicad_sch | Native KiCad CLI |

**Flow Already Implemented:**
```
.kicad_sch → kicad-cli → .net file → KiCadNetlistParser → Circuit object → .json
```

---

## Solution Design

### Approach: Auto-Update JSON Before Import

**Strategy:** When syncing from KiCad, detect if .kicad_sch is newer than .json, and regenerate the JSON.

**Advantages:**
- Minimal code changes
- Reuses existing parsing infrastructure
- Transparent to users
- Handles batch edits efficiently

**Implementation Plan:**

### Phase 1: Detect Stale JSON (2-3 minutes)

Add a method to detect if .json is outdated:

```python
class KiCadToPythonSyncer:
    def is_json_stale(self) -> bool:
        """Check if .json is outdated relative to .kicad_sch

        Returns:
            True if .kicad_sch is newer than .json
            False if .json is up-to-date
        """
        json_mtime = self.json_path.stat().st_mtime
        kicad_sch_mtime = self.kicad_sch_path.stat().st_mtime
        return kicad_sch_mtime > json_mtime
```

**Files to Modify:**
- `src/circuit_synth/tools/kicad_integration/kicad_to_python_sync.py` (add method)

**Test:**
- Create test that verifies detection works
- Edit .kicad_sch and confirm `is_json_stale()` returns True

---

### Phase 2: Auto-Update JSON from .kicad_sch (5-7 minutes)

Add method to regenerate JSON from schematic:

```python
class KiCadToPythonSyncer:
    def update_json_from_schematic(self) -> None:
        """Regenerate JSON netlist from .kicad_sch file

        Process:
        1. Parse .kicad_sch using KiCadParser
        2. Extract Circuit object
        3. Generate JSON netlist
        4. Overwrite stale .json file
        """
        parser = KiCadParser(str(self.kicad_project_dir))
        circuits = parser.parse_circuits()
        circuit = circuits.get("main") or list(circuits.values())[0]

        # Generate updated JSON
        circuit.generate_json_netlist(str(self.json_path))

        logger.info(f"Updated JSON netlist from {self.kicad_sch_path}")
```

**Files to Modify:**
- `src/circuit_synth/tools/kicad_integration/kicad_to_python_sync.py` (add method)

**Dependencies:**
- `KiCadParser` already available
- `circuit.generate_json_netlist()` already implemented

**Test:**
- Manually edit .kicad_sch (add component)
- Call `update_json_from_schematic()`
- Verify .json contains new component

---

### Phase 3: Integrate Into Sync Flow (3-5 minutes)

Modify main sync method to auto-update JSON if stale:

```python
class KiCadToPythonSyncer:
    def sync(self, preview_only: bool = False) -> Dict[str, Any]:
        """Synchronize KiCad to Python

        New behavior:
        - Check if .json is stale relative to .kicad_sch
        - If stale, regenerate .json from schematic
        - Then proceed with normal sync
        """
        # NEW: Auto-update stale JSON
        if self.is_json_stale():
            logger.info("JSON netlist is outdated, regenerating from .kicad_sch...")
            self.update_json_from_schematic()

        # EXISTING: Continue with normal sync flow
        # ... rest of sync() method unchanged ...
```

**Files to Modify:**
- `src/circuit_synth/tools/kicad_integration/kicad_to_python_sync.py` (modify `sync()` method)

**Backward Compatibility:**
- ✅ If .json is up-to-date, no change in behavior
- ✅ If .json is missing, .kicad_sch parsing already handles it
- ✅ All existing code paths still work

**Test:**
- Run full sync workflow (edit in KiCad → import to Python)
- Verify generated Python code contains new components

---

## Implementation Tasks

### Task 1: Add Staleness Detection
- [ ] Implement `is_json_stale()` method
- [ ] Add unit test for detection logic
- [ ] Add logging for debug visibility

### Task 2: Add JSON Regeneration
- [ ] Implement `update_json_from_schematic()` method
- [ ] Handle edge cases (missing .kicad_sch, parse errors)
- [ ] Add error logging and recovery
- [ ] Add unit test for regeneration

### Task 3: Integrate Into Sync
- [ ] Modify `sync()` to call update if stale
- [ ] Add logging to show when update occurs
- [ ] Run full regression tests
- [ ] Verify test 2.2 now passes

### Task 4: Testing & Verification
- [ ] Unit tests for new methods
- [ ] Integration test: Edit → Import workflow
- [ ] Regression tests: Verify existing workflows unchanged
- [ ] Manual test: Reproduce issue scenario from #253

### Task 5: Documentation & Cleanup
- [ ] Update docstrings for modified methods
- [ ] Remove temporary debug logging
- [ ] Verify code coverage >80%

---

## Success Criteria

### Functional Requirements
- ✅ Edit component in KiCad → Manually save
- ✅ Run `kicad_to_python_sync.py`
- ✅ Generated Python code includes new component
- ✅ No manual JSON regeneration needed

### Quality Requirements
- ✅ All existing tests pass
- ✅ New tests pass (detection + regeneration)
- ✅ Code coverage >80% for new code
- ✅ No new dependencies added

### Specific Test Case (from issue #253)

```bash
# Step 1: Generate from Python
python -c """
from circuit_synth import circuit, Component

@circuit(name='test')
def test_circuit():
    pass

test = test_circuit()
test.generate_kicad_project('test')
"""

# Step 2: Edit in KiCad
# Manually open test/test.kicad_sch, add R1 (10k), save

# Step 3: Import back to Python
python kicad_to_python_sync.py test/test.kicad_pro output.py

# Step 4: Verify (SHOULD NOW PASS)
grep "r1 = Component" output.py  # Should find R1 ✅
```

---

## Risk Assessment

### Low Risk Areas
- ✅ `is_json_stale()` - Simple file timestamp comparison
- ✅ `update_json_from_schematic()` - Uses existing KiCadParser
- ✅ Integration into `sync()` - Minimal changes to existing method

### Potential Issues
- ⚠️ **Edge case:** .kicad_sch parsing fails → Add try/catch with helpful error
- ⚠️ **Performance:** Large schematics → Log timing, may need optimization later
- ⚠️ **User expectation:** Auto-update may surprise users → Add info logs

### Mitigation
- ✅ Comprehensive error handling and logging
- ✅ Preserve existing behavior when JSON is current
- ✅ Clear log messages explaining auto-update

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    KiCad → Python Sync                      │
└─────────────────────────────────────────────────────────────┘

Input: .kicad_pro (project file)
  │
  ├─ Find .kicad_sch and .json files
  │
  ├─ NEW: Check if .json is stale
  │  │
  │  └─ If stale:
  │     │
  │     ├─ KiCadParser reads .kicad_sch
  │     ├─ kicad-cli generates .net file
  │     ├─ KiCadNetlistParser reads .net
  │     ├─ Circuit object created
  │     └─ NetlistExporter.generate_json_netlist() updates .json
  │
  ├─ Load (updated) .json file
  ├─ Parse components and nets
  ├─ PythonCodeGenerator creates Python code
  │
  └─ Output: Python file with updated circuit definition
```

---

## Files to Modify

| File | Changes | Type |
|------|---------|------|
| `src/circuit_synth/tools/kicad_integration/kicad_to_python_sync.py` | Add `is_json_stale()`, `update_json_from_schematic()`, modify `sync()` | Core fix |
| `tests/unit/tools/test_kicad_to_python_sync.py` | Add tests for new methods and integration | Tests |
| `CLAUDE.md` | Document the fix if it reveals process improvements | Docs |

---

## Estimated Effort

| Phase | Duration | Notes |
|-------|----------|-------|
| Phase 1: Staleness detection | 2-3 min | Simple file comparison |
| Phase 2: JSON regeneration | 5-7 min | Uses existing code |
| Phase 3: Integration | 3-5 min | Minimal changes to sync() |
| Phase 4: Testing | 5-10 min | Unit + integration tests |
| Phase 5: Cleanup | 2 min | Logging, docs |
| **TOTAL** | **17-27 min** | One focused session |

---

## Next Steps

1. ✅ **Research complete** - Architecture understood
2. ⏭️ **Implement Phase 1** - Add staleness detection
3. ⏭️ **Implement Phase 2** - Add JSON regeneration
4. ⏭️ **Implement Phase 3** - Integrate into sync flow
5. ⏭️ **Test & verify** - Run full test suite
6. ⏭️ **Commit & release** - Create PR, release patch version

---

## References

### Related Code Files
- `KiCadToPythonSyncer`: `src/circuit_synth/tools/kicad_integration/kicad_to_python_sync.py`
- `KiCadParser`: `src/circuit_synth/tools/utilities/kicad_parser.py`
- `NetlistExporter`: `src/circuit_synth/core/netlist_exporter.py`

### Related Issues
- #253 (This issue)
- #250 (CLI parameter bug)
- #251 (Idempotency failure)

### Test References
- Phase 2, Test 2.2: Import Resistor to Python
