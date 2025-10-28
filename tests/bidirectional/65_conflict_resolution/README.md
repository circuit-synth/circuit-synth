# Test 65: Conflict Resolution

## What This Tests
Validates circuit-synth's behavior when conflicting modifications are made to the same component in both Python and KiCad between synchronization cycles. This tests the system's conflict detection and resolution strategy.

## When This Situation Happens
- Developer generates circuit from Python (R1=10k, R2=1k)
- Opens KiCad, makes edits externally (R1→22k, adds R4)
- Meanwhile, edits Python code without importing (R1→10k, adds R3)
- Attempts to regenerate from Python
- System must handle conflicting changes to R1 value

## What Should Work
1. Generate initial KiCad with R1=10k, R2=1k
2. Simulate conflicting changes:
   - **Python side**: Modify R1 value to 47k, add R3
   - **KiCad side**: Manually edit R1 value to 22k, add R4
3. Regenerate from Python without importing KiCad changes
4. Document observed behavior:
   - Does Python overwrite KiCad changes? (likely current behavior)
   - Is there conflict detection or warning?
   - What happens to R3 (Python-only) and R4 (KiCad-only)?

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth2/tests/bidirectional/65_conflict_resolution

# Step 1: Generate initial KiCad project
uv run conflicting_edits.py
open conflicting_edits/conflicting_edits.kicad_pro

# Verify in KiCad:
# - R1 with value "10k"
# - R2 with value "1k"

# Step 2: Manually edit KiCad schematic (DO NOT SAVE TO PYTHON)
# In KiCad schematic editor:
#   - Change R1 value: 10k → 22k
#   - Add R4 (Device:R, value=100k, footprint=R_0603_1608Metric)
#   - Save schematic (Cmd+S)
#   - Note: R1=22k, R4 added
# Close KiCad

# Step 3: Edit Python WITHOUT importing KiCad changes
# In conflicting_edits.py:
#   - Uncomment R3 (adds R3=4.7k)
#   - Change R1 value: "10k" → "47k"
# DO NOT run kicad-to-python import!

# Step 4: Regenerate from Python (creates conflict)
uv run conflicting_edits.py

# Step 5: Open regenerated KiCad
open conflicting_edits/conflicting_edits.kicad_pro

# Step 6: Document observed behavior:
# - What is R1's value? (47k from Python, or 22k from KiCad?)
# - Is R3 present? (added in Python)
# - Is R4 present? (added in KiCad)
# - Are there any warnings or error messages?
```

## Current Expected Behavior (As of 2025-10-28)

Based on circuit-synth's current architecture:

**Python Wins Strategy (Current Behavior):**
- ✅ R1 value becomes 47k (Python overwrites KiCad)
- ✅ R3 is present (added from Python)
- ❌ R4 is lost (not in Python, overwritten during generation)
- ⚠️ No conflict detection or warning
- ⚠️ User's manual KiCad changes silently lost

**Why This Happens:**
- `generate_kicad_project()` regenerates schematic from Python state
- Does not merge with existing KiCad state
- No conflict detection mechanism in place
- Python source is treated as "source of truth"

## Ideal Future Behavior (Feature Request)

**Smart Conflict Detection:**
1. Detect that schematic was modified since last generation
2. Compare timestamps or checksums
3. Warn user: "KiCad schematic has changes not in Python code"
4. Offer resolution strategies:
   - `--force-python`: Overwrite KiCad (current behavior)
   - `--import-first`: Import KiCad changes, then regenerate
   - `--abort`: Stop, require manual resolution

**Example Conflict Warning:**
```
⚠️  CONFLICT DETECTED: R1.value
   Python:  47k
   KiCad:   22k

   Resolution options:
   1. Import KiCad changes first (recommended)
   2. Overwrite KiCad with Python (--force-python)
   3. Abort and resolve manually

Choose option [1/2/3]:
```

## Why This Is Critical

**Real-World Scenarios:**
1. **Team Collaboration** - Multiple developers editing same circuit
2. **Manual KiCad Edits** - Quick fixes made directly in KiCad
3. **Forgotten Import** - Developer forgets to run kicad-to-python before editing
4. **Parallel Workflows** - Python script running while KiCad open
5. **Version Control** - Merge conflicts in both .py and .kicad_sch files

**Data Loss Prevention:**
- Current behavior can silently lose manual KiCad edits
- No warning that KiCad changes will be overwritten
- User assumes bidirectional sync means merge, not overwrite

**Technical Validation:**
- **Conflict Detection**: Can system detect KiCad was modified?
- **Resolution Strategy**: How are conflicts resolved?
- **User Warning**: Is user notified of potential data loss?
- **Merge Capability**: Can Python and KiCad changes be merged?

## Success Criteria

### Current Behavior Documentation (Phase 1)
- ✅ Test demonstrates Python-wins behavior
- ✅ R1 value becomes 47k (Python)
- ✅ R3 present (Python)
- ✅ R4 lost (KiCad-only change discarded)
- ✅ No conflict warnings generated
- ✅ Behavior documented in test output

### Future Enhancement (Phase 2 - Not Implemented)
- ⚠️ Detect KiCad modifications (timestamp/checksum)
- ⚠️ Warn user about conflicts before overwriting
- ⚠️ Offer resolution strategies (import-first, force, abort)
- ⚠️ Preserve both Python and KiCad changes when possible
- ⚠️ Log conflict resolution decisions

## Test Output Format

The automated test will document observed behavior:

```
================================================================================
TEST 65: CONFLICT RESOLUTION - BEHAVIOR DOCUMENTATION
================================================================================

Initial State:
  - R1=10k, R2=1k

Conflicting Changes:
  - Python: R1→47k, +R3=4.7k
  - KiCad:  R1→22k, +R4=100k

Observed Behavior:
  ✅ R1 value: 47k (Python wins)
  ✅ R2 value: 1k (unchanged)
  ✅ R3 present: YES (Python addition)
  ❌ R4 present: NO (KiCad addition lost)
  ⚠️  Conflict warnings: NONE

Current Strategy: PYTHON-WINS (overwrite)
Recommended: Add conflict detection and user warning

================================================================================
```

## Related Issues
- Potential GitHub issue: "Add conflict detection for concurrent Python/KiCad edits"
- Enhancement: Timestamp-based change detection
- Enhancement: Smart merge strategies for non-conflicting changes

## Notes
- This test documents current behavior, not a bug
- Python-wins is reasonable default for code-first workflow
- Enhancement would add safety for manual KiCad editing workflow
- Test may pass by documenting behavior rather than asserting specific outcome
