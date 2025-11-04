---
name: feature
description: Develop new feature with iterative test-first workflow
---

# Feature Development Command

**Purpose:** End-to-end feature development workflow following circuit-synth's test-first, iterative development methodology.

## Usage
```bash
/dev:feature <feature-description>
```

## What This Does

Guides you through the complete feature development workflow:

1. **Problem Analysis**
   - Review user's feature description
   - Investigate existing codebase for context
   - Check related code in circuit-synth AND kicad-sch-api/kicad-pcb-api (we maintain these!)
   - Identify if changes needed upstream vs. in circuit-synth

2. **PRD Creation**
   - Create PRD document in repo root (e.g., `PRD_feature_name.md`)
   - Structure:
     - Problem Statement
     - Proposed Solution
     - Implementation Steps
     - Test Plan
     - Debugging Strategy (logs to add, what to observe)
   - Present PRD to user for review
   - Iterate on PRD based on feedback
   - Review for: simplicity, debugability, observability

3. **Implementation Planning**
   - Break feature into small, testable steps
   - Create GitHub issue for tracking
   - Check out feature branch
   - Plan cycle count (target: 10-20 cycles, 2-3 min each)

4. **Test-First Implementation**
   For each step:
   - **Write failing test FIRST**
   - Implement minimal code to pass test
   - Use iterative cycle pattern:
     - **Cycle N**: Add strategic logging
     - Run code/test immediately
     - Observe logs and behavior
     - Document observation
     - Make small change (1-5 lines)
     - Repeat
   - Track cycle metrics (time, observations)
   - Clean up temporary debug logs
   - Keep essential operational logs

5. **Verification**
   - All tests passing
   - Test coverage >80%
   - No regressions
   - Code formatted (black, isort)
   - Documentation updated if needed

6. **PR Creation**
   - Commit with descriptive message
   - Create PR with summary
   - Run /dev:review-branch for pre-merge validation
   - Address any issues found

## Iterative Cycle Pattern (CRITICAL)

**DO NOT write large amounts of code then test once.**
**DO work in tight cycles:**

```
Cycle 1: Add logs to understand current behavior
  → Run test
  → Observe: Component positions are in wrong coordinate system
  → Hypothesis: Using mm but KiCad expects mils

Cycle 2: Add logs to coordinate conversion
  → Run test
  → Observe: No conversion happening
  → Fix: Add mm_to_mils() conversion

Cycle 3: Run with conversion
  → Observe: Positions correct now!
  → Remove debug logs, keep operational logs
```

**Target:** 10-20 cycles per feature, each 2-3 minutes

## Logging Strategy

Follow standard Python logging best practices:

```python
# Temporary investigation logs (remove after understanding)
logger.debug(f"CYCLE {n}: Investigating {variable_name} = {value}")
logger.debug(f"CYCLE {n}: Function entry with args: {args}")

# Permanent operational logs (keep)
logger.info(f"Generated netlist for {circuit.name}")
logger.debug(f"Selected footprint {footprint} for {component.reference}")
logger.warning(f"Component {ref} missing footprint, using default")
logger.error(f"Failed to validate {ref}: {error}")
```

**Log levels:**
- DEBUG: Development insights, detailed state
- INFO: Important state transitions, user-visible operations
- WARNING: Recoverable issues, deprecated usage
- ERROR: Failures, exceptions

**No emojis in logs.** Professional, parseable output.

## kicad-sch-api / kicad-pcb-api Context

**IMPORTANT:** We maintain kicad-sch-api and kicad-pcb-api repos.

When debugging issues:
1. **Root cause in circuit-synth?** → Fix it here
2. **Root cause in kicad-sch-api/kicad-pcb-api?** → Fix it upstream

**Don't work around upstream bugs - fix them at the source.**

Workflow for upstream fixes:
1. Create GitHub issue in upstream repo
2. Clone, fix, test in that repo
3. Create PR in upstream repo
4. After merge, update circuit-synth dependency
5. Verify fix works end-to-end

## Example Session

```bash
User: /dev:feature "Add Potentiometer component support"

Agent:
[Analyzes codebase, checks existing component patterns]

Creating PRD: PRD_potentiometer_component.md

# PRD: Potentiometer Component Support

## Problem Statement
Users need to add potentiometers to circuits but no Potentiometer
class exists. Current workaround uses generic Resistor.

## Proposed Solution
Create Potentiometer class extending Component with:
- 3-pin support (wiper, end1, end2)
- Value parameter (resistance)
- Footprint auto-selection
- KiCad symbol mapping

## Implementation Steps
1. Create Potentiometer class (src/circuit_synth/components/potentiometer.py)
2. Add footprint selection logic
3. Add tests (test_potentiometer.py)
4. Update component registry

## Test Plan
- Unit tests for Potentiometer creation
- Footprint selection validation
- KiCad project generation test
- Example circuit with potentiometer

## Debugging Strategy
Add logs to:
- Footprint selection logic
- Pin mapping
- KiCad symbol resolution

---

User: [Reviews PRD, provides feedback]
Agent: [Updates PRD based on feedback]
User: "Looks good, proceed"

Agent:
Creating GitHub issue #522: Add Potentiometer component support
Checking out branch: feat/potentiometer-component

Starting test-first implementation:

STEP 1: Write failing test
[Creates test_potentiometer.py with failing test]

STEP 2: Implement with cycles

Cycle 1: Add logs to understand Resistor pattern
  → Running: pytest test_potentiometer.py
  → Observe: Resistor has 2 pins, footprint selection

Cycle 2: Create Potentiometer skeleton with logs
  → Running: pytest test_potentiometer.py
  → Observe: Class created, need 3-pin support

Cycle 3: Implement 3-pin logic
  → Running: pytest test_potentiometer.py
  → Observe: Pins created correctly
  → Test passing!

Cycle 4: Add footprint selection with logs
  → Running: pytest test_potentiometer.py
  → Observe: Footprint selected based on value
  → All tests passing!

Cycle 5: Remove debug logs, keep operational logs
  → Running: pytest test_potentiometer.py
  → All tests passing, clean output

VERIFICATION:
✅ All tests passing
✅ Coverage: 85%
✅ Code formatted
✅ No regressions

Creating PR #523: feat: Add Potentiometer component support

Total time: 30 minutes across 5 cycles (~6 min per cycle)
```

## Options

- `--skip-prd` - Skip PRD creation, go straight to implementation (use for tiny changes)
- `--test-only` - Only create tests, don't implement (for TDD purists)
- `--no-cycles` - Don't track cycles explicitly (not recommended)

## Integration with Workflow

This command embodies the circuit-synth development philosophy:
- GitHub issue-driven development
- Test-first mentality
- Log-driven investigation
- Iterative cycles (add logs → run → observe → repeat)
- Small batch workflow
- Continuous verification

## Success Criteria

Feature is "done" when:
- [ ] All tests passing
- [ ] Test coverage >80%
- [ ] No regressions
- [ ] Code formatted
- [ ] Logs cleaned up (temp logs removed)
- [ ] Documentation updated (if needed)
- [ ] PR created and reviewed
- [ ] GitHub issue can be closed

---

**This command guides you through professional, iterative feature development with circuit-synth's proven methodology.**
