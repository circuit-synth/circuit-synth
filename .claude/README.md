# circuit-synth Development Integration

This directory contains agents and commands for developing the circuit-synth library with Claude Code.

## 🚀 Quick Start

Read `../CLAUDE.md` - This is the comprehensive guide for developing circuit-synth.

Key workflow:
1. **GitHub Issue** - Start with an issue describing what to build
2. **Test First** - Write failing test
3. **Cycles** - Iterate with logs: Add Logs → Run → Observe → Repeat
4. **Small Batch** - Complete task in 15-30 minutes
5. **Release** - Commit and release to PyPI

## 🤖 Available Agents

### Development Agents (`.claude/agents/dev/`)

- **contributor** - Onboarding and development assistance
- Add more specialized development agents as needed

### Development Commands (`.claude/commands/dev/`)

Core development commands:
- `run-tests.md` - Execute test suite
- `review-branch.md` - Comprehensive pre-merge review
- `review-repo.md` - Full repository health check
- `update-and-commit.md` - Document and commit changes
- `release-pypi.md` - Release to PyPI
- `dead-code-analysis.md` - Find unused code before release

## 🎯 Development Workflow

### 1. GitHub Issue-Driven Work

All tasks start with a GitHub issue:

```bash
# Find or create an issue
# Create local branch: git checkout -b fix/issue-123

# Work through cycles with logs
# When done: git commit -m "fix: Description (#123)"
```

### 2. Test-First Development

```python
# Write failing test FIRST
def test_new_feature():
    result = new_feature()
    assert result == expected

# Implement minimal code to pass test
# Add regression tests
# Verify coverage >80%
```

### 3. Log-Driven Cycles

```python
# Add strategic logs with 🔍 marker
logger.debug(f"🔍 Investigating {variable}")

# Run immediately
# Observe logs
# Make small change
# Run again
# Repeat until understanding complete
```

### 4. Small Batch Release

```bash
# Complete task: 15-30 minutes
# Write tests
# Run verification: /dev:review-branch
# Commit: git commit -m "fix: Description (#123)"
# Release: /dev:release-pypi
# Verify installation
```

## 📋 Development Commands

Run these from Claude Code:

```bash
# Testing
/dev:run-tests                          # Run test suite
/dev:run-tests --watch                  # Watch mode

# Code Review
/dev:review-branch --depth=quick        # Quick pre-commit check
/dev:review-branch --depth=full         # Full pre-merge review
/dev:review-repo                        # Full repo health check

# Commit Workflow
/dev:update-and-commit "description"    # Document and commit

# Release
/dev:release-pypi                       # Release to PyPI
/dev:dead-code-analysis                 # Find unused code

# Setup
./tools/maintenance/ensure-clean-environment.sh  # Clean environment
```

## 🔬 Log Management During Development

### Disable Noisy Logs

During investigation, silence unrelated logs:

```python
import logging

# Silence verbose modules
logging.getLogger('urllib3').setLevel(logging.ERROR)
logging.getLogger('kicad').setLevel(logging.WARNING)

# Enable debug for your area
logging.getLogger('circuit_synth.components').setLevel(logging.DEBUG)
logger = logging.getLogger('circuit_synth.components')
```

### Log Markers

- `🔍` - Temporary investigation logs (remove when done)
- `→` - Control flow markers
- `✓` - Verified correct behavior
- `✗` - Issue found

### Cleanup

Remove `🔍` marked logs before committing.

## 🎛️ Settings

### Claude Code Configuration

`.claude/settings.json` defines:
- **Model**: claude-sonnet-4-5 (main)
- **Sub-agents**: claude-haiku-4-5 (fast parallel work)
- **Quality gates**: Test coverage, complexity, type hints
- **Environment**: Python paths, development flags

## 📚 Development Conventions

### Code Organization

```
circuit-synth/
├── src/circuit_synth/
│   ├── core/           # Circuit, Component, Net classes
│   ├── kicad/          # KiCad integration
│   ├── validation/     # Component validation
│   └── ...
├── tests/
│   ├── unit/           # Unit tests
│   ├── integration/    # Integration tests
│   └── examples/       # Example validation
└── .claude/
    ├── agents/dev/     # Development agents
    └── commands/dev/   # Development commands
```

### Test Coverage

- **Target**: >85% overall, >80% for new code
- **Pattern**: Unit → Integration → Example validation
- **Run before release**: `./tools/testing/run_full_regression_tests.py`

### Commit Messages

Follow pattern:
```
fix: Short description (#123)
feat: New feature description (#124)
docs: Documentation update
refactor: Code cleanup or restructure
test: Add or improve tests
```

## 🚀 Typical Development Session

45 minutes available? Here's the pattern:

```
0-2 min: Find/create GitHub issue
2-5 min: Plan with cycles (expect 8-10 cycles)
5-30 min: Implement with test-first + cycles
30-35 min: Verification (parallel review)
35-40 min: Commit with issue reference
40-45 min: Release to PyPI and verify

Time for next task: Plan tomorrow!
```

## 🤝 Collaboration

### When to Be Collaborative

- Uncertain requirements
- Design decisions needed
- Breaking changes planned

### When to Be Autonomous

- Clear GitHub issue exists
- Obvious bug fix
- Well-defined subtask
- Standard refactoring

### Hybrid (Common)

- Discuss architecture
- Autonomous implementation of subtasks
- Verification threads running in parallel

## 💡 Key Principles

1. **GitHub Issues** - All work tracked in issues
2. **Test First** - Never untested code
3. **Log Cycles** - Investigate with logs, not assumptions
4. **Small Batches** - 15-30 min independently releasable chunks
5. **Frequent Releases** - Multiple releases per week
6. **Multi-Threaded** - Parallel verification always running
7. **Burst Friendly** - Tasks fit intermittent availability

## 🔗 Related Files

- **CLAUDE.md** (parent directory) - Complete development guide
- **.claude/settings.json** - Claude Code configuration
- **.claude/commands/dev/** - Available development commands
- **./tools/testing/run_full_regression_tests.py** - Full test suite

## 🚨 Important

- **Always read CLAUDE.md** - Comprehensive development guide
- **Check settings.json** - Current environment configuration
- **Run tests before committing** - Non-negotiable
- **Use GitHub issues** - Track all work
- **Small batches** - Fits your schedule
- **Verify PyPI installations** - After every release

---

*For detailed development guidance, see ../CLAUDE.md*
