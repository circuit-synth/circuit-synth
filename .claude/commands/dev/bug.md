---
name: bug
description: Debug and fix issues with log-driven iterative approach
---

# Bug Fixing Command

**Purpose:** Systematic bug investigation and fixing workflow using log-driven iterative cycles.

## Usage
```bash
/dev:bug <bug-description-or-issue-number>
```

## What This Does

Guides you through systematic bug fixing:

1. **Issue Analysis**
   - Review bug description or GitHub issue
   - Reproduce the issue
   - Create minimal reproduction case
   - Document expected vs. actual behavior

2. **Root Cause Investigation**
   - Add strategic logging to suspected code paths
   - Run reproduction case
   - Observe logs and behavior
   - Form hypothesis about root cause
   - Iterate: add logs → run → observe → refine hypothesis
   - Target: 8-12 investigation cycles

3. **Fix Implementation**
   - Write test that fails due to bug
   - Implement minimal fix
   - Verify test passes
   - Check for regressions
   - Clean up debug logs

4. **Verification**
   - Original issue resolved
   - Test coverage includes regression test
   - No new issues introduced
   - Related functionality still works

5. **Documentation**
   - Update GitHub issue with findings
   - Commit with descriptive message referencing issue
   - Create PR if needed

## Iterative Investigation Pattern

**DO NOT guess at the problem.**
**DO use logs to understand behavior:**

```
Cycle 1: Add logs to entry point
  → Run: Observe function is called with wrong arguments
  → Hypothesis: Caller passing arguments in wrong order

Cycle 2: Add logs to caller
  → Run: Observe caller has correct data
  → Hypothesis: Parameter order mismatch in function signature

Cycle 3: Check function signature
  → Observe: Signature expects (text, at=position) but caller uses (position, text)
  → Root cause found!

Cycle 4: Write test with correct parameter order
  → Run: Test fails (confirms bug)

Cycle 5: Fix parameter order in function signature
  → Run: Test passes!

Cycle 6: Check all callers
  → Run: Found 2 more places with wrong order

Cycle 7: Fix all callers
  → Run: All tests pass

Cycle 8: Clean up debug logs
  → Run: Still passing, output clean
```

**Total: 8 cycles, ~20 minutes**

## Logging Strategy for Debugging

### Temporary Investigation Logs (Remove After)

```python
# Mark investigation logs clearly
logger.debug(f"CYCLE {n}: Checking variable state: {var}")
logger.debug(f"CYCLE {n}: Function entry: {func_name}({args})")
logger.debug(f"CYCLE {n}: Branch taken: {branch_info}")
```

### Strategic Log Placement

1. **Entry/Exit logs** - Track control flow
2. **State inspection** - Verify assumptions
3. **Decision points** - Understand why branches taken
4. **Data transformation** - Input → output validation

### Context Window Management

Silence noisy modules during investigation:

```python
import logging

# Silence unrelated modules
logging.getLogger('urllib3').setLevel(logging.ERROR)
logging.getLogger('kicad').setLevel(logging.WARNING)

# Enable DEBUG for area under investigation
logging.getLogger('circuit_synth.components').setLevel(logging.DEBUG)
logger = logging.getLogger('circuit_synth.components')
```

## kicad-sch-api / kicad-pcb-api Context

**Remember:** We maintain kicad-sch-api and kicad-pcb-api.

When investigating bugs:
1. **Bug in circuit-synth?** → Fix it here
2. **Bug in kicad-sch-api/kicad-pcb-api?** → Fix it upstream

**Look for the best solution to the underlying problem, not workarounds.**

Example:
```
Issue: Component positions not serializing correctly

Investigation reveals:
- circuit-synth calls kicad-sch-api's Position.to_dict()
- Position.to_dict() missing 'angle' field (BUG!)

Correct approach:
1. Fix Position.to_dict() in kicad-sch-api
2. Add regression test in kicad-sch-api
3. Release kicad-sch-api with fix
4. Update circuit-synth dependency
5. Verify fix works end-to-end

Wrong approach:
- Work around it in circuit-synth with custom serialization
```

## Example Session

```bash
User: /dev:bug "Component rotations break after sync (issue #517)"

Agent:
Analyzing issue #517: Label orientation issues on rotated components

REPRODUCTION:
Creating minimal test case...
✅ Reproduced: Labels face wrong direction after rotation

INVESTIGATION PHASE:

Cycle 1: Add logs to label creation
  → Run test
  → Observe: Label angle calculated from component rotation

Cycle 2: Add logs to angle calculation
  → Run test
  → Observe: Angle calculation uses undefined variable 'rotation_normalized'
  → ERROR: NameError: name 'rotation_normalized' is not defined
  → Root cause found!

Cycle 3: Check where rotation_normalized should come from
  → Observe: Should be 'label_angle' (defined 5 lines above)
  → Hypothesis: Variable name typo

TEST PHASE:

Cycle 4: Write test for label angle on rotated component
  → Run: Test fails (NameError)

FIX PHASE:

Cycle 5: Fix variable name: rotation_normalized → label_angle
  → Run: Test passes!
  → Check for other occurrences: None found

VERIFICATION:

Cycle 6: Run full test suite
  → All tests passing
  → No regressions

Cycle 7: Test with actual rotated components
  → Labels now orient correctly!

Cycle 8: Clean up debug logs
  → Remove investigation logs
  → Keep operational logs
  → All tests still passing

RESULT:
✅ Bug fixed in synchronizer.py line 809
✅ Root cause: Variable name typo
✅ Fix: Single line change
✅ All tests passing
✅ No regressions

Creating PR: fix: Correct variable name in label angle calculation (#517)

Total time: 16 minutes across 8 cycles (~2 min per cycle)
```

## Common Bug Patterns

### 1. Parameter Order Issues
**Symptom:** Wrong values in wrong places
**Investigation:** Log function calls with arguments
**Fix:** Correct parameter order

### 2. Coordinate System Bugs
**Symptom:** Positions/rotations wrong in KiCad
**Investigation:** Log coordinate transformations
**Fix:** Add proper mm↔mils conversion

### 3. Reference/UUID Issues
**Symptom:** Component not found, duplicate refs
**Investigation:** Log reference resolution
**Fix:** Use correct identifier (UUID vs. ref)

### 4. State Management
**Symptom:** Values not persisting, cache issues
**Investigation:** Log state changes
**Fix:** Proper state update/invalidation

### 5. Upstream Library Bugs
**Symptom:** Unexpected behavior from kicad-sch-api
**Investigation:** Log library calls and returns
**Fix:** Fix in upstream repo, update dependency

## Options

- `--reproduce-only` - Just create reproduction case, don't fix
- `--cycles=N` - Target N investigation cycles (default: auto)
- `--upstream` - Assume bug is in kicad-sch-api/kicad-pcb-api

## When Bug is Fixed

- [ ] Original issue resolved
- [ ] Regression test added
- [ ] All tests passing
- [ ] Debug logs removed
- [ ] GitHub issue updated with root cause
- [ ] PR created and reviewed
- [ ] Consider if upstream fix needed

## Debugging Tips

1. **Start broad, narrow down** - Log at entry points first
2. **One hypothesis at a time** - Test specific theories
3. **Verify assumptions** - Log what you think is true
4. **Binary search** - Add logs in middle of suspect code
5. **Check boundaries** - Edge cases often reveal bugs
6. **Compare working case** - Log both failing and passing cases

## Success Criteria

Bug is "fixed" when:
- [ ] Can't reproduce original issue
- [ ] Regression test prevents recurrence
- [ ] All tests passing
- [ ] Root cause documented
- [ ] No new issues introduced
- [ ] Code cleaned up (debug logs removed)

---

**This command provides systematic, log-driven bug investigation following circuit-synth's proven debugging methodology.**
