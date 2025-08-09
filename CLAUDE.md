# CLAUDE.md - Circuit-Synth Library Development Guide

This file provides guidance to Claude Code when developing the circuit-synth library. The focus is on maintaining high code quality, thorough testing, and incremental development practices.

## Development Philosophy

### Core Principles
- **Planning-heavy approach**: Always create detailed plans before coding
- **Test-driven development**: Write tests BEFORE implementing features
- **Small, iterative changes**: Make incremental improvements with frequent commits
- **Ask clarifying questions**: Never assume requirements - always confirm understanding
- **Code quality over speed**: Take time to write clean, maintainable code
- **Avoid AI slop**: Review all code for unnecessary complexity or boilerplate

### Development Workflow
1. **Understand**: Thoroughly analyze the request and ask clarifying questions
2. **Plan**: Create a detailed implementation plan with test scenarios
3. **Test First**: Write failing tests that define expected behavior
4. **Implement**: Write minimal code to make tests pass
5. **Refactor**: Improve code quality while keeping tests green
6. **Review**: Check for complexity, AI patterns, and adherence to standards
7. **Commit**: Make small, focused commits with clear messages

## Project Overview

Circuit-synth is a Python library for programmatically generating electronic circuits and converting them to KiCad projects. It includes:
- Core circuit representation (components, nets, subcircuits)
- KiCad file generation (.kicad_sch, .kicad_pcb, .kicad_pro)
- Manufacturing integration (JLCPCB, DigiKey)
- AI-powered component search and circuit validation
- Rust acceleration modules for performance-critical operations

## Tech Stack

### Core Technologies
- **Python**: 3.9+ with type hints and dataclasses
- **Rust**: Performance-critical modules with PyO3 bindings
- **Testing**: pytest with coverage reporting
- **Formatting**: black, isort
- **Linting**: flake8, mypy for type checking
- **Package Management**: uv (primary), pip (fallback)
- **Build System**: maturin for Rust/Python integration

## Essential Development Commands

### Setup and Installation
```bash
# Install in development mode with all dependencies
uv pip install -e ".[dev]"

# Sync dependencies
uv sync

# Register development agents (one-time setup)
uv run register-agents
```

### Code Quality Checks (MUST RUN BEFORE COMMITS)
```bash
# Format Python code
black src/ tests/
isort src/ tests/

# Lint Python code
flake8 src/ tests/
mypy src/

# Format Rust code
cd rust_modules && cargo fmt --all

# Run all formatting
./tools/build/format_all.sh
```

### Testing Commands
```bash
# Run all tests (Python + Rust + Integration)
./tools/testing/run_all_tests.sh

# Python tests with coverage
uv run pytest --cov=circuit_synth --cov-report=term-missing

# Run specific test file
uv run pytest tests/unit/test_core_circuit.py -v

# Test Rust modules
./tools/testing/test_rust_modules.sh

# Pre-release regression test (CRITICAL before PyPI release)
./tools/testing/run_full_regression_tests.py
```

### Building and Distribution
```bash
# Build Python package
uv build

# Build Rust modules
./tools/build/build_rust_modules.sh

# Clean rebuild everything
./tools/build/rebuild_all_rust.sh

# Release to PyPI (from main branch)
./tools/release/release_to_pypi.sh <version>
```

## Code Style Guidelines

### Python Code Standards
```python
# Use type hints for all function signatures
def process_component(name: str, value: float) -> Component:
    """Clear docstring explaining what the function does."""
    pass

# Prefer dataclasses over regular classes for data structures
@dataclass
class CircuitNode:
    id: str
    connections: List[str]
    metadata: Dict[str, Any]

# Use descriptive variable names
voltage_divider_ratio = 0.5  # Good
vdr = 0.5  # Bad

# Keep functions small and focused (max 20-30 lines)
# Extract complex logic into helper functions
```

### Design Principles
- **SOLID**: Follow Single Responsibility, Open/Closed, etc.
- **KISS**: Keep It Simple - avoid over-engineering
- **YAGNI**: Don't add functionality until it's needed
- **DRY**: Don't Repeat Yourself - extract common patterns
- **Composition over Inheritance**: Use composition for flexibility

### Common Anti-Patterns to Avoid
- Deep inheritance hierarchies
- Global state management
- Large monolithic functions
- Unclear variable/function names
- Missing error handling
- Unnecessary abstraction layers
- AI-generated boilerplate comments

## Quality Control Checklist

Before any code changes:
- [ ] Requirement is clearly understood
- [ ] Tests are written first (TDD)
- [ ] Implementation is minimal and focused
- [ ] Code passes all linting checks
- [ ] Tests provide good coverage
- [ ] No unnecessary complexity added
- [ ] Documentation is updated if needed
- [ ] Commit message is clear and descriptive

## Incremental Development Protocol

### Feature Development Process
1. **Break down the feature** into smallest possible increments
2. **Implement one increment** completely with tests
3. **Verify it works** with manual testing
4. **Commit the working increment** before moving on
5. **Repeat** for next increment

### Example Workflow
```bash
# Step 1: Write test for new feature
echo "Write test_new_feature.py"
uv run pytest tests/test_new_feature.py  # Fails (red)

# Step 2: Implement minimal code
echo "Implement feature in src/"
uv run pytest tests/test_new_feature.py  # Passes (green)

# Step 3: Refactor and improve
black src/ tests/
flake8 src/ tests/

# Step 4: Commit
git add -A
git commit -m "feat: Add new feature with tests"
```

## Multi-Attempt Problem Solving

When stuck on the same issue after 3+ attempts:

1. **STOP and Document**
   - Write clear problem statement
   - List all attempted solutions
   - Identify failure patterns

2. **Research**
   - Search for similar issues online
   - Check documentation and best practices
   - Consider if approach is fundamentally wrong

3. **Fresh Approach**
   - Question initial assumptions
   - Try completely different strategy
   - Break problem into smaller pieces

4. **Get Help**
   - Save findings to memory-bank/issues/
   - Ask for code review or pair programming
   - Consider if feature needs redesign

## Memory Bank System

Use memory-bank/ directory for persistent knowledge:

### Structure
```
memory-bank/
├── decisions/     # Architectural decisions and rationale
├── patterns/      # Reusable code patterns
├── issues/        # Known bugs and workarounds
├── progress/      # Development milestones
└── knowledge/     # Domain expertise and learnings
```

### When to Update Memory Bank
- After solving a complex problem
- When making architectural decisions
- After discovering useful patterns
- When finding workarounds for issues
- After learning new best practices

### Example Entry
```markdown
# Title: Component Creation Pattern Optimization

## Date: 2024-01-15

## Problem
Component creation was slow due to repeated symbol lookups.

## Solution
Implemented caching layer for KiCad symbol resolution.

## Code Pattern
Use @lru_cache decorator for symbol lookup functions.

## Impact
70% performance improvement in circuit generation.
```

## Project Structure

```
circuit-synth2/
├── src/circuit_synth/       # Main library code
│   ├── core/               # Core circuit representation
│   ├── kicad/              # KiCad file generation
│   ├── manufacturing/      # Supplier integrations
│   ├── validation/         # Circuit validation
│   └── ai_integration/     # AI-powered features
├── tests/                  # Test suite
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── rust_integration/  # Rust module tests
├── rust_modules/          # Rust acceleration modules
├── tools/                 # Development tools
│   ├── testing/          # Test runners
│   ├── build/            # Build scripts
│   └── release/          # Release automation
├── examples/             # Usage examples
└── docs/                # Documentation
```

## Research Before Implementation

Before implementing new features or patterns:

1. **Search for best practices**
   ```bash
   # Use web search for current best practices
   # "Python circuit generation best practices"
   # "KiCad file format specifications"
   # "Electronic component data structures"
   ```

2. **Check existing implementations**
   ```bash
   # Search codebase for similar patterns
   grep -r "pattern" src/
   find src/ -name "*.py" -exec grep -l "ComponentClass" {} \;
   ```

3. **Review standards and conventions**
   - Python PEPs for language features
   - KiCad documentation for file formats
   - Industry standards for electronic design

## CI/CD and Release Process

### Pre-Release Checklist
1. All tests passing
2. Code coverage > 80%
3. No linting errors
4. Documentation updated
5. CHANGELOG.md updated
6. Version bumped appropriately

### Release Commands
```bash
# Full regression test before release
./tools/testing/run_full_regression_tests.py

# Release to PyPI
./tools/release/release_to_pypi.sh <version>
```

## Debugging Strategies

### Development Debugging
```bash
# Always use uv for running scripts
uv run python debug_script.py

# Verbose test output
uv run pytest -vvs tests/test_file.py

# Debug with logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Performance Profiling
```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()
# Code to profile
profiler.disable()
stats = pstats.Stats(profiler).sort_stats('cumulative')
stats.print_stats(20)
```

## Common Development Tasks

### Adding a New Feature
1. Create issue/ticket for tracking
2. Write comprehensive tests first
3. Implement in small increments
4. Update documentation
5. Add example usage
6. Update CHANGELOG.md

### Fixing a Bug
1. Write test that reproduces the bug
2. Fix the bug (test should pass)
3. Check for similar issues elsewhere
4. Update regression test suite
5. Document in memory-bank/issues/

### Refactoring Code
1. Ensure comprehensive test coverage exists
2. Make incremental changes
3. Run tests after each change
4. Use version control to track progress
5. Update documentation if interfaces change

## Review Checklist for PRs

Before creating a pull request:
- [ ] All tests pass locally
- [ ] Code is formatted (black, isort)
- [ ] No linting errors (flake8, mypy)
- [ ] Test coverage maintained/improved
- [ ] Documentation updated
- [ ] Commit messages follow convention
- [ ] PR description explains changes clearly
- [ ] No unnecessary files in commit

## Contact and Resources

- **Repository**: https://github.com/yourusername/circuit-synth
- **Documentation**: https://circuit-synth.readthedocs.io
- **PyPI Package**: https://pypi.org/project/circuit-synth/
- **Issue Tracker**: GitHub Issues
- **Discord/Slack**: [Community Channel]

## Important Notes

- This is the **development guide** for the circuit-synth library
- For circuit design usage, see examples/ directory
- Always prioritize code quality over feature velocity
- When in doubt, ask for clarification before implementing