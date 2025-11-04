# CLAUDE.md - circuit-synth Library Development Guide

This guide defines how Claude Code assists with developing the circuit-synth Python library.

## 👤 Developer Context

- **Side project** with intermittent development time
- Work in **15-30 minute focused bursts** when you have availability
- **Test-first mentality** - never commit untested code
- **Log-driven investigation** - observe behavior, don't assume
- **Small batch releases** - frequent, incremental PyPI releases
- **Continuous verification** - parallel review threads always running

---

## 🎯 Core Development Philosophy

### 1. GitHub Issue-Driven Development

All work starts with a GitHub issue:

1. **Create/select issue** - Check existing issues or create new one
2. **Break down** - Issue describes the goal; we break into small subtasks
3. **Work on subtask** - One small task (15-30 min) at a time
4. **Reference in commits** - `fix: Correct Text class parameters (#238)`
5. **Close with verification** - Issue closes when task is done and tested

**Why:** Keeps work visible, context survives across sessions, work fits burst schedule.

### 2. Test-First Mentality (MANDATORY)

Never commit untested code.

```python
# Pattern for every task:

# Step 1: Write failing test
def test_potentiometer_component():
    pot = Potentiometer("R1", value="10k")
    assert pot.reference == "R1"
    assert pot.footprint  # Should auto-select

# Step 2: Implement minimal code to pass test
class Potentiometer(Component):
    def __init__(self, reference, value):
        super().__init__(reference)
        self.value = value
        self._select_footprint()

# Step 3: Run test - verify it passes
# Step 4: Add regression tests for edge cases
# Step 5: Verify test coverage >80%
```

**Why:** Test documents expected behavior, provides safety net for changes, catches regressions.

### 3. Iterative Cycle Pattern (CORE)

**Do NOT write large amounts of code, then test once.**
**DO work in tight iterative cycles: Add Logs → Run → Observe → Repeat**

```
Cycle: Add Logs → Run → Observe → Repeat
Target: 10-20 cycles per task, each 2-3 minutes
Result: Deep understanding + confident implementation
```

#### The Cycle Process:

1. **Add strategic logging** to code area you're studying
2. **Run the code/test** immediately
3. **Observe log output** to understand behavior
4. **Refine understanding** based on what logs revealed
5. **Make small change** (1-5 lines) based on observation
6. **Run again immediately** - repeat cycle

#### Example: 8-Cycle Bug Investigation

```
Issue #238: Text class parameters incorrect

Cycle 1: Add logs to see what's being called
  ↓ Run test, observe logs
  ↓ Logs show: Text(position, text) is being called

Cycle 2: Add logs to constructor
  ↓ Run test, observe
  ↓ Logs show: Parameters received in wrong order

Cycle 3: Check Text.__init__ signature
  ↓ Run code
  ↓ Logs show: Signature expects (text, at=position) but caller uses (position, text)

Cycle 4: Find all callers of Text
  ↓ Run grep
  ↓ Found: 3 places calling with wrong parameter order

Cycle 5: Write test with correct parameter order
  ↓ Run test - FAILS (parameters still swapped)

Cycle 6: Fix first caller
  ↓ Run test - PASSES
  ↓ Logs show: Parameters now in correct order

Cycle 7: Fix remaining callers
  ↓ Run all tests - PASS
  ↓ All logs show correct order

Cycle 8: Clean up debug logs, verify production logs
  ↓ Remove 🔍 temporary logs
  ↓ Run test - still passing, output clean
```

**Total time:** ~30 minutes in 8 tight cycles.

---

## 🔬 Log-Driven Investigation

Logs are your development tool. Use them to understand behavior, not to guess.

### Strategic Logging Pattern

Follow standard Python logging best practices. **No emojis in logs.**

```python
# Temporary investigation logs (remove after understanding)
logger.debug(f"CYCLE {n}: Investigating {variable_name} = {value}")
logger.debug(f"CYCLE {n}: Function entry with args: {args}")
logger.debug(f"CYCLE {n}: Branch taken: {branch_info}")

# Permanent operational logs (keep)
# These provide production insight and debugging capability
logger.info(f"Generated netlist for {circuit.name}")
logger.debug(f"Selected footprint {footprint} for {component.reference}")
logger.warning(f"Component {ref} missing footprint, using default")
logger.error(f"Failed to validate {ref}: {error}")
```

**Log Levels:**
- **DEBUG:** Development insights, detailed state inspection
- **INFO:** Important state transitions, user-visible operations
- **WARNING:** Recoverable issues, deprecated API usage
- **ERROR:** Failures, exceptions that need attention

**Professional, parseable output only.**

### Context Window Management

Disable verbose logs from other modules while investigating:

```python
import logging

# Silence noisy libraries
logging.getLogger('urllib3').setLevel(logging.ERROR)
logging.getLogger('kicad').setLevel(logging.WARNING)
logging.getLogger('circuit_synth.netlist').setLevel(logging.WARNING)

# Enable DEBUG for area under study
logging.getLogger('circuit_synth.components').setLevel(logging.DEBUG)
logger = logging.getLogger('circuit_synth.components')
```

### Log Categories

**Temporary Investigation Logs (Remove After Understanding)**
- Variable state inspection: `logger.debug(f"CYCLE {n}: {var} = {value}")`
- Control flow tracing: `logger.debug(f"CYCLE {n}: Entering function {func_name}")`
- Data structure dumps: `logger.debug(f"CYCLE {n}: Dict keys: {dict.keys()}")`
- "Why is this happening?" logs
- Hypothesis testing logs

**Permanent Operational Logs (Keep)**
- Important state transitions: `logger.info(f"Created circuit {name}")`
- User-visible operations: `logger.info(f"Generated {num_nets} nets")`
- Error conditions: `logger.error(f"Failed to validate {ref}: {error}")`
- Warnings: `logger.warning(f"Deprecated API usage: {old_api}")`
- Performance metrics: `logger.debug(f"Netlist generation took {ms}ms")`

**No emojis, symbols, or decorative characters in logs. Professional output only.**

### Claude's Behavior During Cycles

When investigating or developing:

1. **Add strategic logs** - Mark with "CYCLE N:" prefix for easy cleanup
2. **Run immediately** - Don't wait, test right away
3. **Report observations** - Share what logs showed
4. **Propose hypothesis** - What does this tell us?
5. **Plan next cycle** - What will we try next and why?
6. **Disable noise** - Turn off unrelated logs to save context
7. **Keep iterating** - Each cycle informs the next

Example cycle report:
```
Cycle 3 complete:
Logs showed component.pins is empty list.
Hypothesis: pins aren't being loaded from component library.
Next cycle: Add logs to library loading function.
```

**Track cycle metrics:** Time per cycle, observations, hypotheses tested.

---

## 📦 Small Batch Workflow

Work in small, independently releasable chunks.

### Typical Small Batch (15-30 minutes)

1. **Read/create GitHub issue** describing the work (2 min)
2. **Write failing test** capturing desired behavior (3 min)
3. **Implement with cycles** - investigate, understand, code (10-15 cycles, ~15 min)
4. **Verify test passes** - all tests green (2 min)
5. **Clean up logs** - remove 🔍 temporary logs (1 min)
6. **Commit with issue reference** - `fix: Short description (#123)` (1 min)
7. **Release to PyPI** - patch version bump if stable (2 min)
8. **Verify installation** - fresh venv install test (2 min)

### Example: Adding Potentiometer Component (30 min)

```
Issue #245: Add Potentiometer component support

Setup (5 min, 3 cycles):
  Cycle 1: Add logs to existing Resistor class to understand pattern
    ↓ Run, observe: component creation and footprint selection
  Cycle 2: Add logs to footprint selection logic
    ↓ Run, observe: footprint selection based on value
  Cycle 3: Study existing component implementations
    ↓ Run grep, observe: clear pattern for component classes

Test (5 min, 1 cycle):
  Cycle 4: Write failing test for Potentiometer
    ↓ Run test, observe: AttributeError: Potentiometer not defined
    ↓ Good - test is ready

Implementation (15 min, 5 cycles):
  Cycle 5: Create Potentiometer class skeleton with logs
    ↓ Run test, observe: footprint attribute missing
  Cycle 6: Add __init__ and footprint selection with logs
    ↓ Run test, observe: footprint selected correctly
  Cycle 7: Verify netlist generation with logs
    ↓ Run test, observe: netlist generated correctly
  Cycle 8: Test edge cases with logs
    ↓ Run test, observe: all edge cases pass
  Cycle 9: Remove 🔍 logs, keep essential ones
    ↓ Run test, observe: still passing, output clean

Cleanup & Release (5 min):
  Commit: "feat: Add Potentiometer component support (#245)"
  PyPI: Release as patch (0.2.3 → 0.2.4)
  Verify: Fresh install test in new venv

Total: 13 cycles in ~30 minutes (2.3 min per cycle)
```

### Breaking Down Larger Issues

If an issue is too big for 30 minutes:
1. **Create subtask issues** with smaller scope
2. **Work on one subtask per session** (15-30 min)
3. **Each subtask is independently releasable**
4. **Reference parent issue** in subtask (e.g., "Part of #240")
5. **Close parent issue** only when all subtasks done

---

## 🤝 Operating Modes

Claude can work collaboratively or autonomously depending on task clarity.

### Collaborative Mode (Default for Unclear Tasks)

When requirements are ambiguous or need validation:
- **Discuss approach** - Ask questions, explore options
- **Validate assumptions** - Confirm understanding
- **Break down together** - Plan small tasks
- **Create issues together** - Structure the work

**Trigger:** "I'm not sure how to approach this" or complex requirements

### Autonomous Mode (For Clear Tasks)

When requirements are well-defined and clear:
- **Create GitHub issues** - Reference what will be done
- **Implement independently** - Use cycles and logs
- **Run full verification** - Tests, quality checks, formatting
- **Propose commits** - Self-validate before asking
- **Continue momentum** - Don't wait between cycles

**Trigger:** Clear GitHub issue exists, or simple bug fix with obvious solution

### Hybrid Mode (Complex Features)

Balance of both approaches:
- **Discuss architecture** - Collaborative design phase
- **Create task breakdown** - Small subtasks emerge
- **Autonomous implementation** - Of individual subtasks
- **Continuous verification** - Parallel review threads
- **Checkpoint discussions** - At subtask boundaries

**Trigger:** Large feature with design decisions and implementation phases

---

## ⚡ Multi-Threaded Development

Always try to parallelize work. Use Haiku 4.5 extensively for fast parallel execution.

### Parallel Execution Pattern

When you're working on feature X:

```
Main thread (You): Implement feature
  ↓

Parallel threads (Haiku sub-agents):
  Thread A: Run test suite, report failures
  Thread B: Check code quality (black, mypy, flake8)
  Thread C: Security scan for obvious issues
  Thread D: Verify documentation accuracy
  Thread E: Check example circuits still work
```

**Key:** Launch all parallel threads in ONE message. Don't wait sequentially.

### Before Every Commit

Launch verification suite:
1. **Test execution** - Full test suite with coverage
2. **Type checking** - mypy verification
3. **Formatting** - Black, isort formatting
4. **Linting** - flake8 code quality
5. **Security scan** - Basic security checks
6. **Documentation** - README/docs accuracy check
7. **Example circuits** - All examples generate without error

### After Every PyPI Release

Launch post-release verification:
1. **Fresh install test** - New venv, `pip install circuit-synth`
2. **Example circuit** - Run a basic example
3. **Import test** - Verify all imports work
4. **Version check** - PyPI shows correct version
5. **Plugin test** - KiCad integration still works

---

## 🎛️ Development Commands

### Testing & Verification
- `/dev:run-tests` - Execute test suite with coverage
- `/dev:run-tests --watch` - Watch mode for continuous testing

### Code Review & Analysis
- `/dev:review-branch` - Comprehensive branch review (see branch review details below)
- `/dev:review-repo` - Full repository analysis and health check

### Commit Workflow
- `/dev:update-and-commit [description]` - Document changes and create commit

### Release Workflow
- `/dev:release-pypi` - Release to PyPI with version bump
- `/dev:dead-code-analysis` - Find unused code before release

### Development Setup
- `./tools/maintenance/ensure-clean-environment.sh` - Clean pip environment, prevent conflicts

---

## 📊 Review Branch Workflow

The `/dev:review-branch` command provides comprehensive pre-merge review. Key features:

### What It Does:

1. **Code Quality Analysis** - Cyclomatic complexity, maintainability, type hints
2. **Security Scanning** - Hardcoded secrets, unsafe patterns, dependency vulnerabilities
3. **Performance Review** - Algorithm complexity, regression detection
4. **Testing Coverage** - New code coverage, regression test adequacy
5. **Documentation** - API docs current, README updated, examples work
6. **Circuit-Synth Specific** - Component validation, KiCad integration, agent system
7. **Dependency Analysis** - New dependencies, version changes, security updates

### Usage Examples:

```bash
# Quick check before committing
/dev:review-branch --depth=quick

# Full review before merging to main
/dev:review-branch --depth=full --target=main

# Security-focused review
/dev:review-branch --focus=security --threshold=critical

# Performance analysis
/dev:review-branch --focus=performance --depth=full

# With auto-fix suggestions
/dev:review-branch --depth=full --auto-fix=true
```

### Expected Output:

```markdown
# Branch Review: feat/add-potentiometer → main

## Executive Summary
- Risk: MEDIUM
- Key Changes: Added Potentiometer component, 3 files changed, 45 lines added
- Test Coverage: 85% (↑ 2%)
- Action Items: Update website documentation

## Detailed Analysis
### Code Quality: ✓ GOOD
- Complexity: 5/10
- Type Coverage: 100%
- Documentation: Complete

### Testing: ✓ GOOD
- New Tests: 8 tests added
- Coverage: 85% (new code 90%)
- Regression: All tests pass

### Security: ✓ CLEAN
- No hardcoded secrets
- No unsafe patterns
- Dependencies: OK

### Documentation: ⚠️ NEEDS WORK
- README should mention new component
- Website examples should show Potentiometer

## Recommendations
1. Update README.md to mention Potentiometer
2. Add Potentiometer example to website
3. Ready to merge after documentation update
```

---

## 🔄 Self-Improvement Protocol

As you execute tasks, identify opportunities to improve instructions, commands, and workflows.

### When to Self-Improve

- You encounter an error or limitation in these instructions
- You discover a more efficient approach than documented
- User feedback reveals unclear or missing guidance
- You develop a valuable workaround or pattern

### How to Self-Improve

1. **Identify** - Note the specific improvement needed
2. **Ask user** - Explain the improvement and request approval
3. **Document** - Clearly explain what changed and why
4. **Update** - Edit CLAUDE.md with the improvement
5. **Commit** - Create git commit describing the improvement

### Safety Guardrails

- **Ask first** - Always get user approval before updating CLAUDE.md
- **Only modify CLAUDE.md** - Don't change other docs without explicit request
- **Preserve intent** - Keep core philosophy and structure intact
- **Add, don't remove** - Expand guidance, only remove if documenting errors
- **Professional language** - Clear, technical, concise
- **Include reasoning** - Explain why improvement helps

---

## 📚 Project Context

### Codebase Structure

```
circuit-synth/
├── src/
│   └── circuit_synth/
│       ├── core/              # Circuit, Component, Net classes
│       ├── kicad/             # KiCad integration
│       ├── validation/        # Component and circuit validation
│       └── ...
├── tests/
│   ├── unit/                  # Unit tests
│   ├── integration/           # Integration tests
│   └── examples/              # Example circuit validation
├── examples/                  # Example circuits
└── .claude/
    ├── agents/dev/            # Development agents
    └── commands/dev/          # Development commands
```

### Dependency Libraries (We Maintain These!)

**CRITICAL:** We maintain the lower-level KiCad libraries that circuit-synth depends on:

- **kicad-sch-api** - KiCad schematic file API
  - Repository: https://github.com/atopile/kicad-sch-api
  - Purpose: Read/write KiCad .kicad_sch files
  - Used by: circuit-synth for schematic generation

- **kicad-pcb-api** - KiCad PCB file API
  - Repository: https://github.com/atopile/kicad-pcb-api
  - Purpose: Read/write KiCad .kicad_pcb files
  - Used by: circuit-synth for PCB generation

**Decision Rule:** When debugging issues in circuit-synth:

1. **Root cause in circuit-synth** → Fix it here
2. **Root cause in kicad-sch-api or kicad-pcb-api** → Fix it there

**Why this matters:**
- Don't work around upstream bugs - fix them at the source
- Improvements benefit all users of these libraries
- Better architectural separation
- Easier to maintain long-term

**Workflow for upstream fixes:**

1. **Identify root cause** - Is the bug in circuit-synth or the API library?
2. **If in API library:**
   ```bash
   # Create GitHub issue in upstream repo
   gh issue create --repo atopile/kicad-sch-api \
     --title "Bug: Position.to_dict() missing angle field" \
     --body "Root cause analysis...

   Minimal reproduction:
   \`\`\`python
   pos = Position(x=10, y=20, angle=45)
   result = pos.to_dict()
   # Expected: {'x': 10, 'y': 20, 'angle': 45}
   # Actual: {'x': 10, 'y': 20}  # Missing 'angle'
   \`\`\`

   Impact: circuit-synth issue #XXX blocked
   "

   # Clone and fix in that repo
   git clone https://github.com/atopile/kicad-sch-api.git
   cd kicad-sch-api

   # Create branch and fix with test-first approach
   git checkout -b fix/position-angle-serialization
   # ... write test, implement fix, verify

   # Create PR in upstream repo
   gh pr create --fill

   # After merge: Release new version to PyPI
   # (Maintainer will handle this)

   # Update circuit-synth dependency
   cd ../circuit-synth
   # In pyproject.toml: kicad-sch-api>=1.2.3
   poetry update kicad-sch-api

   # Verify fix works in circuit-synth
   pytest tests/test_that_was_blocked.py
   ```

3. **If in circuit-synth:**
   - Fix it here as normal

**Note:** TAC-8 autonomous infrastructure will eventually be set up in kicad-sch-api and kicad-pcb-api repos. For now, workers should create issues there when needed, but fixes will be done manually.

**Example scenario:**

```
Issue: "Component positions not serializing correctly"

Investigation reveals:
- circuit-synth calls kicad-sch-api's Position.to_dict()
- Position.to_dict() has a bug (missing 'angle' field)

Correct approach:
1. Fix Position.to_dict() in kicad-sch-api
2. Add test in kicad-sch-api
3. Release kicad-sch-api v1.2.3
4. Update circuit-synth: kicad-sch-api>=1.2.3
5. Verify fix works in circuit-synth

Wrong approach:
- Work around it in circuit-synth with custom serialization
```

### Testing Strategy

- **Unit tests** - For individual functions/classes
- **Integration tests** - For component interaction
- **Example tests** - Verify example circuits generate and validate
- **Regression tests** - Prevent re-breaking fixed issues
- **Target coverage** - >80% for new code, >85% overall

### Test-First Pattern

All development follows test-first:
1. Write failing test
2. Implement minimal code to pass
3. Add regression tests
4. Verify coverage >80%
5. Commit with test evidence

### Release Process

1. **Work on feature/fix** - Small batch, test-first
2. **Verify test suite** - All tests passing
3. **Version bump** - patch/minor/major as appropriate
4. **Release to PyPI** - `poetry publish`
5. **Verify installation** - Fresh venv test
6. **Create next issue** - Plan next small batch

### Regression Test Suite

Run full test suite before every release:

```bash
./tools/testing/run_full_regression_tests.py
```

Should show:
- All tests passing
- No regressions
- Coverage >85%
- No performance degradation

---

## 🚀 Putting It All Together

### Complete Development Session (Burst Work)

You have 45 minutes available. You want to fix a bug.

```
T=0 min: Open GitHub
  → Find issue #238: "Text class parameters incorrect"
  → Create local branch: git checkout -b fix/issue-238

T=2 min: Plan with cycles
  → This is a 30-min task (8 cycles expected)
  → Break down: 3 cycles understand, 5 cycles fix

T=5 min: Cycle 1-3 (Understanding)
  → Add logs to Text class
  → Run tests, observe logs
  → Find: Parameters being passed in wrong order

T=20 min: Cycle 4-8 (Implementation)
  → Write test with correct parameter order
  → Fix 3 callers of Text()
  → Verify all tests pass
  → Clean up 🔍 temporary logs

T=30 min: Verification
  → Launch parallel verification threads:
    - Run full test suite
    - Check code formatting
    - Verify documentation
    - Security scan

T=35 min: Commit
  → git commit -m "fix: Correct Text class parameters (#238)"
  → All verification threads reporting: ✓ PASSED

T=40 min: Release
  → Patch version bump (0.2.3 → 0.2.4)
  → Release to PyPI
  → Verify installation in fresh venv: ✓ SUCCESS

T=45 min: Done
  → Create issue for next task
  → Push branch, create PR if desired
  → Take a break!
```

---

## 💡 Key Principles Summary

1. **GitHub Issues Drive Work** - All work starts with an issue
2. **Test First** - Never untested code
3. **Iterative Cycles** - Tight 2-3 min cycles with logs
4. **Log-Driven Investigation** - Observe behavior, don't assume
5. **Small Batches** - 15-30 min independently releasable chunks
6. **Frequent Releases** - Small changes released to PyPI regularly
7. **Multi-Threaded** - Parallel verification while developing
8. **Continuous Validation** - Tests, quality checks, security scans
9. **Burst-Friendly** - Small tasks fit intermittent availability
10. **Autonomous Within Bounds** - Work independently on clear issues

---

## 🔄 Self-Improvement Protocol (How to Update This File)

This file itself is a living document. As you discover better approaches:

1. Notice inefficiency or unclear guidance
2. Ask user: "I've found a better way to approach X, should we update CLAUDE.md?"
3. Get approval before making changes
4. Update with clear explanation
5. Commit: "docs: Improve CLAUDE.md - [specific improvement]"

Examples of improvements:
- Add common error solutions discovered
- Document edge cases you encounter
- Clarify ambiguous instructions with examples
- Add helpful command patterns
- Optimize inefficient workflows

*Last updated: 2025-10-23*
*Branch: feat/developer-focused-claude-md*
